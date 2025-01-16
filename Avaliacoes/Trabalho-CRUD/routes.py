import hashlib
from functools import wraps

from app import app, db
from flask import (flash, jsonify, redirect, render_template, request, session,
                   url_for)
from models.user_model import (AlunoModalidade, DetalhesUsuario, Modalidade,
                               Plano, Usuario)


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
        ##Verifica se o usuário está logado e se tem a flag de prof
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
@app.route('/cadastrar_aluno', methods=['GET'])
@professor_required
def cadastrar_aluno():
    planos = Plano.query.all()  # Recuperar todos os planos
    return render_template('cadastro.html', planos=planos)

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
        altura = request.form.get('altura') 
        peso = request.form.get('peso')      
        historico_doencas = request.form.get('historico_doencas')  
        historico_lesoes = request.form.get('historico_lesoes')    
        id_plano = request.form['id_plano'] 
        flag = request.form['flag']
        is_professor = 1 if flag == "professor" else 0

        
        #Criação do usuário na tabela `usuarios`
        try:
            usuario = Usuario(username="username_placeholder", senha_hash="hash_placeholder", is_professor=is_professor, id_plano=id_plano)
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
    show_user_fields = False

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

##Rota protegida para professores
@app.route('/modalidades')
@professor_required
def adicionar_modalidade():
    return render_template('modalidade.html')


##Rota protegida para professores
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

##Rota protegida para professores
@app.route('/vincular_modalidade', methods=['GET'])
@professor_required
def vincular_modalidade():
    ##Busc alunos com planos 2 ou 3
    alunos = (
    db.session.query(
        Usuario.id_usuario,
        DetalhesUsuario.nome,
        Plano.nome.label("plano_nome"),
        Usuario.is_professor  # Incluindo o campo is_professor na query
    )
    .join(DetalhesUsuario, Usuario.id_usuario == DetalhesUsuario.id_usuario)
    .join(Plano, Usuario.id_plano == Plano.id_plano)
    .filter(Usuario.id_plano.in_([2, 3]))
    .filter(Usuario.is_professor != 1)  # Filtrando apenas alunos
    .all()
)

    

    ##Buscar todas as modalidades
    modalidades = Modalidade.query.all()

    return render_template('gerencia_modal.html', alunos=alunos, modalidades=modalidades)


##Rota protegida para professores
@app.route('/gerenciar_modalidades', methods=['GET', 'POST'])
@professor_required
def gerenciar_modalidades():
    if request.method == 'POST':
        id_usuario = request.form.get('id_usuario')
        id_modalidade = request.form.get('id_modalidade')

        # Verificar se o aluno existe
        aluno = Usuario.query.filter_by(id_usuario=id_usuario, is_professor=False).first()
        if not aluno:
            flash("Aluno não encontrado ou inválido.", "danger")
            return redirect(url_for('vincular_modalidade'))

        # Verificar o plano do aluno
        if aluno.id_plano not in [2, 3]:
            flash("Este aluno não pode ser inscrito em modalidades devido ao plano.", "danger")
            return redirect(url_for('vincular_modalidade'))

        # Verificar limite de modalidades para o plano 2
        if aluno.id_plano == 2:
            qtd_modalidades = AlunoModalidade.query.filter_by(id_usuario=id_usuario).count()
            if qtd_modalidades >= 2:
                flash("Alunos com Plano 2 podem participar de no máximo 2 modalidades.", "danger")
                return redirect(url_for('vincular_modalidade'))

        # Verificar se a relação já existe
        relacao_existente = AlunoModalidade.query.filter_by(
            id_usuario=id_usuario, id_modalidade=id_modalidade
        ).first()
        if relacao_existente:
            flash("O aluno já está vinculado a esta modalidade.", "warning")
            return redirect(url_for('vincular_modalidade'))

        # Adicionar o aluno à modalidade
        nova_relacao = AlunoModalidade(id_usuario=id_usuario, id_modalidade=id_modalidade)
        db.session.add(nova_relacao)
        db.session.commit()

        flash("Aluno adicionado à modalidade com sucesso.", "success")
        return redirect(url_for('vincular_modalidade'))

    return render_template('gerencia_modal.html')


