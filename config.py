import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "save_dir": str(Path.home() / "MemoApp"),
    "notes_json_path": "",
    "max_history_versions": 10,
    "max_backup_generations": 5,
    "word_wrap": True,
    "font_family": "Consolas",
    "font_size": 12,
}

CONFIG_PATH = Path.home() / ".memo_app_config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # デフォルト値で不足キーを補完
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Config] 保存エラー: {e}")


def ensure_dirs(config: dict) -> None:
    """必要なディレクトリとファイルを作成"""
    import json
    save_dir = Path(config["save_dir"])
    (save_dir / "attachments").mkdir(parents=True, exist_ok=True)
    (save_dir / "backups").mkdir(parents=True, exist_ok=True)

    # notes.jsonが存在しない場合は自動生成
    notes_path = Path(config.get("notes_json_path", "") or save_dir / "notes.json")
    if not notes_path.exists():
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        with open(notes_path, "w", encoding="utf-8") as f:
            json.dump({"categories": ["未分類"], "notes": []}, f, ensure_ascii=False, indent=2)
