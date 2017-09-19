import os
from flask import Flask, session, url_for, redirect, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import bcrypt
import random

app = Flask(__name__)
app.secret_key = os.environ["flask_secret_key"]

# SQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    """Utente per il login sul sito dell'inventario."""
    __tablename__ = "website_users"

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    passwd = db.Column(db.LargeBinary, nullable=False)

    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd

    def __str__(self):
        return self.username

    def __repr__(self):
        return "<User {}>".format(self.username, self.passwd)


class Ente(db.Model):
    """Ente (Unione Terre di Castelli, Comune di Vignola...)."""
    __tablename__ = "enti"

    eid = db.Column(db.Integer, primary_key=True)
    nomeente = db.Column(db.String)
    nomebreveente = db.Column(db.String)
    servizi = db.relationship("Servizio", backref='ente', lazy='dynamic', cascade="delete")

    def __init__(self, nomeente, nomebreveente):
        self.nomeente = nomeente
        self.nomebreveente = nomebreveente

    def __str__(self):
        return self.nomeente

    def __repr__(self):
        return "<Ente {}>".format(self.nomebreveente)


class Servizio(db.Model):
    """Servizio di un ente (Anagrafe, Ufficio Scuola, Sindaco)."""
    __tablename__ = "servizi"

    sid = db.Column(db.Integer, primary_key=True)
    eid = db.Column(db.Integer, db.ForeignKey('enti.eid'))
    nomeservizio = db.Column(db.String)
    locazione = db.Column(db.String)
    impiegati = db.relationship("Impiegato", backref='servizio', lazy='dynamic', cascade="delete")

    def __init__(self, eid, nomeservizio, locazione):
        self.eid = eid
        self.nomeservizio = nomeservizio
        self.locazione = locazione

    def __str__(self):
        return self.nomeservizio

    def __repr__(self):
        return "<Servizio {}>".format(self.nomeservizio)


class Impiegato(db.Model):
    """Impiegato in uno dei servizi."""
    __tablename__ = "impiegati"

    iid = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('servizi.sid'))
    nomeimpiegato = db.Column(db.String)
    username = db.Column(db.String)
    passwd = db.Column(db.String)
    dispositivi = db.relationship("Accesso", backref='impiegato', lazy='dynamic', cascade="delete")

    def __init__(self, sid, nomeimpiegato, username, passwd):
        self.sid = sid
        self.nomeimpiegato = nomeimpiegato
        self.username = username
        self.passwd = passwd

    def __str__(self):
        return self.nomeimpiegato

    def __repr__(self):
        return "<Impiegato {}>".format(self.nomeimpiegato)


class Dispositivo(db.Model):
    """Dispositivo gestito dal CED registrato nell'inventario."""
    __tablename__ = "dispositivi"

    did = db.Column(db.Integer, primary_key=True)
    accessi = db.relationship("Accesso", backref='dispositivo', lazy='dynamic', cascade="delete")
    tipo = db.Column(db.String)
    marca = db.Column(db.String)
    modello = db.Column(db.String)
    inv_ced = db.Column(db.Integer, unique=True)
    inv_ente = db.Column(db.Integer, unique=True)
    fornitore = db.Column(db.String)
    seriale = db.Column(db.String)
    ip = db.Column(db.String)
    nid = db.Column(db.Integer, db.ForeignKey('reti.nid'))
    rete = db.relationship("Rete", backref='dispositivi')
    hostname = db.Column(db.String, unique=True)
    so = db.Column(db.String)

    def __init__(self, tipo, marca, modello, inv_ced, inv_ente, fornitore, nid, seriale, ip, hostname, so):
        self.tipo = tipo
        self.marca = marca
        self.modello = modello
        self.inv_ced = inv_ced
        self.inv_ente = inv_ente
        self.fornitore = fornitore
        self.nid = nid
        self.seriale = seriale
        self.ip = ip
        self.hostname = hostname
        self.so = so

    def __str__(self):
        if self.marca != "" and self.modello != "":
            return f"{self.marca} {self.modello}"
        elif self.hostname != "":
            return f"Dispositivo {self.hostname}"
        elif self.seriale != "":
            return f"Dispositivo {self.seriale}"
        else:
            return f"Dispositivo {self.did}"

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

    def __str__(self):
        return f"Rete {self.nome}"

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


