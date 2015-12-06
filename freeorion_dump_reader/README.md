# Dump reader alpha

## Install
- PostgreSQL 9.0
- Install python dependencies
  - Django==1.9.0

- Setup path of game repo
    - navigate to `freeorion-utilities\freeorion_dump_reader\dump_reader\dump_reader\`
    - copy `user_settings_sample.py` to `user_settings.py`
    - set value for
       - `DUMP_FOLDER` that points to folder there dumps stored 
       - `PROJECT_FOLDER` that points to freeorion/default/ repository folder

## First run
-  create database `freeorion` in PostgreSQL
- navigate to `freeorion_dump_reader/`
- `python dump_reader/manage.py makemigrations reader`
- `python dump_reader/manage.py migrate`


## Run server
- navigate to `freeorion_dump_reader/`
- execute `python dump_reader/manage.py runserver`
- open `http://127.0.0.1:8000/` in browser
