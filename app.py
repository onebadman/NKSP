import datetime
import os

import pytz as pytz
from flask import Flask, render_template, session, request, redirect, url_for, send_file, send_from_directory

from server.criteria import Criteria
from server.lp import Data, LpSolve, LpIdealDot
from server.meta_data import MenuTypes, Mode, AppType
from server.session import Session
from server.document import render_table, render_criteria
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


def read_file(file):
    if file and allowed_file(file.filename):
        _list = []
        for line in file.stream.readlines():
            _list.append(list(map(float, line.decode('utf-8').split())))
        file.close()
        return _list


@app.route('/')
def main():
    """
    Формирует основную страницу.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.MAIN)
    meta_data.set_active_app(AppType.NSKP)

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
    meta_data.set_active_app(AppType.NSKP)

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
    meta_data.set_active_app(AppType.NSKP)

    file = request.files['file']

    meta_data.load_data = read_file(file)

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
    meta_data.set_active_app(AppType.NSKP)

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
    meta_data.set_active_app(AppType.NSKP)

    if meta_data.mode is Mode.IDEAL_DOT:
        return _ideal_dot_task(meta_data, _session)
    else:
        return _lp_task(meta_data, _session)


@app.route('/criteria', methods=["GET"])
def criteria_get():
    """
    Формирует страницу для вычисления критериев.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.CRITERIA)
    meta_data.set_active_app(AppType.CRITERIA)

    _session.meta_data = meta_data

    if 'criteria' in meta_data.__dict__:
        return render_template('criteria.html', meta_data=meta_data, data_criteria=meta_data.criteria.results.to_print())

    return render_template('criteria.html', meta_data=meta_data)


@app.route('/criteria', methods=['POST'])
def criteria_post():
    """
    Обрабатывает загрузку файла с исходными данными для расчета критериев.
    """

    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_active_menu(MenuTypes.CRITERIA)
    meta_data.set_active_app(AppType.CRITERIA)

    file = request.files['file']

    meta_data.criteria_data = read_file(file)

    meta_data.criteria = Criteria(meta_data.criteria_data)

    _session.meta_data = meta_data
    return redirect(url_for('criteria_get'))


def _lp_task(meta_data, _session):
    result = LpSolve(meta_data.mode, Data(meta_data)).result

    _session.meta_data = meta_data
    _session.result = result

    return render_template('answer.html', meta_data=meta_data, result=result)


def _ideal_dot_task(meta_data, _session):
    result = LpIdealDot(Data(meta_data)).pre_result

    meta_data.r = result.r
    _session.meta_data = meta_data
    _session.result = result.result

    return render_template('answer.html', meta_data=meta_data, result=result.result, pods=result.pods_)


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
    file_stream = render_table(_session.meta_data.mode, result.print(), result.pods)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name=f'result_'
                      f'{datetime.datetime.now(pytz.timezone("Asia/Irkutsk")).strftime("%Y-%m-%d_%H-%M-%S")}'
                      f'.docx')


@app.route('/form/load_criteria_result', methods=["POST"])
def form_load_criteria_result():
    _session = get_session()
    save_session(_session)

    file_stream = render_criteria(_session.meta_data.criteria.results.to_print())

    return send_file(
        file_stream,
        as_attachment=True,
        download_name=f'criteria_'
                      f'{datetime.datetime.now(pytz.timezone("Asia/Irkutsk")).strftime("%Y-%m-%d_%H-%M-%S")}'
                      f'.docx')


@app.route('/form/update_params', methods=['POST'])
def form_update_params():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.update_params(request.form)

    _session.meta_data = meta_data
    return redirect(url_for('answer'))


@app.route('/form/change-mode', methods=['POST'])
def form_change_mode():
    _session = get_session()
    save_session(_session)

    meta_data = _session.meta_data
    meta_data.set_mode(request.form)

    _session.meta_data = meta_data
    return redirect(url_for('data_get'))


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
