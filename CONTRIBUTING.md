# 🤝 Guia de Contribuição

Obrigado pelo seu interesse em contribuir com o **Dashboard de Precificação - Municípios de Alagoas**! 

## 🌟 Como Contribuir

### 🐛 **Reportar Bugs**
1. Verifique se o bug já não foi reportado nas [Issues](https://github.com/dennercaleare1/dashboard-precificacao-alagoas/issues)
2. Use o template de bug report
3. Inclua:
   - Descrição clara do problema
   - Passos para reproduzir
   - Comportamento esperado vs atual
   - Screenshots (se aplicável)
   - Informações do ambiente (Python version, OS, etc.)

### 💡 **Sugerir Melhorias**
1. Abra uma [Issue](https://github.com/dennercaleare1/dashboard-precificacao-alagoas/issues) com o template de feature request
2. Descreva:
   - Problema que a funcionalidade resolve
   - Solução proposta
   - Alternativas consideradas
   - Impacto nos usuários

### 🔧 **Contribuir com Código**

#### **Setup do Ambiente**
```bash
# 1. Fork o repositório
# 2. Clone seu fork
git clone https://github.com/SEU-USERNAME/dashboard-precificacao-alagoas.git
cd dashboard-precificacao-alagoas

# 3. Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# 4. Instale dependências
pip install -r requirements.txt

# 5. Teste o dashboard
streamlit run dashboard_precificacao.py
```

#### **Fluxo de Desenvolvimento**
1. **Crie uma branch** para sua feature/fix:
   ```bash
   git checkout -b feature/nome-da-feature
   # ou
   git checkout -b fix/nome-do-bug
   ```

2. **Faça suas alterações** seguindo os padrões do projeto

3. **Teste suas mudanças**:
   - Execute o dashboard e teste todas as funcionalidades
   - Verifique se não há erros no console
   - Teste com diferentes filtros e dados

4. **Commit suas mudanças**:
   ```bash
   git add .
   git commit -m "✨ feat: adiciona nova funcionalidade X"
   # ou
   git commit -m "🐛 fix: corrige problema com filtros Y"
   ```

5. **Push e abra um Pull Request**:
   ```bash
   git push origin feature/nome-da-feature
   ```

## 📝 **Padrões de Código**

### **Estilo de Código**
- Use **4 espaços** para indentação
- Nomes de variáveis em **snake_case**
- Nomes de funções descritivos
- Comentários claros em português
- Docstrings para funções complexas

### **Estrutura de Commits**
Use emojis e prefixos claros:
- `✨ feat:` - Nova funcionalidade
- `🐛 fix:` - Correção de bug
- `📝 docs:` - Atualizações de documentação
- `🎨 style:` - Melhorias de estilo/formatação
- `♻️ refactor:` - Refatoração de código
- `⚡ perf:` - Melhorias de performance
- `🧪 test:` - Adição/modificação de testes

## 🎯 **Áreas Prioritárias**

### **Alta Prioridade**
- 🗺️ Melhorias no mapa interativo
- 📊 Novos tipos de visualizações
- 🔍 Otimização dos filtros
- 📱 Responsividade mobile

### **Média Prioridade**
- 🎨 Melhorias de UI/UX
- 📈 Novas métricas estatísticas
- 🔧 Otimização de performance
- 📄 Novos formatos de exportação

### **Baixa Prioridade**
- 🧪 Testes automatizados
- 📚 Documentação adicional
- 🌐 Internacionalização

## 🛡️ **Diretrizes de Privacidade**

- **NUNCA** faça commit de dados reais ou sensíveis
- Use sempre dados fictícios para testes
- Verifique o `.gitignore` antes de fazer commits
- Respeite a estrutura de pastas protegidas (`data/`, `docs/`)

## 🚨 **Checklist do Pull Request**

- [ ] Código testado localmente
- [ ] Commits seguem o padrão estabelecido
- [ ] Documentação atualizada (se necessário)
- [ ] Nenhum dado sensível incluído
- [ ] Screenshots incluídos (para mudanças visuais)
- [ ] Descrição clara do que foi alterado

## 🤔 **Dúvidas?**

- Abra uma [Issue](https://github.com/dennercaleare1/dashboard-precificacao-alagoas/issues) com a tag `question`
- Entre em contato através do GitHub

---

**Obrigado por contribuir! 🙏**

Cada contribuição, por menor que seja, faz a diferença para melhorar este projeto.