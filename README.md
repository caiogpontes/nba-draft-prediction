# Previsão de Sucesso de Jogadores Universitários na NBA 🏀

![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellow)

Projeto final (TCC) do curso de Pós-Graduação em Data Science e IA. O objetivo é construir um pipeline de engenharia de dados (web scraping) e um modelo de Machine Learning para prever o sucesso de jogadores universitários (NCAA) na NBA.

---

## 🎯 Objetivos do Projeto

### 1. Engenharia de Dados (Coleta)
* **Coleta de Dados Reais:** Desenvolver um scraper robusto para extrair dados históricos do Draft da NBA, estatísticas de carreira (NBA) e estatísticas universitárias (NCAA) do [Basketball-Reference.com](https://www.basketball-reference.com/).
* **Coleta de Expectativas:** Criar um scraper para extrair dados históricos de "Mock Drafts" do [NBADraft.net](https://www.nbadraft.net/), medindo o "hype" pré-draft de um jogador.
* **Arquitetura Limpa:** Construir o pipeline de coleta seguindo princípios de Clean Code e SOLID (SRP, OCP), separando a lógica de rede, parsing e orquestração.

### 2. Ciência de Dados (Modelagem)
* **Preparação:** Unir, limpar e preparar os dados coletados (reais vs. mock) em uma base de modelo única.
* **Análise (EDA):** Explorar os dados para encontrar correlações e features preditivas.
* **Modelagem:** Treinar um modelo de classificação (ex: Regressão Logística, Random Forest) para prever se um jogador terá uma carreira de "sucesso" na NBA (definida por métricas como VORP, WS, etc.).

---

## 🚀 Como Executar o Pipeline de Coleta

Este projeto utiliza Python. As dependências estão listadas em `requirements.txt`.

### 1. Pré-requisitos
* Python 3.9+
* Git

### 2. Instalação
Clone este repositório e instale as dependências:

```bash
# 1. Clone o projeto
git clone [https://github.com/SEU_USUARIO/previsao_jogadores_universitarios_nba.git](https://github.com/SEU_USUARIO/previsao_jogadores_universitarios_nba.git)
cd previsao_jogadores_universitarios_nba

# 2. (Opcional, mas recomendado) Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

### 3. Executando a Coleta de Dados
Para executar o pipeline completo de web scraping, basta rodar o `main.py`. Os dados serão salvos na pasta `/data`.

```bash
python main.py
```
*Nota: A coleta pode levar um tempo considerável devido aos delays implementados para não sobrecarregar os servidores de origem.*

---

## 📁 Estrutura do Projeto

O projeto é dividido em duas partes principais: o pipeline de engenharia (`src`) e os notebooks de análise (`notebooks`).

```
previsao_jogadores_universitarios_nba/
│
├── data/
│   └── .gitkeep             # Onde os .csv de saída são salvos
│
├── notebooks/
│   ├── 01_data_preparation.ipynb  # Limpeza e junção dos dados
│   ├── 02_exploratory_data_analysis.ipynb # EDA
│   └── 03_model_training.ipynb    # Treinamento do modelo
│
├── src/                     # Código-fonte do pipeline de engenharia (Clean Code)
│   ├── __init__.py
│   ├── config.py            # Configs, constantes, URLs e dicionários de renomeação
│   │
│   ├── infrastructure/      # Camada de "IO" (Input/Output)
│   │   ├── network.py       # (Classe NetworkClient) - Responsável por fazer requests
│   │   └── storage.py       # (Classe DataManager) - Responsável por ler/salvar CSV
│   │
│   ├── parsers/             # Camada de "Lógica de Negócio"
│   │   ├── html_helper.py   # Funções utilitárias (ex: extrair tabela comentada)
│   │   ├── draft_parser.py  # (Classe DraftParser) - Lógica do Basketball-Reference
│   │   ├── stats_parser.py  # (Classe PlayerStatsParser) - Lógica de stats
│   │   └── mock_parser.py   # (Classe MockDraftParser) - Lógica do NBADraft.net
│   │
│   └── pipeline/
│       └── orchestrator.py  # (Classe Orchestrator) - Coordena o fluxo do pipeline
│
├── main.py                  # Ponto de entrada para executar o pipeline de coleta
├── requirements.txt         # Dependências do Python
└── README.md                # Este arquivo
```

---

## 📊 Fontes de Dados

* **Estatísticas Reais:** [Basketball-Reference.com](https://www.basketball-reference.com/)
* **Mock Drafts Históricos:** [NBADraft.net](https://www.nbadraft.net/)

---

## ✍️ Autor

**[Seu Nome]**
* [LinkedIn](https://www.linkedin.com/in/caiogpontes/)
* [GitHub](https://github.com/caiogpontes)

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.