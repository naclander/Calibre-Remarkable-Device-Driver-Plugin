from calibre.utils.config import JSONConfig
from PyQt5.Qt import QWidget, QLabel, QLineEdit, QGridLayout

prefs = JSONConfig("plugins/remarkable_device_plugin")

# Set defaults
prefs.defaults["ip"] = "10.11.99.1"
prefs.defaults["books_path"] = "/"
prefs.defaults["metadata_path"] = "/home/root/"
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

        self.books_path_label = QLabel("Books Path:")
        self.layout.addWidget(self.books_path_label, 2, 0)
        self.books_path_label_msg = QLineEdit(self)
        self.books_path_label_msg.setText(prefs["books_path"])
        self.layout.addWidget(self.books_path_label_msg, 2, 1)
        self.books_path_label.setBuddy(self.books_path_label_msg)

        self.metadata_path_label = QLabel("Config Path:")
        self.layout.addWidget(self.metadata_path_label, 3, 0)
        self.metadata_path_label_msg = QLineEdit(self)
        self.metadata_path_label_msg.setText(prefs["metadata_path"])
        self.layout.addWidget(self.metadata_path_label_msg, 3, 1)
        self.metadata_path_label.setBuddy(self.metadata_path_label_msg)

        self.password_label = QLabel("Password ( If not using Key ):")
        self.layout.addWidget(self.password_label, 4, 0)
        self.password_label_msg = QLineEdit(self)
        self.password_label_msg.setText(prefs["password"])
        self.layout.addWidget(self.password_label_msg, 4, 1)
        self.password_label.setBuddy(self.password_label_msg)

        self.setLayout(self.layout)
        self.setGeometry(150, 150, 150, 150)
        self.setWindowTitle("Remarkable Config")

    def save_settings(self):
        prefs["ip"] = self.ip_label_msg.text()
        # append an extra '/' in case it was forgotten
        prefs["books_path"] = self.books_path_label_msg.text() + "/"
        prefs["metadata_path"] = self.metadata_path_label_msg.text() + "/"
        prefs["password"] = self.password_label_msg.text()
