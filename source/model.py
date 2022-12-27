# *- coding: utf-8 -*-

from typing import Optional, Any, List, Set, Tuple
import json
from pathlib import Path, WindowsPath


class _ModelEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, WindowsPath):
            return {'__{}__'.format(o.__class__.__name__): str(o.resolve())}
        return {'__{}__'.format(o.__class__.__name__): o.__dict__}


def _model_decoder(o):
    if '__Sign__' in o:
        obj = Sign()
        obj.__dict__.update(o['__Sign__'])
        return obj
    elif '__SignValue__' in o:
        obj = SignValue()
        obj.__dict__.update(o['__SignValue__'])
        return obj
    elif '__Hypothesis__' in o:
        obj = Hypothesis()
        obj.__dict__.update(o['__Hypothesis__'])
        return obj
    elif '__KnowledgeBase__' in o:
        obj = KnowledgeBase()
        obj.__dict__.update(o['__KnowledgeBase__'])
        return obj
    elif '__WindowsPath__' in o:
        obj = Path(o['__WindowsPath__']).resolve()
        return obj
    return o


class Sign:
    """Признак. Имеет номер, название и вопрос."""

    def __init__(self, sign_id: int = 0, name: str = "New Sign", question: str = "How? What?"):
        self.id: int = sign_id
        self.name: str = name
        self.question: str = question

    def __repr__(self):
        return f"Sign({self.id}, {self.name}, {self.question})"


class SignValue:
    """
    Вероятности признака. Привязан к гипотезе.
    Имеет уникальный номер и вероятности проявления при наступлении и не наступлении гипотезы H.
    """

    def __init__(self, sign_id: int = -1, p_pos: float = 0.5, p_neg: float = 0.5):
        self.sign_id: int = sign_id
        self._p_pos: float = p_pos
        self._p_neg: float = p_neg

    def __repr__(self):
        return f"\n        SignValue({self.sign_id}, {self.p_pos}, {self.p_neg})"

    @property
    def p_pos(self) -> float:
        return self._p_pos

    @p_pos.setter
    def p_pos(self, value: float):
        if isinstance(value, float):
            self._p_pos = value
        elif isinstance(value, int):
            self._p_pos = float(value)
        elif isinstance(value, str):
            try:
                v = float(value.replace(',', '.'))
                self._p_pos = v
            except ValueError:
                return

    @property
    def p_neg(self) -> float:
        return self._p_neg

    @p_neg.setter
    def p_neg(self, value):
        if isinstance(value, float):
            self._p_neg = value
        elif isinstance(value, int):
            self._p_neg = float(value)
        elif isinstance(value, str):
            try:
                v = float(value.replace(',', '.'))
                self._p_neg = v
            except ValueError:
                return

    ###################################################################################################################

    def set_p_pos(self, p):
        if 0 <= p <= 1:
            self.p_pos = p

    def set_p_neg(self, p):
        if 0 <= p <= 1:
            self.p_neg = p

    def count_p_by_pos(self, p: float):
        return (self.p_pos * p) / ((self.p_pos * p) + self.p_neg * (1 - p))

    def count_p_by_neg(self, p: float):
        return ((1 - self.p_pos) * p) / ((1 - self.p_pos) * p + (1 - self.p_neg) * (1 - p))

    def count_attest_value(self, p: float):
        return abs(self.count_p_by_pos(p) - self.count_p_by_neg(p))


