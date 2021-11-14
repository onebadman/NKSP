FROM python:3.8.6
COPY . /app
WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000
