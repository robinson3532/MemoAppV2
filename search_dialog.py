from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtCore import pyqtSignal


class SearchDialog(QDialog):
    note_selected = pyqtSignal(str)  # note_id

    def __init__(self, note_manager, parent=None):
        super().__init__(parent)
        self.nm = note_manager
        self.setWindowTitle("全文検索")
        self.resize(500, 400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("検索キーワードを入力...")
        self.btn_search = QPushButton("検索")
        row.addWidget(self.input)
        row.addWidget(self.btn_search)
        layout.addLayout(row)

        self.lbl_result = QLabel("結果: 0件")
        layout.addWidget(self.lbl_result)

        self.result_list = QListWidget()
        layout.addWidget(self.result_list)

        self.btn_search.clicked.connect(self._do_search)
        self.input.returnPressed.connect(self._do_search)
        self.result_list.itemDoubleClicked.connect(self._on_select)

    def _do_search(self):
        query = self.input.text().strip()
        if not query:
            return
        results = self.nm.search(query)
        self.result_list.clear()
        for n in results:
            item = QListWidgetItem(f"[{n['category']}]  {n['title']}  ({n['updated_at']})")
            item.setData(256, n["id"])
            self.result_list.addItem(item)
        self.lbl_result.setText(f"結果: {len(results)}件")

    def _on_select(self, item: QListWidgetItem):
        note_id = item.data(256)
        if note_id:
            self.note_selected.emit(note_id)
            self.accept()
