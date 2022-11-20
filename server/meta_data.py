import enum
import json


class MenuTypes(enum.Enum):
    MAIN = 'MAIN'
    LOAD = 'LOAD'
    DATA = 'DATA'
    ANSWER = 'ANSWER'


class Mode(str, enum.Enum):
    """Режим расчётов."""

    MNM = 'MODE_MNM'
    PIECEWISE_GIVEN = 'MODE_PIECEWISE_GIVEN'
    IDEAL_DOT = 'IDEAL_DOT'

    @staticmethod
    def build(value):
        if not value:
            return Mode.MNM
        return Mode(value)


class MetaData:
    """
    Сущность для хранения и взаимодействия с клиентскими метаданными.
    Используется как хранилище состояний клиента.
    """

    menu_active_main: bool
    menu_active_load: bool
    menu_active_data: bool
    menu_active_answer: bool

    load_data: list

    mode: Mode

    free_chlen: bool
    r: float  # Уровень приоритета суммы модулей.
    delta: float  # Малая положительная величина.
    var_y: int  # Индекс столбца, зависимой переменной. Начинается с 1.
    m: int  # Большое положительное число.

    def __init__(self, data=None):
        if data is not None:
            self.menu_active_main = MetaData.get_value(data, 'menu_active_main')
            self.menu_active_load = MetaData.get_value(data, 'menu_active_load')
            self.menu_active_data = MetaData.get_value(data, 'menu_active_data')
            self.menu_active_answer = MetaData.get_value(data, 'menu_active_answer')

            self.load_data = MetaData.get_value(data, 'load_data')

            self.mode = Mode.build(MetaData.get_value(data, 'mode'))

            self.free_chlen = MetaData.get_value(data, 'free_chlen')
            self.r = MetaData.get_value(data, 'r')
            self.delta = MetaData.get_value(data, 'delta')
            self.var_y = MetaData.get_value(data, 'var_y')
            self.m = MetaData.get_value(data, 'm')

    def get_load_data_len(self):
        """
        Получает массив индексов столбцов загруженной матрицы.
        Значения в массиве начинается с 1.
        """
        return list(map(int, range(1, len(self.load_data[0]) + 1)))

    def get_load_data_rows_len(self):
        """
        Получает массив индексов строк загруженной матрицы.
        Значения в массиве начинается с 1.
        """
        return list(map(int, range(1, len(self.load_data) + 1)))

    def set_active_menu(self, menu_type: MenuTypes):
        self._drop_active_menu()

        if menu_type == MenuTypes.MAIN:
            self.menu_active_main = True
        elif menu_type == MenuTypes.LOAD:
            self.menu_active_load = True
        elif menu_type == MenuTypes.DATA:
            self.menu_active_data = True
        elif menu_type == MenuTypes.ANSWER:
            self.menu_active_answer = True

    def set_free_chlen(self, form):
        if self.get_value(form, 'free_chlen'):
            self.free_chlen = True
        else:
            self.free_chlen = False

    def set_data(self, form):
        self.var_y = int(self.get_value(form, 'var_y')) if self.get_value(form, 'var_y') else 1
        self.r = float(self.get_value(form, 'r')) if self.get_value(form, 'r') else 0.1

        if self.mode in [Mode.MNM, Mode.IDEAL_DOT]:
            self.set_free_chlen(form)
            self.delta = float(self.get_value(form, 'delta')) if self.get_value(form, 'delta') else 0.1
        if self.mode is Mode.PIECEWISE_GIVEN:
            self.free_chlen = False
            self.m = int(self.get_value(form, 'M')) if self.get_value(form, 'M') else 100000

    def update_params(self, form):
        self.r = float(self.get_value(form, 'r')) if self.get_value(form, 'r') else 0.1
        if self.mode is Mode.PIECEWISE_GIVEN:
            self.m = int(self.get_value(form, 'M')) if self.get_value(form, 'M') else 100000

    def _drop_active_menu(self):
        self.menu_active_main = False
        self.menu_active_load = False
        self.menu_active_data = False
        self.menu_active_answer = False

    def set_mode(self, form):
        self.mode = Mode(self.get_value(form, 'mode') if self.get_value(form, 'mode') else Mode.MNM)

        if self.mode == Mode.MNM and self.get_value(form, 'ideal_dot'):
            self.mode = Mode.IDEAL_DOT

    @staticmethod
    def get_value(data, key):
        try:
            return data[key]
        except KeyError:
            return None

    def __str__(self):
        return json.dumps(self, cls=MetaData.DataEncoder)

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель MetaData в JSON формат.
        """

        def default(self, obj):
            if isinstance(obj, MetaData):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)
