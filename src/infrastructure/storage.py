import os
import pandas as pd
import logging

logger = logging.getLogger(__name__) # Pega o logger configurado

class DataManager:
    """Responsável por Ler e Salvar arquivos com robustez."""
    
    @staticmethod
    def save_csv(df: pd.DataFrame, filename: str):
        try:
            # Garante diretório se não existir (opcional, mas boa prática)
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            logger.info(f"Arquivo salvo: '{filename}' ({len(df)} registros).")
        except Exception as e:
            logger.error(f"Erro fatal ao salvar {filename}: {e}")

    @staticmethod
    def load_csv(filename: str) -> pd.DataFrame:
        if not os.path.exists(filename):
            logger.warning(f"Arquivo '{filename}' não encontrado. Retornando DataFrame vazio.")
            return pd.DataFrame()
        
        try:
            # Tenta ler padrão
            df = pd.read_csv(filename)
            # Detecção automática de erro de separador (comum em Excel BR)
            if len(df.columns) == 1 and ';' in str(df.iloc[0,0]): 
                logger.info("Detectado separador ';'. Recarregando arquivo...")
                df = pd.read_csv(filename, sep=';')
            return df
        except Exception as e:
            logger.error(f"Erro ao ler {filename}: {e}")
            return pd.DataFrame()
