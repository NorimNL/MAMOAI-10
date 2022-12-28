# *- coding: utf-8 -*-
from pathlib import Path
from typing import Optional, List

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QPushButton, \
    QLineEdit, QSizePolicy, QFileDialog, QTabWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QAction, QDialog

from source.message import InfoMessage, QuestionMessage
from source.model import AppModel, KnowledgeBase, Sign, Hypothesis, CalculationProcess


class AppMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_model = AppModel()
        self.setup_ui()
        self.setup_actions()
        self.setup_signals()
        self.update_file_list()

    def update_file_list(self):
        self.file_list.clear()
        self.file_list.addItems([f.name.split('.')[0] for f in self.app_model.get_file_list()])

    def open_file(self):
        suffix = AppModel.Files.SUFFIX
        dialog = QFileDialog(self, 'Открыть базу знаний')
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setDefaultSuffix(suffix)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setNameFilter('Knowledge Base (*' + suffix + ')')
        if dialog.exec_():
            files = [Path(f).resolve() for f in dialog.selectedFiles()]
            self.app_model.add_manual_paths(files)
            self.update_file_list()

    def open_tab(self, item: QListWidgetItem):
        name = item.text()
        for i in range(self.kb_tabs.count()):
            if self.kb_tabs.tabText(i) == name:
                self.kb_tabs.setCurrentIndex(i)
                return
        tab_widget = KnowledgeBaseWidget(self.app_model, name, self)
        self.kb_tabs.addTab(tab_widget, name)
        self.kb_tabs.setCurrentIndex(self.kb_tabs.count() - 1)
        tab_widget.name_input.textEdited.connect(lambda name: self.app_model.rename_base(tab_widget.kb, name))
        tab_widget.name_input.textEdited.connect(
            lambda name: self.kb_tabs.setTabText(self.kb_tabs.indexOf(tab_widget), name))
        tab_widget.name_input.textEdited.connect(self.update_file_list)

    def create_base(self):
        self.app_model.add_base()
        self.update_file_list()

    def setup_actions(self):
        self.update_action = QAction(self)
        self.update_action.setShortcut('Ctrl+R')
        self.addAction(self.update_action)

    def setup_signals(self):
        self.update_files_button.clicked.connect(self.update_file_list)
        self.add_file_button.clicked.connect(self.open_file)
        self.file_list.itemDoubleClicked.connect(self.open_tab)
        self.create_base_button.clicked.connect(self.create_base)
        self.update_action.triggered.connect(self.update_file_list)
        self.kb_tabs.tabBarDoubleClicked.connect(self.kb_tabs.removeTab)
        self.kb_tabs.tabBarDoubleClicked.connect(lambda index: self.app_model.bases.remove(self.app_model.bases[index]))

    def setup_ui(self):
        self.central_widget = cw = QWidget(self)
        self.h_layout = QHBoxLayout(cw)

        # кнопки добавления и обновления списка файлов
        self.add_file_button = QPushButton(QIcon(":/icons/folder.png"), '', cw)
        self.create_base_button = QPushButton(QIcon(":/icons/add.png"), '', cw)
        self.update_files_button = QPushButton(QIcon(":/icons/update.png"), '', cw)
        self.file_buttons_layout = QHBoxLayout(cw)
        self.file_buttons_layout.addWidget(self.add_file_button)
        self.file_buttons_layout.addWidget(self.create_base_button)
        self.file_buttons_layout.addWidget(self.update_files_button)

        # отображение списка файлов
        self.file_list = QListWidget(cw)
        self.file_list.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.v_layout = QVBoxLayout(cw)
        self.v_layout.addLayout(self.file_buttons_layout)
        self.v_layout.addWidget(self.file_list)
        self.h_layout.addLayout(self.v_layout)

        # вкладки с открытыми базами знаний
        self.kb_tabs = QTabWidget(cw)
        self.h_layout.addWidget(self.kb_tabs)

        self.setCentralWidget(cw)
        self.resize(800, 600)


