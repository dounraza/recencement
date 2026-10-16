from flask import Flask,session, render_template, url_for, redirect,request,flash,Response,send_file,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect as sqlalchemy_inspect, text as sqlalchemy_text
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from os.path import splitext, basename
from werkzeug.utils import secure_filename
import base64
import urllib
import sys
import openpyxl
from openpyxl import Workbook,load_workbook
import os,io
import pytz
from urllib.request import urlopen
from model_api.CppApi import LoginResource,ProtectedResource,InvoiceCpp,RapportMyCpp
from Configuration import Configuration
from model_api.CppApi import  generate_pdf
from run_program import run_program
from run_versement import run_versement
from CppEsper import CppEsper
from versement import Versement
from main import main
from datetime import date,datetime,timedelta
import json,time
import random
import string
import rarfile
from PIL import Image
import shutil
import requests
import subprocess
import mysql.connector
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import model_api.CppApi
from apscheduler.schedulers.blocking import BlockingScheduler
from flask_restful import Resource, Api
# from tkinter import filedialog
# import tkinter
import threading

from dotenv import dotenv_values
import signal
import datetime
app = Flask(__name__)
api = Api(app)
jwt = JWTManager(app)
cnf= Configuration()

  
config = dotenv_values(".env")

# config = dotenv_values("c:/wamp64/www/extract/cpptransportextract/.env")
url=config['APP_URL']
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.Integer, nullable=False)
    full_name = db.Column(db.String(10000), nullable=False)
    env = db.Column(db.Integer, nullable=False)
    
class Cooperatives(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255))
    variance = db.Column(db.Integer)


class RecensementProprietaire(db.Model):
    __tablename__ = 'recensement_proprietaires'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    telephone = db.Column(db.String(40))
    cin = db.Column(db.String(60))
    adresse = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class RecensementChauffeur(db.Model):
    __tablename__ = 'recensement_chauffeurs'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    prenom = db.Column(db.String(120))
    telephone = db.Column(db.String(40))
    cin = db.Column(db.String(60))
    adresse = db.Column(db.String(255))
    type_permis = db.Column(db.String(60))
    annee_experience = db.Column(db.Integer)
    image = db.Column(db.String(255))
    permis_images = db.Column(db.Text)
    sync_status = db.Column(db.String(20), default='pending', nullable=False)
    sync_error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @property
    def images(self):
        try:
            return json.loads(self.permis_images or '{}')
        except (TypeError, ValueError):
            return {}


class RecensementVehicule(db.Model):
    """Fiche locale de recensement d'un véhicule et de son propriétaire."""
    __tablename__ = 'recensement_vehicules'

    id = db.Column(db.Integer, primary_key=True)
    plaque = db.Column(db.String(40), nullable=False, unique=True)
    marque = db.Column(db.String(80), nullable=False)
    modele = db.Column(db.String(80))
    annee = db.Column(db.String(4))
    couleur = db.Column(db.String(40))
    capacite_places = db.Column(db.Integer)
    a_des_publicites = db.Column(db.Boolean, default=False, nullable=False)
    transport_national = db.Column(db.Boolean, default=False, nullable=False)
    sync_status = db.Column(db.String(20), default='pending', nullable=False)
    sync_error = db.Column(db.Text)
    mysql_owner_id = db.Column(db.Integer)
    mysql_vehicle_id = db.Column(db.String(191))
    synced_at = db.Column(db.DateTime)
    chauffeur_nom = db.Column(db.String(120))
    chauffeur_prenom = db.Column(db.String(120))
    chauffeur_telephone = db.Column(db.String(40))
    chauffeur_cin = db.Column(db.String(60))
    chauffeur_type_permis = db.Column(db.String(60))
    chauffeur_annee_experience = db.Column(db.Integer)
    chauffeur_image = db.Column(db.String(255))
    chauffeur_permis_images = db.Column(db.Text)
    proprietaire_nom = db.Column(db.String(120), nullable=False)
    proprietaire_telephone = db.Column(db.String(40))
    proprietaire_cin = db.Column(db.String(60))
    proprietaire_adresse = db.Column(db.String(255))
    cooperative = db.Column(db.String(120))
    image = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @property
    def images(self):
        """Retourne les photos par vue, avec compatibilité avec l'ancien champ image."""
        try:
            metadata = json.loads(self.notes or '{}')
            if isinstance(metadata, dict) and isinstance(metadata.get('images'), dict):
                return metadata['images']
        except (TypeError, ValueError):
            pass
        try:
            values = json.loads(self.image or '{}')
            return values if isinstance(values, dict) else {'devant': self.image}
        except (TypeError, ValueError):
            return {'devant': self.image} if self.image else {}

    @property
    def chauffeur_images(self):
        try:
            values = json.loads(self.chauffeur_permis_images or '{}')
            return values if isinstance(values, dict) else {}
        except (TypeError, ValueError):
            return {}


VEHICLE_BRANDS = [
    'Mercedes Sprinter', 'Mercedes 207', 'Mercedes 307',
    'Mercedes 308', 'Mercedes 309', 'Mercedes 410',
    'Toyota Hiace', 'Toyota Coaster', 'Mazda Bongo', 'Mazda E-Series',
    'Mazda Eclipse', 'Peugeot J5', 'Peugeot Boxer', 'Renault Trafic',
    'Renault Master', 'Hyundai H-1 / Starex', 'Volkswagen Crafter',
    'Iveco Daily', 'Nissan Caravan / Urvan', 'Isuzu', 'Autre'
]
class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')




@app.route('/login', methods=['GET', 'POST'])
def login():
    profilepic_filename = os.path.join("static","cppsystem.jpg")
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form,image=profilepic_filename)
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    
    role=current_user.role
    full_name=current_user.full_name
    createDirectoryFile()
    session['role'] = role
    session['name'] = full_name
    return render_template('dashboard.html',role=role,name=full_name)


def envoyer_photos_recensement(fiche):
    """Organise les cinq vues du véhicule dans Seafile et retourne leurs références."""
    basic = config.get('TOKEN_SEAFILE')
    url_seafile = config.get('URL_SEAFILE_PRO') or config.get('URL_SEAFILE')
    if not basic or not url_seafile:
        return {}

    plaque = fiche.plaque.replace(' ', '')
    cnf.createDirectory(basic, url_seafile, plaque)
    cnf.createDirectory(basic, url_seafile, 'GALERY', plaque)
    token = cnf.getTokenSeafile(basic, url_seafile)
    if not token:
        raise RuntimeError('Token Seafile indisponible')

    references = []
    for vue, nom_fichier in fiche.images.items():
        fichier_local = os.path.join(app.root_path, 'static', 'vehicle_uploads', nom_fichier)
        if not os.path.isfile(fichier_local):
            continue
        resultat = cnf.sendFile(token, url_seafile, 'GALERY', fichier_local, plaque)
        if not resultat or resultat == 'ERROR':
            raise RuntimeError(f'Envoi Seafile impossible pour la vue {vue}')
        if str(resultat).startswith('http'):
            url_image = str(resultat)
        else:
            dossier_parent = config.get('PARENT_DIR', 'Cpp-Transport').strip('/')
            url_image = f"{url_seafile.rstrip('/')}/pictures?xys={dossier_parent}/{plaque}/GALERY|{resultat}"
        references.append({'type': vue, 'url_name': url_image})

    if references:
        cnf.sendFileJson(basic, url_seafile, plaque, json.dumps(references, ensure_ascii=False))
    return {item['type']: item['url_name'] for item in references}


def assurer_schema_recensement_vehicule():
    """Ajoute les colonnes du recensement aux anciennes bases SQLite."""
    db.create_all()
    colonnes = {column['name'] for column in sqlalchemy_inspect(db.engine).get_columns('recensement_vehicules')}
    definitions = {
        'capacite_places': 'INTEGER',
        'a_des_publicites': 'BOOLEAN NOT NULL DEFAULT 0',
        'transport_national': 'BOOLEAN NOT NULL DEFAULT 0',
        'sync_status': "VARCHAR(20) NOT NULL DEFAULT 'pending'",
        'sync_error': 'TEXT',
        'mysql_owner_id': 'INTEGER',
        'mysql_vehicle_id': 'VARCHAR(191)',
        'synced_at': 'DATETIME',
        'chauffeur_nom': 'VARCHAR(120)',
        'chauffeur_prenom': 'VARCHAR(120)',
        'chauffeur_telephone': 'VARCHAR(40)',
        'chauffeur_cin': 'VARCHAR(60)',
        'chauffeur_type_permis': 'VARCHAR(60)',
        'chauffeur_annee_experience': 'INTEGER',
        'chauffeur_image': 'VARCHAR(255)',
        'chauffeur_permis_images': 'TEXT',
    }
    with db.engine.begin() as connexion:
        for nom_colonne, definition in definitions.items():
            if nom_colonne not in colonnes:
                connexion.execute(sqlalchemy_text(
                    f'ALTER TABLE recensement_vehicules ADD COLUMN {nom_colonne} {definition}'
                ))


def synchroniser_recensement(recensement_id):
    """Envoie une fiche locale vers MySQL sans bloquer la validation du formulaire."""
    with app.app_context():
        assurer_schema_recensement_vehicule()
        fiche = RecensementVehicule.query.get(recensement_id)
        if not fiche:
            return
        try:
            fiche.sync_status = 'syncing'
            db.session.commit()
            connexion = mysql.connector.connect(
                host=config.get('RECENSEMENT_DB_HOST', '127.0.0.1'),
                port=int(config.get('RECENSEMENT_DB_PORT', 3306)),
                user=config.get('RECENSEMENT_DB_USER', 'root'),
                password=config.get('RECENSEMENT_DB_PASSWORD', ''),
                database=config.get('RECENSEMENT_DB_NAME', 'cpp_trans_prod'),
            )
            curseur = connexion.cursor()

            # Le propriétaire est dédoublonné par CIN, puis par téléphone + nom.
            nom_complet = (fiche.proprietaire_nom or '').strip()
            morceaux = nom_complet.split(None, 1)
            nom = morceaux[0] if morceaux else nom_complet
            prenom = morceaux[1] if len(morceaux) > 1 else ''
            proprietaire_id = None
            if fiche.proprietaire_cin:
                curseur.execute('SELECT id FROM proprietaires WHERE CIN = %s LIMIT 1', (fiche.proprietaire_cin,))
                resultat = curseur.fetchone()
                proprietaire_id = resultat[0] if resultat else None
            if not proprietaire_id and fiche.proprietaire_telephone:
                curseur.execute('SELECT id FROM proprietaires WHERE phone = %s AND nom = %s LIMIT 1',
                                 (fiche.proprietaire_telephone, nom))
                resultat = curseur.fetchone()
                proprietaire_id = resultat[0] if resultat else None

            maintenant = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            if not proprietaire_id:
                proprietaire_data = {
                    'nom': nom[:255], 'prenom': prenom[:255], 'date_de_naissance': '1900-01-01',
                    'adresse': (fiche.proprietaire_adresse or '')[:100], 'phone': (fiche.proprietaire_telephone or '')[:15],
                    'CIN': (fiche.proprietaire_cin or '')[:13], 'role_id': 0, 'group_prop_id_adelya': 0,
                    'email': '', 'password': '', 'remember_token': '', 'nif': '', 'stat': '', 'validation': 'non',
                    'approbation_coop': 'non', 'ville': '', 'code_postal': '', 'pays': 'Madagascar', 'cooperative_id': 0,
                    'nom_operat': '', 'idAdhesion': '', 'type_paiement': '', 'photo': '', 'periodiciteVersement': '',
                    'tour': '', 'user_id': 0, 'actif': 'oui', 'idSeafile': '', 'objectIdFidMember': '',
                    'created_at': maintenant, 'updated_at': maintenant,
                }
                proprietaire_columns = list(proprietaire_data)
                curseur.execute(
                    f"INSERT INTO proprietaires ({', '.join(proprietaire_columns)}) VALUES ({', '.join(['%s'] * len(proprietaire_columns))})",
                    tuple(proprietaire_data[column] for column in proprietaire_columns),
                )
                proprietaire_id = curseur.lastrowid

            # Le chauffeur saisi dans la fiche véhicule est également créé dans
            # la table MySQL chauffeurs, puis relié par vehicules.chauffeur_id.
            chauffeur_id = 0
            if fiche.chauffeur_nom:
                chauffeur_nom = fiche.chauffeur_nom[:255]
                chauffeur_prenom = (fiche.chauffeur_prenom or '')[:255]
                if fiche.chauffeur_cin:
                    curseur.execute('SELECT id FROM chauffeurs WHERE CIN = %s LIMIT 1', (fiche.chauffeur_cin,))
                elif fiche.chauffeur_telephone:
                    curseur.execute('SELECT id FROM chauffeurs WHERE phone = %s AND nom = %s LIMIT 1',
                                     (fiche.chauffeur_telephone, chauffeur_nom))
                else:
                    curseur.execute('SELECT id FROM chauffeurs WHERE phone = %s AND nom = %s LIMIT 1', ('', chauffeur_nom))
                resultat = curseur.fetchone()
                chauffeur_id = resultat[0] if resultat else 0
                if chauffeur_id:
                    curseur.execute(
                        "UPDATE chauffeurs SET prenom=%s, phone=%s, CIN=%s, type_permis=%s, annee_experience=%s, image=%s, updated_at=%s WHERE id=%s",
                        (chauffeur_prenom, (fiche.chauffeur_telephone or '')[:15],
                         (fiche.chauffeur_cin or '')[:13], (fiche.chauffeur_type_permis or '')[:30],
                         fiche.chauffeur_annee_experience or 0, fiche.chauffeur_image or '', maintenant, chauffeur_id),
                    )
                if not chauffeur_id:
                    chauffeur_data = {
                        'nom': chauffeur_nom, 'prenom': chauffeur_prenom, 'date_de_naissance': '1900-01-01',
                        'phone': (fiche.chauffeur_telephone or '')[:15], 'CIN': (fiche.chauffeur_cin or '')[:13],
                        'adresse': '', 'role_id': 0, 'email': '', 'username': '',
                        'type_permis': (fiche.chauffeur_type_permis or '')[:30],
                        'annee_experience': fiche.chauffeur_annee_experience or 0, 'password': '',
                        'remember_token': '', 'validation': 'non', 'objectIdParse': '', 'cooperative_id': 0,
                        'user_id': 0, 'actif': 'oui', 'nom_operat': '', 'idAdhesion': '', 'type_paiement': '',
                        'image': fiche.chauffeur_image or '', 'idSeafile': '', 'idFidMemeberAdelya': '',
                        'objectIdFidMember': '', 'created_at': maintenant, 'updated_at': maintenant,
                    }
                    chauffeur_columns = list(chauffeur_data)
                    curseur.execute(
                        f"INSERT INTO chauffeurs ({', '.join(chauffeur_columns)}) VALUES ({', '.join(['%s'] * len(chauffeur_columns))})",
                        tuple(chauffeur_data[column] for column in chauffeur_columns),
                    )
                    chauffeur_id = curseur.lastrowid

            images = fiche.images
            references_seafile = envoyer_photos_recensement(fiche)
            photo = (references_seafile.get('devant') or images.get('devant') or '')[:255]
            id_seafile = fiche.plaque[:255]
            commentaires = json.dumps(
                {'images': references_seafile, 'text': json.loads(fiche.notes or '{}').get('text', '')},
                ensure_ascii=False,
            )
            curseur.execute('SELECT num_immatriculation FROM vehicules WHERE num_immatriculation = %s LIMIT 1', (fiche.plaque,))
            vehicule_existant = curseur.fetchone()
            vehicule_data = {
                'num_immatriculation': fiche.plaque[:191], 'marque': fiche.marque, 'nb_place': fiche.capacite_places or 0,
                'type_transport_id': 0, 'proprietaire_id': proprietaire_id, 'group_bus_id_adelya': 0,
                'chauffeur_id': chauffeur_id, 'receveur_id': 0, 'variance_ligne_id': 0, 'gestionnaire_recette_id': 0,
                'objectIdParse': '', 'type_id': 0, 'validation': 'non', 'photo': photo, 'modele': fiche.modele or '',
                'wallet': '', 'materiel_id': '', 'actif': 'oui', 'idSeafile': id_seafile, 'nbCashWaitList': 0,
                'checkingMat': '', 'printPass': '', 'inactivityTimeout': '', 'trackingMinute': '', 'printCash': '',
                'ticketCancelTime': '', 'needPlaceAvailable': '', 'autoReboot': '', 'haveSpecial': '',
                'param': '', 'commission': '', 'annonceur': '', 'comments': commentaires,
                'haspublicite': 'oui' if fiche.a_des_publicites else 'non', 'created_at': maintenant, 'updated_at': maintenant,
            }
            vehicule_columns = list(vehicule_data)
            valeurs = tuple(vehicule_data[column] for column in vehicule_columns)
            if vehicule_existant:
                mysql_id = vehicule_existant[0]
                curseur.execute(
                    "UPDATE vehicules SET marque=%s, nb_place=%s, proprietaire_id=%s, photo=%s, modele=%s, "
                    "comments=%s, haspublicite=%s, idSeafile=%s, chauffeur_id=%s, updated_at=%s WHERE num_immatriculation=%s",
                    (fiche.marque, fiche.capacite_places, proprietaire_id, photo, fiche.modele,
                     commentaires, 'oui' if fiche.a_des_publicites else 'non', id_seafile, chauffeur_id, maintenant, fiche.plaque),
                )
            else:
                curseur.execute(
                    f"INSERT INTO vehicules ({', '.join(vehicule_columns)}) VALUES ({', '.join(['%s'] * len(vehicule_columns))})",
                    valeurs,
                )
                mysql_id = fiche.plaque
            connexion.commit()
            curseur.close()
            connexion.close()

            fiche.mysql_owner_id = proprietaire_id
            fiche.mysql_vehicle_id = mysql_id
            fiche.sync_status = 'synced'
            fiche.sync_error = None
            fiche.synced_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            db.session.commit()
        except Exception as erreur:
            fiche.sync_status = 'error'
            fiche.sync_error = str(erreur)[:1000]
            db.session.commit()
        finally:
            db.session.remove()


@app.post('/recensement/<int:recensement_id>/sync')
@login_required
def synchroniser_un_recensement(recensement_id):
    fiche = RecensementVehicule.query.get_or_404(recensement_id)
    threading.Thread(target=synchroniser_recensement, args=(fiche.id,), daemon=True).start()
    flash(f'La synchronisation du véhicule {fiche.plaque} a été lancée.', 'info')
    return redirect(url_for('recensement_vehicules'))


@app.post('/recensement/sync-all')
@login_required
def synchroniser_tous_les_recensements():
    fiches = RecensementVehicule.query.filter(RecensementVehicule.sync_status != 'synced').all()
    for fiche in fiches:
        threading.Thread(target=synchroniser_recensement, args=(fiche.id,), daemon=True).start()
    flash(f'{len(fiches)} synchronisation(s) lancée(s).', 'info')
    return redirect(url_for('recensement_vehicules'))


