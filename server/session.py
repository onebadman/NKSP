import datetime
import json
import pickle

import jwt
import redis

from server.lp import Result
from server.meta_data import MetaData
from server.config import REDIS_HOST, REDIS_PORT, SECRET_JWT


class Token:
    """
    Токен для идентификации сессий пользователей.
    """

    body: str
    create_time: datetime.datetime

    def __init__(self, token: str = None):
        if token is None:
            self.create_time = datetime.datetime.now()
            self.body = jwt.encode(payload={'create_time': str(self.create_time)}, key=SECRET_JWT, algorithm="HS512")
        else:
            data = Token.decode(token)
            self.body = token
            self.create_time = datetime.datetime.fromisoformat(data['create_time'])

    @staticmethod
    def decode(token: str):
        return jwt.decode(jwt=token, key=SECRET_JWT, algorithms="HS512")

    def __str__(self):
        return self.body


class Session:
    """
    Кастомная сессия пользователя.
    """

    token: Token
    _meta_data: MetaData
    _result: Result

    def __init__(self, token: Token = None):
        if token is None:
            self.create_token()
        else:
            self.token = token

        self._meta_data = None
        self._result = None

    @property
    def meta_data(self) -> MetaData:
        r = Session._get_redis()
        if r.get(f'{self.token.body}_meta_data'):
            self._meta_data = pickle.loads(r.get(f'{self.token.body}_meta_data'))
        else:
            self._meta_data = MetaData()

        return self._meta_data

    @meta_data.setter
    def meta_data(self, new_meta_data: MetaData):
        self._meta_data = new_meta_data

        self.save()

    @property
    def result(self) -> Result:
        r = Session._get_redis()
        if r.get(f'{self.token.body}_result'):
            self._result = pickle.loads(r.get(f'{self.token.body}_result'))
        else:
            self._result = Result.new_result()

        return self._result

    @result.setter
    def result(self, new_result: Result):
        self._result = new_result

        self.save()

    def create_token(self):
        self.token = Token()
        r = Session._get_redis()
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

            r = Session._get_redis()
            data = r.get(token.body)
            if data is None:
                r.close()
                return Session()
            r.close()
            return Session(token)

        except jwt.exceptions.InvalidSignatureError:
            return Session()

    def save(self):
        r = Session._get_redis()
        r.set(f'{self.token.body}_meta_data', pickle.dumps(self._meta_data))
        r.set(f'{self.token.body}_result', pickle.dumps(self._result))
        r.expireat(
            f'{self.token.body}_meta_data',
            datetime.datetime.fromisoformat(f'{datetime.date.today() + datetime.timedelta(days=1)} 04:00:00'))
        r.expireat(
            f'{self.token.body}_result',
            datetime.datetime.fromisoformat(f'{datetime.date.today() + datetime.timedelta(days=1)} 04:00:00'))
        r.close()

    @staticmethod
    def _get_redis() -> redis.Redis:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    class DataEncoder(json.JSONEncoder):
        """
        Класс кодирует модель Session в JSON формат.
        """
        def default(self, obj):
            if isinstance(obj, Session):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)
