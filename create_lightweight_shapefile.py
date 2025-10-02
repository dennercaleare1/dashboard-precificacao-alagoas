#!/usr/bin/env python3
"""
Script para baixar e criar um shapefile leve dos municípios do Brasil
Este script roda uma vez para gerar o arquivo que será commitado no Git
"""

import geopandas as gpd
import requests
import zipfile
import os
from pathlib import Path

def download_and_process_brazil_shapefile():
    """Baixa shapefile do IBGE e cria versão leve para o Brasil"""
    
    print("🌎 Baixando shapefile dos municípios do Brasil do IBGE...")
    
    # URL do IBGE para municípios do Brasil (mais leve que mundo todo)
    url = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/Brasil/BR/BR_Municipios_2022.zip"
    
    # Criar pasta dados/geo se não existir
    geo_dir = Path("dados/geo")
    geo_dir.mkdir(parents=True, exist_ok=True)
    
    # Baixar arquivo
    zip_path = geo_dir / "municipios_brasil.zip"
    
    try:
        print(f"📥 Baixando de: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Download concluído: {zip_path}")
        
        # Extrair arquivos
        print("📂 Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(geo_dir)
        
        # Encontrar arquivo .shp
        shp_files = list(geo_dir.glob("*.shp"))
        if not shp_files:
            print("❌ Arquivo .shp não encontrado!")
            return None
            
        shp_file = shp_files[0]
        print(f"📍 Arquivo shapefile encontrado: {shp_file}")
        
        # Carregar e processar
        print("🔄 Processando geometrias...")
        gdf = gpd.read_file(shp_file)
        
        print(f"📊 Municípios originais: {len(gdf)}")
        print(f"📊 Colunas disponíveis: {list(gdf.columns)}")
        
        # Simplificar geometria para reduzir tamanho (tolerance = 0.01 graus)
        print("🔧 Simplificando geometria...")
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)
        
        # Manter apenas colunas essenciais
        essential_cols = []
        for col in gdf.columns:
            if any(keyword in col.upper() for keyword in ['NM_MUN', 'NOME', 'MUN', 'CD_MUN', 'CODIGO']):
                essential_cols.append(col)
            elif col == 'geometry':
                essential_cols.append(col)
        
        if essential_cols:
            gdf_light = gdf[essential_cols].copy()
        else:
            # Fallback: manter as primeiras colunas + geometry
            gdf_light = gdf.iloc[:, :3].copy()
            gdf_light['geometry'] = gdf['geometry']
        
        print(f"📊 Colunas mantidas: {list(gdf_light.columns)}")
        
        # Salvar versão leve
        output_file = geo_dir / "municipios_brasil_light.shp"
        print(f"💾 Salvando versão leve em: {output_file}")
        gdf_light.to_file(output_file)
        
        # Verificar tamanho
        original_size = sum(f.stat().st_size for f in geo_dir.glob("BR_Municipios_2022.*") if f.exists())
        light_size = sum(f.stat().st_size for f in geo_dir.glob("municipios_brasil_light.*") if f.exists())
        
        print(f"📏 Tamanho original: {original_size / 1024 / 1024:.1f} MB")
        print(f"📏 Tamanho leve: {light_size / 1024 / 1024:.1f} MB")
        print(f"💡 Redução: {(1 - light_size/original_size)*100:.1f}%")
        
        # Limpar arquivos temporários
        print("🧹 Limpando arquivos temporários...")
        zip_path.unlink()
        for f in geo_dir.glob("BR_Municipios_2022.*"):
            f.unlink()
        
        print("✅ Shapefile leve criado com sucesso!")
        return output_file
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

if __name__ == "__main__":
    result = download_and_process_brazil_shapefile()
    if result:
        print(f"\n🎉 Sucesso! Arquivo criado: {result}")
        print("📝 Agora você pode commitar este arquivo no Git")
    else:
        print("\n❌ Falha ao criar shapefile leve")