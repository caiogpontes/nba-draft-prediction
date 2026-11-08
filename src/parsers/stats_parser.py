from io import StringIO
import logging
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from src.config import COLLEGE_RENAMES, NBA_RENAMES
from src.parsers.html_helper import HtmlParser
import re

logger = logging.getLogger(__name__) 

class PlayerStatsParser:
    """Regras de Negócio para extração de estatísticas."""

    @staticmethod
    def extract_college_link(html_content: str) -> Optional[str]:
        """Tenta encontrar o link para o Sports Reference (College)."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Textos que indicam que o link é do college
            TARGET_TEXTS = ["College Stats on SR/CBB", "Sports-Reference.com"]
            
            # Itera sobre todas as tags 'a' que possuem 'href'
            for tag in soup.find_all('a', href=True):
                link_text = tag.text
                link_href = tag['href']

                # 1. Verifica se o texto do link bate com o que procuramos
                
                if any(target in link_text for target in TARGET_TEXTS):
                    
                    # 2. Verifica se a URL contém a parte específica de jogadores do college
                    if "cbb/players" in link_href:
                        # Retorna formatado
                        return link_href if link_href.startswith('http') else f"https://www.sports-reference.com{link_href}"
                        
        except Exception as e:
            
            logger.debug(f"Erro ao extrair link do college: {e}")
            
        return None

    @staticmethod
    def parse_stats_nba(html_content: str, table_id: str, player_id: str) -> List[Dict]:
        try: 
            dfs = pd.read_html(StringIO(html_content), attrs={'id': table_id})
            if not dfs: return []
            
            df = dfs[0]
            
            # Filtros e Limpeza
            if 'Season' in df.columns:
                invalid_rows = ['Career', 'Total'] 
                df = df[~df['Season'].astype(str).isin(invalid_rows)].copy()
                df = df[df['Season'].str.contains('-', na=False)] # Apenas temporadas válidas (ex: 2018-19)

            if table_id in NBA_RENAMES:
                df.rename(columns=NBA_RENAMES[table_id], inplace=True)
            
            if 'VORP' in df.columns:
                df['VORP'] = pd.to_numeric(df['VORP'], errors='coerce').fillna(0)

            df['Player_ID'] = player_id
            return df.to_dict('records') 

        except Exception as e:
            logger.debug(f"Erro parsing NBA para {player_id}: {e}")
            return []
        
    

    @staticmethod
    def parse_nba_profile_college(html_content: str, table_id: str ,player_id: str) -> List[Dict]:
        """Extrai estatísticas universitárias do perfil da NBA e remove colunas duplicadas."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. Tenta extrair (via comentário ou direto)
            df = HtmlParser.extract_commented_table(soup, table_id)
            
            if df is None or df.empty:
                dfs = pd.read_html(StringIO(html_content), attrs={'id': table_id})
                if dfs:
                    df = dfs[0]
            
            if df is None or df.empty:
                return []

            # Normaliza os cabeçalhos e remove colunas duplicadas.
            if isinstance(df.columns, pd.MultiIndex):
                # Pega o último nível (Season, Age, MP, PTS...)
                df.columns = df.columns.get_level_values(-1)
            
            # Limpa nomes
            df.columns = [str(c).strip() for c in df.columns]
            
            
            # Mantém a primeira ocorrência de cada coluna (ex: primeiro MP, primeiro PTS)
            df = df.loc[:, ~df.columns.duplicated()].copy()
            

            # Limpeza de Dados
            if 'Season' in df.columns:
                df = df[df['Season'] != 'Season'].copy()
                invalid_rows = ['Career', 'Total']
                df = df[~df['Season'].astype(str).isin(invalid_rows)].copy()
                df = df[df['Season'].astype(str).str.contains(r'\d', na=False)].copy()

            if table_id in NBA_RENAMES:
                df.rename(columns=NBA_RENAMES[table_id], inplace=True)

            # Conversão das colunas numéricas.
            cols_to_numeric = ['G', 'MP', 'FG', 'FGA', '3P', '3PA', 'FT', 'FTA', 'TRB', 'AST', 'STL', 'BLK', 'PTS', 'Age']
            for col in cols_to_numeric:
                if col in df.columns:
                    
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            df['Player_ID'] = player_id
            
            return df.to_dict('records')

        except Exception as e:
            logger.debug(f"Tabela College (NBA Profile) não encontrada ou erro de parse para {player_id}: {e}")
            return []

    @staticmethod
    def parse_stats_college(html_content: str, table_id: str, player_id: str) -> List[Dict]:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Usa o helper para extrair tabela comentada
            df = HtmlParser.extract_commented_table(soup, table_id)
            
            if df is None or df.empty:
                return []

            if 'Season' in df.columns:
                invalid_rows = ['Career', 'Total']
                df = df[~df['Season'].astype(str).isin(invalid_rows)].copy()
                df = df[df['Season'].str.contains('-', na=False)] # Apenas temporadas válidas (ex: 2018-19)

            # Padroniza os nomes das colunas conforme a configuração.
            if table_id in COLLEGE_RENAMES:
                df.rename(columns=COLLEGE_RENAMES[table_id], inplace=True)

            df['Player_ID'] = player_id
            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Erro parsing College ({table_id}) para {player_id}: {e}")
            return []
        
    @staticmethod
    def extract_player_metadata(html_content: str, player_id: str) -> Dict:
        """Extrai posição, altura, peso e classificação RSCI do perfil universitário."""
        import re 
        
        metadata = {
            'Player_ID': player_id,
            'Position': None,
            'Height_Weight_Raw': None,
            'RSCI_Rank': None,
            'RSCI_Year': None
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            info_div = soup.find('div', {'id': 'info'})
            
            if info_div:
                # Itera sobre TODOS os parágrafos dentro do bloco de informação
                for p_tag in info_div.find_all('p'):
                    p_text = p_tag.text.strip()
                    
                    # 1a. Posição
                    if p_text.startswith('Position:'):
                        metadata['Position'] = p_text.replace('Position:', '').strip()
                        
                    # 1b. Altura e Peso (Procura por 'lb' e 'kg' no texto)
                    elif 'lb' in p_text and 'kg' in p_text:
                        hw_parts = p_text.split('(')
                        metadata['Height_Weight_Raw'] = hw_parts[0].strip() # Ex: 6-10, 252lb

                    # 2. RSCI Top 100
                    elif p_text.startswith('RSCI Top 100:'):
                        rsci_text = p_text.split(':')[-1].strip() 
                        
                        match = re.search(r'(\d+)\s*\((\d{4})\)', rsci_text)
                        if match:
                            metadata['RSCI_Rank'] = int(match.group(1))
                            metadata['RSCI_Year'] = int(match.group(2))
            
        except Exception as e:
            logger.error(f"Erro ao extrair metadados para {player_id}: {e}")
            
        return metadata