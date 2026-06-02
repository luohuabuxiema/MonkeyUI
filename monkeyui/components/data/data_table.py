import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPixmap, QCursor, QFont, QPen
from monkeyui.components.basic.checkbox import MkCheckBox
from monkeyui.components.navigation.pagination import MkPagination
from monkeyui.components.data.preview_dialogs import MkLightboxDialog, MkVideoPlayerDialog
from monkeyui.core.icons import MkPhosphorIcon


class CheckBoxHeader(QHeaderView):
    """Custom table header view with a clickable selection checkbox in the first column."""
    stateChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._checked = False
        self.setSectionsClickable(True)
        self.sectionClicked.connect(self._on_section_clicked)
        # Give generous height to the header
        self.setDefaultSectionSize(40)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        # Call base painter to render sections and gridlines
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()

        if logicalIndex == 0:
            # Draw standard clean styling checkbox centered in section 0
            from PySide6.QtWidgets import QStyle, QStyleOptionButton
            option = QStyleOptionButton()
            
            # Center checkbox in the cell
            box_size = 16
            x = rect.x() + (rect.width() - box_size) // 2
            y = rect.y() + (rect.height() - box_size) // 2
            option.rect = QRect(x, y, box_size, box_size)
            
            option.state = QStyle.StateFlag.State_Enabled
            if self._checked:
                option.state |= QStyle.StateFlag.State_On
            else:
                option.state |= QStyle.StateFlag.State_Off
            
            self.style().drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorCheckBox, option, painter)

    def _on_section_clicked(self, logicalIndex):
        if logicalIndex == 0:
            self._checked = not self._checked
            self.viewport().update()
            self.stateChanged.emit(self._checked)

    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.viewport().update()


class MkImageCellWidget(QWidget):
    """Custom hover-active thumbnail container for image columns."""
    clicked = Signal(str)

    def __init__(self, img_path: str, parent=None):
        super().__init__(parent)
        self.img_path = img_path
        self._is_hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(50, 50)
        
        # Preload and scale pixmap
        self.pixmap = QPixmap(self.img_path)
        
    def enterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.img_path)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 1. Clip path for rounded border-radius 6px
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRoundedRect(QRect(0, 0, rect.width(), rect.height()), 6, 6)
        painter.setClipPath(path)
        
        if not self.pixmap.isNull():
            # Draw fitting image
            scaled_pixmap = self.pixmap.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            # Center offset draw
            x = (rect.width() - scaled_pixmap.width()) // 2
            y = (rect.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Draw solid fallback background
            painter.fillRect(rect, QColor("#f4f4f5"))
            painter.setPen(QColor("#a1a1aa"))
            font = QFont("Microsoft YaHei", 8)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No Img")
            
        # 2. Draw hover translucent overlay with Phosphor eye icon
        if self._is_hovered:
            painter.fillRect(rect, QColor(0, 0, 0, 100))
            eye_pixmap = MkPhosphorIcon.get_pixmap("eye", "#ffffff", 18)
            px = (rect.width() - 18) // 2
            py = (rect.height() - 18) // 2
            painter.drawPixmap(px, py, eye_pixmap)
            
        painter.end()


class MkVideoCellWidget(QWidget):
    """Custom hoverable cell displaying a video thumbnail preview with inline play overlay."""
    clicked = Signal(str)

    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self._is_hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(50, 50)

    def enterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video_path)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Clip path for rounded border-radius 6px
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRoundedRect(QRect(0, 0, rect.width(), rect.height()), 6, 6)
        painter.setClipPath(path)
        
        # Video background color (sleek slate background)
        painter.fillRect(rect, QColor("#0f172a") if not self._is_hovered else QColor("#1e293b"))
        
        # Draw dynamic play button
        icon_color = "#38bdf8" if self._is_hovered else "#ffffff"
        play_pix = MkPhosphorIcon.get_pixmap("play", icon_color, 24)
        px = (rect.width() - 24) // 2
        py = (rect.height() - 24) // 2
        painter.drawPixmap(px, py, play_pix)
        
        # Subtle hover border highlight
        if self._is_hovered:
            painter.setPen(QPen(QColor("#38bdf8"), 1.5))
            painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 6, 6)
            
        painter.end()


