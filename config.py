#!/usr/bin/env python
import os

basedir = os.path.abspath(os.path.dirname(__file__))

TRUE_SYNONYMS = ('1', 'on', 'true', 'y', 'yes')


class Config:
    DEV_MODE = os.environ.get('DEV_MODE').lower() in TRUE_SYNONYMS
    SQLALCHEMY_COMMIT_ON_TEARDPWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_DEPLOYMENT_KEY = os.environ.get('DEPLOYMENT_KEY') or "recipoper secret"
    DEBUG = DEV_MODE
    ADMIN_IDS = tuple(int(id_) for id_ in os.environ["ADMIN_IDS"].split(",")) or tuple()
    TOKEN = os.environ.get('TOKEN')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "db/data.sqlite")}'
    SQLALCHEMY_DATABASE_ECHO = DEV_MODE
