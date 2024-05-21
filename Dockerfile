FROM python:3

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD [ "python", "./server.py" ]

LABEL org.opencontainers.image.title="estus"
LABEL org.opencontainers.image.description="Software inventario per il CED dell'Unione Terre di Castelli"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.url="https://github.com/Steffo99/estus"
LABEL org.opencontainers.image.authors="Stefano Pigozzi <me@steffo.eu>, Lorenzo Balugani <lorenzo.balugani@gmail.com>"