class MkDataTable(QWidget):
    """
    MkDataTable - Declarative shadcn-ui styled data table.
    Integrates pagination, multi-select check boxes, Phosphor actions, and lightboxes.
    """
    editRequested = Signal(int, dict)     # (absolute_row_index, row_dict)
    deleteRequested = Signal(int, dict)   # (absolute_row_index, row_dict)
    selectionChanged = Signal(list)       # list of selected row dicts

    def __init__(self, columns: list = None, data: list = None, page_size: int = 10, selection_enabled: bool = True, parent=None):
        super().__init__(parent)
        
        self.columns_config = columns or []
        self._all_data = data or []
        self.page_size = page_size
        self.selection_enabled = selection_enabled
        
        # Multi-page selection memory
        self._selected_keys = set()  # set of unique row keys/indices
        
        self._setup_ui()
        self.refresh_table()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(15)
        
        # 1. Shadcn-styled outer frame layout container
        self.table_card = QFrame(self)
        self.table_card.setObjectName("TableCard")
        self.table_card.setStyleSheet("""
            QFrame#TableCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        
        card_layout = QVBoxLayout(self.table_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        # 2. Main QTableWidget instantiation
        self.table_widget = QTableWidget(self.table_card)
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection) # Custom checkbox-based selection
        self.table_widget.setShowGrid(False)
        self.table_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(False)
        
        # Inject shadcn-ui stylesheets (slate borders, hover rows, clear headers)
        self.table_widget.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                gridline-color: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 13px;
                color: #0f172a;
            }
            QTableWidget::item {
                border-bottom: 1px solid #f1f5f9;
                padding: 12px 10px;
            }
            QTableWidget::item:hover {
                background-color: #f8fafc;
            }
        """)
        
        # Set up custom header view if checkboxes enabled
        if self.selection_enabled:
            self.header_view = CheckBoxHeader(self.table_widget)
            self.header_view.stateChanged.connect(self._on_header_checkbox_toggled)
        else:
            self.header_view = QHeaderView(Qt.Orientation.Horizontal, self.table_widget)
            self.header_view.setDefaultSectionSize(40)
            
        self.table_widget.setHorizontalHeader(self.header_view)
        
        # Style header view
        self.header_view.setStyleSheet("""
            QHeaderView::section {
                background-color: #f8fafc;
                color: #64748b;
                font-weight: 600;
                font-size: 12px;
                border: none;
                border-bottom: 1px solid #e2e8f0;
                padding: 10px 10px;
                text-align: left;
            }
        """)
        
        card_layout.addWidget(self.table_widget)
        self.main_layout.addWidget(self.table_card, stretch=1)
        
        # 3. Add bottom pagination widget
        self.pagination = MkPagination(total=len(self._all_data), page_size=self.page_size, current=1, parent=self)
        self.pagination.pageChanged.connect(self._on_page_changed)
        
        # Align pager beautifully to the right
        pager_container = QWidget(self)
        pager_layout = QHBoxLayout(pager_container)
        pager_layout.setContentsMargins(0, 5, 0, 0)
        pager_layout.addStretch()
        pager_layout.addWidget(self.pagination)
        
        self.main_layout.addWidget(pager_container)

    def set_data(self, data: list):
        """Sets new dataset and refreshes table from page 1."""
        self._all_data = data or []
        self._selected_keys.clear()
        self.pagination.set_total(len(self._all_data))
        self.pagination.set_current_page(1)
        self.refresh_table()
        self.selectionChanged.emit([])

    def refresh_table(self):
        """Re-populates table cells based on current page slice."""
        current_page = self.pagination.current_page
        start_idx = (current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self._all_data))
        page_data = self._all_data[start_idx:end_idx]
        
        # Set up column counts
        col_count = len(self.columns_config)
        if self.selection_enabled:
            col_count += 1
            
        self.table_widget.setColumnCount(col_count)
        self.table_widget.setRowCount(len(page_data))
        
        # Set horizontal headers
        headers = []
        if self.selection_enabled:
            headers.append("")  # Checkbox header has no label, drawn manually
            
        for col in self.columns_config:
            headers.append(col.get("label", ""))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # Stretch columns configuration
        header = self.table_widget.horizontalHeader()
        if self.selection_enabled:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            self.table_widget.setColumnWidth(0, 48)
            
        col_offset = 1 if self.selection_enabled else 0
        for idx, col in enumerate(self.columns_config):
            c_idx = idx + col_offset
            width = col.get("width")
            if width:
                header.setSectionResizeMode(c_idx, QHeaderView.ResizeMode.Fixed)
                self.table_widget.setColumnWidth(c_idx, width)
            else:
                header.setSectionResizeMode(c_idx, QHeaderView.ResizeMode.Stretch)
                
        # Fill cells
        for row_idx, row_dict in enumerate(page_data):
            abs_row_idx = start_idx + row_idx
            unique_key = self._get_unique_key(abs_row_idx, row_dict)
            
            # Set table row height to accommodate cells beautifully (72px to match premium high-density layouts)
            self.table_widget.setRowHeight(row_idx, 72)
            
            # Render selection checkbox if enabled
            if self.selection_enabled:
                chk = MkCheckBox()
                chk.setFixedSize(16, 16)  # Enforce exact size for perfect alignment
                chk.setChecked(unique_key in self._selected_keys)
                
                # Prevent checkbox from stealing click triggers and wrap cleanly
                container = QWidget()
                h_layout = QHBoxLayout(container)
                h_layout.addWidget(chk)
                h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                h_layout.setContentsMargins(0, 0, 0, 0)
                h_layout.setSpacing(0)
                
                # Re-emit selection change signals on check toggle
                chk.stateChanged.connect(
                    lambda state, key=unique_key: self._on_row_checkbox_toggled(key, state)
                )
                
                self.table_widget.setCellWidget(row_idx, 0, container)
                
            # Fill other columns
            for col_idx, col in enumerate(self.columns_config):
                c_idx = col_idx + col_offset
                col_type = col.get("type", "text")
                col_key = col.get("key")
                cell_val = row_dict.get(col_key, "")
                
                if col_type == "image":
                    # Image thumbnail lightbox cell
                    img_widget = MkImageCellWidget(str(cell_val))
                    img_widget.clicked.connect(self._open_image_lightbox)
                    
                    container = QWidget()
                    h_layout = QHBoxLayout(container)
                    h_layout.addWidget(img_widget)
                    h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    h_layout.setContentsMargins(0, 0, 0, 0)
                    
                    self.table_widget.setCellWidget(row_idx, c_idx, container)
                    
                elif col_type == "video":
                    # Video thumbnail cell launcher
                    vid_widget = MkVideoCellWidget(str(cell_val))
                    vid_widget.clicked.connect(self._open_video_player)
                    
                    container = QWidget()
                    h_layout = QHBoxLayout(container)
                    h_layout.addWidget(vid_widget)
                    h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    h_layout.setContentsMargins(0, 0, 0, 0)
                    
                    self.table_widget.setCellWidget(row_idx, c_idx, container)
                    
                elif col_type == "action":
                    # Actions cell with Phosphor edit/delete buttons
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(0, 0, 0, 0)
                    actions_layout.setSpacing(8)
                    actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    edit_btn = QPushButton(actions_widget)
                    edit_btn.setFixedSize(28, 28)
                    edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    edit_btn.setIcon(MkPhosphorIcon.get_icon("pencil", "#475569", "#3b82f6", 14))
                    edit_btn.setToolTip("编辑行记录")
                    edit_btn.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            border: 1px solid #cbd5e1;
                            border-radius: 4px;
                        }
                        QPushButton:hover {
                            background-color: #f1f5f9;
                            border-color: #3b82f6;
                        }
                    """)
                    # Connect absolute index pass closures
                    edit_btn.clicked.connect(
                        lambda checked, a_idx=abs_row_idx, r_val=row_dict: self.editRequested.emit(a_idx, r_val)
                    )
                    actions_layout.addWidget(edit_btn)
                    
                    del_btn = QPushButton(actions_widget)
                    del_btn.setFixedSize(28, 28)
                    del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    del_btn.setIcon(MkPhosphorIcon.get_icon("trash", "#64748b", "#ef4444", 14))
                    del_btn.setToolTip("删除行记录")
                    del_btn.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            border: 1px solid #cbd5e1;
                            border-radius: 4px;
                        }
                        QPushButton:hover {
                            background-color: #fef2f2;
                            border-color: #ef4444;
                        }
                    """)
                    del_btn.clicked.connect(
                        lambda checked, a_idx=abs_row_idx, r_val=row_dict: self.deleteRequested.emit(a_idx, r_val)
                    )
                    actions_layout.addWidget(del_btn)
                    
                    self.table_widget.setCellWidget(row_idx, c_idx, actions_widget)
                    
                else:
                    # Generic string cells
                    item = QTableWidgetItem(str(cell_val))
                    # Soft vertical align in grid cells
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.table_widget.setItem(row_idx, c_idx, item)
                    
        # Update header checkbox checkmark state
        if self.selection_enabled:
            self._update_header_checkbox_ui()

    def _get_unique_key(self, abs_row_idx: int, row_dict: dict):
        """Resolves unique key for tracking cell selection indices robustly."""
        # Use ID field if present, otherwise fallback to absolute dataset indices
        return row_dict.get("id", str(abs_row_idx))

    def _on_row_checkbox_toggled(self, unique_key, state):
        if state:
            self._selected_keys.add(unique_key)
        else:
            self._selected_keys.discard(unique_key)
            
        self._update_header_checkbox_ui()
        self._emit_selection_change()

    def _on_header_checkbox_toggled(self, checked: bool):
        current_page = self.pagination.current_page
        start_idx = (current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self._all_data))
        page_data = self._all_data[start_idx:end_idx]
        
        # Toggle checkbox selections on page slice items
        for r_idx, row_dict in enumerate(page_data):
            abs_idx = start_idx + r_idx
            key = self._get_unique_key(abs_idx, row_dict)
            if checked:
                self._selected_keys.add(key)
            else:
                self._selected_keys.discard(key)
                
        # Refresh current view cell widget statuses
        self.refresh_table()
        self._emit_selection_change()

    def _update_header_checkbox_ui(self):
        """Updates header master checkbox state according to current page items selection."""
        current_page = self.pagination.current_page
        start_idx = (current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self._all_data))
        page_data = self._all_data[start_idx:end_idx]
        
        if not page_data:
            self.header_view.setChecked(False)
            return
            
        # Checked if every page row is registered in the selected list
        all_checked = True
        for r_idx, row_dict in enumerate(page_data):
            abs_idx = start_idx + r_idx
            key = self._get_unique_key(abs_idx, row_dict)
            if key not in self._selected_keys:
                all_checked = False
                break
                
        self.header_view.setChecked(all_checked)

    def _emit_selection_change(self):
        """Resolves current selected dictionary items and triggers events."""
        selected_items = []
        for idx, row_dict in enumerate(self._all_data):
            key = self._get_unique_key(idx, row_dict)
            if key in self._selected_keys:
                selected_items.append(row_dict)
        self.selectionChanged.emit(selected_items)

    def _on_page_changed(self, page: int):
        self.refresh_table()

    def _open_image_lightbox(self, img_path: str):
        """Launches the overlay image zoom lightbox modal."""
        if not os.path.exists(img_path):
            return
        lightbox = MkLightboxDialog(img_path, self.window())
        lightbox.exec()

    def _open_video_player(self, video_path: str):
        """Launches the custom frameless video preview player."""
        player = MkVideoPlayerDialog(video_path, self.window())
        player.exec()

    def get_selected_rows(self) -> list:
        """Returns lists of currently selected row dicts."""
        selected_items = []
        for idx, row_dict in enumerate(self._all_data):
            key = self._get_unique_key(idx, row_dict)
            if key in self._selected_keys:
                selected_items.append(row_dict)
        return selected_items
