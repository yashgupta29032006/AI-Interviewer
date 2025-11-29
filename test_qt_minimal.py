import sys
from PyQt6.QtWidgets import QApplication, QLabel

app = QApplication(sys.argv)
label = QLabel("Hello World")
label.show()
print("PyQt6 initialized successfully")
sys.exit(app.exec())
