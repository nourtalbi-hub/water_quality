from flask_sqlalchemy import SQLAlchemy

# Instance unique de SQLAlchemy partagée dans toute l'application.
# Pourquoi ici ? Pour éviter les imports circulaires :
# si db est dans __init__.py, les autres fichiers qui importent db
# doivent importer depuis __init__.py qui importe depuis eux → boucle infinie.
db = SQLAlchemy()