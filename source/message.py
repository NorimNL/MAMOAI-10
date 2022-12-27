# *- coding: utf-8 -*-

from PyQt5.QtWidgets import QMessageBox, QWidget, QCommonStyle

MESSAGE_STYLE = """
                QWidget
                {
                    background-color: rgb(236, 236, 236);
                }
                QPushButton
                {
                    padding: 2px 0px 2px 0px;
                    background-color: rgb(180, 180, 180);
                    border: 2px solid rgb(180, 180, 180);
                    border-radius: 4px;
                }
                QPushButton:hover
                {
                    padding: 3px 0px 1px 0px;
                    background-color: rgb(161, 161, 161);
                    border-color: rgb(161, 161, 161);
                }
                QPushButton:pressed
                {
                    padding: 4px 0px 0px 0px;
                    background-color: rgb(123, 123, 124);
                    border: 4px solid transparent;
                    border-radius: 6px;
                }
                QPushButton
                {
                    height: 20px; min-width: 80px;
                }
                """


class StandardMessage(QMessageBox):
    def __init__(self, title: str, text: str, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setStyleSheet(MESSAGE_STYLE)
        self.setWindowTitle(title)
        self.setText(text)


class QuestionMessage(StandardMessage):
    def __init__(self, title: str = 'Вопрос?', text: str = 'Вопрос?', parent: QWidget = None):
        super().__init__(title, text, parent)
        self.setIcon(QMessageBox.Icon.Question)
        self.addButton('Да', QMessageBox.AcceptRole)
        self.addButton('Отмена', QMessageBox.RejectRole)


class InfoMessage(StandardMessage):
    def __init__(self, title: str = 'Внимание', text: str = '!!!', parent: QWidget = None):
        super().__init__(title, text, parent)
        self.setIconPixmap(self.style().standardPixmap(QCommonStyle.SP_MessageBoxInformation))
        self.addButton('ОК', QMessageBox.AcceptRole)
        self.exec()


class CriticalMessage(StandardMessage):
    def __init__(self, title: str = 'Критическая ошибка', text: str = 'Ошибка!', parent: QWidget = None):
        super().__init__(title, text, parent)
        self.setIcon(QMessageBox.Icon.Critical)
        self.addButton('ОК', QMessageBox.AcceptRole)
        self.exec()
