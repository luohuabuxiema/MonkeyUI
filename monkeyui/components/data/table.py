import os
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtCore import Qt

class MkTable(QTableWidget):
    """
    表格组件 (Table)
    """
    def __init__(self, rows=0, columns=0, parent=None):
        super().__init__(rows, columns, parent)
        
        # Behavior
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setShowGrid(False)
        
        # Header configs
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalHeader().setVisible(False)

        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ebeef5;
                background-color: #ffffff;
                gridline-color: transparent;
                font-size: 14px;
                color: #606266;
            }
            QHeaderView::section {
                background-color: #f5f7fa;
                color: #909399;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #ebeef5;
                padding: 12px 8px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #ebeef5;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #f0f9eb; /* or #e6f6f4 */
                color: #606266;
            }
            QTableWidget::item:hover {
                background-color: #f5f7fa;
            }
        """)

    def set_headers(self, headers):
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

    def set_data(self, data):
        self.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, item in enumerate(row_data):
                table_item = QTableWidgetItem(str(item))
                # Add some padding or let stylesheet handle it
                self.setItem(row_idx, col_idx, table_item)
