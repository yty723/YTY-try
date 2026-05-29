import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QPushButton, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import win32gui
import win32con
import win32api
import atexit

# 全局恢复：根据关键词恢复窗口显示 + 取消置顶
def restore_window_by_keyword(keyword):
    try:
        hwnd_list = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if keyword in title:
                    hwnd_list.append(hwnd)
            return True
        win32gui.EnumWindows(callback, None)
        for hwnd in hwnd_list:
            # 恢复显示
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
            # 取消置顶
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    except:
        pass

class InvisibleTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.target_hwnd = None
        self.last_alpha = 255
        self.current_keyword = ""

        # 定时检测
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_mouse_state)
        self.timer.setInterval(80)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("窗口隐身工具（带置顶版）")
        self.setFixedSize(420, 320)
        self.setStyleSheet("background-color: #f7f9fa;")

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 24, 30, 24)

        # 标题
        title_label = QLabel("窗口隐身监控 + 强制置顶")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 输入提示
        tip_label = QLabel("输入窗口标题关键词：")
        tip_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(tip_label)

        # 输入框
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("例如：Koodo、Chrome、Edge、知乎")
        self.key_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.key_input)

        # 按钮行：启动 + 重置
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # 启动按钮
        self.start_btn = QPushButton("启动监控 + 置顶")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d8cf0;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #57a3f3;
            }
        """)
        self.start_btn.clicked.connect(self.start_monitor)

        # 重置按钮
        self.reset_btn = QPushButton("重置/停止")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #909399;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #a8a9ad;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_monitor)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        # 状态显示
        self.status_label = QLabel("状态：等待启动")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.status_label)

        # 退出按钮
        self.exit_btn = QPushButton("退出程序")
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f56c6c;
                color: white;
                padding: 9px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f78585;
            }
        """)
        self.exit_btn.clicked.connect(self.close)
        layout.addWidget(self.exit_btn)

    # 启动监控 + 置顶
    def start_monitor(self):
        text = self.key_input.text().strip()
        if not text:
            self.status_label.setText("请输入有效关键词")
            return

        self.current_keyword = text
        self.status_label.setText(f"正在监控：{text}（已置顶）")
        self.timer.start()

    # 重置功能（停止监控 + 恢复窗口 + 取消置顶）
    def reset_monitor(self):
        self.timer.stop()
        restore_window_by_keyword(self.current_keyword)
        self.status_label.setText("状态：已停止，窗口已恢复")

    # 查找目标窗口
    def find_target_window(self):
        hwnd_list = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.current_keyword in title:
                    hwnd_list.append(hwnd)
            return True
        win32gui.EnumWindows(callback, None)
        return hwnd_list[0] if hwnd_list else None

    # 开启窗口透明属性
    def enable_layered(self, hwnd):
        try:
            ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex | win32con.WS_EX_LAYERED)
        except:
            pass

    # 设置窗口置顶（新增）
    def set_topmost(self, hwnd, top: bool):
        try:
            if top:
                # 置顶
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            else:
                # 取消置顶
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass

    # 设置透明度
    def set_alpha(self, hwnd, alpha):
        try:
            win32gui.SetLayeredWindowAttributes(hwnd, 0, alpha, win32con.LWA_ALPHA)
            self.last_alpha = alpha
        except:
            pass

    # 判断鼠标是否在窗口内
    def is_mouse_in(self, hwnd):
        try:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
            x, y = win32api.GetCursorPos()
            return l <= x <= r and t <= y <= b
        except:
            return False

    # 检测鼠标并控制显隐 + 保持置顶
    def check_mouse_state(self):
        if not self.current_keyword:
            return

        hwnd = self.find_target_window()
        if not hwnd:
            self.status_label.setText(f"未找到窗口：{self.current_keyword}")
            return

        # 开启透明
        self.enable_layered(hwnd)
        # 强制保持置顶（核心）
        self.set_topmost(hwnd, True)

        mouse_in = self.is_mouse_in(hwnd)

        if mouse_in:
            self.set_alpha(hwnd, 255)
            self.status_label.setText(f"✅ {self.current_keyword} → 显示中（置顶）")
        else:
            self.set_alpha(hwnd, 0)
            self.status_label.setText(f"🔒 {self.current_keyword} → 已隐身（置顶）")

    # 关闭窗口时恢复
    def closeEvent(self, event):
        self.timer.stop()
        restore_window_by_keyword(self.current_keyword)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = InvisibleTool()

    # 异常退出时也恢复
    def on_exit():
        restore_window_by_keyword(tool.current_keyword)

    atexit.register(on_exit)

    tool.show()
    sys.exit(app.exec_())