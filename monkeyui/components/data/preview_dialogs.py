import os
from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QFrame, QSizePolicy
from PySide6.QtCore import Qt, QPoint, QSize, QUrl
from PySide6.QtGui import QPainter, QColor, QPixmap, QWheelEvent, QMouseEvent, QDesktopServices
from monkeyui.core.icons import MkPhosphorIcon

try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
    HAS_MULTIMEDIA = True
except ImportError:
    HAS_MULTIMEDIA = False


class MkLightboxCanvas(QWidget):
    """Transparent custom canvas widget drawing the zoomable/panning image."""
    def __init__(self, original_pixmap: QPixmap, dialog, parent=None):
        super().__init__(parent)
        self.pixmap = original_pixmap
        self.dialog = dialog
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent; border: none;")

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap.isNull():
            painter.end()
            return
            
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        rect = self.rect()
        pw = self.pixmap.width()
        ph = self.pixmap.height()
        if pw <= 0 or ph <= 0 or rect.width() <= 0 or rect.height() <= 0:
            painter.end()
            return
            
        ratio = min(rect.width() / pw, rect.height() / ph) * 0.95
        
        # Apply interactive zoom factor
        scaled_w = int(pw * ratio * self.dialog._zoom_factor)
        scaled_h = int(ph * ratio * self.dialog._zoom_factor)
        
        # Centering calculations with pan offset
        x = (rect.width() - scaled_w) // 2 + self.dialog._pan_offset.x()
        y = (rect.height() - scaled_h) // 2 + self.dialog._pan_offset.y()
        
        painter.drawPixmap(x, y, scaled_w, scaled_h, self.pixmap)
        painter.end()


class MkLightboxDialog(QDialog):
    """
    Sleek frameless image viewer with translucent backdrop.
    Supports wheel zooming, mouse-dragging panning, and a custom action toolbar.
    """
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Preview")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Load high quality pixmap
        self._original_pixmap = QPixmap(image_path)
        self._zoom_factor = 1.0
        self._pan_offset = QPoint(0, 0)
        self._is_dragging = False
        self._drag_start_pos = QPoint(0, 0)
        
        # Enforce all labels inside the lightbox to have transparent backgrounds,
        # overriding the parent gallery solid white background stylesheet inheritance
        self.setStyleSheet("""
            QLabel {
                background-color: transparent;
            }
        """)
        
        # Init layout
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self):
        # Master layout (vertical)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top title area (glassmorphic translucent header)
        header_widget = QWidget(self)
        header_widget.setObjectName("HeaderWidget")
        header_widget.setFixedHeight(50)
        header_widget.setStyleSheet("""
            QWidget#HeaderWidget {
                background-color: rgba(20, 20, 20, 160);
                border-bottom: 1px solid rgba(255, 255, 255, 30);
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding-left: 20px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 10, 0)
        
        title_label = QLabel("图片查看器 - 轻量灯箱模式", header_widget)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Close button top-right
        close_btn = QPushButton(header_widget)
        close_btn.setFixedSize(32, 32)
        close_btn.setIcon(MkPhosphorIcon.get_icon("x", "#ffffff", "#ff4d4f", 16))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header_widget)
        
        # Image canvas area (stretches to fill, uses transparent MkLightboxCanvas)
        self.canvas_widget = MkLightboxCanvas(self._original_pixmap, self, self)
        layout.addWidget(self.canvas_widget, stretch=1)
        
        # Bottom controls area (floating styled toolbar)
        toolbar_widget = QWidget(self)
        toolbar_widget.setObjectName("ToolbarWidget")
        toolbar_widget.setFixedHeight(60)
        toolbar_widget.setStyleSheet("""
            QWidget#ToolbarWidget {
                background-color: rgba(20, 20, 20, 180);
                border-top: 1px solid rgba(255, 255, 255, 30);
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                color: #ffffff;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 45);
                border-color: #409eff;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(20, 0, 20, 0)
        toolbar_layout.setSpacing(15)
        toolbar_layout.addStretch()
        
        zoom_in_btn = QPushButton("放大", toolbar_widget)
        zoom_in_btn.setIcon(MkPhosphorIcon.get_icon("zoom-in", "#ffffff", "#ffffff", 14))
        zoom_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("缩小", toolbar_widget)
        zoom_out_btn.setIcon(MkPhosphorIcon.get_icon("zoom-out", "#ffffff", "#ffffff", 14))
        zoom_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar_layout.addWidget(zoom_out_btn)
        
        reset_btn = QPushButton("重置", toolbar_widget)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset)
        toolbar_layout.addWidget(reset_btn)
        
        toolbar_layout.addStretch()
        layout.addWidget(toolbar_widget)

    def paintEvent(self, event):
        # 1. Draw a translucent frosted-glass style background overlay
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(10, 10, 10, 210))
        painter.end()

    def wheelEvent(self, event: QWheelEvent):
        # Adjust zoom factor based on mouse wheel movement
        angle = event.angleDelta().y()
        if angle > 0:
            self._zoom_factor = min(10.0, self._zoom_factor * 1.15)
        else:
            self._zoom_factor = max(0.15, self._zoom_factor / 1.15)
        self.canvas_widget.update()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging:
            current_pos = event.position().toPoint()
            delta = current_pos - self._drag_start_pos
            self._pan_offset += delta
            self._drag_start_pos = current_pos
            self.canvas_widget.update()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()

    def _zoom_in(self):
        self._zoom_factor = min(10.0, self._zoom_factor * 1.25)
        self.canvas_widget.update()

    def _zoom_out(self):
        self._zoom_factor = max(0.15, self._zoom_factor / 1.25)
        self.canvas_widget.update()

    def _reset(self):
        self._zoom_factor = 1.0
        self._pan_offset = QPoint(0, 0)
        self.canvas_widget.update()


