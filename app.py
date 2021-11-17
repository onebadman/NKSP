import datetime
import json

from flask import Flask, render_template, session

from server.meta_data import MetaData, MenuTypes

app = Flask(__name__)
app.secret_key = 'd23f32f24f'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.permanent_session_lifetime = datetime.timedelta(hours=3)


def is_object_session(name):
    """
    Проверяет наличие объекта в сессии.
    :param name: имя объекта.
    :return: True, если объект есть в данных сессии,
             False, в противном случае.
    """

    if name in session:
        return True

    return False


def get_object_session(name):
    """
    Получает объект из данных сессии.
    :param name: имя объекта.
    :return: объект.
    """

    return session[name]


def set_object_session(name, value):
    """
    Добавляет объект в данные сессии.
    :param name: имя объекта.
    :param value: объект.
    """

    session[name] = value


def get_meta_data():
    """
    Получает мета данные пользователя сессии.
    :return: мета данные пользователя сессии.
    """

    if is_object_session('meta_data'):
        return MetaData(json.loads(get_object_session('meta_data')))
    else:
        meta_data = MetaData(None)

        set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

        return meta_data


@app.route('/')
def main():
    meta_data = get_meta_data()
    meta_data.set_active_menu(MenuTypes.MAIN)
    set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

    return render_template('main.html', meta_data=meta_data)


@app.route('/load')
def load():
    meta_data = get_meta_data()
    meta_data.set_active_menu(MenuTypes.LOAD)
    set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

    return render_template('load.html', meta_data=meta_data)


@app.route('/data')
def data():
    meta_data = get_meta_data()
    meta_data.set_active_menu(MenuTypes.DATA)
    set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

    return render_template('data.html', meta_data=meta_data)


@app.route('/answer')
def answer():
    meta_data = get_meta_data()
    meta_data.set_active_menu(MenuTypes.ANSWER)
    set_object_session('meta_data', json.dumps(meta_data, cls=MetaData.DataEncoder))

    return render_template('answer.html', meta_data=meta_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
