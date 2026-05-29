import sys
import ctypes
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer, Qt
import win32gui
import win32con
import win32api

# ================= 精准配置 =================
# 匹配Koodo Reader窗口标题（包含关键词即可）
TARGET_TITLE_KEYWORD = "Koodo Reader"
# ============================================

HIDE_ALPHA = 0
SHOW_ALPHA = 255
CHECK_INTERVAL = 80

# ================= 全局退出保护（核心） =================
def restore_koodo_on_exit():
    try:
        hwnd_list = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if TARGET_TITLE_KEYWORD in title:
                    hwnd_list.append(hwnd)
            return True
        win32gui.EnumWindows(callback, None)
        for hwnd in hwnd_list:
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
    except:
        pass

# 注册：程序退出时自动执行
import atexit
atexit.register(restore_koodo_on_exit)

# ========================================================

class KoodoInvisibleTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.target_hwnd = None
        self.last_alpha = SHOW_ALPHA
        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_mouse_state)
        self.timer.start(CHECK_INTERVAL)

    def init_ui(self):
        self.setWindowTitle("Koodo 隐身工具（防卡死版）")
        self.setFixedSize(380, 220)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("正在等待 Koodo Reader 窗口...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; padding: 8px;")
        layout.addWidget(self.status_label)

        self.refresh_btn = QPushButton("重新绑定 Koodo 窗口")
        self.refresh_btn.clicked.connect(self.refresh_window)
        layout.addWidget(self.refresh_btn)

        self.exit_btn = QPushButton("退出（自动恢复显示）")
        self.exit_btn.setStyleSheet("background: #d9534f; color: white; padding: 8px;")
        self.exit_btn.clicked.connect(self.close)
        layout.addWidget(self.exit_btn)

    def refresh_window(self):
        self.target_hwnd = self.find_koodo_window()
        if self.target_hwnd:
            self.status_label.setText(f"✅ 已绑定 Koodo Reader\n窗口句柄：{self.target_hwnd}")
            self.enable_layered()
            self.set_alpha(SHOW_ALPHA)
        else:
            self.status_label.setText("❌ 未找到 Koodo Reader\n请先打开阅读器再点击刷新")

    def find_koodo_window(self):
        hwnd_list = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if TARGET_TITLE_KEYWORD in title:
                    hwnd_list.append(hwnd)
            return True
        win32gui.EnumWindows(callback, None)
        return hwnd_list[0] if hwnd_list else None

    def enable_layered(self):
        try:
            ex_style = win32gui.GetWindowLong(self.target_hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(self.target_hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED)
        except:
            pass

    def set_alpha(self, alpha):
        try:
            win32gui.SetLayeredWindowAttributes(self.target_hwnd, 0, alpha, win32con.LWA_ALPHA)
            self.last_alpha = alpha
        except:
            pass

    def is_mouse_in_koodo(self):
        if not self.target_hwnd or not win32gui.IsWindow(self.target_hwnd):
            return False
        try:
            left, top, right, bottom = win32gui.GetWindowRect(self.target_hwnd)
            mouse_x, mouse_y = win32api.GetCursorPos()
            return left <= mouse_x <= right and top <= mouse_y <= bottom
        except:
            return False

    def check_mouse_state(self):
        if not self.target_hwnd or not win32gui.IsWindow(self.target_hwnd):
            self.target_hwnd = self.find_koodo_window()
            if not self.target_hwnd:
                self.status_label.setText("⏳ 正在等待 Koodo Reader 窗口...")
                return

        mouse_in = self.is_mouse_in_koodo()

        if mouse_in:
            if self.last_alpha != SHOW_ALPHA:
                self.set_alpha(SHOW_ALPHA)
                self.status_label.setText("🟢 Koodo：显示中")
        else:
            if self.last_alpha != HIDE_ALPHA:
                self.set_alpha(HIDE_ALPHA)
                self.status_label.setText("🔴 Koodo：已隐身")

    def closeEvent(self, event):
        restore_koodo_on_exit()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = KoodoInvisibleTool()
    tool.show()
    sys.exit(app.exec_())