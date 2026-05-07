import json
import uuid
from datetime import datetime
from pathlib import Path


class NoteManager:
    def __init__(self, config: dict):
        self.config = config
        self.notes: list[dict] = []
        self.categories: list[str] = ["未分類"]
        self._load()

    # ───────────────────────── パス ─────────────────────────
    def _notes_path(self) -> Path:
        p = self.config.get("notes_json_path", "")
        if p:
            return Path(p)
        return Path(self.config["save_dir"]) / "notes.json"

    # ───────────────────────── 読み書き ─────────────────────
    def _load(self) -> None:
        path = self._notes_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.notes = data.get("notes", [])
                cats = data.get("categories", ["未分類"])
                if "未分類" not in cats:
                    cats.insert(0, "未分類")
                self.categories = cats
            except Exception as e:
                print(f"[NoteManager] 読み込みエラー: {e}")

    def save(self) -> None:
        path = self._notes_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"categories": self.categories, "notes": self.notes},
                f,
                ensure_ascii=False,
                indent=2,
            )

    def reload(self, config: dict) -> None:
        self.config = config
        self._load()

    # ───────────────────────── メモ CRUD ────────────────────
    def create_note(self, title: str = "新規メモ", category: str = "未分類") -> dict:
        note = {
            "id": str(uuid.uuid4()),
            "title": title,
            "category": category,
            "body": "",
            "updated_at": self._now(),
            "attachments": [],
            "history": [],
        }
        self.notes.append(note)
        return note

    def update_note(self, note_id: str, title: str = None, body: str = None,
                    category: str = None) -> dict | None:
        note = self.get_note(note_id)
        if note is None:
            return None

        max_ver = self.config.get("max_history_versions", 10)
        # 履歴に現在の状態を保存
        history_entry = {
            "body": note["body"],
            "title": note["title"],
            "saved_at": note["updated_at"],
        }
        note["history"].append(history_entry)
        if len(note["history"]) > max_ver:
            note["history"] = note["history"][-max_ver:]

        if title is not None:
            note["title"] = title
        if body is not None:
            note["body"] = body
        if category is not None:
            note["category"] = category
        note["updated_at"] = self._now()
        return note

    def delete_note(self, note_id: str) -> bool:
        before = len(self.notes)
        self.notes = [n for n in self.notes if n["id"] != note_id]
        return len(self.notes) < before

    def get_note(self, note_id: str) -> dict | None:
        for n in self.notes:
            if n["id"] == note_id:
                return n
        return None

    def get_notes_by_category(self, category: str) -> list[dict]:
        return [n for n in self.notes if n["category"] == category]

    def restore_history(self, note_id: str, history_index: int) -> dict | None:
        note = self.get_note(note_id)
        if note is None or history_index >= len(note["history"]):
            return None
        entry = note["history"][history_index]
        note["body"] = entry["body"]
        note["title"] = entry["title"]
        note["updated_at"] = self._now()
        return note

    # ───────────────────────── カテゴリ ─────────────────────
    def add_category(self, name: str) -> bool:
        if name and name not in self.categories:
            self.categories.append(name)
            return True
        return False

    def delete_category(self, name: str) -> bool:
        if name == "未分類" or name not in self.categories:
            return False
        for n in self.notes:
            if n["category"] == name:
                n["category"] = "未分類"
        self.categories.remove(name)
        return True

    def rename_category(self, old_name: str, new_name: str) -> bool:
        if old_name == "未分類" or old_name not in self.categories:
            return False
        if not new_name or new_name in self.categories:
            return False
        idx = self.categories.index(old_name)
        self.categories[idx] = new_name
        for n in self.notes:
            if n["category"] == old_name:
                n["category"] = new_name
        return True

    # ───────────────────────── 添付ファイル ─────────────────
    def add_attachment(self, note_id: str, filename: str) -> bool:
        note = self.get_note(note_id)
        if note is None:
            return False
        if filename not in note["attachments"]:
            note["attachments"].append(filename)
        return True

    def remove_attachment(self, note_id: str, filename: str) -> bool:
        note = self.get_note(note_id)
        if note is None:
            return False
        if filename in note["attachments"]:
            note["attachments"].remove(filename)
            return True
        return False

    # ───────────────────────── 全文検索 ─────────────────────
    def search(self, query: str) -> list[dict]:
        q = query.lower()
        results = []
        for n in self.notes:
            if q in n["title"].lower() or q in n["body"].lower():
                results.append(n)
        return results

    # ───────────────────────── ユーティリティ ───────────────
    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y/%m/%d %H:%M:%S")
