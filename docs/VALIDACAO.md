# Validação da refatoração

- Python 3.11 no Windows: testes de acumulação, grades, valores ausentes,
  interpolação, coordenadas, fechamento de arquivos e mapa offline.
- Leitura real da precipitação: grade 924 × 1001; ecCodes identifica o parâmetro
  nos arquivos fornecidos como `Precipitation from radar`, em kg/m² (= mm).
- Gerados acumulado de maio, mapa de anomalia existente de julho e novo NetCDF
  de anomalia de julho com os arquivos originais e climatologia do repositório.
- Instalação editável do pacote e verificação Ruff executadas.

Somente arquivos da mesma grade podem ser somados. A soma é interpolada uma vez
por triangulação linear para a grade da climatologia. NaNs propagam; fora da
cobertura da grade fonte o resultado permanece ausente. Não há preenchimento de
dias faltantes. O diretório de entrada deve conter exatamente o período desejado.
`anomaly-spread` calcula dispersão espacial após a máscara geográfica; não representa
desvio-padrão histórico nem probabilidade climática.

