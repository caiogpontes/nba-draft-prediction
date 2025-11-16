import time
from typing import Optional
import cloudscraper
import logging
from src.config import ScraperConfig, HEADERS

logger = logging.getLogger(__name__) # Pega o logger configurado

class NetworkClient:
    """Responsável apenas por buscar o conteúdo HTML (Single Responsibility Principle)."""
    def __init__(self, config: ScraperConfig):
        self.scraper = cloudscraper.create_scraper()
        self.config = config

    def get_html(self, url: str) -> Optional[str]:
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self.scraper.get(url, headers=HEADERS, timeout=self.config.timeout)
                response.encoding = 'utf-8' # Força UTF-8
                
                if response.status_code == 200:
                    return response.text
                
                logger.warning(f"HTTP {response.status_code} em {url}. Tentativa {attempt}/{self.config.max_retries}")
            
            except Exception as e:
                logger.error(f"Erro de rede: {e} em {url}")
            
            time.sleep(2 ** attempt) # Backoff exponencial
        
        logger.error(f"Falha definitiva ao acessar: {url}")
        return None