class SignValueTable(QTableWidget):
    remove_sign_value = pyqtSignal(int, int)  # h_id, sign_id
    change_sign_value = pyqtSignal(int, int, str, str)  # h_id, sign_id, p_pos, p_neg

    def __init__(self, parent):
        super().__init__(parent)
        self.h: Optional[Hypothesis] = None
        self.fill_flag = False
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['sign_id', 'Признак', 'p+', 'p-'])
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setColumnHidden(0, True)
        self.resizeColumnToContents(2)
        self.resizeColumnToContents(3)

        self.delete_link_action = QAction("Удалить связь", self)
        self.delete_link_action.setShortcut('Ctrl+D')
        self.addAction(self.delete_link_action)

        self.delete_link_action.triggered.connect(self.confirm_delete)
        self.cellChanged.connect(self.emit_change)

    def emit_change(self, row, col):
        if not self.fill_flag and self.h:
            h_id = self.h.id
            sign_id = int(self.item(row, 0).text())
            p_pos = self.item(row, 2).text()
            p_neg = self.item(row, 3).text()
            self.change_sign_value.emit(h_id, sign_id, p_pos, p_neg)

    def confirm_delete(self):
        if self.hasFocus() and self.h and len(self.h.signs):
            row = self.currentRow()
            h_id = self.h.id
            sign_id = int(self.item(row, 0).text())
            name = self.item(row, 1).text()
            p_pos = self.item(row, 2).text()
            p_neg = self.item(row, 3).text()
            message = QuestionMessage('Удалить', f'Удалить связь <{name}> <{p_pos}> <{p_neg}>?')
            if message.exec_() == message.AcceptRole:
                self.removeRow(row)
                self.remove_sign_value.emit(h_id, sign_id)

    def fill(self, kb: KnowledgeBase, h: Hypothesis):
        self.fill_flag = True
        self.h = h
        self.clearContents()
        self.setRowCount(len(h.signs))
        for i, (s, sv) in enumerate(kb.get_links(h)):
            self.setItem(i, 0, QTableWidgetItem(str(sv.sign_id)))
            self.setItem(i, 1, QTableWidgetItem(s.name))
            self.item(i, 1).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.setItem(i, 2, QTableWidgetItem(str(sv.p_pos)))
            self.setItem(i, 3, QTableWidgetItem(str(sv.p_neg)))
        self.fill_flag = False


