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
    nomeente = db.Column(db.String(64))
    nomebreveente = db.Column(db.String(16))
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
    nomeservizio = db.Column(db.String(128))
    impiegati = db.relationship("Impiegato", backref='servizio', lazy='dynamic')

    def __init__(self, eid, nome):
        self.eid = eid
        self.nome = nome

    def __repr__(self):
        return "<Servizio {}>".format(self.nome)


class Impiegato(db.Model):
    iid = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('servizio.sid'))
    nomeimpiegato = db.Column(db.String(128))
    username = db.Column(db.String(32), unique=True)
    passwd = db.Column(db.String(32))
    dispositivi = db.relationship("Accesso", backref='impiegato', lazy='dynamic')

    def __init__(self, sid, nome, username, passwd):
        self.sid = sid
        self.nome = nome
        self.username = username
        self.passwd = passwd

    def __repr__(self):
        return "<Impiegato {}>".format(self.nome)


class Dispositivo(db.Model):
    did = db.Column(db.Integer, primary_key=True)
    utenti = db.relationship("Accesso", backref='dispositivo', lazy='dynamic')
    tipo = db.Column(db.String(32))
    marca = db.Column(db.String(64))
    modello = db.Column(db.String(32))
    inv_ced = db.Column(db.String(8))
    inv_ente = db.Column(db.String(8))
    fornitore = db.Column(db.String(64))

    def __init__(self, tipo, marca, modello, inv_ced, inv_ente, fornitore
        self.tipo = tipo
        self.marca = marca
        self.modello = modello
        self.inv_ced = inv_ced
        self.inv_ente = inv_ente
        self.fornitore = fornitore

    def __repr__(self):
        return "<Dispositivo {}>".format(self.inv_ced)


class Accesso(db.Model):
    aid = db.Column(db.Integer, primary_key=True)
    iid = db.Column(db.Integer, db.ForeignKey('impiegato.iid'))
    did = db.Column(db.Integer, db.ForeignKey('dispositivo.did'))

    def __init__(self, iid, did):
        self.iid = iid
        self.did = did

    def __repr__(self):
        return "<Accesso {} su {}>".format(iid, did)

db.create_all()

nuovouser = User('stagista', 'smecds')
db.session.add(nuovouser)
nuovouser = User('gmacchi', 'steffo99')
db.session.add(nuovouser)
db.session.commit()
