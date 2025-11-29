import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Optional: Load custom fonts or global styles here
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
