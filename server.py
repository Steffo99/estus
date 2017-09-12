import os
from flask import Flask, session, url_for, redirect, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.secret_key = "pepsecret"

# SQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Utente login inventario
class User(db.Model):
    __tablename__ = "website_users"

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    passwd = db.Column(db.LargeBinary)

    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd

    def __repr__(self):
        return "<User {}>".format(self.username, self.passwd)


# Ente (Unione Terre di Castelli, Comune di Vignola...)
class Ente(db.Model):
    __tablename__ = "enti"

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
    __tablename__ = "servizi"

    sid = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('enti.eid'))
    nomeservizio = db.Column(db.String(128))
    locazione = db.Column(db.String(128))
    impiegati = db.relationship("Impiegato", backref='servizio', lazy='dynamic')

    def __init__(self, eid, nomeservizio, locazione):
        self.eid = eid
        self.nomeservizio = nomeservizio
        self.locazione = locazione

    def __repr__(self):
        return "<Servizio {}>".format(self.nomeservizio)


class Impiegato(db.Model):
    __tablename__ = "impiegati"

    iid = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('servizi.sid'))
    nomeimpiegato = db.Column(db.String(128))
    username = db.Column(db.String(32), unique=True)
    passwd = db.Column(db.String(32))
    dispositivi = db.relationship("Accesso", backref='impiegato', lazy='dynamic')

    def __init__(self, sid, nomeimpiegato, username, passwd):
        self.sid = sid
        self.nomeimpiegato = nomeimpiegato
        self.username = username
        self.passwd = passwd

    def __repr__(self):
        return "<Impiegato {}>".format(self.nome)


class Dispositivo(db.Model):
    __tablename__ = "dispositivi"

    did = db.Column(db.Integer, primary_key=True)
    accessi = db.relationship("Accesso", backref='dispositivo', lazy='dynamic')
    tipo = db.Column(db.String(32))
    marca = db.Column(db.String(64))
    modello = db.Column(db.String(32))
    inv_ced = db.Column(db.String(8))
    inv_ente = db.Column(db.String(8))
    fornitore = db.Column(db.String(64))
    nid = db.Column(db.Integer, db.ForeignKey('reti.nid'))
    rete = db.relationship("Rete", backref='dispositivi')
    seriale = db.Column(db.String(30))

    def __init__(self, tipo, marca, modello, inv_ced, inv_ente, fornitore, nid, seriale):
        self.tipo = tipo
        self.marca = marca
        self.modello = modello
        self.inv_ced = inv_ced
        self.inv_ente = inv_ente
        self.fornitore = fornitore
        self.nid = nid
        self.seriale = seriale

    def __repr__(self):
        return "<Dispositivo {}>".format(self.inv_ced)


class Accesso(db.Model):
    __tablename__ = "assoc_accessi"

    iid = db.Column(db.Integer, db.ForeignKey('impiegati.iid'), primary_key=True)
    did = db.Column(db.Integer, db.ForeignKey('dispositivi.did'), primary_key=True)

    def __init__(self, iid, did):
        self.iid = iid
        self.did = did

    def __repr__(self):
        return "<Accesso {} su {}>".format(self.iid, self.did)


class Rete(db.Model):
    __tablename__ = "reti"

    nid = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64))
    network_ip = db.Column(db.String(64), unique=True, nullable=False)
    subnet = db.Column(db.Integer, nullable=False)
    primary_dns = db.Column(db.String(64))
    secondary_dns = db.Column(db.String(64))

    def __init__(self, nome, network_ip, subnet, primary_dns, secondary_dns):
        self.nome = nome
        self.network_ip = network_ip
        self.subnet = subnet
        self.primary_dns = primary_dns
        self.secondary_dns = secondary_dns

    def __repr__(self):
        return "<Rete {},{}>".format(self.nid, self.nome)


class FakeAccesso:
    def __init__(self, dispositivo):
        self.did = dispositivo.did
        self.iid = None
        self.dispositivo = dispositivo

    def __getitem__(self, key):
        if key == 0:
            return self.dispositivo


# Funzioni del sito
def login(username, password):
    user = User.query.filter_by(username=username).first()
    try:
        return bcrypt.checkpw(bytes(password, encoding="utf-8"), user.passwd)
    except AttributeError:
        # Se non esiste l'Utente
        return False


def subnet_to_string(integer):
    """Converte una subnet mask in numero in una stringa"""
    still_int = (0xFFFFFFFF << (32 - integer)) & 0xFFFFFFFF
    return f"{still_int >> 24}.{(still_int >> 16) & 0xFF}.{(still_int >> 8)}.{still_int & 0xFF}"


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
        return render_template("login.htm", css=css, goldfish=goldfish)
    else:
        if login(request.form['username'], request.form['password']):
            session['username'] = request.form['username']
            return redirect(url_for('page_dashboard'))
        else:
            abort(403)


