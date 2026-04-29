from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QMessageBox, QStatusBar,
    QScrollArea, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QFont

from ui.tree_panel import TreePanel
from ui.editor_panel import EditorPanel
from ui.settings_tab import SettingsTab
from ui.search_dialog import SearchDialog
from core.note_manager import NoteManager
from core.file_manager import FileManager
from core.backup_manager import BackupManager
from utils.config import load_config, save_config, ensure_dirs

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #0d0d1a;
    color: #e8eaf6;
    font-family: "Yu Gothic UI", "Meiryo UI", "Segoe UI", sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #3d3d5c;
    background-color: #12122a;
}

QTabBar::tab {
    background: #0d0d1a;
    color: #b0b8e0;
    padding: 8px 20px;
    border: 1px solid #3d3d5c;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #12122a;
    color: #ffffff;
    border-bottom: 2px solid #cba6f7;
}

QTreeWidget {
    background-color: #0d0d1a;
    border: 1px solid #3d3d5c;
    color: #e8eaf6;
    selection-background-color: #2d2d5a;
    outline: none;
}

QTreeWidget::item:hover {
    background-color: #1e1e3a;
}

QTreeWidget::item:selected {
    background-color: #2d2d5a;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #0a0a14;
    color: #c8cfff;
    padding: 5px;
    border: none;
    border-right: 1px solid #3d3d5c;
    border-bottom: 1px solid #3d3d5c;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #1a1a30;
    color: #cba6f7;
}

QPlainTextEdit#mainEditor {
    background-color: #0a0a14;
    color: #f0f2ff;
    border: 1px solid #3d3d5c;
    selection-background-color: #3d3d7a;
    padding: 4px;
}

QLineEdit {
    background-color: #0d0d1a;
    border: 1px solid #4a4a70;
    color: #f0f2ff;
    padding: 4px 8px;
    border-radius: 4px;
}

QLineEdit:focus {
    border: 1px solid #cba6f7;
    background-color: #12122a;
}

QLineEdit#titleEdit {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
}

QComboBox {
    background-color: #0d0d1a;
    border: 1px solid #4a4a70;
    color: #f0f2ff;
    padding: 4px 8px;
    border-radius: 4px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #12122a;
    color: #f0f2ff;
    selection-background-color: #2d2d5a;
}

QPushButton {
    background-color: #252550;
    color: #e0e4ff;
    border: 1px solid #4a4a70;
    padding: 5px 12px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #35357a;
    color: #ffffff;
    border-color: #cba6f7;
}

QPushButton:pressed {
    background-color: #4a4a99;
}

QPushButton#btnNew {
    background-color: #0d2b4a;
    color: #7dd8f0;
    border-color: #2a6080;
}

QPushButton#btnNew:hover {
    background-color: #1a4a70;
    color: #ffffff;
}

QPushButton#btnDel {
    background-color: #3a0f0f;
    color: #ff8fa3;
    border-color: #6a2020;
}

QPushButton#btnDel:hover {
    background-color: #5a1515;
    color: #ffffff;
}

QPushButton#btnApply {
    background-color: #0f3020;
    color: #7dffb0;
    border-color: #1a6040;
    font-weight: bold;
    padding: 8px 20px;
}

QPushButton#btnApply:hover {
    background-color: #1a5035;
    color: #ffffff;
}

QGroupBox {
    border: 1px solid #4a4a70;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
    color: #c8cfff;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #cba6f7;
}

QListWidget {
    background-color: #0a0a14;
    border: 1px solid #3d3d5c;
    color: #e8eaf6;
    selection-background-color: #2d2d5a;
}

QListWidget::item:hover {
    background-color: #1a1a30;
}

QListWidget::item:selected {
    color: #ffffff;
    background-color: #2d2d5a;
}

QSpinBox {
    background-color: #0d0d1a;
    border: 1px solid #4a4a70;
    color: #f0f2ff;
    padding: 3px 6px;
    border-radius: 4px;
}

QCheckBox {
    color: #e8eaf6;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #6060a0;
    border-radius: 3px;
    background-color: #0d0d1a;
}

