from PyQt5.QtCore import QTimer


class AlarmpiPlugin:

    def __init__(self, parent):
        self.retry_flag = False
        self.parent = parent

    def run_with_retry(self, func, delay_sec=10):
        """Run func with single retry after a delay."""
        func()
        if self.retry_flag:
            self.retry_flag = False
            timer = QTimer(self.parent.main_window)
            timer.setSingleShot(True)
            timer.timeout.connect(func)
            timer.start(delay_sec*1000)