# src/parsers/mock_parser.py
import pandas as pd
import logging
from io import StringIO
from typing import Optional, List
import re 
from src.config import MOCK_DRAFT_RENAMES # Importa do config

logger = logging.getLogger(__name__)

class MockDraftParser:
    """
    Parser V27: Versão final com regra de limpeza forçada.
    - Aplica a regra de "Manter apenas as 2 primeiras palavras" no nome
      do jogador para os formatos antigos (2000-2008), removendo College/Time.
    """
    
    # --- Constantes de Classe (V27) ---
    
    _CLASS_PATTERN = re.compile(r'(Fr|So|Jr|Sr|HSSr)', re.IGNORECASE)
    _POS_PATTERN = re.compile(r'\b(C|PF|SF|SG|PG|G|F|PG/SG|SG/SF|SF/PF)\b')
    
    # V27 - MASTER SPLIT PATTERN
    _OLD_FORMAT_SPLIT_PATTERN = re.compile(r"""
        \s                        # Encontra um espaço
        (?=                       # Seguido por (Lookahead):
            # 1. Altura (com ou sem ponto, ex: ". 6-9" ou " 7-0")
            (\.?"?\s?[567]-\d{1,2})
            |                     # OU
            # 2. Classe (ex: Sr, Jr)
            (Fr|So|Jr|Sr|HSSr)
            |                     # OU
            # 3. Posição (ex: PF, C, PG/SG)
            (\b(C|PF|SF|SG|PG|G|F|PG/SG|SG/SF|SF/PF)\b)
        )
    """, re.IGNORECASE | re.VERBOSE)

    _REQUIRED_MODERN_COLS = {'Mock_Pick', 'Player', 'College'}
    _OLD_FORMAT_PK_VALUES = ["1", "1.", "1.0"]

    
    @staticmethod
    def parse(html_content: str, year: int) -> Optional[pd.DataFrame]:
        """
        Método principal (Dispatcher).
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
            
            df_old = MockDraftParser._parse_old(all_tables, year) 
            
            if df_old is not None:
                logger.debug(f"Formato ANTIGO detectado e parseado para {year}.")
                return df_old
            
            logger.warning(f"Nenhuma tabela válida (moderna ou antiga) foi encontrada no ano {year}.")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Erro fatal no dispatcher do parse {year}: {e}")
            return pd.DataFrame()

    @staticmethod
    def _parse_modern(all_tables: List[pd.DataFrame], year: int) -> Optional[pd.DataFrame]:
        """ Tenta parsear usando a lógica moderna. """
        found_tables_buffer = [] 
        
        for df_table in all_tables:
            df = df_table.copy()
            df.rename(columns=MOCK_DRAFT_RENAMES, inplace=True, errors='ignore')

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
    def _parse_old(all_tables: List[pd.DataFrame], year: int) -> Optional[pd.DataFrame]:
        """ Tenta parsear usando a lógica antiga. """
        
        # --- 1. Encontra a Tabela ---
        found_df = None
        for df_table in all_tables:
            if df_table.empty or df_table.shape[1] < 3:
                continue
            
            col_0_values = df_table.iloc[:, 0].astype(str).str.strip()
            if col_0_values.isin(MockDraftParser._OLD_FORMAT_PK_VALUES).any():
                found_df = df_table.copy() 
                break 
        
        if found_df is None:
            return None 

        # --- 2. Reformata o DataFrame ---
        df_combined = MockDraftParser._reshape_old_table(found_df)
        if df_combined is None:
            logger.warning(f"Formato antigo encontrado, mas não pôde ser reformatado (Ano: {year}).")
            return None

        # --- 3. Extrai e Limpa os Dados ---
        df_final = MockDraftParser._extract_old_data(df_combined, year)
        
        return df_final

    @staticmethod
    def _reshape_old_table(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """ Helper que contém a lógica de 'shape'. """
        
        shape = df.shape[1]
        
        if shape == 8: # Formato 2001-2008
            logger.debug("Processando tabela como 8 colunas (Formato 2001-2008).")
            df_part1 = df.iloc[:, [0, 2, 3]].copy()
            df_part1.columns = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']
            df_part2 = df.iloc[:, [4, 6, 7]].copy()
            df_part2.columns = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']
            return pd.concat([df_part1, df_part2], ignore_index=True)
        
        elif shape == 6: # Formato 2000
            logger.debug("Processando tabela como 6 colunas (Formato 2000).")
            df_part1 = df.iloc[:, [0, 1, 2]].copy()
            df_part1.columns = ['Mock_Pick_Raw', 'Player_Info_Raw', 'Team_Raw']
            
            df_part2 = df.iloc[:, [3, 4, 5]].copy()
            df_part2.columns = ['Mock_Pick_Raw', 'Player_Info_Raw', 'Team_Raw']
            return pd.concat([df_part1, df_part2], ignore_index=True)
        
        elif shape >= 3: # Formato 3 colunas (fallback)
            logger.debug("Processando tabela como 3 colunas.")
            col_names = ['Mock_Pick_Raw', 'Player_Info_Raw', 'Team_Raw']
            df_combined = df.iloc[:, :3].copy()
            df_combined.columns = col_names
            return df_combined
            
        return None # Formato inesperado

    @staticmethod
    def _extract_old_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
        """ 
        Helper V27: Corrige a poluição da string 'Player_Info_Raw' 
        removendo o nome do Time.
        """
        
        df['Year'] = year
        df['Mock_Pick'] = pd.to_numeric(df['Mock_Pick_Raw'], errors='coerce').astype('Int64')
        df.dropna(subset=['Mock_Pick', 'Player_Info_Raw'], inplace=True)
        
        # --- V27 FIX: Remove o Nome do Time da String Raw ---
        if 2001 <= year <= 2008:
            # 1. Cria uma coluna do Time limpa para ser usada na substituição
            df['Team_Clean'] = df['Team_Raw'].astype(str).str.replace(r'[\(\)\*]', '', regex=True).str.strip()
            
            # 2. Remove o Team_Clean da Player_Info_Raw. (Usamos apply e replace(..., 1) para remover apenas a primeira ocorrência)
            df['Player_Info_Raw'] = df.apply(
                lambda row: str(row['Player_Info_Raw']).replace(row['Team_Clean'], '', 1).strip(),
                axis=1
            )
        else:
            # Para o ano 2000 e outros, o Team_Raw é o College/Time
            df['Team_Clean'] = df['Team_Raw'].astype(str).str.strip()
        # -----------------------------------------------------------------

        info_raw_series = df['Player_Info_Raw'].astype(str)
        
        # --- Extração ---
        
        # 1. Extrai Class (ex: Sr, So)
        df['Class'] = info_raw_series.str.extract(MockDraftParser._CLASS_PATTERN).iloc[:, 0].fillna('Unknown')
        
        # 2. Extrai Posição (ex: PF, C, PG/SG)
        df['Pos'] = info_raw_series.str.extract(MockDraftParser._POS_PATTERN).iloc[:, 0].fillna('Unknown')

        # 3. Extrai Player (Limpando a string)
        split_pattern_class = re.compile(r'\s(HSSr|Sr|Jr|So|Fr)', re.IGNORECASE)
        split_pattern_pos = re.compile(r'\s(C|PF|SF|SG|PG|G|F|PG/SG|SG/SF|SF/PF)\b')

        # Usa o Master Split Pattern para quebrar no primeiro delimitador
        temp_player_col = info_raw_series.str.split(
            MockDraftParser._OLD_FORMAT_SPLIT_PATTERN, 
            n=1, 
            regex=True
        ).str[0]
        
        # Limpa pontuações extras e aplica a REGRA DE 2 PALAVRAS (V28)
        temp_player_col = temp_player_col.str.replace(r'[\(\)\*."]', '', regex=True).str.strip()
        
        if year == 2000:
            # Regra de 2 palavras para o ano 2000
            df['Player'] = temp_player_col.apply(
                lambda x: " ".join(x.split()[:2]) if isinstance(x, str) else x
            )
        else:
            # Nos outros anos, confiamos que o split limpou a faculdade/altura
            df['Player'] = temp_player_col
        
        # Seleciona as colunas finais
        df['Team'] = df['Team_Clean'] # Usa a coluna Team limpa
        
        df_final = df[['Year', 'Mock_Pick', 'Player', 'Team', 'Class', 'Pos']].copy()
        
        return df_final
