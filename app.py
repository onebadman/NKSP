import datetime
import os

import pytz as pytz
from flask import Flask, render_template, session, request, redirect, url_for, send_file, send_from_directory

from server.lp import Data, LpSolve
from server.meta_data import MenuTypes
from server.session import Session
from server.document import render_table
from server.config import SECRET_FLASK, SPACE


app = Flask(__name__)
app.secret_key = SECRET_FLASK
ALLOWED_EXTENSIONS = set(['txt'])
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.permanent_session_lifetime = datetime.timedelta(days=1)


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


def allowed_file(filename):
    """
    Проверяет соответствие расширений файлов к разрешённым.
    :param filename: имя загруженного файла.
    :return: True, если файл соответствует маске,
             False, если файл не соответствует маске.
    """

    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def get_session():
    """
    Получает кастомную сущность сессии. Если токен протух, то создает новый.
    Все токены протухаю в 4:00 +08 UTC.
    """

    if is_object_session('token'):
        s = Session.get_session(get_object_session('token'))
        set_object_session('token', s.token.body)
        return s
    return Session()


def save_session(_session: Session):
    set_object_session('token', _session.token.body)


@app.route('/')
def main():
    """
    Формирует основную страницу.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.MAIN)

    _session.meta_data = meta_data
    return render_template('main.html', meta_data=meta_data)


@app.route('/load', methods=['GET'])
def load_get():
    """
    Формирует страницу для загрузки исходных данных.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.LOAD)

    _session.meta_data = meta_data
    return render_template('load.html', meta_data=meta_data)


@app.route('/load', methods=['POST'])
def load_post():
    """
    Обрабатывает загрузку файла с исходными данными.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.LOAD)

    file = request.files['file']
    if file and allowed_file(file.filename):
        _list = []
        for line in file.stream.readlines():
            _list.append(list(map(float, line.decode('utf-8').split())))
        file.close()
        meta_data.load_data = _list
        del _list

    _session.meta_data = meta_data
    return render_template('load.html', meta_data=meta_data)


@app.route('/data', methods=["GET"])
def data_get():
    """
    Формирует страницу с загруженными данными.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.DATA)

    _session.meta_data = meta_data
    return render_template('data.html', meta_data=meta_data)


@app.route('/answer')
def answer():
    """
    Формирует страницу с результатами вычислений.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.ANSWER)

    result = LpSolve(Data(meta_data)).result

    _session.meta_data = meta_data
    _session.result = result

    return render_template('answer.html', meta_data=meta_data, result=result)


@app.route('/form/data', methods=["POST"])
def form_data():
    """
    Обрабатывает форму setData в шаблоне data.html.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_data(request.form)

    _session.meta_data = meta_data
    return redirect(url_for('answer'))


@app.route('/form/load_result', methods=["POST"])
def form_load_result():
    _session = get_session()
    save_session(_session)

    result = _session.result
    file_stream = render_table(result.print())

    return send_file(
        file_stream,
        as_attachment=True,
        download_name=f'result_'
                      f'{datetime.datetime.now(pytz.timezone("Asia/Irkutsk")).strftime("%Y-%m-%d_%H-%M-%S")}'
                      f'.docx')


@app.route('/form/update_r', methods=['POST'])
def form_update_r():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.update_r(request.form)

    _session.meta_data = meta_data
    return redirect(url_for('answer'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    if SPACE == 'dev':
        app.run(host='0.0.0.0', debug=True)
    else:
        from waitress import serve

        serve(app, host="0.0.0.0", port=5000)