@app.route('/recensement-vehicules/<int:recensement_id>', methods=['GET', 'POST'])
@login_required
def voir_recensement(recensement_id):
    fiche = RecensementVehicule.query.get_or_404(recensement_id)
    if request.method == 'POST':
        fiche.marque = request.form.get('marque', fiche.marque).strip()
        fiche.modele = request.form.get('modele', '').strip()
        fiche.couleur = request.form.get('couleur', '').strip()
        fiche.capacite_places = int(request.form['capacite_places']) if request.form.get('capacite_places') else None
        fiche.a_des_publicites = request.form.get('a_des_publicites') == 'on'
        fiche.transport_national = request.form.get('transport_national') == 'on'
        fiche.proprietaire_nom = request.form.get('proprietaire_nom', '').strip() or 'À compléter'
        fiche.proprietaire_telephone = request.form.get('proprietaire_telephone', '').strip()
        fiche.proprietaire_cin = request.form.get('proprietaire_cin', '').strip()
        fiche.proprietaire_adresse = request.form.get('proprietaire_adresse', '').strip()
        fiche.chauffeur_nom = request.form.get('chauffeur_nom', '').strip()
        fiche.chauffeur_prenom = request.form.get('chauffeur_prenom', '').strip()
        fiche.chauffeur_telephone = request.form.get('chauffeur_telephone', '').strip()
        fiche.chauffeur_cin = request.form.get('chauffeur_cin', '').strip()
        fiche.chauffeur_type_permis = request.form.get('chauffeur_type_permis', '').strip()
        fiche.chauffeur_annee_experience = int(request.form['chauffeur_annee_experience']) if request.form.get('chauffeur_annee_experience') else None
        fiche.sync_status = 'pending'
        fiche.sync_error = None
        db.session.commit()
        threading.Thread(target=synchroniser_recensement, args=(fiche.id,), daemon=True).start()
        flash(f'La fiche {fiche.plaque} a été modifiée et remise en synchronisation.', 'success')
        return redirect(url_for('voir_recensement', recensement_id=fiche.id))
    return render_template('recensement_detail.html', vehicule=fiche, marques=VEHICLE_BRANDS)


@app.route('/api/recensement/proprietaires', methods=['GET'])
@login_required
def rechercher_proprietaires_recensement():
    terme = request.args.get('q', '').strip()
    if len(terme) < 2:
        return jsonify([])
    try:
        connexion = mysql.connector.connect(
            host=config.get('RECENSEMENT_DB_HOST', '127.0.0.1'),
            port=int(config.get('RECENSEMENT_DB_PORT', 3306)),
            user=config.get('RECENSEMENT_DB_USER', 'root'),
            password=config.get('RECENSEMENT_DB_PASSWORD', ''),
            database=config.get('RECENSEMENT_DB_NAME', 'cpp_trans_prod'),
        )
        curseur = connexion.cursor(dictionary=True)
        curseur.execute(
            "SELECT nom, prenom, phone, CIN, adresse FROM proprietaires "
            "WHERE phone LIKE %s ORDER BY nom, prenom LIMIT 10",
            (f'%{terme}%',),
        )
        resultats = curseur.fetchall()
        curseur.close()
        connexion.close()
        return jsonify([{
            'nom': f"{p.get('nom') or ''} {p.get('prenom') or ''}".strip(),
            'telephone': p.get('phone') or '',
            'cin': p.get('CIN') or '',
            'adresse': p.get('adresse') or '',
        } for p in resultats])
    except Exception:
        # La recherche locale permet de continuer à travailler si MySQL est indisponible.
        db.create_all()
        resultats = RecensementProprietaire.query.filter(
            RecensementProprietaire.telephone.ilike(f'%{terme}%')
        ).order_by(RecensementProprietaire.nom).limit(10).all()
        return jsonify([{'nom': p.nom, 'telephone': p.telephone or '', 'cin': p.cin or '', 'adresse': p.adresse or ''}
                        for p in resultats])


@app.route('/api/recensement/scan-plaque', methods=['POST'])
@login_required
def scanner_plaque_recensement():
    image = request.files.get('plaque_image')
    if not image or not image.filename:
        return jsonify({'error': 'Photo de plaque manquante'}), 400
    token = config.get('PLATE_RECOGNIZER_TOKEN') or '92a54581b94041c7064517e70862ac9c65a6785b'
    try:
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            files={'upload': (image.filename, image.read(), image.mimetype or 'image/jpeg')},
            headers={'Authorization': f'Token {token}'},
            timeout=45,
        )
        response.raise_for_status()
        results = response.json().get('results', [])
        if not results:
            return jsonify({'error': 'Aucune plaque détectée'}), 422
        return jsonify({'plaque': results[0].get('plate', '').upper()})
    except Exception as erreur:
        return jsonify({'error': f'Lecture de plaque impossible : {erreur}'}), 502


@app.route('/recensement-chauffeurs', methods=['GET', 'POST'])
@login_required
def recensement_chauffeurs():
    db.create_all()
    upload_dir = os.path.join(app.root_path, 'static', 'driver_uploads')
    os.makedirs(upload_dir, exist_ok=True)
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        if not nom:
            flash('Le nom du chauffeur est obligatoire.', 'danger')
            return redirect(url_for('recensement_chauffeurs'))

        photos = {}
        for champ, type_photo in (('chauffeur_image', 'chauffeur'), ('permis_recto', 'permis_recto'), ('permis_verso', 'permis_verso')):
            fichier = request.files.get(champ)
            if not fichier or not fichier.filename:
                continue
            extension = os.path.splitext(fichier.filename)[1].lower()
            if extension not in {'.jpg', '.jpeg', '.png', '.webp'}:
                flash('Les photos doivent être au format JPG, PNG ou WEBP.', 'danger')
                return redirect(url_for('recensement_chauffeurs'))
            nom_fichier = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{type_photo}_{secure_filename(fichier.filename)}"
            fichier.save(os.path.join(upload_dir, nom_fichier))
            photos[type_photo] = nom_fichier

        chauffeur = RecensementChauffeur(
            nom=nom,
            prenom=request.form.get('prenom', '').strip(),
            telephone=request.form.get('telephone', '').strip(),
            cin=request.form.get('cin', '').strip(),
            adresse=request.form.get('adresse', '').strip(),
            type_permis=request.form.get('type_permis', '').strip(),
            annee_experience=int(request.form['annee_experience']) if request.form.get('annee_experience') else None,
            image=photos.get('chauffeur'),
            permis_images=json.dumps(photos),
        )
        db.session.add(chauffeur)
        db.session.commit()
        flash(f'Le chauffeur {nom} a été enregistré.', 'success')
        return redirect(url_for('recensement_chauffeurs'))
    chauffeurs = RecensementChauffeur.query.order_by(RecensementChauffeur.created_at.desc()).all()
    return render_template('recensement_chauffeurs.html', chauffeurs=chauffeurs)


@app.route('/recensement-vehicules', methods=['GET', 'POST'])
@app.route('/recensement', methods=['GET', 'POST'])
@login_required
def recensement_vehicules():
    """Interface de saisie et de consultation du recensement des véhicules."""
    db.create_all()  # crée uniquement la nouvelle table si elle n'existe pas encore
    # Migration légère pour les installations qui possèdent déjà la table.
    colonnes = {column['name'] for column in sqlalchemy_inspect(db.engine).get_columns('recensement_vehicules')}
    with db.engine.begin() as connexion:
        if 'capacite_places' not in colonnes:
            connexion.execute(sqlalchemy_text('ALTER TABLE recensement_vehicules ADD COLUMN capacite_places INTEGER'))
        if 'a_des_publicites' not in colonnes:
            connexion.execute(sqlalchemy_text('ALTER TABLE recensement_vehicules ADD COLUMN a_des_publicites BOOLEAN NOT NULL DEFAULT 0'))
        if 'transport_national' not in colonnes:
            connexion.execute(sqlalchemy_text('ALTER TABLE recensement_vehicules ADD COLUMN transport_national BOOLEAN NOT NULL DEFAULT 0'))
        for nom_colonne, definition in {
            'sync_status': "VARCHAR(20) NOT NULL DEFAULT 'pending'",
            'sync_error': 'TEXT',
            'mysql_owner_id': 'INTEGER',
            'mysql_vehicle_id': 'INTEGER',
            'synced_at': 'DATETIME',
            'chauffeur_nom': 'VARCHAR(120)',
            'chauffeur_prenom': 'VARCHAR(120)',
            'chauffeur_telephone': 'VARCHAR(40)',
            'chauffeur_cin': 'VARCHAR(60)',
            'chauffeur_type_permis': 'VARCHAR(60)',
            'chauffeur_annee_experience': 'INTEGER',
            'chauffeur_image': 'VARCHAR(255)',
            'chauffeur_permis_images': 'TEXT',
        }.items():
            if nom_colonne not in colonnes:
                connexion.execute(sqlalchemy_text(f'ALTER TABLE recensement_vehicules ADD COLUMN {nom_colonne} {definition}'))
    upload_dir = os.path.join(app.root_path, 'static', 'vehicle_uploads')
    os.makedirs(upload_dir, exist_ok=True)
    driver_upload_dir = os.path.join(app.root_path, 'static', 'driver_uploads')
    os.makedirs(driver_upload_dir, exist_ok=True)

    if request.method == 'POST':
        plaque = request.form.get('plaque', '').strip().upper()
        marque = request.form.get('marque', '').strip()
        proprietaire_nom = request.form.get('proprietaire_nom', '').strip() or 'À compléter'

        if not plaque or not marque or marque not in VEHICLE_BRANDS:
            flash('La plaque, la marque et le nom du propriétaire sont obligatoires.', 'danger')
            return redirect(url_for('recensement_vehicules'))

        if RecensementVehicule.query.filter_by(plaque=plaque).first():
            flash(f'Le véhicule {plaque} est déjà recensé.', 'warning')
            return redirect(url_for('recensement_vehicules'))

        images = {}
        for view in ('devant', 'derriere', 'gauche', 'droite', 'interieur'):
            image_file = request.files.get(f'image_{view}')
            if not image_file or not image_file.filename:
                continue
            extension = os.path.splitext(image_file.filename)[1].lower()
            if extension not in {'.jpg', '.jpeg', '.png', '.webp'}:
                flash('Format image accepté : JPG, PNG ou WEBP.', 'danger')
                return redirect(url_for('recensement_vehicules'))
            image_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{view}_{secure_filename(image_file.filename)}"
            image_file.save(os.path.join(upload_dir, image_name))
            images[view] = image_name

        chauffeur_images = {}
        for field_name, image_key in (
            ('chauffeur_image', 'portrait'),
            ('chauffeur_permis_recto', 'permis_recto'),
            ('chauffeur_permis_verso', 'permis_verso'),
        ):
            image_file = request.files.get(field_name)
            if not image_file or not image_file.filename:
                continue
            extension = os.path.splitext(image_file.filename)[1].lower()
            if extension not in {'.jpg', '.jpeg', '.png', '.webp'}:
                flash('Format image chauffeur accepté : JPG, PNG ou WEBP.', 'danger')
                return redirect(url_for('recensement_vehicules'))
            image_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}_{image_key}_{secure_filename(image_file.filename)}"
            image_file.save(os.path.join(driver_upload_dir, image_name))
            chauffeur_images[image_key] = image_name

        notes_text = request.form.get('notes', '').strip()
        vehicule = RecensementVehicule(
            plaque=plaque,
            marque=marque,
            modele=request.form.get('modele', '').strip(),
            annee=request.form.get('annee', '').strip(),
            couleur=request.form.get('couleur', '').strip(),
            capacite_places=int(request.form['capacite_places']) if request.form.get('capacite_places') else None,
            a_des_publicites=request.form.get('a_des_publicites') == 'on',
            transport_national=request.form.get('transport_national') == 'on',
            proprietaire_nom=proprietaire_nom,
            proprietaire_telephone=request.form.get('proprietaire_telephone', '').strip(),
            proprietaire_cin=request.form.get('proprietaire_cin', '').strip(),
            proprietaire_adresse=request.form.get('proprietaire_adresse', '').strip(),
            cooperative=request.form.get('cooperative', '').strip(),
            image=images.get('devant'),
            notes=json.dumps({'text': notes_text, 'images': images}),
            chauffeur_nom=request.form.get('chauffeur_nom', '').strip(),
            chauffeur_prenom=request.form.get('chauffeur_prenom', '').strip(),
            chauffeur_telephone=request.form.get('chauffeur_telephone', '').strip(),
            chauffeur_cin=request.form.get('chauffeur_cin', '').strip(),
            chauffeur_type_permis=request.form.get('chauffeur_type_permis', '').strip(),
            chauffeur_annee_experience=int(request.form['chauffeur_annee_experience']) if request.form.get('chauffeur_annee_experience') else None,
            chauffeur_image=chauffeur_images.get('portrait'),
            chauffeur_permis_images=json.dumps(chauffeur_images),
        )
        db.session.add(vehicule)
        db.session.commit()
        proprietaire_local = RecensementProprietaire.query.filter_by(nom=proprietaire_nom).first()
        if not proprietaire_local:
            proprietaire_local = RecensementProprietaire(nom=proprietaire_nom)
            db.session.add(proprietaire_local)
        proprietaire_local.telephone = request.form.get('proprietaire_telephone', '').strip()
        proprietaire_local.cin = request.form.get('proprietaire_cin', '').strip()
        proprietaire_local.adresse = request.form.get('proprietaire_adresse', '').strip()
        db.session.commit()
        synchronisation_id = vehicule.id
        threading.Thread(target=synchroniser_recensement, args=(synchronisation_id,), daemon=True).start()
        flash(f'Le véhicule {plaque} a été enregistré avec succès.', 'success')
        return redirect(url_for('recensement_vehicules'))

    recherche = request.args.get('q', '').strip()
    query = RecensementVehicule.query.order_by(RecensementVehicule.created_at.desc())
    if recherche:
        terme = f'%{recherche}%'
        query = query.filter(db.or_(RecensementVehicule.plaque.ilike(terme),
                                    RecensementVehicule.proprietaire_nom.ilike(terme),
                                    RecensementVehicule.marque.ilike(terme)))
    vehicules = query.all()
    return render_template('recensement_vehicules.html', vehicules=vehicules, recherche=recherche, marques=VEHICLE_BRANDS)
@app.route('/collect', methods=['GET'])
def collect():    
    if(request.method=='GET') :
        user_agent = request.headers.get('User-Agent')
        if(user_agent=="CPP_TPE_COLLECT"):
            username = request.args.get('username')
            userid = request.args.get('userid')
        #     return jsonify({
        #     'message': 'Error user agent',
        #     'user_agent': user_agent,
        #     'username': username,
        #     'userid': userid,
        # })
            filtered_cooperatives = Cooperatives.query.filter(Cooperatives.id > 0).all()            
            # Étape 2 : select  nom  
            filtered_cooperative_names = [Cooperatives for Cooperatives in filtered_cooperatives]
            return render_template("steps/imageVehicule.html",record=filtered_cooperative_names,username=username,userid=userid)
            # return render_template('pictures.html',role=1,name="CPP-SYSTEM")
        else:
            return jsonify({
            'message': 'Error user agent',
            'user_agent': user_agent
        })
@app.route('/api/meteo/')
def meteo():
    dictionnaire = {
        'type': 'Prévision de température',
        'valeurs': [24, 24, 25, 26, 27, 28],
        'unite': "degrés Celcius"
    }
    return jsonify(dictionnaire)
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/downloadRec', methods=['GET', 'POST'])
def download_file():
#     namefile="FilesRecencement/"+request.form['namfile']
#     # root = tkinter.Tk()
#     # root.lift()  # Cacher la fenêtre principale
#     root.withdraw()  # Cacher la fenêtre principale

# # Demander à l'utilisateur de sélectionner le dossier de destination
#     dossier_destination = filedialog.askdirectory(title="Sélectionner le dossier de destination")

# # Vérifier si l'utilisateur a sélectionné un dossier
#     if dossier_destination:
#         chemin_fichier_source = namefile
#         nom_fichier = os.path.basename(chemin_fichier_source)
#         chemin_fichier_destination = os.path.join(dossier_destination, nom_fichier)

#         # Copier le fichier source vers la destination
#         shutil.copy(chemin_fichier_source, chemin_fichier_destination)
        
#         print("Fichier copié avec succès vers :", chemin_fichier_destination)
#     else:
#         print("Aucun dossier de destination sélectionné")

#     # Fermer la fenêtre Tkinter
#     root.destroy()
    return 'ok'
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

###debute###
@app.route('/home',methods=['GET','POST'])
def homec():
   if(request.method=='POST') :
        email = request.form['email']
        pwd = request.form['password']
        
        return render_template("index.html",data=url)
@app.route('/lottery-cpp',methods=['GET'])
def lottery():
    data=[]
    date_courante = datetime.now()
    profilepic_filename = os.path.join("static","cppsystem.jpg")
    
    date_name=date_courante.strftime("%Y-%m-%d")
    current_nameFile=date_name+"_tickets_game.xlsx"
    nom_fichier="files/"+current_nameFile
    # Load Excel workbook
    classeur = load_workbook(nom_fichier)
    feuille = classeur.active

    # Parcourir les lignes et les colonnes pour afficher les données
    for ligne in feuille.iter_rows(values_only=True):
        data.append(ligne[2])
    data.pop(0)
    return render_template("games/spinner.html",data=date_courante,image=profilepic_filename,ticket=data)

@app.route('/sendInfo',methods=['GET','POST'])
def setInfo():
   return render_template("setInfo.html")
@app.route('/serveur',methods=['GET'])
def setviewServer():
   return render_template("serveur.html")

#  -----------------------------------------------------------------------  #
############ EXTRACTION JOURNALIERE DATA BEGIN   ##############
@app.route('/view_event',methods=['GET'])
def view_event():
   return render_template("view_events.html")
def get_line_event(datebeg,dateend,name):
    from event import event
    from datetime import datetime,timedelta
    event1=event()
  
    date_debut = datetime.strptime(datebeg, '%d/%m/%Y')
    date_fin = datetime.strptime(dateend, '%d/%m/%Y')
    current_date = date_debut
    dates_array = []
    while current_date <= date_fin:
        dates_array.append(current_date)
        current_date += timedelta(days=1)
  
    #sortie de nom de fichier 
    output_file = 'event/'+name+".csv"
    # Tableau pour stocker les dates
   
    results=[]
    # Affichage des dates pour vérification
    for date in dates_array:
        
        dates=date.strftime('%d/%m/%Y')
       
        donnees=event1.getEventParBus(dates)
            # Nombre de processus à utiliser
        if donnees is not None :
            num_processus = 4
                # Appeler la fonction de traitement multi-processing
            event1.traiter_donnees_multiprocessing(donnees, num_processus, output_file)
            results.append(f'Date : {dates} Insertion  avec succès !')   
        else :   
            results.append(f'Date : {dates} Data Not Found !')  
    return results
@app.route('/get_results', methods=['POST'])
def get_results():
    from datetime import datetime
    directory0="event"
    if not os.path.isdir(directory0):
            os.mkdir(directory0)
   
    if request.method == 'POST':
        if 'datebegin' in request.form :
            if request.form['datebegin']!='' :
                dateDebut = request.form['datebegin']
            else :
                retour=[]
                retour.append("Date Begin is required")
                return jsonify(retour)
        if 'dateend' in request.form :
            if request.form['dateend']!='' :
                dateFin = request.form['dateend']
            else  :
                retour=[]
                retour.append("Date End is required")
                return jsonify(retour)
        if(dateDebut!=dateFin):
            dateDebut1 = datetime.strptime(dateDebut, "%Y-%m-%d")
            dateFin1 = datetime.strptime(dateFin, "%Y-%m-%d")
        else :
            dateDebut1 = datetime.strptime(dateDebut, "%Y-%m-%d")
            dateFin1=datetime.strptime(dateDebut, "%Y-%m-%d")
        formatted_date = dateDebut.replace("-", "")
        formatted_date1 = dateFin.replace("-", "")
        name=formatted_date+'_'+formatted_date1
   
    results = get_line_event(dateDebut1.strftime("%d/%m/%Y"),dateFin1.strftime("%d/%m/%Y"),name)  # Appel de votre fonction
    return jsonify(results)
