# src/config.py
import logging
from dataclasses import dataclass

# --- Configuração de Logs ---
def setup_logging():
    logging.basicConfig(
        level=logging.INFO, # Use DEBUG para dev, INFO para prod
        format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        handlers=[logging.StreamHandler()]
    )

# Configuração dos arquivos
FILES = {
    'draft': "data/nba_drafts.csv",
    'nba': "data/nba_player_advanced.csv",
    'college_adv': "data/college_player_advanced.csv",
    'college_per_min': "data/college_player_per_min.csv",
    'mock': "data/mock_drafts.csv",
    # --- NOVOS ARQUIVOS ---
    'combine_anthro': "data/nba_combine_anthro.csv",
    'combine_strength': "data/nba_combine_strength.csv"

}

# AAnos de início e fim para coleta de dados
START_YEAR = 2004
END_YEAR = 2004


# --- Configuração de Rede ---
BASE_URL_BASKETBALL_REF = "https://www.basketball-reference.com"
BASE_URL_NBADRAFT_NET = "https://www.nbadraft.net" 
# URLs da API Oficial (Stats NBA)
API_URL_COMBINE_ANTHRO = "https://stats.nba.com/stats/draftcombineplayeranthro"
API_URL_COMBINE_STRENGTH = "https://stats.nba.com/stats/draftcombinestats"

# Headers Padrão (Para sites normais: Basketball-Ref, NBADraft.net)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
}

# Headers Específicos (Apenas para API da NBA)
NBA_API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true'
}

@dataclass
class ScraperConfig:
    max_retries: int = 3
    timeout: int = 60
    delay_between_requests: int = 2

# --- Mapeamento de Renomeação ---
COLLEGE_RENAMES = {
    'players_advanced': {
        'Team': 'Tm',       'WS/40': 'WS_per_40', 'TS%': 'TS_pct',
        'ORB%': 'ORB_pct',  'DRB%': 'DRB_pct',    'TRB%': 'TRB_pct',
        'AST%': 'AST_pct',  'STL%': 'STL_pct',    'BLK%': 'BLK_pct',
        'TOV%': 'TOV_pct',  'USG%': 'USG_pct'
    },
    'players_per_min': {
        'Team': 'Tm',       'FG%': 'FG_pct',      '3P%': '3P_pct',
        '2P%': '2P_pct',    'eFG%': 'eFG_pct',    'FT%': 'FT_pct'
    }
}

NBA_RENAMES = {
    'advanced': {
        'WS/48': 'WS_per_48', 'TS%': 'TS_pct',  'FG%': 'FG_pct', 
        '3P%': '3P_pct',      'FT%': 'FT_pct',  'ORB%': 'ORB_pct',  
        'DRB%': 'DRB_pct',    'TRB%': 'TRB_pct','AST%': 'AST_pct',  
        'STL%': 'STL_pct',    'BLK%': 'BLK_pct','TOV%': 'TOV_pct',  
        'USG%': 'USG_pct'
    }
}

DRAFT_RENAMES = {
    'stats': {
        'WS/48': 'WS_per_48', 'FG%': 'FG_pct', '3P%': '3P_pct',      
        'FT%': 'FT_pct',      'MP.1': 'MPG', 'PTS.1': 'PPG',
        'TRB.1': 'RPG', 'AST.1': 'APG'
    }
}

MOCK_DRAFT_RENAMES = {
    '#': 'Mock_Pick', 'Pk': 'Mock_Pick', 'Player': 'Player', 'Team': 'Team',
    'School/Club': 'College', 'School': 'College', 'Pos': 'Pos', 'P': 'Pos',
    'Ht': 'Height', 'H': 'Height', 'Wt': 'Weight', 'W': 'Weight',
    'Class': 'Class', 'C': 'Class'
}