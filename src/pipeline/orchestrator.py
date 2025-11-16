# src/pipeline/orchestrator.py
import time
import pandas as pd
import logging
from typing import Dict

# Imports do nosso próprio projeto
from src.config import ScraperConfig, BASE_URL_BASKETBALL_REF, BASE_URL_NBADRAFT_NET
from src.infrastructure.network import NetworkClient
from src.infrastructure.storage import DataManager
from src.parsers.draft_parser import DraftParser
from src.parsers.stats_parser import PlayerStatsParser
from src.parsers.mock_parser import MockDraftParser

logger = logging.getLogger(__name__) # Pega o logger configurado

class Orchestrator:
    def __init__(self):
        self.client = NetworkClient(ScraperConfig())

    def _get_mock_draft_url(self, year: int) -> str:
        """Encapsula a lógica de qual URL usar para mocks."""
        if year < 2009:
            return f"{BASE_URL_NBADRAFT_NET}/mock/{year}-mock-draft/"
        else:
            return f"{BASE_URL_NBADRAFT_NET}/nba-mock-drafts/?year-mock={year}"

    def run_drafts(self, start: int, end: int, output: str):
        results = []
        for year in range(start, end + 1):
            logger.info(f"Baixando Draft {year}...")
            url = f"{BASE_URL_BASKETBALL_REF}/draft/NBA_{year}.html"
            html = self.client.get_html(url)
            if html:
                results.append(DraftParser.parse(html, year))
            time.sleep(self.client.config.delay_between_requests)
        
        if results:
            DataManager.save_csv(pd.concat(results, ignore_index=True), output)

    def run_stats(self, files: Dict[str, str]):
        """
        files: Dict contendo caminhos para 'draft', 'nba', 'college_adv', 'college_poss'
        """
        draft_df = DataManager.load_csv(files['draft'])
        if draft_df.empty: return

        # Retirar os jogadores que não vieram via college
        required = ['College']
        draft_df.dropna(subset=required, inplace=True)

        # Buffers em memória
        data_buffers = {
            'nba': [], 
            'c_adv': [], 
            'c_min': []
        }
        new_college_links = {}
        
        total = len(draft_df)
        
        for idx, row in draft_df.iterrows():
            pid = row['Player_ID']
            nba_link = row.get('Player_Link')
            
            logger.info(f"[{idx+1}/{total}] Processando {pid}...")
            
            if not isinstance(nba_link, str): continue

            # 1. NBA Stats & College Discovery
            nba_html = self.client.get_html(nba_link)
            if nba_html:
                data_buffers['nba'].extend(PlayerStatsParser.parse_stats_nba(nba_html, pid))
                
                # Descobre link do college se não existir
                c_link = row.get('College_Link')
                if pd.isna(c_link):
                    c_link = PlayerStatsParser.extract_college_link(nba_html)
                    if c_link:
                        new_college_links[pid] = c_link

                # 2. College Stats (se link existir)
                if c_link and isinstance(c_link, str):
                    c_html = self.client.get_html(c_link)
                    if c_html:
                        data_buffers['c_adv'].extend(PlayerStatsParser.parse_stats_college(c_html, 'players_advanced', pid))
                        data_buffers['c_min'].extend(PlayerStatsParser.parse_stats_college(c_html, 'players_per_min', pid))
            
            time.sleep(self.client.config.delay_between_requests)

        # Persistência dos Dados
        if data_buffers['nba']: DataManager.save_csv(pd.DataFrame(data_buffers['nba']), files['nba'])
        if data_buffers['c_adv']: DataManager.save_csv(pd.DataFrame(data_buffers['c_adv']), files['college_adv'])
        if data_buffers['c_min']: DataManager.save_csv(pd.DataFrame(data_buffers['c_min']), files['college_per_min'])

        # Atualização dos Links no arquivo original
        if new_college_links:
            self._update_draft_links(draft_df, new_college_links, files['draft'])

    def _update_draft_links(self, df: pd.DataFrame, new_links: Dict, filename: str):
        logger.info("Atualizando links de college...")
        # Lógica vetorizada eficiente do Pandas
        mapped = df['Player_ID'].map(new_links)
        if 'College_Link' in df.columns:
            df['College_Link'] = df['College_Link'].fillna(mapped)
        else:
            df['College_Link'] = mapped
        
        DataManager.save_csv(df, filename)

    def run_mocks(self, start: int, end: int, output: str):
        results = []
        for year in range(start, end + 1):
            logger.info(f"Baixando Mocks {year}...")
            # --- LÓGICA REATORADA ---
            url = self._get_mock_draft_url(year)
            # --- FIM ---
            html = self.client.get_html(url)
            if html:
                # Passa o RENAME_MAP correto para o parser
                df_year = MockDraftParser.parse(html, year)
                if df_year is not None and not df_year.empty:
                    results.append(df_year)
            time.sleep(self.client.config.delay_between_requests)
        
        if results:
            DataManager.save_csv(pd.concat(results, ignore_index=True), output)