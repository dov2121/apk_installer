import sys
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QProgressBar, QComboBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class APKInstaller(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("APK Installer")
        self.setGeometry(400, 200, 500, 300)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")

        layout = QVBoxLayout()

        self.label = QLabel("Select an APK and device")
        self.label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.label)

        # APK Selector
        self.btn_select = QPushButton("Browse APK")
        self.btn_select.setStyleSheet(self.button_style("#0078d7", "#005a9e"))
        self.btn_select.clicked.connect(self.select_apk)
        layout.addWidget(self.btn_select)

        # APK Info Label
        self.apk_info_label = QLabel("APK Info: Not detected")
        layout.addWidget(self.apk_info_label)

        # Device Selector
        self.device_selector = QComboBox()
        self.refresh_devices()
        layout.addWidget(self.device_selector)

        self.btn_refresh_devices = QPushButton("Refresh Devices")
        self.btn_refresh_devices.setStyleSheet(self.button_style("#6c757d", "#5a6268"))
        self.btn_refresh_devices.clicked.connect(self.refresh_devices)
        layout.addWidget(self.btn_refresh_devices)

        # Install Button
        self.btn_install = QPushButton("Install APK")
        self.btn_install.setStyleSheet(self.button_style("#28a745", "#1e7e34"))
        self.btn_install.clicked.connect(self.install_apk)
        layout.addWidget(self.btn_install)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.setStyleSheet("QProgressBar { text-align: center; }")
        layout.addWidget(self.progress)

        self.setLayout(layout)
        self.apk_path = None

    def button_style(self, color, hover):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """

    def select_apk(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select APK", "", "APK Files (*.apk)")
        if file:
            self.apk_path = file
            self.label.setText(f"Selected: {file}")
            self.detect_apk_info(file)

    def detect_apk_info(self, apk_path):
        try:
            result = subprocess.run(["aapt", "dump", "badging", apk_path],
                                    capture_output=True, text=True, check=True)
            output = result.stdout

            package = self.extract_field(output, "package: name='", "'")
            version = self.extract_field(output, "versionName='", "'")
            sdk = self.extract_field(output, "sdkVersion:'", "'")
            target_sdk = self.extract_field(output, "targetSdkVersion:'", "'")

            info = f"Package: {package}\nVersion: {version}\nMin SDK: {sdk}\nTarget SDK: {target_sdk}"
            self.apk_info_label.setText(info)
        except Exception as e:
            self.apk_info_label.setText(f"Error reading APK: {e}")

    def extract_field(self, text, start, end):
        try:
            s = text.index(start) + len(start)
            e = text.index(end, s)
            return text[s:e]
        except ValueError:
            return "Unknown"

    def refresh_devices(self):
        self.device_selector.clear()
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            lines = result.stdout.strip().split("\n")[1:]
            devices = [line.split()[0] for line in lines if "device" in line]
            if devices:
                self.device_selector.addItems(devices)
            else:
                self.device_selector.addItem("No devices found")
        except Exception:
            self.device_selector.addItem("ADB not found")

    def install_apk(self):
        if not self.apk_path:
            self.label.setText("⚠️ No APK selected.")
            return
        device = self.device_selector.currentText()
        if "No devices" in device or "ADB not found" in device:
            self.label.setText("⚠️ No valid device selected.")
            return

        self.progress.setValue(50)
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #ffc107; }")

        try:
            subprocess.run(["adb", "-s", device, "install", "-r", self.apk_path], check=True)
            self.progress.setValue(100)
            self.progress.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")
            self.label.setText("✅ APK installed successfully!")
        except subprocess.CalledProcessError:
            self.progress.setValue(100)
            self.progress.setStyleSheet("QProgressBar::chunk { background-color: #dc3545; }")
            self.label.setText("❌ Installation failed. Check adb connection.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = APKInstaller()
    window.show()
    sys.exit(app.exec_())

