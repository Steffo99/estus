from flask import Flask, session, url_for, redirect, request, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "pepsecret"

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

    def __init__(self, nomeente, nomebreveente):
        self.nomeente = nomeente
        self.nomebreveente = nomebreveente

    def __repr__(self):
        return "<Ente {}>".format(self.nomebreveente)


# Servizio di un ente
class Servizio(db.Model):
    sid = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('ente.eid'))
    nomeservizio = db.Column(db.String(128))
    impiegati = db.relationship("Impiegato", backref='servizio', lazy='dynamic')

    def __init__(self, eid, nomeservizio):
        self.eid = eid
        self.nomeservizio = nomeservizio

    def __repr__(self):
        return "<Servizio {}>".format(self.nomeservizio)


class Impiegato(db.Model):
    iid = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('servizio.sid'))
    nomeimpiegato = db.Column(db.String(128))
    username = db.Column(db.String(32), unique=True)
    passwd = db.Column(db.String(32))

    def __init__(self, sid, nomeimpiegato, username, passwd):
        self.sid = sid
        self.nomeimpiegato = nomeimpiegato
        self.username = username
        self.passwd = passwd

    def __repr__(self):
        return "<Impiegato {}>".format(self.nomeimpiegato)

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
    enti = Ente.query.all()
    conteggioservizi = dict()
    for ente in enti:
        conteggioservizi[ente.nomeente] = Servizio.query.join(Ente).filter_by(eid=ente.eid).count()
    conteggioutenti = dict()
    for ente in enti:
        conteggioutenti[ente.nomeente] = Impiegato.query.join(Servizio).join(Ente).filter_by(eid=ente.eid).count()
    css = url_for("static", filename="style.css")
    return render_template("dashboard.html.j2", css=css, type="main", user=session["username"], conteggioutenti=conteggioutenti, conteggioservizi=conteggioservizi)

@app.route('/ente_add', methods=['GET', 'POST'])
def page_ente_add():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        css = url_for("static", filename="style.css")
        return render_template("ente/add.html.j2", css=css, type="ente", user=session["username"])
    else:
        nuovoent = Ente(request.form['nomeente'], request.form['nomebreveente'])
        db.session.add(nuovoent)
        db.session.commit()
        return redirect(url_for('page_ente_list'))

@app.route('/ente_del/<int:eid>')
def page_ente_del(eid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    ente = Ente.query.get(eid)
    servizi = Servizio.query.filter_by(eid=ente.eid).all()
    for serv in servizi:
        impiegati = Impiegato.query.filter_by(sid=serv.sid).all()
        for imp in impiegati:
            db.session.delete(imp)
        db.session.delete(serv)
    db.session.delete(ente)
    db.session.commit()
    return redirect(url_for('page_ente_list'))

@app.route('/ente_list')
def page_ente_list():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    enti = Ente.query.all()
    css = url_for("static", filename="style.css")
    return render_template("ente/list.html.j2", css=css, enti=enti, type="ente", user=session["username"])

@app.route('/ente_show/<int:eid>', methods=['GET', 'POST'])
def page_ente_show(eid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        ente = Ente.query.get(eid)
        css = url_for("static", filename="style.css")
        return render_template("ente/show.html.j2", css=css, ente=ente, user=session["username"])
    else:
        ente = Ente.query.get(eid)
        ente.nomeente = request.form["nomeente"]
        ente.nomebreveente = request.form["nomebreveente"]
        db.session.commit()
        return redirect(url_for('page_ente_list'))

@app.route('/serv_add', methods=['GET', 'POST'])
def page_serv_add():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        enti = Ente.query.all()
        css = url_for("static", filename="style.css")
        return render_template("servizio/add.html.j2", css=css, enti=enti, type="serv", user=session["username"])
    else:
        nuovoserv = Servizio(request.form['eid'], request.form['nomeservizio'])
        db.session.add(nuovoserv)
        db.session.commit()
        return redirect(url_for('page_serv_list'))

@app.route('/serv_del/<int:sid>')
def page_serv_del(sid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    serv = Servizio.query.get(sid)
    impiegati = Impiegato.query.filter_by(sid=serv.sid).all()
    for imp in impiegati:
        db.session.delete(imp)
    db.session.delete(serv)
    db.session.commit()
    return redirect(url_for('page_serv_list'))

@app.route('/serv_list')
def page_serv_list():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    serv = Servizio.query.join(Ente).all()
    css = url_for("static", filename="style.css")
    return render_template("servizio/list.html.j2", css=css, serv=serv, type="serv", user=session["username"])

@app.route('/serv_list/<int:eid>')
def page_serv_list_plus(eid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    serv = Servizio.query.join(Ente).filter_by(eid=eid).all()
    css = url_for("static", filename="style.css")
    return render_template("servizio/list.html.j2", css=css, user=session["username"])

@app.route('/serv_show/<int:sid>', methods=['GET', 'POST'])
def page_serv_show(sid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        serv = Servizio.query.get(sid)
        enti = Ente.query.all()
        css = url_for("static", filename="style.css")
        return render_template("servizio/show.html.j2", css=css, serv=serv, enti=enti, user=session["username"])
    else:
        serv = Servizio.query.get(sid)
        serv.eid = request.form["eid"]
        serv.nomeservizio = request.form["nomeservizio"]
        db.session.commit()
        return redirect(url_for('page_serv_list'))

@app.route('/imp_add', methods=['GET', 'POST'])
def page_imp_add():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        servizi = Servizio.query.all()
        css = url_for("static", filename="style.css")
        return render_template("impiegato/add.html.j2", css=css, servizi=servizi, type="imp", user=session["username"])
    else:
        nuovoimp = Impiegato(request.form['sid'], request.form['nomeimpiegato'], request.form['username'], request.form['passwd'],)
        db.session.add(nuovoimp)
        db.session.commit()
        return redirect(url_for('page_imp_list'))

@app.route('/imp_del/<int:iid>')
def page_imp_del(iid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    imp = Impiegato.query.get(iid)
    db.session.delete(imp)
    db.session.commit()
    return redirect(url_for('page_imp_list'))

@app.route('/imp_list')
def page_imp_list():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    impiegati = Impiegato.query.join(Servizio).join(Ente).all()
    css = url_for("static", filename="style.css")
    return render_template("impiegato/list.html.j2", css=css, impiegati=impiegati, type="imp", user=session["username"])

@app.route('/imp_list/<int:sid>')
def page_imp_list_plus(sid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    impiegati = Impiegato.query.join(Servizio).filter_by(sid=sid).join(Ente).all()
    css = url_for("static", filename="style.css")
    return render_template("impiegato/list.html.j2", css=css, impiegati=impiegati, user=session["username"])

@app.route('/imp_show/<int:iid>', methods=['GET', 'POST'])
def page_imp_show(iid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        imp = Impiegato.query.get(iid)
        servizi = Servizio.query.all()
        css = url_for("static", filename="style.css")
        return render_template("impiegato/show.html.j2", css=css, imp=imp, servizi=servizi, user=session["username"])
    else:
        imp = Impiegato.query.get(iid)
        imp.sid = request.form["sid"]
        imp.nomeimpiegato = request.form["nomeimpiegato"]
        imp.username = request.form["username"]
        imp.passwd = request.form["passwd"]
        db.session.commit()
        return redirect(url_for('page_imp_list'))
