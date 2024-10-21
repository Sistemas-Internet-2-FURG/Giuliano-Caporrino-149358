from flask import flash, redirect, render_template, request, session, url_for

from app import app, db
from models.user_model import Usuario


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Usuario.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            session['username'] = user.username
            print(session)
            return redirect(url_for('home'))
        else:
            print('Nome de usuário ou senha inválidos!')
            flash('Nome de usuário ou senha inválidos!')
    return render_template('login.html')


@app.route('/home')
def home():
    if 'username' not in session:
        print('user not in session')
        return redirect(url_for('login'))
    print('ok')
    return render_template('home.html', username=session['username'])


@app.route('/logout')
def logout():
    session.pop('username', None) 
    flash('Você saiu com sucesso.')
    return redirect(url_for('login'))
