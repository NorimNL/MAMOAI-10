# *- coding: utf-8 -*-

from typing import Optional, Any, List, Set
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

    def __init__(self):
        self.id: int = 0
        self.name: str = "New Sign"
        self.question: str = "How? What?"

    def __repr__(self):
        return f"Sign({self.id}, {self.name}, {self.question})"


class SignValue:
    """
    Вероятности признака. Привязан к гипотезе.
    Имеет уникальный номер и вероятности проявления при наступлении и не наступлении гипотезы H.
    """

    def __init__(self):
        self.id = 0
        self.sign_id: int = -1
        self._p_pos: float = 0.5
        self._p_neg: float = 0.5

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


class Hypothesis:
    """
    Гипотеза это кортеж вида (H; p; n; (j, p+, p-);..) где
    H - название гипотезы
    p - априорная вероятность
    j - номер признака
    p+ - вероятность наступления j при наступлении H
    p- - вероятность наступления j при не наступлении H
    """

    def __init__(self):
        self.id = 0
        self.name: str = "New Hypothesis"
        self.desc: str = "Empty description"
        self._p: float = 1.0
        self.signs: List[SignValue] = list()

    def __repr__(self):
        return f"Hypothesis({self.name}, {self.p}, {self.signs})"

    @property
    def p(self) -> float:
        return self._p

    @p.setter
    def p(self, value):
        if isinstance(value, float):
            self._p = value
        elif isinstance(value, int):
            self._p = float(value)
        elif isinstance(value, str):
            try:
                v = float(value.replace(',', '.'))
                self._p = v
            except ValueError:
                return

    def get_link_by_id(self, target_id: int) -> SignValue:
        for sv in self.signs:
            if sv.id == target_id:
                return sv

    def add_sign(self, s: Sign):
        sv = SignValue()
        sv.sign_id = s.id
        self.signs.append(sv)

    def remove_sign(self, s: Sign):
        for sv in self.signs:
            if sv.sign_id == s.id:
                self.signs.remove(sv)
                return


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

    def hypo_signs(self, hypo: Hypothesis) -> List[Sign]:
        sign_value_ids = set([sv.sign_id for sv in hypo.signs])
        sign_ids = set([s.id for s in self.signs])
        target_ids = sign_ids & sign_value_ids
        return list([s for s in self.signs if s.id in target_ids])

    def hypo_unsign(self, hypo: Hypothesis) -> List[Sign]:
        sign_value_ids = set([sv.sign_id for sv in hypo.signs])
        sign_ids = set([s.id for s in self.signs])
        target_ids = sign_ids - sign_value_ids
        return list([s for s in self.signs if s.id in target_ids])

    def add_hypos(self):
        h = Hypothesis()
        if self.hypos:
            h.id = self.hypos[-1].id + 1
        self.hypos.append(h)
        return h

    def add_sign(self):
        s = Sign()
        if self.signs:
            s.id = self.signs[-1].id + 1
        self.signs.append(s)
        return s

    def change_sign(self, row, col, text):
        sign = self.signs[row]
        if col == 0:
            sign.name = text
        elif col == 1:
            sign.question = text
        # AppModel.save_base(self)

    def change_hypos(self, row: int, col: int, text):
        h = self.hypos[row]
        if col == 0:
            h.name = text
        elif col == 1:
            try:
                value = float(text.replace(',', '.'))
                h.p = value
            except:
                return
        elif col == 2:
            h.desc = text
        # AppModel.save_base(self)

    def change_sign_link_values(self, row, col, text):
        pass


class AppModel:
    """Бизнес-модель приложения"""

    class JSON:
        ENCODER = _ModelEncoder
        DECODER = _model_decoder

    class Files:
        BASE_DIR = './data/'
        BASE_PATH = Path(BASE_DIR).resolve()
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
    h.p = 0.33

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
