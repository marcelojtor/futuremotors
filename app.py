import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# =========================
# CONFIGURAÇÃO DO APP
# =========================
app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'

# Upload config
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Banco SQLite (pronto para migrar para PostgreSQL)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# MODELOS DO BANCO
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100))
    bateria = db.Column(db.String(100))
    ano = db.Column(db.String(10))
    chassi = db.Column(db.String(100))
    valor = db.Column(db.Float)
    cor = db.Column(db.String(50))
    autonomia = db.Column(db.String(50))
    velocidade = db.Column(db.String(50))
    imagem = db.Column(db.String(200))

# =========================
# CRIAR BANCO E USUÁRIO PADRÃO (CORRIGIDO)
# =========================
with app.app_context():
    db.create_all()

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if not User.query.filter_by(username='ADM').first():
        user = User(
            username='ADM',
            password=generate_password_hash('123456'),
            role='Administrador'
        )
        db.session.add(user)

    if not User.query.filter_by(username='ADM1').first():
        user2 = User(
            username='ADM1',
            password=generate_password_hash('123456'),
            role='Financeiro'
        )
        db.session.add(user2)

    db.session.commit()

# =========================
# ROTAS DE LOGIN
# =========================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Login inválido')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=session['user'], role=session['role'])

# =========================
# VENDAS
# =========================

@app.route('/vendas')
def vendas():
    if 'user' not in session:
        return redirect(url_for('login'))

    produtos = Product.query.all()
    return render_template('vendas.html', produtos=produtos)

# =========================
# PRODUTO
# =========================

@app.route('/produto/<int:id>')
def produto(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    produto = Product.query.get_or_404(id)
    return render_template('produto.html', produto=produto)

# =========================
# ESTOQUE (NOVA ROTA)
# =========================

@app.route('/estoque/cadastrar', methods=['GET', 'POST'])
def cadastrar_produto():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        modelo = request.form['modelo']
        bateria = request.form['bateria']
        ano = request.form['ano']
        chassi = request.form['chassi']
        valor = request.form['valor']
        cor = request.form['cor']
        autonomia = request.form['autonomia']
        velocidade = request.form['velocidade']

        imagem = request.files.get('imagem')
        caminho_imagem = None

        if imagem and imagem.filename != '':
            filename = secure_filename(imagem.filename)
            caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagem.save(caminho_imagem)

        novo_produto = Product(
            modelo=modelo,
            bateria=bateria,
            ano=ano,
            chassi=chassi,
            valor=float(valor),
            cor=cor,
            autonomia=autonomia,
            velocidade=velocidade,
            imagem='/' + caminho_imagem if caminho_imagem else None
        )

        db.session.add(novo_produto)
        db.session.commit()

        flash('Produto cadastrado com sucesso!')
        return redirect(url_for('vendas'))

    return render_template('cadastrar_produto.html')

# =========================
# PROTEÇÃO FINANCEIRO
# =========================

@app.route('/financeiro_login', methods=['GET', 'POST'])
def financeiro_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password) and user.username == 'ADM1':
            session['financeiro'] = True
            return redirect(url_for('financeiro'))
        else:
            flash('Acesso negado ao financeiro')

    return render_template('financeiro_login.html')

@app.route('/financeiro')
def financeiro():
    if not session.get('financeiro'):
        return redirect(url_for('financeiro_login'))

    return render_template('financeiro.html')

# =========================
# RODAR APP
# =========================

if __name__ == '__main__':
    app.run(debug=True)
