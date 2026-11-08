

import pandas as pd
from typing import Literal
from rapidfuzz import process, fuzz

def calculate_proxy_usage(FGA: float, FTA: float, TOV: float) -> float:
    """Calcula FGA + 0,44 × FTA + TOV, com entradas na mesma escala por 40 minutos.

    O resultado é uma aproximação de volume de uso, não uma porcentagem de posses."""
    # 1. Cálculo da Proxy Usage
    usage_percent = (
        FGA + 
        (0.44 * FTA) + 
        TOV
    )
    
    return round(usage_percent, 2)


def get_fuzzy_mapping(target_names, candidate_names, cutoff=80):
    """Cria um dicionário {nome_alvo: nome_candidato} baseado em similaridade."""
    mapping = {}
    for name in target_names:
        match = find_best_match(name, candidate_names, cutoff=cutoff)
        if match:
            mapping[name] = match
    return mapping


def find_best_match(name, choices, cutoff=90):
    # A busca retorna o nome, a pontuação de similaridade e o índice.
    match = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= cutoff:
        return match[0] # Retorna o nome correspondente entre os candidatos.
    return None

def categorize_player(row):
    # Classifica como Bust os jogadores com menos de três temporadas observadas.
    
    if row['seasons_played'] < 3:
        return 0 # Código numérico para Bust
    
    # 2. Classificação por VORP acumulado
    vorp = row['vorp_5y_sum']
    
    if vorp >= 10.0:
        return 3 # Star
    elif vorp >= 3.5:
        return 2 # Starter
    elif vorp >= 0.0:
        return 1 # Rotation
    else:
        return 0 # Bust: VORP acumulado negativo.