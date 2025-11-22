# src/utils/converters.py
import math
import re
from typing import Tuple, Optional


def ft_in_to_cm(ft: int, inches: int) -> float:
    """Converte altura de pés e polegadas para centímetros."""
    TOTAL_INCHES = (ft * 12) + inches
    CM_PER_INCH = 2.54
    return round(TOTAL_INCHES * CM_PER_INCH, 1)

def feet_to_meters(feet: float) -> float:
    """Converte pés (como float, ex: 6.5) para metros."""
    return round(feet * 0.3048, 2)

def inches_to_cm(inches: float) -> float:
    """
    Converte altura de polegadas (decimal) para centímetros.
    Ex: 75.5 -> 191.8 cm
    """
    # Verifica se o valor é nulo/vazio (NaN) antes de calcular
    if inches is None or (isinstance(inches, float) and math.isnan(inches)):
        return None
        
    CM_PER_INCH = 2.54
    return round(inches * CM_PER_INCH, 1)



def _parse_height_weight_string(hw_str: Optional[str]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Parses a string like '6-5, 200lb' into (feet, inches, pounds).
    Returns (None, None, None) on failure.
    """
    if not hw_str:
        return None, None, None
        
    # Regex para capturar PÉS, POLEGADAS e PESO
    # Ex: (6-5, 200lb) ou (6-10, 252lb)
    match = re.search(r'(\d+)-(\d+),\s*(\d+)lb', hw_str)
    
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        pounds = int(match.group(3))
        return feet, inches, pounds
    else:
        return None, None, None


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