class Pesce:
    """Un pesce? In un inventario!?"""
    def __init__(self, origin_obj, avgsize=1.0, variation=0.1, link="#"):
        self.name = str(origin_obj)
        self.size = random.gauss(avgsize, variation)
        self.color = "{:02x}".format(random.randrange(0, 16777216))
        self.position = (random.randrange(0, 1423), random.randrange(52, 600))
        self.link = link

    def __repr__(self):
        return f"<Pesce {self.name}, dimensioni {self.size}, colore #{self.color.hex()}>"


# Funzioni del sito
def login(username, password):
    """Controlla se l'username e la password di un utente del sito sono corrette."""
    user = User.query.filter_by(username=username).first()
    return user is not None and bcrypt.checkpw(bytes(password, encoding="utf-8"), user.passwd)


def subnet_to_string(integer):
    """Converte una subnet mask in numero in una stringa"""
    still_int = (0xFFFFFFFF << (32 - integer)) & 0xFFFFFFFF
    return f"{still_int >> 24}.{(still_int >> 16) & 0xFF}.{(still_int >> 8 & 0xFF)}.{still_int & 0xFF}"


# Sito
@app.route('/')
def page_home():
    """Pagina principale del sito:
    se non sei loggato reindirizza alla pagina del login,
    se sei loggato effettua il logout e dopo reindirizza al login"""
    if 'username' not in session:
        return redirect(url_for('page_login'))
    else:
        return redirect(url_for('page_dashboard'))


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
            session.permanent = request.form.get('remember')
            return redirect(url_for('page_dashboard'))
        else:
            return render_template('error.htm', error="Username o password non validi.")


@app.route('/logout')
def page_logout():
    """Pagina di logout:
    slogga l'utente se visitata"""
    if 'username' in session:
        session.pop('username')
    return redirect(url_for('page_login'))


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
    return render_template("dashboard.htm", pagetype="main", user=session.get("username"),
                           conteggioutenti=conteggioutenti, conteggioservizi=conteggioservizi, goldfish=goldfish)


@app.route('/ente_add', methods=['GET', 'POST'])
def page_ente_add():
    """Pagina di creazione nuovo ente:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva."""
    if 'username' not in session:
        return abort(403)
    if request.method == 'GET':
        return render_template("ente/show.htm", action="add", pagetype="ente", user=session.get("username"))
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
        return abort(403)
    ente = Ente.query.get_or_404(eid)
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
        return abort(403)
    enti = Ente.query.order_by(Ente.nomeente).all()
    return render_template("ente/list.htm", enti=enti, pagetype="ente", user=session.get("username"))


@app.route('/ente_show/<int:eid>', methods=['GET', 'POST'])
def page_ente_show(eid):
    if 'username' not in session:
        return abort(403)
    if request.method == "GET":
        ente = Ente.query.get_or_404(eid)
        return render_template("ente/show.htm", action="show", ente=ente, user=session.get("username"))
    else:
        ente = Ente.query.get_or_404(eid)
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
        return abort(403)
    if request.method == 'GET':
        enti = Ente.query.order_by(Ente.nomeente).all()
        return render_template("servizio/show.htm", action="add", enti=enti, pagetype="serv",
                               user=session.get("username"))
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
        return abort(403)
    serv = Servizio.query.get_or_404(sid)
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
        return abort(403)
    serv = Servizio.query.join(Ente).order_by(Ente.nomeente, Servizio.nomeservizio).all()
    return render_template("servizio/list.htm", serv=serv, pagetype="serv", user=session.get("username"))


