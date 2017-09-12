import os
from flask import Flask, session, url_for, redirect, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import bcrypt

app = Flask(__name__)
app.secret_key = "pepsecret"

# SQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    """Utente per il login sul sito dell'inventario."""
    __tablename__ = "website_users"

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    passwd = db.Column(db.LargeBinary)

    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd

    def __repr__(self):
        return "<User {}>".format(self.username, self.passwd)


class Ente(db.Model):
    """Ente (Unione Terre di Castelli, Comune di Vignola...)."""
    __tablename__ = "enti"

    eid = db.Column(db.Integer, primary_key=True)
    nomeente = db.Column(db.String)
    nomebreveente = db.Column(db.String)
    servizi = db.relationship("Servizio", backref='ente', lazy='dynamic')

    def __init__(self, nomeente, nomebreveente):
        self.nomeente = nomeente
        self.nomebreveente = nomebreveente

    def __repr__(self):
        return "<Ente {}>".format(self.nomebreveente)


class Servizio(db.Model):
    """Servizio di un ente (Anagrafe, Ufficio Scuola, Sindaco)."""
    __tablename__ = "servizi"

    sid = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('enti.eid'))
    nomeservizio = db.Column(db.String)
    locazione = db.Column(db.String)
    impiegati = db.relationship("Impiegato", backref='servizio', lazy='dynamic')

    def __init__(self, eid, nomeservizio, locazione):
        self.eid = eid
        self.nomeservizio = nomeservizio
        self.locazione = locazione

    def __repr__(self):
        return "<Servizio {}>".format(self.nomeservizio)


class Impiegato(db.Model):
    """Impiegato in uno dei servizi."""
    __tablename__ = "impiegati"

    iid = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('servizi.sid'))
    nomeimpiegato = db.Column(db.String)
    username = db.Column(db.String, unique=True)
    passwd = db.Column(db.String)
    dispositivi = db.relationship("Accesso", backref='impiegato', lazy='dynamic')

    def __init__(self, sid, nomeimpiegato, username, passwd):
        self.sid = sid
        self.nomeimpiegato = nomeimpiegato
        self.username = username
        self.passwd = passwd

    def __repr__(self):
        return "<Impiegato {}>".format(self.nome)


class Dispositivo(db.Model):
    """Dispositivo gestito dal CED registrato nell'inventario."""
    __tablename__ = "dispositivi"

    did = db.Column(db.Integer, primary_key=True)
    accessi = db.relationship("Accesso", backref='dispositivo', lazy='dynamic')
    tipo = db.Column(db.String)
    marca = db.Column(db.String)
    modello = db.Column(db.String)
    inv_ced = db.Column(db.String)
    inv_ente = db.Column(db.String)
    fornitore = db.Column(db.String)
    seriale = db.Column(db.String)
    nid = db.Column(db.Integer, db.ForeignKey('reti.nid'))
    rete = db.relationship("Rete", backref='dispositivi')

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
    """Tabella di associazione tra dispositivi e impiegati."""
    __tablename__ = "assoc_accessi"

    iid = db.Column(db.Integer, db.ForeignKey('impiegati.iid'), primary_key=True)
    did = db.Column(db.Integer, db.ForeignKey('dispositivi.did'), primary_key=True)

    def __init__(self, iid, did):
        self.iid = iid
        self.did = did

    def __repr__(self):
        return "<Accesso {} su {}>".format(self.iid, self.did)


class Rete(db.Model):
    """Configurazione di rete di uno o più computer."""
    __tablename__ = "reti"

    nid = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String)
    network_ip = db.Column(db.String, unique=True, nullable=False)
    subnet = db.Column(db.Integer, nullable=False)
    primary_dns = db.Column(db.String)
    secondary_dns = db.Column(db.String)

    def __init__(self, nome, network_ip, subnet, primary_dns, secondary_dns):
        self.nome = nome
        self.network_ip = network_ip
        self.subnet = subnet
        self.primary_dns = primary_dns
        self.secondary_dns = secondary_dns

    def __repr__(self):
        return "<Rete {},{}>".format(self.nid, self.nome)


