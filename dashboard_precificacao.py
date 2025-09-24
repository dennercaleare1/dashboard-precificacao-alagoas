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

# Bibliotecas para IA e Machine Learning (versão simplificada)
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# FUNÇÕES DE FORMATAÇÃO E UTILITÁRIOS
# =============================================================================

# Funções para formatar valores grandes em formato legível (K, M, B)
def formatar_valor_grande(valor, incluir_rs=True):
    """
    Formata valores grandes usando K (milhares), M (milhões), B (bilhões)
    Ex: 1.500.000 → R$ 1,50M ou 1,50M
    """
    if pd.isna(valor) or valor == 0:
        return "R$ 0" if incluir_rs else "0"
    
    prefix = "R$ " if incluir_rs else ""
    
    if valor >= 1_000_000_000:
        return f"{prefix}{valor / 1_000_000_000:.1f}B".replace('.', ',')
    elif valor >= 1_000_000:
        return f"{prefix}{valor / 1_000_000:.1f}M".replace('.', ',')
    elif valor >= 1_000:
        return f"{prefix}{valor / 1_000:.0f}K".replace('.', ',')
    else:
        return f"{prefix}{valor:.0f}".replace('.', ',')

def formatar_numero_grande(numero):
    """
    Formata números grandes sem símbolo de moeda
    Ex: 1.500.000 → 1,5M
    """
    return formatar_valor_grande(numero, incluir_rs=False)

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

def formatar_dataframe_para_exibicao(df, colunas_selecionadas=None):
    """
    Formata DataFrame para exibição resumida, especialmente valores monetários grandes
    """
    if df.empty:
        return df
        
    df_formatado = df.copy()
    colunas_para_formatar = colunas_selecionadas if colunas_selecionadas else df.columns
    
    for coluna in colunas_para_formatar:
        if coluna in df_formatado.columns:
            # Formatar colunas de valor municipal
            if 'Valor_Municipal' in coluna or 'valor_municipal' in coluna.lower():
                try:
                    # Converter para numérico e aplicar formatação resumida
                    valores_numericos = pd.to_numeric(df_formatado[coluna], errors='coerce')
                    # Criar nova coluna formatada em string para evitar warning
                    df_formatado[coluna] = valores_numericos.apply(
                        lambda x: formatar_valor_grande(x) if pd.notna(x) and x > 0 else 'N/A'
                    ).astype(str)
                except:
                    pass
            
            # Formatar outras colunas monetárias grandes
            elif any(palavra in coluna.lower() for palavra in ['preco', 'valor', 'custo', 'receita']):
                try:
                    valores_numericos = pd.to_numeric(df_formatado[coluna], errors='coerce')
                    # Se os valores são muito grandes (> 1 milhão), usar formatação resumida
                    if valores_numericos.max() > 1_000_000:
                        df_formatado[coluna] = valores_numericos.apply(
                            lambda x: formatar_valor_grande(x) if pd.notna(x) and x > 0 else 'N/A'
                        ).astype(str)
                except:
                    pass
                    
            # Formatar população para padrão brasileiro
            elif 'populacao' in coluna.lower() or 'população' in coluna.lower():
                try:
                    valores_numericos = pd.to_numeric(df_formatado[coluna], errors='coerce')
                    df_formatado[coluna] = valores_numericos.apply(
                        lambda x: formatar_numero_brasileiro(x) if pd.notna(x) else 'N/A'
                    ).astype(str)
                except:
                    pass
    
    return df_formatado

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

def converter_numero_brasileiro(valor_str):
    """
    NOVA FUNÇÃO: Converte números no formato brasileiro para Python.
    
    Formatos suportados:
    - '20.553.313.781,77' → 20553313781.77 (valores monetários)
    - '343.700.899,36' → 343700899.36 (áreas com decimais)
    - '2.708.600' → 2708600 (códigos/inteiros)
    - '163' → 163 (valores simples)
    """
    try:
        if pd.isna(valor_str) or valor_str in ['', 'nan', 'NaN']:
            return 0
            
        valor_str = str(valor_str).strip()
        
        if ',' in valor_str:
            # Tem vírgula decimal - é um valor com decimais
            partes = valor_str.split(',')
            parte_inteira = partes[0].replace('.', '')  # Remove pontos dos milhares
            parte_decimal = partes[1]
            return float(f"{parte_inteira}.{parte_decimal}")
        else:
            # Sem vírgula - remove pontos e converte para int
            return int(valor_str.replace('.', ''))
    except:
        return 0

def corrigir_colunas_brasileiras(df):
    """
    Aplica correção de formato brasileiro em todas as colunas numéricas relevantes
    """
    # Colunas que sabemos que estão em formato brasileiro
    colunas_brasileiras = [
        'Populacao', 'Cd Mun', 'Num Imoveis',
        'Area Cidade', 'Area Georef', 'Area Car Total', 'Area Car Media',
        'Perimetro Total Car', 'Perimetro Medio Car', 'Area Max Perim',
        'Valor Mun Perim', 'Valor Mun Area'
    ]
    
    # Também incluir colunas de notas que usam vírgula decimal
    colunas_notas = [col for col in df.columns if 'Nota' in col and df[col].dtype == 'object']
    colunas_brasileiras.extend(colunas_notas)
    
    # Também incluir colunas de percentual
    colunas_percent = [col for col in df.columns if 'Percent' in col and df[col].dtype == 'object']
    colunas_brasileiras.extend(colunas_percent)
    
    for col in colunas_brasileiras:
        if col in df.columns:
            try:
                df[col] = df[col].apply(converter_numero_brasileiro)
            except Exception as e:
                print(f"Erro ao converter coluna {col}: {e}")
                # Mantém original se der erro
                pass
    
    return df

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
        padding: 3rem 0 2rem 0;
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2E86AB 0%, #A23B72 50%, #F18F01 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 2rem;
        text-shadow: 0 4px 8px rgba(0,0,0,0.1);
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    
    .header-container {
        text-align: center;
        margin: 2rem 0 3rem 0;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(46, 134, 171, 0.05) 0%, rgba(162, 59, 114, 0.05) 100%);
        border-radius: 20px;
        border: 1px solid rgba(46, 134, 171, 0.1);
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .header-subtitle {
        color: #6c757d;
        font-size: 1.1rem;
        font-weight: 400;
        margin-top: 0.5rem;
        opacity: 0.8;
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
# SISTEMA DE RECOMENDAÇÃO INTELIGENTE
# =============================================================================

def calculate_municipality_score(df_row, preferences):
    """Calcula o score de um município baseado nas preferências do usuário"""
    score = 0
    explanations = []
    
    # Normalizar valores para scores de 0-100
    try:
        # 1. Orçamento - peso alto (30%)
        valor_area = df_row.get('Valor_Municipal_Area', 0)
        if pd.isna(valor_area):
            valor_area = 0
        
        if preferences['orcamento_max'] > 0:
            if valor_area <= preferences['orcamento_max']:
                budget_score = 100 - (valor_area / preferences['orcamento_max'] * 50)
                score += budget_score * 0.3
                explanations.append(f"💰 Dentro do orçamento (Score: {budget_score:.0f})")
            else:
                budget_score = max(0, 50 - ((valor_area - preferences['orcamento_max']) / preferences['orcamento_max'] * 100))
                score += budget_score * 0.3
                explanations.append(f"💸 Acima do orçamento (Score: {budget_score:.0f})")
        
        # 2. População - peso médio (20%)
        populacao = df_row.get('Populacao', 0)
        if pd.isna(populacao):
            populacao = 0
            
        pop_diff = abs(populacao - preferences['populacao_ideal'])
        pop_score = max(0, 100 - (pop_diff / preferences['populacao_ideal'] * 100))
        score += pop_score * 0.2
        explanations.append(f"👥 População adequada (Score: {pop_score:.0f})")
        
        # 3. Qualidade geral - peso alto (25%)
        nota_media = df_row.get('Nota_Media', 0)
        if pd.isna(nota_media):
            nota_media = 0
            
        quality_score = (nota_media / 25) * 100  # Assumindo nota máxima ~25
        score += quality_score * 0.25
        explanations.append(f"⭐ Qualidade geral (Score: {quality_score:.0f})")
        
        # 4. Critérios específicos baseados no tipo - peso médio (25%)
        specific_score = 0
        if preferences['tipo_preferencia'] == 'Econômico':
            # Prioriza valor baixo e custo-benefício
            if valor_area > 0:
                custo_beneficio = nota_media / (valor_area / 1000000)  # Nota por milhão
                specific_score = min(100, custo_beneficio * 10)
                explanations.append(f"💡 Excelente custo-benefício (Score: {specific_score:.0f})")
        
        elif preferences['tipo_preferencia'] == 'Qualidade':
            # Prioriza notas altas
            nota_veg = df_row.get('Nota_Vegetacao', 0) or 0
            nota_area = df_row.get('Nota_Area', 0) or 0
            nota_relevo = df_row.get('Nota_Relevo', 0) or 0
            
            quality_avg = (nota_veg + nota_area + nota_relevo) / 3
            specific_score = (quality_avg / 8) * 100  # Assumindo nota máxima ~8
            explanations.append(f"🏆 Alta qualidade ambiental (Score: {specific_score:.0f})")
        
        elif preferences['tipo_preferencia'] == 'Crescimento':
            # Prioriza municípios com potencial de crescimento
            num_imoveis = df_row.get('Num_Imoveis', 0) or 0
            area_cidade = df_row.get('Area_Cidade', 0) or 0
            
            if area_cidade > 0:
                densidade = num_imoveis / area_cidade
                specific_score = min(100, densidade * 50)
                explanations.append(f"📈 Potencial de crescimento (Score: {specific_score:.0f})")
        
        score += specific_score * 0.25
        
    except Exception as e:
        score = 0
        explanations = ["❌ Erro no cálculo do score"]
    
    return min(100, max(0, score)), explanations

def get_smart_recommendations(df, preferences, top_n=5):
    """Gera recomendações inteligentes baseadas nas preferências"""
    recommendations = []
    
    for idx, row in df.iterrows():
        score, explanations = calculate_municipality_score(row, preferences)
        
        recommendations.append({
            'municipio': row.get('Municipio', 'N/A'),
            'score': score,
            'explanations': explanations,
            'data': row
        })
    
    # Ordena por score e retorna top N
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations[:top_n]

def create_recommendation_interface(df):
    """Cria a interface de recomendação inteligente"""
    st.markdown("### 🎯 Configure suas Preferências")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Orçamento")
        # Usar clean_brazilian_number para valores corretos
        valor_clean = df['Valor_Municipal_Area'].apply(clean_brazilian_number).fillna(0)
        valor_valid = valor_clean[valor_clean > 0]
        
        if not valor_valid.empty:
            min_valor = 0
            max_valor = int(valor_valid.max() * 1.2)
            median_valor = int(valor_valid.median())
            
            # Converter para milhões
            min_valor_m = min_valor / 1_000_000
            max_valor_m = max_valor / 1_000_000
            median_valor_m = median_valor / 1_000_000
            
            # Garantir que min < max com tolerância mínima
            if max_valor_m - min_valor_m < 1.0:
                # Se a diferença é muito pequena, adicionar range artificial
                max_valor_m = max(min_valor_m + 100.0, min_valor_m * 1.5)  # Adicionar 100M ou 50% a mais
            
            orcamento_max_m = st.slider(
                "Valor máximo por área (R$ milhões)",
                min_value=min_valor_m,
                max_value=max_valor_m,
                value=median_valor_m,
                step=1.0,
                format="R$ %.0fM",
                help="Valor máximo que você está disposto a pagar por área municipal"
            )
            # Converter de volta para valor absoluto
            orcamento_max = int(orcamento_max_m * 1_000_000)
        else:
            st.warning("Dados de valor insuficientes")
            orcamento_max = 1_000_000_000  # 1 bilhão como padrão
        
        st.markdown("#### 👥 População")
        # Usar clean_brazilian_number para garantir conversão correta
        pop_clean = df['Populacao'].apply(clean_brazilian_number).fillna(0)
        pop_valid = pop_clean[pop_clean > 0]
        
        if not pop_valid.empty and len(pop_valid) > 1:
            min_pop = int(pop_valid.min())
            max_pop = int(pop_valid.max())
            median_pop = int(pop_valid.median())
            
            # Converter para milhares
            min_pop_k = min_pop / 1000
            max_pop_k = max_pop / 1000
            median_pop_k = median_pop / 1000
            
            # Garantir que min < max com tolerância mínima
            if max_pop_k - min_pop_k < 1.0:
                # Se a diferença é muito pequena, adicionar range artificial
                max_pop_k = min_pop_k + 10.0  # Adicionar 10K habitantes como range mínimo
            
            populacao_ideal_k = st.slider(
                "População ideal (milhares de habitantes)",
                min_value=min_pop_k,
                max_value=max_pop_k,
                value=median_pop_k,
                step=1.0,
                format="%.0fK",
                help="População ideal do município"
            )
            # Converter de volta para valor absoluto
            populacao_ideal = int(populacao_ideal_k * 1000)
        else:
            st.warning("Dados de população insuficientes")
            populacao_ideal = 50000  # Valor padrão
    
    with col2:
        st.markdown("#### 🎨 Tipo de Investimento")
        tipo_preferencia = st.selectbox(
            "Prioridade principal",
            ['Econômico', 'Qualidade', 'Crescimento'],
            help="Econômico: Melhor custo-benefício\nQualidade: Melhores indicadores\nCrescimento: Potencial de valorização"
        )
        
        st.markdown("#### ⚖️ Importância dos Critérios")
        peso_orcamento = st.slider("Peso do Orçamento", 1, 10, 7)
        peso_qualidade = st.slider("Peso da Qualidade", 1, 10, 8)
        peso_populacao = st.slider("Peso da População", 1, 10, 5)
    
    # Configurações das preferências
    preferences = {
        'orcamento_max': orcamento_max,
        'populacao_ideal': populacao_ideal,
        'tipo_preferencia': tipo_preferencia,
        'peso_orcamento': peso_orcamento,
        'peso_qualidade': peso_qualidade,
        'peso_populacao': peso_populacao
    }
    
    return preferences

def display_recommendations(recommendations, df):
    """Exibe as recomendações de forma visual e atrativa"""
    
    if not recommendations:
        st.warning("Nenhuma recomendação encontrada com os critérios selecionados.")
        return
    
    st.markdown("### 🏆 Suas Recomendações Personalizadas")
    
    # Ranking das recomendações
    for i, rec in enumerate(recommendations):
        municipio = rec['municipio']
        score = rec['score']
        explanations = rec['explanations']
        data = rec['data']
        
        # Criar card da recomendação
        with st.container():
            # Badge de posição
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {'#FFD700' if i == 0 else '#C0C0C0' if i == 1 else '#CD7F32' if i == 2 else '#4CAF50'} 0%, 
                {'#FFA500' if i == 0 else '#A9A9A9' if i == 1 else '#A0522D' if i == 2 else '#45a049'} 100%);
                padding: 2rem;
                border-radius: 15px;
                margin: 1rem 0;
                color: white;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            ">
                <h3 style="margin: 0; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 2rem;">{medal}</span>
                    {municipio}
                    <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.9rem; margin-left: auto;">
                        Score: {score:.0f}/100
                    </span>
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Detalhes em colunas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "💰 Valor por Área", 
                    formatar_valor_grande(data.get('Valor_Municipal_Area', 0)),
                    help="Valor municipal por área"
                )
                st.metric(
                    "👥 População", 
                    formatar_numero_grande(data.get('Populacao', 0))
                )
            
            with col2:
                st.metric(
                    "⭐ Nota Média", 
                    f"{data.get('Nota_Media', 0):.1f}",
                    help="Média das notas de qualidade"
                )
                st.metric(
                    "🏘️ Imóveis", 
                    formatar_numero_grande(data.get('Num_Imoveis', 0))
                )
            
            with col3:
                st.metric(
                    "🌿 Nota Vegetação", 
                    f"{data.get('Nota_Vegetacao', 0):.1f}"
                )
                st.metric(
                    "🏔️ Nota Relevo", 
                    f"{data.get('Nota_Relevo', 0):.1f}"
                )
            
            # Explicações da recomendação
            st.markdown("**🤖 Por que recomendamos:**")
            for explanation in explanations:
                st.markdown(f"• {explanation}")
            
            # Gráfico radar do município
            if i < 3:  # Mostrar radar apenas para top 3
                create_municipality_radar(data, municipio)
            
            st.markdown("---")

