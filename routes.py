import hashlib
from functools import wraps

from app import app, db
from flask import flash, redirect, render_template, request, session, url_for
from models.user_model import DetalhesUsuario, Modalidade, Usuario


@app.route('/')
def index():
    return redirect(url_for('role'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Usuario.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            session['username'] = user.username
            session['logged_in'] = True
            print(session)
            return redirect(url_for('role'))
        else:
            print('Nome de usuário ou senha inválidos!')
            flash('Nome de usuário ou senha inválidos!')
    return render_template('login.html')

@app.route('/role')
def role():
    if not session.get('logged_in'):
        print('Por favor, faça login para continuar.', 'warning')
        return redirect(url_for('login'))
    return render_template('select_role.html')


@app.route('/logout')
def logout():
    session.clear() 
    print('Você saiu com sucesso!', 'info')
    return redirect(url_for('login'))



##Decorador para verificar se o usuário é professor/funcionario
def professor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #Verifica se o usuário está logado e se tem a flag de prof
        if 'username' not in session:
            flash("Por favor, faça login para acessar essa página.", "error")
            return redirect(url_for('login'))
        
        user = Usuario.query.filter_by(username=session['username']).first()
        if not user or not user.is_professor:
            print("Você não tem permissão para acessar esta página.", "error")
            return redirect(url_for('role')) 
        
        return f(*args, **kwargs)
    return decorated_function


##Página protegida para professores
@app.route('/home')
@professor_required
def home():
    return render_template('home.html', username=session.get('username'))

##Página protegida para professores
@app.route('/cadastrar_aluno')
@professor_required
def cadastrar_aluno():
    # Lógica para cadastrar novo aluno
    return render_template('cadastro.html')

##Rota protegida para professores
@app.route('/criar_aluno', methods=['GET', 'POST'])
@professor_required
def criar_aluno():
    if request.method == 'POST':
        #DATA
        nome = request.form['nome']
        cpf = request.form['cpf']
        idade = request.form['idade']
        telefone = request.form['telefone']
        altura = request.form.get('altura')  # Opcional
        peso = request.form.get('peso')      # Opcional
        historico_doencas = request.form.get('historico_doencas')  # Opcional
        historico_lesoes = request.form.get('historico_lesoes')    # Opcional
        
        #Criação do usuário na tabela `usuarios`
        try:
            usuario = Usuario(username="username_placeholder", senha_hash="hash_placeholder", is_professor=0)
            db.session.add(usuario)
            db.session.flush()  

            #Criação dos detalhes na tabela `detalhes_usuarios`
            detalhes = DetalhesUsuario(
                id_usuario=usuario.id_usuario,
                nome=nome,
                cpf=cpf,
                idade=idade,
                telefone=telefone,
                altura=altura if altura else None,
                peso=peso if peso else None,
                historico_doencas=historico_doencas if historico_doencas else None,
                historico_lesoes=historico_lesoes if historico_lesoes else None
            )
            db.session.add(detalhes)
            db.session.commit()
            flash("Aluno cadastrado com sucesso!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar aluno: {e}", "danger")
            return render_template('cadastrar_aluno.html')
    return render_template('cadastrar_aluno.html')






@app.route('/primeiro_login', methods=['GET', 'POST'])
def primeiro_login():
    show_user_fields = False  #Flag deocultar os campos de username e senha

    if request.method == 'POST':
        cpf = request.form.get('cpf')

        ##Verificar se o CPF existe e está vinculado aos placeholders
        usuario_detalhes = (
            db.session.query(Usuario)
            .join(DetalhesUsuario, Usuario.id_usuario == DetalhesUsuario.id_usuario)
            .filter(DetalhesUsuario.cpf == cpf)
            .filter(Usuario.username == "username_placeholder", Usuario.senha_hash == "hash_placeholder")
            .first()
        )

        if not usuario_detalhes:
            flash('CPF não encontrado ou já registrado.', 'danger')
            return render_template('primeiro_login.html', show_user_fields=False)

        #-Se o CPF foi validado e os placeholders existem
        if 'valid_user' not in request.form:
            #-CPF válido, exibir campos de username e senha
            flash('CPF válido. Configure seu username e senha.', 'success')
            return render_template('primeiro_login.html', show_user_fields=True, cpf=cpf)

        #-Etapa 2: Atualizar o username e senha
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('primeiro_login.html', show_user_fields=True, cpf=cpf)

        ##Atualizar o banco de dados
        usuario_detalhes.username = username
        usuario_detalhes.senha_hash = hashlib.sha256(new_password.encode()).hexdigest()
        db.session.commit()

        flash('Dados registrados com sucesso! Faça login com seu novo username.', 'success')
        return redirect(url_for('login'))

    return render_template('primeiro_login.html', show_user_fields=False)




@app.route('/listar-modalidades', methods=['GET'])
def listar_modalidades():
    modalidades = Modalidade.query.all()
    return render_template('listar_modalidades.html', modalidades=modalidades)


@app.route('/modalidades')
@professor_required
def adicionar_modalidade():
    return render_template('modalidade.html')



@app.route('/criar_modalidade', methods=['GET', 'POST'])
@professor_required
def criar_modalidade():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao', '')

        if not nome:
            flash('O campo Nome é obrigatório.', 'danger')
            return render_template('criar_modalidade.html')

        try:
            nova_modalidade = Modalidade(nome=nome, descricao=descricao)
            db.session.add(nova_modalidade)
            db.session.commit()
            flash('Modalidade criada com sucesso!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar modalidade: {e}', 'danger')

    return render_template('criar_modalidade.html')















@app.route('/aluno')
def aluno_home():
    #dados fictícios
    aluno_data = {
        'aluno_nome': 'João Silva',
        'plano': 'Plano Acesso Geral',
        'modalidades': 'Musculação, Natação, Yoga',
        'validade_plano': '31/12/2024',
        'treinos': 'Treino A, Treino B'
    }
    return render_template('aluno_home.html', **aluno_data)














#TODO: FURTURAS FUNÇÕES

@app.route('/alunos')
def listar_alunos():
    #listar alunos
    return "Página para listar alunos."



@app.route('/alunos/vincular_modalidade')
def vincular_modalidade():
    #vincular modalidades ao aluno
    return "Página para vincular modalidades ao aluno."


