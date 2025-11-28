# src/utils/converters.py
import math
import re
from typing import Tuple, Optional
from unidecode import unidecode 
import pandas as pd

def feet_to_meters(feet: float) -> float:
    """Converte pés (como float, ex: 6.5) para metros."""
    return round(feet * 0.3048, 2)

def _parse_height_weight_string(hw_str: Optional[str]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Parses a string like '6-5, 200lb' into (feet, inches, pounds).
    Returns (None, None, None) on failure.
    """
    if not hw_str or not isinstance(hw_str, str):
        return None, None, None
        
    # Regex para capturar PÉS, POLEGADAS e PESO
    # Ex: (6-5, 200lb) ou (6-10, 252lb)
    # Regex mais flexível para espaços: permite '6-5, 200lb', '6-5,200lb', '6-5 , 200 lb' etc.
    match = re.search(r'(\d+)-(\d+)\s*,\s*(\d+)\s*lb', hw_str)
    
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        pounds = int(match.group(3))
        return feet, inches, pounds
    else:
        return None, None, None

def inches_to_cm(inches: Optional[float]) -> Optional[float]:
    """
    Converte altura de polegadas (decimal) para centímetros.
    Ex: 75.5 -> 191.8 cm
    """
    # Verifica se o valor é nulo/vazio (NaN) antes de calcular
    if inches is None or (isinstance(inches, float) and math.isnan(inches)):
        return None
        
    CM_PER_INCH = 2.54
    return round(inches * CM_PER_INCH, 1)

def ft_in_to_cm(ft: Optional[int], inches: Optional[int]) -> Optional[float]:
    """Converte altura de pés e polegadas para centímetros."""
    if ft is None or inches is None:
        return None
        
    CM_PER_INCH = 2.54
    TOTAL_INCHES = (ft * 12) + inches
    return round(TOTAL_INCHES * CM_PER_INCH, 1)


def lbs_to_kg(lbs: Optional[int]) -> Optional[float]:
    """Converte peso de libras (lbs) para quilogramas (kg)."""
    if lbs is None:
        return None
        
    KG_PER_LB = 0.453592
    return round(lbs * KG_PER_LB, 1)

def class_to_int(class_str: Optional[str]) -> Optional[int]:
    """
    Converte a string de ano escolar (Class) em um número inteiro ordinal.
    
    Mapeamento:
    FR (Freshman)  -> 1
    SO (Sophomore) -> 2
    JR (Junior)    -> 3
    SR (Senior)    -> 4
    GR/GS (Grad)   -> 5
    """
    if not class_str or not isinstance(class_str, str):
        return None

    # 1. Normalização: Remove espaços, pontos e joga para maiúsculo
    # Ex: "Sr." -> "SR", "  so " -> "SO"
    clean_str = class_str.strip().replace('.', '').upper()

    # 2. Dicionário de Mapeamento
    class_map = {
        'FR': 1,
        'FRESHMAN': 1, # Caso apareça por extenso
        'SO': 2,
        'SOPHOMORE': 2,
        'JR': 3,
        'JUNIOR': 3,
        'SR': 4,
        'SENIOR': 4,
        'GR': 5,
        'GS': 5,
        'GRAD': 5,
        'HSSR': 0  # Sugestão: High School Senior (comum em dados antigos)
    }

    return class_map.get(clean_str, None)

def clean_name(name):
    if pd.isna(name): return ""
    # 1. Minúsculo
    name = str(name).lower()
    # 2. Remove acentos (Dončić -> Doncic)
    name = unidecode(name)
    # 3. Remove pontuação (C.J. -> cj) e sufixos comuns
    name = name.replace(".", "").replace("'", "").replace("-", " ").replace("...", " ")
    name = name.replace(" jr", "").replace(" iii", "").replace(" ii", "").replace(" iv", "")
    # 4. Abreviações comuns
    name = name.replace("william", "will")  
    name = name.replace("mohamed", "mo")
    return name.strip()

