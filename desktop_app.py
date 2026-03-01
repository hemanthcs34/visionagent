import sys
import ctypes
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Constants for Windows SetWindowDisplayAffinity
# WDA_NONE = 0x00000000
# WDA_MONITOR = 0x00000001 (Black box in screen capture)
# WDA_EXCLUDEFROMCAPTURE = 0x00000011 (Completely invisible in screen capture on Win 10 2004+)
WDA_EXCLUDEFROMCAPTURE = 0x00000011

class StayOnTopApp(QMainWindow):
    def __init__(self, url="http://localhost:5173"):
        super().__init__()

        self.setWindowTitle("CogniSync Agent - Screen Share Invincible")
        self.setGeometry(100, 100, 400, 700) # Small side panel size by default

        # Set window flags: stay on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Create web engine view
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(url))

        # Setup central widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) # Remove margins
        layout.addWidget(self.browser)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def showEvent(self, event):
        super().showEvent(event)
        self.make_window_invincible()

    def make_window_invincible(self):
        """
        Uses Windows API to exclude this window from screen capture.
        """
        if sys.platform == 'win32':
            try:
                # Get the window handle (HWND)
                hwnd = int(self.winId())
                
                # Call SetWindowDisplayAffinity
                # WDA_EXCLUDEFROMCAPTURE (0x11) ensures it's completely excluded from capture.
                user32 = ctypes.windll.user32
                result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
                
                if result == 0:
                    print(f"Failed to set window display affinity. Error code: {ctypes.GetLastError()}")
                else:
                    print("Successfully made the window invincible to screen capture!")
            except Exception as e:
                print(f"Error applying screen capture protection: {e}")
        else:
            print("Screen capture protection is only supported on Windows.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # URL to your frontend - modify if your Vite server runs on a different port
    frontend_url = "http://localhost:5173"
    
    window = StayOnTopApp(frontend_url)
    window.show()
    
    print(f"Starting desktop wrapper for {frontend_url}...")
    print("This window is set to stay on top and is excluded from screen sharing software (like OBS/Teams/Zoom).")
    
    sys.exit(app.exec())
