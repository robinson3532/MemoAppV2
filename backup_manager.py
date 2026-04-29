import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


class BackupManager:
    def __init__(self, config: dict):
        self.config = config

    def _save_dir(self) -> Path:
        return Path(self.config["save_dir"])

    def _backups_dir(self) -> Path:
        return self._save_dir() / "backups"

    def _notes_path(self) -> Path:
        p = self.config.get("notes_json_path", "")
        if p:
            return Path(p)
        return self._save_dir() / "notes.json"

    def _attachments_dir(self) -> Path:
        return self._save_dir() / "attachments"

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    # ─────────────────── 自動世代バックアップ ───────────────────
    def create_auto_backup(self) -> Path | None:
        backups_dir = self._backups_dir()
        backups_dir.mkdir(parents=True, exist_ok=True)

        ts = self._timestamp()
        backup_path = backups_dir / f"backup_{ts}"
        backup_path.mkdir(exist_ok=True)

        # notes.jsonをコピー
        notes_src = self._notes_path()
        if notes_src.exists():
            shutil.copy2(notes_src, backup_path / "notes.json")

        # attachmentsをコピー
        att_src = self._attachments_dir()
        if att_src.exists():
            shutil.copytree(att_src, backup_path / "attachments", dirs_exist_ok=True)

        # 世代数を超えた古いバックアップを削除
        self._prune_backups()
        return backup_path

    def _prune_backups(self) -> None:
        max_gen = self.config.get("max_backup_generations", 5)
        backups_dir = self._backups_dir()
        backups = sorted(
            [d for d in backups_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")]
        )
        while len(backups) > max_gen:
            shutil.rmtree(backups.pop(0))

    # ─────────────────── 手動zipエクスポート ───────────────────
    def export_zip(self, dest_path: str) -> bool:
        try:
            with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
                notes_src = self._notes_path()
                if notes_src.exists():
                    zf.write(notes_src, "notes.json")
                att_src = self._attachments_dir()
                if att_src.exists():
                    for f in att_src.rglob("*"):
                        if f.is_file():
                            zf.write(f, str(Path("attachments") / f.relative_to(att_src)))
            return True
        except Exception as e:
            print(f"[Backup] zipエクスポートエラー: {e}")
            return False

    # ─────────────────── バックアップ一覧 ───────────────────────
    def list_backups(self) -> list[dict]:
        backups_dir = self._backups_dir()
        if not backups_dir.exists():
            return []
        result = []
        for d in sorted(backups_dir.iterdir(), reverse=True):
            if d.is_dir() and d.name.startswith("backup_"):
                ts_str = d.name.replace("backup_", "")
                try:
                    dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    label = dt.strftime("%Y/%m/%d %H:%M:%S")
                except Exception:
                    label = ts_str
                result.append({"label": label, "path": str(d)})
        return result

    # ─────────────────── バックアップ復元 ───────────────────────
    def restore_backup(self, backup_path: str) -> bool:
        src = Path(backup_path)
        if not src.exists():
            return False
        try:
            # notes.jsonを復元
            notes_src = src / "notes.json"
            if notes_src.exists():
                dest = self._notes_path()
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(notes_src, dest)

            # attachmentsを復元
            att_src = src / "attachments"
            att_dest = self._attachments_dir()
            if att_src.exists():
                if att_dest.exists():
                    shutil.rmtree(att_dest)
                shutil.copytree(att_src, att_dest)
            return True
        except Exception as e:
            print(f"[Backup] 復元エラー: {e}")
            return False
