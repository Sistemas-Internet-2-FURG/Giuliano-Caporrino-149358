import datetime
import os
from functools import wraps

import jwt
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mysqldb import MySQL

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')


mysql = MySQL(app)

# Função para verificar o token JWT
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Esperando "Bearer <token>"

        if not token:
            return jsonify({'message': 'Token de acesso é necessário'}), 403
        
        try:
            # Decodificando o token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except:
            return jsonify({'message': 'Token inválido'}), 403
        
        # Passando o user_id para a rota
        return f(current_user_id, *args, **kwargs)
    
    return decorated_function

# Função para gerar o token JWT
def gerar_token(user_id, tipo):
    token = jwt.encode({
        'user_id': user_id,
        'tipo': tipo,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Expira em 1 hora
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return token

# Criação das tabelas no banco de dados
with app.app_context():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS cursos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) UNIQUE
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            matricula VARCHAR(100) UNIQUE,
            tipo ENUM('aluno', 'professor') NOT NULL,
            curso_id INT,
            FOREIGN KEY (curso_id) REFERENCES cursos(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS disciplinas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100),
            professor_id INT,
            curso_id INT,
            FOREIGN KEY (professor_id) REFERENCES usuarios(id),
            FOREIGN KEY (curso_id) REFERENCES cursos(id)
        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS matriculas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            aluno_id INT,
            disciplina_id INT,
            FOREIGN KEY (aluno_id) REFERENCES usuarios(id),
            FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id)
        )''')

        mysql.connection.commit()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")
    finally:
        cursor.close()

# Rota de login
@app.route("/apirestful/login", methods=["POST"])
def login():
    data = request.get_json()
    nome = data['nome']
    matricula = data['matricula']
   
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE nome=%s AND matricula = %s", (nome, matricula,))
    usuario = cursor.fetchone()
    cursor.close()

    if usuario:
        # Gerando o token
        token = gerar_token(usuario[0], usuario[3])
        return jsonify({'message': 'Login bem-sucedido', 'token': token}), 200
    return jsonify({'message': 'Credenciais inválidas'}), 401

# Rota de logout
@app.route("/apirestful/logout", methods=["POST"])
@token_required
def logout(current_user_id):
    # Não há necessidade de uma ação explícita de logout em API com JWT, pois o token não é armazenado no servidor
    return jsonify({'message': 'Logout realizado com sucesso'}), 200

# **CRUD** de usuários:

# Cadastrar usuário
@app.route("/apirestful/usuarios", methods=["POST"])
@token_required
def cadastrar_usuario(current_user_id):
    data = request.get_json()
    nome = data['nome']
    matricula = data['matricula']
    tipo = data['tipo']
    curso_id = data['curso_id']
    
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, matricula, tipo, curso_id) VALUES (%s, %s, %s, %s)",
        (nome, matricula, tipo, curso_id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Usuário cadastrado com sucesso'}), 201

# Listar usuários
@app.route("/apirestful/usuarios", methods=["GET"])
@token_required
def listar_usuarios(current_user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, nome, matricula, tipo FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()

    return jsonify(usuarios), 200

# Atualizar usuário
@app.route("/apirestful/usuarios/<int:user_id>", methods=["PUT"])
@token_required
def atualizar_usuario(current_user_id, user_id):
    data = request.get_json()
    nome = data['nome']
    matricula = data['matricula']
    tipo = data['tipo']
    curso_id = data['curso_id']
    
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE usuarios SET nome = %s, matricula = %s, tipo = %s, curso_id = %s WHERE id = %s",
        (nome, matricula, tipo, curso_id, user_id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Usuário atualizado com sucesso'}), 200

# Deletar usuário
@app.route("/apirestful/usuarios/<int:user_id>", methods=["DELETE"])
@token_required
def deletar_usuario(current_user_id, user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200

# **CRUD** de cursos:

# Cadastrar curso
@app.route("/apirestful/cursos", methods=["POST"])
@token_required
def cadastrar_curso(current_user_id):
    data = request.get_json()
    nome = data['nome']
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO cursos (nome) VALUES (%s)", (nome,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Curso cadastrado com sucesso'}), 201

# Listar cursos
@app.route("/apirestful/cursos", methods=["GET"])
@token_required
def listar_cursos(current_user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, nome FROM cursos")
    cursos = cursor.fetchall()
    cursor.close()

    # Converte os resultados em uma lista de dicionários
    cursos_list = [{"id": curso[0], "nome": curso[1]} for curso in cursos]

    return jsonify(cursos_list), 200

# Atualizar curso
@app.route("/apirestful/cursos/<int:curso_id>", methods=["PUT"])
@token_required
def atualizar_curso(current_user_id, curso_id):
    data = request.get_json()
    nome = data['nome']
    
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE cursos SET nome = %s WHERE id = %s",
        (nome, curso_id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Curso atualizado com sucesso'}), 200

# Deletar curso
@app.route("/apirestful/cursos/<int:curso_id>", methods=["DELETE"])
@token_required
def deletar_curso(current_user_id, curso_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM cursos WHERE id = %s", (curso_id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Curso deletado com sucesso'}), 200

# **CRUD** de disciplinas:

# Cadastrar disciplina
@app.route("/apirestful/disciplinas", methods=["POST"])
@token_required
def cadastrar_disciplina(current_user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT tipo FROM usuarios WHERE id = %s", (current_user_id,))
    usuario = cursor.fetchone()

    if usuario[0] != 'professor':
        return jsonify({'message': 'Acesso negado. Apenas professores podem cadastrar disciplinas.'}), 403

    data = request.get_json()
    nome = data['nome']
    curso_id = data['curso_id']

    try:
        cursor.execute(
            "INSERT INTO disciplinas (nome, professor_id, curso_id) VALUES (%s, %s, %s)",
            (nome, current_user_id, curso_id)
        )
        mysql.connection.commit()
    except Exception as e:
        return jsonify({'message': f'Erro ao cadastrar disciplina: {str(e)}'}), 500
    finally:
        cursor.close()

    return jsonify({'message': 'Disciplina cadastrada com sucesso'}), 201

# Listar disciplinas
@app.route("/apirestful/disciplinas", methods=["GET"])
@token_required
def listar_disciplinas(current_user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT d.id, d.nome, u.nome AS professor, c.nome AS curso
                      FROM disciplinas d
                      JOIN usuarios u ON d.professor_id = u.id
                      JOIN cursos c ON d.curso_id = c.id''')
    disciplinas = cursor.fetchall()
    cursor.close()
    return jsonify(disciplinas), 200

