import io
import os
from typing import List

from docxtpl import DocxTemplate

from server.config import BASE_DIR
from server.lp import Pod
from server.meta_data import Mode


def escape_data(data: list):
    for i in range(len(data)):
        for j in range(len(data[0])):
            if data[i][j] is None:
                data[i][j] = ""
    return data


def render_table_dot(data: list, pods: List[Pod]):
    data_dot = []
    for pod in pods:
        data_dot.append([pod.r, f'{pod.r_dot}*' if pod.is_max else pod.r_dot])

    input_file_name = "result_table_dot.docx"
    path = os.path.join(BASE_DIR, "", input_file_name)

    template = DocxTemplate(path)

    context = {
        'headers': ['α', 'lks', 'L (∑lks)', 'ε', 'E', 'КСП', 'M', 'Ñ'],
        'data': data,
        'headers_dot': ['r', ''],
        'data_dot': data_dot
    }

    template.render(context)

    file_stream = io.BytesIO()
    template.save(file_stream)
    file_stream.seek(0)

    return file_stream


def render_table(mode: Mode, data: list, pods: List[Pod]):
    data = escape_data(data)

    if mode == Mode.IDEAL_DOT:
        return render_table_dot(data, pods)

    input_file_name = "result_table.docx"
    path = os.path.join(BASE_DIR, "", input_file_name)

    template = DocxTemplate(path)

    headers = []
    if mode == Mode.MNM:
        headers = ['α', 'lks', 'L (∑lks)', 'ε', 'E', 'КСП', 'M', 'Ñ']
    elif mode == Mode.PIECEWISE_GIVEN:
        headers = ['α', 'lks', 'L (∑lks)', 'ε', 'Вектор срабатываний', 'E', 'КСП', 'M', 'Ñ']
    elif mode == Mode.HMMCAO:
        headers = ['α', 'lks', 'L (∑lks)', 'ε', 'E', 'КСП', 'M', 'Ñ', 'P']
    else:
        raise Exception("Для используемого метода нет подходящего шаблона!")

    context = {
        'headers': headers,
        'data': data
    }

    template.render(context)

    file_stream = io.BytesIO()
    template.save(file_stream)
    file_stream.seek(0)

    return file_stream


def render_criteria(data: list):
    input_file_name = "result_criteria.docx"
    path = os.path.join(BASE_DIR, "", input_file_name)

    template = DocxTemplate(path)

    headers = ['Вариант модели', 'Е', 'K', 'Ǩ', 'L', 'Ñ', 'М', 'О', 'Z', 'H']

    context = {
        'headers': headers,
        'data': data
    }

    template.render(context)

    file_stream = io.BytesIO()
    template.save(file_stream)
    file_stream.seek(0)

    return file_stream
