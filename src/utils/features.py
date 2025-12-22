# src/utils/features.py

import pandas as pd
from typing import Literal
from rapidfuzz import process, fuzz

def calculate_proxy_usage(FGA: float, FTA: float, TOV: float) -> float:
    """
    Cria a coluna Proxy_Usage (volume de responsabilidade) a partir de métricas brutas.
    
    Atenção: Assume que as colunas já estão escaladas (ex: FGA_per40).
    """
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

# 2. Função para achar o melhor match
def find_best_match(name, choices, cutoff=90):
    # Retorna (Melhor Match, Score, Index)
    match = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= cutoff:
        return match[0] # Retorna o nome encontrado na tabela Draft
    return None

def categorize_player(row):
    # 1. Regra Eliminatória: Se jogou menos de 3 temporadas, é 'Bust' automaticamente
    # (Independente do VORP, pois pode ter feito VORP 0.1 em 10 jogos e sumido)
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
        return 0 # Bust (Mesmo jogando 5 anos, se o VORP é negativo, foi ruim)