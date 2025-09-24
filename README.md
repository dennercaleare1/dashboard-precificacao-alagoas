# 🗺️ Dashboard de Precificação - Municípios de Alagoas

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/dennercaleare1/dashboard-precificacao-alagoas?style=for-the-badge&logo=github)](https://github.com/dennercaleare1/dashboard-precificacao-alagoas/stargazers)

[![Plotly](https://img.shields.io/badge/Plotly-239120?style=flat-square&logo=plotly&logoColor=white)](https://plotly.com/)
[![Folium](https://img.shields.io/badge/Folium-77B829?style=flat-square&logo=folium&logoColor=white)](https://python-visualization.github.io/folium/)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![ReportLab](https://img.shields.io/badge/ReportLab-FF6B35?style=flat-square)](https://www.reportlab.com/)

**📊 Dashboard interativo para análise de dados de precificação dos municípios de Alagoas com mapa geográfico, visualizações avançadas e relatórios em PDF personalizados.**

[🚀 Demo](#-como-executar) • [📊 Funcionalidades](#-funcionalidades) • [🛠️ Instalação](#-instalação) • [🤝 Contribuir](#-como-contribuir)

</div>

---

## 🌟 Sobre o Projeto

Este projeto apresenta um **dashboard completo e interativo** desenvolvido em Streamlit para análise de dados de precificação municipal. O sistema oferece visualizações geográficas, análises estatísticas e relatórios profissionais personalizados.

### 🎯 **Objetivo**
Fornecer uma ferramenta visual e intuitiva para análise de precificação municipal, permitindo insights geográficos e estatísticos para tomada de decisões estratégicas.

## 🚀 Demo

> **🎬 Demonstração Visual:** *(Screenshots serão adicionados em breve)*

### 📱 **Principais Telas do Dashboard:**
- 🗺️ **Mapa Interativo** - Visualização geográfica completa dos 102 municípios
- 📊 **Rankings** - Top municípios e análises comparativas
- 📈 **Gráficos** - Distribuições e correlações avançadas
- 🎨 **PDF Personalizado** - Relatórios profissionais customizáveis
- 🔍 **Filtros Avançados** - Sistema de filtros inteligente e responsivo

### 🛡️ **Privacidade dos Dados**
⚠️ **IMPORTANTE**: Este repositório utiliza **dados fictícios** para demonstração. Os dados reais foram removidos por questões de **privacidade e segurança**. Para usar seus próprios dados, adicione-os na pasta `data/` (que está protegida pelo `.gitignore`).

---

## 📊 Funcionalidades

### 🗺️ **1. Mapa Interativo (Principal)**
- **Visualização Geográfica**: Todos os 102 municípios plotados com coordenadas reais
- **Marcadores Coloridos**: Sistema de cores baseado em faixas de valores
  - 🟢 Verde: Valores baixos (0-33%)
  - 🟠 Laranja: Valores médios (33-66%) 
  - 🔴 Vermelho: Valores altos (66-100%)
- **Popups Informativos**: Detalhes completos de cada município
- **Legenda Interativa**: Explicação clara do sistema de cores
- **Estatísticas Dinâmicas**: Métricas que se atualizam com filtros

### 🏆 **2. Ranking de Valores**
- **Top Municípios**: Ranking por valor de precificação
- **Métricas Destacadas**: Maior, menor, médio e total geral
- **Tabela Detalhada**: Dados formatados para fácil leitura
- **Gráficos Interativos**: Visualizações com Plotly

### 📊 **3. Análise Comparativa**
- **Valor vs População**: Scatter plots com análise de correlação
- **Análise de Eficiência**: Relação entre diferentes variáveis
- **Insights Estatísticos**: Correlações e tendências

### 📈 **4. Distribuição de Preços**
- **Histogramas Interativos**: Distribuição de valores por faixas
- **Análise por Quartis**: Divisão estatística dos dados
- **Faixas de Preço**: Categorização personalizada

### 🔍 **5. Sistema de Filtros Avançado**
- **Seleção de Municípios**: Multiselect para análise específica
- **Faixa de População**: Slider com valores dinâmicos
- **Faixa de Notas**: Filtro por critérios de qualidade
- **Faixa de Valores**: Controle em bilhões de reais
- **Análises Rápidas**: Botões para Top 10, Premium, etc.

### � **6. Relatórios Profissionais**
- **Exportação PDF**: Relatórios formatados com ReportLab
- **Tabelas Estruturadas**: Dados organizados profissionalmente
- **Métricas Resumidas**: KPIs principais destacados

---

## 🛠️ Instalação

### **Pré-requisitos**
- Python 3.8+
- Git
- Arquivo CSV com dados de precificação

### **1. Clone o Repositório**
```bash
git clone https://github.com/[seu-usuario]/dashboard-precificacao-alagoas.git
cd dashboard-precificacao-alagoas
```

### **2. Ambiente Virtual (Recomendado)**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

### **3. Instalar Dependências**
```bash
pip install -r requirements.txt
```

---

## 🚀 Como Executar

### **Método 1: Streamlit Run**
```bash
streamlit run dashboard_precificacao.py
```

### **Método 2: Python Module**
```bash
python -m streamlit run dashboard_precificacao.py --server.port 8501
```

### **Método 3: Com Porta Personalizada**
```bash
streamlit run dashboard_precificacao.py --server.port 8080
```

O dashboard será aberto automaticamente no seu navegador em `http://localhost:8501`

---

## 📁 Estrutura do Projeto

```
dashboard-precificacao-alagoas/
│
├── 📊 dashboard_precificacao.py          # Aplicação principal Streamlit
├── 📋 requirements.txt                   # Dependências Python
├── 📖 README.md                         # Documentação do projeto
│
├── 📁 data/
│   ├── 📄 precificacao_al_dec_*.csv     # Dados de precificação
│   └── 📋 Revisão e Estrutura das Tabelas.pdf  # Documentação dos dados
│
├── 📁 docs/
│   └── 📄 Metabase - Painel Modelo Real.pdf    # Documentação adicional
│
└── 📁 .venv/                            # Ambiente virtual (ignorado no git)
```

---

## 📊 Estrutura dos Dados

### **Dados Municipais Básicos**
- `Nm Mun`: Nome do município
- `Cd Mun`: Código IBGE do município
- `Populacao`: População estimada (IBGE)
- `Sigla Uf`: Sigla da unidade federativa (AL)

### **Sistema de Notas (Critérios de Precificação)**
- `Nota Veg`: Vegetação (aberta, intermediária, fechada)
- `Nota Area`: Área média de lotes CAR (>35ha, 15-35ha, <15ha)
- `Nota Relevo`: Relevo predominante no município
- `Nota P Q1-Q4`: Precipitação por trimestre
- `Nota Insalub`: Insalubridade (dengue)
- `Nota Insalub2`: Insalubridade ajustada (animais peçonhentos)
- `Nota Media`: Média das notas para composição do valor final

### **Dados Geoespaciais**
- `Area Cidade`: Área total do município
- `Area Georef`: Área georreferenciável (exclui terras indígenas, União, etc.)
- `Num Imoveis`: Número de imóveis CAR
- `Area Car Total/Media`: Área total/média dos imóveis CAR
- `Perimetro Total/Medio Car`: Perímetro total/médio CAR

### **Valores de Precificação (INCRA)**
- `Valor Mun Area`: **Valor principal** - baseado na área georreferenciável
- `Valor Mun Perim`: Valor alternativo - baseado no perímetro total CAR

---

## 🎨 Tecnologias Utilizadas

### **Backend & Framework**
- **Streamlit 1.28+**: Framework principal para dashboard web
- **Pandas 2.0+**: Manipulação e análise de dados
- **NumPy 1.24+**: Operações numéricas

### **Visualizações**
- **Plotly 5.15+**: Gráficos interativos avançados
- **Folium 0.15+**: Mapas interativos
- **Streamlit-Folium 0.15+**: Integração Folium + Streamlit

### **Relatórios & Exports**
- **ReportLab 4.0+**: Geração de PDFs profissionais
- **Kaleido 0.2+**: Export de gráficos estáticos

### **Styling & UX**
- **CSS3**: Gradientes modernos e design responsivo
- **HTML5**: Estruturação de componentes customizados

---

## 📖 Documentação

### **Arquivos de Referência**
- `Revisão e Estrutura das Tabelas.pdf`: Documentação completa da estrutura dos dados
- `Metabase - Painel Modelo Real.pdf`: Referência do painel modelo

### **Critérios de Precificação**
Os valores são calculados conforme a **Instrução Normativa INCRA** utilizando:
- Dados do **Quadro II - Tabela de Rendimento e Preço do Anexo I**
- Área georreferenciável (excludente: terras indígenas, União, UCs, SIGEF)
- Sistema de notas ponderado por múltiplos critérios ambientais e geográficos

---

## 🤝 Contribuição

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE). Veja o arquivo `LICENSE` para mais detalhes.

---

## 👨‍💻 Autor

**Denner Caleare**
- GitHub: [@dennercaleare](https://github.com/dennercaleare)
- LinkedIn: [Denner Caleare](https://linkedin.com/in/dennercaleare)

---

<div align="center">

**⭐ Se este projeto foi útil para você, considere dar uma estrela!**

**🚀 Desenvolvido com Streamlit + Python + Plotly + Folium**

</div>
- **Valor Mun Perim**: Valor municipal por perímetro

## 🎨 Características do Dashboard

### Design Responsivo
- Layout em colunas adaptável
- Sidebar com filtros e informações
- Tabs organizadas por tipo de análise

### Visualizações Interativas
- Gráficos de barras horizontais para rankings
- Histogramas para distribuição de dados
- Scatter plots para análise de correlação
- Matriz de correlação com heatmap
- Métricas destacadas em cards

### Funcionalidades Avançadas
- Cache de dados para melhor performance
- Filtros dinâmicos
- Tabelas interativas
- Download de dados
- Tooltips informativos

## 🛠️ Tecnologias Utilizadas

- **Streamlit**: Framework para criação do dashboard
- **Pandas**: Manipulação e análise de dados
- **Plotly**: Visualizações interativas
- **NumPy**: Operações numéricas
- **CSS**: Estilização customizada

## 📈 Tipos de Análises Disponíveis

1. **Análise Demográfica**: População por município
2. **Avaliação de Qualidade**: Distribuição das notas por categoria
3. **Correlações**: Relações entre diferentes variáveis
4. **Análise Financeira**: Valores municipais e métricas econômicas

## 🔧 Personalização

O dashboard pode ser facilmente customizado:

- Modificar cores no CSS customizado
- Adicionar novas visualizações
- Incluir filtros adicionais
- Expandir métricas calculadas

---

## 🤝 Como Contribuir

Contribuições são sempre bem-vindas! 🎉

### 🚀 **Formas de Contribuir**
- 🐛 **Reportar bugs** através das [Issues](https://github.com/dennercaleare1/dashboard-precificacao-alagoas/issues)
- 💡 **Sugerir funcionalidades** usando nossos templates
- 🔧 **Contribuir com código** via Pull Requests
- 📝 **Melhorar documentação**
- ⭐ **Dar uma estrela** no projeto

### 📋 **Processo Simples**
1. 🍴 Fork o repositório
2. 🌿 Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. ✅ Commit suas mudanças (`git commit -m '✨ Add some AmazingFeature'`)
4. 📤 Push para a branch (`git push origin feature/AmazingFeature`)
5. 🔄 Abra um Pull Request

### 📚 **Documentação Completa**
- 📖 [**Guia de Contribuição**](CONTRIBUTING.md) - Instruções detalhadas
- 📅 [**Changelog**](CHANGELOG.md) - Histórico de versões
- 🏷️ [**Issues Templates**](.github/ISSUE_TEMPLATE/) - Modelos padronizados

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## ⭐ Apoie o Projeto

Se este projeto foi útil para você, considere:

- ⭐ **Dar uma estrela** no GitHub
- 🐛 **Reportar bugs** que encontrar
- 💡 **Compartilhar ideias** para melhorias
- 🤝 **Contribuir com código**

---

<div align="center">

**Desenvolvido com ❤️ para análise de dados municipais**

[![GitHub](https://img.shields.io/badge/GitHub-dennercaleare1-181717?style=for-the-badge&logo=github)](https://github.com/dennercaleare1)

</div>

## 📝 Notas

- Os dados são carregados automaticamente do CSV
- Valores numéricos são convertidos do formato brasileiro (vírgula) para americano (ponto)
- Interface otimizada para diferentes tamanhos de tela
- Tratamento de erros para dados ausentes ou incorretos

## 🤝 Contribuições

Para melhorias ou sugestões, sinta-se à vontade para contribuir com o projeto!