from io import StringIO
import logging
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from src.config import COLLEGE_RENAMES, NBA_RENAMES
from src.parsers.html_helper import HtmlParser

logger = logging.getLogger(__name__) # Pega o logger configurado

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
                # (O uso de 'any' deixa mais limpo que vários 'or')
                if any(target in link_text for target in TARGET_TEXTS):
                    
                    # 2. Verifica se a URL contém a parte específica de jogadores do college
                    if "cbb/players" in link_href:
                        # Retorna formatado
                        return link_href if link_href.startswith('http') else f"https://www.sports-reference.com{link_href}"
                        
        except Exception as e:
            # É boa prática logar o erro em vez de apenas 'pass', para debug futuro
            logger.debug(f"Erro ao extrair link do college: {e}")
            
        return None

    @staticmethod
    def parse_stats_nba(html_content: str, player_id: str) -> List[Dict]:
        try:
            table_id = 'advanced'

            dfs = pd.read_html(StringIO(html_content), attrs={'id': table_id})
            if not dfs: return []
            
            df = dfs[0]
            
            # Filtros e Limpeza
            if 'Season' in df.columns:
                invalid_rows = ['Career', 'Total', '2025-2026']
                df = df[~df['Season'].astype(str).isin(invalid_rows)].copy()
                df = df[df['Season'].str.contains('-', na=False)] # Apenas temporadas válidas (ex: 2018-19)

            if table_id in NBA_RENAMES:
                df.rename(columns=NBA_RENAMES[table_id], inplace=True)
            
            if 'VORP' in df.columns:
                df['VORP'] = pd.to_numeric(df['VORP'], errors='coerce').fillna(0)

            df['Player_ID'] = player_id
            return df.head(5).to_dict('records')

        except Exception as e:
            logger.debug(f"Erro parsing NBA para {player_id}: {e}")
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

            # Aplica renomeação baseada no dicionário externo (OCP Compliance)
            if table_id in COLLEGE_RENAMES:
                df.rename(columns=COLLEGE_RENAMES[table_id], inplace=True)

            df['Player_ID'] = player_id
            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Erro parsing College ({table_id}) para {player_id}: {e}")
            return []