QCheckBox::indicator:unchecked {
    background-color: #0d0d1a;
}

QCheckBox::indicator:checked {
    background-color: #cba6f7;
    border-color: #cba6f7;
    image: none;
}

QSpinBox {
    background-color: #0d0d1a;
    border: 1px solid #4a4a70;
    color: #f0f2ff;
    padding: 3px 20px 3px 6px;
    border-radius: 4px;
    min-width: 90px;
}

QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #4a4a70;
    border-bottom: 1px solid #4a4a70;
    background-color: #252550;
    border-top-right-radius: 4px;
}

QSpinBox::up-button:hover {
    background-color: #35357a;
}

QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid #4a4a70;
    background-color: #252550;
    border-bottom-right-radius: 4px;
}

QSpinBox::down-button:hover {
    background-color: #35357a;
}

QSpinBox::up-arrow {
    width: 8px;
    height: 8px;
}

QSpinBox::down-arrow {
    width: 8px;
    height: 8px;
}

QLabel#sectionLabel {
    color: #c8cfff;
    font-weight: bold;
    padding-top: 4px;
}

QLabel#statusLabel {
    color: #9090c0;
    font-size: 11px;
}

QSplitter::handle {
    background-color: #3d3d5c;
    width: 2px;
}

QScrollBar:vertical {
    background: #0a0a14;
    width: 10px;
    border: none;
}

QScrollBar::handle:vertical {
    background: #3d3d7a;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #5a5aaa;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QStatusBar {
    background-color: #080810;
    color: #9090c0;
    border-top: 1px solid #3d3d5c;
}

QDialog {
    background-color: #12122a;
    color: #e8eaf6;
}

