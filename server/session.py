import datetime
import json

import jwt
import redis


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
            self.body = token
            self.create_time = datetime.datetime.fromisoformat(data['create_time'])

    @staticmethod
    def decode(token: str):
        return jwt.decode(jwt=token, key='secret', algorithms="HS512")

    def __str__(self):
        return self.body


class Session:
    """
    Кастомная сессия пользователя.
    """

    token: Token

    def __init__(self, token: Token = None):
        if token is None:
            self.create_token()
        else:
            self.token = token

    def create_token(self):
        self.token = Token()
        r = redis.Redis(decode_responses=True)
        r.set(
            self.token.body, "")
        r.expireat(
            self.token.body,
            datetime.datetime.fromisoformat(f'{datetime.date.today() + datetime.timedelta(days=1)} 04:00:00'))
        r.close()

    @staticmethod
    def get_session(_token: str):
        try:
            token = Token(_token)

            r = redis.Redis()
            data = r.get(token.body)
            if data is None:
                r.close()
                return Session()
            r.close()
            return Session(token)

        except jwt.exceptions.InvalidSignatureError as e:
            return Session()

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель Session в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, Session):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)
