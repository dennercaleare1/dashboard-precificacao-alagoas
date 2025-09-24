# 📅 Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.2.0] - 2025-09-24

### ✨ Adicionado
- 🤝 Arquivo CONTRIBUTING.md com guias de contribuição
- 📅 CHANGELOG.md para documentar versões
- 🏷️ Badges profissionais no README (Python, Streamlit, License, Stars)
- 🎬 Seção de demo visual no README
- 📚 Documentação melhorada com links e navegação

### 🧹 Removido
- ❌ Documentação técnica desnecessária (CORRECAO_FILTROS_SLIDERS, TRANSFORMACOES_PDF_PERSONALIZADO, ORGANIZACAO_PRIVACIDADE)
- 🗑️ Cache Python (__pycache__/)
- 🧹 Arquivos temporários (streamlit.pid)

### 🔧 Corrigido
- 📝 Referências quebradas no README
- 🔗 Links internos atualizados

### 🔒 Segurança
- ✅ Repositório tornado público com dados sensíveis protegidos
- 🛡️ Estrutura de privacidade mantida com .gitignore

## [1.1.0] - 2025-09-19

### ✨ Adicionado
- 🎨 Sistema completo de PDF personalizado
- 📄 Interface de personalização de relatórios
- 🎯 Seleção de seções do relatório
- 👤 Campos de personalização (nome, empresa, observações)
- 🎨 Opções de tema (Profissional, Moderno, Clássico)
- 📊 Incluir/excluir diferentes seções (mapa, rankings, análises)

### 🐛 Corrigido
- ✅ Problemas de layout no PDF (textos sobrepostos)
- 🔧 Validação de filtros slider (valores min/max iguais) 
- 🔢 Conversão de números brasileiros (pontos/vírgulas)
- 📐 Espaçamentos e margens do PDF
- 🎨 Cores de fundo problemáticas removidas

### ♻️ Refatorado
- 🗂️ Aba "📄 Dados & Exportação" → "📄 Gerar PDF Personalizado"
- 🔧 Lógica de conversão de unidades centralizada
- 📊 Sistema de filtros com tolerância para edge cases

## [1.0.0] - 2025-09-18

### ✨ Adicionado - Lançamento Inicial
- 🗺️ **Mapa Interativo**: Visualização de todos os 102 municípios de Alagoas
- 🏆 **Sistema de Rankings**: Top municípios por diferentes critérios
- 📊 **Análises Comparativas**: Scatter plots e correlações
- 📈 **Distribuição de Preços**: Histogramas e análises estatísticas
- 🔍 **Filtros Avançados**: Multiselect, sliders e filtros rápidos
- 📄 **Exportação PDF**: Relatórios profissionais formatados
- 🎨 **Interface Moderna**: Design responsivo com Streamlit
- 📱 **7 Abas Funcionais**: 
  - 🗺️ Mapa Principal
  - 🏆 Ranking de Valores  
  - 📊 Análise Comparativa
  - 📈 Distribuição de Preços
  - 🔍 Filtros Avançados
  - 📄 Dados & Exportação
  - ℹ️ Sobre o Projeto

### 🛠️ **Tecnologias Utilizadas**
- **Frontend**: Streamlit 1.28+
- **Mapas**: Folium para visualizações geográficas
- **Gráficos**: Plotly para visualizações interativas
- **Dados**: Pandas para manipulação de dados
- **PDF**: ReportLab para geração de relatórios
- **Estilo**: CSS customizado

### 🔒 **Recursos de Segurança**
- 🛡️ Dados sensíveis protegidos por .gitignore
- 📁 Estrutura de pastas organizada (data/, docs/)
- 🔐 Sistema de privacidade implementado

---

## 🏷️ **Tipos de Mudanças**

- `✨ Adicionado` - para novas funcionalidades
- `🔧 Corrigido` - para correções de bugs
- `♻️ Refatorado` - para mudanças que não corrigem bugs nem adicionam funcionalidades
- `🧹 Removido` - para funcionalidades removidas
- `🔒 Segurança` - para vulnerabilidades corrigidas
- `⚡ Performance` - para melhorias de performance
- `📝 Documentação` - apenas mudanças de documentação

## 🔗 **Links Úteis**

- [Repositório GitHub](https://github.com/dennercaleare1/dashboard-precificacao-alagoas)
- [Como Contribuir](CONTRIBUTING.md)
- [Licença](LICENSE)