def create_municipality_radar(data, municipio):
    """Cria gráfico radar para um município específico"""
    categories = ['Vegetação', 'Área', 'Relevo', 'Qualidade P.Q1', 'Qualidade P.Q2']
    values = [
        data.get('Nota_Vegetacao', 0),
        data.get('Nota_Area', 0),
        data.get('Nota_Relevo', 0),
        data.get('Nota P Q1', 0),
        data.get('Nota P Q2', 0)
    ]
    
    # Normalizar valores para 0-10
    max_val = max(values) if max(values) > 0 else 1
    values_norm = [v/max_val * 10 for v in values]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_norm + [values_norm[0]],  # Fechar o polígono
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(102, 126, 234, 0.3)',
        line=dict(color='rgb(102, 126, 234)', width=2),
        name=municipio
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False,
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, width='stretch')

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
        
        # Carrega o CSV como string para preservar formatação brasileira
        df = pd.read_csv(csv_file, dtype=str)
        
        # NOVA CORREÇÃO: Aplica conversão brasileira em todas as colunas numéricas
        df = corrigir_colunas_brasileiras(df)
        
        # Limpeza e processamento dos dados
        # Remove colunas desnecessárias
        df = df.drop(['_mb_row_id', 'Unnamed Column'], axis=1, errors='ignore')
        
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
            formatar_numero_grande(len(df)),
            help="Número total de municípios analisados"
        )
    
    with col2:
        if 'Valor_Municipal_Area' in df.columns:
            # Limpa e converte valores da área
            area_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            valor_total_area = area_clean.sum()
            st.metric(
                "Valor Total",
                formatar_valor_grande(valor_total_area),
                help="Valor municipal total por área"
            )
        else:
            st.metric("Valor Total", "N/A")
    
    with col3:
        if 'Valor_Municipal_Area' in df.columns:
            # Calcula valor médio por município
            area_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            area_valid = area_clean[area_clean > 0]
            if len(area_valid) > 0:
                valor_medio = area_valid.mean()
                st.metric(
                    "Valor Médio",
                    formatar_valor_grande(valor_medio),
                    help="Valor médio por município (área)"
                )
            else:
                st.metric("Valor Médio", "N/A")
        else:
            st.metric("Valor Médio", "N/A")
    
    with col4:
        if 'Valor_Municipal_Area' in df.columns:
            area_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            area_valid = area_clean[area_clean > 0]
            if len(area_valid) > 0:
                valor_max = area_valid.max()
                st.metric(
                    "Maior Valor",
                    formatar_valor_grande(valor_max),
                    help="Maior valor municipal por área"
                )
            else:
                st.metric("Maior Valor", "N/A")
        else:
            st.metric("Maior Valor", "N/A")

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
        title="Ranking dos 15 Principais Municípios por Valor de Área",
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
    """Cria gráfico de distribuição de preços melhorado"""
    if 'Valor_Municipal_Area' not in df.columns:
        st.warning("Dados de valor não disponíveis")
        return None
    
    df_clean = df.copy()
    df_clean['Valor_Area'] = df_clean['Valor_Municipal_Area'].apply(clean_brazilian_number)
    df_clean = df_clean[df_clean['Valor_Area'] > 0]
    
    if df_clean.empty:
        st.warning("Dados insuficientes para distribuição")
        return None
    
    # Converte para bilhões
    df_clean['Valor_Bilhoes'] = df_clean['Valor_Area'] / 1_000_000_000
    
    # Cria histograma com estilo melhorado
    fig = px.histogram(
        df_clean,
        x='Valor_Bilhoes',
        nbins=25,
        title="Distribuição de Valores Municipais por Área",
        labels={'Valor_Bilhoes': 'Valor Municipal (R$ Bilhões)', 'count': 'Quantidade de Municípios'},
        color_discrete_sequence=['#00D4AA'],
        opacity=0.8
    )
    
    # Adiciona linha de média
    media = df_clean['Valor_Bilhoes'].mean()
    fig.add_vline(
        x=media, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Média: R$ {media:.1f}B",
        annotation_position="top right"
    )
    
    # Melhorias visuais
    fig.update_traces(
        marker_line_color='white',
        marker_line_width=1.5,
        hovertemplate='<b>Faixa de Valor:</b> R$ %{x:.1f}B<br>' +
                      '<b>Quantidade:</b> %{y} municípios<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(
        height=500,
        title_font_size=18,
        title_x=0.5,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        margin=dict(l=60, r=60, t=100, b=60),
        xaxis=dict(
            gridcolor='lightgray',
            gridwidth=0.5,
            title_font_size=14
        ),
        yaxis=dict(
            gridcolor='lightgray',
            gridwidth=0.5,
            title_font_size=14
        )
    )
    
    return fig

