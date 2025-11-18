# main.py
import logging
from src.pipeline.orchestrator import Orchestrator
from src.config import setup_logging, FILES, START_YEAR, END_YEAR

# Configura o logging
setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Iniciando pipeline de dados da NBA...")
    
    bot = Orchestrator()
    
    # # # ETAPA 1: Coletar Drafts Reais (basketbal9 l-reference)
    # bot.run_drafts(start=START_YEAR, end=END_YEAR, output=FILES['draft'])
    
    # # # ETAPA 2: Coletar Estatísticas dos Jogadores (baseado no Passo 1)
    # bot.run_stats(files=FILES)

    # ETAPA 3: Coletar Mock Drafts (nbadraft.net)
    bot.run_mocks(start=START_YEAR, end=END_YEAR, output=FILES['mock'])

    # ETAPA 4: Coletar Dados do Combine (NBA.com API)
    # bot.run_combine(
    #     start=START_YEAR, 
    #     end=END_YEAR, 
    #     file_anthro=FILES['combine_anthro'], 
    #     file_strength=FILES['combine_strength']
    # )
    
    logger.info("Pipeline concluído.")