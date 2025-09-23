# =============================================================================
# IMPORTS E DEPENDÊNCIAS
# =============================================================================

# Bibliotecas principais
import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import io

# Bibliotecas de visualização
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium

# Bibliotecas para geração de PDF
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.units import inch

# =============================================================================
# FUNÇÕES DE FORMATAÇÃO E UTILITÁRIOS
# =============================================================================

# Função para formatar valores grandes em formato legível (K, M, B)
def formatar_valor_grande(valor):
    """
    Formata valores grandes usando K (milhares), M (milhões), B (bilhões)
    Ex: 1.500.000 → R$ 1,50M
    """
    if valor >= 1_000_000_000:
        return f"R$ {valor / 1_000_000_000:.2f}B".replace('.', ',')
    elif valor >= 1_000_000:
        return f"R$ {valor / 1_000_000:.2f}M".replace('.', ',')
    elif valor >= 1_000:
        return f"R$ {valor / 1_000:.2f}K".replace('.', ',')
    else:
        return f"R$ {valor:.2f}".replace('.', ',')

def formatar_numero_brasileiro(numero):
    """
    Formata números no padrão brasileiro: 1.234.567 
    """
    try:
        numero = int(numero)
        return f"{numero:,.0f}".replace(',', '.')
    except:
        return str(numero)

def formatar_valor_brasileiro(valor):
    """
    Formata valores monetários no padrão brasileiro: R$ 1.234.567,89
    """
    try:
        valor = float(valor)
        if valor >= 1000:
            # Para valores >= 1000, usa separador de milhares (ponto) e decimais (vírgula)
            valor_formatado = f"{valor:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
            return f"R$ {valor_formatado}"
        else:
            # Para valores < 1000, apenas troca ponto por vírgula nos decimais
            return f"R$ {valor:.2f}".replace('.', ',')
    except:
        return str(valor)