def create_price_by_population_chart(df):
    """Cria gráfico de valor por população"""
    if 'Valor_Municipal_Area' not in df.columns or 'População' not in df.columns:
        return None
    
    df_clean = df.copy()
    df_clean['Valor_Area'] = df_clean['Valor_Municipal_Area'].apply(clean_brazilian_number)
    df_clean['Pop'] = df_clean['População'].apply(clean_brazilian_number)
    
    # Remove valores inválidos
    df_clean = df_clean[(df_clean['Valor_Area'] > 0) & (df_clean['Pop'] > 0)]
    
    if df_clean.empty:
        return None
    
    # Converte unidades
    df_clean['Valor_Bilhoes'] = df_clean['Valor_Area'] / 1_000_000_000
    df_clean['Pop_Milhares'] = df_clean['Pop'] / 1000
    df_clean['Valor_per_Capita'] = df_clean['Valor_Area'] / df_clean['Pop']
    
    # Cria scatter plot
    fig = px.scatter(
        df_clean,
        x='Pop_Milhares',
        y='Valor_Bilhoes',
        size='Valor_per_Capita',
        hover_name='Municipio',
        title="Correlação entre Valor Municipal e População",
        labels={
            'Pop_Milhares': 'População (milhares)',
            'Valor_Bilhoes': 'Valor Municipal (R$ Bilhões)',
            'Valor_per_Capita': 'Valor per Capita (R$)'
        },
        color='Valor_per_Capita',
        color_continuous_scale='Viridis',
        size_max=20
    )
    
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>' +
                      'População: %{x:.0f}k habitantes<br>' +
                      'Valor Municipal: R$ %{y:.1f}B<br>' +
                      'Valor per Capita: R$ %{marker.size:,.0f}<br>' +
                      '<extra></extra>'
    )
    
    fig.update_layout(
        height=500,
        title_font_size=18,
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        margin=dict(l=60, r=60, t=100, b=60),
        coloraxis_colorbar_title="Valor per Capita<br>(R$)"
    )
    
    return fig

