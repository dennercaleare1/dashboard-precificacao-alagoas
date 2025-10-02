#!/bin/bash

# Script de configuração para facilitar o uso do Dashboard

echo "🗺️  Configurando Dashboard de Precificação - Municípios de Alagoas"
echo ""

# Adiciona alias ao .zshrc se não existir
ALIAS_LINE="alias dashboard='cd \"/Users/dennercaleare/Documents/Zetta/Treino StreamLit Precificacao\" && ./manage_dashboard.sh'"

if ! grep -q "alias dashboard=" ~/.zshrc 2>/dev/null; then
    echo "# Dashboard de Precificação - Municípios de Alagoas" >> ~/.zshrc
    echo "$ALIAS_LINE" >> ~/.zshrc
    echo "✅ Alias 'dashboard' adicionado ao ~/.zshrc"
else
    echo "⚠️  Alias 'dashboard' já existe no ~/.zshrc"
fi

echo ""
echo "🎯 Configuração concluída!"
echo ""
echo "📋 Como usar:"
echo "  1. Reinicie o terminal ou execute: source ~/.zshrc"
echo "  2. Use os comandos:"
echo "     • dashboard start    - Inicia o dashboard"
echo "     • dashboard stop     - Para o dashboard"
echo "     • dashboard restart  - Reinicia o dashboard"
echo "     • dashboard status   - Verifica status"
echo "     • dashboard logs     - Mostra logs em tempo real"
echo ""
echo "🌐 URL do Dashboard: http://localhost:8520"
echo ""