import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSizePolicy
from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtGui import QIntValidator

class MkPagination(QWidget):
    """
    分页器 (Pagination) 组件
    模仿 Element Plus 风格
    """
    pageChanged = Signal(int)

    def __init__(self, total=0, page_size=10, current=1, parent=None):
        super().__init__(parent)
        self._total = total
        self._page_size = page_size
        self._current_page = current
        self._total_pages = max(1, (self._total + self._page_size - 1) // self._page_size)

        self._setup_ui()
        self._update_ui()

    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Style
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #606266;
                min-width: 32px;
                min-height: 32px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #00a896; /* #409eff if you prefer blue */
            }
            QPushButton:disabled {
                color: #c0c4cc;
                background-color: transparent;
            }
            QPushButton.active {
                background-color: #00a896;
                color: white;
            }
            QPushButton.active:hover {
                color: white;
            }
            QLabel {
                color: #606266;
                font-size: 14px;
                margin: 0 4px;
            }
            QLineEdit {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                color: #606266;
                min-width: 40px;
                max-width: 40px;
                min-height: 28px;
                text-align: center;
                padding: 0 4px;
            }
            QLineEdit:focus {
                border-color: #00a896;
            }
        """)

        # Total label
        self.total_label = QLabel(f"共计 {self._total}")
        self.layout.addWidget(self.total_label)

        # Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(4)
        self.layout.addLayout(self.buttons_layout)

        # Jump layout
        self.jump_layout = QHBoxLayout()
        self.jump_layout.setSpacing(4)
        self.jump_layout.addWidget(QLabel("页"))
        
        self.jump_input = QLineEdit(str(self._current_page))
        self.jump_input.setValidator(QIntValidator(1, 9999))
        self.jump_input.setAlignment(Qt.AlignCenter)
        self.jump_input.returnPressed.connect(self._on_jump)
        self.jump_layout.addWidget(self.jump_input)

        self.layout.addLayout(self.jump_layout)

    def _update_ui(self):
        # Clear existing buttons
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._total_pages = max(1, (self._total + self._page_size - 1) // self._page_size)
        self.total_label.setText(f"共计 {self._total}")
        self.jump_input.setText(str(self._current_page))

        # Prev button
        prev_btn = QPushButton("◀")
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.setEnabled(self._current_page > 1)
        prev_btn.clicked.connect(lambda: self.set_current_page(self._current_page - 1))
        self.buttons_layout.addWidget(prev_btn)

        # Page buttons logic (simplified for now, showing max 7 buttons)
        pages = self._get_page_list()
        for p in pages:
            if p == "...":
                btn = QPushButton("...")
                btn.setEnabled(False)
            else:
                btn = QPushButton(str(p))
                btn.setCursor(Qt.PointingHandCursor)
                if p == self._current_page:
                    btn.setProperty("class", "active")
                btn.clicked.connect(lambda checked, page=p: self.set_current_page(page))
            self.buttons_layout.addWidget(btn)

        # Next button
        next_btn = QPushButton("▶")
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.setEnabled(self._current_page < self._total_pages)
        next_btn.clicked.connect(lambda: self.set_current_page(self._current_page + 1))
        self.buttons_layout.addWidget(next_btn)

    def _get_page_list(self):
        # Always show 1, last, and around current
        if self._total_pages <= 7:
            return list(range(1, self._total_pages + 1))
        
        pages = [1]
        if self._current_page > 3:
            pages.append("...")
        
        start = max(2, self._current_page - 1)
        end = min(self._total_pages - 1, self._current_page + 1)
        
        # Adjust if current page is near the edges
        if self._current_page <= 3:
            end = 4
        if self._current_page >= self._total_pages - 2:
            start = self._total_pages - 3
            
        pages.extend(range(start, end + 1))
        
        if self._current_page < self._total_pages - 2:
            pages.append("...")
        pages.append(self._total_pages)
        
        return pages

    def _on_jump(self):
        text = self.jump_input.text()
        if text.isdigit():
            page = int(text)
            self.set_current_page(page)

    def set_current_page(self, page):
        page = max(1, min(page, self._total_pages))
        if self._current_page != page:
            self._current_page = page
            self._update_ui()
            self.pageChanged.emit(self._current_page)

    def set_total(self, total):
        self._total = max(0, total)
        self._update_ui()

    def set_page_size(self, size):
        self._page_size = max(1, size)
        self._update_ui()

    @Property(int)
    def current_page(self):
        return self._current_page

    @Property(int)
    def total(self):
        return self._total
