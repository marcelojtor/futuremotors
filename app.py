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

# Banco SQLite
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# MODELOS
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

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100))
    servico = db.Column(db.String(200))
    data_entrada = db.Column(db.String(20))
    data_saida = db.Column(db.String(20))
    mao_obra = db.Column(db.Float)
    pecas = db.Column(db.String(200))
    valor_total = db.Column(db.Float)
    status = db.Column(db.String(50))

class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
    data = db.Column(db.String(20))

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(50))
    data_visita = db.Column(db.String(20))
    interesse = db.Column(db.String(100))
    observacoes = db.Column(db.String(300))

# NOVO MODEL MARKETING
class Marketing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor_investido = db.Column(db.Float)
    canal = db.Column(db.String(100))
    retorno = db.Column(db.Float)
    data = db.Column(db.String(20))

# =========================
# INIT BANCO
# =========================
with app.app_context():
    db.create_all()

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if not User.query.filter_by(username='ADM').first():
        db.session.add(User(
            username='ADM',
            password=generate_password_hash('123456'),
            role='Administrador'
        ))

    if not User.query.filter_by(username='ADM1').first():
        db.session.add(User(
            username='ADM1',
            password=generate_password_hash('123456'),
            role='Financeiro'
        ))

    db.session.commit()

# =========================
# LOGIN
# =========================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            session['user'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))

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

    return render_template('vendas.html', produtos=Product.query.all())

@app.route('/produto/<int:id>')
def produto(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('produto.html', produto=Product.query.get_or_404(id))

# =========================
# ESTOQUE
# =========================

@app.route('/estoque/cadastrar', methods=['GET', 'POST'])
def cadastrar_produto():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        imagem = request.files.get('imagem')
        caminho = None

        if imagem and imagem.filename:
            filename = secure_filename(imagem.filename)
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagem.save(caminho)

        produto = Product(
            modelo=request.form['modelo'],
            bateria=request.form['bateria'],
            ano=request.form['ano'],
            chassi=request.form['chassi'],
            valor=float(request.form['valor']),
            cor=request.form['cor'],
            autonomia=request.form['autonomia'],
            velocidade=request.form['velocidade'],
            imagem='/' + caminho if caminho else None
        )

        db.session.add(produto)
        db.session.commit()

        flash('Produto cadastrado!')
        return redirect(url_for('vendas'))

    return render_template('cadastrar_produto.html')

@app.route('/estoque')
def estoque():
    if 'user' not in session:
        return redirect(url_for('login'))

    filtro = request.args.get('modelo')

    if filtro:
        produtos = Product.query.filter(Product.modelo.like(f"%{filtro}%")).all()
    else:
        produtos = Product.query.all()

    return render_template('estoque.html', produtos=produtos)

# =========================
# OFICINA
# =========================

@app.route('/oficina')
def oficina():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template('oficina.html', servicos=Service.query.all())

@app.route('/oficina/entrada', methods=['GET', 'POST'])
def oficina_entrada():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        servico = Service(
            modelo=request.form['modelo'],
            servico=request.form['servico'],
            data_entrada=request.form['data_entrada'],
            data_saida=request.form['data_saida'],
            mao_obra=float(request.form['mao_obra']),
            pecas=request.form['pecas'],
            valor_total=float(request.form['valor_total']),
            status=request.form['status']
        )

        db.session.add(servico)
        db.session.commit()

        flash('Serviço registrado!')
        return redirect(url_for('oficina'))

    return render_template('oficina_entrada.html')

# =========================
# CLIENTES
# =========================

@app.route('/clientes')
def clientes():
    if 'user' not in session:
        return redirect(url_for('login'))

    lista = Client.query.all()
    return render_template('clientes.html', clientes=lista)

@app.route('/clientes/novo', methods=['GET', 'POST'])
def cliente_novo():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        cliente = Client(
            nome=request.form['nome'],
            endereco=request.form['endereco'],
            telefone=request.form['telefone'],
            data_visita=request.form['data_visita'],
            interesse=request.form['interesse'],
            observacoes=request.form['observacoes']
        )

        db.session.add(cliente)
        db.session.commit()

        flash('Cliente cadastrado!')
        return redirect(url_for('clientes'))

    return render_template('cliente_novo.html')

# =========================
# MARKETING (NOVO)
# =========================

@app.route('/marketing')
def marketing():
    if 'user' not in session:
        return redirect(url_for('login'))

    dados = Marketing.query.all()

    total_investido = sum(d.valor_investido for d in dados)
    total_retorno = sum(d.retorno for d in dados)
    lucro = total_retorno - total_investido

    return render_template(
        'marketing.html',
        dados=dados,
        investido=total_investido,
        retorno=total_retorno,
        lucro=lucro
    )

@app.route('/marketing/novo', methods=['GET', 'POST'])
def marketing_novo():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        registro = Marketing(
            valor_investido=float(request.form['valor_investido']),
            canal=request.form['canal'],
            retorno=float(request.form['retorno']),
            data=request.form['data']
        )

        db.session.add(registro)
        db.session.commit()

        flash('Campanha registrada!')
        return redirect(url_for('marketing'))

    return render_template('marketing_novo.html')

# =========================
# FINANCEIRO
# =========================

@app.route('/financeiro')
def financeiro():
    if not session.get('financeiro'):
        return redirect(url_for('financeiro_login'))

    dados = Finance.query.all()

    entradas = sum(d.valor for d in dados if d.tipo == 'entrada')
    saidas = sum(d.valor for d in dados if d.tipo == 'saida')
    saldo = entradas - saidas

    return render_template(
        'financeiro.html',
        dados=dados,
        entradas=entradas,
        saidas=saidas,
        saldo=saldo
    )

@app.route('/financeiro/novo', methods=['GET', 'POST'])
def financeiro_novo():
    if not session.get('financeiro'):
        return redirect(url_for('financeiro_login'))

    if request.method == 'POST':
        registro = Finance(
            tipo=request.form['tipo'],
            descricao=request.form['descricao'],
            valor=float(request.form['valor']),
            data=request.form['data']
        )

        db.session.add(registro)
        db.session.commit()

        flash('Registro financeiro adicionado!')
        return redirect(url_for('financeiro'))

    return render_template('financeiro_novo.html')

# =========================
# LOGIN FINANCEIRO
# =========================

@app.route('/financeiro_login', methods=['GET', 'POST'])
def financeiro_login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']) and user.username == 'ADM1':
            session['financeiro'] = True
            return redirect(url_for('financeiro'))

        flash('Acesso negado')

    return render_template('financeiro_login.html')

# =========================
# RUN
# =========================

if __name__ == '__main__':
    app.run(debug=True)