class Hypothesis:
    """
    Гипотеза это кортеж вида (H; p; n; (j, p+, p-);..) где
    H - название гипотезы
    p - априорная вероятность
    j - номер признака
    p+ - вероятность наступления j при наступлении H
    p- - вероятность наступления j при не наступлении H
    """

    def __init__(self, h_id: int = 0, name: str = "New Hypothesis", desc: str = "Empty description", p: float = 1.0):
        self.id = h_id
        self.name: str = name
        self.desc: str = desc
        self._init_p: float = p
        self.p = self._init_p
        self.p_max = self._init_p
        self.p_min = self._init_p
        self.signs: List[SignValue] = list()

    def __repr__(self):
        return f"Hypothesis({self.name}, {self.init_p}, {self.signs})"

    @property
    def init_p(self) -> float:
        return self._init_p

    @init_p.setter
    def init_p(self, value):
        if isinstance(value, float):
            self._init_p = value
        elif isinstance(value, int):
            self._init_p = float(value)
        elif isinstance(value, str):
            try:
                v = float(value.replace(',', '.'))
                self._init_p = v
            except ValueError:
                return

    def get_link_by_sign_id(self, sign_id: int) -> SignValue:
        for sv in self.signs:
            if sv.sign_id == sign_id:
                return sv

    def add_sign(self, s: Sign) -> SignValue:
        sv = SignValue()
        sv.sign_id = s.id
        self.signs.append(sv)
        return sv

    def remove_sign(self, s: Sign):
        for sv in self.signs:
            if sv.sign_id == s.id:
                self.signs.remove(sv)
                return

    ###################################################################################################################

    def set_p(self, p):
        if 0 <= p <= 1:
            self.p = p

    def get_sign_val_by_id(self, id) -> Optional[SignValue]:
        for s in self.signs:
            if s.id == id:
                return s
        return None

    def count_p(self, answer: bool, sign: SignValue, r=1, log=False):
        self.p = sign.count_p_by_pos(self.p) if answer else sign.count_p_by_neg(self.p)
        self.p *= r
        if log:
            print(f"Answer: {answer}, current P: {self.p}")

    def get_sign_ids(self):
        ids = []
        for s in self.signs:
            ids.append(s.sign_id)
        return ids

    def count_attest_values(self, log=False):
        sign_ids = self.get_sign_ids()

        arr = []
        for i in range(len(self.signs)):
            arr.append([])
        attest_values_data = dict(zip(sign_ids, arr))

        for sv_id in sign_ids:
            attest_values_data[sv_id] = self.get_sign_val_by_id(sv_id).count_attest_value(self.p)
            if log:
                print(f"Att. value for question {sv_id + 1}: {attest_values_data[sv_id]}")
        return attest_values_data

    def max_attest_value_id(self, log=False) -> int:
        attest_values_data = self.count_attest_values(log)
        return max(attest_values_data, key=attest_values_data.get)

    def count_p_max(self):
        for s in self.signs:
            self.p_max = s.count_p_by_pos(self.p_max)
        return self.p_max

    def count_p_min(self):
        for s in self.signs:
            self.p_min = s.count_p_by_neg(self.p_min)
        return self.p_min


class CalculationProcess:
    """
        2) Находим 1-ый вопрос с макс. ЦС
        3) Задаём вопрос
        4) Получаем ответ, удаляем заданный вопрос из списка
        5) Считаем Р, умножаем Р на R ответа
        + 6) Считаем Pmax и Pmin для каждой гипотезы
        7) Сравниваем Pmax и Pmin различных гипотез
           Если любая Pmax меньше максимальной Pmin, то выкидывам гипотезу
           Если любая Pmin больше минимальной Pmax, то выдаём гипотезу как ответ
           и завершаем алгоритм
        8) Если вопросы закончились, выдаём гипотезу с макс. Р
        9) Считаем ЦС для оставшихся вопросов
        10) Повторяем с п.2 до остановки
    """

    def __init__(self,
                 h_list: List[Hypothesis],
                 signs_to_check: List[Sign],
                 is_console: bool
                 ):
        self.h_list: List[Hypothesis] = h_list
        self.is_console: bool = is_console
        self.signs_to_check: List[Sign] = signs_to_check
        self.current_question: int = signs_to_check[0].id
        self.stop: bool = False

    def print_question(self, sign_id: int):
        for s in self.signs_to_check:
            if s.id == sign_id:
                print(s.question)

    def get_answer(self):
        if self.is_console:
            return int(input("Your answer: "))
        else:
            return 2

    def delete_sign(self, del_sign_id: int):
        idx = None
        if not any(sign.id == del_sign_id for sign in self.signs_to_check):
            print("Sign list doesn't contain sign with id {del_sign_id} \n")
            return
        for i in self.signs_to_check:
            if i.id == del_sign_id:
                idx = i.id
        self.signs_to_check.pop(idx)

    def get_max_h(self) -> str:
        """
        Возвращает имя гипотезы с максимальной вероятностью
        """
        h_names = [h.name for h in self.h_list if hasattr(h, 'name')]
        ps = [h.p for h in self.h_list if hasattr(h, 'p')]
        data = dict(zip(h_names, ps))
        for k, v in data.items():
            if v == max(ps):
                return k

    def process_answer(self, answer: int) -> Tuple[bool, float]:
        """
        Нет - 0 → (False, 1.0)
        Скорее нет - 1 → (False, 0.75)
        Не знаю - 2 → (True, 0.5)
        Скорее да - 3 → (True, 0.75)
        Да - 4 → (True, 1.0)
        """
        choice = {
            0: (False, 1.0),
            1: (False, 0.75),
            2: (True, 0.5),
            3: (True, 0.75),
            4: (True, 1.0)
        }
        if answer not in list(choice.keys()):
            answer = 2
        return choice[answer]

    def recount_ps(self, sign_id: int, answer: bool, r: float):
        for h in self.h_list:
            sign_value = h.get_sign_val_by_id(sign_id)
            h.count_p(answer, sign_value, r)

    def compare_p_min_max(self) -> bool:
        """
        Сравниваем Pmax и Pmin всех гипотез.
        Если любая Pmax меньше максимальной Pmin, то выкидывам гипотезу
        Если любая Pmin больше минимальной Pmax, то выдаём гипотезу как ответ
        и завершаем алгоритм
        """
        h_names = [h.name for h in self.h_list if hasattr(h, 'name')]
        ps_min_list = []
        ps_max_list = []

        for h in self.h_list:
            ps_min_list.append(h.count_p_min())
            ps_max_list.append(h.count_p_max())

        ps_min = dict(zip(h_names, ps_min_list))
        ps_max = dict(zip(h_names, ps_max_list))

    def step(self, answer_id: int):
        answer, r = self.process_answer(answer_id)
        # Удаляем заданный вопрос из списка
        if len(self.signs_to_check) == 0:
            self.stop = True
        # Считаем Р, умножаем Р на R ответа
        self.recount_ps(r)
        # Считаем Pmax и Pmin для каждой гипотезы,
        # сравниваем Pmax и Pmin различных гипотез,
        # проверяем останов
        self.stop = self.compare_p_min_max()
        return self.stop

    def calculate(self):
        stop = False

        while not stop:
            question_id = self.get_first_question()
            self.current_question = question_id
            # Выводим вопрос
            if self.is_console:
                self.print_question(question_id)
            else:
                pass
            # Получаем ответ
            answer_id = self.get_answer()
            self.delete_sign(question_id)
            self.step(answer_id)
        if self.is_console:
            print(self.get_max_h())
        else:
            pass
        return self.get_max_h()

    def get_h_by_id(self, h_id):
        for h in self.h_list:
            if h.id == h_id:
                return h
        return

    def get_first_question(self):
        max_h_id = self.get_max_h()
        return self.get_h_by_id(max_h_id).max_attest_value_id()


