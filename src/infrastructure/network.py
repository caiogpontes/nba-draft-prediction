

import time
from typing import Optional
import cloudscraper
import logging
from src.config import ScraperConfig, HEADERS 

logger = logging.getLogger(__name__) 

class NetworkClient:
    """Obtém páginas HTML com reutilização de sessão e novas tentativas."""
    def __init__(self, config: ScraperConfig):
        # Reutiliza a sessão nas requisições.
        self.scraper = cloudscraper.create_scraper() 
        self.config = config

    def get_html(self, url: str, custom_headers: Optional[dict] = None) -> Optional[str]:
        
        
        request_headers = custom_headers if custom_headers else HEADERS

        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self.scraper.get(url, headers=request_headers, timeout=self.config.timeout)
                response.encoding = 'utf-8' 
                
                if response.status_code == 200:
                    if attempt > 1:
                        logger.info(f"Sucesso na tentativa {attempt}/{self.config.max_retries} para {url}")
                    return response.text
                
                logger.warning(f"HTTP {response.status_code} em {url}. Tentativa {attempt}/{self.config.max_retries}")
            
            except Exception as e:
                logger.warning(f"Erro de rede na tentativa {attempt}/{self.config.max_retries}: {e} em {url}")
            
            time.sleep(2 ** attempt)
        
        logger.error(f"Falha definitiva ao acessar: {url} após {self.config.max_retries} tentativas.")
        return None