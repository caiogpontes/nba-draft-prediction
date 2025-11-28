# nba-draft-prediction: Modelo Preditivo para Sucesso na NBA 🏀

![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellow)

Projeto final (TCC) do curso de Pós-Graduação em Data Science e IA. O objetivo é construir um pipeline de engenharia de dados (web scraping) e um modelo de Machine Learning para prever o sucesso de jogadores universitários (NCAA) na NBA.

---

## 🎯 Objetivos do Projeto

### 1. Engenharia de Dados (Coleta)
* **Coleta de Dados Reais:** Desenvolver um scraper robusto para extrair dados históricos do Draft, estatísticas de carreira (NBA) e estatísticas universitárias (NCAA) do [Basketball-Reference.com](https://www.basketball-reference.com/).
* **Coleta Física e Agilidade:** Integrar dados do **NBA Combine (Medidas Antropométricas e Testes de Força/Salto)** utilizando a biblioteca `nba-api`.
* **Coleta de Expectativas:** Criar um scraper para extrair dados históricos de "Mock Drafts" do [NBADraft.net](https://www.nbadraft.net/).
* **Arquitetura Limpa:** Construir o pipeline de coleta seguindo princípios de **Clean Code** e **SOLID (SRP, OCP)**.

### 2. Ciência de Dados (Modelagem)
* **Variável Alvo (Y):** Definir o sucesso de carreira pela métrica **VORP Acumulado nos 5 Primeiros Anos**.
* **Análise (EDA):** Explorar os dados para encontrar correlações e features preditivas.
* **Feature Engineering:** Criar *features* preditivas como `Pick_Differential` (Mock vs. Real) e `Proxy_Usage` (Volume Ofensivo).
* **Preparação:** Unir, limpar e preparar os 7 DataFrames em uma base de modelo única.

---

## 🚀 Como Executar o Pipeline de Coleta

Este projeto utiliza Python. As dependências estão listadas em `requirements.txt`.

### 1. Instalação e Configuração
Clone este repositório e instale as dependências:

```bash
# 1. Clone o projeto (Certifique-se de estar no diretório raiz)
git clone [https://github.com/SEU_USUARIO/nba-draft-prediction.git](https://github.com/SEU_USUARIO/nba-draft-prediction.git)
cd nba-draft-prediction

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
nba-draft-prediction/
│
├── data/
│   └── .gitkeep             # Onde os .csv de saída são salvos
│
├── notebooks/
│   ├── 01_data_preparation.ipynb  # Limpeza e junção dos dados
│   ├── 02_exploratory_data_analysis.ipynb # EDA
│   ├── 03_feature_engineering.ipynb # Criação da Variável Alvo e Features
│   └── 04_model_training.ipynb    # Treinamento do modelo
│
├── src/                           # Código-fonte do pipeline de engenharia (Clean Code)
│   ├── config.py                  # Configs, constantes e Mapeamentos
│   ├── infrastructure/            # NetworkClient, DataManager (I/O)
│   ├── parsers/                   # Lógica de extração (MockParser, StatsParser)
│   ├── pipeline/                  # Orchestrator (Coordenação do Fluxo)
│   └── utils/                     # Para corversoes, métodos para 
│
├── main.py                  # Ponto de entrada para executar o pipeline de coleta
├── requirements.txt         # Dependências do Python
└── README.md                # Este arquivo
```

---

## 📊 Fontes de Dados

* **Estatísticas Reais:** [Basketball-Reference.com](https://www.basketball-reference.com/)
* **Dados Físicos (Combine):** [NBA Stats API] (nba-api)
* **Mock Drafts Históricos:** [NBADraft.net](https://www.nbadraft.net/)

---

## ✍️ Autor

**[Caio Gonçalves Pontes]**
* [LinkedIn](https://www.linkedin.com/in/caiogpontes/)
* [GitHub](https://github.com/caiogpontes)

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.