def corrigir_populacao(populacao_series):
    """
    CORRIGIDO: Interpreta corretamente os pontos como separadores de milhares.
    Exemplo: '953.326' deve ser interpretado como 953.326 habitantes (não como float)
    """
    try:
        # Converte para string e remove pontos (separadores de milhares brasileiros)
        return populacao_series.astype(str).str.replace('.', '').astype(int)
    except:
        # Fallback: tenta conversão com preenchimento de NaN
        return pd.to_numeric(populacao_series, errors='coerce').fillna(0).astype(int)

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILOS
# =============================================================================
st.set_page_config(
    page_title="Dashboard de Precificação - Municípios de Alagoas",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS moderno e profissional
st.markdown("""
<style>
    .main-header {
        color: #2E86AB;
        text-align: center;
        padding: 2rem 0;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #2E86AB, #A23B72);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        margin: 0.5rem 0;
        transition: transform 0.3s ease;
    }
    
    .sidebar-info {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Métricas com gradientes modernos */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.25);
        margin: 0.8rem 0;
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.35);
    }
    
    /* Valores das métricas em branco */
    [data-testid="metric-container"] > div {
        background: transparent;
        color: white !important;
    }
    
    [data-testid="metric-container"] label {
        color: rgba(255,255,255,0.9) !important;
        font-weight: 600;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: white !important;
        font-weight: 700;
        font-size: 1.8rem;
    }
    
    /* Botões com estilo moderno */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Tabs com estilo moderno */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #ffffff;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        border: 2px solid #e9ecef;
        font-weight: 600;
        color: #495057 !important;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        border-color: #667eea;
        color: #667eea !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #667eea;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Força cor do texto das abas */
    .stTabs [data-baseweb="tab"] div {
        color: inherit !important;
    }
    
    .stTabs [aria-selected="true"] div {
        color: white !important;
    }
    
    /* Remove elementos desnecessários */
    .metric-container {
        background: transparent !important;
        border: none !important;
    }
    
    /* Estilo para botão PDF discreto */
    .pdf-button {
        font-size: 1.2rem;
        padding: 0.3rem 0.6rem;
        border-radius: 8px;
        opacity: 0.7;
        transition: opacity 0.2s ease;
    }
    
    .pdf-button:hover {
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

def clean_brazilian_number(value):
    """Limpa e converte valores numéricos brasileiros para float"""
    if pd.isna(value):
        return np.nan
    # Converte para string e remove aspas
    str_val = str(value).replace('"', '').strip()
    # Se já é um número, retorna
    try:
        return float(str_val)
    except ValueError:
        pass
    # Remove pontos (separadores de milhares) e substitui vírgula por ponto
    # Identifica se tem vírgula (decimal) ou apenas pontos (milhares)
    if ',' in str_val:
        # Tem vírgula decimal
        parts = str_val.rsplit(',', 1)  # Divide pela última vírgula
        if len(parts) == 2:
            integer_part = parts[0].replace('.', '')  # Remove pontos de milhares
            decimal_part = parts[1]
            str_val = f"{integer_part}.{decimal_part}"
    else:
        # Apenas pontos (pode ser milhares ou decimal)
        if str_val.count('.') > 1:
            # Múltiplos pontos = separadores de milhares
            str_val = str_val.replace('.', '')
    
    try:
        return float(str_val)
    except ValueError:
        return np.nan

# =============================================================================
# CARREGAMENTO E PROCESSAMENTO DE DADOS
# =============================================================================

@st.cache_data
def load_data():
    """Carrega e processa os dados do CSV"""
    try:
        # Procura arquivos CSV na pasta data primeiro, depois no diretório atual
        data_paths = ['data', '.']
        csv_file = None
        
        for data_dir in data_paths:
            if os.path.exists(data_dir):
                csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                if csv_files:
                    csv_file = os.path.join(data_dir, csv_files[0])
                    break
        
        if not csv_file:
            st.error("Nenhum arquivo CSV encontrado!")
            return pd.DataFrame()
        
        # Carrega o CSV especificando que a coluna Populacao deve ser tratada como string
        # para preservar os separadores de milhares brasileiros
        df = pd.read_csv(csv_file, dtype={'Populacao': str})
        
        # Limpeza e processamento dos dados
        # Remove colunas desnecessárias
        df = df.drop(['_mb_row_id', 'Unnamed Column'], axis=1, errors='ignore')
        
        # Aplica a limpeza às colunas numéricas
        numeric_columns = df.select_dtypes(include=['object']).columns
        for col in numeric_columns:
            if col not in ['Nm Mun', 'Sigla Uf', 'Ckey']:
                df[col] = df[col].apply(clean_brazilian_number)
        
        # Renomeia colunas para facilitar o uso
        column_mapping = {
            'Nm Mun': 'Municipio',
            'Cd Mun': 'Codigo_Municipio',
            'Populacao': 'Populacao',
            'Nota Veg': 'Nota_Vegetacao',
            'Nota Area': 'Nota_Area',
            'Nota Relevo': 'Nota_Relevo',
            'Nota Media': 'Nota_Media',
            'Area Cidade': 'Area_Cidade',
            'Num Imoveis': 'Num_Imoveis',
            'Valor Mun Perim': 'Valor_Municipal_Perimetro',
            'Valor Mun Area': 'Valor_Municipal_Area'
        }
        
        df = df.rename(columns=column_mapping)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

# =============================================================================
# FUNÇÕES DE MÉTRICAS E VISUALIZAÇÕES
# =============================================================================

def create_overview_metrics(df):
    """Cria métricas de visão geral focadas em precificação por área"""
    if df.empty:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏘️ Total de Municípios",
            formatar_numero_brasileiro(len(df)),
            help="Número total de municípios analisados"
        )
    
    with col2:
        if 'Valor_Municipal_Area' in df.columns:
            # Limpa e converte valores da área
            area_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            valor_total_area = area_clean.sum()
            st.metric(
                "💰 Valor Total",
                f"R$ {valor_total_area/1_000_000_000:.2f}B".replace('.', ','),
                help="Valor municipal total por área (em bilhões)"
            )
        else:
            st.metric("💰 Valor Total", "N/A")
    
    with col3:
        if 'Valor_Municipal_Area' in df.columns:
            # Calcula valor médio por município
            area_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            area_valid = area_clean[area_clean > 0]
            if len(area_valid) > 0:
                valor_medio = area_valid.mean()
                st.metric(
                    "� Valor Médio",
                    f"R$ {valor_medio/1_000_000:.2f}M".replace('.', ','),
                    help="Valor médio por município (área) em milhões"
                )
            else:
                st.metric("� Valor Médio", "N/A")
        else:
            st.metric("📊 Valor Médio", "N/A")
    
    with col4:
        if 'Valor_Municipal_Area' in df.columns:
            area_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            area_valid = area_clean[area_clean > 0]
            if len(area_valid) > 0:
                valor_max = area_valid.max()
                st.metric(
                    "🏆 Maior Valor",
                    f"R$ {valor_max/1_000_000_000:.2f}B".replace('.', ','),
                    help="Maior valor municipal por área"
                )
            else:
                st.metric("🏆 Maior Valor", "N/A")
        else:
            st.metric("🏆 Maior Valor", "N/A")

def create_population_chart(df):
    """Cria gráfico de população por município"""
    if 'Populacao' not in df.columns or 'Municipio' not in df.columns:
        st.warning("Dados de população não disponíveis")
        return
    
    # Limpa e converte dados de população
    df_clean = df.copy()
    df_clean['Populacao'] = pd.to_numeric(df_clean['Populacao'], errors='coerce').fillna(0)
    
    # Remove municípios com população 0 ou nula
    df_clean = df_clean[df_clean['Populacao'] > 0]
    
    if df_clean.empty:
        st.warning("Nenhum dado válido de população encontrado")
        return
    
    # Top 15 municípios por população
    top_pop = df_clean.nlargest(15, 'Populacao')
    
    fig = px.bar(
        top_pop,
        x='Populacao',
        y='Municipio',
        orientation='h',
        title="Top 15 Municípios por População",
        labels={'Populacao': 'População', 'Municipio': 'Município'},
        color='Populacao',
        color_continuous_scale='Blues'
    )
    
def create_value_ranking_chart(df):
    """Cria gráfico de ranking dos municípios por valor"""
    if 'Valor_Municipal_Area' not in df.columns or 'Municipio' not in df.columns:
        st.warning("Dados de valor por área não disponíveis")
        return None
    
    # Limpa e converte dados
    df_clean = df.copy()
    df_clean['Valor_Area_Clean'] = pd.to_numeric(df_clean['Valor_Municipal_Area'], errors='coerce').fillna(0)
    df_clean = df_clean.dropna(subset=['Valor_Area_Clean'])
    df_clean = df_clean[df_clean['Valor_Area_Clean'] > 0]
    
    if df_clean.empty:
        st.warning("Dados insuficientes para análise de valores")
        return None
    
    # Top 15 municípios por valor
    top_values = df_clean.nlargest(15, 'Valor_Area_Clean')
    
    # Converte para bilhões para melhor visualização
    top_values['Valor_Bilhoes'] = top_values['Valor_Area_Clean'] / 1_000_000_000
    
    fig = px.bar(
        top_values,
        x='Valor_Bilhoes',
        y='Municipio',
        title="🏆 Top 15 Municípios por Valor de Área",
        labels={'Valor_Bilhoes': 'Valor (R$ Bilhões)', 'Municipio': 'Município'},
        color='Valor_Bilhoes',
        color_continuous_scale='Viridis',
        orientation='h'
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        font=dict(size=12),
        title_font_size=16,
        margin=dict(l=150, r=50, t=80, b=50)
    )
    
    return fig

def create_value_per_population_chart(df):
    """Cria gráfico de valor por habitante"""
    if 'Valor_Municipal_Area' not in df.columns or 'Populacao' not in df.columns:
        st.warning("Dados de valor ou população não disponíveis")
        return None
    
    # Limpa dados
    df_clean = df.copy()
    df_clean['Valor_Area'] = pd.to_numeric(df_clean['Valor_Municipal_Area'], errors='coerce').fillna(0)
    df_clean['Pop'] = pd.to_numeric(df_clean['Populacao'], errors='coerce').fillna(0)
    df_clean = df_clean[(df_clean['Valor_Area'] > 0) & (df_clean['Pop'] > 0)]
    
    if df_clean.empty:
        st.warning("Dados insuficientes para análise")
        return None
    
    # Calcula valor per capita (em milhões por mil habitantes)
    df_clean['Valor_Per_Capita'] = (df_clean['Valor_Area'] / df_clean['Pop']) * 1000
    
    # Top 15 por valor per capita
    top_per_capita = df_clean.nlargest(15, 'Valor_Per_Capita')
    
    fig = px.scatter(
        top_per_capita,
        x='Pop',
        y='Valor_Area',
        hover_data=['Municipio', 'Valor_Per_Capita'],
        title="💹 Valor vs População dos Municípios",
        labels={
            'Pop': 'População',
            'Valor_Area': 'Valor por Área (R$)'
        },
        color='Valor_Per_Capita',
        color_continuous_scale='RdYlBu_r',
        size='Valor_Area',
        size_max=15
    )
    
    fig.update_layout(
        height=500,
        title_font_size=16,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def create_price_distribution_chart(df):
    """Cria gráfico de distribuição de preços"""
    if 'Valor_Municipal_Area' not in df.columns:
        st.warning("Dados de valor não disponíveis")
        return None
    
    df_clean = df.copy()
    df_clean['Valor_Area'] = pd.to_numeric(df_clean['Valor_Municipal_Area'], errors='coerce').fillna(0)
    df_clean = df_clean[df_clean['Valor_Area'] > 0]
    
    if df_clean.empty:
        st.warning("Dados insuficientes para distribuição")
        return None
    
    # Converte para bilhões
    df_clean['Valor_Bilhoes'] = df_clean['Valor_Area'] / 1_000_000_000
    
    fig = px.histogram(
        df_clean,
        x='Valor_Bilhoes',
        nbins=20,
        title="📊 Distribuição de Valores por Área",
        labels={'Valor_Bilhoes': 'Valor (R$ Bilhões)', 'count': 'Quantidade de Municípios'},
        color_discrete_sequence=['#2E86AB']
    )
    
    fig.update_layout(
        height=400,
        title_font_size=16,
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def create_notes_distribution(df):
    """Cria gráfico de distribuição das notas"""
    note_columns = [col for col in df.columns if 'Nota' in col and col != 'Nota_Media']
    
    if not note_columns:
        st.warning("Dados de notas não disponíveis")
        return
    
    # Criar subplot para múltiplas notas
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=note_columns[:4],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, col in enumerate(note_columns[:4]):
        row = (i // 2) + 1
        col_pos = (i % 2) + 1
        
        fig.add_trace(
            go.Histogram(
                x=df[col],
                name=col.replace('Nota_', ''),
                marker_color=colors[i],
                opacity=0.7,
                nbinsx=20
            ),
            row=row, col=col_pos
        )
    
    fig.update_layout(
        title="Distribuição das Notas por Categoria",
        height=600,
        showlegend=False
    )
    
    return fig

# =============================================================================
# MAPEAMENTO E GEOLOCALIZAÇÃO
# =============================================================================

def create_interactive_map(df):
    """Cria um mapa interativo dos municípios de Alagoas com dados de precificação"""
    
    # Coordenadas aproximadas dos municípios de Alagoas (algumas principais)
    municipios_coords = {
        'Maceió': [-9.6658, -35.7353],
        'Arapiraca': [-9.7515, -36.6597],
        'Palmeira dos Índios': [-9.4056, -36.6283],
        'Rio Largo': [-9.4739, -35.8553],
        'União dos Palmares': [-9.1647, -36.0264],
        'Penedo': [-10.2869, -36.5861],
        'Coruripe': [-10.1253, -36.1758],
        'São Miguel dos Campos': [-9.7808, -36.0897],
        'Santana do Ipanema': [-9.3739, -37.2456],
        'Delmiro Gouveia': [-9.3872, -37.9953],
        'Pilar': [-9.5969, -35.9567],
        'Marechal Deodoro': [-9.7122, -35.8975],
        'São Sebastião': [-9.9022, -36.5583],
        'Girau do Ponciano': [-9.8769, -36.8197],
        'Campo Alegre': [-9.7797, -36.3583],
        'Viçosa': [-9.3736, -36.2378],
        'Quebrangulo': [-9.3206, -36.4711],
        'São José da Laje': [-9.0036, -36.0528],
        'Flexeiras': [-9.2633, -35.7189],
        'Murici': [-9.3128, -35.9450],
        'Messias': [-9.4058, -35.8197],
        'Satuba': [-9.5706, -35.8306],
        'Santa Luzia do Norte': [-9.6272, -35.8256],
        'Coqueiro Seco': [-9.6286, -35.7942],
        'Maribondo': [-9.5464, -36.2181],
        'Cajueiro': [-9.3886, -36.1256],
        'Colônia Leopoldina': [-8.9067, -35.7450],
        'Joaquim Gomes': [-9.0372, -35.8131],
        'Novo Lino': [-9.1281, -35.6575],
        'Jacuípe': [-8.9225, -35.5264],
        'Porto de Pedras': [-9.1772, -35.2550],
        'Maragogi': [-9.0122, -35.2228],
        'Japaratinga': [-9.0767, -35.2506],
        'São Luís do Quitunde': [-9.3161, -35.5597],
        'Passo de Camaragibe': [-9.2467, -35.4831],
        'Barra de Santo Antônio': [-9.4281, -35.5019],
        'Matriz de Camaragibe': [-9.1506, -35.5378],
        'Porto Calvo': [-9.0386, -35.3978],
        'Jundiá': [-8.9742, -35.8583],
        'Branquinha': [-9.2331, -35.9383],
        'Capela': [-9.4078, -36.0831],
        'Chã Preta': [-9.2328, -36.2742],
        'Paulo Jacinto': [-9.1406, -36.4086],
        'Ibateguara': [-8.9719, -35.9367],
        'Pindoba': [-8.9714, -36.3028],
        'Coité do Nóia': [-9.0669, -36.1708],
        'Taquarana': [-9.0575, -36.0589],
        'Feira Grande': [-9.9039, -36.6700],
        'Cacimbinhas': [-9.3925, -37.0825],
        'Arapiraca': [-9.7515, -36.6597],
        'Lagoa da Canoa': [-9.8594, -36.7672]
    }
    
    # Centro do mapa (Alagoas)
    center_lat, center_lon = -9.5713, -36.7820
    
    # Criar o mapa base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Calcular estatísticas para coloração
    if 'Valor_Municipal_Area' in df.columns:
        valor_min = df['Valor_Municipal_Area'].min()
        valor_max = df['Valor_Municipal_Area'].max()
        
        # Adicionar marcadores para cada município
        for _, row in df.iterrows():
            municipio = row['Municipio']
            valor = row['Valor_Municipal_Area']
            
            # Tentar encontrar coordenadas do município
            coords = municipios_coords.get(municipio)
            if not coords:
                # Se não encontrar, usar coordenadas aproximadas baseadas no índice
                lat_offset = (hash(municipio) % 100 - 50) * 0.01
                lon_offset = (hash(municipio + 'lon') % 100 - 50) * 0.01
                coords = [center_lat + lat_offset, center_lon + lon_offset]
            
            # Calcular cor baseada no valor (normalizado entre 0 e 1)
            normalized_value = (valor - valor_min) / (valor_max - valor_min) if valor_max > valor_min else 0
            
            # Definir cor baseada no valor (verde para baixo, amarelo para médio, vermelho para alto)
            if normalized_value < 0.33:
                color = 'green'
                icon_color = 'lightgreen'
            elif normalized_value < 0.66:
                color = 'orange'
                icon_color = 'orange'
            else:
                color = 'red'
                icon_color = 'lightred'
            
            # Criar popup com informações detalhadas
            # Corrigir população removendo pontos (separador de milhares brasileiro)
            populacao_valor = str(row.get('Populacao', 0)).replace('.', '').replace(',', '')
            try:
                populacao_int = int(float(populacao_valor))
            except:
                populacao_int = 0
                
            popup_text = f"""
            <b>{municipio}</b><br>
            💰 Valor (Área): {formatar_valor_brasileiro(valor)}<br>
            👥 População: {formatar_numero_brasileiro(populacao_int)}<br>
            """
            
            # Adicionar notas se disponíveis
            nota_columns = [col for col in df.columns if col.startswith('Nota')]
            if nota_columns:
                popup_text += "<br><b>Notas:</b><br>"
                for nota_col in nota_columns[:3]:  # Mostrar apenas as 3 primeiras notas
                    if pd.notna(row.get(nota_col)):
                        nota_name = nota_col.replace('Nota_', '').replace('_', ' ')
                        popup_text += f"📊 {nota_name}: {row[nota_col]:.1f}<br>"
            
            # Adicionar marcador ao mapa
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{municipio} - {formatar_valor_brasileiro(valor)}",
                icon=folium.Icon(
                    color=color,
                    icon='info-sign',
                    prefix='glyphicon'
                )
            ).add_to(m)
    
    # Adicionar legenda com melhor formatação
    legend_html = '''
    <div style="position: fixed; 
                bottom: 20px; left: 20px; width: 250px; height: auto; min-height: 140px;
                background-color: white; border: 2px solid #333; z-index: 9999; 
                font-size: 13px; padding: 12px; border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3); font-family: Arial, sans-serif;
                color: #333;">
    <p style="margin: 0 0 8px 0; font-weight: bold; color: #333; font-size: 14px;">
        📊 Legenda - Valores (Área)
    </p>
    <p style="margin: 4px 0; color: #333; display: flex; align-items: center;">
        <span style="display: inline-block; width: 12px; height: 12px; 
                     background-color: green; border-radius: 50%; margin-right: 8px;"></span>
        <span style="color: #333;">Valores Baixos (até 33%)</span>
    </p>
    <p style="margin: 4px 0; color: #333; display: flex; align-items: center;">
        <span style="display: inline-block; width: 12px; height: 12px; 
                     background-color: orange; border-radius: 50%; margin-right: 8px;"></span>
        <span style="color: #333;">Valores Médios (33% - 66%)</span>
    </p>
    <p style="margin: 4px 0; color: #333; display: flex; align-items: center;">
        <span style="display: inline-block; width: 12px; height: 12px; 
                     background-color: red; border-radius: 50%; margin-right: 8px;"></span>
        <span style="color: #333;">Valores Altos (66% - 100%)</span>
    </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

# =============================================================================
# QUERY BUILDER E ANÁLISES AVANÇADAS
# =============================================================================

def create_query_builder_interface(df):
    """Interface de Query Builder similar ao Metabase"""
    
    st.markdown("### 🤖 Construtor de Consultas Inteligente")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
    <h4 style="color: white; margin: 0;">💡 Como Usar o Query Builder</h4>
    <p style="margin: 5px 0; color: white;">
    Monte sua própria consulta escolhendo <b>o que visualizar</b>, <b>como agrupar</b> e <b>quais filtros aplicar</b>.
    Ideal para análises personalizadas sem precisar de conhecimento técnico!
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Interface principal dividida em 3 seções
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("#### 📊 1. O que Mostrar?")
        
        # Seleção do tipo de visualização
        viz_type = st.selectbox(
            "Tipo de Visualização:",
            ["📈 Gráfico de Barras", "📊 Tabela Detalhada", "🥧 Gráfico de Pizza", 
             "📉 Linha do Tempo", "🎯 Métricas (Cards)", "🗺️ Dados Geográficos"],
            key="qb_viz_type"
        )
        
        # Seleção das colunas a mostrar
        available_columns = {
            'Municipio': 'Nome do Município',
            'Populacao': 'População',
            'Valor_Municipal_Area': 'Valor por Área (R$)',
            'Valor_Municipal_Perimetro': 'Valor por Perímetro (R$)',
            'Nota_Media': 'Nota Média',
            'Nota_Vegetacao': 'Nota Vegetação',
            'Nota_Area': 'Nota Área',
            'Nota_Relevo': 'Nota Relevo',
            'Area_Cidade': 'Área da Cidade',
            'Num_Imoveis': 'Número de Imóveis'
        }
        
        # Filtrar colunas disponíveis baseado no que existe no DataFrame
        available_cols = {k: v for k, v in available_columns.items() if k in df.columns}
        
        selected_columns = st.multiselect(
            "Dados para Mostrar:",
            options=list(available_cols.keys()),
            format_func=lambda x: available_cols[x],
            default=['Municipio', 'Valor_Municipal_Area'] if all(col in df.columns for col in ['Municipio', 'Valor_Municipal_Area']) else list(available_cols.keys())[:2],
            key="qb_columns"
        )
        
    with col2:
        st.markdown("#### 🔧 2. Como Agrupar?")
        
        # Agrupamento
        group_option = st.selectbox(
            "Agrupar Dados Por:",
            ["Sem Agrupamento", "Por Faixa de População", "Por Faixa de Nota", 
             "Por Faixa de Valor", "Por Região (Alfabética)", "Por Quartis"],
            key="qb_group"
        )
        
        # Ordenação
        if selected_columns:
            sort_column = st.selectbox(
                "Ordenar Por:",
                options=selected_columns,
                format_func=lambda x: available_cols.get(x, x),
                key="qb_sort_col"
            )
            
            sort_order = st.radio(
                "Ordem:",
                ["Crescente (A→Z, 1→∞)", "Decrescente (Z→A, ∞→1)"],
                key="qb_sort_order"
            )
        else:
            sort_column = None
            sort_order = "Crescente (A→Z, 1→∞)"
            
        # Limite de resultados
        limit_results = st.checkbox("Limitar Resultados", value=False, key="qb_limit")
        if limit_results:
            max_results = st.slider("Máximo de Resultados:", 5, 50, 10, key="qb_max_results")
        else:
            max_results = None
    
    with col3:
        st.markdown("#### 🎯 3. Quais Filtros?")
        
        # Filtros personalizados
        st.markdown("**Filtros Personalizados:**")
        
        # Filtro por população
        if 'Populacao' in df.columns:
            pop_filter = st.checkbox("Filtrar por População", key="qb_pop_filter")
            if pop_filter:
                pop_clean = pd.to_numeric(df['Populacao'], errors='coerce').fillna(0)
                pop_min, pop_max = int(pop_clean.min()), int(pop_clean.max())
                pop_range_qb = st.slider(
                    "Faixa de População:",
                    min_value=pop_min, max_value=pop_max,
                    value=(pop_min, pop_max), key="qb_pop_range"
                )
            else:
                pop_range_qb = None
        else:
            pop_filter = False
            pop_range_qb = None
            
        # Filtro por valor
        if 'Valor_Municipal_Area' in df.columns:
            valor_filter = st.checkbox("Filtrar por Valor", key="qb_valor_filter")
            if valor_filter:
                valor_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
                valor_valid = valor_clean[valor_clean > 0]
                if not valor_valid.empty:
                    valor_min_bi = valor_valid.min() / 1_000_000_000
                    valor_max_bi = valor_valid.max() / 1_000_000_000
                    valor_range_qb = st.slider(
                        "Faixa de Valor (R$ bilhões):",
                        min_value=float(valor_min_bi), max_value=float(valor_max_bi),
                        value=(float(valor_min_bi), float(valor_max_bi)), 
                        step=0.5, key="qb_valor_range"
                    )
                else:
                    valor_range_qb = None
            else:
                valor_range_qb = None
        else:
            valor_filter = False
            valor_range_qb = None
            
        # Filtro por nota
        if 'Nota_Media' in df.columns:
            nota_filter = st.checkbox("Filtrar por Nota", key="qb_nota_filter")
            if nota_filter:
                nota_clean = pd.to_numeric(df['Nota_Media'], errors='coerce').fillna(0)
                nota_min, nota_max = float(nota_clean.min()), float(nota_clean.max())
                nota_range_qb = st.slider(
                    "Faixa de Nota:",
                    min_value=nota_min, max_value=nota_max,
                    value=(nota_min, nota_max), 
                    step=0.1, key="qb_nota_range"
                )
            else:
                nota_range_qb = None
        else:
            nota_filter = False
            nota_range_qb = None
    
    st.markdown("---")
    
    # Botão para executar consulta
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        execute_query = st.button("🚀 Executar Consulta", type="primary", key="execute_qb")
    
    if execute_query or st.session_state.get('auto_execute_qb', False):
        if selected_columns:
            try:
                # Aplicar filtros
                filtered_df = df.copy()
                
                if pop_filter and pop_range_qb:
                    pop_clean = pd.to_numeric(filtered_df['Populacao'], errors='coerce').fillna(0)
                    filtered_df = filtered_df[(pop_clean >= pop_range_qb[0]) & (pop_clean <= pop_range_qb[1])]
                
                if valor_filter and valor_range_qb:
                    valor_clean = pd.to_numeric(filtered_df['Valor_Municipal_Area'], errors='coerce').fillna(0)
                    valor_min_real = valor_range_qb[0] * 1_000_000_000
                    valor_max_real = valor_range_qb[1] * 1_000_000_000
                    filtered_df = filtered_df[(valor_clean >= valor_min_real) & (valor_clean <= valor_max_real)]
                
                if nota_filter and nota_range_qb:
                    nota_clean = pd.to_numeric(filtered_df['Nota_Media'], errors='coerce').fillna(0)
                    filtered_df = filtered_df[(nota_clean >= nota_range_qb[0]) & (nota_clean <= nota_range_qb[1])]
                
                # Aplicar agrupamento
                result_df = apply_grouping(filtered_df, group_option, selected_columns)
                
                # Aplicar ordenação
                if sort_column and sort_column in result_df.columns:
                    ascending = sort_order.startswith("Crescente")
                    result_df = result_df.sort_values(sort_column, ascending=ascending)
                
                # Aplicar limite
                if limit_results and max_results:
                    result_df = result_df.head(max_results)
                
                # Mostrar resultado
                show_query_result(result_df, viz_type, selected_columns, available_cols)
                
            except Exception as e:
                st.error(f"Erro ao executar consulta: {str(e)}")
        else:
            st.warning("⚠️ Selecione pelo menos uma coluna para mostrar!")

def apply_grouping(df, group_option, selected_columns):
    """Aplica agrupamento aos dados conforme opção selecionada"""
    
    if group_option == "Sem Agrupamento":
        return df[selected_columns]
    
    elif group_option == "Por Faixa de População":
        if 'Populacao' in df.columns:
            pop_clean = pd.to_numeric(df['Populacao'], errors='coerce').fillna(0)
            df['Faixa_Populacao'] = pd.cut(pop_clean, 
                                         bins=[0, 20000, 50000, 100000, float('inf')],
                                         labels=['Pequeno (até 20k)', 'Médio (20k-50k)', 
                                               'Grande (50k-100k)', 'Muito Grande (100k+)'])
            # Agrupar e agregar
            numeric_cols = [col for col in selected_columns if col != 'Municipio' and df[col].dtype in ['int64', 'float64']]
            if numeric_cols:
                grouped = df.groupby('Faixa_Populacao')[numeric_cols].agg(['count', 'mean', 'sum']).round(2)
                grouped.columns = [f'{col}_{stat}' for col, stat in grouped.columns]
                return grouped.reset_index()
            else:
                return df.groupby('Faixa_Populacao').size().reset_index(name='Quantidade')
        else:
            return df[selected_columns]
    
    elif group_option == "Por Faixa de Nota":
        if 'Nota_Media' in df.columns:
            nota_clean = pd.to_numeric(df['Nota_Media'], errors='coerce').fillna(0)
            df['Faixa_Nota'] = pd.cut(nota_clean,
                                    bins=[0, 2, 4, 6, 8, 10],
                                    labels=['Muito Baixa (0-2)', 'Baixa (2-4)', 
                                          'Média (4-6)', 'Alta (6-8)', 'Muito Alta (8-10)'])
            numeric_cols = [col for col in selected_columns if col != 'Municipio' and df[col].dtype in ['int64', 'float64']]
            if numeric_cols:
                grouped = df.groupby('Faixa_Nota')[numeric_cols].agg(['count', 'mean']).round(2)
                grouped.columns = [f'{col}_{stat}' for col, stat in grouped.columns]
                return grouped.reset_index()
            else:
                return df.groupby('Faixa_Nota').size().reset_index(name='Quantidade')
        else:
            return df[selected_columns]
    
    elif group_option == "Por Faixa de Valor":
        if 'Valor_Municipal_Area' in df.columns:
            valor_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            valor_bi = valor_clean / 1_000_000_000
            df['Faixa_Valor'] = pd.cut(valor_bi,
                                     bins=[0, 5, 15, 25, float('inf')],
                                     labels=['Baixo (até 5B)', 'Médio (5B-15B)', 
                                           'Alto (15B-25B)', 'Premium (25B+)'])
            numeric_cols = [col for col in selected_columns if col != 'Municipio' and df[col].dtype in ['int64', 'float64']]
            if numeric_cols:
                grouped = df.groupby('Faixa_Valor')[numeric_cols].agg(['count', 'mean', 'sum']).round(2)
                grouped.columns = [f'{col}_{stat}' for col, stat in grouped.columns]
                return grouped.reset_index()
            else:
                return df.groupby('Faixa_Valor').size().reset_index(name='Quantidade')
        else:
            return df[selected_columns]
    
    elif group_option == "Por Região (Alfabética)":
        if 'Municipio' in df.columns:
            df['Primeira_Letra'] = df['Municipio'].str[0].str.upper()
            numeric_cols = [col for col in selected_columns if col != 'Municipio' and df[col].dtype in ['int64', 'float64']]
            if numeric_cols:
                grouped = df.groupby('Primeira_Letra')[numeric_cols].agg(['count', 'mean']).round(2)
                grouped.columns = [f'{col}_{stat}' for col, stat in grouped.columns]
                return grouped.reset_index()
            else:
                return df.groupby('Primeira_Letra').size().reset_index(name='Quantidade')
        else:
            return df[selected_columns]
    
    elif group_option == "Por Quartis":
        if len(selected_columns) > 1:
            numeric_col = next((col for col in selected_columns if col != 'Municipio' and df[col].dtype in ['int64', 'float64']), None)
            if numeric_col:
                quartis = pd.qcut(pd.to_numeric(df[numeric_col], errors='coerce').fillna(0), 
                                q=4, labels=['Q1 (25% menores)', 'Q2', 'Q3', 'Q4 (25% maiores)'])
                df['Quartil'] = quartis
                numeric_cols = [col for col in selected_columns if col != 'Municipio' and df[col].dtype in ['int64', 'float64']]
                if numeric_cols:
                    grouped = df.groupby('Quartil')[numeric_cols].agg(['count', 'mean']).round(2)
                    grouped.columns = [f'{col}_{stat}' for col, stat in grouped.columns]
                    return grouped.reset_index()
                else:
                    return df.groupby('Quartil').size().reset_index(name='Quantidade')
        return df[selected_columns]
    
    return df[selected_columns]

def show_query_result(result_df, viz_type, selected_columns, available_cols):
    """Exibe o resultado da consulta conforme tipo de visualização escolhido"""
    
    st.markdown("### 📋 Resultado da Consulta")
    st.markdown(f"**{len(result_df)} registro(s) encontrado(s)**")
    
    if viz_type == "📊 Tabela Detalhada":
        # Formatar nomes das colunas para exibição
        display_df = result_df.copy()
        column_rename = {}
        for col in display_df.columns:
            if col in available_cols:
                column_rename[col] = available_cols[col]
            elif '_' in col:
                # Formatar colunas agregadas
                parts = col.split('_')
                if len(parts) >= 2:
                    base_name = available_cols.get(parts[0], parts[0])
                    stat_name = {'count': 'Quantidade', 'mean': 'Média', 'sum': 'Total'}.get(parts[1], parts[1])
                    column_rename[col] = f"{base_name} ({stat_name})"
        
        if column_rename:
            display_df = display_df.rename(columns=column_rename)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Opção de download
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Resultado (CSV)",
            data=csv,
            file_name=f"consulta_personalizada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    elif viz_type == "📈 Gráfico de Barras":
        if len(result_df.columns) >= 2:
            x_col = result_df.columns[0]
            y_col = result_df.columns[1]
            
            fig = px.bar(result_df, x=x_col, y=y_col,
                        title=f"{available_cols.get(y_col, y_col)} por {available_cols.get(x_col, x_col)}",
                        labels={x_col: available_cols.get(x_col, x_col),
                               y_col: available_cols.get(y_col, y_col)})
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Gráfico de barras precisa de pelo menos 2 colunas")
    
    elif viz_type == "🥧 Gráfico de Pizza":
        if len(result_df.columns) >= 2:
            labels_col = result_df.columns[0]
            values_col = result_df.columns[1]
            
            fig = px.pie(result_df, names=labels_col, values=values_col,
                        title=f"Distribuição de {available_cols.get(values_col, values_col)}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Gráfico de pizza precisa de pelo menos 2 colunas")
    
    elif viz_type == "🎯 Métricas (Cards)":
        numeric_cols = result_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            cols = st.columns(min(len(numeric_cols), 4))
            for i, col in enumerate(numeric_cols[:4]):
                with cols[i]:
                    valor = result_df[col].sum() if len(result_df) > 1 else result_df[col].iloc[0]
                    st.metric(
                        label=available_cols.get(col, col),
                        value=formatar_numero_brasileiro(valor) if valor > 1000 else f"{valor:.2f}".replace('.', ',')
                    )
        else:
            st.warning("⚠️ Não há colunas numéricas para mostrar métricas")
    
    elif viz_type == "📉 Linha do Tempo":
        if len(result_df.columns) >= 2:
            x_col = result_df.columns[0]
            y_col = result_df.columns[1]
            
            fig = px.line(result_df, x=x_col, y=y_col,
                         title=f"Tendência de {available_cols.get(y_col, y_col)}",
                         labels={x_col: available_cols.get(x_col, x_col),
                                y_col: available_cols.get(y_col, y_col)})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Gráfico de linha precisa de pelo menos 2 colunas")
    
    elif viz_type == "🗺️ Dados Geográficos":
        if 'Municipio' in result_df.columns:
            st.markdown("**Dados Geográficos por Município:**")
            st.dataframe(result_df, use_container_width=True)
            
            if len(result_df) <= 10:
                st.info("💡 Dica: Com poucos municípios, você pode visualizar no mapa principal!")
        else:
            st.warning("⚠️ Dados geográficos precisam incluir a coluna 'Município'")

# =============================================================================
# GERAÇÃO DE RELATÓRIOS E EXPORTAÇÃO
# =============================================================================

def generate_pdf_report(df):
    """Gera um relatório em PDF com os dados e análises principais"""
    
    # Criar buffer para o PDF
    buffer = io.BytesIO()
    
    # Configurar documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#1f77b4'),
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#1f77b4')
    )
    
    # Conteúdo do PDF
    story = []
    
    # Título
    story.append(Paragraph("📊 Relatório de Precificação", title_style))
    story.append(Paragraph("Municípios de Alagoas", title_style))
    story.append(Spacer(1, 20))
    
    # Data de geração
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"<b>Data de geração:</b> {data_atual}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Resumo Executivo
    story.append(Paragraph("📈 Resumo Executivo", heading_style))
    
    # Calcular métricas
    total_municipios = len(df)
    if 'Populacao' in df.columns:
        populacao_clean = corrigir_populacao(df['Populacao'])
        total_populacao = int(populacao_clean.sum())
    else:
        total_populacao = 0
        
    if 'Nota_Media' in df.columns:
        nota_clean = pd.to_numeric(df['Nota_Media'], errors='coerce').fillna(0)
        nota_media = nota_clean.mean()
    else:
        nota_media = 0
        
    if 'Valor_Municipal_Area' in df.columns:
        valor_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
        valor_total = valor_clean.sum()
    else:
        valor_total = 0
    
    # Tabela de métricas principais
    metrics_data = [
        ['Métrica', 'Valor'],
        ['Total de Municípios', f'{total_municipios:,}'],
        ['População Total', f'{formatar_numero_brasileiro(total_populacao)} habitantes'],
        ['Nota Média Geral', f'{nota_media:.1f}'],
        ['Valor Municipal Total', formatar_valor_grande(valor_total)]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Top 10 Municípios por População
    if 'Populacao' in df.columns and 'Municipio' in df.columns:
        story.append(Paragraph("🏘️ Top 10 Municípios por População", heading_style))
        
        df_clean = df.copy()
        df_clean['Populacao'] = pd.to_numeric(df_clean['Populacao'], errors='coerce').fillna(0)
        top_pop = df_clean.nlargest(10, 'Populacao')[['Municipio', 'Populacao']]
        
        pop_data = [['Município', 'População']]
        for _, row in top_pop.iterrows():
            pop_data.append([row['Municipio'], formatar_numero_brasileiro(row['Populacao'])])
        
        pop_table = Table(pop_data, colWidths=[3*inch, 2*inch])
        pop_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        
        story.append(pop_table)
        story.append(Spacer(1, 20))
    
    # Análise por Notas
    note_columns = [col for col in df.columns if 'Nota' in col and col != 'Nota_Media']
    if note_columns:
        story.append(Paragraph("⭐ Análise das Notas de Avaliação", heading_style))
        
        notes_data = [['Categoria', 'Média', 'Mínimo', 'Máximo']]
        for col in note_columns[:5]:  # Limita a 5 colunas para caber na página
            values = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(values) > 0:
                notes_data.append([
                    col.replace('Nota_', '').replace('_', ' '),
                    f"{values.mean():.2f}".replace('.', ','),
                    f"{values.min():.2f}".replace('.', ','),
                    f"{values.max():.2f}".replace('.', ',')
                ])
        
        notes_table = Table(notes_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        
        story.append(notes_table)
        story.append(Spacer(1, 20))
    
    # Nova página para valores municipais
    story.append(PageBreak())
    
    # Top 10 por Valor Municipal
    if 'Valor_Municipal_Area' in df.columns and 'Municipio' in df.columns:
        story.append(Paragraph("💰 Top 10 Municípios por Valor Municipal", heading_style))
        
        df_clean = df.copy()
        df_clean['Valor_Municipal_Area'] = pd.to_numeric(df_clean['Valor_Municipal_Area'], errors='coerce').fillna(0)
        top_values = df_clean.nlargest(10, 'Valor_Municipal_Area')[['Municipio', 'Valor_Municipal_Area']]
        
        values_data = [['Município', 'Valor Municipal (R$)']]
        for _, row in top_values.iterrows():
            values_data.append([row['Municipio'], formatar_valor_brasileiro(row['Valor_Municipal_Area'])])
        
        values_table = Table(values_data, colWidths=[3*inch, 3*inch])
        values_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        
        story.append(values_table)
        story.append(Spacer(1, 20))
    
    # Resumo estatístico
    story.append(Paragraph("📊 Resumo Estatístico Geral", heading_style))
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        summary_stats = df[numeric_cols].describe()
        
        # Seleciona apenas algumas colunas principais para o relatório
        main_cols = []
        for col in ['Populacao', 'Nota_Media', 'Valor_Municipal_Area']:
            if col in summary_stats.columns:
                main_cols.append(col)
        
        if main_cols:
            stats_data = [['Estatística'] + [col.replace('_', ' ') for col in main_cols]]
            
            for stat in ['mean', 'std', 'min', 'max']:
                row = [stat.title()]
                for col in main_cols:
                    value = summary_stats.loc[stat, col]
                    if col == 'Populacao':
                        row.append(formatar_numero_brasileiro(value))
                    elif col == 'Valor_Municipal_Area':
                        row.append(formatar_valor_brasileiro(value))
                    else:
                        row.append(f"{value:.2f}".replace('.', ','))
                stats_data.append(row)
            
            stats_table = Table(stats_data)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            
            story.append(stats_table)
    
    # Rodapé
    story.append(Spacer(1, 30))
    story.append(Paragraph("📋 Relatório gerado automaticamente pelo Dashboard de Precificação", styles['Normal']))
    story.append(Paragraph("🏘️ Dados referentes aos municípios de Alagoas", styles['Normal']))
    
    # Construir PDF
    doc.build(story)
    
    # Retornar o buffer
    buffer.seek(0)
    return buffer

def apply_filters(df, municipios_selecionados, busca_texto, pop_range, nota_range, valor_range, show_top_only):
    """Aplica todos os filtros selecionados ao DataFrame"""
    df_filtered = df.copy()
    
    # Filtro por municípios selecionados
    if municipios_selecionados and 'Municipio' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Municipio'].isin(municipios_selecionados)]
    
    # Filtro por busca de texto
    if busca_texto and 'Municipio' in df_filtered.columns:
        df_filtered = df_filtered[
            df_filtered['Municipio'].str.contains(busca_texto, case=False, na=False)
        ]
    
    # Filtro por população
    if 'Populacao' in df_filtered.columns:
        pop_clean = pd.to_numeric(df_filtered['Populacao'], errors='coerce').fillna(0)
        df_filtered = df_filtered[
            (pop_clean >= pop_range[0]) & (pop_clean <= pop_range[1])
        ]
    
    # Filtro por nota média
    if 'Nota_Media' in df_filtered.columns:
        nota_clean = pd.to_numeric(df_filtered['Nota_Media'], errors='coerce').fillna(0)
        df_filtered = df_filtered[
            (nota_clean >= nota_range[0]) & (nota_clean <= nota_range[1])
        ]
    
    # Filtro por valor municipal
    if 'Valor_Municipal_Area' in df_filtered.columns:
        valor_clean = pd.to_numeric(df_filtered['Valor_Municipal_Area'], errors='coerce').fillna(0)
        # Converter de bilhões para valores reais (valor_range está em bilhões)
        valor_min_real = valor_range[0] * 1_000_000_000
        valor_max_real = valor_range[1] * 1_000_000_000
        df_filtered = df_filtered[
            (valor_clean >= valor_min_real) & (valor_clean <= valor_max_real)
        ]
    
    # Aplicar filtros rápidos
    if show_top_only == "Top 10 Valor" and 'Valor_Municipal_Area' in df_filtered.columns:
        valor_clean = pd.to_numeric(df_filtered['Valor_Municipal_Area'], errors='coerce').fillna(0)
        df_filtered = df_filtered.nlargest(10, 'Valor_Municipal_Area')
    elif show_top_only == "Top 10 Perímetro" and 'Valor_Municipal_Perimetro' in df_filtered.columns:
        perim_clean = pd.to_numeric(df_filtered['Valor_Municipal_Perimetro'], errors='coerce').fillna(0)
        df_filtered = df_filtered.nlargest(10, 'Valor_Municipal_Perimetro')
    elif show_top_only == "Top 5 Premium" and 'Valor_Municipal_Area' in df_filtered.columns:
        valor_clean = pd.to_numeric(df_filtered['Valor_Municipal_Area'], errors='coerce').fillna(0)
        df_filtered = df_filtered.nlargest(5, 'Valor_Municipal_Area')
    elif show_top_only == "Baixo Valor" and 'Valor_Municipal_Area' in df_filtered.columns:
        valor_clean = pd.to_numeric(df_filtered['Valor_Municipal_Area'], errors='coerce').fillna(0)
        # Pegar valores abaixo de 5 bilhões
        df_filtered = df_filtered[valor_clean < 5_000_000_000]
    
    return df_filtered

def create_scatter_analysis(df):
    """Cria análise de correlação scatter"""
    if 'Populacao' not in df.columns or 'Nota_Media' not in df.columns:
        st.warning("Dados para análise de correlação não disponíveis")
        return
    
    # Limpa os dados
    df_clean = df.copy()
    df_clean['Populacao'] = pd.to_numeric(df_clean['Populacao'], errors='coerce').fillna(0)
    df_clean['Nota_Media'] = pd.to_numeric(df_clean['Nota_Media'], errors='coerce').fillna(0)
    
    # Remove registros com valores inválidos
    df_clean = df_clean[(df_clean['Populacao'] > 0) & (df_clean['Nota_Media'] > 0)]
    
    if df_clean.empty:
        st.warning("Dados insuficientes para análise de correlação")
        return
    
    fig = px.scatter(
        df_clean,
        x='Populacao',
        y='Nota_Media',
        hover_data=['Municipio'],
        title="Relação entre População e Nota Média",
        labels={'Populacao': 'População', 'Nota_Media': 'Nota Média'},
        color='Nota_Media',
        color_continuous_scale='RdYlBu_r',
        size='Populacao',
        size_max=20
    )
    
    fig.update_layout(height=500)
    
    return fig

def create_value_analysis(df):
    """Cria análise de valores municipais"""
    if 'Valor_Municipal_Area' not in df.columns:
        st.warning("Dados de valor municipal não disponíveis")
        return
    
    # Limpa os dados
    df_clean = df.copy()
    df_clean['Valor_Municipal_Area'] = pd.to_numeric(df_clean['Valor_Municipal_Area'], errors='coerce').fillna(0)
    
    # Remove registros com valores inválidos
    df_clean = df_clean[df_clean['Valor_Municipal_Area'] > 0]
    
    if df_clean.empty:
        st.warning("Dados insuficientes para análise de valores")
        return
    
    # Top 10 municípios por valor
    top_values = df_clean.nlargest(10, 'Valor_Municipal_Area')
    
    fig = px.bar(
        top_values,
        x='Municipio',
        y='Valor_Municipal_Area',
        title="Top 10 Municípios por Valor Municipal (Área)",
        labels={'Valor_Municipal_Area': 'Valor Municipal (R$)', 'Municipio': 'Município'},
        color='Valor_Municipal_Area',
        color_continuous_scale='Greens'
    )
    
    fig.update_layout(
        height=500,
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    return fig

# =============================================================================
# INTERFACE PRINCIPAL E CONTROLE DE APLICAÇÃO  
# =============================================================================

def main():
    # Header principal com botão PDF no canto direito
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.markdown('<h1 class="main-header">🏘️ Dashboard de Precificação - Municípios de Alagoas</h1>', unsafe_allow_html=True)
    
    # Carrega os dados primeiro
    df = load_data()
    
    if df.empty:
        st.error("❌ Não foi possível carregar os dados. Verifique se o arquivo CSV está no diretório correto.")
        return
    
    # Inicializar valores padrão no session_state se não existirem
    if 'municipios_selecionados' not in st.session_state:
        st.session_state.municipios_selecionados = []
    if 'busca_texto' not in st.session_state:
        st.session_state.busca_texto = ""
    if 'show_top_only' not in st.session_state:
        st.session_state.show_top_only = "Todos"
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔍 Filtros")
        
        # Seleção de municípios
        municipios_lista = sorted(df['Municipio'].unique()) if 'Municipio' in df.columns else []
        municipios_selecionados = st.multiselect(
            "🏘️ Municípios",
            options=municipios_lista,
            placeholder="Todos",
            key="municipios_selecionados"
        )
        
        # Busca rápida
        busca_texto = st.text_input(
            "🔍 Buscar",
            placeholder="Nome do município...",
            key="busca_texto"
        )
        
        # População
        if 'Populacao' in df.columns:
            pop_clean = pd.to_numeric(df['Populacao'], errors='coerce').fillna(0)
            pop_min, pop_max = int(pop_clean.min()), int(pop_clean.max())
            
            pop_range = st.slider(
                "👥 População",
                min_value=pop_min,
                max_value=pop_max,
                value=(pop_min, pop_max),
                key="pop_range"
            )
        
        # Nota média
        if 'Nota_Media' in df.columns:
            nota_clean = pd.to_numeric(df['Nota_Media'], errors='coerce').fillna(0)
            nota_min, nota_max = float(nota_clean.min()), float(nota_clean.max())
            
            nota_range = st.slider(
                "⭐ Nota",
                min_value=nota_min,
                max_value=nota_max,
                value=(nota_min, nota_max),
                step=0.1,
                key="nota_range"
            )
        
        # Valor por área
        if 'Valor_Municipal_Area' in df.columns:
            area_values = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            area_valid = area_values[area_values > 0]
            
            if not area_valid.empty:
                valor_min, valor_max = float(area_valid.min()), float(area_valid.max())
                valor_min_bi = valor_min / 1_000_000_000
                valor_max_bi = valor_max / 1_000_000_000
                
                valor_range = st.slider(
                    "💰 Valor (R$ bi)",
                    min_value=valor_min_bi,
                    max_value=valor_max_bi,
                    value=(valor_min_bi, valor_max_bi),
                    step=1.0,
                    key="valor_range"
                )
            else:
                valor_range = (0, 0)
        else:
            valor_range = (0, 0)
        
        # Análise rápida
        show_top_only = st.selectbox(
            "🎯 Análise",
            options=["Todos", "Top 10 Valor", "Top 10 Perímetro", "Top 5 Premium", "Baixo Valor"],
            key="show_top_only"
        )
        
        # Botão limpar
        if st.button("🗑️ Limpar", type="secondary", use_container_width=True):
            keys_to_clear = ['municipios_selecionados', 'busca_texto', 'pop_range', 'nota_range', 'valor_range', 'show_top_only']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    # Aplica filtros
    df_original = df.copy()  # Manter cópia original para estatísticas
    
    # Obter valores dos filtros do session_state ou valores padrão
    municipios_selecionados = st.session_state.get('municipios_selecionados', [])
    busca_texto = st.session_state.get('busca_texto', "")
    show_top_only = st.session_state.get('show_top_only', "Todos")
    
    # Valores padrão para ranges baseados nos dados
    if 'Populacao' in df.columns:
        pop_clean = pd.to_numeric(df['Populacao'], errors='coerce').fillna(0)
        pop_min, pop_max = int(pop_clean.min()), int(pop_clean.max())
        pop_range_val = st.session_state.get('pop_range', (pop_min, pop_max))
    else:
        pop_range_val = (0, 0)
    
    if 'Nota_Media' in df.columns:
        nota_clean = pd.to_numeric(df['Nota_Media'], errors='coerce').fillna(0)
        nota_min, nota_max = float(nota_clean.min()), float(nota_clean.max())
        nota_range_val = st.session_state.get('nota_range', (nota_min, nota_max))
    else:
        nota_range_val = (0, 0)
    
    if 'Valor_Municipal_Area' in df.columns:
        # Os dados já foram processados, usamos diretamente
        valor_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
        valor_valid = valor_clean[valor_clean > 0]
        if not valor_valid.empty:
            valor_min, valor_max = float(valor_valid.min()), float(valor_valid.max())
            # Usar bilhões para ser consistente com o slider
            valor_min_bi, valor_max_bi = valor_min / 1_000_000_000, valor_max / 1_000_000_000
            valor_range_val = st.session_state.get('valor_range', (valor_min_bi, valor_max_bi))
        else:
            valor_range_val = (0, 0)
    else:
        valor_range_val = (0, 0)
    
    df_filtered = apply_filters(
        df, 
        municipios_selecionados, 
        busca_texto, 
        pop_range_val, 
        nota_range_val, 
        valor_range_val, 
        show_top_only
    )
    
    # Verificar se há dados após filtros
    if df_filtered.empty:
        st.warning("⚠️ Nenhum município corresponde aos filtros aplicados. Tente ajustar os critérios.")
        df_filtered = df_original  # Usar dados originais se filtros resultarem em conjunto vazio
    
    # Adicionar botão PDF no cabeçalho direito
    with header_col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaço para alinhar com o título
        # Criar duas colunas pequenas para alinhar o botão mais à direita
        _, btn_col = st.columns([2, 1])
        with btn_col:
            if st.button("📄", help="Gerar Relatório PDF", type="secondary"):
                with st.spinner("Gerando PDF..."):
                    try:
                        # Usar dados filtrados para o relatório
                        pdf_buffer = generate_pdf_report(df_filtered)
                        
                        # Gerar nome do arquivo com timestamp e info de filtros
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        if len(df_filtered) != len(df_original):
                            filename = f"relatorio_precificacao_alagoas_filtrado_{len(df_filtered)}municipios_{timestamp}.pdf"
                        else:
                            filename = f"relatorio_precificacao_alagoas_{timestamp}.pdf"
                        
                        st.download_button(
                            label="⬇️",
                            data=pdf_buffer.getvalue(),
                            file_name=filename,
                            mime="application/pdf",
                            help="Download do Relatório PDF"
                        )
                        
                        if len(df_filtered) != len(df_original):
                            st.success(f"✅ PDF pronto ({len(df_filtered)} municípios)")
                        else:
                            st.success("✅ PDF pronto!")
                            
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    # Usar dados filtrados para todas as visualizações
    df = df_filtered
    
    # Métricas de visão geral
    st.markdown("## 📈 Visão Geral")
    create_overview_metrics(df)
    
    st.markdown("---")
    
    # Tabs para diferentes análises focadas em precificação
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🗺️ Mapa Interativo", "🏆 Ranking de Valores", "📊 Análise Comparativa", "📈 Distribuição de Preços", "🤖 Query Builder", "📋 Dados & Exportação"])
    
    with tab1:
        st.markdown("### 🗺️ Mapa Interativo dos Municípios")
        st.markdown("Visualize os municípios de Alagoas com dados de precificação. As cores dos marcadores representam diferentes faixas de valores.")
        
        # Criar e exibir o mapa em tela cheia
        if 'Valor_Municipal_Area' in df_filtered.columns:
            try:
                interactive_map = create_interactive_map(df_filtered)
                # Mapa ocupando toda a largura da tela
                st_folium(interactive_map, width=None, height=600, use_container_width=True)
                
                # Estatísticas do mapa
                st.markdown("#### 📊 Estatísticas do Mapa")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_municipios = len(df_filtered)
                    st.metric("�️ Total de Municípios", total_municipios)
                
                with col2:
                    if 'Valor_Municipal_Area' in df_filtered.columns:
                        # Converter para valores numéricos e calcular total em bilhões
                        valores_clean = pd.to_numeric(df_filtered['Valor_Municipal_Area'], errors='coerce').fillna(0)
                        valor_total_bi = valores_clean.sum() / 1_000_000_000
                        st.metric("💰 Valor Total", f"R$ {valor_total_bi:.2f}B".replace('.', ','))
                
                with col3:
                    if 'Populacao' in df_filtered.columns:
                        pop_clean = corrigir_populacao(df_filtered['Populacao'])
                        pop_total = int(pop_clean.sum())
                        st.metric("👥 População Total", formatar_numero_brasileiro(pop_total))
                
            except Exception as e:
                st.error(f"❌ Erro ao carregar o mapa: {str(e)}")
                st.info("💡 Dica: Certifique-se de que os dados de localização estão disponíveis.")
        else:
            st.warning("⚠️ Dados de valor municipal não disponíveis para o mapa.")

    with tab2:
        st.markdown("### �🏆 Ranking dos Municípios por Valor")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_ranking = create_value_ranking_chart(df_filtered)
            if fig_ranking:
                st.plotly_chart(fig_ranking, use_container_width=True)
        
        with col2:
            st.markdown("#### 📈 Estatísticas")
            if 'Valor_Municipal_Area' in df_filtered.columns:
                valores_clean = df_filtered['Valor_Municipal_Area'].apply(clean_brazilian_number)
                valores_valid = valores_clean.dropna()
                
                if not valores_valid.empty:
                    st.metric("💰 Maior Valor", f"R$ {valores_valid.max()/1_000_000_000:.2f}B".replace('.', ','))
                    st.metric("📊 Valor Médio", f"R$ {valores_valid.mean()/1_000_000_000:.2f}B".replace('.', ',')) 
                    st.metric("📉 Menor Valor", f"R$ {valores_valid.min()/1_000_000:.2f}M".replace('.', ','))
                    st.metric("🎯 Total Geral", f"R$ {valores_valid.sum()/1_000_000_000:.2f}B".replace('.', ','))
                else:
                    st.info("📊 Nenhum dado de valor disponível para os filtros aplicados")
        
        # Tabela detalhada
        st.markdown("### 📋 Dados Detalhados")
        if 'Municipio' in df_filtered.columns and 'Valor_Municipal_Area' in df_filtered.columns:
            display_df = df_filtered[['Municipio', 'Valor_Municipal_Area', 'Valor_Municipal_Perimetro']].copy()
            display_df['Valor_Area_Limpo'] = display_df['Valor_Municipal_Area'].apply(clean_brazilian_number)
            display_df['Valor_Perim_Limpo'] = display_df['Valor_Municipal_Perimetro'].apply(clean_brazilian_number)
            display_df = display_df.sort_values('Valor_Area_Limpo', ascending=False)
            
            # Formata para exibição
            display_df['Valor Área (R$ Mi)'] = (display_df['Valor_Area_Limpo'] / 1_000_000).round(1)
            display_df['Valor Perímetro (R$ Mi)'] = (display_df['Valor_Perim_Limpo'] / 1_000_000).round(2)
            
            final_df = display_df[['Municipio', 'Valor Área (R$ Mi)', 'Valor Perímetro (R$ Mi)']]
            st.dataframe(final_df, use_container_width=True)

    with tab3:
        st.markdown("### 💹 Análise: Valor vs População")
        
        fig_comparison = create_value_per_population_chart(df_filtered)
        if fig_comparison:
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Análise de correlação específica
        st.markdown("### 🔗 Correlação entre Valores")
        if 'Valor_Municipal_Area' in df_filtered.columns and 'Valor_Municipal_Perimetro' in df_filtered.columns:
            area_clean = df_filtered['Valor_Municipal_Area'].apply(clean_brazilian_number)
            perim_clean = df_filtered['Valor_Municipal_Perimetro'].apply(clean_brazilian_number)
            
            valid_data = pd.DataFrame({
                'Area': area_clean,
                'Perimetro': perim_clean
            }).dropna()
            
            if len(valid_data) > 1:
                correlation = valid_data['Area'].corr(valid_data['Perimetro'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🔗 Correlação", f"{correlation:.3f}")
                with col2:
                    st.metric("📊 Dados Válidos", f"{len(valid_data)}")
                with col3:
                    ratio_medio = (valid_data['Area'] / valid_data['Perimetro']).mean()
                    st.metric("⚖️ Ratio Médio (Área/Perímetro)", f"{ratio_medio:.2f}".replace('.', ','))
    
    with tab4:
        st.markdown("### 📊 Distribuição de Preços por Área")
        
        fig_distribution = create_price_distribution_chart(df_filtered)
        if fig_distribution:
            st.plotly_chart(fig_distribution, use_container_width=True)
        
        # Faixas de preço
        st.markdown("### 💼 Análise por Faixas de Preço")
        if 'Valor_Municipal_Area' in df_filtered.columns:
            valores_clean = df_filtered['Valor_Municipal_Area'].apply(clean_brazilian_number)
            valores_valid = valores_clean.dropna()
            
            if not valores_valid.empty:
                # Converte para bilhões
                valores_bi = valores_valid / 1_000_000_000
                
                # Define faixas
                faixas = {
                    "💚 Baixo (< 5B)": (valores_bi < 5).sum(),
                    "💛 Médio (5B - 15B)": ((valores_bi >= 5) & (valores_bi < 15)).sum(),
                    "🧡 Alto (15B - 25B)": ((valores_bi >= 15) & (valores_bi < 25)).sum(),
                    "❤️ Premium (≥ 25B)": (valores_bi >= 25).sum()
                }
                
                col1, col2, col3, col4 = st.columns(4)
                cols = [col1, col2, col3, col4]
                
                for i, (faixa, count) in enumerate(faixas.items()):
                    with cols[i]:
                        percentage = (count / len(valores_bi) * 100) if len(valores_bi) > 0 else 0
                        st.metric(faixa, f"{count}", f"{percentage:.1f}%")
            
            # Limpa os dados financeiros
            valor_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            
            with col1:
                st.metric("Valor Médio", formatar_valor_grande(valor_clean.mean()))
            with col2:
                st.metric("Valor Máximo", formatar_valor_grande(valor_clean.max()))
            with col3:
                st.metric("Valor Mínimo", formatar_valor_grande(valor_clean.min()))
    
                st.info("💡 Dica: Certifique-se de que os dados de localização estão disponíveis.")
        else:
            st.warning("⚠️ Dados de valor municipal não disponíveis para o mapa.")

    # Tab 5: Query Builder
    with tab5:
        st.markdown("# 🤖 Query Builder - Construtor de Consultas")
        create_query_builder_interface(df_filtered)
    
    # Tab 6: Dados & Exportação
    with tab6:
        st.markdown("# 📋 Dados & Exportação")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🔍 Filtros da Tabela")
            
            # Filtros específicos para a tabela
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                # Filtro por município
                if 'Municipio' in df.columns:
                    municipios_disponiveis = ['Todos'] + sorted(df['Municipio'].unique().tolist())
                    municipio_filtro = st.selectbox("🏘️ Filtrar por Município", municipios_disponiveis)
                else:
                    municipio_filtro = None
                    st.warning("⚠️ Coluna de município não encontrada")
                
            with filter_col2:
                # Filtro por faixa de população
                if 'Populacao' in df.columns:
                    pop_clean = corrigir_populacao(df['Populacao'])
                    pop_min, pop_max = int(pop_clean.min()), int(pop_clean.max())
                    pop_filtro = st.slider("👥 Faixa de População", pop_min, pop_max, (pop_min, pop_max), format="%d")
                else:
                    pop_filtro = None
        
        with col2:
            st.markdown("### 📊 Estatísticas Rápidas")
            st.metric("📍 Total de Registros", len(df))
            if 'Municipio' in df.columns:
                st.metric("🏘️ Municípios", df['Municipio'].nunique())
            else:
                st.metric("🏘️ Municípios", "N/A")
            st.metric("📋 Colunas", len(df.columns))
            
            # Botão de download
            st.markdown("### 💾 Exportar Dados")
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar CSV Completo",
                data=csv_data,
                file_name=f"precificacao_alagoas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        # Aplicar filtros na tabela
        df_tabela = df.copy()
        
        if municipio_filtro and municipio_filtro != 'Todos' and 'Municipio' in df.columns:
            df_tabela = df_tabela[df_tabela['Municipio'] == municipio_filtro]
            
        if pop_filtro and 'Populacao' in df.columns:
            pop_clean = corrigir_populacao(df_tabela['Populacao'])
            df_tabela = df_tabela[(pop_clean >= pop_filtro[0]) & (pop_clean <= pop_filtro[1])]
        
        # Exibir tabela filtrada
        st.markdown("### 📋 Tabela de Dados")
        
        if len(df_tabela) > 0:
            st.info(f"📊 Exibindo {len(df_tabela)} de {len(df)} registros")
            
            # Opções de visualização
            colunas_padrao = []
            if 'Municipio' in df.columns:
                colunas_padrao.append('Municipio')
            if 'Populacao' in df.columns:
                colunas_padrao.append('Populacao')
            if 'Valor_Municipal_Area' in df.columns:
                colunas_padrao.append('Valor_Municipal_Area')
            if 'Nota_Media' in df.columns:
                colunas_padrao.append('Nota_Media')
            
            # Se não encontrou as colunas padrão, usar as 5 primeiras
            if not colunas_padrao:
                colunas_padrao = df.columns[:5].tolist()
                
            show_cols = st.multiselect(
                "🔍 Selecionar Colunas para Exibir",
                options=df.columns.tolist(),
                default=colunas_padrao,
                help="Escolha quais colunas deseja visualizar na tabela"
            )
            
            if show_cols:
                st.dataframe(
                    df_tabela[show_cols], 
                    use_container_width=True,
                    height=400
                )
            else:
                st.warning("⚠️ Selecione pelo menos uma coluna para exibir")
        else:
            st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados")
        
        # Informações técnicas em expansor
        with st.expander("ℹ️ Informações Técnicas"):
            st.markdown(f"""
            **Fonte dos dados:** CSV de Precificação - Municípios de Alagoas
            
            **Total de registros:** {formatar_numero_brasileiro(len(df))}
            
            **Colunas disponíveis:** {len(df.columns)}
            
            **Última atualização:** {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}
            
            **Estrutura dos dados:**
            """)
            
            # Mostrar tipos de dados
            info_df = pd.DataFrame({
                'Coluna': df.columns,
                'Tipo': df.dtypes.astype(str),
                'Valores Únicos': [df[col].nunique() for col in df.columns],
                'Nulos': [df[col].isnull().sum() for col in df.columns]
            })
            st.dataframe(info_df, use_container_width=True)

    # Footer simplificado
    st.markdown("---")
    st.markdown("*💡 Dica: Use a aba 'Dados & Exportação' para visualizar e baixar os dados completos*")

if __name__ == "__main__":
    main()