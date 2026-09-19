# MERGE-CPTEC

Projeto de Valkiria Andrade para processamento e visualização meteorológica.
Código organizado em pacote Python, com configuração pela linha de comando,
testes de regressão e verificações automáticas no GitHub Actions.

## Instalação

Python 3.10 ou superior. Na pasta deste repositório:

```bash
python -m venv .venv
# Windows PowerShell: .venv/Scripts/Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

WRF e MERGE precisam também de ecCodes: `python -m pip install -e ".[grib]"`.
O pacote ecCodes oferece binários para Windows, Linux e macOS. NetCDF, cálculos e
mapas não dependem desse extra. A leitura GRIB usa diretamente ecCodes, substituindo pygrib.

## Execução

Exemplo (confira os nomes e metadados dos seus arquivos):

```bash
merge-cptec --input Dados/mai --product accumulation --title "Acumulado — maio 2024" --output output/acumulado.png
merge-cptec --help
```

O acumulado soma os arquivos diários do diretório: mantenha apenas o período desejado, sem duplicatas. --product anomaly-netcdf exige --climatology e salva NetCDF; --product anomaly lê esse NetCDF para gerar mapa. --product climatology lê precacum. --region norte recorta o Norte (use --shapefile para máscara estadual). anomaly-spread usa dispersão espacial do campo, não desvio-padrão climatológico nem categorias probabilísticas.

`--shapefile caminho/BR_UF_2022.shp` aplica máscara e limites locais; o arquivo
deve incluir seus arquivos auxiliares e CRS. ZIPs precisam ser extraídos.
Sem shapefile, Cartopy pode baixar a cartografia Natural Earth no primeiro uso.
`--title` configura o título e `--verbose` mostra detalhes dos erros.
Mapas são salvos sem abrir janelas. A pasta de saída é criada automaticamente.

## Arquitetura e manutenção

- `src/merge_cptec/io.py`: leitura, fechamento de recursos e validação de grades.
- `src/merge_cptec/cli.py`: argumentos e coordenação do processamento.
- `src/merge_cptec/plotting.py`: renderização e máscara geográfica.
- `Scripts/`: entradas com os nomes históricos, usando o pacote instalado.
- `tests/`: dados sintéticos e regressões independentes de serviços externos.
- `Dados/` e `Figuras/`: acervo original preservado.

As entradas históricas agora exigem os mesmos argumentos da CLI. Caminhos,
datas e arquivos antes fixos no código devem ser informados explicitamente.
Paletas e resolução foram padronizadas; figuras não são cópias pixel a pixel
das versões antigas. Valores ausentes não são convertidos em zero.

```bash
pytest -q
ruff check src Scripts tests
```

A CI executa testes em Python 3.10 e 3.12. Os testes usam pequenos dados
sintéticos e cartografia local; a interpretação científica e a cobertura do
período devem ser conferidas com os dados operacionais.

Histórico, descrição científica e imagens: [README original](docs/README-original.md).
