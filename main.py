import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QIcon
from planner.main_window import MainWindow


def resource_path(relative_path):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path


def apply_dark_theme(app):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(27, 42, 31))
    palette.setColor(QPalette.WindowText, QColor(238, 242, 225))
    palette.setColor(QPalette.Base, QColor(19, 31, 23))
    palette.setColor(QPalette.Text, QColor(238, 242, 225))
    palette.setColor(QPalette.Button, QColor(53, 84, 48))
    palette.setColor(QPalette.ButtonText, QColor(248, 250, 239))
    palette.setColor(QPalette.Highlight, QColor(111, 156, 70))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #1b2a1f;
            color: #eef2e1;
            selection-background-color: #6f9c46;
        }
        QTabWidget::pane {
            border: 1px solid #49613f;
            border-radius: 6px;
            background: #1f3325;
        }
        QTabBar::tab {
            padding: 8px 14px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            background: #263b2a;
            color: #d9e5c3;
            font-weight: 600;
        }
        QTabBar::tab:selected {
            background: #3f6f32;
            color: white;
        }
        QPushButton {
            padding: 9px 12px;
            border-radius: 6px;
            background-color: #4f8a38;
            color: white;
            font-weight: bold;
            border: 1px solid #83ad5e;
        }
        QPushButton:hover { background-color: #609e45; }
        QPushButton:pressed { background-color: #3d702b; }
        QPushButton:disabled {
            background-color: #445043;
            color: #a6b49a;
            border-color: #596454;
        }
        QSpinBox, QComboBox, QLineEdit {
            padding: 6px;
            border-radius: 4px;
            background-color: #142218;
            color: #f3f7e8;
            border: 1px solid #5e714d;
        }
        QSpinBox:focus, QComboBox:focus, QLineEdit:focus {
            border: 1px solid #b9d77a;
        }
        QListWidget {
            background-color: #142218;
            border: 1px solid #5e714d;
            border-radius: 6px;
            alternate-background-color: #1c2f20;
        }
        QListWidget::item {
            padding: 6px;
        }
        QListWidget::item:selected {
            background: #4f8a38;
            color: white;
        }
        QTextEdit {
            background-color: #101a13;
            border: 1px solid #516343;
            border-radius: 6px;
            font-family: Consolas, monospace;
            color: #eaf1d9;
        }
        QLabel {
            color: #eef2e1;
        }
        QLabel#BigNumber {
            font-size: 44px;
            font-weight: bold;
            color: #a7e05f;
        }
        QScrollBar:vertical {
            background: #152419;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background: #557447;
            border-radius: 5px;
            min-height: 20px;
        }
    """)

def main():
    app = QApplication(sys.argv)
    icon = QIcon(str(resource_path("assets/app_icon.ico")))
    app.setWindowIcon(icon)
    apply_dark_theme(app)
    win = MainWindow()
    win.setWindowIcon(icon)
    win.resize(1400, 880)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