@app.route('/dashboard')
def page_dashboard():
    enti = Ente.query.all()
    conteggioservizi = dict()
    goldfish = url_for("static", filename="goldfish.png")
    for ente in enti:
        conteggioservizi[ente.nomeente] = Servizio.query.join(Ente).filter_by(eid=ente.eid).count()
    conteggioutenti = dict()
    for ente in enti:
        conteggioutenti[ente.nomeente] = Impiegato.query.join(Servizio).join(Ente).filter_by(eid=ente.eid).count()
    css = url_for("static", filename="style.css")
    return render_template("dashboard.htm", css=css, type="main", user=session["username"],
                           conteggioutenti=conteggioutenti, conteggioservizi=conteggioservizi, goldfish=goldfish)


@app.route('/ente_add', methods=['GET', 'POST'])
def page_ente_add():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        css = url_for("static", filename="style.css")
        return render_template("ente/add.htm", css=css, type="ente", user=session["username"])
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
    return render_template("ente/list.htm", css=css, enti=enti, type="ente", user=session["username"])


@app.route('/ente_show/<int:eid>', methods=['GET', 'POST'])
def page_ente_show(eid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        ente = Ente.query.get(eid)
        css = url_for("static", filename="style.css")
        return render_template("ente/show.htm", css=css, ente=ente, user=session["username"])
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
        return render_template("servizio/add.htm", css=css, enti=enti, type="serv", user=session["username"])
    else:
        nuovoserv = Servizio(request.form['eid'], request.form['nomeservizio'], request.form['locazione'])
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
    return render_template("servizio/list.htm", css=css, serv=serv, type="serv", user=session["username"])


@app.route('/serv_list/<int:eid>')
def page_serv_list_plus(eid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    serv = Servizio.query.join(Ente).filter_by(eid=eid).all()
    css = url_for("static", filename="style.css")
    return render_template("servizio/list.htm", css=css, serv=serv, type="serv", user=session["username"])


@app.route('/serv_show/<int:sid>', methods=['GET', 'POST'])
def page_serv_show(sid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        serv = Servizio.query.get(sid)
        enti = Ente.query.all()
        css = url_for("static", filename="style.css")
        return render_template("servizio/show.htm", css=css, serv=serv, enti=enti, user=session["username"])
    else:
        serv = Servizio.query.get(sid)
        serv.eid = request.form["eid"]
        serv.nomeservizio = request.form["nomeservizio"]
        serv.locazione = request.form["locazione"]
        db.session.commit()
        return redirect(url_for('page_serv_list'))


@app.route('/imp_add', methods=['GET', 'POST'])
def page_imp_add():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        servizi = Servizio.query.join(Ente).all()
        css = url_for("static", filename="style.css")
        return render_template("impiegato/add.htm", css=css, servizi=servizi, type="imp", user=session["username"])
    else:
        nuovoimp = Impiegato(request.form['sid'], request.form['nomeimpiegato'], request.form['username'],
                             request.form['passwd'],)
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
    return render_template("impiegato/list.htm", css=css, impiegati=impiegati, type="imp", user=session["username"])


@app.route('/imp_list/<int:sid>')
def page_imp_list_plus(sid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    impiegati = Impiegato.query.join(Servizio).filter_by(sid=sid).join(Ente).all()
    css = url_for("static", filename="style.css")
    return render_template("impiegato/list.htm", css=css, impiegati=impiegati, user=session["username"])


@app.route('/imp_show/<int:iid>', methods=['GET', 'POST'])
def page_imp_show(iid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        imp = Impiegato.query.get(iid)
        servizi = Servizio.query.all()
        css = url_for("static", filename="style.css")
        return render_template("impiegato/show.htm", css=css, imp=imp, servizi=servizi, user=session["username"])
    else:
        imp = Impiegato.query.get(iid)
        imp.sid = request.form["sid"]
        imp.nomeimpiegato = request.form["nomeimpiegato"]
        imp.username = request.form["username"]
        imp.passwd = request.form["passwd"]
        db.session.commit()
        return redirect(url_for('page_imp_list'))


@app.route('/disp_add', methods=['GET', 'POST'])
def page_disp_add():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        serial = request.args.get("scanned_barcode")
        opzioni = ["Centralino", "Dispositivo generico di rete", "Marcatempo", "PC", "Portatile", "POS", "Router",
                   "Server", "Stampante di rete", "Switch", "Telefono IP", "Monitor", "Scanner", "Stampante locale"]
        reti = Rete.query.all()
        impiegati = Impiegato.query.all()
        css = url_for("static", filename="style.css")
        return render_template("dispositivo/add.htm", css=css, impiegati=impiegati, opzioni=opzioni, reti=reti,
                               type="dev", user=session["username"], serial=serial)
    else:
        nuovodisp = Dispositivo(request.form['tipo'], request.form['marca'], request.form['modello'],
                                request.form['inv_ced'], request.form['inv_ente'], request.form['fornitore'],
                                request.form['rete'], request.form['seriale'])
        db.session.add(nuovodisp)
        db.session.commit()
        # Trova tutti gli utenti, edizione sporco hack in html
        users = list()
        while True:
            # Trova tutti gli utenti esistenti
            userstring = 'utente{}'.format(len(users))
            if userstring in request.form:
                users.append(request.form[userstring])
            else:
                break
        for user in users:
            nuovologin = Accesso(int(user), nuovodisp.did)
            db.session.add(nuovologin)
        db.session.commit()
        # TODO: se un dispositivo non ha utenti si incasina parecchio
        return redirect(url_for('page_disp_list'))


@app.route('/disp_del/<int:did>')
def page_disp_del(did):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    disp = Dispositivo.query.get(did)
    db.session.delete(disp)
    db.session.commit()
    return redirect(url_for('page_disp_list'))


@app.route('/disp_list')
def page_disp_list():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    accessi = list()
    dispositivi = Dispositivo.query.all()
    for dispositivo in dispositivi:
        accesso = Accesso.query.join(Dispositivo).filter_by(did=dispositivo.did).join(Impiegato).all()
        if not accesso:
            # oh dio mio a cosa stavo pensando viva il duck typing
            accessi.append([FakeAccesso(dispositivo)])
        else:
            accessi.append(accesso)
    css = url_for("static", filename="style.css")
    return render_template("dispositivo/list.htm", css=css, accessi=accessi, type="disp", user=session["username"])


@app.route('/disp_details/<int:did>')
def page_details_host(did):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    disp = Dispositivo.query.filter_by(did=did).first_or_404()
    accessi = Accesso.query.filter_by(did=did).all()
    css = url_for("static", filename="style.css")
    return render_template("dispositivo/details.htm", css=css, disp=disp, accessi=accessi, type="disp",
                           user=session["username"])


@app.route('/imp_details/<int:iid>')
def page_details_imp(iid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    impiegato = Impiegato.query.filter_by(iid=iid).first()
    css = url_for("static", filename="style.css")
    return render_template("impiegato/details.htm", css=css, imp=impiegato, type="imp", user=session["username"])


@app.route('/net_add', methods=['GET', 'POST'])
def page_net_add():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        css = url_for("static", filename="style.css")
        return render_template("net/add.htm", css=css, type="net", user=session["username"])
    else:
        nuovonet = Rete(nome=request.form["nome"], network_ip=request.form["network_ip"], subnet=request.form["subnet"],
                        primary_dns=request.form["primary_dns"], secondary_dns=request.form["secondary_dns"])
        db.session.add(nuovonet)
        db.session.commit()
        return redirect(url_for('page_net_list'))


@app.route('/net_del/<int:nid>')
def page_net_del(nid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    rete = Rete.query.get(nid)
    db.session.delete(rete)
    db.session.commit()
    return redirect(url_for('page_net_list'))


@app.route('/net_list')
def page_net_list():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    reti = Rete.query.all()
    css = url_for("static", filename="style.css")
    return render_template("net/list.htm", css=css, reti=reti, type="net", user=session["username"])


@app.route('/net_details/<int:nid>')
def page_net_details(nid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    net = Rete.query.filter_by(nid=nid).first()
    dispositivi = Dispositivo.query.join(Rete).filter_by(nid=nid).all()
    subnet = subnet_to_string(net.subnet)
    css = url_for("static", filename="style.css")
    return render_template("net/details.htm", css=css, net=net, subnet=subnet, dispositivi=dispositivi, type="net",
                           user=session["username"])


if __name__ == "__main__":
    if not os.path.isfile("data.db"):
        db.create_all()
        try:
            nuovapassword = bcrypt.hashpw(b"smecds", bcrypt.gensalt())
            nuovouser = User('stagista', nuovapassword)
            db.session.add(nuovouser)
            retenulla = Rete(nome="Sconosciuta", network_ip="0.0.0.0", subnet=0, primary_dns="0.0.0.0",
                             secondary_dns="0.0.0.0")
            db.session.add(retenulla)
            db.session.commit()
        except Exception:
            db.session.rollback()
    app.run(debug=True)
