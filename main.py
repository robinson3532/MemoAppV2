import sys
import os

# パッケージ解決のためsys.pathを設定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MemoApp")
    app.setOrganizationName("MemoApp")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
