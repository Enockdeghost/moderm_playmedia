import sys
import os
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *

class PlaylistModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.playlist = []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.playlist)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.playlist):
            return None
        
        if role == Qt.DisplayRole:
            return os.path.basename(self.playlist[index.row()])
        elif role == Qt.UserRole:
            return self.playlist[index.row()]
        return None
    
    def addMedia(self, filepath):
        self.beginInsertRows(QModelIndex(), len(self.playlist), len(self.playlist))
        self.playlist.append(filepath)
        self.endInsertRows()
    
    def removeMedia(self, index):
        if 0 <= index < len(self.playlist):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.playlist[index]
            self.endRemoveRows()
    
    def clear(self):
        self.beginResetModel()
        self.playlist.clear()
        self.endResetModel()

class MediaPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Media Player")
        self.setWindowIcon(QIcon())
        self.resize(1200, 800)
        
        # Initialize media player
        self.media_player = QMediaPlayer()
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        
        # Playlist
        self.playlist_model = PlaylistModel()
        self.current_index = -1
        
        # Settings
        self.settings = QSettings('MediaPlayer', 'Settings')
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        self.setup_connections()
        self.setup_shortcuts()
        
        # Load settings
        self.load_settings()
        
        # Apply dark theme
        self.apply_dark_theme()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left panel (playlist)
        self.left_panel = QWidget()
        self.left_panel.setMaximumWidth(300)
        self.left_panel.setMinimumWidth(200)
        left_layout = QVBoxLayout(self.left_panel)
        
        # Playlist header
        playlist_header = QLabel("Playlist")
        playlist_header.setStyleSheet("font-weight: bold; padding: 10px;")
        left_layout.addWidget(playlist_header)
        
        # Playlist view
        self.playlist_view = QListView()
        self.playlist_view.setModel(self.playlist_model)
        self.playlist_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_view.customContextMenuRequested.connect(self.show_playlist_context_menu)
        left_layout.addWidget(self.playlist_view)
        
        # Playlist buttons
        playlist_buttons = QHBoxLayout()
        self.add_file_btn = QPushButton("Add File")
        self.add_folder_btn = QPushButton("Add Folder")
        self.clear_playlist_btn = QPushButton("Clear")
        
        playlist_buttons.addWidget(self.add_file_btn)
        playlist_buttons.addWidget(self.add_folder_btn)
        playlist_buttons.addWidget(self.clear_playlist_btn)
        left_layout.addLayout(playlist_buttons)
        
        # Right panel (video and controls)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Video widget
        self.video_widget.setStyleSheet("background-color: black;")
        right_layout.addWidget(self.video_widget, 1)
        
        # Controls panel
        controls_panel = self.create_controls_panel()
        right_layout.addWidget(controls_panel)
        
        # Add panels to main layout
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(right_panel, 1)
        
        # Splitter for resizing
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 950])
        
        main_layout.addWidget(splitter)
    
    def create_controls_panel(self):
        controls_widget = QWidget()
        controls_widget.setFixedHeight(120)
        layout = QVBoxLayout(controls_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Progress bar and time labels
        progress_layout = QHBoxLayout()
        
        self.current_time_label = QLabel("00:00")
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.total_time_label = QLabel("00:00")
        
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.position_slider)
        progress_layout.addWidget(self.total_time_label)
        
        layout.addLayout(progress_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        # Media control buttons
        self.previous_btn = QPushButton("⏮")
        self.play_pause_btn = QPushButton("▶")
        self.stop_btn = QPushButton("⏹")
        self.next_btn = QPushButton("⏭")
        
        # Set button sizes
        for btn in [self.previous_btn, self.play_pause_btn, self.stop_btn, self.next_btn]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.play_pause_btn.setFixedSize(50, 50)
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.previous_btn)
        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addStretch()
        
        # Volume control
        volume_layout = QHBoxLayout()
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(30, 30)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(100)
        
        volume_layout.addWidget(self.mute_btn)
        volume_layout.addWidget(self.volume_slider)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.setMaximumWidth(80)
        speed_layout.addWidget(self.speed_combo)
        
        # Right side controls
        right_controls = QHBoxLayout()
        right_controls.addLayout(volume_layout)
        right_controls.addLayout(speed_layout)
        
        # Add to main controls layout
        controls_layout.addLayout(right_controls)
        
        layout.addLayout(controls_layout)
        
        return controls_widget
    
    def setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        open_file_action = QAction('Open File', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)
        
        open_folder_action = QAction('Open Folder', self)
        open_folder_action.setShortcut('Ctrl+Shift+O')
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        fullscreen_action = QAction('Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        toggle_playlist_action = QAction('Toggle Playlist', self)
        toggle_playlist_action.setShortcut('Ctrl+L')
        toggle_playlist_action.triggered.connect(self.toggle_playlist)
        view_menu.addAction(toggle_playlist_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        # Media player connections
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.mediaStatusChanged.connect(self.media_status_changed)
        
        # Control connections
        self.play_pause_btn.clicked.connect(self.play_pause)
        self.stop_btn.clicked.connect(self.stop)
        self.previous_btn.clicked.connect(self.previous_media)
        self.next_btn.clicked.connect(self.next_media)
        
        self.position_slider.sliderMoved.connect(self.set_position)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.mute_btn.clicked.connect(self.toggle_mute)
        self.speed_combo.currentTextChanged.connect(self.change_speed)
        
        # Playlist connections
        self.playlist_view.doubleClicked.connect(self.play_selected)
        self.add_file_btn.clicked.connect(self.open_file)
        self.add_folder_btn.clicked.connect(self.open_folder)
        self.clear_playlist_btn.clicked.connect(self.clear_playlist)
    
    def setup_shortcuts(self):
        # Keyboard shortcuts
        QShortcut(QKeySequence(Qt.Key_Space), self, self.play_pause)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.seek_forward)
        QShortcut(QKeySequence(Qt.Key_Left), self, self.seek_backward)
        QShortcut(QKeySequence(Qt.Key_Up), self, self.volume_up)
        QShortcut(QKeySequence(Qt.Key_Down), self, self.volume_down)
        QShortcut(QKeySequence(Qt.Key_M), self, self.toggle_mute)
    
    def apply_dark_theme(self):
        dark_style = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #606060;
        }
        QSlider::groove:horizontal {
            border: 1px solid #999999;
            height: 8px;
            background: #404040;
            margin: 2px 0;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #ffffff;
            border: 1px solid #5c5c5c;
            width: 18px;
            margin: -2px 0;
            border-radius: 9px;
        }
        QListView {
            background-color: #353535;
            border: 1px solid #555555;
            selection-background-color: #4a90e2;
        }
        QMenuBar {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QMenuBar::item:selected {
            background-color: #404040;
        }
        QMenu {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555555;
        }
        QMenu::item:selected {
            background-color: #404040;
        }
        """
        self.setStyleSheet(dark_style)
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Media File", "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.mp3 *.wav *.flac *.aac);;All Files (*)"
        )
        if file_path:
            self.playlist_model.addMedia(file_path)
    
    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            supported_formats = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', 
                               '.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg']
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(fmt) for fmt in supported_formats):
                        self.playlist_model.addMedia(os.path.join(root, file))
    
    def play_selected(self, index):
        self.current_index = index.row()
        file_path = self.playlist_model.data(index, Qt.UserRole)
        if file_path:
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.media_player.play()
    
    def play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            if self.media_player.mediaStatus() == QMediaPlayer.NoMedia:
                if self.playlist_model.rowCount() > 0:
                    self.current_index = 0
                    self.play_selected(self.playlist_model.index(0))
                    return
            self.media_player.play()
    
    def stop(self):
        self.media_player.stop()
    
    def previous_media(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.play_selected(self.playlist_model.index(self.current_index))
    
    def next_media(self):
        if self.current_index < self.playlist_model.rowCount() - 1:
            self.current_index += 1
            self.play_selected(self.playlist_model.index(self.current_index))
    
    def media_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setText("⏸")
        else:
            self.play_pause_btn.setText("▶")
    
    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.current_time_label.setText(self.format_time(position))
    
    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.total_time_label.setText(self.format_time(duration))
    
    def set_position(self, position):
        self.media_player.setPosition(position)
    
    def set_volume(self, volume):
        self.media_player.setVolume(volume)
        if volume == 0:
            self.mute_btn.setText("🔇")
        else:
            self.mute_btn.setText("🔊")
    
    def toggle_mute(self):
        if self.media_player.isMuted():
            self.media_player.setMuted(False)
            self.mute_btn.setText("🔊")
        else:
            self.media_player.setMuted(True)
            self.mute_btn.setText("🔇")
    
    def change_speed(self, speed_text):
        speed = float(speed_text.replace('x', ''))
        self.media_player.setPlaybackRate(speed)
    
    def media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.next_media()
    
    def seek_forward(self):
        position = self.media_player.position() + 10000  # 10 seconds
        self.media_player.setPosition(position)
    
    def seek_backward(self):
        position = self.media_player.position() - 10000  # 10 seconds
        self.media_player.setPosition(max(0, position))
    
    def volume_up(self):
        volume = min(100, self.volume_slider.value() + 5)
        self.volume_slider.setValue(volume)
    
    def volume_down(self):
        volume = max(0, self.volume_slider.value() - 5)
        self.volume_slider.setValue(volume)
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def toggle_playlist(self):
        if self.left_panel.isVisible():
            self.left_panel.hide()
        else:
            self.left_panel.show()
    
    def clear_playlist(self):
        self.playlist_model.clear()
        self.current_index = -1
    
    def show_playlist_context_menu(self, position):
        index = self.playlist_view.indexAt(position)
        if index.isValid():
            menu = QMenu(self)
            remove_action = menu.addAction("Remove")
            action = menu.exec_(self.playlist_view.mapToGlobal(position))
            
            if action == remove_action:
                self.playlist_model.removeMedia(index.row())
                if self.current_index == index.row():
                    self.current_index = -1
                elif self.current_index > index.row():
                    self.current_index -= 1
    
    def show_about(self):
        QMessageBox.about(self, "About", 
                         "Modern Media Player\n\n"
                         "A feature-rich media player built with PyQt5\n"
                         "Supports various audio and video formats\n\n"
                         "Features:\n"
                         "• Playlist management\n"
                         "• Speed control\n"
                         "• Keyboard shortcuts\n"
                         "• Dark theme\n"
                         "• Fullscreen mode")
    
    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        hours = minutes // 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes%60:02d}:{seconds%60:02d}"
        else:
            return f"{minutes:02d}:{seconds%60:02d}"
    
    def load_settings(self):
        # Load window geometry
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        
        # Load volume
        volume = self.settings.value("volume", 70, type=int)
        self.volume_slider.setValue(volume)
        self.media_player.setVolume(volume)
    
    def save_settings(self):
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Save volume
        self.settings.setValue("volume", self.volume_slider.value())
    
    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("Modern Media Player")
    app.setOrganizationName("MediaPlayer")
    
    player = MediaPlayer()
    player.show()
    
    sys.exit(app.exec_())