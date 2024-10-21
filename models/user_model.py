import hashlib

from app import db


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False) 

    def verify_password(self, password):
        # aux = hashlib.sha256(password.encode()).hexdigest()
        # print(aux)
        return self.senha_hash == hashlib.sha256(password.encode()).hexdigest()

