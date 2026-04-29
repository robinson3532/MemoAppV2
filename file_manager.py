import os
import shutil
from pathlib import Path


class FileManager:
    def __init__(self, config: dict):
        self.config = config

    def _attachments_dir(self) -> Path:
        return Path(self.config["save_dir"]) / "attachments"

    def copy_attachment(self, src_path: str) -> str | None:
        """添付ファイルをattachmentsディレクトリへコピーし、ファイル名を返す"""
        src = Path(src_path)
        if not src.exists():
            return None
        dest_dir = self._attachments_dir()
        dest_dir.mkdir(parents=True, exist_ok=True)

        # 同名ファイルが存在する場合はリネーム
        dest = dest_dir / src.name
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{src.stem}_{counter}{src.suffix}"
            counter += 1

        shutil.copy2(src, dest)
        return dest.name

    def delete_attachment(self, filename: str) -> bool:
        path = self._attachments_dir() / filename
        if path.exists():
            path.unlink()
            return True
        return False

    def get_attachment_path(self, filename: str) -> Path:
        return self._attachments_dir() / filename

    def open_attachment(self, filename: str) -> bool:
        path = self.get_attachment_path(filename)
        if not path.exists():
            return False
        import subprocess, sys
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.call(["open", str(path)])
        else:
            subprocess.call(["xdg-open", str(path)])
        return True
