#!/usr/bin/env python3
"""
Script de teste para verificar se os dados estão carregando corretamente
"""

import pandas as pd
import os

def test_csv_loading():
    # Procura pelo arquivo CSV na pasta dados
    csv_file = None
    
    # Primeiro procura na pasta dados
    dados_path = 'dados'
    if os.path.exists(dados_path):
        precificacao_file = os.path.join(dados_path, 'precificacao_alagoas.csv')
        if os.path.exists(precificacao_file):
            csv_file = precificacao_file
        else:
            # Procura qualquer CSV na pasta dados
            csv_files = [f for f in os.listdir(dados_path) if f.endswith('.csv')]
            if csv_files:
                csv_file = os.path.join(dados_path, csv_files[0])
    
    if not csv_file:
        print("❌ Arquivo CSV não encontrado!")
        return False
    print(f"✅ Arquivo encontrado: {csv_file}")
    
    # Carrega o CSV
    try:
        df = pd.read_csv(csv_file, dtype=str)
        print(f"✅ CSV carregado com sucesso!")
        print(f"📊 Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
        
        # Mostra as primeiras colunas
        print(f"\n📋 Primeiras colunas:")
        for i, col in enumerate(df.columns[:10]):
            print(f"  {i+1}. {col}")
        
        # Mostra alguns dados
        print(f"\n🏘️ Primeiros 3 municípios:")
        if 'Nm Mun' in df.columns:
            for i in range(min(3, len(df))):
                municipio = df.iloc[i]['Nm Mun']
                populacao = df.iloc[i]['Populacao'] if 'Populacao' in df.columns else 'N/A'
                print(f"  {i+1}. {municipio} (Pop: {populacao})")
        
        # Verifica colunas importantes
        colunas_importantes = ['Nm Mun', 'Populacao', 'Valor Mun Area', 'Valor Mun Perim', 'Nota Media']
        print(f"\n🔍 Verificando colunas importantes:")
        for col in colunas_importantes:
            if col in df.columns:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col} - NÃO ENCONTRADA")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar CSV: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando carregamento dos dados...\n")
    success = test_csv_loading()
    print(f"\n{'✅ Teste concluído com sucesso!' if success else '❌ Teste falhou!'}")