# src/parsers/mock_parser.py
import pandas as pd
import logging
from io import StringIO
from typing import Optional, List, Dict
import re # <-- Movid_para o topo
from src.config import MOCK_DRAFT_RENAMES

logger = logging.getLogger(__name__)

class MockDraftParser:
    """
    - Constantes definidas para Regex ("Valores Mágicos").
    - _parse_antigo foi quebrado em helpers (SRP).
    """
    
    # --- Constantes de Classe (Auto-documentação) ---
    
    # Regex para extrair "Fr", "So", "Jr", "Sr", "HSSr"
    _CLASS_PATTERN = re.compile(r'\b(Fr|So|Jr|Sr|HSSr)\b', re.IGNORECASE)
    
    # Regex para separar o nome do jogador do resto (ex: "Nome 6-10 ...")
    _PLAYER_NAME_SPLIT_PATTERN = re.compile(r'\s(?=[567]-\d{1,2})')
    
    # Colunas que definem uma tabela "moderna" (após padronização)
    _REQUIRED_MODERN_COLS = {'Mock_Pick', 'Player', 'College'}
    
    # Valores que definem uma tabela "antiga" na primeira coluna
    _ANTIGO_PK_VALUES = ["1", "1.", "1.0"]

    
    @staticmethod
    def parse(html_content: str, year: int) -> Optional[pd.DataFrame]:
        """
        Método principal (Dispatcher). Tenta o formato moderno primeiro,
        depois faz fallback para o formato antigo.
        """
        try:
            all_tables = pd.read_html(StringIO(html_content))
            if not all_tables:
                logger.warning(f"Nenhuma tabela HTML encontrada na página do ano {year}.")
                return pd.DataFrame()
        except Exception as e:
            logger.warning(f"Erro de parsing inicial (pd.read_html) no ano {year}: {e}")
            return pd.DataFrame()

        try:
            # --- Estratégia 1: Tenta o Moderno ---
            df_modern = MockDraftParser._parse_modern(all_tables, year)
            if df_modern is not None:
                logger.debug(f"Formato MODERNO detectado e parseado para {year}.")
                return df_modern

            # --- Estratégia 2: Fallback para o Antigo ---
            logger.debug(f"Formato moderno não encontrado para {year}. Tentando formato ANTIGO...")
            df_antigo = MockDraftParser._parse_antigo(all_tables, year)
            if df_antigo is not None:
                logger.debug(f"Formato ANTIGO detectado e parseado para {year}.")
                return df_antigo
            
            logger.warning(f"Nenhuma tabela válida (moderna ou antiga) foi encontrada no ano {year}.")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Erro fatal no dispatcher do parse {year}: {e}")
            return pd.DataFrame()

    @staticmethod
    def _parse_modern(all_tables: List[pd.DataFrame], year: int) -> Optional[pd.DataFrame]:
        """ Tenta parsear usando a lógica moderna (baseada em cabeçalhos V14). """
        found_tables_buffer = [] 
        
        for df_table in all_tables:
            df = df_table.copy()
            df.rename(columns=MOCK_DRAFT_RENAMES, inplace=True, errors='ignore')

            # Usa a constante de classe
            if MockDraftParser._REQUIRED_MODERN_COLS.issubset(set(df.columns)):
                logger.debug(f"Formato moderno: Tabela candidata encontrada (Shape={df.shape})")
                found_tables_buffer.append(df)
        
        if not found_tables_buffer:
            return None

        df_combined = pd.concat(found_tables_buffer, ignore_index=True)
        df_combined['Year'] = year
        df_combined['Mock_Pick'] = pd.to_numeric(df_combined.get('Mock_Pick'), errors='coerce').astype('Int64')
        df_combined.dropna(subset=['Mock_Pick', 'Player'], inplace=True)
        df_combined.drop_duplicates(subset=['Year', 'Mock_Pick'], keep='first', inplace=True)
        
        final_col_names = list(set(MOCK_DRAFT_RENAMES.values()))
        cols_to_keep = [col for col in final_col_names if col in df_combined.columns]
        cols_to_keep.append('Year')

        return df_combined[cols_to_keep].sort_values(by='Mock_Pick')

    @staticmethod
    def _parse_antigo(all_tables: List[pd.DataFrame], year: int) -> Optional[pd.DataFrame]:
        """ Tenta parsear usando a lógica antiga (baseada em '1.0' e shape). """
        
        # --- 1. Encontra a Tabela ---
        found_df = None
        for df_table in all_tables:
            if df_table.empty or df_table.shape[1] < 3:
                continue
            
            col_0_values = df_table.iloc[:, 0].astype(str).str.strip()
            # Usa a constante de classe
            if col_0_values.isin(MockDraftParser._ANTIGO_PK_VALUES).any():
                found_df = df_table.copy()
                break 
        
        if found_df is None:
            return None # Falha: Não encontrou formato antigo

        # --- 2. Reformata a Tabela ---
        df_combined = MockDraftParser._reshape_antigo_table(found_df)
        if df_combined is None:
            logger.warning(f"Formato antigo encontrado, mas não pôde ser reformatado (Ano: {year}).")
            return None

        # --- 3. Extrai e Limpa os Dados ---
        df_final = MockDraftParser._extract_antigo_data(df_combined, year)
        
        return df_final

    @staticmethod
    def _reshape_antigo_table(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """ Helper que contém a lógica de 'shape' (8, 6, 3 colunas). """
        
        shape = df.shape[1]
        
        if shape == 8: # Formato 2001
            logger.debug("Processando tabela como 8 colunas (Formato até 2008).")
            df_part1 = df.iloc[:, [0, 2, 3]].copy()
            df_part1.columns = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']
            df_part2 = df.iloc[:, [4, 6, 7]].copy()
            df_part2.columns = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']
            return pd.concat([df_part1, df_part2], ignore_index=True)
        
        elif shape == 6: # Formato 6 colunas
            logger.debug("Processando tabela como 6 colunas.")
            col_names = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw',
                         'Mock_Pick_Raw_2', 'Team_Raw_2', 'Player_Info_Raw_2']
            df.columns = col_names
            df_part1 = df[['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']].copy()
            df_part2 = df[['Mock_Pick_Raw_2', 'Team_Raw_2', 'Player_Info_Raw_2']].copy()
            df_part2.columns = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']
            return pd.concat([df_part1, df_part2], ignore_index=True)
        
        elif shape >= 3: # Formato 3 colunas
            logger.debug("Processando tabela como 3 colunas.")
            col_names = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']
            df_combined = df.iloc[:, :3].copy()
            df_combined.columns = col_names
            return df_combined
            
        return None # Formato inesperado

    @staticmethod
    def _extract_antigo_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
        """ Helper que limpa e extrai dados do DataFrame antigo reformatado. """
        
        df['Year'] = year
        df['Mock_Pick'] = pd.to_numeric(df['Mock_Pick_Raw'], errors='coerce').astype('Int64')
        df.dropna(subset=['Mock_Pick', 'Player_Info_Raw'], inplace=True)
        
        # Converte para string para garantir que .str funcione
        info_raw = df['Player_Info_Raw'].astype(str)
        
        # --- Extração usando Constantes de Classe ---
        
        # 1. Extrai Player
        df['Player'] = info_raw.str.split(MockDraftParser._PLAYER_NAME_SPLIT_PATTERN, n=1).str[0].str.strip()
        
        # 2. Extrai Class
        df['Class'] = info_raw.str.extract(MockDraftParser._CLASS_PATTERN).fillna('Unknown')

        # 3. Extrai Team
        df['Team'] = df['Team_Raw'].astype(str).str.strip()
        
        df_final = df[['Year', 'Mock_Pick', 'Player', 'Team', 'Class']].copy()
        
        return df_final