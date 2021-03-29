from app import app, add_courier_types
from data import db_session
from os.path import exists
from os import mkdir


if not exists('./db'):
    mkdir('./db')
db_session.global_init('db/base.db')
add_courier_types()

if __name__ == "__main__":
    app.run()
