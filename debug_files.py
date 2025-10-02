#!/usr/bin/env python3
"""Script para debug - verificar arquivos disponíveis"""

import os
import sys

print("=== DEBUG: Verificando arquivos ===")
print(f"Diretório atual: {os.getcwd()}")
print(f"Arquivos no diretório atual:")
for item in os.listdir('.'):
    print(f"  - {item}")

print(f"\nVerificando pasta 'dados':")
if os.path.exists('dados'):
    print("  ✅ Pasta 'dados' existe")
    for item in os.listdir('dados'):
        print(f"    - {item}")
        
    csv_files = [f for f in os.listdir('dados') if f.endswith('.csv')]
    print(f"  📄 Arquivos CSV encontrados: {csv_files}")
else:
    print("  ❌ Pasta 'dados' não encontrada")

print(f"\nVerificando pasta 'data':")
if os.path.exists('data'):
    print("  ✅ Pasta 'data' existe")
    for item in os.listdir('data'):
        print(f"    - {item}")
else:
    print("  ❌ Pasta 'data' não encontrada")

print(f"\nArquivos específicos:")
files_to_check = [
    'dados/precificacao_alagoas_NOVO.csv',
    'dados/precificacao_alagoas.csv'
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"  ✅ {file_path} - EXISTE")
    else:
        print(f"  ❌ {file_path} - NÃO ENCONTRADO")