@app.route('/serv_list/<int:eid>')
def page_serv_list_plus(eid):
    """Pagina di elenco dei servizi registrati sul sito, filtrati per ente."""
    if 'username' not in session:
        return abort(403)
    serv = Servizio.query.join(Ente).filter_by(eid=eid).order_by(Servizio.nomeservizio).all()
    return render_template("servizio/list.htm", serv=serv, pagetype="serv", user=session.get("username"))


@app.route('/serv_show/<int:sid>', methods=['GET', 'POST'])
def page_serv_show(sid):
    if 'username' not in session:
        return abort(403)
    if request.method == "GET":
        serv = Servizio.query.get_or_404(sid)
        enti = Ente.query.all()
        return render_template("servizio/show.htm", action="show", serv=serv, enti=enti, user=session.get("username"))
    else:
        serv = Servizio.query.get_or_404(sid)
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
        return abort(403)
    if request.method == 'GET':
        servizi = Servizio.query.join(Ente).order_by(Ente.nomeente, Servizio.nomeservizio).all()
        return render_template("impiegato/show.htm", action="add", servizi=servizi, pagetype="imp",
                               user=session.get("username"))
    else:
        nuovoimp = Impiegato(request.form['sid'], request.form['nomeimpiegato'], request.form['username'],
                             request.form['passwd'],)
        db.session.add(nuovoimp)
        db.session.commit()
        return redirect(url_for('page_imp_list'))


@app.route('/imp_del/<int:iid>')
def page_imp_del(iid):
    """Pagina di cancellazione impiegato:
    accetta richieste GET per cancellare l'impiegato specificato."""
    if 'username' not in session:
        return abort(403)
    imp = Impiegato.query.get_or_404(iid)
    db.session.delete(imp)
    db.session.commit()
    return redirect(url_for('page_imp_list'))


@app.route('/imp_list')
def page_imp_list():
    """Pagina di elenco degli impiegati registrati nell'inventario."""
    if 'username' not in session:
        return abort(403)
    impiegati = Impiegato.query.join(Servizio).join(Ente)\
        .order_by(Ente.nomeente, Servizio.nomeservizio, Impiegato.nomeimpiegato).all()
    return render_template("impiegato/list.htm", impiegati=impiegati, pagetype="imp", user=session.get("username"))


@app.route('/imp_list/<int:sid>')
def page_imp_list_plus(sid):
    """Pagina di elenco degli impiegati registrati nell'inventario, filtrati per servizio."""
    if 'username' not in session:
        return abort(403)
    impiegati = Impiegato.query.join(Servizio).filter_by(sid=sid).join(Ente).order_by(Impiegato.nomeimpiegato).all()
    return render_template("impiegato/list.htm", impiegati=impiegati, user=session.get("username"))


@app.route('/imp_show/<int:iid>', methods=['GET', 'POST'])
def page_imp_show(iid):
    if 'username' not in session:
        return abort(403)
    if request.method == "GET":
        imp = Impiegato.query.get_or_404(iid)
        servizi = Servizio.query.all()
        return render_template("impiegato/show.htm", action="show", imp=imp, servizi=servizi,
                               user=session.get("username"))
    else:
        imp = Impiegato.query.get_or_404(iid)
        imp.sid = request.form["sid"]
        imp.nomeimpiegato = request.form["nomeimpiegato"]
        imp.username = request.form["username"]
        imp.passwd = request.form["passwd"]
        db.session.commit()
        return redirect(url_for('page_imp_list'))


@app.route('/imp_details/<int:iid>')
def page_imp_details(iid):
    if 'username' not in session:
        return abort(403)
    imp = Impiegato.query.filter_by(iid=iid).join(Servizio).join(Ente).first_or_404()
    accessi = Accesso.query.filter_by(iid=imp.iid).join(Dispositivo).all()
    return render_template("impiegato/details.htm", accessi=accessi, impiegato=imp, user=session.get("username"))


