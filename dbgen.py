from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

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

db.create_all()

nuovouser = User('Snake', 'v3n0m')
db.session.add(nuovouser)
db.session.commit()
