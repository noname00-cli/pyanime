#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyanime_ui.py - PyQt6 GUI for pyanime

import sys
import asyncio
import qasync
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QLabel, QLineEdit, QPushButton, QTableWidget, 
                           QTableWidgetItem, QTextEdit, QProgressBar, QComboBox,
                           QMessageBox, QSplitter, QTabWidget, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDateTime

from providers.Hianime.Scraper.searchAnimedetails import searchAnimeandetails, getAnimeDetails
from providers.Hianime.Scraper.searchEpisodedetails import getanimepisode
from providers.Hianime.Scraper.getEpisodestreams import serverextractor, streams
from providers.Hianime.Downloader.downloader import m3u8_parsing, downloading, set_progress_emitter, ProgressEmitter
from config.hianime import subtitle


class SearchWorker(QThread):
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, search_query):
        super().__init__()
        self.search_query = search_query

    def run(self):
        try:
            results = searchAnimeandetails(self.search_query)
            self.results_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


class EpisodeWorker(QThread):
    episodes_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, watch_link):
        super().__init__()
        self.watch_link = watch_link

    def run(self):
        try:
            episodes = getanimepisode(self.watch_link)
            self.episodes_ready.emit(episodes)
        except Exception as e:
            self.error_occurred.emit(str(e))


class DownloadWorker(QThread):
    episode_started = pyqtSignal(str, int, int)
    episode_completed = pyqtSignal(str, bool)
    download_finished = pyqtSignal(bool, str, int, int)

    def __init__(self, episodes, anime_title, needs):
        super().__init__()
        self.episodes = episodes
        self.anime_title = anime_title
        self.needs = needs

    async def download_episode_async(self, episode, anime_title, needs):
        try:
            servers = serverextractor(episode)

            if isinstance(servers, tuple) and len(servers) == 2:
                hianime_servers, animepahe_servers = servers
                if hianime_servers and 'sub' in hianime_servers:
                    selected_servers = hianime_servers['sub'] if needs == 'sub' else hianime_servers.get('dub', hianime_servers['sub'])
                elif hianime_servers and 'dub' in hianime_servers:
                    selected_servers = hianime_servers['dub'] if needs == 'dub' else hianime_servers.get('sub', hianime_servers['dub'])
                else:
                    return 1
            else:
                selected_servers = [s for s in servers if s.get('data_type') == needs]
                if not selected_servers:
                    return 1

            if not selected_servers:
                return 1

            server = selected_servers[0] if isinstance(selected_servers, list) else selected_servers

            media = streams(server, episode)
            segments, name, subs = m3u8_parsing(media)

            if not segments:
                return 1

            base_url = None
            if isinstance(media, dict) and 'link' in media and 'file' in media['link'] and media['link']['file'].startswith('http'):
                base_url = '/'.join(media['link']['file'].split('/')[:-1]) + '/'

            code = await downloading(segments, f"{episode['No']}. {name}", anime_title, subs, base_url)

            return code

        except Exception as e:
            print(f"Error downloading episode {episode['No']}: {e}")
            return 1

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            success_count = 0
            failed_count = 0
            total = len(self.episodes)

            for i, episode in enumerate(self.episodes):
                episode_name = f"Episode {episode['No']}: {episode.get('Title', 'Unknown')}"
                self.episode_started.emit(episode_name, i + 1, total)

                try:
                    result = loop.run_until_complete(
                        self.download_episode_async(episode, self.anime_title, self.needs)
                    )

                    if result == 0:
                        success_count += 1
                        self.episode_completed.emit(episode_name, True)
                    else:
                        failed_count += 1
                        self.episode_completed.emit(episode_name, False)

                except Exception as e:
                    failed_count += 1
                    self.episode_completed.emit(episode_name, False)

            loop.close()

            self.download_finished.emit(
                success_count > 0,
                f"Download completed: {success_count} successful, {failed_count} failed",
                success_count,
                failed_count
            )

        except Exception as e:
            self.download_finished.emit(False, f"Download failed: {str(e)}", 0, len(self.episodes))


class DownloadProgressWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.episode_label = QLabel("Ready to download")
        self.episode_label.setObjectName("episodeProgress")
        layout.addWidget(self.episode_label)

        self.episode_progress = QProgressBar()
        self.episode_progress.setVisible(False)
        layout.addWidget(self.episode_progress)

        self.step_label = QLabel("")
        self.step_label.setObjectName("stepProgress")
        layout.addWidget(self.step_label)

        self.step_progress = QProgressBar()
        self.step_progress.setVisible(False)
        layout.addWidget(self.step_progress)

        self.segment_label = QLabel("")
        self.segment_label.setObjectName("segmentProgress")
        layout.addWidget(self.segment_label)

        self.segment_progress = QProgressBar()
        self.segment_progress.setVisible(False)
        layout.addWidget(self.segment_progress)

        self.stats_label = QLabel("")
        self.stats_label.setObjectName("statsLabel")
        layout.addWidget(self.stats_label)

        self.setLayout(layout)

    def start_episode_download(self, episode_name, current, total):
        self.episode_label.setText(f"Downloading {episode_name}")
        self.episode_progress.setVisible(True)
        self.episode_progress.setRange(0, total)
        self.episode_progress.setValue(current)

        self.step_progress.setVisible(True)
        self.segment_progress.setVisible(True)
        self.step_label.setVisible(True)
        self.segment_label.setVisible(True)
        self.stats_label.setVisible(True)

    def complete_episode_download(self, episode_name, success):
        status = "✅ Completed" if success else "❌ Failed"
        self.episode_label.setText(f"{status}: {episode_name}")

        current_value = self.episode_progress.value()
        self.episode_progress.setValue(current_value + 1)

    def update_step_progress(self, current_step, total_steps, message):
        self.step_label.setText(f"Step {current_step}/{total_steps}: {message}")
        self.step_progress.setRange(0, total_steps)
        self.step_progress.setValue(current_step)

    def update_segment_progress(self, completed, total, retries):
        if total > 0:
            percentage = int((completed / total) * 100)
            self.segment_label.setText(f"Segments: {completed}/{total} ({percentage}%)")
            self.segment_progress.setRange(0, total)
            self.segment_progress.setValue(completed)
            self.stats_label.setText(f"Retries: {retries}")

    def reset_progress(self):
        self.episode_label.setText("Ready to download")
        self.episode_progress.setVisible(False)
        self.step_progress.setVisible(False)
        self.segment_progress.setVisible(False)
        self.step_label.setVisible(False)
        self.segment_label.setVisible(False)
        self.stats_label.setVisible(False)

    def finish_download(self):
        self.step_label.setText("Download completed!")
        self.segment_label.setText("")
        self.stats_label.setText("")


class AnimeDetailsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.title_label = QLabel("Anime Details")
        self.title_label.setObjectName("sectionTitle")
        layout.addWidget(self.title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)

        scroll.setWidget(self.details_widget)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def update_details(self, anime_details):
        for i in reversed(range(self.details_layout.count())):
            child = self.details_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        def get_value(keys, default="N/A"):
            d = anime_details
            for key in keys:
                if isinstance(d, dict) and key in d and d[key]:
                    d = d[key]
                else:
                    return default
            return d if d else default

        details_map = {
            'Title': get_value(['title']),
            'Japanese Name': get_value(['details', 'Synonyms']) if get_value(['details', 'Synonyms']) != "N/A" else get_value(['title']),
            'In Japanese': get_value(['details', 'Japanese']),
            'Duration': get_value(['details', 'Duration']),
            'Age Rating': get_value(['age']),
            'Quality': get_value(['quality']),
            'Air Date': get_value(['details', 'Aired']),
            'Status': get_value(['details', 'Status']),
            'Genres': get_value(['details', 'Genres']),
            'Producers': get_value(['details', 'Producers']) if get_value(['details', 'Producers']) != "N/A" else "Not Available",
            'Studio': get_value(['details', 'Studios']),
        }

        for key, value in details_map.items():
            label = QLabel(f"{key}: {value}")
            label.setObjectName("detailItem")
            label.setWordWrap(True)

            if key == "Status":
                if value == "Finished Airing":
                    label.setStyleSheet("color: #00fb8a;")
                elif value == "Currently Airing":
                    label.setStyleSheet("color: #ffb84d;")
                else:
                    label.setStyleSheet("color: #ff0000;")
            elif key == "Producers" and value == "Not Available":
                label.setStyleSheet("color: #ff0000;")

            self.details_layout.addWidget(label)

        synopsis = get_value(['details', 'Overview'], 'No synopsis available')
        synopsis_label = QLabel(f"Synopsis: {synopsis}")
        synopsis_label.setObjectName("synopsis")
        synopsis_label.setWordWrap(True)
        self.details_layout.addWidget(synopsis_label)


class PyAnimeGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.search_results = []
        self.selected_anime = None
        self.episodes = []
        self.selected_episodes = []

        self.setup_ui()
        self.load_stylesheet()

    def setup_ui(self):
        self.setWindowTitle("PyAnime GUI v1.0.0")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        header_label = QLabel("PyAnime - Anime Downloader")
        header_label.setObjectName("header")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        search_group = QGroupBox("Search Anime")
        search_layout = QHBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter anime name...")
        self.search_input.returnPressed.connect(self.search_anime)

        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("primaryButton")
        self.search_button.clicked.connect(self.search_anime)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        main_layout.addWidget(search_group)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QTabWidget()

        self.search_table = QTableWidget()
        self.search_table.itemSelectionChanged.connect(self.on_anime_selected)
        left_panel.addTab(self.search_table, "Search Results")

        episodes_widget = QWidget()
        episodes_layout = QVBoxLayout(episodes_widget)

        episode_select_layout = QHBoxLayout()
        self.episode_input = QLineEdit()
        self.episode_input.setPlaceholderText("1 / 1,2 / 1-10")
        episode_select_button = QPushButton("Select Episodes")
        episode_select_button.clicked.connect(self.select_episodes)

        episode_select_layout.addWidget(QLabel("Episodes:"))
        episode_select_layout.addWidget(self.episode_input)
        episode_select_layout.addWidget(episode_select_button)
        episodes_layout.addLayout(episode_select_layout)

        self.episodes_table = QTableWidget()
        episodes_layout.addWidget(self.episodes_table)

        left_panel.addTab(episodes_widget, "Episodes")

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.anime_details = AnimeDetailsWidget()
        right_layout.addWidget(self.anime_details)

        download_group = QGroupBox("Download Options")
        download_layout = QVBoxLayout(download_group)

        sub_dub_layout = QHBoxLayout()
        sub_dub_layout.addWidget(QLabel("Audio:"))
        self.audio_combo = QComboBox()
        self.audio_combo.addItems(["sub", "dub"])
        if subtitle:
            self.audio_combo.setCurrentText(subtitle)
        sub_dub_layout.addWidget(self.audio_combo)
        sub_dub_layout.addStretch()
        download_layout.addLayout(sub_dub_layout)

        self.download_button = QPushButton("Download Selected Episodes")
        self.download_button.setObjectName("downloadButton")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        download_layout.addWidget(self.download_button)

        self.progress_widget = DownloadProgressWidget()
        download_layout.addWidget(self.progress_widget)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setObjectName("logText")
        download_layout.addWidget(self.log_text)

        right_layout.addWidget(download_group)
        splitter.addWidget(right_panel)

        splitter.setSizes([700, 700])
        main_layout.addWidget(splitter)

        self.statusBar().showMessage("Ready")

    def load_stylesheet(self):
        try:
            script_dir = Path(__file__).parent
            parent_dir = script_dir.parent
            css_path = parent_dir / 'config' / 'styles.css'

            if css_path.exists():
                with open(css_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
                self.log(f"Loaded stylesheet from: {css_path}")
            else:
                self.log(f"Warning: styles.css not found at {css_path}")

        except Exception as e:
            self.log(f"Error loading stylesheet: {e}")

    def log(self, message):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def search_anime(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter an anime name")
            return

        self.search_button.setEnabled(False)
        self.search_button.setText("Searching...")
        self.statusBar().showMessage("Searching for anime...")

        self.search_worker = SearchWorker(query)
        self.search_worker.results_ready.connect(self.on_search_results)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_results(self, results):
        self.search_results = results
        self.populate_search_table(results)

        self.search_button.setEnabled(True)
        self.search_button.setText("Search")
        self.statusBar().showMessage(f"Found {len(results)} results")
        self.log(f"Search completed: {len(results)} results found")

    def on_search_error(self, error):
        QMessageBox.critical(self, "Search Error", f"Failed to search: {error}")
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")
        self.statusBar().showMessage("Search failed")
        self.log(f"Search error: {error}")

    def populate_search_table(self, results):
        if not results:
            return

        headers = ["No", "Title", "Type", "Episodes", "Duration", "Subs", "Dubs"]
        self.search_table.setColumnCount(len(headers))
        self.search_table.setHorizontalHeaderLabels(headers)
        self.search_table.setRowCount(len(results))

        for row, anime in enumerate(results):
            self.search_table.setItem(row, 0, QTableWidgetItem(str(anime.get('No', ''))))
            self.search_table.setItem(row, 1, QTableWidgetItem(anime.get('Title', '')))
            self.search_table.setItem(row, 2, QTableWidgetItem(anime.get('Type', '')))
            self.search_table.setItem(row, 3, QTableWidgetItem(anime.get('Episodes', '')))
            self.search_table.setItem(row, 4, QTableWidgetItem(anime.get('Duration', '')))
            self.search_table.setItem(row, 5, QTableWidgetItem(anime.get('Subs', '')))
            self.search_table.setItem(row, 6, QTableWidgetItem(anime.get('Dubs', '')))

        self.search_table.resizeColumnsToContents()

    def on_anime_selected(self):
        current_row = self.search_table.currentRow()
        if current_row >= 0 and current_row < len(self.search_results):
            self.selected_anime = self.search_results[current_row]
            watch_link = self.selected_anime['Imp']['Watch Link']

            try:
                anime_details = getAnimeDetails(watch_link)
                self.anime_details.update_details(anime_details)
                self.log(f"Selected: {anime_details.get('title', 'Unknown')}")
            except Exception as e:
                self.log(f"Error getting anime details: {e}")

            self.statusBar().showMessage("Loading episodes...")
            self.episode_worker = EpisodeWorker(watch_link)
            self.episode_worker.episodes_ready.connect(self.on_episodes_loaded)
            self.episode_worker.error_occurred.connect(self.on_episodes_error)
            self.episode_worker.start()

    def on_episodes_loaded(self, episodes):
        self.episodes = episodes
        self.populate_episodes_table(episodes)
        self.statusBar().showMessage(f"Loaded {len(episodes)} episodes")
        self.log(f"Loaded {len(episodes)} episodes")

    def on_episodes_error(self, error):
        QMessageBox.critical(self, "Episodes Error", f"Failed to load episodes: {error}")
        self.log(f"Episodes error: {error}")

    def populate_episodes_table(self, episodes):
        if not episodes:
            return

        headers = ["No", "Title", "Episode Name", "Japanese Name"]
        self.episodes_table.setColumnCount(len(headers))
        self.episodes_table.setHorizontalHeaderLabels(headers)
        self.episodes_table.setRowCount(len(episodes))

        for row, episode in enumerate(episodes):
            self.episodes_table.setItem(row, 0, QTableWidgetItem(str(episode.get('No', ''))))
            self.episodes_table.setItem(row, 1, QTableWidgetItem(episode.get('Title', '')))
            self.episodes_table.setItem(row, 2, QTableWidgetItem(episode.get('Episode Name', '')))
            self.episodes_table.setItem(row, 3, QTableWidgetItem(episode.get('Japanese Name', '')))

        self.episodes_table.resizeColumnsToContents()

    def select_episodes(self):
        selection = self.episode_input.text().strip()
        if not selection or not self.episodes:
            QMessageBox.warning(self, "Warning", "Please enter episode selection")
            return

        try:
            selected_episodes = []
            if '-' in selection:
                start, end = map(int, selection.split('-'))
                selected_episodes = [ep for ep in self.episodes if start <= int(ep["No"]) <= end]
            elif ',' in selection:
                selected_episodes = [ep for ep in self.episodes if int(ep["No"]) in map(int, selection.split(','))]
            else:
                selected_episodes = [ep for ep in self.episodes if int(ep["No"]) == int(selection)]

            self.selected_episodes = selected_episodes
            self.download_button.setEnabled(len(selected_episodes) > 0)
            self.log(f"Selected {len(selected_episodes)} episodes for download")

        except Exception as e:
            QMessageBox.warning(self, "Selection Error", f"Invalid selection format: {e}")

    def start_download(self):
        if not self.selected_episodes:
            QMessageBox.warning(self, "Warning", "No episodes selected")
            return

        anime_title = self.selected_anime.get('Title', 'Unknown')
        audio_type = self.audio_combo.currentText()

        self.download_button.setEnabled(False)
        self.progress_widget.reset_progress()

        self.download_worker = DownloadWorker(self.selected_episodes, anime_title, audio_type)
        self.download_worker.episode_started.connect(self.progress_widget.start_episode_download)
        self.download_worker.episode_completed.connect(self.progress_widget.complete_episode_download)
        self.download_worker.download_finished.connect(self.on_download_finished)
        self.download_worker.start()

        self.log(f"Starting download of {len(self.selected_episodes)} episodes...")

    def on_download_finished(self, success, message, success_count, failed_count):
        self.download_button.setEnabled(True)
        self.progress_widget.finish_download()
        self.statusBar().showMessage("Download completed")
        self.log(f"Download finished: {message}")

        if success_count > 0:
            QMessageBox.information(
                self,
                "Download Complete",
                f"Download Summary:\n✅ Successful: {success_count}\n❌ Failed: {failed_count}"
            )
        else:
            QMessageBox.critical(self, "Download Failed", message)


def main():
    app = QApplication(sys.argv)

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = PyAnimeGUI()

    # Setup progress emitter from downloader
    progress_emitter = ProgressEmitter()
    set_progress_emitter(progress_emitter)

    # Connect signals to progress widget
    progress_emitter.segment_progress.connect(window.progress_widget.update_segment_progress)
    progress_emitter.step_progress.connect(window.progress_widget.update_step_progress)

    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
