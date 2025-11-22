# src/pipeline/orchestrator.py - VERSÃO FINAL LIMPA
import time
import pandas as pd
import logging
from typing import Dict, List, Set
import os
from nba_api.stats.endpoints import draftcombineplayeranthro, draftcombinestats

from src.config import (
    ScraperConfig, BASE_URL_BASKETBALL_REF, BASE_URL_NBADRAFT_NET,
    HEADERS # Usamos o HEADERS padrão agora
)
from src.infrastructure.network import NetworkClient
from src.infrastructure.storage import DataManager
from src.parsers.draft_parser import DraftParser
from src.parsers.stats_parser import PlayerStatsParser
from src.parsers.mock_parser import MockDraftParser


logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.client = NetworkClient(ScraperConfig())

    # ... (Métodos auxiliares _get_mock_draft_url, _get_existing_ids, _update_draft_links mantidos) ...

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

    def _append_and_save(self, new_data_list: List[pd.DataFrame], filepath: str):
        """
        Helper OTIMIZADO: Carrega, Concatena, Salva. (Centraliza a lógica de I/O)
        """
        if not new_data_list: return

        try:
            # 1. Carrega histórico (se existir)
            if os.path.exists(filepath):
                existing_df = DataManager.load_csv(filepath)
                all_data = [existing_df] + new_data_list
            else:
                all_data = new_data_list
            
            # 2. Concatena
            final_df = pd.concat(all_data, ignore_index=True)
            
            # 3. Remove duplicatas (Segurança)
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
        
    def run_drafts(self, start: int, end: int, output: str):
        # ... (Mantido)
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
            # Não precisa passar headers customizados, usa o padrão HEADERS
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
        # ... (Mantido)
        draft_df = DataManager.load_csv(files['draft'])
        if draft_df.empty: return

        # Filtro Não-Destrutivo
        if 'College' not in draft_df.columns:
            has_college_mask = pd.Series([False] * len(draft_df), index=draft_df.index)
        else:
            has_college_mask = draft_df['College'].notna() & (draft_df['College'].astype(str).str.strip() != '')
        
        ignored_count = len(draft_df) - has_college_mask.sum()
        if ignored_count > 0:
            logger.info(f"Ignorados {ignored_count} jogadores sem College.")

        # 1. Identifica processados
        processed_nba_ids = self._get_existing_ids(files['nba'], 'Player_ID')
        
        # OTIMIZAÇÃO: Listas vazias (não carregamos o histórico para a RAM)
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
        
        unsaved_count = 0 
        
        for counter, (idx, row) in enumerate(pending_players.iterrows(), start=1):
            pid = row['Player_ID']
            nba_link = row.get('Player_Link')
            
            logger.info(f"[{counter}/{total_pending}] Processando: {pid}")
            
            if not isinstance(nba_link, str): continue

            # Não precisa de headers customizados aqui, usa o padrão.
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
                        c_per_min = PlayerStatsParser.parse_stats_college(c_html, 'players_per_min', pid)
                        
                        if c_adv: new_college_adv.append(pd.DataFrame(c_adv))
                        if c_per_min: new_college_per_min.append(pd.DataFrame(c_per_min))
            
            unsaved_count += 1
            
            # OTIMIZAÇÃO: Salva e LIMPA a memória
            if unsaved_count >= 10:
                self._append_and_save(new_nba_data, files['nba'])
                self._append_and_save(new_college_adv, files['college_adv'])
                self._append_and_save(new_college_per_min, files['college_per_min'])
                
                # Esvazia as listas para liberar memória
                new_nba_data = []
                new_college_adv = []
                new_college_per_min = []
                unsaved_count = 0
            
            time.sleep(self.client.config.delay_between_requests)

        # Salvamento Final (o que sobrou)
        self._append_and_save(new_nba_data, files['nba'])
        self._append_and_save(new_college_adv, files['college_adv'])
        self._append_and_save(new_college_per_min, files['college_per_min'])

        if new_college_links:
            self._update_draft_links(draft_df, new_college_links, files['draft'])

    def run_mocks(self, start: int, end: int, output: str):
        # ... (Mantido)
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
            
    # --- NOVO MÉTODO AUXILIAR (Formatador de Ano) ---
    def _format_season_year(self, year: int) -> str:
        """Converte 2000 -> '2000-01' para a API da NBA."""
        next_year = (year + 1) % 100
        return f"{year}-{next_year:02d}"

    def run_combine(self, start: int, end: int, file_anthro: str, file_strength: str):
        """Coleta dados do NBA Combine usando a biblioteca nba_api."""
        
        # Listas para armazenar todos os resultados, incluindo o histórico
        anthro_results = []
        strength_results = []
        
        # Carrega históricos se existirem (para o Delta Load)
        if os.path.exists(file_anthro): anthro_results.append(DataManager.load_csv(file_anthro))
        if os.path.exists(file_strength): strength_results.append(DataManager.load_csv(file_strength))

        # Verifica anos já processados (baseado no arquivo de Anthro como referência)
        existing_years = set()
        if anthro_results and 'Season_Year' in anthro_results[0].columns:
            # Concatena temporariamente só para checar os anos existentes
            existing_df = pd.concat(anthro_results)
            existing_years = set(existing_df['Season_Year'].astype(int).unique())

        for year in range(start, end + 1):
            if year in existing_years:
                logger.info(f"Combine {year} já coletado. Pulando.")
                continue

            season_param = self._format_season_year(year)
            logger.info(f"Baixando NBA Combine {season_param} via NBA-API...")

            try:
                # 1. Coleta Antropometria
                anthro_data = draftcombineplayeranthro.DraftCombinePlayerAnthro(season_year=season_param)
                df_anthro = anthro_data.get_data_frames()[0]
                df_anthro['Season_Year'] = year
                anthro_results.append(df_anthro)

                # 2. Coleta Força/Agilidade
                strength_data = draftcombinestats.DraftCombineStats(season_all_time=season_param)
                df_strength = strength_data.get_data_frames()[0]
                df_strength['Season_Year'] = year
                strength_results.append(df_strength)

            except Exception as e:
                logger.error(f"Falha ao coletar dados do Combine {season_param} via NBA-API: {e}")
            
            time.sleep(self.client.config.delay_between_requests)

        # Salvamento Final
        self._save_combine_final(anthro_results, file_anthro)
        self._save_combine_final(strength_results, file_strength)

    def _save_combine_final(self, data_list: List[pd.DataFrame], filepath: str):
        if not data_list: return
        final_df = pd.concat(data_list, ignore_index=True)
        
        # Assume que PLAYER_ID é a chave
        subset_cols = ['PLAYER_ID', 'Season_Year'] if 'PLAYER_ID' in final_df.columns else None
        
        final_df.drop_duplicates(subset=subset_cols, inplace=True)
        DataManager.save_csv(final_df, filepath)