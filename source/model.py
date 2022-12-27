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
    # print(AppModel.Files.get_file_list())
    # print(AppModel.Files.create_path('TT_data'))
    # print(AppModel.Files.get_file_list()[0].name)
    #
    # test_path = "../data/test_data.kb.json"
    # s = Sign()
    # s.id = 10
    # s.name = "Sign One"
    #
    # h = Hypothesis()
    # h.name = "Hy One"
    # h.init_p = 0.33
    #
    # sv = SignValue()
    # sv.sign_id = s.id
    # sv.p_pos = 0.75
    # sv.p_neg = 0.25
    #
    # sv2 = SignValue()
    # sv2.sign_id = 3
    # sv2.p_pos = 0.66
    # sv2.p_neg = 0.22
    #
    # h.signs.append(sv)
    # h.signs.append(sv2)
    #
    # kb = KnowledgeBase()
    # kb.signs.append(s)
    # kb.hypos.append(h)
    #
    # print(kb)
    # #
    # # with open(test_path, 'w') as f:
    # #     json.dump({"__KnowledgeBase__": kb.__dict__}, f, indent=4, cls=AppModel.JSON.ENCODER)
    # #
    # # with open(test_path, 'r') as f:
    # #     d = json.load(f, object_hook=AppModel.JSON.DECODER)
    # #     print(d)
    #
    # app = AppModel()
    # app.bases.append(kb)
    # print(app)
    # print(app.bases[0].last_path)
    # app.save_base(kb)
    # print(app.bases[0].last_path)
    # # p = Path('../data/test_data.kb.json').resolve()
    # c = app.load_base(Path(kb.last_path))
    # print(c)
    # print(app)
    # print(app.bases[0].last_path)

    test_signs = [
        Sign(0, "Шучу с другими", "Я не склонен постоянно шутить и смеяться с другими людьми."),
        Sign(1, "Юмор помогает при подавленности",
             "Обычно, когда я один и чувствую себя подавленным, юмор поднимает мне настроение."),
        Sign(2, "Шучу над ошибками", "Если кто-то допускает ошибку, я часто подшучиваю над этим."),
        Sign(3, "Позволяю больше", "Я позволяю людям смеяться, подшучивать над собой больше, чем следовало бы."),
        Sign(4, "Легко смешу других",
             "Мне нетрудно рассмешить других – мне кажется, у меня от природы хорошее чувство юмора."),
        Sign(5, "Нелепости при подавленности смешат", "Когда я подавлен, меня не смешат нелепости жизни."),
        Sign(6, "Обидный юмор", "Мой юмор никогда не обижает и не задевает других людей."),
        Sign(7, "Увлекаюсь самокритикой",
             "Я могу увлечься самокритикой или принижением самого себя, если это смешит мою семью или друзей."),
        Sign(8, "Редко смешу успешно", "Мне редко удается рассмешить людей, когда я рассказываю смешные истории."),
        Sign(9, "Ищу смешное в ситуации",
             "Если я расстроен или чувствую себя несчастным, я стараюсь найти нечто смешное в ситуации, чтобы почувствовать себя лучше."),
        Sign(10, "Не волнует обидность юмора",
             "Когда я шучу или рассказываю нечто смешное, меня мало волнует, обидит ли это кого-то."),
        Sign(11, "Располагаю своими неудачами",
             "Я часто стараюсь расположить к себе людей, понравиться им, рассказывая что-нибудь смешное о своих слабостях, промахах или неудачах."),
        Sign(12, "Много шучу", "Близкие друзья считают, что я много шучу и смеюсь."),
        Sign(13, "Юмор, чтобы не впасть в отчаяние",
             "Если я расстроен чем-то, мое чувство юмора помогает мне не впадать в отчаяние."),
        Sign(14, "Против критичного юмора",
             "Мне не нравится, когда кто-то использует юмор с целью критики или унижения других."),
        Sign(15, "Против самоиронии", "Я не склонен шутить над собой, делая себя объектом юмора."),
        Sign(16, "Не люблю развлекать", "Обычно мне не нравится рассказывать анекдоты и развлекать людей."),
        Sign(17, "Когда несчастна, думаю о смешном",
             "Если я один и чувствую себя несчастным, я стараюсь подумать о чем-нибудь смешном, чтобы поднять себе настроение."),
        Sign(18, "Не могу сдержать обидные шутки",
             "Если мне приходит в голову нечто остроумное, я не могу сдержаться и не рассказать, даже если это кого-то обидит."),
        Sign(19, "Слишком самоиронична для других",
             "Я часто перегибаю палку, иронизируя над собой, чтобы рассмешить окружающих."),
        Sign(20, "Люблю веселить", "Мне доставляет удовольствие веселить других."),
        Sign(21, "Нет ЧЮ при плохом настроении",
             "Мне трудно сохранять чувство юмора, если я расстроен или мне грустно."),
        Sign(22, "Не смеюсь над другими", "Я никогда не смеюсь над другими, даже если все мои друзья делают это."),
        Sign(23, "Я объект шуток близких", "В компании друзей или в кругу семьи надо мной часто подшучивают."),
        Sign(24, "Шучу реже друзей", "В компании друзей я шучу реже, чем другие."),
        Sign(25, "Смешное не спасает от проблем",
             "Даже если найти нечто смешное в ситуации, от трудностей это не избавит."),
        Sign(26, "Шучу над неприятными",
             "Если мне кто-то не нравится, я часто шучу или подтруниваю над этим человеком."),
        Sign(27, "Проблемы - повод посмеяться",
             "Я использую свои жизненные проблемы и слабости для того, чтобы повеселить других."),
        Sign(28, "В окружении хорошо шучу",
             "Обычно в присутствии других людей я могу придумать гораздо более остроумные вещи, чем другие."),
        Sign(29, "ЧЮ не зависит от компании",
             "Мне не всегда нужна компания для того, чтобы развеселиться – я найду над чем посмеяться, даже будучи в одиночестве."),
        Sign(30, "Не буду шутить обидно",
             "Даже если что-то кажется мне очень смешным, я не буду смеяться или шутить по этому поводу, если это кого-то обидит."),
        Sign(31, "Объект шуток ради настроения близких",
             "Позволять другим смеяться надо мной – мой способ поддерживать друзей и семью в хорошем расположении духа."),
    ]

    desc_0 = "Люди c аффилиативным чувством юмора часто шутят, спонтанно вовлекаются в добродушный обмен шутливыми замечаниями. Этот мягкий, доброжелательный и толерантный стиль юмора способствует укреплению межличностных отношений и росту взаимной привлекательности. Аффилиативный юмор связывается с экстраверсией, открытостью новому опыту, оптимизмом, жизнерадостностью, самопринятием и самоценностью, с успешностью установления и поддержания межличностных отношений, удовлетворенностью качеством жизни, преобладанием положительных эмоций и хорошего настроения."
    desc_1 = "Самоподдерживающий стиль юмора подразумевает оптимистичный взгляд на жизнь, умение сохранять чувство юмора перед лицом трудностей и проблем, то есть является регулятором эмоций и механизмом совладания со стрессом. По сравнению с аффилиативным, самоподдерживающий юмор выполняет, в первую очередь, интрапсихическую функцию и потому не так сильно связан с экстраверсией. Он имеет отрицательную связь с нейротизмом и положительно коррелирует с оптимизмом, открытостью новому опыту, самоценностью и удовлетворенностью качеством жизни, с успешностью установления и поддержания межличностных отношений."
    desc_2 = "Агрессивный юмор включает в себя сарказм, насмешку, подтрунивание, он может быть использован в целях манипуляции другим. Люди с агрессивным стилем юмора часто не могут справиться с желанием сострить, даже если шутка может кого-то обидеть. Этот стиль юмора положительно связан с нейротизмом, враждебностью, гневом и агрессией и отрицательно — с удовлетворенностью межличностными отношениями, дружелюбием и совестливостью, социальной компетентностью, способностью оказывать эмоциональную поддержку другому человеку и эффективностью юмора как копинг-стратегии."
    desc_3 = "Самоуничижительный стиль означает использование юмора, направленного против самого себя, с целью снискания расположения значимых других. Такие люди, заискивая перед окружающими, позволяют им делать себя объектом шуток и готовы разделить с ними этот смех. Хотя они могут восприниматься как остроумные и веселые, за этим стоят низкая самооценка и обостренная потребность в принятии. Они испытывают трудности в отстаивании своих прав. Самоуничижительный стиль юмора положительно связывается с нейротизмом, депрессией, тревогой и отрицательно — с удовлетворенностью межличностными отношениями, качеством жизни, психологическим благополучием, самоценностью."

    sv_0 = [
        SignValue(0, 0.3, 0.8),
        SignValue(1, 0.5, 0.4),
        SignValue(2, 0.6, 0.5),
        SignValue(3, 0.4, 0.5),
        SignValue(4, 0.65, 0.2),
        SignValue(5, 0.4, 0.6),
        SignValue(6, 0.8, 0.3),
        SignValue(7, 0.6, 0.5),
        SignValue(8, 0.25, 0.7),
        SignValue(9, 0.6, 0.4),
        SignValue(10, 0.68, 0.4),
        SignValue(11, 0.65, 0.5),
        SignValue(12, 0.67, 0.27),
        SignValue(13, 0.7, 0.4),
        SignValue(14, 0.75, 0.4),
        SignValue(15, 0.6, 0.4),
        SignValue(16, 0.4, 0.7),
        SignValue(17, 0.6, 0.4),
        SignValue(18, 0.5, 0.6),
        SignValue(19, 0.5, 0.6),
        SignValue(20, 0.8, 0.1),
        SignValue(21, 0.6, 0.5),
        SignValue(22, 0.7, 0.3),
        SignValue(23, 0.7, 0.5),
        SignValue(24, 0.4, 0.6),
        SignValue(25, 0.3, 0.6),
        SignValue(26, 0.2, 0.8),
        SignValue(27, 0.6, 0.5),
        SignValue(28, 0.75, 0.4),
        SignValue(29, 0.65, 0.3),
        SignValue(30, 0.7, 0.3),
        SignValue(31, 0.65, 0.4)
    ]

    sv_1 = [
        SignValue(0, 0.5, 0.6),
        SignValue(1, 0.7, 0.2),
        SignValue(2, 0.2, 0.5),
        SignValue(3, 0.2, 0.7),
        SignValue(4, 0.56, 0.45),
        SignValue(5, 0.3, 0.7),
        SignValue(6, 0.65, 0.5),
        SignValue(7, 0.3, 0.65),
        SignValue(8, 0.4, 0.5),
        SignValue(9, 0.8, 0.2),
        SignValue(10, 0.4, 0.5),
        SignValue(11, 0.5, 0.6),
        SignValue(12, 0.4, 0.5),
        SignValue(13, 0.9, 0.2),
        SignValue(14, 0.6, 0.2),
        SignValue(15, 0.45, 0.65),
        SignValue(16, 0.5, 0.5),
        SignValue(17, 0.8, 0.3),
        SignValue(18, 0.5, 0.5),
        SignValue(19, 0.3, 0.75),
        SignValue(20, 0.2, 0.5),
        SignValue(21, 0.2, 0.8),
        SignValue(22, 0.6, 0.5),
        SignValue(23, 0.6, 0.5),
        SignValue(24, 0.4, 0.5),
        SignValue(25, 0.2, 0.7),
        SignValue(26, 0.5, 0.6),
        SignValue(27, 0.6, 0.5),
        SignValue(28, 0.4, 0.5),
        SignValue(29, 0.75, 0.3),
        SignValue(30, 0.4, 0.5),
        SignValue(31, 0.3, 0.7),
    ]

    sv_2 = [
        SignValue(0, 0.6, 0.4, ),
        SignValue(1, 0.6, 0.4, ),
        SignValue(2, 0.8, 0.3, ),
        SignValue(3, 0.3, 0.65, ),
        SignValue(4, 0.6, 0.4, ),
        SignValue(5, 0.7, 0.3, ),
        SignValue(6, 0.2, 0.85, ),
        SignValue(7, 0.5, 0.6, ),
        SignValue(8, 0.4, 0.5, ),
        SignValue(9, 0.2, 0.7, ),
        SignValue(10, 0.8, 0.3, ),
        SignValue(11, 0.4, 0.7, ),
        SignValue(12, 0.4, 0.5, ),
        SignValue(13, 0.5, 0.6, ),
        SignValue(14, 0.35, 0.75, ),
        SignValue(15, 0.7, 0.4, ),
        SignValue(16, 0.6, 0.4, ),
        SignValue(17, 0.4, 0.5, ),
        SignValue(18, 0.8, 0.5, ),
        SignValue(19, 0.35, 0.7, ),
        SignValue(20, 0.2, 0.5, ),
        SignValue(21, 0.7, 0.3, ),
        SignValue(22, 0.8, 0.5, ),
        SignValue(23, 0.65, 0.6, ),
        SignValue(24, 0.3, 0.6, ),
        SignValue(25, 0.7, 0.3, ),
        SignValue(26, 0.8, 0.4, ),
        SignValue(27, 0.3, 0.5, ),
        SignValue(28, 0.55, 0.4, ),
        SignValue(29, 0.4, 0.6, ),
        SignValue(30, 0.4, 0.8, ),
        SignValue(31, 0.4, 0.65, ),
    ]

    sv_3 = [
        SignValue(0, 0.7, 0.3, ),
        SignValue(1, 0.4, 0.6, ),
        SignValue(2, 0.4, 0.5, ),
        SignValue(3, 0.8, 0.4, ),
        SignValue(4, 0.4, 0.6, ),
        SignValue(5, 0.6, 0.4, ),
        SignValue(6, 0.55, 0.3, ),
        SignValue(7, 0.8, 0.3, ),
        SignValue(8, 0.3, 0.6, ),
        SignValue(9, 0.6, 0.5, ),
        SignValue(10, 0.3, 0.7, ),
        SignValue(11, 0.8, 0.3, ),
        SignValue(12, 0.3, 0.5, ),
        SignValue(13, 0.6, 0.4, ),
        SignValue(14, 0.65, 0.5, ),
        SignValue(15, 0.3, 0.75, ),
        SignValue(16, 0.3, 0.6, ),
        SignValue(17, 0.55, 0.6, ),
        SignValue(18, 0.3, 0.7, ),
        SignValue(19, 0.8, 0.4, ),
        SignValue(20, 0.7, 0.4, ),
        SignValue(21, 0.4, 0.7, ),
        SignValue(22, 0.75, 0.5, ),
        SignValue(23, 0.75, 0.3, ),
        SignValue(24, 0.3, 0.6, ),
        SignValue(25, 0.5, 0.6, ),
        SignValue(26, 0.3, 0.5, ),
        SignValue(27, 0.8, 0.3, ),
        SignValue(28, 0.6, 0.5, ),
        SignValue(29, 0.45, 0.6, ),
        SignValue(30, 0.65, 0.3, ),
        SignValue(31, 0.75, 0.4, ),
    ]

    test_hs = [
        Hypothesis(0, "Аффилиативный", desc_0, 0.2),
        Hypothesis(1, "Самоподдерживающий", desc_1, 0.35),
        Hypothesis(2, "Агрессивный", desc_2, 0.3),
        Hypothesis(3, "Самоуничижительный", desc_3, 0.15),
    ]
    test_hs[0].signs = sv_0
    test_hs[1].signs = sv_1
    test_hs[2].signs = sv_2
    test_hs[3].signs = sv_3

    kb = KnowledgeBase()
    kb.signs = test_signs
    kb.hypos = test_hs
    kb.name = 'Humor_M'
    AppModel.save_base(kb)
    print("END")
