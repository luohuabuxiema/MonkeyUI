# -*- coding: utf-8 -*-
"""
@File ：upload.py
@Desc ：Modern web-style file drag-and-drop upload component for MonkeyUI.
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QFileDialog, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QEvent, QSize
from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor
from monkeyui.core.icons import MkPhosphorIcon
from monkeyui.components.basic.button import MkButton

class MkUpload(QWidget):
    """
    Modern file upload component supporting drag-and-drop,
    file list display, size validation, and type filters.
    """
    
    filesSelected = Signal(list)  # Emitted when new files are selected/dropped
    fileRemoved = Signal(str)     # Emitted when a file is removed from selection
    
    def __init__(self, parent=None, multiple=False, accept_filters=None, max_size_mb=50.0, tip_text=""):
        super().__init__(parent)
        self._multiple = multiple
        self._accept_filters = accept_filters if accept_filters else ["*.*"]
        self._max_size_mb = max_size_mb
        self._tip_text = tip_text if tip_text else f"支持任意文件，单文件不超过 {max_size_mb}MB"
        
        # Internal state
        self._selected_files = []  # List of absolute file paths
        
        # Set up layouts
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(12)
        
        # 1. Drag & Drop Area Frame
        self.drop_area = QFrame()
        self.drop_area.setObjectName("MkDropArea")
        self.drop_area.setFrameShape(QFrame.Shape.NoFrame)
        self.drop_area.setAcceptDrops(True)
        self.drop_area.installEventFilter(self)
        
        # Layout inside drop area
        self.drop_layout = QVBoxLayout(self.drop_area)
        self.drop_layout.setContentsMargins(20, 30, 20, 30)
        self.drop_layout.setSpacing(10)
        self.drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Cloud/Upload Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setScaledContents(True)
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.drop_layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Main Instruction Text
        self.main_text_label = QLabel("将文件拖拽到此处，或 点击上传")
        self.main_text_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Medium))
        self.main_text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.drop_layout.addWidget(self.main_text_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Secondary Helper/Tip Text
        self.tip_label = QLabel(self._tip_text)
        self.tip_label.setFont(QFont("Microsoft YaHei", 8))
        self.tip_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.drop_layout.addWidget(self.tip_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.main_layout.addWidget(self.drop_area)
        
        # 2. File List Widget
        self.file_list_widget = QWidget()
        self.file_list_layout = QVBoxLayout(self.file_list_widget)
        self.file_list_layout.setContentsMargins(0, 0, 0, 0)
        self.file_list_layout.setSpacing(6)
        self.file_list_widget.setVisible(False)
        
        self.main_layout.addWidget(self.file_list_widget)
        
        # Apply initial styles
        self.set_drag_state(False)
        self.update_icons()
        
    def update_icons(self):
        # High resolution upload icon
        upload_pix = MkPhosphorIcon.get_pixmap("upload-simple", "#64748b", 48)
        self.icon_label.setPixmap(upload_pix)

    def set_drag_state(self, active: bool):
        # Styles reflecting standard modern element-plus/shadcn file uploader colors
        if active:
            # Active Drag Enter style: bright blue border and soft highlight background
            self.drop_area.setStyleSheet("""
                QFrame#MkDropArea {
                    border: 2px dashed #3b82f6;
                    border-radius: 8px;
                    background-color: #eff6ff;
                }
            """)
            self.main_text_label.setStyleSheet("color: #2563eb;")
            self.tip_label.setStyleSheet("color: #60a5fa;")
            self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap("upload-simple", "#3b82f6", 48))
        else:
            # Normal style: soft gray dashed border and pale background, highlighting on hover
            self.drop_area.setStyleSheet("""
                QFrame#MkDropArea {
                    border: 2px dashed #cbd5e1;
                    border-radius: 8px;
                    background-color: #f8fafc;
                }
                QFrame#MkDropArea:hover {
                    border-color: #3b82f6;
                    background-color: #eff6ff;
                }
            """)
            self.main_text_label.setStyleSheet("color: #334155;")
            self.tip_label.setStyleSheet("color: #64748b;")
            self.icon_label.setPixmap(MkPhosphorIcon.get_pixmap("upload-simple", "#64748b", 48))

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj == self.drop_area:
            if event.type() == QEvent.Type.MouseButtonPress:
                # Trigger manual selection on left-click
                if event.button() == Qt.MouseButton.LeftButton:
                    self.trigger_file_dialog()
                    return True
            elif event.type() == QEvent.Type.DragEnter:
                # Hover file inside boundary
                if event.mimeData().hasUrls():
                    local_files = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
                    if local_files:
                        event.acceptProposedAction()
                        self.set_drag_state(True)
                        return True
            elif event.type() == QEvent.Type.DragLeave:
                self.set_drag_state(False)
                return True
            elif event.type() == QEvent.Type.Drop:
                # Drop file
                self.set_drag_state(False)
                urls = event.mimeData().urls()
                files = [url.toLocalFile() for url in urls if url.isLocalFile()]
                if files:
                    self.handle_files_selected(files)
                    event.acceptProposedAction()
                    return True
        return super().eventFilter(obj, event)

    def trigger_file_dialog(self):
        # Convert wildcards into standard QFileDialog filter string
        filter_str = "Selected Files (" + " ".join(self._accept_filters) + ");;All Files (*.*)"
        
        if self._multiple:
            files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", filter_str)
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", filter_str)
            files = [file_path] if file_path else []
            
        if files:
            self.handle_files_selected(files)

    def handle_files_selected(self, files: list):
        valid_files = []
        rejected_reasons = []
        
        for file_path in files:
            if not os.path.exists(file_path):
                continue
                
            # 1. Check size limit
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self._max_size_mb:
                rejected_reasons.append(f"文件 '{os.path.basename(file_path)}' 超过了最大体积限制 ({self._max_size_mb}MB)。")
                continue
                
            # 2. Check type filter
            if not self._check_file_filter(file_path):
                rejected_reasons.append(f"文件 '{os.path.basename(file_path)}' 不符合后缀要求 ({', '.join(self._accept_filters)})。")
                continue
                
            valid_files.append(file_path)
            
        # Display alerts if any rejected
        if rejected_reasons:
            from monkeyui.components.form.auth import MkMessage
            for reason in rejected_reasons:
                MkMessage.warning(self.window(), reason)
                
        if not valid_files:
            return
            
        if self._multiple:
            # Append new selections excluding duplicates
            for f in valid_files:
                if f not in self._selected_files:
                    self._selected_files.append(f)
        else:
            # Replace single file
            self._selected_files = [valid_files[0]]
            
        # Refresh GUI file list
        self.rebuild_file_list()
        
        # Emit signal
        self.filesSelected.emit(list(self._selected_files))

    def _check_file_filter(self, file_path: str) -> bool:
        if "*.*" in self._accept_filters or "*" in self._accept_filters:
            return True
            
        _, ext = os.path.splitext(file_path.lower())
        for f in self._accept_filters:
            clean_filter = f.replace("*", "").lower()
            if ext == clean_filter or clean_filter == ext:
                return True
        return False

    def rebuild_file_list(self):
        # Clear layout first
        while self.file_list_layout.count():
            item = self.file_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if not self._selected_files:
            self.file_list_widget.setVisible(False)
            return
            
        self.file_list_widget.setVisible(True)
        
        for file_path in self._selected_files:
            # Create a card frame for each file
            card = QFrame()
            card.setObjectName("FileCard")
            card.setStyleSheet("""
                QFrame#FileCard {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                }
                QFrame#FileCard:hover {
                    background-color: #f1f5f9;
                    border-color: #cbd5e1;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(10)
            
            # File symbol icon
            doc_icon = QLabel()
            doc_icon.setPixmap(MkPhosphorIcon.get_pixmap("file", "#475569", 16))
            card_layout.addWidget(doc_icon)
            
            # File name label
            file_name = os.path.basename(file_path)
            name_label = QLabel(file_name)
            name_label.setFont(QFont("Microsoft YaHei", 9))
            name_label.setStyleSheet("color: #1e293b; background: transparent; border: none;")
            # Elide text if too long
            name_label.setToolTip(file_path)
            card_layout.addWidget(name_label, stretch=1)
            
            # File size label
            size_bytes = os.path.getsize(file_path)
            size_text = self._format_file_size(size_bytes)
            size_label = QLabel(size_text)
            size_label.setFont(QFont("Microsoft YaHei", 8))
            size_label.setStyleSheet("color: #64748b; background: transparent; border: none;")
            card_layout.addWidget(size_label)
            
            # Delete button
            btn_del = QPushButton()
            btn_del.setFixedSize(20, 20)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setIcon(MkPhosphorIcon.get_icon("trash", "#94a3b8", "#ef4444", 14))
            btn_del.setStyleSheet("QPushButton { border: none; background: transparent; }")
            btn_del.clicked.connect(lambda checked=False, f=file_path: self.remove_file(f))
            card_layout.addWidget(btn_del)
            
            self.file_list_layout.addWidget(card)

    def _format_file_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def remove_file(self, file_path: str):
        if file_path in self._selected_files:
            self._selected_files.remove(file_path)
            self.rebuild_file_list()
            self.fileRemoved.emit(file_path)
            self.filesSelected.emit(list(self._selected_files))

    def get_files(self) -> list:
        """Returns the list of absolute file paths currently selected."""
        return list(self._selected_files)

    def clear(self):
        """Clears all uploaded files."""
        self._selected_files.clear()
        self.rebuild_file_list()
