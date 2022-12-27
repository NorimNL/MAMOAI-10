# *- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from source.check_clone import check_clone

APP_NAME = "Knowledge Base Constructor"


def main():
    argv = sys.argv.copy()
    argv.append(APP_NAME)
    argv.append("--platform")
    argv.append("windows:dpiawareness=0")

    application = QApplication(argv)
    application.setWindowIcon(QIcon(":/icons/app.png"))
    application.setApplicationName(APP_NAME)
    exit_code = check_clone()
    if exit_code == 0:
        from source.widgets import AppMainWindow
        main_window = AppMainWindow()
        main_window.show()
        exit_code = application.exec()
    else:
        from source.message import CriticalMessage
        CriticalMessage('Ошибка запуска', 'Приложение уже запущено!')
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
