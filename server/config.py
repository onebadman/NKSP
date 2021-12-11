import os

SECRET_FLASK = os.environ.get('SECRET_FLASK')
SECRET_JWT = os.environ.get('SECRET_JWT')

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get("REDIS_PORT")

SPACE = os.environ.get("SPACE")