class KnowledgeBase:
    """База знаний. Состоит из признаков и гипотез."""

    def __init__(self):
        self.name = "New Knowledge Base"
        self.last_path: Path = Path('')
        self.signs: List[Sign] = list()
        self.hypos: List[Hypothesis] = list()

    def __repr__(self):
        return f"KnowledgeBase(\n    {self.signs},\n    {self.hypos}\n)"

    def get_hypothesis_by_id(self, target_id: int) -> Hypothesis:
        for h in self.hypos:
            if h.id == target_id:
                return h

    def get_sign_by_id(self, target_id: int) -> Sign:
        for s in self.signs:
            if s.id == target_id:
                return s

    def get_signs_in_hypothesis(self, h: Hypothesis) -> List[Sign]:
        return [self.get_sign_by_id(sv.sign_id) for sv in h.signs]

    def get_signs_out_hypothesis(self, h: Hypothesis) -> List[Sign]:
        return list(set(self.signs) - set(self.get_signs_in_hypothesis(h)))

    def get_links(self, h: Hypothesis) -> List[Tuple[Sign, SignValue]]:
        return [(self.get_sign_by_id(sv.sign_id), sv) for sv in h.signs]

    def add_hypos(self) -> Hypothesis:
        h = Hypothesis()
        if self.hypos:
            h.id = self.hypos[-1].id + 1
        self.hypos.append(h)
        return h

    def add_sign(self) -> Sign:
        s = Sign()
        if self.signs:
            s.id = self.signs[-1].id + 1
        self.signs.append(s)
        return s

    def change_sign(self, sign_id: int, name: str, question: str) -> Sign:
        s = self.get_sign_by_id(sign_id)
        s.name = name
        s.question = question
        return s

    def change_hypos(self, hypo_id: int, name: str, desc: str, p: str) -> Hypothesis:
        h = self.get_hypothesis_by_id(hypo_id)
        h.name = name
        h.desc = desc
        try:
            value = float(p.replace(',', '.'))
            h.init_p = value
        except ValueError:
            return h
        return h

    def change_link(self, h_id: int, sign_id: int, p_pos: str, p_neg: str):
        h = self.get_hypothesis_by_id(h_id)
        sv = h.get_link_by_sign_id(sign_id)
        sv.p_pos = p_pos
        sv.p_neg = p_neg

    def delete_sign(self, sign_id: int):
        self.signs.remove(self.get_sign_by_id(sign_id))
        to_remove = list()
        for h in self.hypos:
            for sv in h.signs:
                if sv.sign_id == sign_id:
                    to_remove.append(sv)
            for sv in to_remove:
                h.signs.remove(sv)

    def delete_hypo(self, hypo_id: int):
        self.hypos.remove(self.get_hypothesis_by_id(hypo_id))

    def delete_link(self, h_id, sign_id):
        h = self.get_hypothesis_by_id(h_id)
        sv = h.get_link_by_sign_id(sign_id)
        h.signs.remove(sv)


