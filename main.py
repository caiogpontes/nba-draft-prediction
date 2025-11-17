# main.py
import logging
from src.pipeline.orchestrator import Orchestrator
from src.config import setup_logging

# Configura o logging
setup_logging()
logger = logging.getLogger(__name__)

# Configuração dos arquivos
FILES = {
    'draft': "data/nba_drafts.csv",
    'nba': "data/nba_player_advanced.csv",
    'college_adv': "data/college_player_advanced.csv",
    'college_per_min': "data/college_player_per_min.csv",
    'mock': "data/mock_drafts.csv"
}

START_YEAR = 2000
END_YEAR = 2001

if __name__ == "__main__":
    logger.info("Iniciando pipeline de dados da NBA...")
    
    bot = Orchestrator()
    
    # # ETAPA 1: Coletar Drafts Reais (basketbal9 l-reference)
    # bot.run_drafts(start=START_YEAR, end=END_YEAR, output=FILES['draft'])
    
    # # ETAPA 2: Coletar Estatísticas dos Jogadores (baseado no Passo 1)
    # bot.run_stats(files=FILES)

    # ETAPA 3: Coletar Mock Drafts (nbadraft.net)
    bot.run_mocks(start=START_YEAR, end=END_YEAR, output=FILES['mock'])
    
    logger.info("Pipeline concluído.")