@app.route('/disp_add', methods=['GET', 'POST'])
def page_disp_add():
    """Pagina di creazione nuovo dispositivo:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva."""
    if 'username' not in session:
        return abort(403)
    if request.method == 'GET':
        serial = request.args.get("scanned_barcode")
        opzioni = ["Centralino", "Dispositivo generico di rete", "Marcatempo", "PC", "Portatile", "POS", "Router",
                   "Server", "Stampante di rete", "Switch", "Telefono IP", "Monitor", "Scanner", "Stampante locale"]
        sistemi = [" ", "CentOS", "Fedora", "Open SUSE", "Red Hat", "Ubuntu", "Windows 10 x64", "Windows 2000",
                   "Windows 2003 server", "Windows 2007 server", "Windows 7", "Windows 8", "Windows 8.1", "Windows 98",
                   "Windows NT", "Windows Vista", "Windows XP", "Debian", "Altro"]
        reti = Rete.query.order_by(Rete.nome).all()
        impiegati = Impiegato.query.order_by(Impiegato.nomeimpiegato).all()
        return render_template("dispositivo/show.htm", action="add", impiegati=impiegati, opzioni=opzioni, reti=reti,
                               pagetype="dev", user=session.get("username"), serial=serial, sistemi=sistemi)
    else:
        if request.form["inv_ced"]:
            try:
                int(request.form["inv_ced"])
            except ValueError:
                return render_template("error.htm", error="Il campo Inventario CED deve contenere un numero.")
        if request.form["inv_ente"]:
            try:
                int(request.form["inv_ente"])
            except ValueError:
                return render_template("error.htm", error="Il campo Inventario ente deve contenere un numero.")
        nuovodisp = Dispositivo(request.form['tipo'], request.form['marca'], request.form['modello'],
                                int(request.form['inv_ced']) if request.form['inv_ced'] else None,
                                int(request.form['inv_ente']) if request.form['inv_ente'] else None,
                                request.form['fornitore'], request.form['rete'], request.form['seriale'],
                                request.form['ip'], request.form['hostname'], request.form['so'])
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
        return redirect(url_for('page_disp_list'))


@app.route('/disp_del/<int:did>')
def page_disp_del(did):
    """Pagina di cancellazione dispositivo:
    accetta richieste GET per cancellare il dispositivo specificato."""
    if 'username' not in session:
        return abort(403)
    disp = Dispositivo.query.get_or_404(did)
    for accesso in disp.accessi:
        db.session.delete(accesso)
    db.session.delete(disp)
    db.session.commit()
    return redirect(url_for('page_disp_list'))


@app.route('/disp_list')
def page_disp_list():
    """Pagina di elenco dei dispositivi registrati nell'inventario."""
    if 'username' not in session:
        return abort(403)
    accessi = list()
    dispositivi = Dispositivo.query.order_by(Dispositivo.inv_ced).all()
    for dispositivo in dispositivi:
        accesso = Accesso.query.join(Dispositivo).filter_by(did=dispositivo.did).join(Impiegato).all()
        if not accesso:
            # oh dio mio a cosa stavo pensando viva il duck typing
            accessi.append([FakeAccesso(dispositivo)])
        else:
            accessi.append(accesso)
    return render_template("dispositivo/list.htm", accessi=accessi, pagetype="disp", user=session.get("username"))


@app.route('/disp_details/<int:did>')
def page_disp_details(did):
    """Pagina di dettagli di un dispositivo, contenente anche gli utenti che vi hanno accesso."""
    if 'username' not in session:
        return abort(403)
    disp = Dispositivo.query.get_or_404(did)
    accessi = Accesso.query.filter_by(did=did).all()
    return render_template("dispositivo/details.htm", disp=disp, accessi=accessi, pagetype="disp",
                           user=session.get("username"))


