import pandas as pd
from bs4 import BeautifulSoup, Comment
from io import StringIO
from typing import Optional

class HtmlParser:
    """Classe utilitária para manipulação de BeautifulSoup."""
    
    @staticmethod
    def extract_commented_table(soup: BeautifulSoup, table_id: str) -> Optional[pd.DataFrame]:
        """Extrai uma tabela contida em comentários HTML (<!-- ... -->)."""
        # Busca comentários que contenham o ID da tabela
        comments = soup.find_all(string=lambda text: isinstance(text, Comment) and f'id="{table_id}"' in text)
        
        for comment in comments:
            try:
                # Lê o HTML contido no comentário.
                dfs = pd.read_html(StringIO(str(comment)), attrs={'id': table_id})
                if dfs:
                    return dfs[0]
            except ValueError:
                continue
        return None
