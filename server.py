from flask import Flask, render_template, request, url_for, session, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'itsapepperonisecret'

# SQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)

# Utente login inventario
class User(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    passwd = db.Column(db.String(80))

    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd

    def __repr__(self):
        return "<User {}>".format(self.username, self.passwd)

# Ente (Unione Terre di Castelli, Comune di Vignola...)
class Ente(db.Model):
    eid = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64))
    nomebreve = db.Column(db.String(16))
    servizi = db.relationship("Servizio", backref='ente', lazy='dynamic')

    def __init__(self, nome, nomebreve):
        self.nome = nome
        self.nomebreve = nomebreve

    def __repr__(self):
        return "<Ente {}>".format(self.nomebreve)


# Servizio di un ente
class Servizio(db.Model):
    sid = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('ente.eid'))
    nome = db.Column(db.String(128))
    impiegati = db.relationship("Impiegato", backref='servizio', lazy='dynamic')

    def __init__(self, eid, nome):
        self.eid = eid
        self.nome = nome

    def __repr__(self):
        return "<Servizio {}>".format(self.nome)


class Impiegato(db.Model):
    iid = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('servizio.sid'))
    nome = db.Column(db.String(128))
    username = db.Column(db.String(32), unique=True)
    passwd = db.Column(db.String(32))

    def __init__(self, sid, nome, username, passwd):
        self.sid = sid
        self.nome = nome
        self.username = username
        self.passwd = passwd

    def __repr__(self):
        return "<Impiegato {}>".format(self.nome)

# Funzioni del sito
def login(username, password):
    user = User.query.filter_by(username=username).first()
    return password == user.passwd

# Sito
@app.route('/')
def page_home():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    else:
        session.pop('username')
        return "Logout eseguito con successo."

@app.route('/login', methods=['GET', 'POST'])
def page_login():
    if request.method == 'GET':
        css = url_for("static", filename="style.css")
        goldfish = url_for("static", filename="goldfish.png")
        return render_template("login.html.j2", css=css, goldfish=goldfish)
    else:
        if login(request.form['username'], request.form['password']):
            session['username'] = request.form['username']
            return redirect(url_for('page_dashboard'))
        else:
            return "Errore."

@app.route('/dashboard')
def page_dashboard():
    return "Buongiornissimo {}".format(session['username'])

@app.route('/ente_add', methods=['GET', 'POST'])
def page_ente_add():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        # Visualizza la pagina di creazione ente
        css = url_for("static", filename="style.css")
        return render_template("ente_add.html.j2", css=css)
    else:
        # Crea un nuovo ente
        nuovoent = Ente(request.form['nome'], request.form['nomebreve'])
        db.session.add(nuovoent)
        db.session.commit()
        return redirect(url_for('page_ente_list'))

@app.route('/ente_del/<int:eid>')
def page_ente_del(eid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    ente = Ente.query.get(eid)
    db.session.delete(ente)
    db.session.commit()
    return redirect(url_for('page_ente_list'))

@app.route('/ente_list')
def page_ente_list():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    enti = Ente.query.all()
    css = url_for("static", filename="style.css")
    return render_template("ente_list.html.j2", css=css, enti=enti)

@app.route('/ente_show/<int:eid>', methods=['GET', 'POST'])
def page_ente_show(eid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        ente = Ente.query.get(eid)
        css = url_for("static", filename="style.css")
        return render_template("ente_show.html.j2", css=css, ente=ente)
    else:
        ente = Ente.query.get(eid)
        ente.nome = request.form["nome"]
        ente.nomebreve = request.form["nomebreve"]
        db.session.commit()
        return redirect(url_for('page_ente_list'))
