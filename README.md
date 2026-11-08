# NBA Draft Prediction 🏀

Projeto de conclusão da pós-graduação em Data Science e IA. O projeto reúne um pipeline de coleta de dados do Draft da NBA e notebooks que estimam o desempenho profissional de jogadores vindos da NCAA a partir de informações disponíveis na época do Draft.

A variável-alvo combina o VORP (*Value Over Replacement Player*) acumulado nas cinco primeiras temporadas na NBA com o número de temporadas disputadas. Jogadores com menos de três temporadas recebem a classe `Bust`. Para os demais, o VORP acumulado define a classe.

| Classe | VORP acumulado |
| --- | --- |
| `Star` | 10 ou mais |
| `Starter` | De 3,5 até menos de 10 |
| `Rotation` | De 0 até menos de 3,5 |
| `Bust` | Abaixo de 0 |

## Instalação

Os notebooks principais registram Python 3.13.16 nos metadados. Crie um ambiente virtual com Python 3.13.

```bash
git clone https://github.com/caiogpontes/nba-draft-prediction.git
cd nba-draft-prediction
python -m venv .venv
```

Ative o ambiente com `.venv\Scripts\Activate.ps1` no PowerShell ou `source .venv/bin/activate` no Bash. Em seguida, instale as dependências do pipeline e dos notebooks.

```bash
python -m pip install -r requirements.txt
```

## Coleta de dados

Para refazer a coleta, execute na raiz do repositório.

```bash
python main.py
```

O pipeline está configurado para os Drafts de 2000 a 2025 e salva os CSVs em `data/`. A coleta acessa serviços externos e pode demorar devido às pausas entre requisições.

- Histórico do Draft e estatísticas da NBA e da NCAA. [Basketball Reference](https://www.basketball-reference.com/)
- Mock Drafts históricos. [NBADraft.net](https://www.nbadraft.net/)
- Medidas antropométricas e testes de força e agilidade do Combine, consultados com `nba-api`.

## Notebooks

Abra os notebooks no VS Code ou no Jupyter e selecione o kernel do ambiente virtual. Execute com `notebooks/` como diretório de trabalho, pois há células que leem arquivos em `../data/`.

Para reconstruir as bases a partir dos CSVs de coleta, execute `01` e depois `03`. Em seguida, execute `02` para explorar as bases preparadas ou `04` a `07` para os experimentos de modelagem. A pasta `notebooks/old_notebooks/` contém versões históricas e fica fora desse fluxo.

| Notebook | Etapa |
| --- | --- |
| `01_data_preparation.ipynb` | Consolidação dos CSVs e cálculo do VORP acumulado |
| `02_exploratory_data_analysis_(EDA).ipynb` | Análise exploratória |
| `03_feature_engineering.ipynb` | Criação das classes e variáveis, com separação das bases pelo ano do Draft |
| `04_multinomial_logistic_regression.ipynb` | Regressão logística multinomial |
| `05_model_training.ipynb` | Treinamento e comparação de modelos de classificação |
| `06_model_training_automl.ipynb` | Busca de hiperparâmetros e avaliação de modelos |
| `07_neural_networks.ipynb` | Treinamento e avaliação de redes neurais |

## Estrutura do projeto

- `main.py` executa a coleta.
- `src/` contém a configuração, a infraestrutura de rede e armazenamento, os parsers, a orquestração e os utilitários.
- `data/` reúne os CSVs de coleta e as bases preparadas.
- `notebooks/` reúne as etapas de análise e modelagem.
- `requirements.txt` reúne as dependências do pipeline e dos notebooks ativos.
- `requirements_mlops.txt` contém uma lista separada de dependências para MLOps, fora do fluxo principal.

## Autor

Caio Gonçalves Pontes. [LinkedIn](https://www.linkedin.com/in/caiogpontes/) · [GitHub](https://github.com/caiogpontes)

## Licença

[MIT](LICENSE).