############ EXTRACTION JOURNALIERE DATA END  ##############

#  -----------------------------------------------------------------------  #
@app.route('/extract/incidents',methods=['POST'])
def extractionData():
    if request.method == 'POST':
      dateDebut = request.form['dateDebut']
      dateFin = request.form['dateFin']
      return ExtractSupport(dateDebut,dateFin)
def ExtractSupport(datec,dateFin) :
    url_sql=config['URL_MYSQL']
    username=config['USER_MYSQL']
    password=config['PASSWORD']
    databasename=config['DATABASE_NAME']
    database_config={
        "username":username,
        "passwd":password,
        "url_serve":url_sql,
        "database":databasename
    }
   
    #debut
    separateDate=datec.split('-')
    month=int(separateDate[1])
    year=int(separateDate[0])
    dayd=int(separateDate[2])
    datecc=str(dayd)+"/"+str(month)+"/"+str(year)
    #fin
    separateDate1=dateFin.split('-')
    month1=int(separateDate1[1])
    year1=int(separateDate1[0])
    dayd1=int(separateDate1[2])
    datefin=str(dayd1)+"/"+str(month1)+"/"+str(year1)
   
     #get list date#
    start = date(year,month,dayd)
    end = date(year1, month1, dayd1)
    value=(end-start).days

    periods = value+1
    daterange = []
    for day in range(periods):
        datep = (start + datetime.timedelta(days = day)).isoformat()
        daterange.append(datep)
    #end list#
    
    appid=config['PARSE_APP_ID']
    rest_api_key=config['PARSE_API_KEY_REST']
    masterkey=config['PARSE_MASTER_KEY']
    url=config['URL_DOMAIN'] 
    cnf.connect(appid,rest_api_key,masterkey,url)
    for x in daterange :
        value=cnf.getIncidentS(database_config,x)
    return value
@app.route('/getIncident',methods=['GET','POST'])
def getIncident():
        url_sql=config['URL_MYSQL']
        username=config['USER_MYSQL']
        password=config['PASSWORD']
        databasename=config['DATABASE_NAME']
        database_config={
            "username":username,
            "passwd":password,
            "url_serve":url_sql,
            "database":databasename
            }
    
        dateLast=cnf.getLastDateExtractionIS(database_config)
        return render_template("getIncident.html",data=dateLast)

@app.route('/getArret',methods=['GET'])
def getDataArret():
    url_sql=config['URL_MYSQL']
    username=config['USER_MYSQL']
    password=config['PASSWORD']
    databasename=config['DATABASE_NAME']
    database_config={
        "username":username,
        "passwd":password,
        "url_serve":url_sql,
        "database":databasename
    }
   
    
    appid=config['PARSE_APP_ID']
    rest_api_key=config['PARSE_API_KEY_REST']
    masterkey=config['PARSE_MASTER_KEY']
    url=config['URL_DOMAIN'] 
    cnf.connect(appid,rest_api_key,masterkey,url)
    arret=cnf.getArretLists(database_config)
    return arret
    #cnf.getArretInfo(database_config)

@app.route('/good',methods=['GET','POST'])
def test():
    return request.method
    #return render_template("index.html",data=url)
@app.route('/uploadFichier',methods=['GET'])
def viewUpload():
    return render_template("uploadFiles.html") 
def process_file(filepath):
    # do something with the file
    pass 
def allowed_file(filename):
    app.config['ALLOWED_EXTENSIONS'] = {'rar'}

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/sendFileVehicule',methods=['POST'])
def sendFileUniqueVehicule() :
     # if fichier.tell() == 0:
    #     return 'No selected file'
    devant_name=''
    derriere_name=''
    gauche_name=''
    droite_name=''
    interieur_name=''
    filenameArray=[]
    env_chkc=current_user.env
       
    recencement_file_vehic='non'
    if 'devant_vehicule' in request.files:
        # return jsonify({"error": "No 'devant_vehicule' file provided."}), 400
        devant=request.files['devant_vehicule']
        devant_name=devant.filename
        filenameArray.append({'name_files': devant_name, 'type': 'devant'})
        chemin = os.path.join("SeafileTemp",devant_name)
        devant.save(chemin) 
    if 'derriere_vehicule' in request.files:
        derriere=request.files['derriere_vehicule']
        derriere_name=derriere.filename
        filenameArray.append({'name_files': derriere_name, 'type': 'derriere'})
        chemin = os.path.join("SeafileTemp",derriere_name)
        derriere.save(chemin)
    if 'gauche_vehicule' in request.files: 
        gauche=request.files['gauche_vehicule']
        gauche_name=gauche.filename
        
        filenameArray.append({'name_files': gauche_name, 'type': 'gauche_vehicule'})
        chemin = os.path.join("SeafileTemp",gauche_name)
        gauche.save(chemin)
    if 'droite_vehicule' in request.files:  
        droite=request.files['droite_vehicule']
        droite_name=droite.filename
        
        filenameArray.append({'name_files': droite_name, 'type': 'droite_vehicule'})
        chemin = os.path.join("SeafileTemp",droite_name)
        droite.save(chemin)
    if 'interieur_vehicule' in request.files: 
        interieur=request.files['interieur_vehicule']
        interieur_name=interieur.filename
        
        filenameArray.append({'name_files': interieur_name, 'type': 'interieur_vehicule'})
        chemin = os.path.join("SeafileTemp",interieur_name)
        interieur.save(chemin)
    if 'recencement_file_vehic' in request.form :
        recencement_file_vehic=request.form['recencement_file_vehic']
    nameDirectory=request.form['plaque'] 
    datax=config['TOKEN_SEAFILE']
    
    urlseafile=config['URL_SEAFILE']
    env=config['environnement']
    url_trp=config['TRP_DOMAIN_URL']
    if env_chkc==1 :
        urlseafile=config['URL_SEAFILE_PRO']
        url_trp=config['TRP_DOMAIN_URL_PROD']
    ###get les contenu d fichier s'il existe ####
    getContentsjson=cnf.getContenuFiles(datax,urlseafile,nameDirectory,"TRP")
    dataj=[]
    try :
        if len(getContentsjson)==0 :
            dataj=[]
        else :
            dataj=getContentsjson
           
    except :
            dataj=[]
    header = {
                "Content-Type":"application/json"
    }
    data_vehic={
        'plaque':nameDirectory,
        'recencement_file_vehic':recencement_file_vehic
    }
   
    cnf.createDirectory(datax,urlseafile,nameDirectory)
    cnf.createDirectory(datax,urlseafile,"GALERY",nameDirectory)
    nameDirectoryfirst="GALERY"
    # chemin = os.path.join("SeafileTemp",filename)
    try :
        cnf.deleteFileExist(nameDirectory,env_chkc)  
        for file_info in filenameArray:
            file_type = file_info.get('type')
            filenameq=file_info.get('name_files') 
        # for i in range(len(filenameArray)):
            
            dataobject={}
            imageLue = Image.open("SeafileTemp/"+filenameq)
                                    #reduction taille image
            new_size=(600, 600)
            im1 = imageLue.resize(new_size)
            im1.save("liveImage/"+filenameq)
            #                         #get Token 
            token=cnf.getTokenSeafile(datax, urlseafile)
            os.remove("SeafileTemp/"+filenameq)
            
            nameFile="liveImage/"+filenameq
                                    #send file
            namefilesup=cnf.sendFile(token, urlseafile,nameDirectoryfirst,nameFile,nameDirectory)
            # getContentsjson=cnf.getContenuFiles(token, urlseafile,nameDirectory,nameFile)
            os.remove("liveImage/"+filenameq)
            dataobject={'url_name':namefilesup,'type':file_type}
                       
            dataj.append(dataobject)
                        
                           
        cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(dataj))  
        data_seafile={
            "plaque":nameDirectory,
            "json_seafile":json.dumps(dataj)
        }
        try :
            response_seafile = requests.post(url_trp+"api/update_seafile", json=data_seafile, headers=header, timeout=120)
            print(response_seafile)
            sys.stdout.flush()
        except  Exception as e :
            return e
            # return "ok"
        ##Send File json to transport
            # response = requests.post(url_trp+"api/update_recenc_vehicle", json=data_vehic, headers=header, timeout=120)
        return 'Gallerie envoyéé avec succès!'
    except Exception as e :
        return e

    return json.dumps(filenameArray)
def createDirectoryFile() :
    try :
        directory0="SeafileTemp"
        directory1="liveImage"
        directory2="FilesRecencement"
        directory3="ImageTemporaire"
        directory4="myfiles"
        directory5="FilesTemps"
        
        ## If folder doesn't exists, create it ##
        if not os.path.isdir(directory0):
            os.mkdir(directory0)
        if not os.path.isdir(directory1):
            os.mkdir(directory1)
        if not os.path.isdir(directory2):
            os.mkdir(directory2)
        if not os.path.isdir(directory3):
            os.mkdir(directory3)
        if not os.path.isdir(directory4):
            os.mkdir(directory4)
        if not os.path.isdir(directory5):
            os.mkdir(directory5)
    except Exception as e :
        print(e)
        pass
@app.route('/sendFilePaperVehicule',methods=['POST'])
def sendFilePapsVehicule() :
     # if fichier.tell() == 0:
    #     return 'No selected file'
    licence=''
    assurance=''
    carte_grise_recto=''
    carte_grise_verso=''
    filenameArray=[]
    env_chkc=current_user.env
    
    if 'licence' in request.files:
        licence=request.files['licence']
        licence_name=licence.filename
        filenameArray.append({'name_files': licence_name, 'type': 'Licence'})
        chemin = os.path.join("SeafileTemp",licence_name)
        licence.save(chemin)
     
    if 'licence_v' in request.files:
        licence=request.files['licence_v']
        licence_name=licence.filename
        filenameArray.append({'name_files': licence_name, 'type': 'Licence_Verso'})
        chemin = os.path.join("SeafileTemp",licence_name)
        licence.save(chemin)

    
    if 'assurance' in request.files:
        assurance=request.files['assurance']
        assurance_name=assurance.filename
        filenameArray.append({'name_files': assurance_name, 'type': 'Assurance'})
        chemin = os.path.join("SeafileTemp",assurance_name)
        assurance.save(chemin)
    if 'assurance_v' in request.files:
        assurance=request.files['assurance_v']
        assurance_name=assurance.filename
        filenameArray.append({'name_files': assurance_name, 'type': 'Assurance'})
        chemin = os.path.join("SeafileTemp",assurance_name)
        assurance.save(chemin)
    if 'nifsta_r' in request.files:
        nifstat_r=request.files['nifsta_r']
        nifstat_name_r=nifstat_r.filename
        filenameArray.append({'name_files': nifstat_name_r, 'type': 'NIF/STAT_r'})
        chemin = os.path.join("SeafileTemp",nifstat_name_r)
        nifstat_r.save(chemin)
    if 'nifsta_v' in request.files:
        nifstat=request.files['nifsta_v']
        nifstat_name=nifstat.filename
        filenameArray.append({'name_files': nifstat_name, 'type': 'NIF/STAT_v'})
        chemin = os.path.join("SeafileTemp",nifstat_name)
        nifstat.save(chemin)
    
    if 'visite_technique' in request.files:
        visite_tech=request.files['visite_technique']
        visite_tech_name=visite_tech.filename
        filenameArray.append({'name_files': visite_tech_name, 'type': 'visite_technique'})
        chemin = os.path.join("SeafileTemp",visite_tech_name)
        visite_tech.save(chemin)
    if 'carte_grise_recto' in request.files:
        cgr=request.files['carte_grise_recto']
        cgr_name=cgr.filename
        filenameArray.append({'name_files': cgr_name, 'type': 'Carte_grise_recto'})
        chemin = os.path.join("SeafileTemp",cgr_name)
        cgr.save(chemin)
    if 'carte_grise_verso' in request.files:
        cgv=request.files['carte_grise_verso']
        cgv_name=cgv.filename
        filenameArray.append({'name_files': cgv_name, 'type': 'Carte_grise_verso'})
        chemin = os.path.join("SeafileTemp",cgv_name)
        cgv.save(chemin)
    
    nameDirectory=request.form['plaque'] 
    datax=config['TOKEN_SEAFILE']
    urlseafile=config['URL_SEAFILE']
    url_trp=config['TRP_DOMAIN_URL']
    if env_chkc==1 :
        urlseafile=config['URL_SEAFILE_PRO']
        url_trp=config['TRP_DOMAIN_URL_PROD']
 
    ###get les contenu d fichier s'il existe ####
    getContentsjson=cnf.getContenuFiles(datax,urlseafile,nameDirectory,"TRP")
    dataj=[]
    try :
        if len(getContentsjson)==0 :
            dataj=[]
        else :
            dataj=getContentsjson
           
    except :
            dataj=[]
    cnf.createDirectory(datax,urlseafile,nameDirectory,"")
    cnf.createDirectory(datax,urlseafile,"PAPER",nameDirectory)
    nameDirectoryfirst="PAPER"
    try :
        cnf.deleteFileExist(nameDirectory,env_chkc)          
        for file_info in filenameArray:
            file_type = file_info.get('type')
            filenameq=file_info.get('name_files') 
            dataobject={}
            imageLue = Image.open("SeafileTemp/"+filenameq)
            #reduction taille image
            new_size=(600, 600)
            im1 = imageLue.resize(new_size)
            im1.save("liveImage/"+filenameq)
          #get Token 
            token=cnf.getTokenSeafile(datax, urlseafile)
            os.remove("SeafileTemp/"+filenameq)
            nameFile="liveImage/"+filenameq
                   #send file   
            namefilesup=cnf.sendFile(token, urlseafile,nameDirectoryfirst,nameFile,nameDirectory)
            os.remove("liveImage/"+filenameq)
            dataobject={'url_name':namefilesup,'type':file_type}
                       
            dataj.append(dataobject)
                        
            
        cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(dataj))  
        data_seafile={
            "plaque":nameDirectory,
            "json_seafile":json.dumps(dataj)
        }
        try :
            response_seafile = requests.post(url_trp+"api/update_seafile", json=data_seafile, headers=header, timeout=120)
            print(response_seafile)
            sys.stdout.flush()
        except :
            pass
            # return "ok"
        return 'Papier véhicule envoyé avec succès!'
    except Exception as e :
        return e
@app.route('/listeFile',methods=['GET'])
def listeViewVehicule():
    
    data=[]
    try :
        # date_courante = datetime.now()
        # date_name=date_courante.strftime("%Y-%m-%d")
        header = {
                "Content-Type":"application/json"
        }
        env = config['environnement']
        url_trp = config['TRP_DOMAIN_URL']
        env_chkc=current_user.env
        if env_chkc==1 :
            url_trp = config['TRP_DOMAIN_URL_PROD']
        print(env_chkc)
        print(url_trp)
        response = requests.get(url_trp+"api/get_vehicle_nr", json={}, headers=header, timeout=120)
        # print(response.text)
        # sys.stdout.flush()
        # current_nameFile="liste_vehicule.xlsx"
        # nom_fichier="FilesTemps/"+current_nameFile
        # # Load Excel workbook
        # classeur = load_workbook(nom_fichier)
        # feuille = classeur.active
        #     # Parcourir les lignes et les colonnes pour afficher les données
        # for ligne in feuille.iter_rows(values_only=True):
        #     data.append(ligne)
        # data.pop(0)
        # # print("Données chargées à partir du fichier Excel :", data)
        # # print('fkdkdsfklsfkmlfksdmfds')
        # # sys.stdout.flush()
        
        role=current_user.role
        name=current_user.full_name
        return render_template("steps/listeRecence.html",record=response.json(),role=role,name=name)
    except FileNotFoundError:
        print("Le fichier spécifié n'a pas été trouvé.")
        sys.stdout.flush()
        current_nameFile="liste_vehicule.xlsx"
        nom_fichier="FilesTemps/"+current_nameFile
        # Load Excel workbook
        classeur = load_workbook(nom_fichier)
        feuille = classeur.active
            # Parcourir les lignes et les colonnes pour afficher les données
        for ligne in feuille.iter_rows(values_only=True):
            data.append(ligne)
        data.pop(0)
        print("Données exception chargées à partir du fichier Excel :", data)
        return render_template("steps/listeRecence.html",record=data)
     

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return render_template("steps/listeRecence.html",record=data)
   
@app.route('/liste/recence/file',methods=['GET'])
def setviewDownload():
    path="FilesRecencement"
    p=os.listdir(path)
    files={}
    datas=[]
    for x in p :
        dat=x.split('_')
        files={"date":dat[0],"nom_fichier":x}
        datas.append(files)

    # return  dates
    return render_template("download/download.html",record=datas)