def create_price_boxplot(df):
    """Cria boxplot da distribuição de preços"""
    if 'Valor_Municipal_Area' not in df.columns:
        return None
    
    df_clean = df.copy()
    df_clean['Valor_Area'] = df_clean['Valor_Municipal_Area'].apply(clean_brazilian_number)
    df_clean = df_clean[df_clean['Valor_Area'] > 0]
    
    if df_clean.empty:
        return None
    
    # Converte para bilhões
    df_clean['Valor_Bilhoes'] = df_clean['Valor_Area'] / 1_000_000_000
    
    # Cria boxplot
    fig = px.box(
        df_clean,
        y='Valor_Bilhoes',
        title="Análise Estatística da Distribuição de Valores",
        labels={'Valor_Bilhoes': 'Valor Municipal (R$ Bilhões)'},
        color_discrete_sequence=['#FF6B6B']
    )
    
    fig.update_traces(
        hovertemplate='<b>Estatísticas:</b><br>' +
                      'Q1: %{q1:.1f}B<br>' +
                      'Mediana: %{median:.1f}B<br>' +
                      'Q3: %{q3:.1f}B<br>' +
                      'Máximo: %{upperfence:.1f}B<br>' +
                      'Mínimo: %{lowerfence:.1f}B<br>' +
                      '<extra></extra>',
        boxpoints='outliers'
    )
    
    fig.update_layout(
        height=400,
        title_font_size=16,
        title_x=0.5,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        margin=dict(l=60, r=60, t=80, b=60),
        yaxis=dict(
            gridcolor='lightgray',
            gridwidth=0.5,
            title_font_size=14
        )
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
            Valor (Área): {formatar_valor_grande(valor)}<br>
            👥 População: {formatar_numero_grande(populacao_int)}<br>
            """
            
            # Adicionar notas se disponíveis
            nota_columns = [col for col in df.columns if col.startswith('Nota')]
            if nota_columns:
                popup_text += "<br><b>Notas:</b><br>"
                for nota_col in nota_columns[:3]:  # Mostrar apenas as 3 primeiras notas
                    if pd.notna(row.get(nota_col)):
                        nota_name = nota_col.replace('Nota_', '').replace('_', ' ')
                        popup_text += f"{nota_name}: {row[nota_col]:.1f}<br>"
            
            # Adicionar marcador ao mapa
            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{municipio} - {formatar_valor_grande(valor)}",
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
        Legenda - Valores (Área)
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
    
    st.markdown("### Construtor de Consultas")
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
        st.markdown("#### 1. Tipo de Visualização")
        
        # Seleção do tipo de visualização
        viz_type = st.selectbox(
            "Tipo de Visualização:",
            ["Gráfico de Barras", "Tabela Detalhada", "Gráfico de Pizza", 
             "Linha do Tempo", "Métricas (Cards)", "Dados Geográficos"],
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
        st.markdown("#### 3. Filtros de Dados")
        
        # Filtros personalizados
        st.markdown("**Filtros Personalizados:**")
        
        # Filtro por população
        if 'Populacao' in df.columns:
            pop_filter = st.checkbox("Filtrar por População", key="qb_pop_filter")
            if pop_filter:
                pop_clean = pd.to_numeric(df['Populacao'], errors='coerce').fillna(0)
                pop_min, pop_max = int(pop_clean.min()), int(pop_clean.max())
                # Converter para milhares
                pop_min_k = pop_min / 1000
                pop_max_k = pop_max / 1000
                pop_range_qb_k = st.slider(
                    "Faixa de População (milhares):",
                    min_value=pop_min_k, max_value=pop_max_k,
                    value=(pop_min_k, pop_max_k), 
                    step=1.0,
                    key="qb_pop_range",
                    format="%.0fK"
                )
                # Converter de volta
                pop_range_qb = (int(pop_range_qb_k[0] * 1000), int(pop_range_qb_k[1] * 1000))
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
                    valor_range_qb_bi = st.slider(
                        "Faixa de Valor Municipal:",
                        min_value=float(valor_min_bi), max_value=float(valor_max_bi),
                        value=(float(valor_min_bi), float(valor_max_bi)), 
                        step=0.1, 
                        key="qb_valor_range",
                        format="R$ %.1fB"
                    )
                    # Converter de volta para valores absolutos
                    valor_range_qb = (valor_range_qb_bi[0] * 1_000_000_000, valor_range_qb_bi[1] * 1_000_000_000)
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
        execute_query = st.button("Executar Consulta", type="primary", key="execute_qb")
    
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
    
    st.markdown("### Resultado da Consulta")
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
        
        st.dataframe(display_df, width='stretch')
        
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
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("⚠️ Gráfico de barras precisa de pelo menos 2 colunas")
    
    elif viz_type == "🥧 Gráfico de Pizza":
        if len(result_df.columns) >= 2:
            labels_col = result_df.columns[0]
            values_col = result_df.columns[1]
            
            fig = px.pie(result_df, names=labels_col, values=values_col,
                        title=f"Distribuição de {available_cols.get(values_col, values_col)}")
            st.plotly_chart(fig, width='stretch')
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
            st.plotly_chart(fig, width='stretch')
        else:
            st.warning("⚠️ Gráfico de linha precisa de pelo menos 2 colunas")
    
    elif viz_type == "🗺️ Dados Geográficos":
        if 'Municipio' in result_df.columns:
            st.markdown("**Dados Geográficos por Município:**")
            st.dataframe(result_df, width='stretch')
            
            if len(result_df) <= 10:
                st.info("💡 Dica: Com poucos municípios, você pode visualizar no mapa principal!")
        else:
            st.warning("⚠️ Dados geográficos precisam incluir a coluna 'Município'")

# =============================================================================
# GERAÇÃO DE RELATÓRIOS E EXPORTAÇÃO
# =============================================================================

def generate_custom_pdf_report(df, titulo="Relatório de Precificação Municipal", subtitulo="Análise Estratégica", 
                              incluir_timestamp=True, incluir_capa=True, incluir_resumo_executivo=True,
                              incluir_ranking=True, incluir_estatisticas=True, incluir_graficos=True,
                              incluir_analise_qualidade=True, incluir_insights=True, incluir_recomendacoes=True,
                              incluir_quadro_resumo=True, incluir_conclusoes=True, incluir_metodologia=False,
                              incluir_rodape_premium=True, top_count=10, criterio_ranking="Valor Municipal",
                              incluir_correlacao=True, incluir_distribuicao=True):
    """Gera um relatório PDF PERSONALIZADO baseado nas configurações do usuário"""
    
    # Importar bibliotecas adicionais
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Backend não-interativo
    import seaborn as sns
    from datetime import datetime
    import tempfile
    import base64
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image
    import numpy as np
    
    # Configurar matplotlib para português e estilo profissional
    plt.style.use('seaborn-v0_8')
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9
    plt.rcParams['figure.titlesize'] = 14
    
    # Criar buffer para o PDF
    buffer = io.BytesIO()
    
    # Configurar documento PDF com design premium e margens adequadas
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=60,
        bottomMargin=60
    )
    
    # Estilos premium
    styles = getSampleStyleSheet()
    
    # Estilo do título principal
    title_style = ParagraphStyle(
        'PremiumTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # centralizado
        textColor=colors.HexColor('#1a365d'),
        fontName='Helvetica-Bold'
    )
    
    # Estilo do subtítulo
    subtitle_style = ParagraphStyle(
        'PremiumSubtitle', 
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20,
        alignment=1,
        textColor=colors.HexColor('#2d3748'),
        fontName='Helvetica'
    )
    
    # Estilo de seções (simplificado)
    section_style = ParagraphStyle(
        'PremiumSection',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=15,
        spaceBefore=25,
        textColor=colors.HexColor('#2b6cb0'),
        fontName='Helvetica-Bold',
        leftIndent=0
    )
    
    # Estilo para destaques
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#2d3748'),
        fontName='Helvetica-Bold',
        leftIndent=10,
        spaceAfter=10,
        spaceBefore=8
    )
    
    # Estilo para insights (simplificado para evitar sobreposições)
    insight_style = ParagraphStyle(
        'Insight',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4a5568'),
        fontName='Helvetica',
        leftIndent=20,
        spaceAfter=8,
        spaceBefore=4
    )
    
    # Conteúdo do PDF
    story = []
    
    # === CAPA PREMIUM (se selecionada) ===
    if incluir_capa:
        story.append(Spacer(1, 30))
        
        # Criar box de título premium
        title_box_data = [
            [f"🏛️ {titulo.upper()}"],
            [subtitulo],
            ["Estado de Alagoas - 2024/2025"]
        ]
        
        title_box_table = Table(title_box_data, colWidths=[6*inch])
        title_box_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 20),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, 1), 16),
            ('FONTNAME', (0, 2), (0, 2), 'Helvetica'),
            ('FONTSIZE', (0, 2), (0, 2), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#2d3748'))
        ]))
        
        story.append(title_box_table)
        story.append(Spacer(1, 30))
        
        # Box de informações da capa
        if incluir_timestamp:
            data_atual = datetime.now().strftime("%d de %B de %Y às %H:%M")
        else:
            data_atual = datetime.now().strftime("%B de %Y")
            
        info_data = [
            ['📅 Data do Relatório:', data_atual],
            ['📊 Municípios Analisados:', f"{len(df)} municípios"],
            ['🎯 Tipo de Análise:', 'Precificação por Área Municipal'],
            ['💼 Gerado por:', 'Dashboard de Precificação - IA'],
        ]
        
        info_table = Table(info_data, colWidths=[2.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        
        story.append(info_table)
        story.append(PageBreak())
    
    # Usar a mesma lógica do PDF original mas com condicionais para cada seção
    # Adicionar todas as outras seções condicionalmente...
    
    # === RESUMO EXECUTIVO (se selecionado) ===
    if incluir_resumo_executivo:
        story.append(Paragraph("📊 RESUMO EXECUTIVO", section_style))
        # ... resto da lógica do resumo executivo
    
    # === RANKING (se selecionado) ===
    if incluir_ranking:
        story.append(Paragraph(f"🏆 RANKING DOS TOP {top_count} MUNICÍPIOS", section_style))
        # ... resto da lógica do ranking
    
    # Continuar para todas as outras seções...
    
    # Construir PDF
    doc.build(story)
    
    # Retornar o buffer
    buffer.seek(0)
    return buffer

def generate_pdf_report(df):
    """Gera um relatório PREMIUM em PDF com design profissional, gráficos e análises avançadas"""
    
    # Importar bibliotecas adicionais
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Backend não-interativo
    import seaborn as sns
    from datetime import datetime
    import tempfile
    import base64
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image
    import numpy as np
    
    # Configurar matplotlib para português e estilo profissional
    plt.style.use('seaborn-v0_8')
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9
    plt.rcParams['figure.titlesize'] = 14
    
    # Criar buffer para o PDF
    buffer = io.BytesIO()
    
    # Configurar documento PDF com design premium e margens adequadas
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=60,
        leftMargin=60,
        topMargin=60,
        bottomMargin=60
    )
    
    # Estilos premium
    styles = getSampleStyleSheet()
    
    # Estilo do título principal
    title_style = ParagraphStyle(
        'PremiumTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # centralizado
        textColor=colors.HexColor('#1a365d'),
        fontName='Helvetica-Bold'
    )
    
    # Estilo do subtítulo
    subtitle_style = ParagraphStyle(
        'PremiumSubtitle', 
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=20,
        alignment=1,
        textColor=colors.HexColor('#2d3748'),
        fontName='Helvetica'
    )
    
    # Estilo de seções (simplificado)
    section_style = ParagraphStyle(
        'PremiumSection',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=15,
        spaceBefore=25,
        textColor=colors.HexColor('#2b6cb0'),
        fontName='Helvetica-Bold',
        leftIndent=0
    )
    
    # Estilo para destaques
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#2d3748'),
        fontName='Helvetica-Bold',
        leftIndent=10,
        spaceAfter=10,
        spaceBefore=8
    )
    
    # Estilo para insights (simplificado para evitar sobreposições)
    insight_style = ParagraphStyle(
        'Insight',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4a5568'),
        fontName='Helvetica',
        leftIndent=20,
        spaceAfter=8,
        spaceBefore=4
    )
    
    # Conteúdo do PDF
    story = []
    
    # === CAPA PREMIUM ===
    story.append(Spacer(1, 30))
    
    # Criar box de título premium
    title_box_data = [
        ["🏛️ RELATÓRIO EXECUTIVO PREMIUM"],
        ["ANÁLISE DE PRECIFICAÇÃO MUNICIPAL"],
        ["Estado de Alagoas - 2024/2025"]
    ]
    
    title_box_table = Table(title_box_data, colWidths=[6*inch])
    title_box_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 20),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, 1), 16),
        ('FONTNAME', (0, 2), (0, 2), 'Helvetica'),
        ('FONTSIZE', (0, 2), (0, 2), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#2d3748'))
    ]))
    
    story.append(title_box_table)
    story.append(Spacer(1, 30))
    
    # Box de informações da capa
    data_atual = datetime.now().strftime("%d de %B de %Y às %H:%M")
    info_data = [
        ['📅 Data do Relatório:', data_atual],
        ['📊 Municípios Analisados:', f"{len(df)} municípios"],
        ['🎯 Tipo de Análise:', 'Precificação por Área Municipal'],
        ['💼 Gerado por:', 'Dashboard de Precificação - IA'],
    ]
    
    info_table = Table(info_data, colWidths=[2.5*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
    ]))
    
    story.append(info_table)
    story.append(PageBreak())
    
    # === RESUMO EXECUTIVO ===
    story.append(Paragraph("� RESUMO EXECUTIVO", section_style))
    
    if not df.empty:
        # Calcular métricas principais
        total_municipios = len(df)
        
        # Análise de valores
        if 'Valor_Municipal_Area' in df.columns:
            valores_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
            valores_validos = valores_clean[valores_clean > 0]
            
            if len(valores_validos) > 0:
                valor_total = valores_validos.sum()
                valor_medio = valores_validos.mean()
                valor_mediano = valores_validos.median()
                valor_max = valores_validos.max()
                valor_min = valores_validos.min()
                
                # Encontrar município com maior e menor valor
                idx_max = valores_clean.idxmax()
                idx_min = valores_clean[valores_clean > 0].idxmin()
                municipio_max = df.loc[idx_max, 'Municipio'] if 'Municipio' in df.columns else 'N/A'
                municipio_min = df.loc[idx_min, 'Municipio'] if 'Municipio' in df.columns else 'N/A'
                
                story.append(Paragraph("💰 ANÁLISE FINANCEIRA", highlight_style))
                story.append(Spacer(1, 5))
                
                # Criar tabela para análise financeira ao invés de parágrafos sobrepostos
                financeira_data = [
                    ['📊 MÉTRICA', '💰 VALOR'],
                    ['Valor total do mercado', formatar_valor_grande(valor_total)],
                    ['Valor médio por município', formatar_valor_grande(valor_medio)],
                    ['Valor mediano', formatar_valor_grande(valor_mediano)],
                    ['Maior valor', f"{formatar_valor_grande(valor_max)} ({municipio_max})"],
                    ['Menor valor', f"{formatar_valor_grande(valor_min)} ({municipio_min})"]
                ]
                
                # Análise de distribuição
                q1 = valores_validos.quantile(0.25)
                q3 = valores_validos.quantile(0.75)
                financeira_data.extend([
                    ['25% dos municípios valem até', formatar_valor_grande(q1)],
                    ['75% dos municípios valem até', formatar_valor_grande(q3)]
                ])
                
                financeira_table = Table(financeira_data, colWidths=[3*inch, 2.5*inch])
                financeira_table.setStyle(TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    
                    # Dados
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                    
                    # Bordas e espaçamento
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
                ]))
                
                story.append(financeira_table)
                story.append(Spacer(1, 15))
        
        # Análise populacional
        if 'Populacao' in df.columns:
            pop_clean = pd.to_numeric(df['Populacao'], errors='coerce').fillna(0)
            pop_valida = pop_clean[pop_clean > 0]
            
            if len(pop_valida) > 0:
                pop_total = pop_valida.sum()
                pop_media = pop_valida.mean()
                pop_max = pop_valida.max()
                
                # Encontrar município mais populoso
                idx_pop_max = pop_clean.idxmax()
                municipio_pop_max = df.loc[idx_pop_max, 'Municipio'] if 'Municipio' in df.columns else 'N/A'
                
                story.append(Paragraph("👥 ANÁLISE DEMOGRÁFICA", highlight_style))
                story.append(Spacer(1, 5))
                
                # Criar tabela para análise demográfica
                demografica_data = [
                    ['📊 MÉTRICA', '👥 VALOR'],
                    ['População total', f"{formatar_numero_grande(pop_total)} habitantes"],
                    ['População média', f"{formatar_numero_grande(pop_media)} habitantes"],
                    ['Maior população', f"{formatar_numero_grande(pop_max)} ({municipio_pop_max})"]
                ]
                
                # Análise de densidade populacional (se possível)
                if 'Valor_Municipal_Area' in df.columns:
                    # Calcular valor per capita médio
                    df_temp = df.copy()
                    df_temp['Pop_Clean'] = pop_clean
                    df_temp['Val_Clean'] = valores_clean
                    df_temp = df_temp[(df_temp['Pop_Clean'] > 0) & (df_temp['Val_Clean'] > 0)]
                    if not df_temp.empty:
                        df_temp['Valor_Per_Capita'] = df_temp['Val_Clean'] / df_temp['Pop_Clean']
                        valor_per_capita_medio = df_temp['Valor_Per_Capita'].mean()
                        demografica_data.append(['Valor médio per capita', formatar_valor_grande(valor_per_capita_medio)])
                
                demografica_table = Table(demografica_data, colWidths=[3*inch, 2.5*inch])
                demografica_table.setStyle(TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#38a169')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    
                    # Dados
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fff4')),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                    
                    # Bordas e espaçamento
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#c6f6d5')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
                ]))
                
                story.append(demografica_table)
    
    story.append(Spacer(1, 30))
    
    # === TOP 10 RANKING ===
    story.append(Paragraph("🏆 RANKING DOS TOP 10 MUNICÍPIOS", section_style))
    story.append(Spacer(1, 10))
    
    if 'Valor_Municipal_Area' in df.columns and 'Municipio' in df.columns:
        # Preparar dados para tabela premium
        df_ranking = df[['Municipio', 'Valor_Municipal_Area']].copy()
        
        # Adicionar população se disponível
        if 'Populacao' in df.columns:
            df_ranking['Populacao'] = df['Populacao']
        
        df_ranking['Valor_Clean'] = pd.to_numeric(df_ranking['Valor_Municipal_Area'], errors='coerce').fillna(0)
        df_ranking = df_ranking[df_ranking['Valor_Clean'] > 0].sort_values('Valor_Clean', ascending=False).head(10)
        
        # Criar tabela premium
        if 'Populacao' in df_ranking.columns:
            ranking_data = [['🥇', 'Município', 'Valor da Área', 'População', 'Valor per Capita']]
        else:
            ranking_data = [['🥇', 'Município', 'Valor da Área']]
        
        medals = ['🥇', '🥈', '🥉'] + ['🏅'] * 7
        
        for i, (_, row) in enumerate(df_ranking.iterrows()):
            medal = medals[i] if i < len(medals) else f"{i+1}º"
            
            if 'Populacao' in df_ranking.columns:
                pop_clean = pd.to_numeric(row['Populacao'], errors='coerce')
                if pd.notna(pop_clean) and pop_clean > 0:
                    per_capita = row['Valor_Clean'] / pop_clean
                    ranking_data.append([
                        medal,
                        row['Municipio'],
                        formatar_valor_grande(row['Valor_Municipal_Area']),
                        formatar_numero_grande(pop_clean),
                        formatar_valor_grande(per_capita)
                    ])
                else:
                    ranking_data.append([
                        medal,
                        row['Municipio'],
                        formatar_valor_grande(row['Valor_Municipal_Area']),
                        'N/A',
                        'N/A'
                    ])
            else:
                ranking_data.append([
                    medal,
                    row['Municipio'],
                    formatar_valor_grande(row['Valor_Municipal_Area'])
                ])
        
        # Definir larguras das colunas
        if 'Populacao' in df_ranking.columns:
            col_widths = [0.6*inch, 2.2*inch, 1.4*inch, 1*inch, 1.2*inch]
        else:
            col_widths = [0.8*inch, 3*inch, 2*inch]
        
        ranking_table = Table(ranking_data, colWidths=col_widths)
        ranking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Estilo para as primeiras 3 posições
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ffd700')),  # Ouro
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#c0c0c0')),  # Prata  
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#cd7f32')),  # Bronze
            
            # Estilo geral
            ('ALTERNATEROWBACKGROUND', (0, 4), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8)
        ]))
        
        story.append(ranking_table)
        story.append(Spacer(1, 20))
    
    story.append(PageBreak())
    
    # === GRÁFICOS E VISUALIZAÇÕES ===
    story.append(Paragraph("📊 ANÁLISES VISUAIS", section_style))
    
    # Função para criar gráfico e converter para imagem
    def create_chart_image(chart_func, width=6, height=4):
        """Cria um gráfico e retorna como imagem para o PDF"""
        try:
            fig, ax = plt.subplots(figsize=(width, height))
            chart_func(ax)
            
            # Salvar em buffer temporário
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            img_buffer.seek(0)
            return Image(img_buffer, width=width*inch, height=height*inch)
        except Exception as e:
            print(f"Erro ao criar gráfico: {e}")
            return None
    
    # GRÁFICO 1: Top 10 Municípios por Valor
    if 'Valor_Municipal_Area' in df.columns and 'Municipio' in df.columns:
        def chart_top_valores(ax):
            df_chart = df.copy()
            df_chart['Valor_Clean'] = pd.to_numeric(df_chart['Valor_Municipal_Area'], errors='coerce').fillna(0)
            top_10 = df_chart.nlargest(10, 'Valor_Clean')
            
            colors_gradient = plt.cm.Blues(np.linspace(0.4, 0.9, 10))
            bars = ax.barh(range(10), top_10['Valor_Clean'], color=colors_gradient)
            
            ax.set_yticks(range(10))
            ax.set_yticklabels([nome[:15] + '...' if len(nome) > 15 else nome 
                               for nome in top_10['Municipio']], fontsize=9)
            ax.set_xlabel('Valor Municipal (R$)', fontsize=10)
            ax.set_title('🏆 TOP 10 MUNICÍPIOS POR VALOR MUNICIPAL', fontsize=12, fontweight='bold', pad=20)
            
            # Adicionar valores nas barras
            for i, (bar, valor) in enumerate(zip(bars, top_10['Valor_Clean'])):
                ax.text(bar.get_width() + max(top_10['Valor_Clean']) * 0.01, 
                       bar.get_y() + bar.get_height()/2, 
                       formatar_valor_grande(valor), 
                       va='center', fontsize=8, fontweight='bold')
            
            ax.grid(axis='x', alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.tight_layout()
        
        chart_img = create_chart_image(chart_top_valores, width=7, height=5)
        if chart_img:
            story.append(chart_img)
            story.append(Spacer(1, 15))
    
    # GRÁFICO 2: Distribuição Populacional
    if 'Populacao' in df.columns:
        def chart_distribuicao_pop(ax):
            pop_clean = pd.to_numeric(df['Populacao'], errors='coerce').fillna(0)
            pop_valida = pop_clean[pop_clean > 0]
            
            # Criar histograma
            n, bins, patches = ax.hist(pop_valida, bins=15, color='lightblue', 
                                     edgecolor='navy', alpha=0.7)
            
            # Colorir barras com gradiente
            cm = plt.cm.viridis
            for i, (patch, value) in enumerate(zip(patches, n)):
                patch.set_facecolor(cm(value / max(n)))
            
            ax.set_xlabel('População', fontsize=10)
            ax.set_ylabel('Número de Municípios', fontsize=10)
            ax.set_title('📊 DISTRIBUIÇÃO POPULACIONAL DOS MUNICÍPIOS', 
                        fontsize=12, fontweight='bold', pad=20)
            
            # Adicionar linha da média
            media_pop = pop_valida.mean()
            ax.axvline(media_pop, color='red', linestyle='--', linewidth=2, 
                      label=f'Média: {formatar_numero_grande(media_pop)}')
            ax.legend()
            
            ax.grid(axis='y', alpha=0.3)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.tight_layout()
        
        chart_img2 = create_chart_image(chart_distribuicao_pop, width=7, height=4)
        if chart_img2:
            story.append(chart_img2)
            story.append(Spacer(1, 15))
    
    # GRÁFICO 3: Correlação População x Valor (se ambos existirem)
    if 'Populacao' in df.columns and 'Valor_Municipal_Area' in df.columns:
        def chart_correlacao(ax):
            df_scatter = df.copy()
            df_scatter['Pop_Clean'] = pd.to_numeric(df_scatter['Populacao'], errors='coerce').fillna(0)
            df_scatter['Val_Clean'] = pd.to_numeric(df_scatter['Valor_Municipal_Area'], errors='coerce').fillna(0)
            df_scatter = df_scatter[(df_scatter['Pop_Clean'] > 0) & (df_scatter['Val_Clean'] > 0)]
            
            if len(df_scatter) > 3:
                scatter = ax.scatter(df_scatter['Pop_Clean'], df_scatter['Val_Clean'], 
                                   alpha=0.6, s=60, c=range(len(df_scatter)), 
                                   cmap='viridis', edgecolors='black', linewidth=0.5)
                
                # Linha de tendência
                z = np.polyfit(df_scatter['Pop_Clean'], df_scatter['Val_Clean'], 1)
                p = np.poly1d(z)
                ax.plot(df_scatter['Pop_Clean'], p(df_scatter['Pop_Clean']), 
                       "r--", alpha=0.8, linewidth=2)
                
                # Calcular R²
                correlation = df_scatter['Pop_Clean'].corr(df_scatter['Val_Clean'])
                ax.set_title(f'💹 CORRELAÇÃO POPULAÇÃO × VALOR MUNICIPAL\n(R = {correlation:.3f})', 
                           fontsize=12, fontweight='bold', pad=20)
                
                ax.set_xlabel('População', fontsize=10)
                ax.set_ylabel('Valor Municipal (R$)', fontsize=10)
                
                # Destacar top 3 municípios
                top_3 = df_scatter.nlargest(3, 'Val_Clean')
                for _, row in top_3.iterrows():
                    ax.annotate(row['Municipio'][:10], 
                              (row['Pop_Clean'], row['Val_Clean']),
                              xytext=(5, 5), textcoords='offset points',
                              fontsize=8, fontweight='bold',
                              bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
                
                ax.grid(True, alpha=0.3)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                plt.tight_layout()
        
        chart_img3 = create_chart_image(chart_correlacao, width=7, height=5)
        if chart_img3:
            story.append(chart_img3)
            story.append(Spacer(1, 20))
    
    # Nova página para análises detalhadas
    story.append(PageBreak())
    
    # === ANÁLISES DETALHADAS ===
    story.append(Paragraph("📈 ANÁLISES DETALHADAS", section_style))
    
    # Análise de qualidade (notas)
    if any(col.startswith('Nota') for col in df.columns):
        story.append(Paragraph("⭐ INDICADORES DE QUALIDADE", highlight_style))
        
        nota_cols = [col for col in df.columns if col.startswith('Nota')]
        quality_data = [['Indicador', 'Mín.', 'Máx.', 'Média', 'Top Município']]
        
        for col in nota_cols[:6]:  # Top 6 indicadores
            values = pd.to_numeric(df[col], errors='coerce').dropna()
            if not values.empty:
                max_idx = values.idxmax()
                top_municipio = df.loc[max_idx, 'Municipio'] if 'Municipio' in df.columns else 'N/A'
                
                quality_data.append([
                    col.replace('_', ' ').replace('Nota ', ''),
                    f"{values.min():.2f}".replace('.', ','),
                    f"{values.max():.2f}".replace('.', ','),
                    f"{values.mean():.2f}".replace('.', ','),
                    top_municipio
                ])
        
        quality_table = Table(quality_data, colWidths=[1.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 2*inch])
        quality_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('ALTERNATEROWBACKGROUND', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ebf8ff')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6)
        ]))
        
        story.append(quality_table)
        story.append(Spacer(1, 15))
    
    # === INSIGHTS E RECOMENDAÇÕES ===
    story.append(Paragraph("🧠 INSIGHTS E RECOMENDAÇÕES", section_style))
    
    # Gerar insights automáticos baseados nos dados
    insights = []
    
    if 'Valor_Municipal_Area' in df.columns:
        valores_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
        valores_validos = valores_clean[valores_clean > 0]
        
        if len(valores_validos) > 0:
            cv = valores_validos.std() / valores_validos.mean()  # Coeficiente de variação
            
            if cv > 1:
                insights.append("📊 Alta variabilidade nos valores municipais indica oportunidades diversificadas de investimento.")
            elif cv < 0.3:
                insights.append("📊 Baixa variabilidade nos valores sugere um mercado mais homogêneo e estável.")
            
            # Análise de concentração
            top_10_percent = valores_validos.quantile(0.9)
            high_value_count = len(valores_validos[valores_validos >= top_10_percent])
            
            if high_value_count <= len(valores_validos) * 0.05:
                insights.append("🎯 Mercado concentrado: poucos municípios representam a maior parte do valor total.")
            
            # Análise de oportunidades
            median_val = valores_validos.median()
            cheap_opportunities = len(valores_validos[valores_validos <= median_val * 0.5])
            
            if cheap_opportunities > 0:
                insights.append(f"� Identificadas {cheap_opportunities} oportunidades de investimento com valores abaixo da média do mercado.")
    
    # Insight populacional
    if 'Populacao' in df.columns and 'Valor_Municipal_Area' in df.columns:
        pop_clean = pd.to_numeric(df['Populacao'], errors='coerce').fillna(0)
        
        # Calcular correlação população x valor
        df_corr = pd.DataFrame({
            'pop': pop_clean,
            'val': pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
        })
        df_corr = df_corr[(df_corr['pop'] > 0) & (df_corr['val'] > 0)]
        
        if len(df_corr) > 3:
            correlation = df_corr['pop'].corr(df_corr['val'])
            
            if correlation > 0.7:
                insights.append("👥 Forte correlação positiva entre população e valor municipal indica mercados populacionais valorizados.")
            elif correlation < 0.3:
                insights.append("🎯 Baixa correlação população-valor sugere oportunidades em municípios menos populosos.")
    
    # Adicionar insights ao relatório
    for insight in insights[:5]:  # Top 5 insights
        story.append(Paragraph(insight, insight_style))
    
    story.append(Spacer(1, 20))
    
    # === QUADRO RESUMO EXECUTIVO ===
    story.append(Paragraph("📋 QUADRO RESUMO EXECUTIVO", section_style))
    
    # Criar resumo visual final
    if 'Valor_Municipal_Area' in df.columns:
        valores_clean = pd.to_numeric(df['Valor_Municipal_Area'], errors='coerce').fillna(0)
        valores_validos = valores_clean[valores_clean > 0]
        
        if len(valores_validos) > 0:
            # Dados para o quadro resumo
            resumo_data = [
                ['📊 INDICADOR', '📈 VALOR', '🎯 STATUS'],
                [
                    'Mercado Total', 
                    formatar_valor_grande(valores_validos.sum()),
                    '🟢 Consolidado' if len(valores_validos) > 50 else '🟡 Em Desenvolvimento'
                ],
                [
                    'Ticket Médio', 
                    formatar_valor_grande(valores_validos.mean()),
                    '🟢 Atrativo' if valores_validos.mean() > valores_validos.median() * 1.2 else '🟡 Estável'
                ],
                [
                    'Oportunidades (<Q1)', 
                    f"{len(valores_validos[valores_validos <= valores_validos.quantile(0.25)])} municípios",
                    '🟢 Alto Potencial' if len(valores_validos[valores_validos <= valores_validos.quantile(0.25)]) > 10 else '🟡 Moderado'
                ],
                [
                    'Municípios Premium (>Q3)', 
                    f"{len(valores_validos[valores_validos >= valores_validos.quantile(0.75)])} municípios",
                    '💎 Mercado VIP'
                ],
                [
                    'Volatilidade do Mercado',
                    f"{(valores_validos.std() / valores_validos.mean()):.1%}",
                    '🟢 Baixa' if (valores_validos.std() / valores_validos.mean()) < 0.5 
                    else '🟡 Moderada' if (valores_validos.std() / valores_validos.mean()) < 1.0 
                    else '🔴 Alta'
                ]
            ]
            
            resumo_table = Table(resumo_data, colWidths=[2.2*inch, 2*inch, 1.8*inch])
            resumo_table.setStyle(TableStyle([
                # Cabeçalho especial
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a202c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Cores alternadas mais elegantes
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e6fffa')),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f0fff4')),
                ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#fef5e7')),
                ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#faf5ff')),
                ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#fffbf0')),
                
                # Estilo do texto
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # Primeira coluna em negrito
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                
                # Bordas e espaçamento
                ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#4a5568')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
            ]))
            
            story.append(resumo_table)
            story.append(Spacer(1, 20))
    
    # === CONCLUSÕES E PRÓXIMOS PASSOS ===
    story.append(Paragraph("🚀 CONCLUSÕES E PRÓXIMOS PASSOS", section_style))
    
    conclusoes_text = """
    <b>🎯 CONCLUSÃO PRINCIPAL:</b><br/>
    Com base na análise abrangente dos dados municipais de Alagoas, identificamos um mercado 
    robusto com oportunidades claras de investimento e crescimento, apresentando características 
    distintas que permitem estratégias direcionadas.<br/><br/>
    
    <b>📈 PRÓXIMOS PASSOS RECOMENDADOS:</b><br/>
    • <b>Fase 1:</b> Análise detalhada dos municípios do 1º quartil para identificação de oportunidades<br/>
    • <b>Fase 2:</b> Desenvolvimento de estratégias específicas para municípios premium<br/>
    • <b>Fase 3:</b> Implementação de monitoramento contínuo dos indicadores-chave<br/>
    • <b>Fase 4:</b> Diversificação de portfólio baseada nas correlações identificadas<br/><br/>
    
    <b>⚡ AÇÕES IMEDIATAS:</b><br/>
    • Priorizar municípios com melhor relação valor/população<br/>
    • Estabelecer parcerias estratégicas com municípios de alto potencial<br/>
    • Desenvolver métricas de acompanhamento customizadas
    """
    
    story.append(Paragraph(conclusoes_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # === METODOLOGIA E OBSERVAÇÕES ===
    story.append(Paragraph("📋 METODOLOGIA E OBSERVAÇÕES TÉCNICAS", section_style))
    
    metodologia_text = """
    Este relatório foi gerado automaticamente através de análise estatística avançada dos dados 
    municipais de Alagoas. As métricas incluem análises de tendência central, dispersão e 
    correlação entre variáveis demográficas e econômicas.
    
    <b>Fontes de Dados:</b> Base oficial de dados municipais de Alagoas<br/>
    <b>Período de Análise:</b> Dados mais recentes disponíveis<br/>
    <b>Metodologia:</b> Análise estatística descritiva e inferencial<br/>
    <b>Geração:</b> Sistema automatizado com IA para insights
    """
    
    story.append(Paragraph(metodologia_text, styles['Normal']))
    
    # === RODAPÉ PREMIUM ===
    story.append(Spacer(1, 40))
    
    # Linha separadora elegante
    separator_table = Table([['_' * 80]], colWidths=[6*inch])
    separator_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#cbd5e0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 12)
    ]))
    story.append(separator_table)
    story.append(Spacer(1, 15))
    
    # Informações do documento
    footer_info_data = [
        ['📊 DASHBOARD DE PRECIFICAÇÃO MUNICIPAL', '🏛️ GOVERNO DE ALAGOAS'],
        ['🤖 Relatório Gerado por Inteligência Artificial', '📈 Análise de Dados Avançada'],
        [f'📅 {datetime.now().strftime("%d de %B de %Y às %H:%M")}', f'📄 Documento #{datetime.now().strftime("%Y%m%d%H%M")}']
    ]
    
    footer_table = Table(footer_info_data, colWidths=[3*inch, 3*inch])
    footer_table.setStyle(TableStyle([
        # Primeira linha (título)
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Segunda linha (subtítulo)
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 1), 9),
        
        # Terceira linha (data)
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#4a5568')),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica'),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        
        # Estilo geral
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#4a5568')),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
    ]))
    
    story.append(footer_table)
    
    # Nota de confidencialidade
    story.append(Spacer(1, 15))
    confidencial_text = """
    <i>Este documento contém análises estratégicas baseadas em dados oficiais. 
    Todas as informações foram processadas através de algoritmos de inteligência artificial 
    para garantir precisão e insights relevantes para tomada de decisão.</i>
    """
    
    confidencial_style = ParagraphStyle(
        'Confidencial',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096'),
        fontName='Helvetica-Oblique',
        alignment=1,  # Centralizado
        spaceAfter=10
    )
    
    story.append(Paragraph(confidencial_text, confidencial_style))
    
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
    
    # Filtro por população - usando clean_brazilian_number para garantir conversão correta
    if 'Populacao' in df_filtered.columns:
        pop_clean = df_filtered['Populacao'].apply(clean_brazilian_number).fillna(0)
        df_filtered = df_filtered[
            (pop_clean >= pop_range[0]) & (pop_clean <= pop_range[1])
        ]
    
    # Filtro por nota média
    if 'Nota_Media' in df_filtered.columns:
        nota_clean = pd.to_numeric(df_filtered['Nota_Media'], errors='coerce').fillna(0)
        df_filtered = df_filtered[
            (nota_clean >= nota_range[0]) & (nota_clean <= nota_range[1])
        ]
    
    # Filtro por valor municipal - usando clean_brazilian_number para garantir conversão correta
    if 'Valor_Municipal_Area' in df_filtered.columns:
        valor_clean = df_filtered['Valor_Municipal_Area'].apply(clean_brazilian_number).fillna(0)
        # valor_range já vem convertido para valores absolutos
        df_filtered = df_filtered[
            (valor_clean >= valor_range[0]) & (valor_clean <= valor_range[1])
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
    # Header principal centralizado e bonito
    st.markdown("""
    <div class="header-container">
        <h1 class="main-header">🏘️ Dashboard de Precificação<br>Municípios de Alagoas</h1>
        <p class="header-subtitle">Sistema de Análise e Monitoramento de Dados Municipais</p>
    </div>
    """, unsafe_allow_html=True)
    
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
        st.markdown("### Filtros")
        
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
            # Usar clean_brazilian_number para garantir conversão correta
            pop_clean = df['Populacao'].apply(clean_brazilian_number).fillna(0)
            pop_valid = pop_clean[pop_clean > 0]
            
            if not pop_valid.empty:
                pop_min, pop_max = int(pop_valid.min()), int(pop_valid.max())
                
                # Converter para milhares para facilitar visualização
                pop_min_k = pop_min / 1000
                pop_max_k = pop_max / 1000
                
                # Garantir que min < max com tolerância mínima
                if pop_max_k - pop_min_k < 1.0:
                    # Se a diferença é muito pequena, adicionar range artificial
                    pop_max_k = pop_min_k + 10.0  # Adicionar 10K habitantes como range mínimo
                
                pop_range_k = st.slider(
                    "👥 População (em milhares)",
                    min_value=pop_min_k,
                    max_value=pop_max_k,
                    value=(pop_min_k, pop_max_k),
                    step=1.0,
                    key="pop_range",
                    format="%.0fK"
                )
                # Converter de volta para valores absolutos
                pop_range = (int(pop_range_k[0] * 1000), int(pop_range_k[1] * 1000))
        
        # Nota média
        if 'Nota_Media' in df.columns:
            nota_clean = pd.to_numeric(df['Nota_Media'], errors='coerce').fillna(0)
            nota_valid = nota_clean[nota_clean > 0]
            
            if not nota_valid.empty:
                nota_min, nota_max = float(nota_valid.min()), float(nota_valid.max())
                
                # Garantir que min < max com tolerância mínima
                if nota_max - nota_min < 0.1:
                    # Se a diferença é muito pequena, adicionar range artificial
                    nota_max = min(nota_min + 1.0, 10.0)  # Adicionar 1 ponto ou até 10
                
                nota_range = st.slider(
                    "⭐ Nota",
                    min_value=nota_min,
                    max_value=nota_max,
                    value=(nota_min, nota_max),
                    step=0.1,
                    key="nota_range"
                )
            else:
                st.info("Dados de nota não disponíveis")
                nota_range = (0, 10)
        
        # Valor por área
        if 'Valor_Municipal_Area' in df.columns:
            # Usar clean_brazilian_number para garantir conversão correta
            area_values = df['Valor_Municipal_Area'].apply(clean_brazilian_number).fillna(0)
            area_valid = area_values[area_values > 0]
            
            if not area_valid.empty:
                valor_min, valor_max = float(area_valid.min()), float(area_valid.max())
                valor_min_bi = valor_min / 1_000_000_000
                valor_max_bi = valor_max / 1_000_000_000
                
                # Garantir que min < max com tolerância mínima
                if valor_max_bi - valor_min_bi < 0.1:
                    # Se a diferença é muito pequena, adicionar range artificial
                    valor_max_bi = valor_min_bi + 1.0  # Adicionar 1 bilhão como range mínimo
                
                valor_range_bi = st.slider(
                    "💰 Valor Municipal (R$ bilhões)",
                    min_value=valor_min_bi,
                    max_value=valor_max_bi,
                    value=(valor_min_bi, valor_max_bi),
                    step=0.1,
                    key="valor_range",
                    format="R$ %.1fB"
                )
                # Converter de volta para valores absolutos
                valor_range = (valor_range_bi[0] * 1_000_000_000, valor_range_bi[1] * 1_000_000_000)
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
        
        st.markdown("---")
        
        # Botão limpar
        if st.button("🗑️ Limpar", type="secondary"):
            keys_to_clear = ['municipios_selecionados', 'busca_texto', 'pop_range', 'nota_range', 'valor_range', 'show_top_only']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    # Aplica filtros
    df_original = df.copy()  # Manter cópia original para estatísticas
    
    # Obter valores dos filtros do session_state
    municipios_selecionados = st.session_state.get('municipios_selecionados', [])
    busca_texto = st.session_state.get('busca_texto', "")
    show_top_only = st.session_state.get('show_top_only', "Todos")
    
    # Converter os valores dos sliders para usar na filtragem
    # População - converter de volta de milhares para valores absolutos
    if 'pop_range' in st.session_state:
        pop_range_k = st.session_state['pop_range']
        pop_range_val = (int(pop_range_k[0] * 1000), int(pop_range_k[1] * 1000))
    else:
        if 'Populacao' in df.columns:
            pop_clean = df['Populacao'].apply(clean_brazilian_number).fillna(0)
            pop_valid = pop_clean[pop_clean > 0]
            if not pop_valid.empty:
                pop_range_val = (int(pop_valid.min()), int(pop_valid.max()))
            else:
                pop_range_val = (0, 0)
        else:
            pop_range_val = (0, 0)
    
    # Nota média - usar diretamente
    if 'nota_range' in st.session_state:
        nota_range_val = st.session_state['nota_range']
    else:
        if 'Nota_Media' in df.columns:
            nota_clean = pd.to_numeric(df['Nota_Media'], errors='coerce').fillna(0)
            nota_range_val = (float(nota_clean.min()), float(nota_clean.max()))
        else:
            nota_range_val = (0, 0)
    
    # Valor municipal - converter de bilhões para valores absolutos
    if 'valor_range' in st.session_state:
        valor_range_bi = st.session_state['valor_range']
        valor_range_val = (valor_range_bi[0] * 1_000_000_000, valor_range_bi[1] * 1_000_000_000)
    else:
        if 'Valor_Municipal_Area' in df.columns:
            valor_clean = df['Valor_Municipal_Area'].apply(clean_brazilian_number).fillna(0)
            valor_valid = valor_clean[valor_clean > 0]
            if not valor_valid.empty:
                valor_range_val = (float(valor_valid.min()), float(valor_valid.max()))
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
    
    # Usar dados filtrados para todas as visualizações
    df = df_filtered
    
    # Métricas de visão geral
    st.markdown("## 📈 Visão Geral")
    create_overview_metrics(df)
    
    st.markdown("---")
    
    # Tabs para diferentes análises focadas em precificação
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Mapa Interativo", "Ranking de Valores", "Análise Comparativa", "Distribuição de Preços", "Consultor de Dados", "Recomendação AI", "📄 Gerar PDF Personalizado"])
    
    with tab1:
        st.markdown("### Mapa Interativo dos Municípios")
        st.markdown("Visualize os municípios de Alagoas com dados de precificação. As cores dos marcadores representam diferentes faixas de valores.")
        
        # Criar e exibir o mapa em tela cheia
        if 'Valor_Municipal_Area' in df_filtered.columns:
            try:
                interactive_map = create_interactive_map(df_filtered)
                # Mapa ocupando toda a largura da tela
                st_folium(interactive_map, height=600, width='stretch')
                
                # Estatísticas do mapa
                st.markdown("#### 📊 Estatísticas do Mapa")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_municipios = len(df_filtered)
                    st.metric("Total de Municípios", total_municipios)
                
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
            st.warning("Dados de valor municipal não disponíveis para o mapa.")

    with tab2:
        st.markdown("### Ranking dos Municípios por Valor")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_ranking = create_value_ranking_chart(df_filtered)
            if fig_ranking:
                st.plotly_chart(fig_ranking, width='stretch')
        
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
        st.markdown("### Dados Detalhados")
        if 'Municipio' in df_filtered.columns and 'Valor_Municipal_Area' in df_filtered.columns:
            display_df = df_filtered[['Municipio', 'Valor_Municipal_Area', 'Valor_Municipal_Perimetro']].copy()
            display_df['Valor_Area_Limpo'] = display_df['Valor_Municipal_Area'].apply(clean_brazilian_number)
            display_df['Valor_Perim_Limpo'] = display_df['Valor_Municipal_Perimetro'].apply(clean_brazilian_number)
            display_df = display_df.sort_values('Valor_Area_Limpo', ascending=False)
            
            # Formata para exibição
            display_df['Valor Área (R$ Mi)'] = (display_df['Valor_Area_Limpo'] / 1_000_000).round(1)
            display_df['Valor Perímetro (R$ Mi)'] = (display_df['Valor_Perim_Limpo'] / 1_000_000).round(2)
            
            final_df = display_df[['Municipio', 'Valor Área (R$ Mi)', 'Valor Perímetro (R$ Mi)']]
            st.dataframe(final_df, width='stretch')

    with tab3:
        st.markdown("### Análise: Valor vs População")
        
        fig_comparison = create_value_per_population_chart(df_filtered)
        if fig_comparison:
            st.plotly_chart(fig_comparison, width='stretch')
        
        # Análise de correlação específica
        st.markdown("### Correlação entre Valores")
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
                    st.metric("Correlação", f"{correlation:.3f}")
                with col2:
                    st.metric("Dados Válidos", f"{len(valid_data)}")
                with col3:
                    ratio_medio = (valid_data['Area'] / valid_data['Perimetro']).mean()
                    st.metric("Ratio Médio (Área/Perímetro)", f"{ratio_medio:.2f}".replace('.', ','))
    
    with tab4:
        st.markdown("# � Distribuição de Preços")
        st.markdown("---")
        
        # Métricas gerais
        if 'Valor_Municipal_Area' in df_filtered.columns:
            valores_clean = df_filtered['Valor_Municipal_Area'].apply(clean_brazilian_number)
            valores_valid = valores_clean.dropna()
            
            if not valores_valid.empty:
                # Converte para bilhões para as métricas
                valores_bi = valores_valid / 1_000_000_000
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Valor Total", f"R$ {valores_bi.sum():.1f}B".replace('.', ','))
                with col2:
                    st.metric("Valor Médio", f"R$ {valores_bi.mean():.1f}B".replace('.', ','))
                with col3:
                    st.metric("Valor Máximo", f"R$ {valores_bi.max():.1f}B".replace('.', ','))
                with col4:
                    st.metric("Municípios", f"{len(valores_valid)}")
        
        st.markdown("---")
        
        # Layout em duas colunas para os gráficos principais
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de distribuição principal
            fig_distribution = create_price_distribution_chart(df_filtered)
            if fig_distribution:
                st.plotly_chart(fig_distribution, width='stretch')
                
        with col2:
            # Boxplot para mostrar estatísticas
            fig_boxplot = create_price_boxplot(df_filtered)
            if fig_boxplot:
                st.plotly_chart(fig_boxplot, width='stretch')
        
        # Gráfico de dispersão (linha completa)
        st.markdown("### Relação Valor vs População")
        fig_scatter = create_price_by_population_chart(df_filtered)
        if fig_scatter:
            st.plotly_chart(fig_scatter, width='stretch')
        else:
            st.info("💡 Dados de população necessários para análise comparativa.")
        
        st.markdown("---")
        
        # Análise por faixas de preço
        st.markdown("### Análise por Faixas de Preço")
        if 'Valor_Municipal_Area' in df_filtered.columns:
            valores_clean = df_filtered['Valor_Municipal_Area'].apply(clean_brazilian_number)
            valores_valid = valores_clean.dropna()
            
            if not valores_valid.empty:
                # Converte para bilhões
                valores_bi = valores_valid / 1_000_000_000
                
                # Define faixas melhoradas
                faixas = {
                    "Baixo (< 5B)": (valores_bi < 5).sum(),
                    "Médio (5B - 15B)": ((valores_bi >= 5) & (valores_bi < 15)).sum(),
                    "Alto (15B - 25B)": ((valores_bi >= 15) & (valores_bi < 25)).sum(),
                    "Premium (≥ 25B)": (valores_bi >= 25).sum()
                }
                
                # Layout das faixas
                col1, col2, col3, col4 = st.columns(4)
                cols = [col1, col2, col3, col4]
                
                for i, (faixa, count) in enumerate(faixas.items()):
                    with cols[i]:
                        percentage = (count / len(valores_bi) * 100) if len(valores_bi) > 0 else 0
                        st.metric(
                            faixa, 
                            f"{count} municípios", 
                            f"{percentage:.1f}% do total".replace('.', ',')
                        )
                
                # Gráfico de pizza das faixas
                st.markdown("### Distribuição por Faixas")
                
                # Cria dados para o gráfico de pizza
                labels = list(faixas.keys())
                values = list(faixas.values())
                
                # Remove faixas vazias
                filtered_data = [(label, value) for label, value in zip(labels, values) if value > 0]
                
                if filtered_data:
                    labels_filtered, values_filtered = zip(*filtered_data)
                    
                    fig_pie = px.pie(
                        values=values_filtered,
                        names=labels_filtered,
                        title="Distribuição de Municípios por Faixa de Valor",
                        color_discrete_sequence=['#00D4AA', '#FFD700', '#FF8C00', '#FF6B6B']
                    )
                    
                    fig_pie.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>' +
                                      'Municípios: %{value}<br>' +
                                      'Percentual: %{percent}<br>' +
                                      '<extra></extra>'
                    )
                    
                    fig_pie.update_layout(
                        height=400,
                        title_font_size=16,
                        title_x=0.5,
                        font=dict(size=12),
                        margin=dict(l=60, r=60, t=80, b=60)
                    )
                    
                    st.plotly_chart(fig_pie, width='stretch')
                
        else:
            st.warning("⚠️ Dados de valor municipal não disponíveis para análise de faixas.")

    # Tab 5: Consultor de Dados
    with tab5:
        st.markdown("# Construtor de Consultas")
        create_query_builder_interface(df_filtered)

    # Tab 6: Recomendação AI
    with tab6:
        st.markdown("### 🤖 Sistema de Recomendação Inteligente")
        st.markdown("Nosso algoritmo de IA analisa seus critérios e recomenda os melhores municípios para seu perfil de investimento.")
        
        # Interface de preferências
        preferences = create_recommendation_interface(df_filtered)
        
        # Botão para gerar recomendações
        if st.button("🚀 Gerar Recomendações", type="primary", key="ai_recommendations"):
            with st.spinner("🤖 Analisando dados e gerando recomendações personalizadas..."):
                # Gerar recomendações
                recommendations = get_smart_recommendations(df_filtered, preferences, top_n=5)
                
                # Exibir recomendações
                display_recommendations(recommendations, df_filtered)
                
                # Estatísticas das recomendações
                if recommendations:
                    st.markdown("### 📊 Resumo das Recomendações")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        avg_score = sum([r['score'] for r in recommendations]) / len(recommendations)
                        st.metric("Score Médio", f"{avg_score:.1f}/100")
                    
                    with col2:
                        valores = [r['data'].get('Valor_Municipal_Area', 0) for r in recommendations]
                        avg_valor = sum(valores) / len(valores) if valores else 0
                        st.metric("Valor Médio", formatar_valor_grande(avg_valor))
                    
                    with col3:
                        populacoes = [r['data'].get('Populacao', 0) for r in recommendations]
                        avg_pop = sum(populacoes) / len(populacoes) if populacoes else 0
                        st.metric("Pop. Média", formatar_valor_grande(avg_pop))
                    
                    with col4:
                        notas = [r['data'].get('Nota_Media', 0) for r in recommendations]
                        avg_nota = sum(notas) / len(notas) if notas else 0
                        st.metric("Nota Média", f"{avg_nota:.1f}")
                    
                    # Gráfico comparativo dos top 5
                    st.markdown("### 📈 Comparação Visual dos Top 5")
                    
                    municipios = [r['municipio'] for r in recommendations]
                    scores = [r['score'] for r in recommendations]
                    
                    fig_comparison = px.bar(
                        x=municipios,
                        y=scores,
                        title="Scores de Recomendação por Município",
                        labels={'x': 'Município', 'y': 'Score (0-100)'},
                        color=scores,
                        color_continuous_scale='Viridis'
                    )
                    
                    fig_comparison.update_layout(
                        xaxis_tickangle=-45,
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_comparison, width='stretch')
    
    # Tab 7: PDF Personalizado
    with tab7:
        st.markdown("# 🎯 Gerador de PDF Personalizado")
        
        # Status dos dados - mais compacto
        if len(df) != len(df_original):
            st.info(f"📊 Trabalhando com **{len(df):,}** municípios filtrados de {len(df_original):,} total".replace(',', '.'))
        else:
            st.info(f"📊 Trabalhando com **{len(df):,}** municípios (dados completos)".replace(',', '.'))
        
        st.markdown("---")
        
        # CONFIGURAÇÕES PRINCIPAIS
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            st.markdown("**⚙️ Configurações**")
            # Aplicar filtros ou usar dados completos  
            usar_filtros = st.radio(
                "Dados:",
                ["Usar dados filtrados atuais", "Usar todos os dados"],
                help="Escolha quais dados incluir no PDF"
            )
            
            # Título personalizado
            titulo_personalizado = st.text_input(
                "Título:",
                value="Relatório Municipal - Alagoas",
                help="Título da capa"
            )
        
        with col_config2:
            st.markdown("**🎯 Opções do Ranking**")
            # Configurações de ranking
            top_municipios_count = st.slider(
                "Qtd no ranking:",
                min_value=5, max_value=15, value=10
            )
            
            criterio_ranking = st.selectbox(
                "Critério:",
                ["Valor Municipal", "População", "Valor per Capita"]
            )
        
        st.markdown("---")
        
        # CONTEÚDO DO RELATÓRIO - Simplificado
        st.markdown("**📋 O que incluir no PDF:**")
        
        col_content1, col_content2 = st.columns(2)
        
        with col_content1:
            incluir_capa = st.checkbox("🏛️ Capa Premium", value=True)
            incluir_resumo_executivo = st.checkbox("📈 Resumo Executivo", value=True)
            incluir_ranking = st.checkbox("🏆 Ranking", value=True)
            incluir_graficos = st.checkbox("📊 Gráficos", value=True)
        
        with col_content2:
            incluir_insights = st.checkbox("🧠 Insights", value=True)
            incluir_recomendacoes = st.checkbox("🎯 Recomendações", value=True)
            incluir_estatisticas = st.checkbox("� Estatísticas", value=True)
            incluir_metodologia = st.checkbox("📋 Metodologia", value=False)
        
        # Mostrar status dos dados de forma concisa
        if len(df) != len(df_original):
            st.success(f"📊 **{len(df):,}** registros filtrados de **{len(df_original):,}** total".replace(',', '.'))
        else:
            st.info(f"� **{len(df):,}** registros (todos os dados)".replace(',', '.'))
        
        col_config, col_info = st.columns([1, 1])
        
        with col_config:
            st.markdown("### Configuração")
            
            # Definir colunas padrão
            colunas_padrao = []
            if 'Municipio' in df.columns:
                colunas_padrao.append('Municipio')
            if 'População' in df.columns:
                colunas_padrao.append('População')
            if 'Valor_Municipal_Area' in df.columns:
                colunas_padrao.append('Valor_Municipal_Area')
            if 'Nota_Media' in df.columns:
                colunas_padrao.append('Nota_Media')
            
            # Se não encontrou as colunas padrão, usar as 5 primeiras
            if not colunas_padrao:
                colunas_padrao = df.columns[:5].tolist()
            
            # Seleção de colunas
            show_cols = st.multiselect(
                "Colunas para Exportar",
                options=df.columns.tolist(),
                default=colunas_padrao,
                key="export_columns_selector"
            )
            
            # Opções de exportação
            incluir_todos_dados = st.checkbox(
                "Incluir dados completos (sem filtros)"
            )
        
        st.markdown("---")
        
        # Visualização dos dados primeiro
        tab_view1, tab_view2 = st.tabs(["📋 Tabela", "📈 Estatísticas"])
        
        with tab_view1:
            if len(df) > 0 and show_cols:
                # Criar DataFrame formatado para exibição
                df_formatado_completo = formatar_dataframe_para_exibicao(df[show_cols], show_cols)
                st.dataframe(
                    df_formatado_completo, 
                    width='stretch',
                    height=500
                )
            elif not show_cols:
                st.warning("Selecione colunas para visualizar")
            else:
                st.info("Configure os filtros para visualizar dados")
        
        with tab_view2:
            if len(df) > 0:
                # Identificar colunas numéricas
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                
                if numeric_cols:
                    stats_df = df[numeric_cols].describe()
                    
                    # Criar DataFrame formatado para estatísticas
                    stats_formatadas = pd.DataFrame(index=stats_df.index)
                    
                    for coluna in stats_df.columns:
                        if ('Valor_Municipal' in coluna or 'valor_municipal' in coluna.lower() or 
                            any(palavra in coluna.lower() for palavra in ['preco', 'valor', 'custo', 'receita'])):
                            # Se os valores são muito grandes, formatá-los
                            if stats_df[coluna].max() > 1_000_000:
                                stats_formatadas[coluna] = [
                                    formatar_valor_grande(valor) if pd.notna(valor) else 'N/A' 
                                    for valor in stats_df[coluna]
                                ]
                            else:
                                stats_formatadas[coluna] = stats_df[coluna]
                        else:
                            stats_formatadas[coluna] = stats_df[coluna]
                    
                    st.dataframe(stats_formatadas, width='stretch')
                else:
                    st.warning("Nenhuma coluna numérica encontrada")
            else:
                st.info("Aplique filtros para ver estatísticas")
        
        st.markdown("---")
        
        st.markdown("---")
        
        # PREVIEW COMPACTO
        df_para_pdf = df if usar_filtros == "Usar dados filtrados atuais" else df_original
        
        # Contar seções selecionadas
        secoes_selecionadas = []
        if incluir_capa: secoes_selecionadas.append("Capa")
        if incluir_resumo_executivo: secoes_selecionadas.append("Resumo")
        if incluir_ranking: secoes_selecionadas.append("Ranking")
        if incluir_graficos: secoes_selecionadas.append("Gráficos")
        if incluir_insights: secoes_selecionadas.append("Insights")
        if incluir_recomendacoes: secoes_selecionadas.append("Recomendações")
        if incluir_estatisticas: secoes_selecionadas.append("Estatísticas")
        if incluir_metodologia: secoes_selecionadas.append("Metodologia")
        
        col_preview1, col_preview2 = st.columns(2)
        with col_preview1:
            st.success(f"📄 {len(secoes_selecionadas)} seções • {len(df_para_pdf)} municípios")
        with col_preview2:
            tipo_dados = "Filtrados" if usar_filtros == "Usar dados filtrados atuais" else "Todos"
            st.info(f"🏆 Top {top_municipios_count} • Dados {tipo_dados}")
        
        st.markdown("---")
        
        # GERAÇÃO DO PDF
        if len(df_para_pdf) == 0:
            st.error("❌ Nenhum dado disponível. Ajuste os filtros.")
        else:
            if st.button("🎯 GERAR PDF PERSONALIZADO", type="primary", use_container_width=True):
                with st.spinner("🔄 Gerando relatório..."):
                    try:
                        pdf_personalizado = generate_pdf_report(df_para_pdf)
                        
                        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"relatorio_{len(df_para_pdf)}municipios_{timestamp}.pdf"
                        
                        st.success("✅ PDF gerado!")
                        
                        st.download_button(
                            label="📥 BAIXAR PDF",
                            data=pdf_personalizado,
                            file_name=filename,
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
                        st.info("💡 Tente desmarcar algumas opções de gráficos.")
        
        # Dicas e informações adicionais
        st.markdown("---")
        st.markdown("## 💡 Dicas para um PDF Perfeito")
        
        tips_col1, tips_col2 = st.columns(2)
        
        with tips_col1:
            st.markdown("""
            **🎯 Para Relatórios Executivos:**
            - Mantenha Capa, Resumo e Ranking
            - Inclua Insights e Recomendações
            - Use dados filtrados para foco específico
            """)
        
        with tips_col2:
            st.markdown("""
            **📊 Para Relatórios Técnicos:**
            - Inclua todas as Estatísticas e Gráficos
            - Adicione Metodologia
            - Use dados completos para análise abrangente
            """)
        
        st.info("💡 **Dica:** Relatórios com muitos gráficos podem demorar mais para gerar, mas ficam mais impactantes!")
        
        # Downloads Complementares
        st.markdown("---")
        st.markdown("## 📊 Downloads Complementares")
        
        col_export1, col_export2, col_export3 = st.columns(3)
        
        with col_export1:
            st.markdown("**📄 Download Rápido**")
            if len(df_para_pdf) > 0:
                # CSV essencial
                colunas_essenciais = ['Municipio', 'População', 'Valor_Municipal_Area']
                colunas_disponiveis = [col for col in colunas_essenciais if col in df_para_pdf.columns]
                
                if colunas_disponiveis:
                    csv_simples = df_para_pdf[colunas_disponiveis].to_csv(index=False)
                    st.download_button(
                        label="📊 CSV Dados",
                        data=csv_simples,
                        file_name=f"dados_{pd.Timestamp.now().strftime('%H%M')}.csv",
                        mime="text/csv"
                    )
            else:
                st.info("Sem dados disponíveis")
        
        with col_export2:
            st.markdown("**🎯 Dica**")
            st.info("💡 Para relatórios executivos: mantenha Capa, Resumo e Ranking")
        
        with col_export3:
            st.markdown("**📊 Status**")
            if len(secoes_selecionadas) >= 4:
                st.success("✅ Relatório completo")
            else:
                st.warning("⚠️ Relatório básico")
        
    # Footer com informações úteis
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <strong>Sistema de Análise de Precificação - Estado de Alagoas</strong>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()