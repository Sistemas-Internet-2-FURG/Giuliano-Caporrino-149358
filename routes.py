from app import app, db
from flask import flash, redirect, render_template, request, session, url_for
from models.user_model import Usuario


@app.route('/')
def index():
    return redirect(url_for('home'))

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
            return redirect(url_for('home'))
        else:
            print('Nome de usuário ou senha inválidos!')
            flash('Nome de usuário ou senha inválidos!')
    return render_template('login.html')


@app.route('/home')
def home():
    if not session.get('logged_in'):
        print('Por favor, faça login para continuar.', 'warning')
        return redirect(url_for('login'))

    return render_template('home.html', username=session['username'])


@app.route('/logout')
def logout():
    session.clear() 
    print('Você saiu com sucesso!', 'info')
    return redirect(url_for('login'))