##Rota protegida para professores
@app.route('/remover_aluno_modalidade', methods=['POST'])
@professor_required
def remover_aluno_modalidade():
    data = request.get_json()  # Receber os dados como JSON
    id_usuario = data.get('id_usuario')
    id_modalidade = data.get('id_modalidade')

    # Buscar a relação específica entre o aluno e a modalidade
    relacao = AlunoModalidade.query.filter_by(id_usuario=id_usuario, id_modalidade=id_modalidade).first()
    if relacao:
        # Remover a relação do banco de dados
        db.session.delete(relacao)
        db.session.commit()
        return jsonify({"success": True, "message": "Aluno removido da modalidade com sucesso."}), 200
    else:
        return jsonify({"success": False, "message": "Erro ao tentar remover aluno."}), 400




##Rota protegida para professores
@app.route('/modalidades_vinculadas/<int:id_usuario>', methods=['GET'])
def modalidades_vinculadas(id_usuario):

    modalidades = (
        db.session.query(Modalidade.id_modalidade, Modalidade.nome)
        .join(AlunoModalidade, Modalidade.id_modalidade == AlunoModalidade.id_modalidade)
        .filter(AlunoModalidade.id_usuario == id_usuario)
        .all()
    )

    modalidades_list = [
        {"id_modalidade": modalidade.id_modalidade, "nome": modalidade.nome}
        for modalidade in modalidades
    ]

    
    return jsonify(modalidades_list)



@app.route('/aluno')
def aluno_home():
    
    id_username = session.get('username')

#informações do aluno
    aluno = db.session.query(
        Usuario.username,
        Usuario.id_usuario,
        DetalhesUsuario.nome,
        DetalhesUsuario.cpf,
        DetalhesUsuario.idade,
        DetalhesUsuario.altura,
        DetalhesUsuario.peso,
        DetalhesUsuario.telefone,
        DetalhesUsuario.historico_doencas,
        DetalhesUsuario.historico_lesoes,
        Plano.nome.label('plano_nome'),
        Plano.descricao.label('plano_descricao'),
        Plano.preco.label('plano_valor')
    ).join(DetalhesUsuario, Usuario.id_usuario == DetalhesUsuario.id_usuario).join(Plano, Usuario.id_plano == Plano.id_plano).filter(Usuario.username == id_username).first()

    print(id_username, aluno)
    # Verificar se o aluno existe
    if not aluno:
        return "Aluno não encontrado.", 404

    # Buscar modalidades do aluno
    # Buscar modalidades do aluno corretamente filtradas
    modalidades = (
        db.session.query(Modalidade.nome)
        .join(AlunoModalidade, Modalidade.id_modalidade == AlunoModalidade.id_modalidade)
        .filter(AlunoModalidade.id_usuario == aluno.id_usuario)  
        .all())


    # Renderizar a página com as informações
    return render_template(
        'aluno_home.html',
        aluno=aluno,
        modalidades=modalidades
    )

@app.route('/alunos')
def listar_alunos():
    # Obter todos os alunos do banco de dados
    alunos = db.session.query(
        DetalhesUsuario.nome,
        DetalhesUsuario.cpf,
        DetalhesUsuario.idade,
        DetalhesUsuario.telefone,
        Plano.nome.label('plano_nome')
    ).join(Usuario, DetalhesUsuario.id_usuario == Usuario.id_usuario).outerjoin(Plano, Usuario.id_plano == Plano.id_plano).filter(Usuario.is_professor == 0)  # Filtrar apenas alunos, não professores.all()

    # Renderizar o template com os dados dos alunos
    return render_template('listar_alunos.html', alunos=alunos)