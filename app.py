import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
 
app.secret_key = os.getenv('secret')

##Configrando a conexão com meu banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

import routes

if __name__ == '__main__':
    app.run(debug=True)
