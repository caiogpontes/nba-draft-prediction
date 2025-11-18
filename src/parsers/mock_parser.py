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
        """ 
        Tenta parsear usando a lógica antiga (baseada em '1.0' e shape). 
        Este é o "roteiro" limpo que chama os helpers.
        """
        
        # --- FIX V31: Inicializa a variável para evitar NameError ---
        found_df = None
        col_0_values = None 
        # -----------------------------------------------------------

        # --- 1. Encontra a Tabela ---
        for df_table in all_tables:
            if df_table.empty or df_table.shape[1] < 3:
                continue
            
            # A variável é atribuída aqui, dentro do loop
            col_0_values = df_table.iloc[:, 0].astype(str).str.strip() 
            if col_0_values.isin(MockDraftParser._OLD_FORMAT_PK_VALUES).any():
                found_df = df_table.copy() 
                break 
        
        if found_df is None:
            return None # Falha: Não encontrou formato antigo

        # --- 2. Reformata o DataFrame ---
        df_combined = MockDraftParser._reshape_old_table(found_df, year)
        if df_combined is None:
            logger.warning(f"Formato antigo encontrado, mas não pôde ser reformatado (Ano: {year}).")
            return None

        # --- 3. Extrai e Limpa os Dados ---
        df_final = MockDraftParser._extract_old_data(df_combined, year)
        
        return df_final

    @staticmethod
    def _reshape_old_table(df: pd.DataFrame, year: int) -> Optional[pd.DataFrame]:
        """ Helper que contém a lógica de 'shape'. """
        
        shape = df.shape[1]
        
        if shape == 8: # Formato 2001-2008
            logger.debug("Processando tabela como 8 colunas (Formato 2001-2008).")
            
            # --- FIX V32: Concatenação de Nome e Remoção do Index Out-of-Bounds ---
            if 2001 <= year <= 2008:
                logger.debug(f"APLICANDO CORREÇÃO DE NOME CONCATENADO para o ano {year}.")
                
                # O problema é que o Nome do Jogador 1 (Col 3) está dividido na Col 4.
                # Corrigimos isso juntando a Col 3 + Col 4 (se Col 4 existir, ou seja, shape > 4).
                if shape > 4: 
                    # Col 3 = Nome + Col 4 = Resto
                    df[3] = df[3].astype(str).str.strip() + ' ' + df[4].astype(str).str.strip()
                
                # Não tentamos mais acessar df[8], pois o shape é 8 (índices 0-7).
            # ----------------------------------------------------------------------

            # Agora, a Col 3 contém o nome COMPLETO do primeiro jogador.
            # E a Col 7 contém a informação do segundo jogador.
            df_part1 = df.iloc[:, [0, 2, 3]].copy()
            df_part1.columns = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']
            df_part2 = df.iloc[:, [4, 6, 7]].copy()
            df_part2.columns = ['Mock_Pick_Raw', 'Team_Raw', 'Player_Info_Raw']
            return pd.concat([df_part1, df_part2], ignore_index=True)
        
        # ... (Restante do código para shape == 6 e shape >= 3 permanece igual)
        
        return None
    
    @staticmethod
    def _extract_old_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
        """ 
        Helper V33: Corrige o bug de truncamento (Matt -> Matt Freije) 
        usando um regex de captura direcionado para Altura.
        """
        import re # Garante que está importado

        df['Year'] = year
        df['Mock_Pick'] = pd.to_numeric(df['Mock_Pick_Raw'], errors='coerce').astype('Int64')
        df.dropna(subset=['Mock_Pick', 'Player_Info_Raw'], inplace=True)
        
        # Remove caracteres problemáticos da string raw antes de tudo
        info_raw_series = df['Player_Info_Raw'].astype(str).str.replace(r'[\(\)\*."]', '', regex=True).str.strip()
        
        # --- Extração V33 ---
        
        # 1. Extrai Class e Pos (permanece igual, pois funcionam)
        df['Class'] = info_raw_series.str.extract(MockDraftParser._CLASS_PATTERN).iloc[:, 0].fillna('Unknown')
        df['Pos'] = info_raw_series.str.extract(MockDraftParser._POS_PATTERN).iloc[:, 0].fillna('Unknown')
        df['Team'] = df['Team_Raw'].astype(str).str.strip()

        # 2. Extrai Player (Lógica Principal de Limpeza)
        if 2001 <= year <= 2008:
            # --- NOVO REGEX DE CAPTURA: Captura TUDO que vem antes da altura (ex: 6-9) ---
            # Padrão: (.*?) = Grupo de captura 1 (o que queremos)
            # \s[567]-\d = Ponto de parada (espaço + Altura)
            height_capture_pattern = re.compile(r'(.*?)\s[567]-\d{1,2}')
            
            # Tenta capturar o nome/college. Retorna NaN se a altura não for encontrada.
            player_col_extracted = info_raw_series.str.extract(height_capture_pattern, expand=False)
            
            # Se a extração falhar (NaN), a string original era curta e já é o nome (usamos fillna)
            # Isso é robusto contra erros de Altura
            df['Player'] = player_col_extracted.fillna(info_raw_series).str.strip()
            
        elif year == 2000:
            # Regra de 2 palavras para o ano 2000
            df['Player'] = info_raw_series.apply(
                lambda x: " ".join(x.split()[:2]) if isinstance(x, str) else x
            )
        else:
            # Fallback (usa a string como está se o ano não se encaixar)
            df['Player'] = info_raw_series.str.strip()
        
        # Seleciona as colunas finais
        df_final = df[['Year', 'Mock_Pick', 'Player', 'Team', 'Class', 'Pos']].copy()
        
        return df_final