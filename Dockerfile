FROM python:3.10.4

COPY . /app
WORKDIR /app

ENV BASE_DIR="/app/resources/"

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000
