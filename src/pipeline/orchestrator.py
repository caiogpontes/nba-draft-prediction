# src/pipeline/orchestrator.py
import time
import pandas as pd
import logging
from typing import Dict, List, Set
import os

from src.config import ScraperConfig, BASE_URL_BASKETBALL_REF, BASE_URL_NBADRAFT_NET
from src.infrastructure.network import NetworkClient
from src.infrastructure.storage import DataManager
from src.parsers.draft_parser import DraftParser
from src.parsers.stats_parser import PlayerStatsParser
from src.parsers.mock_parser import MockDraftParser

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.client = NetworkClient(ScraperConfig())

    def _get_mock_draft_url(self, year: int) -> str:
        """Encapsula a lógica de qual URL usar para mocks."""
        if year == 2005:
            return f"{BASE_URL_NBADRAFT_NET}/{year}-nba-draft/"
        elif year < 2009:
            return f"{BASE_URL_NBADRAFT_NET}/mock/{year}-mock-draft/"
        else:
            return f"{BASE_URL_NBADRAFT_NET}/nba-mock-drafts/?year-mock={year}"

    def _get_existing_ids(self, filepath: str, id_column: str) -> Set[str]:
        """Helper: Retorna um conjunto (Set) de IDs que já foram processados."""
        if not os.path.exists(filepath):
            return set()
        
        try:
            df = DataManager.load_csv(filepath)
            if id_column in df.columns:
                # Retorna como set de strings para busca rápida
                return set(df[id_column].astype(str).unique())
        except Exception:
            pass
        return set()

    def run_drafts(self, start: int, end: int, output: str):
        existing_years = self._get_existing_ids(output, 'Year')
        existing_years_int = {int(float(y)) for y in existing_years if y.replace('.', '', 1).isdigit()}
        
        results = []
        
        if os.path.exists(output):
            results.append(DataManager.load_csv(output))

        for year in range(start, end + 1):
            if year in existing_years_int:
                logger.info(f"Draft {year} já coletado. Pulando.")
                continue

            logger.info(f"Baixando Draft {year}...")
            url = f"{BASE_URL_BASKETBALL_REF}/draft/NBA_{year}.html"
            html = self.client.get_html(url)
            if html:
                df_year = DraftParser.parse(html, year)
                if not df_year.empty:
                    results.append(df_year)
            
            time.sleep(self.client.config.delay_between_requests)
        
        if results:
            final_df = pd.concat(results, ignore_index=True)
            final_df.drop_duplicates(subset=['Year', 'Player_ID'], inplace=True)
            DataManager.save_csv(final_df, output)

    def run_stats(self, files: Dict[str, str]):
        draft_df = DataManager.load_csv(files['draft'])
        if draft_df.empty: return

        # Filtro Não-Destrutivo
        if 'College' not in draft_df.columns:
            logger.warning("Coluna 'College' não encontrada no arquivo de draft.")
            has_college_mask = pd.Series([False] * len(draft_df), index=draft_df.index)
        else:
            has_college_mask = draft_df['College'].notna() & (draft_df['College'].astype(str).str.strip() != '')
        
        ignored_count = len(draft_df) - has_college_mask.sum()
        if ignored_count > 0:
            logger.info(f"Ignorados {ignored_count} jogadores sem College.")

        # 1. Identifica quem já foi processado
        processed_nba_ids = self._get_existing_ids(files['nba'], 'Player_ID')
        
        # Listas para armazenar APENAS OS NOVOS DADOS durante o loop
        new_nba_data = []
        new_college_adv = []
        new_college_per_min = []
        
        new_college_links = {}
        
        draft_df['Player_ID'] = draft_df['Player_ID'].astype(str)
        pending_players = draft_df[
            (~draft_df['Player_ID'].isin(processed_nba_ids)) & 
            (has_college_mask)
        ]
        
        total_pending = len(pending_players)
        if total_pending == 0:
            logger.info("Todos os jogadores elegíveis já foram processados.")
            return

        logger.info(f"Iniciando processamento de {total_pending} jogadores pendentes...")
        
        unsaved_count = 0 # Contador para controlar o salvamento parcial
        
        for counter, (idx, row) in enumerate(pending_players.iterrows(), start=1):
            pid = row['Player_ID']
            nba_link = row.get('Player_Link')
            
            logger.info(f"[{counter}/{total_pending}] Processando: {pid}")
            
            if not isinstance(nba_link, str): continue

            nba_html = self.client.get_html(nba_link)
            if nba_html:
                nba_stats = PlayerStatsParser.parse_stats_nba(nba_html, pid)
                if nba_stats:
                    new_nba_data.append(pd.DataFrame(nba_stats))
                
                c_link = row.get('College_Link')
                if pd.isna(c_link):
                    c_link = PlayerStatsParser.extract_college_link(nba_html)
                    if c_link:
                        new_college_links[pid] = c_link

                if c_link and isinstance(c_link, str):
                    c_html = self.client.get_html(c_link)
                    if c_html:
                        c_adv = PlayerStatsParser.parse_stats_college(c_html, 'players_advanced', pid)
                        c_per_min = PlayerStatsParser.parse_stats_college(c_html, 'players_per_poss', pid)
                        
                        if c_adv: new_college_adv.append(pd.DataFrame(c_adv))
                        if c_per_min: new_college_per_min.append(pd.DataFrame(c_per_min))
            
            unsaved_count += 1
            
            # Salva PARCIALMENTE a cada 10 novos jogadores processados
            if unsaved_count >= 10:
                self._append_and_save(new_nba_data, files['nba'])
                self._append_and_save(new_college_adv, files['college_adv'])
                self._append_and_save(new_college_per_min, files['college_per_min'])
                
                # Limpa os buffers temporários para liberar memória e evitar duplicatas
                new_nba_data = []
                new_college_adv = []
                new_college_per_min = []
                unsaved_count = 0
            
            time.sleep(self.client.config.delay_between_requests)

        # Salvamento Final (o que sobrou no buffer)
        self._append_and_save(new_nba_data, files['nba'])
        self._append_and_save(new_college_adv, files['college_adv'])
        self._append_and_save(new_college_per_min, files['college_per_min'])

        if new_college_links:
            self._update_draft_links(draft_df, new_college_links, files['draft'])

    def _append_and_save(self, new_data_list: List[pd.DataFrame], filepath: str):
        """
        Helper OTIMIZADO: Carrega o arquivo existente, adiciona os novos dados,
        remove duplicatas e salva.
        """
        if not new_data_list: return

        try:
            # 1. Carrega dados existentes
            if os.path.exists(filepath):
                existing_df = DataManager.load_csv(filepath)
                all_data = [existing_df] + new_data_list
            else:
                all_data = new_data_list
            
            # 2. Concatena
            final_df = pd.concat(all_data, ignore_index=True)
            
            # 3. Remove duplicatas
            if 'Player_ID' in final_df.columns and 'Season' in final_df.columns:
                 final_df.drop_duplicates(subset=['Player_ID', 'Season'], inplace=True)
            else:
                 final_df.drop_duplicates(inplace=True)
            
            # 4. Salva
            DataManager.save_csv(final_df, filepath)
            
        except Exception as e:
            logger.error(f"Erro ao salvar em {filepath}: {e}")

    def _update_draft_links(self, df: pd.DataFrame, new_links: Dict, filename: str):
        logger.info("Atualizando links de college...")
        mapped = df['Player_ID'].map(new_links)
        if 'College_Link' in df.columns:
            df['College_Link'] = df['College_Link'].fillna(mapped)
        else:
            df['College_Link'] = mapped
        DataManager.save_csv(df, filename)

    def run_mocks(self, start: int, end: int, output: str):
        existing_years = self._get_existing_ids(output, 'Year')
        existing_years_int = {int(float(y)) for y in existing_years if y.replace('.', '', 1).isdigit()}

        results = []
        if os.path.exists(output):
            results.append(DataManager.load_csv(output))

        for year in range(start, end + 1):
            if year in existing_years_int:
                logger.info(f"Mock Draft {year} já coletado. Pulando.")
                continue

            logger.info(f"Baixando Mocks {year}...")
            url = self._get_mock_draft_url(year)
            html = self.client.get_html(url)
            if html:
                df_year = MockDraftParser.parse(html, year)
                if df_year is not None and not df_year.empty:
                    results.append(df_year)
            
            time.sleep(self.client.config.delay_between_requests)
        
        if results:
            final_df = pd.concat(results, ignore_index=True)
            final_df.drop_duplicates(subset=['Year', 'Mock_Pick'], inplace=True)
            DataManager.save_csv(final_df, output)

    def _update_draft_links(self, df: pd.DataFrame, new_links: Dict, filename: str):
        logger.info("Atualizando links de college...")
        mapped = df['Player_ID'].map(new_links)
        if 'College_Link' in df.columns:
            df['College_Link'] = df['College_Link'].fillna(mapped)
        else:
            df['College_Link'] = mapped
        DataManager.save_csv(df, filename)

    def run_mocks(self, start: int, end: int, output: str):
        existing_years = self._get_existing_ids(output, 'Year')
        existing_years_int = {int(float(y)) for y in existing_years if y.replace('.', '', 1).isdigit()}

        results = []
        if os.path.exists(output):
            results.append(DataManager.load_csv(output))

        for year in range(start, end + 1):
            if year in existing_years_int:
                logger.info(f"Mock Draft {year} já coletado. Pulando.")
                continue

            logger.info(f"Baixando Mocks {year}...")
            url = self._get_mock_draft_url(year)
            html = self.client.get_html(url)
            if html:
                df_year = MockDraftParser.parse(html, year)
                if df_year is not None and not df_year.empty:
                    results.append(df_year)
            
            time.sleep(self.client.config.delay_between_requests)
        
        if results:
            final_df = pd.concat(results, ignore_index=True)
            final_df.drop_duplicates(subset=['Year', 'Mock_Pick'], inplace=True)
            DataManager.save_csv(final_df, output)