# Atualizar disciplina
@app.route("/apirestful/disciplinas/<int:disciplina_id>", methods=["PUT"])
@token_required
def atualizar_disciplina(current_user_id, disciplina_id):
    data = request.get_json()
    nome = data['nome']
    curso_id = data['curso_id']
    
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE disciplinas SET nome = %s, curso_id = %s WHERE id = %s",
        (nome, curso_id, disciplina_id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Disciplina atualizada com sucesso'}), 200

# Deletar disciplina
@app.route("/apirestful/disciplinas/<int:disciplina_id>", methods=["DELETE"])
@token_required
def deletar_disciplina(current_user_id, disciplina_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM disciplinas WHERE id = %s", (disciplina_id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Disciplina deletada com sucesso'}), 200

# **CRUD** de matrículas:

# Cadastrar matrícula
@app.route("/apirestful/matriculas", methods=["POST"])
@token_required
def matricular_disciplina(current_user_id):
    data = request.get_json()
    disciplina_id = data['disciplina_id']
    
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO matriculas (aluno_id, disciplina_id) VALUES (%s, %s)",
        (current_user_id, disciplina_id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'Matrícula realizada com sucesso'}), 201
# Listar matrículas
@app.route("/apirestful/matriculas", methods=["GET"])
@token_required
def listar_matriculas(current_user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT m.id, u.nome AS aluno, c.nome AS curso, d.nome AS disciplina
                      FROM matriculas m
                      JOIN usuarios u ON m.aluno_id = u.id
                      JOIN cursos c ON u.curso_id = c.id
                      JOIN disciplinas d ON m.disciplina_id = d.id
                      WHERE m.aluno_id = %s''', (current_user_id,))
    matriculas = cursor.fetchall()
    cursor.close()

    return jsonify(matriculas), 200


# Atualizar matrícula
@app.route("/apirestful/matriculas/<int:id>", methods=["PUT"])
@token_required
def atualizar_matricula(current_user_id, id):
    data = request.get_json()
    nova_disciplina_id = data['disciplina_id']
    
    cursor = mysql.connection.cursor()
    
    # Verificar se a matrícula existe
    cursor.execute("SELECT * FROM matriculas WHERE id = %s AND aluno_id = %s", (id, current_user_id))
    matricula = cursor.fetchone()
    
    if not matricula:
        cursor.close()
        return jsonify({'message': 'Matrícula não encontrada ou você não tem permissão para atualizar'}), 404
    
    # Atualizar a matrícula
    cursor.execute("UPDATE matriculas SET disciplina_id = %s WHERE id = %s", (nova_disciplina_id, id))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'message': 'Matrícula atualizada com sucesso'}), 200

# Deletar matrícula
@app.route("/apirestful/matriculas/<int:id>", methods=["DELETE"])
@token_required
def deletar_matricula(current_user_id, id):
    cursor = mysql.connection.cursor()

    # Verificar se a matrícula existe
    cursor.execute("SELECT * FROM matriculas WHERE id = %s AND aluno_id = %s", (id, current_user_id))
    matricula = cursor.fetchone()
    
    if not matricula:
        cursor.close()
        return jsonify({'message': 'Matrícula não encontrada ou você não tem permissão para deletar'}), 404

    # Deletar a matrícula
    cursor.execute("DELETE FROM matriculas WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'message': 'Matrícula deletada com sucesso'}), 200

if __name__ == "__main__":
    app.run(debug=True)