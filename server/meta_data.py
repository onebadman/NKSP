import enum
import json


class MenuTypes(enum.Enum):
    MAIN = 'MAIN'
    LOAD = 'LOAD'
    DATA = 'DATA'
    ANSWER = 'ANSWER'


class MetaData:
    """
    Сущность для хранения и взаимодействия с клиентскими метаданными.
    Используется как хранилище состояний клиента.
    """

    menu_active_main: bool
    menu_active_load: bool
    menu_active_data: bool
    menu_active_answer: bool

    def __init__(self, data):
        if data is not None:
            self.menu_active_main = data['menu_active_main']
            self.menu_active_load = data['menu_active_load']
            self.menu_active_data = data['menu_active_data']
            self.menu_active_answer = data['menu_active_answer']

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

    def _drop_active_menu(self):
        self.menu_active_main = False
        self.menu_active_load = False
        self.menu_active_data = False
        self.menu_active_answer = False

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель MetaData в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, MetaData):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)
