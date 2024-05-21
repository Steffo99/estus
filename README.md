<div align="center">

![](.media/icon-128x128_round.png)

# estus
Software inventario per il CED dell'[Unione Terre di Castelli](http://www.terredicastelli.mo.it/)

</div>

## Nuove funzioni rispetto all'inventario vecchio
- _Quasi_ responsivo
- Aggiunta nuovi dispositivi tramite codice a barre
- Semplificati o rimossi molti dei campi inutilizzati del vecchio inventario
- Innovativa e sperimentale modalità di visualizzazione dati dell'inventario: la **IttioVision** :fish:!
- Clona dispositivi per non dover rimettere gli stessi dati duecentomila volte

## Installazione
- Clonare il repository su un computer con installato Apache 2 utilizzando `git clone git@github.com:Steffo99/estus.git`.
- Eseguire `python3.6 server.py` per generare il database iniziale, poi terminarlo con Ctrl-C.
- Installare `mod_wsgi` per Python 3.6, aggiungendo [queste righe](https://stackoverflow.com/questions/44914961/install-mod-wsgi-on-ubuntu-with-python-3-6-apache-2-4-and-django-1-11) alla configurazione di Apache 2.
- Impostare la variabile di ambiente `flask_secret_key` a una qualsiasi stringa (serve per criptare i cookies della sessione)
- Seguire la guida [Deploying a Flask App](http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi).

Il login predefinito è `stagista` con password `smecds`, ma è possibile creare altri utenti nella pagina `/user_add` e anche eliminare l'utente predefinito dopo avere fatto il login con un utente diverso.

### Aggiornamenti
Per aggiornare all'ultima versione, _dovrebbe_ essere sufficiente eseguire `git pull` nella cartella dove è stato clonato il sito.

### HTTPS
Se volete utilizzare il protocollo HTTPS per le connessioni al sito, è possibile configurarlo velocemente utilizzando [Certbot](https://certbot.eff.org/).

## Sicurezza
Le password degli utenti del sito sono hashate e saltate con [bcrypt](https://it.wikipedia.org/wiki/Bcrypt).

## Configurazione Barcode Scanner
Per inserire dei dispositivi tramite codice a barre:

- Scaricare l'applicazione Android [Barcode Scanner](https://play.google.com/store/apps/details?id=com.google.zxing.client.android).
- Nelle impostazioni, immettere come URL ricerca personalizzata `https://estus.steffo.eu/disp_add?scanned_barcode=%s` (se su un dominio diverso, mettere il dominio corretto).
- Dopo aver scansionato un codice, cliccare il tasto Ricerca Personalizzata per eseguire l'immissione di un nuovo dispositivo.