@app.route('/get_file_event',methods=['GET'])
def get_file_event():
    path="event"
    if not os.path.isdir(path):
            os.mkdir(path)
    p=os.listdir(path)
    files={}
    datas=[]
    for x in p :
        dat=x.split('_')
        files={"date":dat[0],"nom_fichier":x}
        datas.append(files)

    # return  dates
    return render_template("download/file_event.html",record=datas)
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return  result_str
@app.route('/sendTeamVehicule',methods=['POST'])
def sendTeam():
    env_chkc=current_user.env
    url_trp = config['TRP_DOMAIN_URL']
    env=config['environnement']
    urlseafile=config['URL_SEAFILE']
    if env_chkc==1 :
        urlseafile=config['URL_SEAFILE_PRO']
        url_trp=config['TRP_DOMAIN_URL_PROD']
    nameDirectoryPerso=get_random_string(8)
    nameDirectory=request.form['plaque']
    nom=request.form['nom']
    prenom=request.form['prenom']
    tel=request.form['tel']
    role=request.form['role']
    header = {
                "Content-Type":"application/json"
    }
    json_dat={"plaque":nameDirectory,"status":request.form['status'],"busList":request.form['busList'],"anne_exp":request.form['anne_exp'],"role":role,"nom":nom,"prenom":prenom,"tel":tel,"idSeafile":nameDirectoryPerso}
    da=json.dumps(json_dat)
    data_vehic={
                "content_files":da,
                "plaque":nameDirectory,
                "type" : request.form['role'],
                "status" : 1
            }
    response = requests.post(url_trp+"api/add_new_prepose", json=data_vehic, headers=header, timeout=120)
    # # print(response)
    # # sys.stdout.flush()
    # return  request.files
    permis_recto=''
    permis_verso=''
    cin_recto=''
    cin_verso=''
    cin_r_recto=''
    cin_r_verso=''
    permis_r_recto=''
    permis_r_verso=''
    filenameArray=[]
    pb=[]
    data={}
    datax=config['TOKEN_SEAFILE']
    
    # if env  == "prod" :
    #     url_trp = config['TRP_DOMAIN_URL_PROD']
    #     urlseafile=config['URL_SEAFILE_PRO']
    
    #TO DO : create 
    #create new directory  seafile personnel
    #generate
   
    nameDirectory=request.form['plaque']
    nom=request.form['nom']
    prenom=request.form['prenom']
    tel=request.form['tel']
    role=request.form['role']
    #data[0]={"plaque":nameDirectory,"role":role,"nom":nom,"prenom":prenom,"tel":tel,"idSeafile":nameDirectoryPerso}
    #send data in mysql  

    #pb.append(data[0])
    cnf.createDirectory(datax,urlseafile,nameDirectory,"")
    cnf.createDirectory(datax,urlseafile,"TEAM",nameDirectory)
    nameDirectoryfirst="TEAM"
    if 'badge_rc'in request.files:
        badge_rc=request.files['badge_rc']
        badge_rc_name=badge_rc.filename
        filenameArray.append({'name_files': badge_rc_name, 'type': 'Badge_R'})
        chemin = os.path.join("SeafileTemp",badge_rc_name)
        badge_rc.save(chemin)
    if 'badge_ch'in request.files:
        badge_ch=request.files['badge_ch']
        badge_ch_name=badge_ch.filename
        filenameArray.append({'name_files': badge_ch_name, 'type': 'Badge_C'})
        chemin = os.path.join("SeafileTemp",badge_ch_name)
        badge_ch.save(chemin)
    if 'permis_recto' in request.files:
        permis_recto=request.files['permis_recto']
        permis_recto_name=permis_recto.filename
        filenameArray.append({'name_files': permis_recto_name, 'type': 'Permis_r'})
        chemin = os.path.join("SeafileTemp",permis_recto_name)
        permis_recto.save(chemin)
    if 'permis_verso' in request.files:
        permis_verso=request.files['permis_verso']
        permis_verso_name=permis_verso.filename
        filenameArray.append({'name_files': permis_verso_name, 'type': 'Permis_v'})
        chemin = os.path.join("SeafileTemp",permis_verso_name)
        permis_verso.save(chemin)
    if 'cin_recto' in request.files:
        cin_recto=request.files['cin_recto']
        cin_recto_name=cin_recto.filename
        filenameArray.append({'name_files': cin_recto_name, 'type': 'cin_r'})
        chemin = os.path.join("SeafileTemp",cin_recto_name)
        cin_recto.save(chemin)
    if 'cin_verso' in request.files:
        cin_verso=request.files['cin_verso']
        cin_verso_name=cin_verso.filename
        filenameArray.append({'name_files': cin_verso_name, 'type': 'cin_v'})
        chemin = os.path.join("SeafileTemp",cin_verso_name)
        cin_verso.save(chemin)
    if 'cin_r_recto' in request.files:
        cin_r_recto=request.files['cin_r_recto']
        cin_r_recto_name=cin_r_recto.filename
        filenameArray.append({'name_files': cin_r_recto_name, 'type': 'cin_r_recto'})
        chemin = os.path.join("SeafileTemp",cin_r_recto_name)
        cin_r_recto.save(chemin)
    if 'cin_p_recto' in request.files:
        cin_p_recto=request.files['cin_p_recto']
        cin_p_recto_name=cin_p_recto.filename
        filenameArray.append({'name_files': cin_p_recto_name, 'type': 'cin_p_recto'})
        chemin = os.path.join("SeafileTemp",cin_p_recto_name)
        cin_p_recto.save(chemin)
    if 'cin_p_verso' in request.files:
        cin_p_verso=request.files['cin_p_verso']
        cin_p_verso_name=cin_p_verso.filename
        filenameArray.append({'name_files': cin_p_verso_name, 'type': 'cin_p_verso'})
        chemin = os.path.join("SeafileTemp",cin_p_verso_name)
        cin_p_verso.save(chemin)
    if 'cin_r_verso' in request.files:
        cin_r_verso=request.files['cin_r_verso']
        cin_r_verso_name=cin_r_verso.filename
        filenameArray.append({'name_files': cin_r_verso_name, 'type': 'cin_r_verso'})
        chemin = os.path.join("SeafileTemp",cin_r_verso_name)
        cin_r_verso.save(chemin)
    if 'permis_r_recto' in request.files:
        permis_r_recto=request.files['permis_r_recto']
        permis_r_recto_name=permis_r_recto.filename
        filenameArray.append({'name_files': permis_r_recto_name, 'type': 'Permis_rec_r'})
        chemin = os.path.join("SeafileTemp",permis_r_recto_name)
        permis_r_recto.save(chemin)
    if 'permis_r_verso' in request.files:
        permis_r_verso=request.files['permis_r_verso']
        permis_r_verso_name=permis_r_verso.filename
        filenameArray.append({'name_files': permis_r_verso_name, 'type': 'Permis_rec_v'})
        chemin = os.path.join("SeafileTemp",permis_r_verso_name)
        permis_r_verso.save(chemin)
    if 'photo_ch' in request.files:
        photo_ch=request.files['photo_ch']
        photo_ch_name=photo_ch.filename
        filenameArray.append({'name_files': photo_ch_name, 'type': 'photo_chauffeur'})
        chemin = os.path.join("SeafileTemp",photo_ch_name)
        photo_ch.save(chemin) 
    if 'photo_rc' in request.files:
        photo_rc=request.files['photo_rc']
        photo_rc_name=photo_rc.filename 
        filenameArray.append({'name_files': photo_rc_name, 'type': 'photo_receveur'})
        chemin = os.path.join("SeafileTemp",photo_rc_name)
        photo_rc.save(chemin)
    if 'photo_pr' in request.files:
        photo_pr=request.files['photo_pr']
        photo_pr_name=photo_pr.filename
        filenameArray.append({'name_files': photo_pr_name, 'type': 'photo_proprio'})
        chemin = os.path.join("SeafileTemp",photo_pr_name)
        photo_pr.save(chemin)
    cooperative="#"
    if 'cooperative' in request.form :
        cooperative=request.form['cooperative'] 
    # sendRecencements(pb,cooperative)
    ###get les contenu d fichier s'il existe ####
    getContentsjson=cnf.getContenuFiles(datax,urlseafile,nameDirectory,"TRP")
    dataj=[]
    try :
        if len(getContentsjson)==0 :
            dataj=[]
        else :
            dataj=getContentsjson
           
    except :
            dataj=[]
   
    try :
        cnf.deleteFileExist(nameDirectory,env_chkc)          
        for file_info in filenameArray:
            file_type = file_info.get('type')
            filenameq=file_info.get('name_files') 
            dataobject={}
            imageLue = Image.open("SeafileTemp/"+filenameq)
            #reduction taille image
            new_size=(600, 600)
            im1 = imageLue.resize(new_size)
            im1.save("liveImage/"+filenameq)
            #get Token 
            token=cnf.getTokenSeafile(datax, urlseafile)
            os.remove("SeafileTemp/"+filenameq)
            nameFile="liveImage/"+filenameq
            #send file
            namefilesup=cnf.sendFile(token, urlseafile,nameDirectoryfirst,nameFile,nameDirectory)
            os.remove("liveImage/"+filenameq)
            dataobject={'url_name':namefilesup,'type':file_type,'idSeafile':nameDirectoryPerso}

            dataj.append(dataobject)      
            
        cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(dataj))  
        data_seafile={
            "plaque":nameDirectory,
            "json_seafile":json.dumps(dataj)
        }
        try :
            response_seafile = requests.post(url_trp+"api/update_seafile", json=data_seafile, headers=header, timeout=120)
            print(response_seafile)
            sys.stdout.flush()
        except :
            pass
    except Exception as e :
        print(e)
        return e
    return "Team véhicule envoyé avec succès!"
@app.route('/sendPointage',methods=['POST'])
def sendPointage():
    pb=[]
    devant_name=''
    filenameArray=[]
    recencement='non'
    ell_ext=""
    ell_int=""
    annonceur=""
    comments=""
    if 'cooperative' in request.form:
        cooperative=request.form['cooperative']
    else :
        cooperative="#"
    if 'config_siege' in request.form:
        config_siege=request.form['config_siege']
    else:
        config_siege=''
    if 'plaque_im' in request.form:
        plaque=request.form['plaque_im']

    if 'marque' in request.form:
        marque=request.form['marque']
    if 'nbplc_vehic' in request.form:
        nbplc_vehic=request.form['nbplc_vehic']
    if 'ell_int' in request.form:
        ell_int=request.form['ell_int']
    if 'ell_ext' in request.form:
        ell_ext=request.form['ell_ext']
        
    if 'recencement' in request.form:
        recencement=request.form['recencement']
    if 'data_json' in request.form:
        data=request.form['data_json']
    if 'annonceur' in request.form:
        annonceur=request.form['annonceur']
    if 'comments' in request.form:
        comments=request.form['comments']
        try :
            val=json.loads(data)
            pb.append(val)
        except :
            print('or')
    if 'userid' in request.form:
        userid=request.form['userid']
    if 'username' in request.form:
        username=request.form['username']
    env=config['environnement']
    if 'env' in request.form:
        env=request.form['env']
    nameDirectory=request.form['plaque_im'] 
    datax=config['TOKEN_SEAFILE']
    urlseafile=config['URL_SEAFILE']
    url_trp = config['TRP_DOMAIN_URL']
    env_chkc=current_user.env
    if env_chkc==1 :
        urlseafile=config['URL_SEAFILE_PRO']
        url_trp=config['TRP_DOMAIN_URL_PROD']
    header = {
                "Content-Type":"application/json"
            }
    data_vehic={
                "full_name_user_rec":current_user.full_name,
                "num_immatriculation":plaque,
                "marque" : marque,
                "type_transport_id" : 1,
                "propietaire_id" : 0,
                "nbplc_vehic" :int(nbplc_vehic),
                "chauffeur_id": 0,
                "receveur_id" : 0,
                "variance_ligne_id" : cooperative,
                "recencement":recencement,
                "ell_ext":ell_ext,
                "ell_int":ell_int,
                "config_siege":config_siege,
                "annonceur":annonceur,
                "comments":comments,
                "src":"TPE_COLLECT"
            }
    print(data_vehic)
    print("call api transport")
    print(url_trp+"api/add_new_vehicle")
    response = requests.post(url_trp+"api/add_new_vehicle", json=data_vehic, headers=header, timeout=120)
    sys.stdout.flush()
    if 'devant_vehicule' in request.files:
        # return jsonify({"error": "No 'devant_vehicule' file provided."}), 400
        devant=request.files['devant_vehicule']
        devant_name=devant.filename
        filenameArray.append({'name_files': devant_name, 'type': 'devant'})
        chemin = os.path.join("SeafileTemp",devant_name)
        devant.save(chemin) 
    
    
    
    ###get les contenu d fichier s'il existe ####
        getContentsjson=cnf.getContenuFiles(datax,urlseafile,nameDirectory,"TRP")
        dataj=[]
    try :
        if len(getContentsjson)==0 :
            dataj=[]
        else :
            dataj=getContentsjson
           
    except :
            dataj=[]
    cnf.createDirectory(datax,urlseafile,nameDirectory)
    cnf.createDirectory(datax,urlseafile,"GALERY",nameDirectory)
    nameDirectoryfirst="GALERY"
    # chemin = os.path.join("SeafileTemp",filename)
    try :
        cnf.deleteFileExist(nameDirectory,env_chkc)      
        for file_info in filenameArray:
            file_type = file_info.get('type')
            filenameq=file_info.get('name_files') 
        # for i in range(len(filenameArray)):
            
            dataobject={}
            imageLue = Image.open("SeafileTemp/"+filenameq)
                                    #reduction taille image
            new_size=(600, 600)
            im1 = imageLue.resize(new_size)
            im1.save("liveImage/"+filenameq)
            #                         #get Token 
            token=cnf.getTokenSeafile(datax, urlseafile)
            os.remove("SeafileTemp/"+filenameq)
            
            nameFile="liveImage/"+filenameq
                                    #send file
            namefilesup=cnf.sendFile(token, urlseafile,nameDirectoryfirst,nameFile,nameDirectory)
            # getContentsjson=cnf.getContenuFiles(token, urlseafile,nameDirectory,nameFile)
            os.remove("liveImage/"+filenameq)
            dataobject={'url_name':namefilesup,'type':file_type}
                       
            dataj.append(dataobject)
                        
                
        cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(dataj))  
        data_seafile={
            "plaque":nameDirectory,
            "json_seafile":json.dumps(dataj)
        }
        try :
            response_seafile = requests.post(url_trp+"api/update_seafile", json=data_seafile, headers=header, timeout=120)
            print(response_seafile)
            sys.stdout.flush()
        except :
            pass
            # return "ok"
        return 'Gallerie envoyéé avec succès!'
    except Exception as e :
        return e
    # try :
    #     url_trp = config['TRP_DOMAIN_URL']
    #     if(env.lower()=='prod'):
    #         url_trp = config['TRP_DOMAIN_URL_PROD']
    #     header = {
    #         "Content-Type":"application/json"
    #     }
    #     data_vehic={
    #         "num_immatriculation":plaque,
    #         "marque" : marque,
    #         "type_transport_id" : 1,
    #         "propietaire_id" : 0,
    #         "nbplc_vehic" :int(nbplc_vehic),
    #         "chauffeur_id": 0,
    #         "receveur_id" : 0,
    #         "variance_ligne_id" : cooperative,
    #         "src":"TPE_COLLECT"
    #     }
       
    #     response = requests.post(url_trp+"api/addVehicule", json=data_vehic, headers=header, timeout=120)
    #     print(response)
    #     sys.stdout.flush()
    #     return "ok"
    # except Exception as e:
    #     print(e)
    #     sys.stdout.flush()
    #     return e
    # # return sendExcelData(pb,cooperative,userid,username)
        

@app.route('/download',methods=['POST'])
def uploadMyFiles():
    fichier = request.files['fichier']
   
    filename1 =fichier.filename
    
    filename=filename1.replace(' ','')
    
    # data=patoolib.extract_archive(fichier,"SeafileTemp")
    
    ###check name file and type####
    firstDirectory=filename.split("_")
    countf=int(len(firstDirectory)-1)
    typefl=[]
    for n in range(countf):
        typefl.append(firstDirectory[n])
    type_file=switch('_'.join(typefl))
    secnameDirec=firstDirectory[countf]
    firstDirectory=secnameDirec.split(".rar")
    NAME_DIRECTORY=firstDirectory[0] if(type(firstDirectory) == list) else ""   
    datax=config['TOKEN_SEAFILE']
    urlseafile=config['URL_SEAFILE']
    env_chkc=current_user.env
    if env_chkc==1 :
        urlseafile=config['URL_SEAFILE_PRO']
        url_trp=config['TRP_DOMAIN_URL_PROD']
   
    ###get les contenu d fichier s'il existe ####
    
    getContentsjson=cnf.getContenuFiles(datax,urlseafile,NAME_DIRECTORY,"TRP")
    # p=cnf.deleteFileExist(NAME_DIRECTORY)
    cnf.deleteFileExist(NAME_DIRECTORY,env_chkc)
    dataj=[]
    try :
        if len(getContentsjson)==0 :
            dataj=[]
        else :
            dataj=getContentsjson
            # t={"type":"re","frer":"rezre"}
    except :
            dataj=[]
 
    # return  dataj
    if (NAME_DIRECTORY!="") :
        datax=config['TOKEN_SEAFILE']
        urlseafile=config['URL_SEAFILE']
        cnf.createDirectory(datax,urlseafile,NAME_DIRECTORY)
        chemin = os.path.join("SeafileTemp",filename)
        fichier.save(chemin)
        
        # extraire le fichier
        rf = rarfile.RarFile(chemin)
        rf.extractall("SeafileTemp")
        rf.close()
        
        os.remove("SeafileTemp/"+filename)
        listFiles=os.listdir('SeafileTemp')
        with rarfile.RarFile(fichier) as rf:
            contain=rf.namelist()
        count=len(contain)
        
        for listFile in listFiles:
            
            new_directoryname=listFile
            nameDirectory =NAME_DIRECTORY#new_directoryname.replace(' ','')
            dataobject={}
            dataobject1=[]
            fileD="Cpp-Transport"
            liste_dictionnaires=[]
          
            
            contenus=os.listdir("SeafileTemp/"+listFile)
            start_time = time.time()
            try :
                for contenuDirectory in contenus:
                        # dataobject['type']=type_file
                        imageLue = Image.open("SeafileTemp/"+listFile+'/'+contenuDirectory)
                                    #reduction taille image
                        new_size=(600, 600)
                        im1 = imageLue.resize(new_size)
                        im1.save("SeafileTemp/"+listFile+'/'+contenuDirectory)
                                    #get Token 
                        token=cnf.getTokenSeafile(datax, urlseafile)
                        nameFile="SeafileTemp/"+listFile+'/'+contenuDirectory
                                    #send file
                        namefilesup=cnf.sendFile(token, urlseafile,nameDirectory,nameFile)
                        getContentsjson=cnf.getContenuFiles(token, urlseafile,nameDirectory,nameFile)
                        dataobject={'url_name':namefilesup,'type':type_file}
                                    #urlseafile+"/pictures?xys="+fileD+"|"+c[0]+"|"+namefilesup
                        # dataobject1.append(dataobject)
                        # datajson=dataj.append(dataobject)#json.dumps(dataj.append(dataobject))
                        dataj.append(dataobject)
                        
                        # dataj.append(dataobject)    
                                #send json  files
                        
                                    #delete dossier
                cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(dataj))   
                # cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(datajson))        
            except Exception as e :
                    print(e)
                    # shutil.rmtree('SeafileTemp/'+listFile)
                    # contain.pop()
                    # fileD="Cpp-Transport"
                    # dataobject={}
                    # dataobject1=[]
                    # liste_dictionnaires=[]
                    
                    # try :
                    #         c=nameDirectory.split('/')       
                    #         for file_name1 in contain:
                            
                    #             dataobject['type']='photo'
                    #             imageLue = Image.open("SeafileTemp/"+file_name1)
                    #             #reduction taille image
                    #             new_size=(600, 600)
                    #             im1 = imageLue.resize(new_size)
                    #             im1.save("SeafileTemp/"+file_name1)
                    #             #get Token 
                    #             token=cnf.getTokenSeafile(datax, urlseafile)
                    #             nameFile="SeafileTemp/"+file_name1
                    #             #send file
                    #             namefilesup=cnf.sendFile(token, urlseafile,nameDirectory,nameFile)
                    #             dataobject={'url_name':namefilesup}
                    #             #urlseafile+"/pictures?xys="+fileD+"|"+c[0]+"|"+namefilesup
                    #             dataobject1.append(dataobject)
                    #             datajson=json.dumps(dataobject1)
                        
                    #         #send json  files
                        
                            
                    #         cnf.sendFileJson(datax,urlseafile,nameDirectory,datajson)
                    #             #delete dossier
                    #         shutil.rmtree('SeafileTemp/'+nameDirectory1)
                    # except Exception as e :
                    #         print(e)
                    #         shutil.rmtree('SeafileTemp/'+nameDirectory)
            
            shutil.rmtree('SeafileTemp/'+listFile)
        return    ("\n--- %s seconds ---" % (time.time() - start_time))
    else :
        return Response("{'error':'Name of directory is not found'}", status=404, mimetype='application/json')
@app.route('/checking',methods=['GET'])
def checkSeafile():
    conf=cnf.checkServerSeafile()  
    status='success' 
    if(conf==0):
       status='failed'
    return status
@app.route('/getAllPointage',methods=['POST'])
def getAllPointage():
    url_sql=config['URL_MYSQL']
    username=config['USER_MYSQL']
    password=config['PASSWORD']
    databasename=config['DATABASE_NAME']
    database_config={
        "username":username,
        "passwd":password,
        "url_serve":url_sql,
        "database":databasename
    }
    cnf.connect(appid, rest_api_key,masterkey,url)

    dateDebut = request.form['dateDebut']
    dateFin = request.form['dateFin']
    pointage=cnf.ExtractPointage(database_config,dateDebut,dateFin)
    return 'ok'
