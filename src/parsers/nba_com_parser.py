# src/parsers/nba_com_parser.py
import pandas as pd
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

class NbaComParser:
    """
    Parser dedicado para a API stats.nba.com (JSON).
    """

    @staticmethod
    def parse(json_content: str, year: int) -> Optional[pd.DataFrame]:
        """
        Converte a resposta JSON da API da NBA (que possui estrutura aninhada) 
        em um DataFrame, utilizando os headers e rowSet extraídos.
        """
        try:
            # 1. Decodifica o JSON em um dicionário Python
            data = json.loads(json_content)
            
            # 2. Valida a Estrutura
            if not data.get('resultSets'):
                logger.warning(f"JSON da NBA não contém 'resultSets' para o ano {year}.")
                return pd.DataFrame() # Retorna DF vazio para consistência

            result_set = data['resultSets'][0]
            headers = result_set['headers']
            rows = result_set['rowSet']

            if not rows:
                logger.info(f"Nenhum dado de Combine encontrado na API para o ano {year}.")
                return pd.DataFrame() 

            # 3. CONSTRUÇÃO CORRETA DO DATAFRAME (Substitui a linha com erro)
            # O Pandas precisa dos cabeçalhos e das linhas como duas listas separadas.
            df = pd.DataFrame(rows, columns=headers) 
            
            # 4. Adiciona o ano de referência (Season_Year) para controle e merge
            df['Season_Year'] = year
            
            return df

        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar JSON da NBA para o ano {year}. Conteúdo pode ser HTML de erro.")
            return None
        except Exception as e:
            # Captura exceções genéricas (ex: KeyError se a estrutura mudar)
            logger.error(f"Erro genérico no parser da NBA ({year}): {e}")
            return None