class LinkHypothesisDialog(QDialog):
    def __init__(self, kb: KnowledgeBase):
        super().__init__()
        self.setWindowFlags(Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.kb: KnowledgeBase = kb
        self.h: Optional[Hypothesis] = None
        self.in_signs: List[Sign] = list()
        self.out_signs: List[Sign] = list()
        self.setup_ui()
        self.fill_hypos_list()
        self.setup_signals()

    def new_include_sign(self, item):
        if self.h:
            s = self.out_signs[self.unincluded_signs_list.indexFromItem(item).row()]
            self.h.add_sign(s)
            self.fill_signs(self.h)

    def fill_hypos_list(self):
        self.hypos_list.clear()
        self.hypos_list.addItems([h.name for h in self.kb.hypos])

    def fill_signs(self, h: Hypothesis):
        self.h = h
        self.in_signs = self.kb.get_signs_in_hypothesis(self.h)
        self.out_signs = self.kb.get_signs_out_hypothesis(self.h)

        self.unincluded_signs_list.clear()
        self.unincluded_signs_list.addItems([s.name for s in self.out_signs])

        self.included_signs_table.fill(self.kb, self.h)

    def setup_signals(self):
        self.hypos_list.itemClicked.connect(
            lambda item: self.fill_signs(self.kb.hypos[self.hypos_list.indexFromItem(item).row()]))
        self.unincluded_signs_list.itemDoubleClicked.connect(self.new_include_sign)
        self.included_signs_table.change_sign_value.connect(self.kb.change_link)
        self.included_signs_table.change_sign_value.connect(lambda: self.fill_signs(self.h))
        self.included_signs_table.remove_sign_value.connect(self.kb.delete_link)
        self.included_signs_table.remove_sign_value.connect(lambda: self.fill_signs(self.h))

    def setup_ui(self):
        self.overview_layout = QHBoxLayout(self)
        # 1
        self.include_label = QLabel('Гипотезы')
        self.hypos_list = QListWidget(self)
        self.hypos_layout = QVBoxLayout(self)
        self.hypos_layout.addWidget(self.include_label)
        self.hypos_layout.addWidget(self.hypos_list)
        self.overview_layout.addLayout(self.hypos_layout)
        # 2
        self.include_label = QLabel('Входящие признаки')
        self.included_signs_table = SignValueTable(self)

        self.include_layout = QVBoxLayout(self)
        self.include_layout.addWidget(self.include_label)
        self.include_layout.addWidget(self.included_signs_table)
        self.overview_layout.addLayout(self.include_layout)
        # 3
        self.exclude_label = QLabel('Не входящие признаки')
        self.unincluded_signs_list = QListWidget(self)
        self.exclude_layout = QVBoxLayout(self)
        self.exclude_layout.addWidget(self.exclude_label)
        self.exclude_layout.addWidget(self.unincluded_signs_list)
        self.overview_layout.addLayout(self.exclude_layout)


class SignTable(QTableWidget):
    remove_sign = pyqtSignal(int)
    change_sign = pyqtSignal(int, str, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.fill_flag = False
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['id', 'Признак', 'Вопрос'])
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setColumnHidden(0, True)

        self.cellChanged.connect(self.emit_change)

    def emit_change(self, row, col):
        if not self.fill_flag:
            sign_id = int(self.item(row, 0).text())
            name = self.item(row, 1).text()
            question = self.item(row, 2).text()
            self.change_sign.emit(sign_id, name, question)

    def confirm_delete(self):
        if self.hasFocus() and self.currentRow() >= 0:
            row = self.currentRow()
            sign_id = int(self.item(row, 0).text())
            name = self.item(row, 1).text()
            question = self.item(row, 2).text()
            message = QuestionMessage('Удалить', f'Удалить признак <{name}> <{question}>?')
            if message.exec_() == message.AcceptRole:
                self.removeRow(row)
                self.remove_sign.emit(sign_id)

    def fill(self, signs: List[Sign]):
        self.fill_flag = True
        self.clearContents()
        self.setRowCount(len(signs))
        for i, s in enumerate(signs):
            self.setItem(i, 0, QTableWidgetItem(str(s.id)))
            self.setItem(i, 1, QTableWidgetItem(s.name))
            self.setItem(i, 2, QTableWidgetItem(s.question))
        self.fill_flag = False


class HypothesisTable(QTableWidget):
    remove_hypothesis = pyqtSignal(int)
    change_hypothesis = pyqtSignal(int, str, str, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.fill_flag = False
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['id', 'Гипотеза', 'Вероятность', 'Описание'])
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setColumnHidden(0, True)

        self.cellChanged.connect(self.emit_change)

    def emit_change(self, row, col):
        if not self.fill_flag:
            hypo_id = int(self.item(row, 0).text())
            name = self.item(row, 1).text()
            p = self.item(row, 2).text()
            desc = self.item(row, 3).text()
            self.change_hypothesis.emit(hypo_id, name, desc, p)

    def confirm_delete(self):
        if self.hasFocus():
            row = self.currentRow()
            hypo_id = int(self.item(row, 0).text())
            name = self.item(row, 1).text()
            p = self.item(row, 2).text()
            desc = self.item(row, 3).text()
            message = QuestionMessage('Удалить', f'Удалить гипотезу <{name}> <{desc}> <{p}>?')
            if message.exec_() == message.AcceptRole:
                self.removeRow(row)
                self.remove_hypothesis.emit(hypo_id)

    def fill(self, hypos: List[Hypothesis]):
        self.fill_flag = True
        self.clearContents()
        self.setRowCount(len(hypos))
        for i, h in enumerate(hypos):
            self.setItem(i, 0, QTableWidgetItem(str(h.id)))
            self.setItem(i, 1, QTableWidgetItem(h.name))
            self.setItem(i, 2, QTableWidgetItem(f'{h.init_p:.3f}'))
            self.setItem(i, 3, QTableWidgetItem(h.desc))
        self.fill_flag = False


class BaseStateTable(QTableWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['P', 'P min', 'P max', 'Гипотеза'])
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)

    def fill(self, hypos: List[Hypothesis]):
        self.clearContents()
        self.setRowCount(len(hypos))
        only_read = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        for i, h in enumerate(hypos):
            self.setItem(i, 0, QTableWidgetItem(f'{h.init_p:.3f}'))
            self.setItem(i, 1, QTableWidgetItem(f'{h.p_min:.3f}'))
            self.setItem(i, 2, QTableWidgetItem(f'{h.p_max:.3f}'))
            self.setItem(i, 3, QTableWidgetItem(h.name))
            self.item(i, 0).setFlags(only_read)
            self.item(i, 1).setFlags(only_read)
            self.item(i, 2).setFlags(only_read)
            self.item(i, 3).setFlags(only_read)