QMessageBox {
    background-color: #12122a;
    color: #e8eaf6;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MemoApp")
        self.resize(1200, 780)
        self.setStyleSheet(DARK_STYLE)

        # 設定・マネージャ初期化
        self.config = load_config()
        ensure_dirs(self.config)

        self.nm = NoteManager(self.config)
        self.fm = FileManager(self.config)
        self.bm = BackupManager(self.config)

        self._build_ui()
        self._setup_shortcuts()
        self._setup_status_bar()

        # 起動時にツリーを描画
        self.tree_panel.refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # タブ
        self.tab_widget = QTabWidget()
        root_layout.addWidget(self.tab_widget)

        # ── メモタブ ──────────────────────────────────────────────
        memo_tab = QWidget()
        memo_layout = QHBoxLayout(memo_tab)
        memo_layout.setContentsMargins(4, 4, 4, 4)
        memo_layout.setSpacing(4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tree_panel = TreePanel(self.nm)
        self.tree_panel.setMinimumWidth(220)
        self.tree_panel.setMaximumWidth(400)

        self.editor_panel = EditorPanel(self.nm, self.fm, self.config)
        self.editor_panel.apply_config(self.config)

        splitter.addWidget(self.tree_panel)
        splitter.addWidget(self.editor_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([260, 900])

        memo_layout.addWidget(splitter)
        self.tab_widget.addTab(memo_tab, "📝 メモ")

        # ── 設定タブ ──────────────────────────────────────────────
        self.settings_tab = SettingsTab(self.config, self.nm, self.bm)
        self.tab_widget.addTab(self.settings_tab, "⚙️ 設定")

        # ── ショートカット一覧タブ ────────────────────────────────
        self.tab_widget.addTab(self._build_shortcut_tab(), "⌨️ ショートカット")

        # シグナル接続
        self.tree_panel.note_selected.connect(self._on_note_selected)
        self.tree_panel.note_create.connect(self._on_note_create)
        self.tree_panel.note_delete.connect(self._on_note_delete)
        self.tree_panel.category_changed.connect(self._on_category_changed)
        self.editor_panel.note_saved.connect(self._on_note_saved)
        self.settings_tab.settings_changed.connect(self._on_settings_changed)

    def _build_shortcut_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        SHORTCUTS = [
            ("メモ操作", [
                ("Ctrl+N",             "新規メモ作成（New memo）"),
                ("Ctrl+S",             "メモを保存（Save）"),
                ("削除ボタン",          "選択中のメモを削除（Delete memo）"),
            ]),
            ("テキスト編集", [
                ("Ctrl+Z",             "Undo"),
                ("Ctrl+Y",             "Redo"),
                ("Ctrl+C",             "Copy"),
                ("Ctrl+X",             "Cut"),
                ("Ctrl+V",             "Paste"),
                ("Ctrl+A",             "Select All"),
            ]),
            ("検索", [
                ("Ctrl+F",             "本文内検索バーを開く／閉じる（Find）"),
                ("Ctrl+G",             "全文検索ダイアログを開く（Global search）"),
            ]),
        ]

        for section, items in SHORTCUTS:
            # セクションヘッダ
            hdr = QLabel(section)
            hdr_font = QFont()
            hdr_font.setBold(True)
            hdr_font.setPointSize(13)
            hdr.setFont(hdr_font)
            hdr.setStyleSheet("color: #cba6f7; padding-top: 4px;")
            layout.addWidget(hdr)

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setStyleSheet("color: #3d3d5c;")
            layout.addWidget(line)

            for keys, desc in items:
                row = QHBoxLayout()
                lbl_key = QLabel(keys)
                lbl_key.setStyleSheet(
                    "background:#1a1a35; color:#89dceb; padding:3px 10px;"
                    "border-radius:4px; font-family:Consolas,monospace; font-size:12px;"
                )
                lbl_key.setFixedWidth(280)
                lbl_desc = QLabel(desc)
                lbl_desc.setStyleSheet("color:#e8eaf6; padding-left:12px;")
                row.addWidget(lbl_key)
                row.addWidget(lbl_desc)
                row.addStretch()
                layout.addLayout(row)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, self._on_note_create)
        QShortcut(QKeySequence("Ctrl+G"), self, self._open_global_search)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")

    # ─────────────────── イベントハンドラ ────────────────────────
    def _on_note_selected(self, note_id: str):
        self.editor_panel.load_note(note_id)
        note = self.nm.get_note(note_id)
        if note:
            self.status_bar.showMessage(f"メモを開きました: {note['title']}")

    def _on_note_create(self):
        note = self.nm.create_note()
        self.nm.save()
        self.tree_panel.refresh()
        self.tree_panel.select_note(note["id"])
        self.editor_panel.load_note(note["id"])
        self.status_bar.showMessage("新規メモを作成しました")

    def _on_note_delete(self, note_id: str):
        note = self.nm.get_note(note_id)
        if note is None:
            return
        reply = QMessageBox.question(
            self, "削除確認",
            f"「{note['title']}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.nm.delete_note(note_id)
            self.nm.save()
            self.tree_panel.refresh()
            # エディタをクリア
            self.editor_panel.current_note_id = None
            self.editor_panel.title_edit.clear()
            self.editor_panel.editor.clear()
            self.status_bar.showMessage("メモを削除しました")

    def _on_category_changed(self):
        self.editor_panel.refresh_categories(self.nm.categories)

    def _on_note_saved(self):
        self.tree_panel.refresh()
        # 保存時に自動バックアップ
        self.bm.create_auto_backup()
        self.status_bar.showMessage("保存しました", 2000)

    def _on_settings_changed(self, config: dict):
        self.config = config
        self.nm.reload(config)
        self.fm.config = config
        self.bm.config = config
        # フォント・折り返しをエディタに即時反映
        self.editor_panel.apply_config(config)
        self.editor_panel.refresh_categories(self.nm.categories)
        self.tree_panel.refresh()
        self.settings_tab.refresh_backup_list()
        self.status_bar.showMessage(
            f"設定を反映しました（フォント: {config.get('font_family','Consolas')} {config.get('font_size',12)}pt）",
            3000
        )

    def _open_global_search(self):
        dlg = SearchDialog(self.nm, self)
        dlg.note_selected.connect(self._on_note_selected)
        dlg.exec()

    def closeEvent(self, event):
        save_config(self.config)
        event.accept()