class AppModel:
    """Бизнес-модель приложения"""

    class JSON:
        ENCODER = _ModelEncoder
        DECODER = _model_decoder

    class Files:
        BASE_DIR = './data/'
        BASE_PATH = Path(BASE_DIR).resolve()
        BASE_PATH.mkdir(parents=True, exist_ok=True)
        SUFFIX = '.kb.json'

        @classmethod
        def create_path(cls, name) -> Path:
            return cls.BASE_PATH / (name + cls.SUFFIX)

        @classmethod
        def get_file_list(cls) -> List[Path]:
            # print(cls.BASE_PATH)
            return list(cls.BASE_PATH.glob(f'*{cls.SUFFIX}'))

    def __init__(self):
        self.bases: List[KnowledgeBase] = list()
        self.manual_files: Set[Path] = set()

    def __repr__(self):
        bases_str = '/n'.join([b.__repr__() for b in self.bases])
        return f"AppModel({bases_str})"

    def get_file_list(self) -> Set[Path]:
        return self.manual_files.union(set(self.Files.get_file_list()))

    def find_file(self, name: str) -> Path:
        file_name = name + self.Files.SUFFIX
        for p in self.get_file_list():
            if p.name == file_name:
                return p

    def add_manual_paths(self, files: List[Path]):
        self.manual_files = set(self.manual_files).union(set(files))

    def rename_base(self, base: KnowledgeBase, name: str):
        old_path = self.Files.create_path(base.name)
        new_path = self.Files.create_path(name)
        base.name = name
        old_path.rename(new_path)
        self.save_base(base)

    def add_base(self):
        kb = KnowledgeBase()
        self.bases.append(kb)
        AppModel.save_base(kb)

    @staticmethod
    def save_base(base: KnowledgeBase):
        path = AppModel.Files.create_path(base.name)  # self.BASE_DIR + base.name + '.kb.json'
        base.last_path = path
        with path.open('w') as file:
            json.dump({f'__{base.__class__.__name__}__': base.__dict__}, file, indent=4, cls=AppModel.JSON.ENCODER)

    def load_base(self, path: Path) -> int:
        for index, item in enumerate(self.bases):
            if item.last_path.name == path.name:
                return index

        with path.open('r') as file:
            data: KnowledgeBase = json.load(file, object_hook=self.JSON.DECODER)
        data.last_path = path
        self.bases.append(data)
        return len(self.bases) - 1


if __name__ == '__main__':
    print(AppModel.Files.get_file_list())
    print(AppModel.Files.create_path('TT_data'))
    print(AppModel.Files.get_file_list()[0].name)

    test_path = "../data/test_data.kb.json"
    s = Sign()
    s.id = 10
    s.name = "Sign One"

    h = Hypothesis()
    h.name = "Hy One"
    h.init_p = 0.33

    sv = SignValue()
    sv.sign_id = s.id
    sv.p_pos = 0.75
    sv.p_neg = 0.25

    sv2 = SignValue()
    sv2.sign_id = 3
    sv2.p_pos = 0.66
    sv2.p_neg = 0.22

    h.signs.append(sv)
    h.signs.append(sv2)

    kb = KnowledgeBase()
    kb.signs.append(s)
    kb.hypos.append(h)

    print(kb)
    #
    # with open(test_path, 'w') as f:
    #     json.dump({"__KnowledgeBase__": kb.__dict__}, f, indent=4, cls=AppModel.JSON.ENCODER)
    #
    # with open(test_path, 'r') as f:
    #     d = json.load(f, object_hook=AppModel.JSON.DECODER)
    #     print(d)

    app = AppModel()
    app.bases.append(kb)
    print(app)
    print(app.bases[0].last_path)
    app.save_base(kb)
    print(app.bases[0].last_path)
    # p = Path('../data/test_data.kb.json').resolve()
    c = app.load_base(Path(kb.last_path))
    print(c)
    print(app)
    print(app.bases[0].last_path)

