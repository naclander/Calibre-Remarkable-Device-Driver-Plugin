from calibre.utils.config import JSONConfig
from PyQt5.Qt import QWidget, QLabel, QLineEdit, QGridLayout

prefs = JSONConfig("plugins/remarkable_device_plugin")

# Set defaults
prefs.defaults["ip"] = "10.11.99.1"
prefs.defaults["password"] = ""


class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.layout = QGridLayout()
        self.layout.setSpacing(10)

        self.ip_label = QLabel("Remarkable IP:")

        self.layout.addWidget(self.ip_label, 1, 0)

        self.ip_label_msg = QLineEdit(self)
        self.ip_label_msg.setText(prefs["ip"])
        self.layout.addWidget(self.ip_label_msg, 1, 1)
        self.ip_label.setBuddy(self.ip_label_msg)

        self.password_label = QLabel("Password ( If not using Key ):")
        self.layout.addWidget(self.password_label, 2, 0)

        self.password_label_msg = QLineEdit(self)
        self.password_label_msg.setText(prefs["password"])
        self.layout.addWidget(self.password_label_msg, 2, 1)
        self.password_label.setBuddy(self.password_label_msg)

        self.setLayout(self.layout)
        self.setGeometry(150, 150, 150, 150)
        self.setWindowTitle("Remarkable Config")

    def save_settings(self):
        prefs["ip"] = self.ip_label_msg.text()
        prefs["password"] = self.password_label_msg.text()