@app.route('/getPointage')
def getPointage():
   # pap=cnf.getPaps(database_config,str(d1))
    return render_template('pointage.html')
@app.route('/getCommission')
def getCommission():
    return render_template('getCommission.html')

@app.route('/getDevice',methods=['GET'])
def getDevice():
    return render_template("getDevice.html")
@app.route('/getDevice',methods=['POST'])
def getAllDevice():
    return render_template("getDevice.html")

    #return render_template("index.html",data=url)

@app.route('/sendRequestVersement',methods=['GET'])
def sendversement():
    url=config['APP_URL']+"storevers"
    return render_template("requestVersement.html",data=url)

@app.route('/showDate',methods=['GET'])
def showing():
    url=config['APP_URL']+"store"
    return render_template("show.html",data=url)
@app.route('/store',methods=['POST'])
def getData():
    #return request.form['dateDebut']
    if request.method == 'POST':
      dateDebut = request.form['dateDebut']
      dateFin = request.form['dateFin']
      v=run_program()
      p=v.run_application(dateDebut,dateFin)
      return p
    #   p=extract(dateDebut,dateFin)

    #   return p
      
@app.route('/storevers',methods=['POST'])
def sendVersement():
    if request.method == 'POST':
      dateDebut = request.form['dateDebut']
      dateFin = request.form['dateFin']
      v=Versement()
      versement=v.versementPy(dateDebut,dateFin)
      return versement   
#test pass variable
def extract(datedebut,dateFin):
    maincpp= main()
    data={
        "dateDebut":datedebut,
        "dateFin":dateFin,
    }
    
    p=maincpp.extractDataw(data)
    return p
######## Versement Debut  ############
def versementPy(datec,dateFin) :
    #config serveur parse
    appid=config['PARSE_APP_ID']
    rest_api_key=config['PARSE_API_KEY_REST']
    masterkey=config['PARSE_MASTER_KEY']
    url=config['URL_DOMAIN']
    #config serveur mysql
    url_sql=config['URL_MYSQL']
    username=config['USER_MYSQL']
    password=config['PASSWORD']
    databasename=config['DATABASE_NAME']
    database_config={
        "username":username,
        "passwd":password,
        "url_serve":url_sql,
        "database":databasename
    }
    pub_key_core =config['PUBLIC_KEY_MP']
    pri_key_core = config['PRIVATE_KEY_MP']
    url_core = config['CORE_DOMAIN_URL_MP']
    s=pub_key_core+":"+pri_key_core
    datax=base64.b64encode(s.encode('UTF-8')).decode('UTF-8')
   
    # separateDate=datec.split('-')
    # month=int(separateDate[1])
    # year=separateDate[0]
    # dayd=separateDate[2]
    # date=str(dayd)+"/"+str(month)+"/"+str(year) 
    separateDate=datec.split('-')
    month=int(separateDate[1])
    year=int(separateDate[0])
    dayd=int(separateDate[2])
    datecc=str(dayd)+"/"+str(month)+"/"+str(year)
    #fin
    separateDate1=dateFin.split('-')
    month1=int(separateDate1[1])
    year1=int(separateDate1[0])
    dayd1=int(separateDate1[2])
    datefin=str(dayd1)+"/"+str(month1)+"/"+str(year1)
   
     #get list date#
    start = date(year,month,dayd)
    end = date(year1, month1, dayd1)
    value=(end-start).days

    periods = value+1
    daterangeversement = []
    for day in range(periods):
        datep = (start + datetime.timedelta(days = day)).isoformat()
        daterangeversement.append(datep)
    #end list# 
    cnf.connect(appid,rest_api_key,masterkey,url)
    for datex in daterangeversement :
        #1-get Liste Vehicle in event
        #2-get List proprio 
        #3-get Vehicle proprio 
        vehicu=cnf.getAllVehicule(f"{datex}")
    
        # tokenbear=cnf.getTokenCore(datax,url_core)
        tab=[]
    #prop=cnf.sendInfoCore(url_core,paramProprio,tokenbear)
        if len(vehicu)>0 :
            for x in vehicu : 
                ca=cnf.getCAParBus(str(f"{date}"),x)
                obj=cnf.getObjectIdEventComm(str(f"{date}"),x)
                com=cnf.getCommissionParBus(str(f"{date}"),x)
                amount=float(ca)-float(com)  
                paramProprio=cnf.infoProprio(database_config,x,str(f"{date}"),amount)
                tokenbear=cnf.getTokenCore(datax,url_core)
                
                if(int(amount)<=0) :
                    return 'Vérifier svp votre montant'
                else :
                    prop=cnf.sendValueCore(url_core,paramProprio,tokenbear,database_config,obj)
                    tab.append(prop)
            return ' '.join(str(e) for e in tab)
    else :
        tab.append('Pas de véhicule en service')
        return ' '.join(str(e) for e in tab)
######## Versement  FIN  ############
@app.route('/getAllcommission',methods=['POST'])
def getDataCommission():
    appid=config['PARSE_APP_ID']
    rest_api_key=config['PARSE_API_KEY_REST']
    masterkey=config['PARSE_MASTER_KEY']
    url=config['URL_DOMAIN']
    #config serveur mysql
    url_sql=config['URL_MYSQL']
    username=config['USER_MYSQL']
    password=config['PASSWORD']
    databasename=config['DATABASE_NAME']
    database_config={
        "username":username,
        "passwd":password,
        "url_serve":url_sql,
        "database":databasename
    }
    # cnf.connect(appid,rest_api_key,masterkey,url)
    #return request.form['dateDebut']
    p=cnf.getVehiculeAll(database_config)
  
    if request.method == 'POST':
      dateDebut = request.form['dateDebut']
      dateFin = request.form['dateFin']
      for x in p :
          com=cnf.getCommissionParExtract(database_config,str(f"{dateDebut}"),str(f"{dateFin}"),x)
      
      return 'ok'
      
######## Send SMS Debut  ############
@app.route('/signaler')
def sendSms():
    today = date.today()
    d1 = today.strftime("%Y-%m-%d")
    url_sql=config['URL_MYSQL']
    username=config['USER_MYSQL']
    password=config['PASSWORD']
    databasename=config['DATABASE_NAME']
    database_config={
        "username":username,
        "passwd":password,
        "url_serve":url_sql,
        "database":databasename
    }
    # print(database_config)
    
    pap=cnf.getPaps(database_config,str(d1))
    return render_template('sendSms.html',data=pap) #"user",name="ererere"
@app.route('/getAllDevice',methods=['POST'])
def getDeviceCppEsper():
    if request.method == 'POST':
      types = request.form['type']
      esp=CppEsper()
      p=esp.initialize(types)
      return p
@app.route('/testsms',methods=['GET'])
def testsms():
    import requests
    from requests.auth import HTTPBasicAuth

    url = "https://api.blsmsgw.com:8443/bin/send"

    data = {
        "source_addr": "CPP-SYSTEM",
        "encoding": 0,
        "message": "SMS Test from Python API",
        "recipients": [
            {
                "recipient_id": 111,
                "dest_addr": "261343276968"
            }
        ]
    }

    username = "evelyn.johary@cpp-system.com"
    password = "99737616275075426154901"

    response = requests.post(url, json=data, auth=HTTPBasicAuth(username, password))
    # return response.status_code
    if response.status_code == 200:
        print("SMS sent successfully!")
        return response.text
    else:
        print("SMS sending failed. Status code:", response.status_code)
        print("Response:", response.text)
        return 'ok'
    # secret_key = "Y2RhNmIzODkwZjQ5MzQ5MWY2ZGNlZWRmNGQzZmUwM2E1ZmZjZWMxZjIxMGQ4MmQ0MWU3NDlhMTExYmExOTU5Nw=="#"YWUyMGJhYWE2YzFhOGNmYjA1ZGFhMzVhM2U2MjE5NWI0MGE3ZTYxNTA1NjY5OTI4YzRhYWM5YTI1MWRhYjNmNw=="
    # api_key = "22a7a835674d72a4"#"8be0dbfc0496169e"
    
    # basicc=api_key+":"+secret_key
    # content_type = "application/json"
    # source_addr ="CPP-SYSTEM"
    # session = requests.Session()
    # session.auth = (api_key, secret_key)
    # # heards={ 
    # # 'cache-control': 'no-cache',
    # # 'Content-Type': content_type,
    # # }
    # # URL = 'https://apisms.beem.africa/public/v1/sender-names'#apisms.beem.africa/v1/send'#'https://apisms.beem.africa/public/v1/sender-names' #
    # # response = session.get(URL, json={}, headers=[])
    # # print(response.text)
    # # return response.json()

    # base_url = "https://api.blsmsgw.com:8443/bin/send"
    # username = "evelyn.johary@cpp-system.com"#'22a7a835674d72a4'
    # password = 99737616275075426154901
    
    # #print(headers)
    # # Encode the basicc string in Base64
    # token = base64.b64encode(basicc.encode()).decode()
    #  # payload = {
    # #     'source_addr': source_addr,
    # #     "schedule_time": "",
    # #     "encoding":"0",
    # #     'message': 'Hello, this is a test message.',
    # #     "recipients": [
    # #             {
    # #                 "recipient_id": 1,
    # #                 "dest_addr": "261333109923"
    # #             }
    # #     ]
    # # }
    # headers = {
    #     'cache-control': 'no-cache',
    #     'Content-Type': 'application/json',
    # }

   
    # payload= {
    #     'USERNAME':username,
    #     'PASSWORD':password,
    #     'DESTADDR':"261343276968",
    #     'SOURCEADDR':'CPP-SYSTEM',
    #     'MESSAGE':"ddsds"
    # }
   
    # response = requests.post(url=base_url,data=payload,headers=headers,verify=False)
    
    # response_status = {'status_code': str((response.__dict__))}
    # return (response_status)
    # if response.status_code == 200:
    #     return (response)
    # else:
    #     return ('Error: '+str(response.status_code)+" "+response.text)

@app.route('/getFile',methods=['GET'])
def getFileDeviceCppEsper():
      esp=CppEsper()
      p=esp.getnerateFileXlsx('')
      return p
#set data versement batch 
@app.route('/task/versement',methods=['GET'])
def sendBatchVersement():
      today = date.today().strftime("%d/%m/%Y")
      vers=run_versement()
      p=vers.run_application(today)
      return {"status":"200","Message":"Info create with successfully!"}
#send all versement in date
 
@app.route('/sendSmsToProprio',methods=['POST'])
def sendMessage():
    url_sql=config['URL_MYSQL']
    username=config['USER_MYSQL']
    password=config['PASSWORD']
    databasename=config['DATABASE_NAME']
    core_url = config['CORE_DOMAIN_URL_MP']
    database_config={
        "username":username,
        "passwd":password,
        "url_serve":url_sql,
        "database":databasename,
        "core_agent":config['CORE_AGENT_X']
        }
        
    types = request.form['type']
    vehicule = request.form['vehic']
    cnf.sendSmsviaCpp(core_url,database_config,vehicule, types)
    return ""   
######## Send SMS FIN  ############
@app.route('/pay_cpp',methods=['GET','POST'])
def pay_cpp():
    
    from datetime import datetime

    # Obtenir la date actuelle
    now = datetime.now()

    # Extraire le mois et l'année
    current_month = now.month
    current_year = now.year
   
    if request.method == 'POST':
        #data company et partner
        form_data = request.form
        company=form_data.get('company')
        partner=form_data.get('partner')
        month=int(form_data.get('month'))
        year=int(form_data.get('year'))
    elif request.method == 'GET':
        #data company et partner
        company="7qXmlUm1EE"
        partner="liwlKgNjkE"
        month=4#int(current_month)
        year=int(current_year)
    
    
    try :
        type_trs="TRANSACTION"
        url = config['PARSE_URL_PAY']
        appid = config['PARSE_APP_ID_PAY']
        masterkey = config['PARSE_MASTER_KEY_PAY']
        rest_api_key=config['PARSE_API_REST_KEY_PAY']
        headers = {
            "X-Parse-Application-Id": f'{appid}',
            "X-Parse-REST-API-Key":  f'{rest_api_key}',
            "X-Parse-Master-Key":  f'{masterkey}',
            "Content-Type": "application/json"
        }
        params = urllib.parse.urlencode({"limit":100000,"where": json.dumps({
                "month":int(month),
                "year":int(year),
                # "day":24,
                "company": {'__type': 'Pointer', 'className': 'Company', 'objectId': company},
                "partner": {'__type': 'Pointer', 'className': 'CompanyCustomer', 'objectId':partner},
                "type":type_trs,
            }),"include":"company,customer,partner.customer,transaction,transaction.status"})
        myurl=url+'/classes/PartnerEvent'
        result=requests.get(myurl,params=params,headers=headers)
          # print("Status : "+str(result.status_code))
        x=result.json()
        data=[]  
        values=x['results']
        p=0
        numbill = random.randint(0, 10000)   
        from datetime import date
        date_emis = date.today()
        status="Payé"
        id_partner=""
        amountTotal=0
        for x in values :
                #info Partenaire
                adrress_part=x.get('partner', {}).get('customer', {}).get('address') if 'partner' in x and 'customer' in x['partner'] else None 
                email_part=x.get('partner', {}).get('customer', {}).get('email') if 'partner' in x and 'customer' in x['partner'] else None 
                phone_part=x.get('partner', {}).get('customer', {}).get('phone') if 'partner' in x and 'customer' in x['partner'] else None 

                #info Company
                data_v={
                    #info Comp
                    "name":x['company']['name'] ,
                    "logo":x['company']['logo'] ,
                    "phone":x['company']['phone'] ,
                    "address":x['company']['address'] ,
                    "email":x['company']['email'] ,
                    #info Part
                    "name_partner":x['partner']['customer']['firstname'] ,
                    "address_part":adrress_part if adrress_part else "-",
                    "email_partner":email_part if email_part else "-",
                    "phone_partner":phone_part if phone_part else "-",
                    #transaca
                    "amount_initial":x['transaction']['amount_initial'] ,
                    "month":x['month'] ,
                    "year":x['year'] ,
                    "numbill":numbill ,
                    "status":x['transaction']['status']['name'],
                    
                }
                data.append(data_v)
                p+=1
                # # Begin info company
                repres_name=x['company']['name']
                logo=x['company']['logo']
                phone_company=x['company']['phone']
                email_company=x['company']['email']
                address=x['company']['address'] 
                # #  End info company
                # # TO DO Begin info partner

                repres_name_partner=x['partner']['customer']['firstname'] 
                address_part=adrress_part if adrress_part else "-"    
                phone_partner=phone_part if phone_part else "-"
                email_partner=email_part if email_part else "-"
              
                #   End info partner
                amount=x['transaction']['amount_initial'] 
                amountTotal+=amount
                month=x['month']
                year=x['year']
                tva=0
                partiel=1  #1 if true ,if false  mensuel
                sum_ttc=0
                types=x['type']
        
                num_bill=str(numbill)
                
                total_operation=p
                ref="CPP-FACT-TRS-"+str(month)+str(year)+"-"+str(num_bill)
                label="POST PAY pour les "+str(x['type'])+"  mois de"     
                if(str(x['type'])=="COMMISSION"):
                    ref="CPP-FACT-COMM-"+str(month)+str(year)+"-"+str(num_bill) 
        data_pay_transac={
                            "objectIdCore":x['objectId'],
                            "amount":float(),
                            "company":x['company']['objectId'],
                            "month":int(month),
                            "year":int(year)
                }  
        objectId=model_api.CppApi.create_transact_payre(data_pay_transac)  
        if(objectId != "#|#"):
            components = objectId.split('|')
        # rendered_html = render_template('templates_pdf/facture.html',partiel=partiel,label=label,record=values,amountTotal=amountTotal,url_image=logo,date_emis=date_emis,total_operation=total_operation,company=repres_name,phone_company=phone_company,email_company=email_company,status=status,tva=tva,sum_ttc=sum_ttc,amount=amount,partner=id_partner,partner_name=repres_name_partner,partner_phone=phone_partner,partner_email=email_partner,ref=ref,month=month,year=year)   
        rendered_html = render_template(
                'templates_pdf/facture.html',
                partiel=partiel,
                label=label,
                sum_ttc=str(amount),
                record=values,
                components=components[1],
                amountTotal=amountTotal,
                url_image=logo,
                date_emis=date_emis,
                total_operation=total_operation,
                company=repres_name,
                phone_company=phone_company,
                email_company=email_company,
                adress_part=address_part,
                status=status,
                tva=tva,
                amount=amount,
                partner=id_partner,
                partner_name=repres_name_partner,
                partner_phone=phone_partner,
                partner_email=email_partner,
                ref=ref,
                month=month,
                year=year
        )
        rendered=generate_pdf(rendered_html,year,month,num_bill)
        return rendered
    except Exception as e :
        # print(e)
        return str(e)
    #generate invoice
    
######## Send SMS FIN  ############

def uploadMyFilesTask():
    fichier = request.files['fichier']
   
    filename1 = fichier.filename
    cnf.getTaskToken()
def switch(typefile):
    if typefile == "P":
        return "Papier_vehicule"
    elif typefile == "G_EXT":
        return "Exterieur_vehicule"
    elif typefile == "G_EXT_L":
        return "gauche"
    elif typefile == "G_EXT_R":
        return "droite"
    elif typefile == "G_INT":
        return "Interieur_vehicule"
    elif typefile == "G":
        return "Galery_vehicule"
    elif typefile == "T":
        return "team_chauffeur"    
###FIN#####
@app.route('/pictures',methods=['GET'])
def setviewVehicule():

# Étape 1 : select * from table where id > 0
   filtered_cooperatives = Cooperatives.query.filter(Cooperatives.id > 0).all()
   
# Étape 2 : select  *  
   filtered_cooperative_names = [Cooperatives for Cooperatives in filtered_cooperatives]

   return render_template("steps/imageVehicule.html",record=filtered_cooperative_names)
@app.route('/edit_vehicle/', defaults={'bus_number': None}, methods=['GET'])
@app.route('/edit_vehicle/<string:bus_number>',methods=['GET'])
def editVehicle(bus_number):
   # Étape 1 : select * from table where id > 0
#    filtered_cooperatives = Cooperatives.query.filter(Cooperatives.id > 0).all()
   
