import hashlib

from app import db


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    is_professor = db.Column(db.Boolean, nullable=False, default=False)  
    
    def verify_password(self, password):
        # aux = hashlib.sha256(password.encode()).hexdigest()
        # print(aux)
        return self.senha_hash == hashlib.sha256(password.encode()).hexdigest()


class DetalhesUsuario(db.Model):
    __tablename__ = 'detalhes_usuarios'

    id_detalhes = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)  
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    telefone = db.Column(db.String(15), nullable=False)
    altura = db.Column(db.Float, nullable=True)  # Opcional
    peso = db.Column(db.Float, nullable=True)    # Opcional
    historico_doencas = db.Column(db.Text, nullable=True)  # Opcional
    historico_lesoes = db.Column(db.Text, nullable=True)   # Opcional

    ##Relacionamento com a tabela `usuarios`
    usuario = db.relationship('Usuario', backref=db.backref('detalhes', lazy=True))
