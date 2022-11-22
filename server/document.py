import io
import os

from docxtpl import DocxTemplate

from server.config import BASE_DIR
from server.meta_data import Mode


def escape_data(data: list):
    for i in range(len(data)):
        for j in range(len(data[0])):
            if data[i][j] is None:
                data[i][j] = ""
    return data


def render_table(mode: Mode, data: list):
    data = escape_data(data)

    input_file_name = "result_table.docx"
    path = os.path.join(BASE_DIR, "", input_file_name)

    template = DocxTemplate(path)

    headers = []
    if mode == Mode.MNM:
        headers = ['α', 'lks', '∑lks', 'ε', 'E', 'КСП', 'M', 'Ñ']
    elif mode == Mode.PIECEWISE_GIVEN:
        headers = ['α', 'lks', '∑lks', 'ε', 'Вектор срабатываний', 'E', 'КСП', 'M', 'Ñ']

    context = {
        'headers': headers,
        'data': data
    }

    template.render(context)

    file_stream = io.BytesIO()
    template.save(file_stream)
    file_stream.seek(0)

    return file_stream