#    # Étape 2 : format data
#    filtered_cooperative_names = [Cooperatives for Cooperatives in filtered_cooperatives]
   header = {
                "Content-Type":"application/json"
    }
   role=current_user.role
   name=current_user.full_name
   env=config['environnement']
   url_trp =config['TRP_DOMAIN_URL']
   urlseafile=config['URL_SEAFILE']
   env_chkc=current_user.env
   datax=config['TOKEN_SEAFILE']
   if env_chkc==1 :
       url_trp =config['TRP_DOMAIN_URL_PROD']
       urlseafile=config['URL_SEAFILE_PRO']
   
   response = requests.get(url_trp+"api/get_ligne", json={}, headers=header, timeout=120)
   
   record=response.json()
   dataj=[]
   types=[]
   devant_image = ""
   derriere_image = ""
   gauche_vehicule = ""
   droite_vehicule = ""
   interieure_vehicule = ""
   Licence = ""
   Licence_Verso = ""
   Assurance = ""
   nif_stat_r = ""
   nif_stat_v = ""
   visite_technique = ""
   Carte_grise_recto = ""
   Carte_grise_verso = ""
   cin_p_recto = ""
   cin_p_verso = ""
   photo_pr = "",
   photo_receveur="",
   Permis_rec_v="",
   Permis_rec_r="",
   cin_r_verso="",
   cin_r_recto="",
   Badge_R=""
   photo_chauffeur=""
   cin_v=""
   cin_r=""
   Permis_v=""
   Permis_r=""
   Badge_C=""
   nom_rece = ""
   nom_chf = ""
   prenom_chf = ""
   anne_exp_chf = ""
   tel_chf = ""
   role = ""
   status_chf = ""
   prenom_rece = ""
   anne_exp_rece = ""
   tel_rece = ""
   role = ""
   role = ""
   status_rece = "" 
   nom_proprio = "" 
   pnom_proprio = "" 
   tel_prop = "" 
   if request.view_args.get("bus_number") :
       bus=request.view_args.get("bus_number")
       getContentsjson=cnf.getContenuFiles(datax,urlseafile,bus,"TRP")
       response_preps = requests.get(url_trp+"api/get_preps/"+bus, json={}, headers=header, timeout=120)
       chauffeurs = []
       receveurs = []
       proprio = []
    #    response_preps = requests.get(url_trp+"api/get_preps/"+bus, json={}, headers=header, timeout=120)
           
    #    record_preps=response_preps.json()
    #    return response_preps.json()
       try :
            response_preps = requests.get(url_trp+"api/get_preps/"+bus, json={}, headers=header, timeout=120)
           
            record_preps=response_preps.json()
            # return response_preps
            for item in record_preps:
                # if(item["type"]=="chauffeur"):
                    content = json.loads(item["content_files"])  # Convertir JSON string en dictionnaire
                    if(content["role"]=="chauffeur"):
                        info = {
                            "plaque": content["plaque"],
                            "status": content["status"],
                            "busList": content["busList"],
                            "anne_exp": content["anne_exp"],
                            "role": content["role"],
                            "nom": content["nom"],
                            "prenom": content["prenom"],
                            "tel": content["tel"],
                            "idSeafile": content["idSeafile"]
                        }
                        chauffeurs.append(info)
                    elif(content["role"]=="proprietaire"):
                # elif(item["type"]=="proprietaire"):
                    # content = json.loads(item["content_files"])  # Convertir JSON string en dictionnaire
                        infop = {
                            "plaque": content["plaque"],
                            "status": content["status"],
                            "busList": content["busList"],
                            "anne_exp": content["anne_exp"],
                            "role": content["role"],
                            "nom": content["nom"],
                            "prenom": content["prenom"],
                            "tel": content["tel"],
                            "idSeafile": content["idSeafile"]
                        }
                        proprio.append(infop)
                    elif(content["role"]=="receveur"):
                        info1 = {
                            "plaque": content["plaque"],
                            "status": content["status"],
                            "busList": content["busList"],
                            "anne_exp": content["anne_exp"],
                            "role": content["role"],
                            "nom": content["nom"],
                            "prenom": content["prenom"],
                            "tel": content["tel"],
                            "idSeafile": content["idSeafile"]
                        }
                        receveurs.append(info1) 
             
            if chauffeurs :
                for item in  chauffeurs :
                    nom_chf = item['nom']
                    prenom_chf = item['prenom']
                    anne_exp_chf = item['anne_exp']
                    tel_chf = item['tel']
                    role = item['role']
                    status_chf = item['status']
            if receveurs :
                for item1 in  receveurs :
                    nom_rece = item1['nom']
                    prenom_rece = item1['prenom']
                    anne_exp_rece = item1['anne_exp']
                    tel_rece = item1['tel']
                    role = item1['role']
                    status_rece = item1['status']
            if proprio :
                for item2 in  proprio :
                    nom_proprio = item2['nom']
                    pnom_proprio = item2['prenom']
                    tel_prop= item2['tel']
                  
       except :
           nom_rece=""
           prenom_rece=""
           anne_exp_rece=""
           role=""
           tel_rece=""
           status_rece=""
           nom_chf = ""
           prenom_chf = ""
           anne_exp_chf = ""
           tel_chf = ""
           role = ""
           status_chf = ""
           nom_proprio = "" 
           pnom_proprio = "" 
           tel_prop = "" 
    # # Résultat des listes
    #    print("Chauffeurs:")
    #    print(chauffeurs)

    #    print("\nPropriétaires:")
    #    print(proprio)

    #    print("\nReceveurs:")
    #    print(receveurs)
    #    sys.stdout.flush()
# Trier les données par type
       
                # if chauffeurs and "anne_exp" in chauffeurs[0] and chauffeurs[0]["anne_exp"]:
                #     anne_exp_chf=chauffeurs[0]["anne_exp"]
                # if chauffeurs and "nom" in chauffeurs[0] and chauffeurs[0]["nom"]:
                #     nom_chf=receveurs[0]["nom"]
                # if chauffeurs and "prenom" in chauffeurs[0] and chauffeurs[0]["prenom"]:
                #     prenom_chf=receveurs[0]["prenom"]
                # if chauffeurs and "tel" in chauffeurs[0] and chauffeurs[0]["tel"]:
                #     tel_chf=receveurs[0]["tel"]
                # if chauffeurs and "status" in chauffeurs[0] and chauffeurs[0]["status"]:
                #     status_chf=receveurs[0]["status"]
            
       if len(getContentsjson)!=0 :
          dataj=getContentsjson 
       #get Info vehicule
    #    values=json.dumps(dataj)
       
       images = {
        "devant": None,
        "derriere": None,
        "gauche_vehicule": None,
        "droite_vehicule": None,
        "interieur_vehicule": None,
        "Licence": None,
        "Licence_Verso": None,
        "Assurance": None,
        "NIF/STAT_r": None,
        "NIF/STAT_v": None,
        "visite_technique": None,
        "Carte_grise_recto": None,
        "Carte_grise_verso": None,  
        "cin_p_recto":None,
        "cin_p_verso":None,
        "photo_receveur":None,
        "Permis_rec_v":None,
        "Permis_rec_r":None,
        "cin_r_verso":None,
        "cin_r_recto":None,
        "Badge_R":None,
        "photo_proprio":None ,  
        "photo_chauffeur":None ,  
        "cin_v":None ,  
        "cin_r":None ,  
        "Permis_v":None ,  
        "Permis_r":None ,  
        "Badge_C":None ,  
        }
            
    # Remplissage des valeurs
    
       for item in dataj:
            type_image = item.get("type")
            if type_image in images:
                images[type_image] = item.get("url_name", None)
       
    # Assignation aux variables individuelles si nécessaire
       devant_image = images["devant"]
       derriere_image = images["derriere"]
       gauche_vehicule = images["gauche_vehicule"]
       droite_vehicule = images["droite_vehicule"]
       interieure_vehicule = images["interieur_vehicule"]
       Licence = images["Licence"]
       Licence_Verso = images["Licence_Verso"]
       Assurance = images["Assurance"]
       nif_stat_r = images["NIF/STAT_r"]
       nif_stat_v = images["NIF/STAT_v"]
       visite_technique = images["visite_technique"]
       Carte_grise_recto = images["Carte_grise_recto"]
       Carte_grise_verso= images["Carte_grise_verso"]
       cin_p_recto = images["cin_p_recto"]
       cin_p_verso = images["cin_p_verso"]
       photo_pr = images["photo_proprio"]
       photo_receveur = images["photo_receveur"]
       Permis_rec_v = images["Permis_rec_v"]
       Permis_rec_r = images["Permis_rec_r"]
       cin_r_verso = images["cin_r_verso"]
       cin_r_recto = images["cin_r_recto"]
       Badge_R = images["Badge_R"]
       photo_chauffeur = images["photo_chauffeur"]
       cin_v = images["cin_v"]
       cin_r = images["cin_r"]
       Permis_v = images["Permis_v"]
       Permis_r = images["Permis_r"]
       Badge_C = images["Badge_C"]
    #    return  json.dumps(types)
       vehicule = requests.get(url_trp+"api/get_vehicle_nr/"+bus, json={}, headers=header, timeout=120)
    #    print(vehicule.text)
    #    sys.stdout.flush()
    #    vehicule_info=vehicule.json()
       try :  
            vehicule_info=vehicule.json()
       except :
            vehicule_info={}
            pass
       # Vérifier si la liste n'est pas vide avant d'accéder aux éléments
       if vehicule_info and isinstance(vehicule_info, list):
            first_vehicle = vehicule_info[0]  # Récupérer le premier élément
            plaque = first_vehicle.get("plaque", "N/A")
            modele = first_vehicle.get("modele", "N/A")
            marque = first_vehicle.get("marque", "N/A")
            ligne_variance_id = first_vehicle.get("ligne_variance_id", "N/A")
            ell_int =first_vehicle.get("ell_int", "")
            ell_ext =first_vehicle.get("ell_ext", "")
            annonceur =first_vehicle.get("annonceur", "")
            comments =first_vehicle.get("comments", "")
            haspublicite =first_vehicle.get("haspublicite", "")
       else :
            bus=""
            plaque = ""
            modele = ""
            marque = ""
            ligne_variance_id = ""
            ell_int = ""
            ell_ext = ""
            comments = ""
            annonceur = ""
            haspublicite = ""
            
   else :
       bus=""
       plaque = ""
       modele = ""
       marque = ""
       ligne_variance_id = ""
       ell_int = ""
       ell_ext = ""
       comments = ""
       annonceur = ""
       haspublicite = ""
#    if request.view_args.get("role") :
#        role=request.view_args.get("role")
#    if request.view_args.get("role") :
#        name=request.view_args.get("name")
   username=name
#    role=role
   return render_template("steps/included/edit_vehicule.html",
                          photo_receveur = photo_receveur,
                          Permis_rec_v =Permis_rec_v,
                          Permis_rec_r = Permis_rec_r,
                          cin_r_verso = cin_r_verso,
                          cin_r_recto = cin_r_recto,
                          Badge_R = Badge_R,
                          comments = comments,
                          annonceur = annonceur,

                          photo_chauffeur = photo_chauffeur,
                          cin_v =cin_v,
                          cin_r = cin_r,
                          Permis_v = Permis_v,
                          Permis_r = Permis_r,
                          Badge_C = Badge_C,

                          status_chf=status_chf,
                          tel_chf=tel_chf,
                          prenom_chf=prenom_chf,
                          nom_chf=nom_chf,
                          anne_exp_chf=anne_exp_chf,
                          nom_proprio = nom_proprio ,
                          pnom_proprio =pnom_proprio,
                          tel_prop = tel_prop, 
                          status_rece=status_rece,
                          tel_rece=tel_rece,
                          nom_rece=nom_rece,
                          prenom_rece=prenom_rece,
                          anne_exp_rece=anne_exp_rece,        
                                
                          photo_pr=photo_pr,
                          devant_image=devant_image,
                          cin_p_verso=cin_p_verso,
                          cin_p_recto=cin_p_recto,
                          derriere_image=derriere_image,
                          gauche_vehicule=gauche_vehicule,
                          droite_vehicule=droite_vehicule,
                          interieur_vehicule=interieure_vehicule,
                          username=username,
                          record=record,
                          bus=bus,
                          marque=marque,
                          plaque=plaque,
                          modele=modele,
                          ligne_variance_id=ligne_variance_id,
                          haspublicite=haspublicite,
                          ell_int=ell_int,
                          ell_ext=ell_ext,
                          Licence=Licence,
                          Licence_Verso=Licence_Verso,
                          Assurance=Assurance,
                          nif_stat_r=nif_stat_r,
                          nif_stat_v=nif_stat_v,
                          visite_technique=visite_technique,
                          Carte_grise_recto=Carte_grise_recto,
                          Carte_grise_verso=Carte_grise_verso
                          )
@app.route('/view_reconizer',methods=['GET'])
def setviewReconizer():
   return render_template("reconizer.html")
@app.route('/listUpload',methods=['GET'])
def setviewViewUpl():
   return render_template("listPaperVehicule/uploadAll.html")
@app.route('/testTemplate',methods=['GET'])
def setviewTemplate():
   return render_template("templates_pdf/export.html")

