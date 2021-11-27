import datetime
import json
import jwt


class Token:
    """
    Токен для идентификации сессий пользователей.
    """

    body: str
    create_time: datetime.datetime

    def __init__(self, token: str = None):
        if token is None:
            self.create_time = datetime.datetime.now()
            self.body = jwt.encode(payload={'create_time': str(self.create_time)}, key='secret', algorithm="HS512")
        else:
            data = Token.decode(token)
            if data is None:
                raise Exception("Bad token!")
            self.body = token
            self.create_time = datetime.datetime.fromisoformat(data['create_time'])

    @staticmethod
    def decode(token: str):
        try:
            return jwt.decode(jwt=token, key='secret', algorithms="HS512")
        except jwt.exceptions.InvalidSignatureError as e:
            print(e)
            return None

    def __str__(self):
        return self.body


class Session:
    """
    Кастомная сессия пользователя.
    """

    token: Token

    def __init__(self, token: str = None):
        if token is None:
            self.create_token()
        else:
            self.token = Session.get_session(token)

    def create_token(self):
        self.token = Token()
        # сохранить токен в БД.

    @staticmethod
    def get_session(_token: str):
        token = Token(_token)
        # проверить наличие токена в БД, если его там нет, создать новый.
        return token

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель Session в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, Session):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)
