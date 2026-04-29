from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QComboBox, QPushButton, QLabel, QSplitter,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
    QPlainTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QKeySequence, QShortcut


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(self.editor._line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor._paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_number_area_width(0)

        # マルチカーソル用
        self._extra_cursors: list[QTextCursor] = []

    def _line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        from PyQt6.QtCore import QRect
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height())
        )

    def _paint_line_numbers(self, event):
        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e2e"))

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#555577"))
                painter.setFont(self.font())
                painter.drawText(
                    0, top,
                    self.line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_num + 1)
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_num += 1

    def _highlight_current_line(self):
        from PyQt6.QtGui import QColor
        from PyQt6.QtWidgets import QTextEdit
        extra = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor("#2a2a3e"))
            sel.format.setProperty(
                sel.format.Property.FullWidthSelection, True
            )
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

    # ─────────────── マルチカーソル (Ctrl+D) ────────────────────
    def add_cursor_at_selection(self):
        """選択テキストと同じ次の出現箇所にカーソルを追加"""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        selected = cursor.selectedText()
        doc = self.document()
        from PyQt6.QtGui import QTextDocument
        found = doc.find(selected, cursor.selectionEnd())
        if found.isNull():
            return
        self._extra_cursors.append(found)
        self._apply_extra_cursors_highlight()

    def _apply_extra_cursors_highlight(self):
        from PyQt6.QtGui import QColor
        from PyQt6.QtWidgets import QTextEdit
        extra = []
        # 現在行ハイライト
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor("#2a2a3e"))
        sel.format.setProperty(sel.format.Property.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        extra.append(sel)
        # マルチカーソルハイライト
        for c in self._extra_cursors:
            s = QTextEdit.ExtraSelection()
            s.format.setBackground(QColor("#44475a"))
            s.cursor = c
            extra.append(s)
        self.setExtraSelections(extra)

    def keyPressEvent(self, event):
        if self._extra_cursors and event.key() not in (
            Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt
        ):
            for c in self._extra_cursors:
                if event.key() == Qt.Key.Key_Backspace:
                    c.deletePreviousChar()
                elif event.text():
                    c.insertText(event.text())
        super().keyPressEvent(event)


class EditorPanel(QWidget):
    note_saved = pyqtSignal()

    def __init__(self, note_manager, file_manager, config, parent=None):
        super().__init__(parent)
        self.nm = note_manager
        self.fm = file_manager
        self.config = config
        self.current_note_id: str | None = None
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._build_ui()
        self._setup_shortcuts()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # タイトル行
        title_row = QHBoxLayout()
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("タイトル")
        self.title_edit.setObjectName("titleEdit")
        self.cat_combo = QComboBox()
        self.cat_combo.setObjectName("catCombo")
        self.cat_combo.setMinimumWidth(120)
        title_row.addWidget(QLabel("タイトル:"))
        title_row.addWidget(self.title_edit, 3)
        title_row.addWidget(QLabel("カテゴリ:"))
        title_row.addWidget(self.cat_combo, 1)
        layout.addLayout(title_row)

        # 検索バー（初期非表示）
        self.search_bar = QWidget()
        sb_layout = QHBoxLayout(self.search_bar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索...")
        self.btn_find_next = QPushButton("次へ")
        self.btn_find_prev = QPushButton("前へ")
        self.btn_search_close = QPushButton("✕")
        sb_layout.addWidget(QLabel("検索:"))
        sb_layout.addWidget(self.search_input)
        sb_layout.addWidget(self.btn_find_prev)
        sb_layout.addWidget(self.btn_find_next)
        sb_layout.addWidget(self.btn_search_close)
        self.search_bar.setVisible(False)
        layout.addWidget(self.search_bar)

        # テキストエディタ
        self.editor = CodeEditor()
        self.editor.setObjectName("mainEditor")
        layout.addWidget(self.editor, 5)

        # 添付ファイルエリア
        att_label = QLabel("📎 添付ファイル")
        att_label.setObjectName("sectionLabel")
        layout.addWidget(att_label)

        att_row = QHBoxLayout()
        self.btn_attach = QPushButton("ファイルを追加")
        self.btn_attach.setObjectName("btnAttach")
        self.btn_detach = QPushButton("🗑 選択を削除")
        self.btn_detach.setObjectName("btnDel")
        att_row.addWidget(self.btn_attach)
        att_row.addWidget(self.btn_detach)
        att_row.addStretch()
        layout.addLayout(att_row)

        self.att_list = QListWidget()
        self.att_list.setObjectName("attList")
        self.att_list.setMaximumHeight(100)
        self.att_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self.att_list)

        # ステータスバー
        status_row = QHBoxLayout()
        self.lbl_char_count = QLabel("文字数: 0")
        self.lbl_char_count.setObjectName("statusLabel")
        self.btn_history = QPushButton("📋 履歴")
        self.btn_history.setObjectName("btnHistory")
        status_row.addWidget(self.lbl_char_count)
        status_row.addStretch()
        status_row.addWidget(self.btn_history)
        layout.addLayout(status_row)

        # シグナル接続
        self.title_edit.textChanged.connect(self._on_content_changed)
        self.cat_combo.currentTextChanged.connect(self._on_content_changed)
        self.editor.textChanged.connect(self._on_text_changed)
        self.btn_attach.clicked.connect(self._on_attach)
        self.btn_detach.clicked.connect(self._on_detach)
        self.att_list.itemDoubleClicked.connect(self._on_open_attachment)
        self.att_list.customContextMenuRequested.connect(self._on_att_context_menu)
        self.btn_search_close.clicked.connect(lambda: self.search_bar.setVisible(False))
        self.btn_find_next.clicked.connect(lambda: self._find_text(forward=True))
        self.btn_find_prev.clicked.connect(lambda: self._find_text(forward=False))
        self.btn_history.clicked.connect(self._show_history)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self, self._manual_save)
        QShortcut(QKeySequence("Ctrl+F"), self, self._toggle_search)

    # ─────────────────── メモ読み込み ────────────────────────────
    def load_note(self, note_id: str):
        self._auto_save_timer.stop()
        self.current_note_id = note_id
        note = self.nm.get_note(note_id)
        if note is None:
            return
        self.title_edit.blockSignals(True)
        self.editor.blockSignals(True)
        self.title_edit.setText(note["title"])
        self.editor.setPlainText(note["body"])
        idx = self.cat_combo.findText(note["category"])
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)
        self.title_edit.blockSignals(False)
        self.editor.blockSignals(False)
        self._refresh_attachments(note)
        self._update_char_count()

    def _refresh_attachments(self, note: dict):
        self.att_list.clear()
        for fname in note.get("attachments", []):
            item = QListWidgetItem(fname)
            self.att_list.addItem(item)

    def refresh_categories(self, categories: list[str]):
        current = self.cat_combo.currentText()
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItems(categories)
        idx = self.cat_combo.findText(current)
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)
        self.cat_combo.blockSignals(False)

    # ─────────────────── 保存 ────────────────────────────────────
    def _on_content_changed(self):
        self._auto_save_timer.start(3000)  # 3秒後に自動保存

    def _on_text_changed(self):
        self._update_char_count()
        self._on_content_changed()

    def _auto_save(self):
        self._save()

    def _manual_save(self):
        self._save()

    def _save(self):
        if self.current_note_id is None:
            return
        self.nm.update_note(
            self.current_note_id,
            title=self.title_edit.text(),
            body=self.editor.toPlainText(),
            category=self.cat_combo.currentText(),
        )
        self.nm.save()
        self.note_saved.emit()

    # ─────────────────── 文字数 ──────────────────────────────────
    def _update_char_count(self):
        count = len(self.editor.toPlainText())
        self.lbl_char_count.setText(f"文字数: {count}")

    def apply_config(self, config: dict):
        self.config = config
        family = config.get("font_family", "Consolas")
        size   = config.get("font_size", 12)
        font = QFont(family, size)
        self.editor.setFont(font)
        # スタイルシートの固定指定を動的上書きしてフォントを確実に反映
        self.editor.setStyleSheet(
            f"QPlainTextEdit#mainEditor {{"
            f"  background-color: #0a0a14;"
            f"  color: #f0f2ff;"
            f"  border: 1px solid #3d3d5c;"
            f"  selection-background-color: #3d3d7a;"
            f"  padding: 4px;"
            f"  font-family: '{family}';"
            f"  font-size: {size}pt;"
            f"}}"
        )
        wrap = config.get("word_wrap", True)
        from PyQt6.QtWidgets import QPlainTextEdit
        self.editor.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth if wrap
            else QPlainTextEdit.LineWrapMode.NoWrap
        )

    # ─────────────────── 検索 ────────────────────────────────────
    def _toggle_search(self):
        self.search_bar.setVisible(not self.search_bar.isVisible())
        if self.search_bar.isVisible():
            self.search_input.setFocus()

    def _find_text(self, forward: bool = True):
        text = self.search_input.text()
        if not text:
            return
        from PyQt6.QtGui import QTextDocument
        flag = QTextDocument.FindFlag(0)
        if not forward:
            flag = QTextDocument.FindFlag.FindBackward
        found = self.editor.find(text, flag)
        if not found:
            # 先頭 or 末尾に折り返し
            cursor = self.editor.textCursor()
            cursor.movePosition(
                QTextCursor.MoveOperation.Start if forward
                else QTextCursor.MoveOperation.End
            )
            self.editor.setTextCursor(cursor)
            self.editor.find(text, flag)

    # ─────────────────── 添付ファイル ────────────────────────────
    def _on_attach(self):
        if self.current_note_id is None:
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "ファイルを選択")
        for path in paths:
            fname = self.fm.copy_attachment(path)
            if fname:
                self.nm.add_attachment(self.current_note_id, fname)
        self.nm.save()
        note = self.nm.get_note(self.current_note_id)
        if note:
            self._refresh_attachments(note)

    def _on_detach(self):
        """選択中の添付ファイルを削除（ボタン）"""
        item = self.att_list.currentItem()
        if item is None:
            return
        self._delete_attachment(item.text())

    def _on_att_context_menu(self, pos):
        """添付ファイルリストの右クリックメニュー"""
        from PyQt6.QtWidgets import QMenu
        item = self.att_list.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        act_open = menu.addAction("開く")
        act_del  = menu.addAction("削除")
        action = menu.exec(self.att_list.viewport().mapToGlobal(pos))
        if action == act_open:
            self._on_open_attachment(item)
        elif action == act_del:
            self._delete_attachment(item.text())

    def _delete_attachment(self, fname: str):
        """確認ダイアログ→物理削除→メモデータから除去"""
        reply = QMessageBox.question(
            self, "添付ファイル削除",
            f"「{fname}」を削除しますか？\nファイルは完全に削除されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.fm.delete_attachment(fname)
        if self.current_note_id:
            self.nm.remove_attachment(self.current_note_id, fname)
            self.nm.save()
            note = self.nm.get_note(self.current_note_id)
            if note:
                self._refresh_attachments(note)

    def _on_open_attachment(self, item: QListWidgetItem):
        fname = item.text()
        if not self.fm.open_attachment(fname):
            QMessageBox.warning(self, "エラー", f"ファイルが見つかりません: {fname}")

    # ─────────────────── 履歴 ────────────────────────────────────
    def _show_history(self):
        if self.current_note_id is None:
            return
        note = self.nm.get_note(self.current_note_id)
        if not note or not note.get("history"):
            QMessageBox.information(self, "履歴", "履歴がありません。")
            return

        from PyQt6.QtWidgets import QDialog, QListWidget, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("編集履歴")
        dlg.resize(400, 300)
        dlg_layout = QVBoxLayout(dlg)
        lst = QListWidget()
        for i, h in enumerate(reversed(note["history"])):
            lst.addItem(f"{h['saved_at']}  |  {h['title']}")
        dlg_layout.addWidget(lst)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        dlg_layout.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted and lst.currentRow() >= 0:
            rev_index = lst.currentRow()
            actual_index = len(note["history"]) - 1 - rev_index
            reply = QMessageBox.question(
                self, "確認",
                "選択したバージョンに復元しますか？\n現在の内容は履歴に追加されます。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.nm.restore_history(self.current_note_id, actual_index)
                self.nm.save()
                self.load_note(self.current_note_id)
                self.note_saved.emit()