@app.route('/disp_show/<int:did>', methods=['GET', 'POST'])
def page_disp_show(did):
    if 'username' not in session:
        return abort(403)
    if request.method == 'GET':
        disp = Dispositivo.query.get_or_404(did)
        accessi = Accesso.query.filter_by(did=did).all()
        impiegati = Impiegato.query.order_by(Impiegato.nomeimpiegato).all()
        opzioni = ["Centralino", "Dispositivo generico di rete", "Marcatempo", "PC", "Portatile", "POS", "Router",
                   "Server", "Stampante di rete", "Switch", "Telefono IP", "Monitor", "Scanner", "Stampante locale"]
        sistemi = [" ", "CentOS", "Fedora", "Open SUSE", "Red Hat", "Ubuntu", "Windows 10 x64", "Windows 2000",
                   "Windows 2003 server", "Windows 2007 server", "Windows 7", "Windows 8", "Windows 8.1", "Windows 98",
                   "Windows NT", "Windows Vista", "Windows XP", "Debian", "Altro"]
        reti = Rete.query.order_by(Rete.nome).all()
        return render_template("dispositivo/show.htm", action="show", dispositivo=disp, accessi=accessi,
                               impiegati=impiegati, pagetype="disp", user=session.get("username"), opzioni=opzioni,
                               reti=reti, sistemi=sistemi)
    else:
        disp = Dispositivo.query.get_or_404(did)
        accessi = Accesso.query.filter_by(did=did).all()
        if request.form["inv_ced"]:
            try:
                disp.inv_ced = int(request.form["inv_ced"])
            except ValueError:
                return render_template("error.htm", error="Il campo Inventario CED deve contenere un numero.")
        else:
            disp.inv_ced = None
        if request.form["inv_ente"]:
            try:
                disp.inv_ente = int(request.form["inv_ente"])
            except ValueError:
                return render_template("error.htm", error="Il campo Inventario ente deve contenere un numero.")
        else:
            disp.inv_ente = None
        disp.tipo = request.form['tipo']
        disp.marca = request.form['marca']
        disp.modello = request.form['modello']
        disp.fornitore = request.form['fornitore']
        disp.nid = int(request.form['rete'])
        disp.ip = request.form['ip']
        disp.hostname = request.form['hostname']
        disp.so = request.form['so']
        # Trova tutti gli utenti, edizione sporco hack in html
        users = list()
        while True:
            # Trova tutti gli utenti esistenti
            userstring = 'utente{}'.format(len(users))
            if userstring in request.form:
                users.append(request.form[userstring])
            else:
                break
        for accesso in accessi:
            db.session.delete(accesso)
        for user in users:
            nuovologin = Accesso(int(user), disp.did)
            db.session.add(nuovologin)
        db.session.commit()
        return redirect(url_for('page_disp_list'))


@app.route('/disp_clone/<int:did>', methods=['GET', 'POST'])
def page_disp_clone(did):
    if 'username' not in session:
        return abort(403)
    if request.method == 'GET':
        disp = Dispositivo.query.get_or_404(did)
        accessi = Accesso.query.filter_by(did=did).all()
        impiegati = Impiegato.query.order_by(Impiegato.nomeimpiegato).all()
        opzioni = ["Centralino", "Dispositivo generico di rete", "Marcatempo", "PC", "Portatile", "POS", "Router",
                   "Server", "Stampante di rete", "Switch", "Telefono IP", "Monitor", "Scanner", "Stampante locale"]
        sistemi = [" ", "CentOS", "Fedora", "Open SUSE", "Red Hat", "Ubuntu", "Windows 10 x64", "Windows 2000",
                   "Windows 2003 server", "Windows 2007 server", "Windows 7", "Windows 8", "Windows 8.1", "Windows 98",
                   "Windows NT", "Windows Vista", "Windows XP", "Debian", "Altro"]
        reti = Rete.query.order_by(Rete.nome).all()
        return render_template("dispositivo/show.htm", action="clone", dispositivo=disp, accessi=accessi,
                               impiegati=impiegati, pagetype="disp", user=session.get("username"), opzioni=opzioni,
                               reti=reti, sistemi=sistemi)
    else:
        if request.form["inv_ced"]:
            try:
                int(request.form["inv_ced"])
            except ValueError:
                return render_template("error.htm", error="Il campo Inventario CED deve contenere un numero.")
        if request.form["inv_ente"]:
            try:
                int(request.form["inv_ente"])
            except ValueError:
                return render_template("error.htm", error="Il campo Inventario ente deve contenere un numero.")
        nuovodisp = Dispositivo(request.form['tipo'], request.form['marca'], request.form['modello'],
                                int(request.form['inv_ced']) if request.form['inv_ced'] else None,
                                int(request.form['inv_ente']) if request.form['inv_ente'] else None,
                                request.form['fornitore'], request.form['rete'], request.form['seriale'],
                                request.form['ip'], request.form['hostname'], request.form['so'])
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
        return redirect(url_for('page_disp_list'))


