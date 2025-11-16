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
                    response.encoding = 'utf-8' 
                    
                    if response.status_code == 200:
                        
                        # --- NOVA LINHA ---
                        # Se não foi a primeira tentativa, avisa que o retry funcionou
                        if attempt > 1:
                            logger.info(f"Sucesso na tentativa {attempt}/{self.config.max_retries} para {url}")
                        # --- FIM DA NOVA LINHA ---
                            
                        return response.text
                    
                    logger.warning(f"HTTP {response.status_code} em {url}. Tentativa {attempt}/{self.config.max_retries}")
                
                except Exception as e:
                    # --- MUDANÇA: de ERROR para WARNING ---
                    # Isso não é um erro fatal ainda, é apenas um aviso de tentativa.
                    logger.warning(f"Erro de rede na tentativa {attempt}/{self.config.max_retries}: {e} em {url}")
                    # --- FIM DA MUDANÇA ---
                
                time.sleep(2 ** attempt) # Backoff exponencial
            
            # Este é o único erro que deve ser 'ERROR'
            logger.error(f"Falha definitiva ao acessar: {url} após {self.config.max_retries} tentativas.")
            return None