class FakeAccesso:
    """Hackerino usato nel caso in cui non ci sia nessun impiegato assegnato a un dispositivo.
    Viva il duck typing!"""
    def __init__(self, dispositivo):
        self.did = dispositivo.did
        self.iid = None
        self.dispositivo = dispositivo

    def __getitem__(self, key):
        if key == 0:
            return self.dispositivo


# Funzioni del sito
def login(username, password):
    """Controlla se l'username e la password di un utente del sito sono corrette."""
    user = User.query.filter_by(username=username).first()
    return user is not None and bcrypt.checkpw(bytes(password, encoding="utf-8"), user.passwd)


def subnet_to_string(integer):
    """Converte una subnet mask in numero in una stringa"""
    still_int = (0xFFFFFFFF << (32 - integer)) & 0xFFFFFFFF
    return f"{still_int >> 24}.{(still_int >> 16) & 0xFF}.{(still_int >> 8)}.{still_int & 0xFF}"


# Sito
@app.route('/')
def page_home():
    """Pagina principale del sito:
    se non sei loggato reindirizza alla pagina del login,
    se sei loggato effettua il logout e dopo reindirizza al login"""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    else:
        session.pop('username')
        return redirect(url_for('page_login'))


@app.route('/login', methods=['GET', 'POST'])
def page_login():
    """Pagina di login:
    accetta richieste GET per la visualizzazione della pagina
    e richieste POST con form data per il login"""
    if request.method == 'GET':
        goldfish = url_for("static", filename="goldfish.png")
        return render_template("login.htm", goldfish=goldfish)
    else:
        if login(request.form['username'], request.form['password']):
            session['username'] = request.form['username']
            return redirect(url_for('page_dashboard'))
        else:
            abort(403)


@app.route('/dashboard')
def page_dashboard():
    """Dashboard del sito:
    Conteggia i servizi e visualizza la navbar
    Sì, è un po' inutile."""
    enti = Ente.query.all()
    conteggioservizi = dict()
    goldfish = url_for("static", filename="goldfish.png")
    for ente in enti:
        conteggioservizi[ente.nomeente] = Servizio.query.join(Ente).filter_by(eid=ente.eid).count()
    conteggioutenti = dict()
    for ente in enti:
        conteggioutenti[ente.nomeente] = Impiegato.query.join(Servizio).join(Ente).filter_by(eid=ente.eid).count()
    return render_template("dashboard.htm", type="main", user=session["username"],
                           conteggioutenti=conteggioutenti, conteggioservizi=conteggioservizi, goldfish=goldfish)


@app.route('/ente_add', methods=['GET', 'POST'])
def page_ente_add():
    """Pagina di creazione nuovo ente:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        return render_template("ente/add.htm", type="ente", user=session["username"])
    else:
        nuovoent = Ente(request.form['nomeente'], request.form['nomebreveente'])
        db.session.add(nuovoent)
        db.session.commit()
        return redirect(url_for('page_ente_list'))


@app.route('/ente_del/<int:eid>')
def page_ente_del(eid):
    """Pagina di cancellazione ente:
    accetta richieste GET per cancellare l'ente specificato."""
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
    """Pagina di elenco degli enti disponibili sul sito."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    enti = Ente.query.all()
    return render_template("ente/list.htm", enti=enti, type="ente", user=session["username"])


@app.route('/ente_show/<int:eid>', methods=['GET', 'POST'])
def page_ente_show(eid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        ente = Ente.query.get(eid)
        return render_template("ente/show.htm", ente=ente, user=session["username"])
    else:
        ente = Ente.query.get(eid)
        ente.nomeente = request.form["nomeente"]
        ente.nomebreveente = request.form["nomebreveente"]
        db.session.commit()
        return redirect(url_for('page_ente_list'))


@app.route('/serv_add', methods=['GET', 'POST'])
def page_serv_add():
    """Pagina di creazione nuovo servizio:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        enti = Ente.query.all()
        return render_template("servizio/add.htm", enti=enti, type="serv", user=session["username"])
    else:
        nuovoserv = Servizio(request.form['eid'], request.form['nomeservizio'], request.form['locazione'])
        db.session.add(nuovoserv)
        db.session.commit()
        return redirect(url_for('page_serv_list'))