@app.route('/sendRarFileVehicule',methods=['POST'])
def uploadRarFile():
   
    # target_directory = "C:\\Users\\zorazafi\\Desktop\\LIGNE D\\"
    # winrar_executable = "C:\\Program Files\\WinRAR\\WinRAR.exe"

    # for item in os.listdir(target_directory):
    #     item_path = os.path.join(target_directory, item)
    #     if os.path.isdir(item_path):
    #         compress_with_winrar(item_path, winrar_executable)
    # return "ok"
    ##
    filenameArray=[]
    datax=config['TOKEN_SEAFILE']
    urlseafile=config['URL_SEAFILE']
    env_chkc=current_user.env
    if env_chkc==1 :
        urlseafile=config['URL_SEAFILE_PRO']
        url_trp=config['TRP_DOMAIN_URL_PROD']
    if 'file_vehicules' in request.files:
        
        fichier = request.files['file_vehicules']
   
        filename = fichier.filename
        
        chemin = os.path.join("SeafileTemp",filename)
        # try :
        #     shutil.rmtree('SeafileTemp/'+filename.split(".rar")[0].replace(' ',''))
        # except :
        #     pass
        fichier.save(chemin)
        
        firstDirectory=filename.split(".rar")
       
        # Path to the TAR archive
        rar_file_path = chemin
       
        extract_to = "SeafileTemp"
        os.makedirs(extract_to, exist_ok=True)

        # Extract the contents of the RAR archive
        with rarfile.RarFile(rar_file_path) as rf:
            rf.extractall(extract_to)

       
        # Path of the newly extracted directory
        extracted_directory_path = os.path.join(extract_to, firstDirectory[0])
        print("extraction des fichiers")
        os.remove("SeafileTemp/"+filename)
        listdirectoryFiles=os.listdir("SeafileTemp")
        for listdir1 in listdirectoryFiles:
            NAME_DIRECTORY=listdir1.replace(' ','')
            try :
                os.remove("SeafileTemp/"+NAME_DIRECTORY+"/Thumbs.db")
            except :
                pass
                    # New path with the desired name
            new_directory_path = os.path.join(extract_to, NAME_DIRECTORY)
            # os.rename(extracted_directory_path, new_directory_path)
            
           
            try :
                listFiles=os.listdir("SeafileTemp/"+NAME_DIRECTORY)
                nameDirectory =NAME_DIRECTORY.replace(' ','')
                os.remove("SeafileTemp/"+filename)
            except :
                pass
            cnf.createDirectory(datax,urlseafile,nameDirectory)
            cnf.createDirectory(datax,urlseafile,"PAPER",nameDirectory)
            cnf.createDirectory(datax,urlseafile,"GALERY",nameDirectory)
            cnf.createDirectory(datax,urlseafile,"TEAM",nameDirectory)   
            cnf.deleteFileExist(nameDirectory,env_chkc)  
            # NAME_DIRECTORY=firstDirectory[0].replace(' ','')
            # # New path with the desired name
            # new_directory_path = os.path.join(extract_to, NAME_DIRECTORY)
            # os.rename(extracted_directory_path, new_directory_path)
            # os.remove("SeafileTemp/"+filename)
            # listFiles=os.listdir("SeafileTemp/"+NAME_DIRECTORY)
            # nameDirectory =NAME_DIRECTORY.replace(' ','')
            # cnf.createDirectory(datax,urlseafile,nameDirectory)
            # cnf.createDirectory(datax,urlseafile,"PAPER",nameDirectory)
            # cnf.createDirectory(datax,urlseafile,"GALERY",nameDirectory)
            # cnf.createDirectory(datax,urlseafile,"TEAM",nameDirectory)   
            # cnf.deleteFileExist(nameDirectory)  
        
            for listFile1 in listFiles:
                
                dataobject={}
                dataobject1=[]
                fileD="Cpp-Transport"
                liste_dictionnaires=[]
                firstDirectory=listFile1.split("_")
                # countf=int(len(firstDirectory)-1)
                firstDirectory.pop()
                # print(firstDirectory)
                delimiter ="_"
                ti = delimiter.join(firstDirectory)
            
                if ti =="G_EXT" :
                    typefls="devant_derriere"
                    nameDirectoryfirst="GALERY"
                if ti =="G_EXT_L" :
                    typefls="gauche"
                    nameDirectoryfirst="GALERY"
                if ti =="G_EXT_R" :
                    typefls="droite"
                    nameDirectoryfirst="GALERY"
                if ti =="G_INT" :
                    typefls="Interieur_vehicule"
                    nameDirectoryfirst="GALERY"
                if ti =="P_R" :
                    typefls="Papier"
                    nameDirectoryfirst="PAPER"
                if ti =="P" :
                    typefls="Papier"
                    nameDirectoryfirst="PAPER"
                if ti =="T_R" :
                    typefls="team_receveur"
                    nameDirectoryfirst="TEAM"
                if ti =="T_C" :
                    typefls="team_chauffeur"
                    nameDirectoryfirst="TEAM"
                getContentsjson=cnf.getContenuFiles(datax,urlseafile,NAME_DIRECTORY,"TRP")
                try :
                    if len(getContentsjson)==0 :
                        dataj=[]
                    else :
                        dataj=getContentsjson
                        # t={"type":"re","frer":"rezre"}
                except :
                    dataj=[]
                try :
                    listFile=listFile1.replace(' ','')
                    contenus=os.listdir("SeafileTemp/"+nameDirectory+"/"+listFile)
                except :
                    listFile=listFile1
                    if listFile != "Thumbs.db" :
                       contenus=os.listdir("SeafileTemp/"+nameDirectory+"/"+listFile)
                    pass
                try :
                        for contenuDirectory in contenus:
                            try :
                                dating=get_creation_date("SeafileTemp/"+NAME_DIRECTORY+"/"+listFile+'/'+contenuDirectory)
                            except :
                                dating="undefined"      
                            imageLue = Image.open("SeafileTemp/"+NAME_DIRECTORY+"/"+listFile+'/'+contenuDirectory)
                            #reduction taille image
                            new_size=(600, 600)
                            im1 = imageLue.resize(new_size)
                            im1.save("SeafileTemp/"+NAME_DIRECTORY+"/"+listFile+'/'+contenuDirectory)
                                            #get Token 
                            token=cnf.getTokenSeafile(datax, urlseafile)
                        
                            nameFile="SeafileTemp/"+NAME_DIRECTORY+"/"+listFile+'/'+contenuDirectory
                                            #send file
                            namefilesup=cnf.sendFile(token, urlseafile,nameDirectoryfirst,nameFile,nameDirectory)
                            # getContentsjson=cnf.getContenuFiles(token, urlseafile,nameDirectory,nameFile)
                            dataobject={'url_name':namefilesup,'type':typefls,'dateFile':dating}
                            
                            dataj.append(dataobject)
                        # print(dataj)
                        cnf.deleteFileExist(nameDirectory,env_chkc)                 
                        cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(dataj))   
                    # cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(datajson))   
                        if listFile != "Thumbs.db" :  
                            shutil.rmtree('SeafileTemp/'+NAME_DIRECTORY+"/"+listFile)
                        
                except Exception as e:
                    print(e)
                    shutil.rmtree('SeafileTemp/'+NAME_DIRECTORY)
                    pass    
        shutil.rmtree('SeafileTemp/'+NAME_DIRECTORY)
        return "1"
    # if 'derriere_vehicule_rar' in request.files:
    #     derriere=request.files['derriere_vehicule_rar']
    #     derriere_name=derriere.filename
    #     filenameArray.append({'name_files': derriere_name, 'type': 'derriere'})
    #     chemin = os.path.join("SeafileTemp",derriere_name)
    #     derriere.save(chemin)
    #     filename=derriere_name.replace(' ','')
    #     firstDirectory=filename.split("_")
    #     countf=int(len(firstDirectory)-1)
    #     secnameDirec=firstDirectory[countf]
    #     firstDirectory=secnameDirec.split(".rar")
    #     NAME_DIRECTORY=firstDirectory[0] if(type(firstDirectory) == list) else ""   
    #     rf = rarfile.RarFile(chemin)
    #     rf.extractall("SeafileTemp")
    #     rf.close()
    #     os.remove("SeafileTemp/"+derriere_name)
    # if 'gauche_vehicule' in request.files: 
    #     gauche=request.files['gauche_vehicule']
    #     gauche_name=gauche.filename
    #     filenameArray.append({'name_files': gauche_name, 'type': 'gauche_vehicule'})
    #     chemin = os.path.join("SeafileTemp",gauche_name)
    #     gauche.save(chemin)

    #     filename=gauche_name.replace(' ','')
    #     firstDirectory=filename.split("_")
    #     countf=int(len(firstDirectory)-1)
    #     secnameDirec=firstDirectory[countf]
    #     firstDirectory=secnameDirec.split(".rar")
    #     NAME_DIRECTORY=firstDirectory[0] if(type(firstDirectory) == list) else ""   
    #     rf = rarfile.RarFile(chemin)
    #     rf.extractall("SeafileTemp")
    #     rf.close()
    #     os.remove("SeafileTemp/"+gauche_name)
    # if 'droite_vehicule' in request.files:  
    #     droite=request.files['droite_vehicule']
    #     droite_name=droite.filename
    #     filenameArray.append({'name_files': droite_name, 'type': 'droite_vehicule'})
    #     chemin = os.path.join("SeafileTemp",droite_name)
    #     droite.save(chemin)

    #     filename=droite_name.replace(' ','')
    #     firstDirectory=filename.split("_")
    #     countf=int(len(firstDirectory)-1)
    #     secnameDirec=firstDirectory[countf]
    #     firstDirectory=secnameDirec.split(".rar")
    #     NAME_DIRECTORY=firstDirectory[0] if(type(firstDirectory) == list) else ""   
    #     rf = rarfile.RarFile(chemin)
    #     rf.extractall("SeafileTemp")
    #     rf.close()
    #     os.remove("SeafileTemp/"+droite_name)
    # if 'interieur_vehicule' in request.files: 
    #     interieur=request.files['interieur_vehicule']
    #     interieur_name=interieur.filename
    #     filenameArray.append({'name_files': interieur_name, 'type': 'interieur_vehicule'})
    #     chemin = os.path.join("SeafileTemp",interieur_name)
    #     interieur.save(chemin)
         
    #     filename=interieur_name.replace(' ','')
    #     firstDirectory=interieur_name.split("_")
    #     countf=int(len(firstDirectory)-1)
    #     secnameDirec=firstDirectory[countf]
    #     firstDirectory=secnameDirec.split(".rar")
    #     NAME_DIRECTORY=firstDirectory[0] if(type(firstDirectory) == list) else ""   
    #     rf = rarfile.RarFile(chemin)
    #     rf.extractall("SeafileTemp")
    #     rf.close()
    #     os.remove("SeafileTemp/"+interieur_name)
    # if 'team_vehicule' in request.files: 
    #     team=request.files['team_vehicule']
    #     team_name=team.filename
    #     filenameArray.append({'name_files': team_name, 'type': 'Prepose_vehicule'})
    #     chemin = os.path.join("SeafileTemp",team_name)
    #     team.save(chemin)
         
    #     filename=team_name.replace(' ','')
    #     firstDirectory=team_name.split("_")
    #     countf=int(len(firstDirectory)-1)
    #     secnameDirec=firstDirectory[countf]
    #     firstDirectory=secnameDirec.split(".rar")
    #     NAME_DIRECTORY=firstDirectory[0] if(type(firstDirectory) == list) else ""   
    #     rf = rarfile.RarFile(chemin)
    #     rf.extractall("SeafileTemp")
    #     rf.close()
    #     os.remove("SeafileTemp/"+team_name)
 
   
    # #get Liste des données
   
    # for listFile in listFiles:
    #     new_directoryname=listFile
    #     dataobject={}
    #     dataobject1=[]
    #     fileD="Cpp-Transport"
    #     liste_dictionnaires=[]
    #     contenus=os.listdir("SeafileTemp/"+listFile)
    #     #get type in switch listdirectory 
    #     firstDirectory=listFile.split("_")
    #     countf=int(len(firstDirectory)-1)
    #     typefl=[]
    #     getContentsjson=cnf.getContenuFiles(datax,urlseafile,NAME_DIRECTORY,"TRP")
    
    #     try :
    #         if len(getContentsjson)==0 :
    #             dataj=[]
    #         else :
    #             dataj=getContentsjson
    #             # t={"type":"re","frer":"rezre"}
    #     except :
    #             dataj=[]
 
    #     for n in range(countf):
    #         typefl.append(firstDirectory[n])
    #     v=firstDirectory[0]
    #     ti='_'.join(typefl)
    #     type_file=switch('_'.join(typefl))
    #     typefls="photo"
    #     if ti =="G_EXT" :
    #         typefls="devant_derriere"
    #     if ti =="G_EXT_L" :
    #         typefls="gauche"
    #     if ti =="G_EXT_R" :
    #         typefls="droite"
    #     if ti =="G_INT" :
    #         typefls="Interieur_vehicule"
    #     if ti =="P_R" :
    #         typefls="Papier_team"
    #     if ti =="T_R" :
    #         typefls="equipe"
    #     print(typefls)    
    #     if v=="G" :
    #         nameDirectoryfirst="GALERY"
    #     if v=="P" :
    #         nameDirectoryfirst="PAPER"
    #     if v=="T" :
    #         nameDirectoryfirst="TEAM"
        
    #     start_time = time.time()
    #     try :
    #         for contenuDirectory in contenus:
    #                 imageLue = Image.open("SeafileTemp/"+listFile+'/'+contenuDirectory)
    #                 #reduction taille image
    #                 new_size=(600, 600)
    #                 im1 = imageLue.resize(new_size)
    #                 im1.save("SeafileTemp/"+listFile+'/'+contenuDirectory)
    #                                 #get Token 
    #                 token=cnf.getTokenSeafile(datax, urlseafile)
    #                 nameFile="SeafileTemp/"+listFile+'/'+contenuDirectory
    #                                 #send file
    #                 namefilesup=cnf.sendFile(token, urlseafile,nameDirectoryfirst,nameFile,nameDirectory)
    #                 getContentsjson=cnf.getContenuFiles(token, urlseafile,nameDirectory,nameFile)
    #                 dataobject={'url_name':namefilesup,'type':typefls}
                    
    #                 dataj.append(dataobject)
    #         cnf.deleteFileExist(nameDirectory)                 
    #         cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(dataj))   
    #             # cnf.sendFileJson(datax,urlseafile,nameDirectory,json.dumps(datajson))     
    #         shutil.rmtree('SeafileTemp/'+listFile)   

    #     except Exception as e :
    #             print(e)
    #             return "0"
    # return "1"
def get_creation_date(image_path):
      try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data and 36867 in exif_data:
                creation_date = exif_data[36867]
                return creation_date
            else:
                return "Date de création introuvable dans les métadonnées"
      except (IOError, AttributeError):
        return "Erreur lors de la lecture de l'image ou des métadonnées"

@app.route('/reconizer',methods=['POST'])
def reconizer() :
    # open following url to get ipaddress
    urlopen("http://ipinfo.io/json")

    # load data into array
    data = json.load(urlopen("http://ipinfo.io/json"))

    # # extract lattitude
    # lat = data['loc'].split(',')[0]

    # # extract longitude
    # lon = data['loc'].split(',')[1]
   
    
    if 'fichier' in request.files:
        fichier = request.files['fichier']
        filename=fichier.filename
    else :
        return "Fichier is required"
    extension = os.path.splitext(filename)[1][1:].strip()
    ext_arrs = ['jpg', 'png', 'gif', 'jfif','PNG','JPG','jpeg']
    # if fichier.tell() == 0:
    #     return 'No selected file'
    from datetime import datetime
    if extension in ext_arrs: 
        token="92a54581b94041c7064517e70862ac9c65a6785b"
        chemin1=os.path.join("SeafileTemp",fichier.filename)
        fichier.save(chemin1)
        imageLue = Image.open("SeafileTemp/"+fichier.filename)
            #reduction taille image
        new_size=(600, 600)
        im1 = imageLue.resize(new_size)
        im1.save("ImageTemporaire/"+fichier.filename)
            #check=os.path.exists("SeafileTemp/"+fichier.filename)
        chemin=os.path.join("ImageTemporaire",fichier.filename)
        datavehicule={}
        with open(chemin, 'rb') as fp :
                        response = requests.post(
                                    'https://api.platerecognizer.com/v1/plate-reader/',
                                    files=dict(upload=fp),
                                    headers={'Authorization':'Token '+token})
                        value=response.json()
                        value1=value['results']
                        # utc_datetime = datetime.strptime(str(value['timestamp']),"%Y-%m-%dT%H:%M:%S.%fZ")
                        
                        utc_datetime = datetime.strptime(str(value['timestamp']), "%Y-%m-%dT%H:%M:%S.%fZ")

                        # Set the desired timezone offset (+3 hours in this case)
                        timezone_offset = timedelta(hours=3)

                        # Apply the timezone offset to the UTC datetime
                        desired_datetime = utc_datetime + timezone_offset

                        # Format the datetime to display date and time in the desired timezone
                        formatted_datetime= desired_datetime.strftime("%Y-%m-%d %H:%M:%S")
                        
                        if not value1 :
                            return "error"
                        else :
                            for x in value1:
                                plate=x['plate']   
                                datavehicule={"date":str(formatted_datetime),"plaque":plate.upper(),'location':data['loc']}
                        # pb.append(datavehicule)
        return json.dumps(datavehicule)
    if extension == "json" :               
    # return json.dumps(check)
    # print(name)
        print("check file in server")
            #get all  dossier
        with open('vehicule.json', 'r') as f:
                datajson = json.load(f)
                vehicule=datajson['vehicule']
                token=config['TOKEN_SEAFILE']
                urlseafile=config['URL_SEAFILE']
                allVehicule=[]
                pb=[]
                data={}
        for i in range(len(vehicule)) :
                getContentsjson=cnf.getContenuFiles(token, urlseafile,vehicule[i],"TRP")
                if len(getContentsjson)!=0 :
                        # listeVehicle=getContentsjson
                    for i in range(len(getContentsjson)) :
                        types=getContentsjson[i]
                        if("type" in types):
                            if(types['type']=='devant'):
                                allVehicule.append(types)
                        # if(listeVehicle['type']=="Exterieur_vehicule") :
                        #     allVehicule.append(listeVehicle['url_name'])
                    #    print(getContentsjson)
                # return json.dumps(allVehicule)
                #get Liste Contents if type "devant"getContenuFiles
                # NAME_DIRECTORY=firstDirectory[0] if(type(firstDirectory) == list) else ""   

                # for i in (5)):
                #     namevehicule[i]=datajson['vehicule'][i]
                #     getContentsjson=cnf.getContenuFiles(token, urlseafile,namevehicule[i],"TRP")
                # return getContentsjson
                #get Url 
        countV=len(allVehicule)
                
        if(countV>0):
                
                for i in range(countV) :
                    image_link=allVehicule[i]['url_name'] #"https://qacseafile.cpp-system.com/pictures?xys=Cpp-Transport/9375TBG|x99g0t81OkIQQeXvptZu.png"
                    index = image_link.rfind("|")
                    rsp = requests.get(image_link)
                    name_str = image_link[index+1:]
                    if rsp.status_code == 200:
                        with open("myfiles/"+name_str, 'wb') as f:
                             f.write(rsp.content)
                    listchemin =os.listdir("myfiles")
                                # countListChemin=len(listchemin)
                    regions = ['mx', 'us-ca','mg'] # Change to your country
                            
                                #image < 3 Mo
                                # for i in range(countListChemin):
                        # fichier = request.files['fichier']
                        # filename=fichier.filename
                        # chemin =os.path.join("SeafileTemp",filename)
                    chemin =os.path.join("myfiles",name_str)
                                # chemin =os.path.join("myfiles",listchemin[i])
                    with open(chemin, 'rb') as fp :
                        response = requests.post(
                                        'https://api.platerecognizer.com/v1/plate-reader/',
                                        json={"mmc":True},
                                        files=dict(upload=fp),
                                        headers={'Authorization': 'Token 92a54581b94041c7064517e70862ac9c65a6785b'})
                        value=response.json()
                        utc_datetime = datetime.strptime(str(value['timestamp']), "%Y-%m-%dT%H:%M:%S.%fZ")

                        # Set the desired timezone offset (+3 hours in this case)
                        timezone_offset = timedelta(hours=3)

                        # Apply the timezone offset to the UTC datetime
                        desired_datetime = utc_datetime + timezone_offset

                        # Format the datetime to display date and time in the desired timezone
                        formatted_datetime= desired_datetime.strftime("%Y-%m-%d %H:%M:%S")
                        
                        value1=value['results']
                        for x in value1:
                            plate=x['plate']   
                            data[i]={"date":str(formatted_datetime),"plaque":plate.upper()}
                        pb.append(data[i])
        return sendExcelData(pb,'',"","")

    # else :
    #         fichier = request.files['fichier']
    #         pb=[]
    #         ext_arrs = ['jpg', 'png', 'gif', 'jfif','PNG','JPG','jpeg']
    #         if extension in ext_arrs:
    #             check=os.path.exists("SeafileTemp/"+fichier.filename)
    #             chemin=os.path.join("SeafileTemp",fichier.filename)
    #             fichier.save(chemin)
    #             #    p=os.path.isfile(chemin)
    #         else :
    #             print("file is not supported")
    #             pass  
    
    #         with open(chemin, 'rb') as fp :
    #             response = requests.post(
    #                         'https://api.platerecognizer.com/v1/plate-reader/',
    #                         files=dict(upload=fp),
    #                         headers={'Authorization': 'Token 92a54581b94041c7064517e70862ac9c65a6785b'})
    #             value=response.json()
    #             return value
    #             value1=value['results']
    #             for x in value1:
    #                 plate=x['plate']   
    #                 data={"date":str(value['timestamp']),"plaque":plate.upper()}
    #             pb.append(data)
    #             return value
@app.route('/Recense/mail',methods=['POST','GET'])
def SendFilesRece():
    if request.method == 'POST':
        nameFile=request.form.get('namfile')
        pdf_name=str(nameFile)
    if request.method == 'GET':
        nameFile=request.form.get('namfile')
        dates=datetime.date.today()
        pdf_name=str(dates)+"_recencement_vehicule.xlsx"
    from generate_game import generate_game
    cnf=generate_game()
    
    types=1
    email="razafimandimbydoun@gmail.com"
    cnf.sendMail(pdf_name,date,types,email) 
    return  "ok" 


@app.route('/telecharger/<string:id>')
def telecharger_fichier(id):
    # Ici, vous pouvez utiliser l'ID pour déterminer le chemin du fichier à télécharger
    chemin_fichier = os.path.realpath("event/"+id)
    # chemin_fichier = f'C:\wamp64\www\extract\cpptransportextract\event\{id}'
    return send_file(chemin_fichier, as_attachment=True, )
@app.route('/telecharger/file/')
def telecharger_fichier_card_bus():
        dateb="15/10/2024 00:01:13"
        dateend="29/10/2024 23:59:00"
        PARSE_APP_ID=config['PARSE_APP_ID'] 
        PARSE_MASTER_KEY= config['PARSE_MASTER_KEY'] 
        PARSE_API_KEY_REST=config['PARSE_API_KEY_REST']
        headers = {
                    "X-Parse-Application-Id": f"{PARSE_APP_ID}",
                    "X-Parse-REST-API-Key": f"{PARSE_MASTER_KEY}",
                    "X-Parse-Master-Key": f"{PARSE_API_KEY_REST}",
                    "Content-Type": "application/json"
                }
        params = urllib.parse.urlencode({"limit":1000000,"where": json.dumps({
                "date": {
                    "$gte": f"{dateb}",
                    "$lte": f"{dateend}",
                },
                "type":"CPP",
                "month":"10",
                "year":"2024",
                "cancelled":False,
            }),"include":"vehicule"})
        myurl='https://bus.cpp-system.com/api/classes/CppTransportEvent'
          
        result=requests.get(myurl,params=params,headers=headers)
          # print("Status : "+str(result.status_code))
        x=result.json()
        
        values=x['results']

        vehicule=[]
        tab=[]
         
        for x in  values :
            if 'vehicule' in x:
                vehicules={
                      "numero" :x['vehicule']['numero'],
                      "numero_card" :x['cardNumber'],
                      "dates" :x['date'],
                  }
                vehicule.append(vehicules)
         
                    
                    #tab["vehicule"].append(x)
        return json.dump(vehicule)
    # try :  
    #       dateb="15/10/2024 00:01:13"
    #       dateend="29/10/2024 23:59:00"
    #       PARSE_APP_ID=config['PARSE_APP_ID'] 
    #       PARSE_MASTER_KEY= config['PARSE_MASTER_KEY'] 
    #       PARSE_API_KEY_REST=config['PARSE_API_KEY_REST']
    #       headers = {
    #                 "X-Parse-Application-Id": f"{PARSE_APP_ID}",
    #                 "X-Parse-REST-API-Key": f"{PARSE_MASTER_KEY}",
    #                 "X-Parse-Master-Key": f"{PARSE_API_KEY_REST}",
    #                 "Content-Type": "application/json"
    #             }
    #       params = urllib.parse.urlencode({"limit":1000000,"where": json.dumps({
    #             "date": {
    #                 "$gte": f"{dateb}",
    #                 "$lte": f"{dateend}",
    #             },
    #             "type":"CPP",
    #             "month":"10",
    #             "year":"2024",
    #             "cancelled":False,
    #         }),"include":"vehicule"})
    #       myurl='https://bus.cpp-system.com/api/classes/CppTransportEvent'
          
    #       result=requests.get(myurl,params=params,headers=headers)
    #       # print("Status : "+str(result.status_code))
    #       x=result.json()
         
    #       values=x['results']

    #       vehicule=[]
    #       tab=[]
         
    #       for x in  values :
    #            if 'vehicule' in x:
    #               vehicules={
    #                   "numero" :x['vehicule']['numero'],
    #                   "numero_card" :x['cardNumber'],
    #                   "dates" :x['date'],
    #               }
    #               vehicule.append(vehicules)
         
                    
    #                 #tab["vehicule"].append(x)
    #       return json.dump(vehicule)
    #       return ("Extraction  entre "+dateb+" à "+dateend+" avec succès \n")    
    # except Exception as e: 
    #       print (e)  
          
    #       errors=[]
    #       return []