@app.route('/net_add', methods=['GET', 'POST'])
def page_net_add():
    """Pagina di creazione nuova rete:
    come tutte le altre pagine di creazione del sito,
    accetta GET per visualizzare la pagina
    e POST con form data per l'aggiunta effettiva."""
    if 'username' not in session:
        return abort(403)
    if request.method == 'GET':
        return render_template("net/show.htm", action="add", pagetype="net", user=session.get("username"))
    else:
        try:
            int(request.form["subnet"])
        except ValueError:
            return render_template("error.htm", error="Il campo Subnet deve contenere il numero di bit della subnet. "
                                                      "(8, 16, 24...)")
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
        return abort(403)
    if Rete.query.count() <= 1:
        return render_template("error.htm", error="Non puoi cancellare l'ultima rete rimasta!")
    rete = Rete.query.get_or_404(nid)
    defaultrete = Rete.query.filter_by(network_ip="0.0.0.0").first()
    dispositivi = Dispositivo.query.filter_by(nid=rete.nid).all()
    for dispositivo in dispositivi:
        dispositivo.nid = defaultrete.nid
    db.session.delete(rete)
    db.session.commit()
    return redirect(url_for('page_net_list'))


@app.route('/net_list')
def page_net_list():
    if 'username' not in session:
        return abort(403)
    reti = Rete.query.order_by(Rete.nome).all()
    return render_template("net/list.htm", reti=reti, pagetype="net", user=session.get("username"))


@app.route('/net_details/<int:nid>')
def page_net_details(nid):
    if 'username' not in session:
        return abort(403)
    net = Rete.query.get_or_404(nid)
    dispositivi = Dispositivo.query.join(Rete).filter_by(nid=nid).all()
    subnet = subnet_to_string(net.subnet)
    return render_template("net/details.htm", net=net, subnet=subnet, dispositivi=dispositivi, pagetype="net",
                           user=session.get("username"))


@app.route('/net_show/<int:nid>', methods=['GET', 'POST'])
def page_net_show(nid):
    if 'username' not in session:
        return abort(403)
    if request.method == 'GET':
        net = Rete.query.filter_by(nid=nid).first_or_404()
        return render_template("net/show.htm", action="show", net=net, pagetype="net", user=session.get("username"))
    else:
        net = Rete.query.filter_by(nid=nid).first_or_404()
        net.nome = request.form['nome']
        net.network_ip = request.form['network_ip']
        net.subnet = request.form['subnet']
        net.primary_dns = request.form['primary_dns']
        net.secondary_dns = request.form['secondary_dns']
        db.session.commit()
        return redirect(url_for('page_net_list'))


@app.route('/user_list')
def page_user_list():
    """Pagina di elenco degli utenti che possono connettersi al sito.
    Le password sono hashate."""
    if 'username' not in session:
        return abort(403)
    utenti = User.query.order_by(User.username).all()
    return render_template("user/list.htm", utenti=utenti, pagetype="user", user=session.get("username"))


