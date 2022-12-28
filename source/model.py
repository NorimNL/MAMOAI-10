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
        else:
            print("Incorrect p")

    def set_p_neg(self, p):
        if 0 <= p <= 1:
            self.p_neg = p
        else:
            print("Incorrect p")

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

    def reset(self):
        self.p = self.init_p
        self.p_max = self.init_p
        self.p_min = self.init_p

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

    def del_sign(self, sign_to_del_id):
        idxs_to_del = []
        for s in self.signs:
            if s.sign_id == sign_to_del_id:
                idxs_to_del.append(s.sign_id)
        for i in idxs_to_del:
            self.signs.pop(i)

    def get_sign_val_by_id(self, sign_id) -> Optional[SignValue]:
        for sv in self.signs:
            if sv.sign_id == sign_id:
                return sv
        return

    def count_p(self, answer: bool, sign: SignValue, r=1.0, log=False):
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

        for sign_id in sign_ids:
            attest_values_data[sign_id] = self.get_sign_val_by_id(sign_id).count_attest_value(self.p)
            if log:
                print(f"Att. value for question {sign_id + 1}: {attest_values_data[sign_id]}")
        print()
        return attest_values_data

    def max_attest_value_id(self, log=False) -> int:
        attest_values_data = self.count_attest_values(log)
        max_attest_value_id = max(attest_values_data, key=attest_values_data.get)
        return max_attest_value_id

    def count_p_max(self):
        for s in self.signs:
            self.p_max = self.get_sign_val_by_id(s.sign_id).count_p_by_pos(self.p_max)
        return self.p_max

    def count_p_min(self):
        for s in self.signs:
            self.p_min = self.get_sign_val_by_id(s.sign_id).count_p_by_neg(self.p_min)
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
        print(f"Signs to check len: {len(self.signs_to_check)}")
        for s in self.signs_to_check:
            if s.id == sign_id:
                print(s.question)

    def get_answer(self):
        if self.is_console:
            print("Нет (0) - Скорее нет (1) - Не знаю (2) - Скорее да (3) - Да (4)")
            return int(input("Your answer: "))
        else:
            ANSWER = 2
            return ANSWER

    def get_h_by_id(self, h_id):
        for h in self.h_list:
            if h.id == h_id:
                return h
        return None

    def get_sign_by_id(self, sign_id):
        for s in self.signs_to_check:
            if s.id == sign_id:
                return s
        return None

    def delete_sign(self, del_sign_id: int):
        idx = None
        print(f"Sign to delete: {del_sign_id}")
        if not any(sign.id == del_sign_id for sign in self.signs_to_check):
            print(f"Sign list doesn't contain sign with id {del_sign_id} \n")
            return
        for i in self.signs_to_check:
            if i.id == del_sign_id:
                idx = i.id
        self.signs_to_check.pop(idx)
        print(f"Sign {del_sign_id} successfuly deleted")

    def update_signs(self, sign_to_del):
        for h in self.h_list:
            h.del_sign(sign_to_del)

    def get_max_h(self, log=False) -> int:
        """
        Возвращает имя гипотезы с максимальной вероятностью
        """
        h_ids = [h.id for h in self.h_list if hasattr(h, 'id')]
        if log:
            print(f"H_list: {h_ids}")
        ps = [h.p for h in self.h_list if hasattr(h, 'p')]
        if log:
            print(f"P_list: {ps}")
        data = dict(zip(h_ids, ps))
        if log:
            print(f"Data:")
        print(data)

        for k, v in data.items():
            if v == max(ps):
                return k

    def get_first_question(self):
        max_h_id = self.get_max_h()
        print(f"{max_h_id}) {self.get_sign_by_id(max_h_id).question}, \n p - {self.h_list[max_h_id].p}")
        # return self.get_h_by_id(max_h_id).max_attest_value_id(self.signs_to_check)
        return self.get_h_by_id(max_h_id).max_attest_value_id()

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
            # print(f"Sign ID: {sign_id}")
            # sign_value = h.get_sign_val_by_id(sign_id)
            sign_value = h.get_link_by_sign_id(sign_id)
            # print(f"Sign value: {sign_value}")
            h.count_p(answer, sign_value, r)

    def get_minmax_data(self, log=False):
        h_ids = [h.id for h in self.h_list if hasattr(h, 'id')]

        ps_min_list = []
        ps_max_list = []

        for h in self.h_list:
            ps_min_list.append(h.count_p_min())
            ps_max_list.append(h.count_p_max())

        ps_min_data = dict(zip(h_ids, ps_min_list))
        ps_max_data = dict(zip(h_ids, ps_max_list))
        # Максимальная Pmin
        p_min = max(ps_min_list)
        # Минимальная Pmax
        p_max = min(ps_max_list)
        if log:
            print(f"Min. data: \n {ps_min_data} \n")
            print(f"Max. data: \n {ps_max_data} \n")
            print(f"Min. p: \n {p_min:.5f}")
            print(f"Max. p: \n {p_max:.5f}")

        ids_to_delete = []
        for h in self.h_list:
            if log:
                print(f"Pmax of {h.name} = {h.p_max:.5f}")
            if h.p_max < p_min:
                ids_to_delete.append(h.id)

        ids_to_answer = []
        for h in self.h_list:
            if log:
                print(f"Pmin of {h.name} = {h.p_min:.5f}")
            if h.p_min < p_max:
                ids_to_answer.append(h.id)

        if log:
            print(f"Ids to delete: {ids_to_delete}")
            print(f"Ids to answer: {ids_to_answer}")

        # return ps_min, ps_max, p_min, p_max, ids_to_delete, ids_to_answer
        return ids_to_delete, ids_to_answer

    def stop_or_del_hyp(self):
        ids_to_delete, ids_to_answer = self.get_minmax_data()
        if len(ids_to_answer) > 1:
            return False
        else:
            return True

    def step(self, answer_id: int, question_id):
        answer, r = self.process_answer(answer_id)
        # Удаляем заданный вопрос из списка
        if len(self.signs_to_check) == 0:
            self.stop = True
        # Считаем Р, умножаем Р на R ответа
        self.recount_ps(self.current_question, answer, r)
        self.delete_sign(question_id)
        self.update_signs(question_id)
        self.get_max_h()
        # Считаем Pmax и Pmin для каждой гипотезы,
        # сравниваем Pmax и Pmin различных гипотез,
        # проверяем останов
        self.stop = self.stop_or_del_hyp()
        return self.stop

    def calculate(self):
        while not self.stop:
            question_id = self.get_first_question()
            print(f"Question id: {question_id}")
            self.current_question = question_id
            # Выводим вопрос
            if self.is_console:
                self.print_question(question_id)
            else:
                pass
            # Получаем ответ
            answer_id = self.get_answer()
            self.step(answer_id, question_id)
        if self.is_console:
            print(f"\nCongrats! \n{self.get_h_by_id(self.get_max_h()).description}")
        else:
            pass
        return self.get_max_h()


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

    def reset_hypothesis(self):
        for h in self.hypos:
            h.reset()
        return self

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