def sendExcelData(data1,cooperative,userid,username) :
    from datetime import datetime
    workbook = Workbook()
    sheet = workbook.active
    listData=list()
    date_courante = datetime.now()
    date_name=date_courante.strftime("%Y-%m-%d")
    #check file if exist 
    nameFile="liste_vehiculess.xlsx"
    file_path = 'FilesTemps/'+nameFile  # Replace with the path to your file

    if os.path.isfile(file_path):
        workbook1 = openpyxl.load_workbook(file_path)
        sheet1 = workbook1.active    
        try :
            for x in data1 :
                
                data=[[x['plaque'],x['date'],x['location'],cooperative,userid,username,'ok']]
                # print(data)
            for row_data in data:
                sheet1.append(row_data)
                workbook1.save(filename=file_path)
            return json.dumps({"msg":"ok"})
        except Exception as e :
            print(e)
            return "error"
    else:
        print("File does not exist or is a directory.")
        listData.append(("Vehicule","Date","location","cooperative","user_id","Username","Status"))
        try :
            for x in data1 :
                listData.append((x['plaque'],x['date'],x['location'],cooperative,userid,username,'ok'))
            c=tuple(listData)
            temp_file="FilesTemps/"+date_name+"_vehicule"+".xlsx"
            real_path = os.path.realpath(temp_file)
            excel_io = io.BytesIO()   
            excel_io.seek(0)
            for row in c:
                sheet.append(row)
                workbook.save(temp_file)
            send_file(real_path, as_attachment=True)
            return json.dumps({"msg":"ok"})
        except Exception as e :
            return print(e)
def sendRecencements(data1,cooperative) :
    workbook = Workbook()
    sheet = workbook.active
    listData=list()
    date_courante = datetime.date.today()
    
    date_name=str(date_courante)
    #check file if exist 
    nameFile=str(date_name)+"_recencement_vehicule.xlsx"
    file_path = 'FilesRecencement/'+nameFile  # Replace with the path to your file

    if os.path.isfile(file_path):
        workbook1 = openpyxl.load_workbook(file_path)
        sheet1 = workbook1.active
        try :
            for x in data1 :
                data=[[cooperative,x['plaque'],date_name,x['role'],x['nom'],x['prenom'],x['tel'],x['idSeafile'],'ok']]
                # print(data)
            for row_data in data:
                sheet1.append(row_data)
                workbook1.save(filename=file_path)
            return json.dumps({"msg":"ok"})
        except Exception as e :
            print(e)
            sys.stdout.flush()
            return "error"
    else:
        print("File does not exist or is a directory.")
        sys.stdout.flush()
        listData.append(("Cooperative","vehicule","Date","role","nom","prénom","telephone","idSeafile","Status"))
        try :
            for x in data1 :
                print(x)
                listData.append((cooperative,x['plaque'],date_name,x['role'],x['nom'],x['prenom'],x['tel'],x['idSeafile'],'ok'))
            c=tuple(listData)
            temp_file="FilesRecencement/"+date_name+"_recencement_vehicule"+".xlsx"
            real_path = os.path.realpath(temp_file)
            excel_io = io.BytesIO()   
            excel_io.seek(0)
            for row in c:
                sheet.append(row)
                workbook.save(temp_file)
            send_file(real_path, as_attachment=True)
            return json.dumps({"msg":"ok"})
        except Exception as e :
            print(e)
            sys.stdout.flush()
            return e
def compress_with_winrar(folder_path, winrar_path):
    folder_name = os.path.basename(folder_path)
    output_rar_path = f"{folder_name}.rar"
    
    command = [
        winrar_path,
        "a",  # Add to archive
        "-r",  # Recurse subdirectories
        "-ep1",  # Exclude base folder from names
        "-inul",  # Disable progress display
        output_rar_path,
        folder_name
    ]

    subprocess.run(command, cwd=os.path.dirname(folder_path))

#API GET INVOICE 
api.add_resource(LoginResource, '/api/login')
# api.add_resource(GetaDataPay, '/api/transaction/pay')
api.add_resource(ProtectedResource, '/api/resource')
api.add_resource(InvoiceCpp, '/api/invoice')
api.add_resource(RapportMyCpp, '/api/rapports')
    

# api.add_resource(ProtectedResource, '/api/protected')
def extract_and_run():
    print ('__________  _____ _____.___.')
    print ('\______   \/  _  \\__  |   |')
    print (' |     ___/  /_\  \/   |   |')
    print (' |    |  /    |    \____   |')
    print (' |____|  \____|__  / ______|')
    now = time.time()
    current_time = time.localtime(now)
    month =  current_time.tm_mon    # Extraire l'année actuelle
    year = current_time.tm_year
    if(month==1) :
        month=12
        year=year-1
    else :
        month=month-1
    data={
                "month":int(month),
                "year":int(year)
    }
    model_api.CppApi.extractDataPay(data) 
    sys.stdout.flush() 

def send_and_run():
    print('Facture create')
    with app.app_context():
    #extract  data pay 
            #get data if not sended to pay 
        record=model_api.CppApi.batch_related_transaction() 
        if record is not None :
                for x in record :
                    data={
                            "objectIdCore":x['objectId'],
                            "amount":float(x['total']),
                            "company":x['company_pay'],
                            "month":int(x['month']),
                            "year":int(x['year'])
                        }
                    data2={
                        "company":x['company_pay'],
                        "idAdelyaCompany":x['id_adelya_company'],
                        "idPartenaire":x['id_partner'],
                        "month":int(x['month']),
                        "year":int(x['year']),
                        "transaction_id":"",   
                        }
                        
                    objectId=model_api.CppApi.create_transact_payre(data)  
                    if(objectId!="#|#"):
                        fval=objectId.split('|')
                        if(fval[0]!="#" and fval[1]!="#"  ):
                            fval=model_api.CppApi.update_batch(data["objectIdCore"],fval[0],data2,fval[1]) 
                            print("Pdf create with successfully!")
                            sys.stdout.flush() 
                
def sendMailTo():
    model_api.CppApi.sendFilesBilling()  
def app_rune() :
   app.run(host='0.0.0.0', port=8082, debug=True, use_reloader=False)

def run_flask_app():
    import sched
    print('schedule run')
     # Initialisation du planificateur
    scheduler = sched.scheduler(time.time, time.sleep)
    # Planification de l'événement suivant
        #   Extraction PAY
    # # schedule_test_schedule(scheduler)
    # schedule_transaction_pay(scheduler)
    # # #       Extraction commission
    # schedule_next_event(scheduler)
    # # #       Send And run
    # schedule_udpate_transaction_pay(scheduler)
    #     #send Mail
    # schedule_send(scheduler)
    ## send  
    #run_event_day(scheduler)
    try:
        # Démarrage du planificateur
        scheduler.run()
    except KeyboardInterrupt:
        # Si l'utilisateur appuie sur Ctrl+C, affiche un message et termine proprement le programme
        print("\nArrêt du planificateur...")
           
def signal_handler(sig, frame):
        
        print("Interruption détectée. Traitement en cours...")
        # Mettez ici le code pour effectuer des opérations avant l'arrêt du serveur
        print("Serveur en cours d'arrêt.")
        sys.exit()

signal.signal(signal.SIGINT, signal_handler)
def main():
    appid = config['PARSE_APP_ID']
    rest_api_key = config['PARSE_API_KEY_REST']
    masterkey = config['PARSE_MASTER_KEY']
    url = config['URL_DOMAIN']
    cnf.connect(appid, rest_api_key, masterkey, url)
    # Run the Flask app
   # flask_thread = threading.Thread(target=app_rune)
   # flask_thread.start()
    app_rune()
    #run schedule
   
   #envoyer 
    run_flask_app()
    time.sleep(5)
    # flask_thread.join()
    # app_rune()

def extract_comm():
    data1=[]
    
    detailsTransact=[]
    val={
                        "reference":"",
                        "amount":"",
                        "type":"",
                        "motif":"",
                        "id_client":"",
                        "card":"", 
                        "commission_var":"",
                        "amount_commission":"",
                        "transaction_id":"",
         }
    try :
        now = time.time()
        current_time = time.localtime(now)
        month =  current_time.tm_mon    # Extraire l'année actuelle
        year = current_time.tm_year
        if(month==1) :
            month=12
            year=year-1
        else :
            month=month-1
        data={ "month":month, "year":year}
        company_get=model_api.CppApi.batch_transaction_commission(data)
        data={ "month":month, "year":year,"company":company_get}
        print('Commission')
    
        get_data=model_api.CppApi.commissionBatch(data)
       
        # getCommissionCpp(data)
        totalcomm=0
        logocpp="https://qacseafile.cpp-system.com/pictures?xys=Cpp-Transport/test|4DOMxN4bSqWUEB0hhftj.jpg"        
        if get_data is not None :
                    for item in get_data:
                        args_list = json.loads(item["args"]) # Convert the string representation of a list to an actual list
                        id=item['objectId']
                        
                        company_pay=item['company_pay']
                        month=item['month']
                        year=item['year']      
                        num=random.randint(0, 9999)
                        # ref_fact="FACT-CPP-"+str(year)+"_"+str(month)+"_"+str(num)
                        ref_fact="COMM-CPP-"+str(year)+"_"+str(month)+"_"+str(num) 
                       
                        for args in args_list:
                           
                            totalcomm=float(args["commission_var"])+float(args["amount_commission"])
                            
                            record={
                                                "src":"CPP-PAY",
                                                "type": "COMMISSION",
                                                "company_pay":"CPP-SYSTEM",
                                                "id_adelya_company":0,
                                                "id_partner":company_pay,
                                                "logo":logocpp,
                                                "month":month,
                                                "year":year,
                                                "total":totalcomm,
                                                "total_commission":totalcomm,
                                                "total_commission_var":0,
                                                "status":0,
                                                "periode_paiement":"j+30",
                                                "date_payement":"date+30",
                                                "args":json.dumps([]),
                                                "ref_facture":ref_fact,
                                                "ref_paiement":"",
                                                "payment_method": "",#MM , BNK
                                                "id_external_transac": "Null",#MM , BNK
                                                "psp_name": "",# TLM,ORG,ART,BNI,BOA,BMOI,MCB
                                                "cc1":"", #numero mobile money
                                                "cc2":"", #numero rib
                                                "cc3":"", #other
                                                "cc4":id if args is not None else "", #null if type transaction and value id if commission
                                                "sended":False, #send to company
                                                "url_invoice":"", #url
                                                "email":"",
                                                "num_bill":str(num), #numero
                                    }
                        data1.append(record)
                    if data1 is not None :
                        for args in data1:
                            valueReturn=model_api.CppApi.sendValueToCore(args,'COMMISSION')
                        if(valueReturn=="Success"):
                            print('insertion commission avec success')
                            sys.stdout.flush() 

                        else :
                            print(valueReturn)
                            sys.stdout.flush() 
        else :
            print('Aucun data')
            sys.stdout.flush() 
    except Exception as e :
        print(e)
        sys.stdout.flush() 
        return e    
@app.route('/rap/download/<string:id>')
def download_rap(id):
    chemin_fichier = os.path.realpath("PdfFiles/"+id)
    return send_file(chemin_fichier, as_attachment=True, )

@app.route('/commission', methods=['GET', 'POST'])            
def getCommissionCpp(data):
    print(get_data)
    sys.stdout.flush() 
    totalcomm=0
    #Set parameters
    data={
            "month":12,
            "year":2023,
            "company":data['company']#"mDREP67pC6" #company angalana le commission
    }
    if(data=="") :
      data={
            "month":12,
            "year":2023,
            "company":"mDREP67pC6" #company angalana le commission
        }
    
    types="COMMISSION"
    data1=[]
    detailsTransact=[]
    get_data=model_api.CppApi.commissionBatch(data) 
    
    # return get_data
    val={
                        "reference":"",
                        "amount":"",
                        "type":"",
                        "motif":"",
                        "id_client":"",
                        "card":"", 
                        "commission_var":"",
                        "amount_commission":"",
                        "transaction_id":"",
         }
    detailsTransact.append(val)
    if get_data is not None :
        for item in get_data:
            args_list = eval(item[item['id']]["args"])  # Convert the string representation of a list to an actual list
            id=item[item['id']]['id']
            company_pay=item[item['id']]['company_pay']
            month=item[item['id']]['month']
            year=item[item['id']]['year']       
        for args in args_list:
            totalcomm+=float(args["commission_var"])+float(args["amount_commission"])
            logocpp="https://qacseafile.cpp-system.com/pictures?xys=Cpp-Transport/test|4DOMxN4bSqWUEB0hhftj.jpg"
            num=random.randint(0, 9999)
            # ref_fact="FACT-CPP-"+str(year)+"_"+str(month)+"_"+str(num)
            ref_fact="COMM-CPP-"+str(year)+"_"+str(month)+"_"+str(num)
        record={
                            "src":"CPP-PAY",
                            "type": types,
                            "company_pay":"CPP-SYSTEM",
                            "id_adelya_company":0,
                            "id_partner":company_pay,
                            "logo":logocpp,
                            "month":month,
                            "year":year,
                            "total":totalcomm,
                            "total_commission":totalcomm,
                            "total_commission_var":0,
                            "status":0,
                            "periode_paiement":"j+30",
                            "date_payement":"date+30",
                            "args":json.dumps(detailsTransact),
                            "ref_facture":ref_fact,
                            "ref_paiement":"",
                            "payment_method": "",#MM , BNK
                            "id_external_transac": "Null",#MM , BNK
                            "psp_name": "",# TLM,ORG,ART,BNI,BOA,BMOI,MCB
                            "cc1":"", #numero mobile money
                            "cc2":"", #numero rib
                            "cc3":"", #other
                            "cc4":id, #null if type transaction and value id if commission
                            "sended":False, #send to company
                            "url_invoice":"", #url
                            "email":"",
                            "num_bill":str(num), #numero
                }
        data1.append(record)
        if data1 is not None :
            valueReturn=model_api.CppApi.sendValueToCore(data1,record)
            if(valueReturn=="Success"):
                return 'insertion commission avec success'
            else :
                return 'erreur '
    else :
       return 'Aucun data '
#get transaction pay
def schedule_transaction_pay(scheduler):
    now = time.time()
    current_time = time.localtime(now)
    current_hour = current_time.tm_hour
    current_minute = current_time.tm_min
    day=current_time.tm_mday
    days=1
    hours=11
    minute=1
     #-get all Transaction cpp pay 02 matin 
    if(day==days) : 
        delay_until_1451 = ((hours - current_hour) * 3600) + ((minute - current_minute) * 60)
        scheduler.enter(delay_until_1451, 1, extract_and_run)
        return  'ok'
    else :
        pass
#get commission
def schedule_next_event(scheduler):
    #-commission cpp
    now = time.time()
    current_time = time.localtime(now)
    current_hour = current_time.tm_hour
    current_minute = current_time.tm_min
    day=current_time.tm_mday
    if(day==24 & current_hour==4 & current_minute==30) : 
        delay_until_1451 = ((8 - current_hour) * 3600) + ((1 - current_minute) * 60)
        scheduler.enter(delay_until_1451, 1, extract_comm)
    else :
        pass
    
#-generate facture send Transaction midi
def schedule_udpate_transaction_pay(scheduler):
    now = time.time()
    current_time = time.localtime(now)
    current_hour = current_time.tm_hour
    current_minute = current_time.tm_min
    day=current_time.tm_mday
    # if(day==14 & current_hour==11 & current_minute==13 ) :
    days=1  
    curc=11 
    curren=30 
    if(day==days) : 
        delay_until_1451 = ((curc - current_hour) * 3600) + ((curren- current_minute) * 60)
        scheduler.enter(delay_until_1451, 1, send_and_run)
    else :
        pass
#-Send Mail to company
def schedule_send(scheduler):
    # delay_until_1451=calculateSchedule(13,20)
    now = time.time()
    current_time = time.localtime(now)
    current_hour = current_time.tm_hour
    current_minute = current_time.tm_min
    day=current_time.tm_mday
    days=1  
    curc=12
    curren=30 
    
    if(day==days) : 
        delay_until_1451 = ((curc - current_hour) * 3600) + ((curren - current_minute) * 60)
        scheduler.enter(delay_until_1451, 1, sendMailTo)
    else :
        return 
   
#-Run schedule

def calculateSchedule(hours,minut) :
    now = time.time()
    current_time = time.localtime(now)
    current_hour = current_time.tm_hour
    current_minute = current_time.tm_min
    # Calculate the date of the next month
    delay_until_1451=0
    if (current_time.tm_mday == 13 and current_hour == 15 and current_hour == minut ):
        delay_until_1451 = ((hours - current_hour) * 3600) + ((minut - current_minute) * 60)
       
    # else:
    #     next_run_date = datetime.datetime(now.year, now.month + 1, 13, hours, minut)
   
    #delay_until_next_month = (next_run_date - now).total_seconds()
    # next_month = now.replace(day=13, hour=int(hours), minute=int(minut), second=0, microsecond=0) + datetime.timedelta(days=31)
    # # If the calculated date is beyond the first day of the next month, adjust
    # if next_month.month != (now.month % 12) + 1:
    #     next_month = next_month.replace(day=1)
    # # Calculate the delay until the next month
    # delay_until_next_month = (next_month - now).total_seconds()
    # # Schedule the next execution
    return delay_until_1451
    # scheduler.enter(0, 1, extract_and_run)
def testS() :
    model_api.CppApi.testSchedule()
max_repetitions = 3
def schedule_test_schedule(scheduler):
    now = time.time()
    current_time = time.localtime(now)
    # current_hour = current_time.tm_hour
    # current_minute = current_time.tm_min
    day=current_time.tm_mday
    days=29
    # hours=10
    # minute=55
    
     #-get all Transaction cpp pay 02 matin 
    if(day==days ) : 
        repeat_task(scheduler,5,testS,limit=max_repetitions)
        return  'ok'
    else :
        pass
def repeat_task(scheduler,interval, action, actionargs=(),limit=None):
    if limit is not None:
        if limit <= 0:
            print('stop')
            return "stop"
        limit -= 1
    scheduler.enter(interval, 1, repeat_task, (scheduler,interval, action, actionargs,limit))
    action(*actionargs)
@app.route('/testMysql', methods=['GET'])
def connectMy():
    #### Event  Jours  update  connect to  prod #####
    import mysql
    database_config={
                "username":'cpp_trans_prod',
                "passwd":"VN[*UFpPTD*I8Bh7",
                "url_serve":"102.16.66.6",
                "database":"cpp_trans_prod"
    }
    # sqlstate.connect(,database_config['username'],database_config['passwd'],database_config['database'])
    mydb = mysql.connector.connect(
            host=database_config['url_serve'],
            port=1238,
            user=database_config['username'],
            password=database_config['passwd'],
            database=database_config['database'],
        )
    try :
             mycursor = mydb.cursor()
             sql="SELECT * FROM activate_filtre_montants ORDER BY id DESC LIMIT 1"
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
            
             return myresult
    except Exception as e :
             print(str(e))
             sys.stdout.flush()
             return str(e)    
def run_event_day(scheduler):
    import schedule
    import time
    schedule.every().day.at("09:00").do(get_data)
    while True:
        schedule.run_pending()
        time.sleep(60)
def get_data():
    date_actuelle = datetime.date.today() - datetime.timedelta(days=1)
    dateDebut=dateFin=str(date_actuelle)
    # print(dateDebut)
    # sys.stdout.flush()
    v=run_program()
    v.run_application(dateDebut,dateFin)
    
if __name__ == "__main__":
    app.config['DEBUG'] = True 
    main()
    
    