@app.route('/user_del/<int:uid>')
def page_user_del(uid):
    """Pagina di cancellazione impiegato:
    accetta richieste GET per cancellare l'utente specificato."""
    if 'username' not in session:
        return abort(403)
    if User.query.count() <= 1:
        return render_template("error.htm", error="Non puoi cancellare l'ultimo utente rimasto!")
    utente = User.query.get_or_404(uid)
    if utente.username == session["username"]:
        return render_template("error.htm", error="Non puoi cancellare l'utente con cui sei loggato!")
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
        return abort(403)
    if request.method == 'GET':
        return render_template("user/add.htm", pagetype="user", user=session.get("username"))
    else:
        p = bytes(request.form["passwd"], encoding="utf-8")
        cenere = bcrypt.hashpw(p, bcrypt.gensalt())
        nuovo = User(request.form['username'], cenere)
        db.session.add(nuovo)
        db.session.commit()
        return redirect(url_for('page_user_list'))


@app.route('/query', methods=['GET', 'POST'])
def page_query():
    """Pagina delle query manuali:
    in GET visualizza la pagina per fare una query,
    mentre in POST visualizza i risultati."""
    if 'username' not in session:
        return abort(403)
    if request.method == 'GET':
        return render_template("query.htm", user=session.get("username"), pagetype="query")
    else:
        try:
            result = db.engine.execute("SELECT" + request.form["query"] + ";")
        except Exception as e:
            return render_template("query.htm", query=request.form["query"], error=repr(e),
                                   user=session.get("username"), pagetype="query")
        return render_template("query.htm", query=request.form["query"], result=result, user=session.get("username"),
                               pagetype="query")


@app.route('/smecds')
def page_smecds():
    """Pagina che visualizza i credits del sito"""
    return render_template("smecds.htm", pagetype="main", user=session.get("username"))


@app.route('/pheesh')
def page_pheesh():
    """Acquario del sito.
    I pesci sono generati dinamicamente basandosi sui dati presenti nel database."""
    if 'username' not in session:
        return abort(403)
    enti = Ente.query.all()
    servizi = Servizio.query.all()
    impiegati = Impiegato.query.all()
    dispositivi = Dispositivo.query.all()
    reti = Rete.query.all()
    utenti = User.query.all()
    pesci = []
    for obj in enti:
        random.seed(hash(obj.nomeente))
        pesci.append(Pesce(obj, 3, 0.9, f"/ente_list"))
    for obj in servizi:
        random.seed(hash(obj.nomeservizio))
        pesci.append(Pesce(obj, 2, 0.5, f"/serv_list"))
    for obj in reti:
        random.seed(hash(obj.nome))
        pesci.append(Pesce(obj, 1.5, 0.4, f"/net_details/{obj.nid}"))
    for obj in impiegati:
        random.seed(hash(obj.nomeimpiegato))
        pesci.append(Pesce(obj, 1, 0.3, f"/imp_list"))
    for obj in dispositivi:
        random.seed(hash(obj.did))
        if obj.marca != "" and obj.modello != "":
            pesci.append(Pesce(obj, 0.8, 0.2, f"/disp_details/{obj.did}"))
        elif obj.seriale != "":
            pesci.append(Pesce(obj, 0.8, 0.2, f"/disp_details/{obj.did}"))
        else:
            pesci.append(Pesce(obj, 0.8, 0.2, f"/disp_details/{obj.did}"))
    for obj in utenti:
        random.seed(hash(obj.username))
        pesci.append(Pesce(obj, 1.5, 0.1, f"/user_list"))
    return render_template("pheesh.htm", user=session.get("username"), pheesh=pesci, footer=False)


@app.errorhandler(400)
def page_400(_):
    return render_template('400.htm', user=session.get("username"))


@app.errorhandler(403)
def page_403(_):
    return render_template('403.htm', user=session.get("username"))


@app.errorhandler(404)
def page_404(_):
    return render_template('404.htm', user=session.get("username"))


@app.errorhandler(500)
def page_500(e):
    return render_template('500.htm', e=e, user=session.get("username"))


if __name__ == "__main__":
    # Se non esiste il database, crealo e inizializzalo!
    if not os.path.isfile("db.sqlite"):
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
    app.run()
