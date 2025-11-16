import logging
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
from src.config import BASE_URL_BASKETBALL_REF, DRAFT_RENAMES

logger = logging.getLogger(__name__) # Pega o logger configurado

class DraftParser:
    @staticmethod
    def parse(html_content: str, year: int) -> pd.DataFrame:
        try:
            table_id = 'stats'

            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table', {'id': 'stats'})
            if not table: return pd.DataFrame()

            # Extração de Metadata (Links e IDs)
            meta_data = {}
            for row in table.tbody.find_all('tr'):
                player_col = row.find('td', {'data-stat': 'player'})
                if player_col and player_col.find('a'):
                    link_tag = player_col.find('a')
                    p_name = link_tag.text.strip()
                    p_href = link_tag['href']
                    p_id = p_href.split('/')[-1].replace('.html', '')
                    meta_data[p_name] = {'link': BASE_URL_BASKETBALL_REF + p_href, 'id': p_id}

            df = pd.read_html(StringIO(html_content), attrs={'id': 'stats'}, header=1)[0]

            if table_id in DRAFT_RENAMES:
                df.rename(columns=DRAFT_RENAMES[table_id], inplace=True)
            
            # Limpeza
            df = df[df['Pk'] != 'Pk'].copy() # Remove cabeçalhos repetidos
            df['Year'] = year
            df['Player_Link'] = df['Player'].map(lambda x: meta_data.get(x, {}).get('link'))
            df['Player_ID'] = df['Player'].map(lambda x: meta_data.get(x, {}).get('id'))
            
            required = ['Pk', 'Player', 'Player_ID', 'Player_Link', 'College']
            df.dropna(subset=required, inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Erro no Draft {year}: {e}")
            return pd.DataFrame()
