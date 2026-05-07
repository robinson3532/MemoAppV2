from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QCheckBox, QGroupBox,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QComboBox
)
from PyQt6.QtCore import pyqtSignal
from pathlib import Path


class SettingsTab(QWidget):
    settings_changed = pyqtSignal(dict)

    def __init__(self, config: dict, note_manager, backup_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.nm = note_manager
        self.bm = backup_manager
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── 保存設定 ──────────────────────────────────────────────
        grp_save = QGroupBox("保存設定")
        grp_save_layout = QVBoxLayout(grp_save)

        # 保存ディレクトリ
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("保存ディレクトリ:"))
        self.edit_save_dir = QLineEdit()
        self.btn_browse_save = QPushButton("参照")
        row1.addWidget(self.edit_save_dir)
        row1.addWidget(self.btn_browse_save)
        grp_save_layout.addLayout(row1)

        # notes.json読み込みパス
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("読み込むnotes.jsonパス:"))
        self.edit_notes_path = QLineEdit()
        self.edit_notes_path.setPlaceholderText("空欄の場合は保存ディレクトリのnotes.jsonを使用")
        self.btn_browse_notes = QPushButton("参照")
        row2.addWidget(self.edit_notes_path)
        row2.addWidget(self.btn_browse_notes)
        grp_save_layout.addLayout(row2)

        layout.addWidget(grp_save)

        # ── 表示設定 ──────────────────────────────────────────────
        grp_disp = QGroupBox("表示設定")
        grp_disp_layout = QVBoxLayout(grp_disp)
        grp_disp_layout.setSpacing(6)

        row_wrap = QHBoxLayout()
        self.chk_wrap = QCheckBox("行を折り返す")
        row_wrap.addWidget(self.chk_wrap)
        row_wrap.addStretch()
        grp_disp_layout.addLayout(row_wrap)

        row_font = QHBoxLayout()
        row_font.setSpacing(6)
        lbl_font = QLabel("フォント:")
        lbl_font.setFixedWidth(60)
        row_font.addWidget(lbl_font)
        self.combo_font = QComboBox()
        self.combo_font.setFixedWidth(160)
        self.combo_font.addItems(["Consolas", "Courier New", "MS Gothic", "Yu Gothic", "Meiryo"])
        row_font.addWidget(self.combo_font)
        lbl_size = QLabel("サイズ:")
        lbl_size.setFixedWidth(50)
        row_font.addWidget(lbl_size)
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(6, 48)
        self.spin_font_size.setFixedWidth(90)  # 数値+矢印が重ならない幅
        self.spin_font_size.setMinimumWidth(90)
        row_font.addWidget(self.spin_font_size)
        row_font.addStretch()
        grp_disp_layout.addLayout(row_font)

        layout.addWidget(grp_disp)

        # ── 履歴設定 ──────────────────────────────────────────────
        grp_hist = QGroupBox("編集履歴設定")
        grp_hist_layout = QHBoxLayout(grp_hist)
        grp_hist_layout.addWidget(QLabel("保持バージョン数:"))
        self.spin_history = QSpinBox()
        self.spin_history.setRange(1, 100)
        self.spin_history.setFixedWidth(90)
        self.spin_history.setMinimumWidth(90)
        grp_hist_layout.addWidget(self.spin_history)
        grp_hist_layout.addStretch()
        layout.addWidget(grp_hist)

        # ── バックアップ設定 ──────────────────────────────────────
        grp_backup = QGroupBox("バックアップ設定")
        grp_backup_layout = QVBoxLayout(grp_backup)

        row_gen = QHBoxLayout()
        row_gen.addWidget(QLabel("保持世代数:"))
        self.spin_backup_gen = QSpinBox()
        self.spin_backup_gen.setRange(1, 50)
        self.spin_backup_gen.setFixedWidth(90)
        self.spin_backup_gen.setMinimumWidth(90)
        row_gen.addWidget(self.spin_backup_gen)
        row_gen.addStretch()
        self.btn_export_zip = QPushButton("📦 zipエクスポート")
        self.btn_export_zip.setFixedWidth(160)
        row_gen.addWidget(self.btn_export_zip)
        grp_backup_layout.addLayout(row_gen)

        # バックアップ一覧
        grp_backup_layout.addWidget(QLabel("バックアップ一覧（ダブルクリックで復元）:"))
        self.backup_list = QListWidget()
        self.backup_list.setMaximumHeight(150)
        grp_backup_layout.addWidget(self.backup_list)
        btn_refresh_row = QHBoxLayout()
        self.btn_refresh_backup = QPushButton("🔄 一覧を更新")
        self.btn_refresh_backup.setFixedWidth(140)
        btn_refresh_row.addWidget(self.btn_refresh_backup)
        btn_refresh_row.addStretch()
        grp_backup_layout.addLayout(btn_refresh_row)

        layout.addWidget(grp_backup)

        # ── 適用ボタン ────────────────────────────────────────────
        self.btn_apply = QPushButton("✅ 設定を適用")
        self.btn_apply.setObjectName("btnApply")
        layout.addWidget(self.btn_apply)
        layout.addStretch()

        # シグナル接続
        self.btn_browse_save.clicked.connect(self._browse_save_dir)
        self.btn_browse_notes.clicked.connect(self._browse_notes_path)
        self.btn_export_zip.clicked.connect(self._export_zip)
        self.btn_refresh_backup.clicked.connect(self.refresh_backup_list)
        self.backup_list.itemDoubleClicked.connect(self._restore_backup)
        self.btn_apply.clicked.connect(self._apply)

    def _load_values(self):
        self.edit_save_dir.setText(self.config.get("save_dir", ""))
        self.edit_notes_path.setText(self.config.get("notes_json_path", ""))
        self.chk_wrap.setChecked(self.config.get("word_wrap", True))
        font_idx = self.combo_font.findText(self.config.get("font_family", "Consolas"))
        if font_idx >= 0:
            self.combo_font.setCurrentIndex(font_idx)
        self.spin_font_size.setValue(self.config.get("font_size", 12))
        self.spin_history.setValue(self.config.get("max_history_versions", 10))
        self.spin_backup_gen.setValue(self.config.get("max_backup_generations", 5))
        self.refresh_backup_list()

    def _browse_save_dir(self):
        d = QFileDialog.getExistingDirectory(self, "保存ディレクトリを選択")
        if d:
            self.edit_save_dir.setText(d)

    def _browse_notes_path(self):
        p, _ = QFileDialog.getOpenFileName(self, "notes.jsonを選択", filter="JSON Files (*.json)")
        if p:
            self.edit_notes_path.setText(p)

    def _apply(self):
        self.config["save_dir"] = self.edit_save_dir.text().strip()
        self.config["notes_json_path"] = self.edit_notes_path.text().strip()
        self.config["word_wrap"] = self.chk_wrap.isChecked()
        self.config["font_family"] = self.combo_font.currentText()
        self.config["font_size"] = self.spin_font_size.value()
        self.config["max_history_versions"] = self.spin_history.value()
        self.config["max_backup_generations"] = self.spin_backup_gen.value()

        from utils.config import save_config, ensure_dirs
        save_config(self.config)
        ensure_dirs(self.config)
        self.settings_changed.emit(self.config)
        QMessageBox.information(self, "設定", "設定を適用しました。")

    def _export_zip(self):
        dest, _ = QFileDialog.getSaveFileName(
            self, "zipエクスポート先を選択", filter="Zip Files (*.zip)"
        )
        if not dest:
            return
        if not dest.endswith(".zip"):
            dest += ".zip"
        ok = self.bm.export_zip(dest)
        if ok:
            QMessageBox.information(self, "完了", f"エクスポートしました:\n{dest}")
        else:
            QMessageBox.warning(self, "エラー", "エクスポートに失敗しました。")

    def refresh_backup_list(self):
        self.backup_list.clear()
        for b in self.bm.list_backups():
            item = QListWidgetItem(b["label"])
            item.setData(256, b["path"])
            self.backup_list.addItem(item)

    def _restore_backup(self, item: QListWidgetItem):
        path = item.data(256)
        label = item.text()
        reply = QMessageBox.question(
            self, "バックアップ復元",
            f"「{label}」のバックアップを復元しますか？\n現在のデータは上書きされます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok = self.bm.restore_backup(path)
            if ok:
                self.nm.reload(self.config)
                self.settings_changed.emit(self.config)
                QMessageBox.information(self, "完了", "バックアップを復元しました。")
            else:
                QMessageBox.warning(self, "エラー", "復元に失敗しました。")
