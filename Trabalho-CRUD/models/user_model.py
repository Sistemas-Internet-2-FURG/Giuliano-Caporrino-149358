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
    id_plano = db.Column(db.Integer, db.ForeignKey('planos.id_plano'), nullable=True)
    
    
    def verify_password(self, password):
        # aux = hashlib.sha256(password.encode()).hexdigest()
        # print(aux)
        return self.senha_hash == hashlib.sha256(password.encode()).hexdigest()


class DetalhesUsuario(db.Model):
    __tablename__ = 'detalhes_usuarios'

    
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), primary_key=True)
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



class Modalidade(db.Model):
    __tablename__ = 'modalidades'

    id_modalidade = db.Column(db.Integer, primary_key=True, autoincrement=True)  # ID único da modalidade
    nome = db.Column(db.String(100), nullable=False, unique=True)  # Nome da modalidade, ex: "Yoga"
    descricao = db.Column(db.Text, nullable=True)  # Descrição da modalidade (opcional)
    criado_em = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)  # Data de criação



class Plano(db.Model):
    __tablename__ = 'planos'

    id_plano = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)

    #Relacionamento com a tabela de usuários
    usuarios = db.relationship('Usuario', backref='plano', lazy=True)


class AlunoModalidade(db.Model):
    __tablename__ = 'aluno_modalidades'

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario', ondelete='CASCADE'), nullable=False)
    id_modalidade = db.Column(db.Integer, db.ForeignKey('modalidades.id_modalidade', ondelete='CASCADE'), nullable=False)

    aluno = db.relationship('Usuario', backref='modalidades_relacionadas', lazy=True)
    modalidade = db.relationship('Modalidade', backref='alunos_relacionados', lazy=True)