@app.route('/serv_del/<int:sid>')
def page_serv_del(sid):
    """Pagina di cancellazione servizio:
    accetta richieste GET per cancellare il servizio specificato."""
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
    """Pagina di elenco dei servizi registrati sul sito."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    serv = Servizio.query.join(Ente).all()
    return render_template("servizio/list.htm", serv=serv, type="serv", user=session["username"])


@app.route('/serv_list/<int:eid>')
def page_serv_list_plus(eid):
    """Pagina di elenco dei servizi registrati sul sito, filtrati per ente."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    serv = Servizio.query.join(Ente).filter_by(eid=eid).all()
    return render_template("servizio/list.htm", serv=serv, type="serv", user=session["username"])


@app.route('/serv_show/<int:sid>', methods=['GET', 'POST'])
def page_serv_show(sid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        serv = Servizio.query.get(sid)
        enti = Ente.query.all()
        return render_template("servizio/show.htm", serv=serv, enti=enti, user=session["username"])
    else:
        serv = Servizio.query.get(sid)
        serv.eid = request.form["eid"]
        serv.nomeservizio = request.form["nomeservizio"]
        serv.locazione = request.form["locazione"]
        db.session.commit()
        return redirect(url_for('page_serv_list'))


@app.route('/imp_add', methods=['GET', 'POST'])
def page_imp_add():
    """Pagina di creazione nuovo impiegato:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        servizi = Servizio.query.join(Ente).all()
        return render_template("impiegato/add.htm", servizi=servizi, type="imp", user=session["username"])
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
    """Pagina di elenco degli impiegati registrati nell'inventario."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    impiegati = Impiegato.query.join(Servizio).join(Ente).all()
    return render_template("impiegato/list.htm", impiegati=impiegati, type="imp", user=session["username"])


@app.route('/imp_list/<int:sid>')
def page_imp_list_plus(sid):
    """Pagina di elenco degli impiegati registrati nell'inventario, filtrati per servizio."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    impiegati = Impiegato.query.join(Servizio).filter_by(sid=sid).join(Ente).all()
    return render_template("impiegato/list.htm", impiegati=impiegati, user=session["username"])


@app.route('/imp_show/<int:iid>', methods=['GET', 'POST'])
def page_imp_show(iid):
    """Pagina di cancellazione impiegato:
    accetta richieste GET per cancellare l'impiegato specificato."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == "GET":
        imp = Impiegato.query.get(iid)
        servizi = Servizio.query.all()
        return render_template("impiegato/show.htm", imp=imp, servizi=servizi, user=session["username"])
    else:
        imp = Impiegato.query.get(iid)
        imp.sid = request.form["sid"]
        imp.nomeimpiegato = request.form["nomeimpiegato"]
        imp.username = request.form["username"]
        imp.passwd = request.form["passwd"]
        db.session.commit()
        return redirect(url_for('page_imp_list'))


@app.route('/imp_details/<int:iid>')
def page_imp_details(iid):
    """Pagina dei dettagli di un impiegato"""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    impiegato = Impiegato.query.filter_by(iid=iid).first()
    return render_template("impiegato/details.htm", imp=impiegato, type="imp", user=session["username"])


@app.route('/disp_add', methods=['GET', 'POST'])
def page_disp_add():
    """Pagina di creazione nuovo dispositivo:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        serial = request.args.get("scanned_barcode")
        opzioni = ["Centralino", "Dispositivo generico di rete", "Marcatempo", "PC", "Portatile", "POS", "Router",
                   "Server", "Stampante di rete", "Switch", "Telefono IP", "Monitor", "Scanner", "Stampante locale"]
        reti = Rete.query.all()
        impiegati = Impiegato.query.all()
        return render_template("dispositivo/add.htm", impiegati=impiegati, opzioni=opzioni, reti=reti,
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
    """Pagina di cancellazione dispositivo:
    accetta richieste GET per cancellare il dispositivo specificato."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    disp = Dispositivo.query.get(did)
    db.session.delete(disp)
    db.session.commit()
    return redirect(url_for('page_disp_list'))


@app.route('/disp_list')
def page_disp_list():
    """Pagina di elenco dei dispositivi registrati nell'inventario."""
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
    return render_template("dispositivo/list.htm", accessi=accessi, type="disp", user=session["username"])


@app.route('/disp_details/<int:did>')
def page_disp_details(did):
    """Pagina di dettagli di un dispositivo, contenente anche gli utenti che vi hanno accesso."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    disp = Dispositivo.query.filter_by(did=did).first_or_404()
    accessi = Accesso.query.filter_by(did=did).all()
    return render_template("dispositivo/details.htm", disp=disp, accessi=accessi, type="disp",
                           user=session["username"])


@app.route('/net_add', methods=['GET', 'POST'])
def page_net_add():
    """Pagina di creazione nuova rete:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        return render_template("net/add.htm", type="net", user=session["username"])
    else:
        nuovonet = Rete(nome=request.form["nome"], network_ip=request.form["network_ip"], subnet=request.form["subnet"],
                        primary_dns=request.form["primary_dns"], secondary_dns=request.form["secondary_dns"])
        db.session.add(nuovonet)
        db.session.commit()
        return redirect(url_for('page_net_list'))


@app.route('/net_del/<int:nid>')
def page_net_del(nid):
    """Pagina di cancellazione rete:
    accetta richieste GET per cancellare la rete specificata."""
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
    return render_template("net/list.htm", reti=reti, type="net", user=session["username"])


@app.route('/net_details/<int:nid>')
def page_net_details(nid):
    if 'username' not in session:
        return redirect(url_for('page_login'))
    net = Rete.query.filter_by(nid=nid).first()
    dispositivi = Dispositivo.query.join(Rete).filter_by(nid=nid).all()
    subnet = subnet_to_string(net.subnet)
    return render_template("net/details.htm", net=net, subnet=subnet, dispositivi=dispositivi, type="net",
                           user=session["username"])


@app.route('/user_list')
def page_user_list():
    """Pagina di elenco degli utenti che possono connettersi al sito.
    Le password sono hashate."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    utenti = User.query.all()
    return render_template("user/list.htm", utenti=utenti, type="user", user=session["username"])


@app.route('/user_del/<int:uid>')
def page_user_del(uid):
    """Pagina di cancellazione impiegato:
    accetta richieste GET per cancellare l'utente specificato."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    utente = User.query.get(uid)
    db.session.delete(utente)
    db.session.commit()
    return redirect(url_for('page_user_list'))


@app.route('/user_add', methods=['GET', 'POST'])
def page_user_add():
    """Pagina di creazione nuovo utente del sito:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva.
    Le password vengono hashate con bcrypt."""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    if request.method == 'GET':
        return render_template("user/add.htm", type="user", user=session["username"])
    else:
        p = bytes(request.form["passwd"], encoding="utf-8")
        cenere = bcrypt.hashpw(p, bcrypt.gensalt())
        nuovo = User(request.form['username'], cenere)
        db.session.add(nuovo)
        db.session.commit()
        return redirect(url_for('page_user_list'))


if __name__ == "__main__":
    # Se non esiste il database, crealo e inizializzalo!
    if not os.path.isfile("data.db"):
        db.create_all()
        try:
            # L'utente predefinito è "stagista" "smecds".
            nuovapassword = bcrypt.hashpw(b"smecds", bcrypt.gensalt())
            nuovouser = User('stagista', nuovapassword)
            db.session.add(nuovouser)
            # Crea una rete nulla da utilizzare quando non ci sono altre reti disponibili
            retenulla = Rete(nome="Sconosciuta", network_ip="0.0.0.0", subnet=0, primary_dns="0.0.0.0",
                             secondary_dns="0.0.0.0")
            db.session.add(retenulla)
            db.session.commit()
        except IntegrityError:
            # Se queste operazioni sono già state compiute in precedenza, annullale
            db.session.rollback()
    # Esegui il sito in modalità debug
    app.run(debug=True)