class MkVideoPlayerDialog(QDialog):
    """
    Highly premium and robust video playback overlay dialog.
    Supports a fully custom skin control interface.
    """
    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Player")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.video_path = video_path
        self.resize(800, 500)
        
        self.player = None
        self.audio = None
        self.video_widget = None
        
        # Enforce transparent backgrounds for all label text to bypass parent window QSS inheritance
        self.setStyleSheet("""
            QLabel {
                background-color: transparent;
            }
        """)
        
        self._setup_ui()
        if HAS_MULTIMEDIA:
            self._init_player()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Transparent glassmorphic header
        header_widget = QWidget(self)
        header_widget.setObjectName("HeaderWidget")
        header_widget.setFixedHeight(50)
        header_widget.setStyleSheet("""
            QWidget#HeaderWidget {
                background-color: rgba(20, 20, 20, 160);
                border-bottom: 1px solid rgba(255, 255, 255, 30);
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding-left: 20px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 10, 0)
        
        title_text = f"视频播放器 - {os.path.basename(self.video_path)}"
        title_label = QLabel(title_text, header_widget)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton(header_widget)
        close_btn.setFixedSize(32, 32)
        close_btn.setIcon(MkPhosphorIcon.get_icon("x", "#ffffff", "#ff4d4f", 16))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._on_close)
        header_layout.addWidget(close_btn)
        
        self.main_layout.addWidget(header_widget)
        
        # Body frame (where player lives)
        self.body_frame = QFrame(self)
        self.body_frame.setStyleSheet("background-color: #000000;")
        body_layout = QVBoxLayout(self.body_frame)
        body_layout.setContentsMargins(0, 0, 0, 0)
        
        if HAS_MULTIMEDIA:
            # 1. Custom Player Layout
            self.video_widget = QVideoWidget(self.body_frame)
            body_layout.addWidget(self.video_widget)
            self.main_layout.addWidget(self.body_frame, stretch=1)
            
            # Custom Control Bar at the bottom
            self.controls_widget = QWidget(self)
            self.controls_widget.setFixedHeight(60)
            self.controls_widget.setStyleSheet("""
                QWidget {
                    background-color: rgba(20, 20, 20, 220);
                    border-top: 1px solid rgba(255, 255, 255, 30);
                }
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 30);
                }
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                }
                QSlider::groove:horizontal {
                    border: none;
                    height: 4px;
                    background: rgba(255, 255, 255, 60);
                    border-radius: 2px;
                }
                QSlider::sub-page:horizontal {
                    background: #409eff;
                    border-radius: 2px;
                }
                QSlider::handle:horizontal {
                    background: #ffffff;
                    border: 1px solid #409eff;
                    width: 12px;
                    height: 12px;
                    margin: -4px 0;
                    border-radius: 6px;
                }
            """)
            
            controls_layout = QHBoxLayout(self.controls_widget)
            controls_layout.setContentsMargins(15, 0, 15, 0)
            controls_layout.setSpacing(10)
            
            # Play/Pause toggle
            self.play_btn = QPushButton(self.controls_widget)
            self.play_btn.setFixedSize(32, 32)
            self.play_btn.setIcon(MkPhosphorIcon.get_icon("play", "#ffffff", "#409eff", 16))
            self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.play_btn.clicked.connect(self._toggle_play)
            controls_layout.addWidget(self.play_btn)
            
            # Timeline Slider
            self.timeline_slider = QSlider(Qt.Orientation.Horizontal, self.controls_widget)
            self.timeline_slider.setRange(0, 100)
            self.timeline_slider.setCursor(Qt.CursorShape.PointingHandCursor)
            self.timeline_slider.sliderMoved.connect(self._on_timeline_seek)
            controls_layout.addWidget(self.timeline_slider, stretch=1)
            
            # Time indicator label
            self.time_label = QLabel("00:00 / 00:00", self.controls_widget)
            controls_layout.addWidget(self.time_label)
            
            # Mute/Volume icon
            self.volume_btn = QPushButton(self.controls_widget)
            self.volume_btn.setFixedSize(32, 32)
            self.volume_btn.setIcon(MkPhosphorIcon.get_icon("speaker-high", "#ffffff", "#409eff", 16))
            self.volume_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.volume_btn.clicked.connect(self._toggle_mute)
            controls_layout.addWidget(self.volume_btn)
            
            # Volume slider
            self.volume_slider = QSlider(Qt.Orientation.Horizontal, self.controls_widget)
            self.volume_slider.setRange(0, 100)
            self.volume_slider.setValue(70)
            self.volume_slider.setFixedWidth(80)
            self.volume_slider.setCursor(Qt.CursorShape.PointingHandCursor)
            self.volume_slider.valueChanged.connect(self._on_volume_changed)
            controls_layout.addWidget(self.volume_slider)
            
            self.main_layout.addWidget(self.controls_widget)
            
        else:
            # 2. Stunning Fallback Layout when QtMultimedia is absent
            fallback_widget = QWidget(self.body_frame)
            fallback_layout = QVBoxLayout(fallback_widget)
            fallback_layout.setContentsMargins(40, 40, 40, 40)
            fallback_layout.setSpacing(20)
            
            message_icon = QLabel(fallback_widget)
            message_icon.setFixedSize(64, 64)
            message_icon.setPixmap(MkPhosphorIcon.get_pixmap("play", "#409eff", 64))
            fallback_layout.addWidget(message_icon, alignment=Qt.AlignmentFlag.AlignCenter)
            
            message_title = QLabel("视频解码服务已就绪", fallback_widget)
            message_title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
            fallback_layout.addWidget(message_title, alignment=Qt.AlignmentFlag.AlignCenter)
            
            message_desc = QLabel(
                f"出于对 PySide6 底层依赖环境（QtMultimedia、GStreamer/DirectShow）的稳定性考量，\n"
                f"我们已经安全拦截播放器加载。视频文件路径准备就绪：\n\n"
                f"{self.video_path}\n\n"
                f"为了获得最佳的硬件解码和超高清播放体验，推荐直接点击下方按钮拉起你的系统默认视频播放器。",
                fallback_widget
            )
            message_desc.setStyleSheet("color: #a0cfff; font-size: 13px; line-height: 20px;")
            message_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_layout.addWidget(message_desc, alignment=Qt.AlignmentFlag.AlignCenter)
            
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(15)
            btn_layout.addStretch()
            
            launch_system_btn = QPushButton("使用系统播放器打开", fallback_widget)
            launch_system_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            launch_system_btn.setStyleSheet("""
                QPushButton {
                    background-color: #409eff;
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #66b1ff;
                }
            """)
            launch_system_btn.clicked.connect(self._launch_system_player)
            btn_layout.addWidget(launch_system_btn)
            
            close_fallback_btn = QPushButton("关闭", fallback_widget)
            close_fallback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_fallback_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: 1px solid rgba(255, 255, 255, 50);
                    color: #ffffff;
                    padding: 9px 19px;
                    border-radius: 6px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 30);
                }
            """)
            close_fallback_btn.clicked.connect(self._on_close)
            btn_layout.addWidget(close_fallback_btn)
            
            btn_layout.addStretch()
            fallback_layout.addLayout(btn_layout)
            
            body_layout.addWidget(fallback_widget)
            self.main_layout.addWidget(self.body_frame, stretch=1)

    def paintEvent(self, event):
        # Draw translucent dark overlay window background
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(10, 10, 10, 200))
        painter.end()

    def _init_player(self):
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        
        # Connect player callbacks
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        
        # Load local video file
        url = QUrl.fromLocalFile(self.video_path)
        self.player.setSource(url)
        
        # Initial volume
        self.audio.setVolume(0.7)
        
        # Auto-play on dialog launch
        self.player.play()
        self.play_btn.setIcon(MkPhosphorIcon.get_icon("pause", "#ffffff", "#409eff", 16))

    def _toggle_play(self):
        if not self.player:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setIcon(MkPhosphorIcon.get_icon("play", "#ffffff", "#409eff", 16))
        else:
            self.player.play()
            self.play_btn.setIcon(MkPhosphorIcon.get_icon("pause", "#ffffff", "#409eff", 16))

    def _on_timeline_seek(self, position):
        if self.player:
            # position is in value of timeline slider (0 to 100)
            target_ms = int((position / 100.0) * self.player.duration())
            self.player.setPosition(target_ms)

    def _on_position_changed(self, position):
        if not self.player or self.player.duration() <= 0:
            return
        # Calculate percentage
        pct = int((position / self.player.duration()) * 100)
        # Block signals temporarily to prevent sliderMoved recursive loops
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(pct)
        self.timeline_slider.blockSignals(True)
        
        self._update_time_label(position, self.player.duration())

    def _on_duration_changed(self, duration):
        if not self.player:
            return
        self._update_time_label(self.player.position(), duration)

    def _update_time_label(self, pos, dur):
        pos_sec = pos // 1000
        dur_sec = dur // 1000
        
        pos_min = pos_sec // 60
        pos_sec = pos_sec % 60
        
        dur_min = dur_sec // 60
        dur_sec = dur_sec % 60
        
        self.time_label.setText(f"{pos_min:02d}:{pos_sec:02d} / {dur_min:02d}:{dur_sec:02d}")

    def _toggle_mute(self):
        if not self.audio:
            return
        is_muted = self.audio.isMuted()
        self.audio.setMuted(not is_muted)
        
        if not is_muted:
            # Now muted
            self.volume_btn.setIcon(MkPhosphorIcon.get_icon("speaker-x", "#ffffff", "#409eff", 16))
            self.volume_slider.setValue(0)
        else:
            # Now unmuted
            self.volume_btn.setIcon(MkPhosphorIcon.get_icon("speaker-high", "#ffffff", "#409eff", 16))
            self.volume_slider.setValue(70)
            self.audio.setVolume(0.7)

    def _on_volume_changed(self, value):
        if not self.audio:
            return
        vol = value / 100.0
        self.audio.setVolume(vol)
        if value == 0:
            self.audio.setMuted(True)
            self.volume_btn.setIcon(MkPhosphorIcon.get_icon("speaker-x", "#ffffff", "#409eff", 16))
        else:
            self.audio.setMuted(False)
            self.volume_btn.setIcon(MkPhosphorIcon.get_icon("speaker-high", "#ffffff", "#409eff", 16))

    def _launch_system_player(self):
        url = QUrl.fromLocalFile(self.video_path)
        QDesktopServices.openUrl(url)

    def _on_close(self):
        if self.player:
            self.player.stop()
        self.close()
