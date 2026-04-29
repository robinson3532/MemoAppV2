from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu,
    QInputDialog, QMessageBox, QDialog, QListWidget,
    QListWidgetItem, QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class CategoryEditDialog(QDialog):
    def __init__(self, note_manager, parent=None):
        super().__init__(parent)
        self.nm = note_manager
        self.setWindowTitle("カテゴリ編集")
        self.setMinimumSize(360, 320)
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.addWidget(QLabel("カテゴリ一覧（「未分類」は削除・リネーム不可）"))
        self.cat_list = QListWidget()
        layout.addWidget(self.cat_list)
        btn_row = QHBoxLayout()
        self.btn_add    = QPushButton("＋ 追加")
        self.btn_rename = QPushButton("✏ リネーム")
        self.btn_delete = QPushButton("🗑 削除")
        self.btn_delete.setObjectName("btnDel")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_rename)
        btn_row.addWidget(self.btn_delete)
        layout.addLayout(btn_row)
        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(self.accept)
        layout.addWidget(close_btn)
        self.btn_add.clicked.connect(self._on_add)
        self.btn_rename.clicked.connect(self._on_rename)
        self.btn_delete.clicked.connect(self._on_delete)

    def _refresh_list(self):
        self.cat_list.clear()
        for cat in self.nm.categories:
            self.cat_list.addItem(QListWidgetItem(cat))

    def _current_name(self):
        item = self.cat_list.currentItem()
        return item.text() if item else None

    def _on_add(self):
        name, ok = QInputDialog.getText(self, "カテゴリ追加", "新しいカテゴリ名:")
        if ok and name.strip():
            if self.nm.add_category(name.strip()):
                self.nm.save()
                self._refresh_list()
            else:
                QMessageBox.warning(self, "警告", "同名のカテゴリが既に存在します。")

    def _on_rename(self):
        old = self._current_name()
        if old is None:
            return
        if old == "未分類":
            QMessageBox.warning(self, "警告", "「未分類」はリネームできません。")
            return
        new, ok = QInputDialog.getText(self, "リネーム", f"「{old}」の新しい名前:", text=old)
        if ok and new.strip() and new.strip() != old:
            if self.nm.rename_category(old, new.strip()):
                self.nm.save()
                self._refresh_list()
            else:
                QMessageBox.warning(self, "警告", "同名のカテゴリが既に存在するか、リネームできません。")

    def _on_delete(self):
        name = self._current_name()
        if name is None:
            return
        if name == "未分類":
            QMessageBox.warning(self, "警告", "「未分類」は削除できません。")
            return
        reply = QMessageBox.question(
            self, "カテゴリ削除",
            f"「{name}」を削除しますか？\n属するメモは「未分類」に移動されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.nm.delete_category(name)
            self.nm.save()
            self._refresh_list()


class TreePanel(QWidget):
    note_selected    = pyqtSignal(str)
    note_create      = pyqtSignal()
    note_delete      = pyqtSignal(str)
    category_changed = pyqtSignal()

    def __init__(self, note_manager, parent=None):
        super().__init__(parent)
        self.nm = note_manager
        self._sort_col = 0
        self._sort_asc = True
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        btn_row = QHBoxLayout()
        self.btn_new = QPushButton("＋ 新規メモ")
        self.btn_new.setObjectName("btnNew")
        self.btn_del = QPushButton("🗑 削除")
        self.btn_del.setObjectName("btnDel")
        self.btn_edit_cat = QPushButton("📁 カテゴリ編集")
        self.btn_edit_cat.setObjectName("btnCat")
        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_del)
        btn_row.addWidget(self.btn_edit_cat)
        layout.addLayout(btn_row)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["タイトル", "更新日時"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionsClickable(True)
        self.tree.setIndentation(20)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self.tree)

        self.btn_new.clicked.connect(self.note_create.emit)
        self.btn_del.clicked.connect(self._on_delete)
        self.btn_edit_cat.clicked.connect(self._on_edit_categories)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.header().sectionClicked.connect(self._on_header_clicked)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

    def refresh(self):
        expanded = set()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.isExpanded():
                expanded.add(item.text(0))
        self.tree.clear()
        for cat in self.nm.categories:
            cat_item = QTreeWidgetItem([cat, ""])
            cat_item.setData(0, Qt.ItemDataRole.UserRole, None)
            cat_item.setData(0, Qt.ItemDataRole.UserRole + 1, "category")
            font = QFont()
            font.setBold(True)
            cat_item.setFont(0, font)
            self.tree.addTopLevelItem(cat_item)
            notes = self._sort_notes(self.nm.get_notes_by_category(cat))
            for n in notes:
                child = QTreeWidgetItem([n["title"], n["updated_at"]])
                child.setData(0, Qt.ItemDataRole.UserRole, n["id"])
                child.setData(0, Qt.ItemDataRole.UserRole + 1, "note")
                cat_item.addChild(child)
            if cat in expanded:
                cat_item.setExpanded(True)
        self.tree.header().setSortIndicatorShown(True)
        self.tree.header().setSortIndicator(
            self._sort_col,
            Qt.SortOrder.AscendingOrder if self._sort_asc else Qt.SortOrder.DescendingOrder
        )

    def _sort_notes(self, notes):
        key = "updated_at" if self._sort_col == 1 else "title"
        return sorted(notes, key=lambda n: n[key], reverse=not self._sort_asc)

    def _on_item_clicked(self, item, col):
        kind = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if kind == "note":
            note_id = item.data(0, Qt.ItemDataRole.UserRole)
            if note_id:
                self.note_selected.emit(note_id)
        elif kind == "category":
            item.setExpanded(not item.isExpanded())

    def _on_header_clicked(self, col):
        if col == self._sort_col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self.refresh()

    def _on_delete(self):
        item = self.tree.currentItem()
        if item is None:
            return
        kind = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if kind == "note":
            self.note_delete.emit(item.data(0, Qt.ItemDataRole.UserRole))
        elif kind == "category":
            self._delete_category(item.text(0))

    def _on_edit_categories(self):
        dlg = CategoryEditDialog(self.nm, self)
        dlg.exec()
        self.refresh()
        self.category_changed.emit()

    def _delete_category(self, name):
        if name == "未分類":
            QMessageBox.warning(self, "警告", "「未分類」は削除できません。")
            return
        reply = QMessageBox.question(
            self, "カテゴリ削除",
            f"「{name}」を削除しますか？\n属するメモは「未分類」に移動されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.nm.delete_category(name)
            self.nm.save()
            self.refresh()
            self.category_changed.emit()

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is None:
            return
        kind = item.data(0, Qt.ItemDataRole.UserRole + 1)
        menu = QMenu(self)
        if kind == "category":
            act_edit = menu.addAction("カテゴリを編集")
            act_del  = menu.addAction("カテゴリを削除")
            action = menu.exec(self.tree.viewport().mapToGlobal(pos))
            if action == act_edit:
                self._on_edit_categories()
            elif action == act_del:
                self._delete_category(item.text(0))
        elif kind == "note":
            act_del = menu.addAction("メモを削除")
            action = menu.exec(self.tree.viewport().mapToGlobal(pos))
            if action == act_del:
                self.note_delete.emit(item.data(0, Qt.ItemDataRole.UserRole))

    def select_note(self, note_id):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            cat_item = root.child(i)
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                if child.data(0, Qt.ItemDataRole.UserRole) == note_id:
                    self.tree.setCurrentItem(child)
                    return