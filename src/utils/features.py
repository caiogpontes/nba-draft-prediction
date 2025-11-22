# src/utils/features.py

import pandas as pd
from typing import Literal

def calculate_proxy_usage(df: pd.DataFrame, source: Literal['per40', 'per100']) -> pd.DataFrame:
    """
    Cria a coluna Proxy_Usage (volume de responsabilidade) a partir de métricas brutas.
    
    Atenção: Assume que as colunas já estão escaladas (ex: FGA_per40).
    """
    
    # 1. Define os sufixos corretos baseados na fonte de dados
    if source == 'per40':
        suffix = '_per40'
    elif source == 'per100':
        suffix = '_per100' # Se você usar Per 100 Possessions
    else:
        raise ValueError("A fonte deve ser 'per40' ou 'per100'.")

    # 2. Define as colunas de entrada
    fga_col = 'FGA' + suffix
    fta_col = 'FTA' + suffix
    tov_col = 'TOV' + suffix
    
    # 3. Garante que as colunas existam (evita KeyErrors)
    required_cols = [fga_col, fta_col, tov_col]
    if not all(col in df.columns for col in required_cols):
        raise KeyError(f"DataFrame College não contém as colunas necessárias para {source}: {required_cols}")

    # 4. Cálculo da Proxy Usage
    df['Proxy_Usage'] = (
        df[fga_col] + 
        (0.44 * df[fta_col]) + 
        df[tov_col]
    )
    
    return df