class RunBaseDialog(QDialog):
    def __init__(self, kb: KnowledgeBase):
        super().__init__()
        self.setWindowFlags(Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.kb: KnowledgeBase = kb
        self.calculator = CalculationProcess(kb.hypos, kb.signs, False)
        self.setup_ui()
        self.setup_signals()
        self.question_label.setText('Вопрос: ' + self.kb.get_sign_by_id(self.calculator.current_question).question)
        self.state_table.fill(self.calculator.h_list)

    def next_step(self, value: int):
        self.calculator.step(value, self.calculator.current_question)
        print(self.calculator.current_question, type(self.calculator.current_question))  # 0
        print(self.kb.get_sign_by_id(self.calculator.current_question))  # None
        # self.question_label.setText('Вопрос: ' + self.kb.get_sign_by_id(self.calculator.current_question).question)
        self.state_table.fill(self.calculator.h_list)

    def setup_signals(self):
        self.no_button.clicked.connect(lambda: self.next_step(0))
        self.p_no_button.clicked.connect(lambda: self.next_step(1))
        self.no_know_button.clicked.connect(lambda: self.next_step(2))
        self.p_yes_button.clicked.connect(lambda: self.next_step(3))
        self.yes_button.clicked.connect(lambda: self.next_step(4))

    def setup_ui(self):
        self.v_layout = QVBoxLayout(self)

        self.question_label = QLabel("Вопрос: как выспаться?", self)
        self.v_layout.addWidget(self.question_label)

        # Нет - 0   Скорее нет - 1  Не знаю - 2     Скорее да - 3   Да - 4
        self.input_layout = QHBoxLayout(self)
        self.no_button = QPushButton('Нет', self)
        self.p_no_button = QPushButton('Скорее нет', self)
        self.no_know_button = QPushButton('Не знаю', self)
        self.p_yes_button = QPushButton('Скорее да', self)
        self.yes_button = QPushButton('Да', self)
        self.input_layout.addWidget(self.no_button)
        self.input_layout.addWidget(self.p_no_button)
        self.input_layout.addWidget(self.no_know_button)
        self.input_layout.addWidget(self.p_yes_button)
        self.input_layout.addWidget(self.yes_button)
        self.v_layout.addLayout(self.input_layout)

        self.state_table = BaseStateTable(self)
        self.v_layout.addWidget(self.state_table)


class KnowledgeBaseWidget(QWidget):
    def __init__(self, model: AppModel, name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_model = model
        self.path = self.app_model.find_file(name)
        index = self.app_model.load_base(self.path)
        self.kb = self.app_model.bases[index]
        self.setup_ui()

        # actions
        self.save_action = QAction("Сохранить базу знаний", self)
        self.save_action.setShortcut('Ctrl+S')
        self.addAction(self.save_action)

        self.delete_action = QAction("Удалить", self)
        self.delete_action.setShortcut('Ctrl+D')
        self.addAction(self.delete_action)

        # fill data
        self.name_input.setText(self.kb.name)
        self.sign_table.fill(self.kb.signs)
        self.hypos_table.fill(self.kb.hypos)

        self.setup_signals()

    def open_links_dialog(self):
        dialog = LinkHypothesisDialog(self.kb)
        dialog.exec_()

    def open_run_base(self):
        dialog = RunBaseDialog(self.kb)
        dialog.exec_()

    def setup_signals(self):
        # tables signals
        self.sign_table.change_sign.connect(self.kb.change_sign)
        self.sign_table.change_sign.connect(lambda: self.sign_table.fill(self.kb.signs))
        self.sign_table.remove_sign.connect(self.kb.delete_sign)
        self.hypos_table.change_hypothesis.connect(self.kb.change_hypos)
        self.hypos_table.change_hypothesis.connect(lambda: self.hypos_table.fill(self.kb.hypos))
        self.hypos_table.remove_hypothesis.connect(self.kb.delete_hypo)
        # buttons clicks
        self.add_sign_button.clicked.connect(lambda: (self.kb.add_sign(), self.sign_table.fill(self.kb.signs)))
        self.add_hypos_button.clicked.connect(lambda: (self.kb.add_hypos(), self.hypos_table.fill(self.kb.hypos)))
        self.link_button.clicked.connect(self.open_links_dialog)
        self.run_base.clicked.connect(self.open_run_base)
        # actions triggers
        self.save_action.triggered.connect(lambda: self.app_model.save_base(self.kb))
        self.save_action.triggered.connect(lambda: InfoMessage('Сохранение', 'База знаний сохранена'))
        self.delete_action.triggered.connect(self.hypos_table.confirm_delete)
        self.delete_action.triggered.connect(self.sign_table.confirm_delete)

    def setup_ui(self):
        self.h_layout = QHBoxLayout(self)
        self.overview_layout = QVBoxLayout(self)
        self.edit_layout = QVBoxLayout(self)
        self.h_layout.addLayout(self.overview_layout)
        self.h_layout.addLayout(self.edit_layout)

        # название базы знаний
        self.name_label = QLabel('Название базы знаний:')
        self.name_input = QLineEdit(self)
        self.name_layout = QHBoxLayout(self)
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_input)
        self.overview_layout.addLayout(self.name_layout)

        # кнопки добавление гипотез/признаков и их связывания
        self.buttons_layout = QHBoxLayout(self)
        self.add_sign_button = QPushButton('Новый признак', self)
        self.add_hypos_button = QPushButton('Новая гипотеза', self)
        self.link_button = QPushButton('Привязка', self)
        self.run_base = QPushButton('Запустить', self)
        self.buttons_layout.addWidget(self.add_sign_button)
        self.buttons_layout.addWidget(self.add_hypos_button)
        self.buttons_layout.addWidget(self.link_button)
        self.buttons_layout.addWidget(self.run_base)
        self.overview_layout.addLayout(self.buttons_layout)

        # список признаков
        self.sign_table = SignTable(self)
        self.overview_layout.addWidget(self.sign_table)

        # список гипотез
        self.hypos_table = HypothesisTable(self)
        self.overview_layout.addWidget(self.hypos_table)
