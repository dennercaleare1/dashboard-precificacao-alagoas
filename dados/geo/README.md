# Dados Geográficos

Esta pasta armazena dados geográficos otimizados para o dashboard.

## Arquivos que serão baixados automaticamente:

### `brasil_municipios_2022.zip` (~50-70MB)
- Shapefile original do IBGE com todos os municípios do Brasil
- Baixado automaticamente na primeira execução
- Fonte: https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/

### `brasil_municipios_simplified.geojson` (~15-25MB)
- Versão simplificada e otimizada do shapefile
- Criado automaticamente após o primeiro download
- Usado nas próximas execuções para carregar mais rápido

## Benefícios:

✅ **Preparado para expansão**: Contém todos os municípios do Brasil
✅ **Otimizado**: Geometrias simplificadas para melhor performance
✅ **Cache inteligente**: Baixa uma vez, usa sempre
✅ **Compatível**: Funciona no Streamlit Cloud (arquivo final <25MB)

## Nota:
- O primeiro carregamento pode demorar alguns minutos
- Execuções seguintes serão muito mais rápidas
- Adequado para futuras expansões para outros estados do Brasil