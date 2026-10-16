from flask import Flask,session, render_template, url_for, redirect,request,flash,Response,send_file,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from os.path import splitext, basename
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
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import model_api.CppApi
from apscheduler.schedulers.blocking import BlockingScheduler
from flask_restful import Resource, Api
# from tkinter import filedialog
# import tkinter
from dotenv import dotenv_values
import threading 
def getEventPer(month,year):
     
     try :  
           config = dotenv_values(".env")
           PARSE_APP_ID=config['PARSE_APP_ID'] 
           PARSE_MASTER_KEY= config['PARSE_MASTER_KEY'] 
           PARSE_API_KEY_REST=config['PARSE_API_KEY_REST']
           headers = {
                    "X-Parse-Application-Id": f"{PARSE_APP_ID}",
                    "X-Parse-REST-API-Key": f"{PARSE_API_KEY_REST}",
                    "X-Parse-Master-Key": f"{PARSE_MASTER_KEY}",
                    "Content-Type": "application/json"
                }
           params = urllib.parse.urlencode({"limit":1000000,"where": json.dumps({
                "month":str(month),
                "year":str(year),
                "vehicule": {'__type': 'Pointer', 'className': 'CppTransportVehicule', 'objectId': "kUovZlu504"},
            }),"include":"vehicule"})
           myurl='https://bus.cpp-system.com/api/classes/CppTransportEvent'
     
           result=requests.get(myurl,params=params,headers=headers)
           x=result.json()
          
           values=x['results']
           for x in  values :
              #update value
                object_id = x['objectId']
                old_ticket = x.get("ticketNumber", "")
        
        # Modification du ticketNumber si le format est correct
                parts = old_ticket.split('-')
                if len(parts) >= 3:
                    new_ticket = f"0958TBC-{parts[1]}-{parts[2]}"
                else:
                    new_ticket = old_ticket  # garde tel quel si le format est inattendu

                # Payload de mise à jour
                update_payload = {
                    "vehicule": {
                        "__type": "Pointer",
                        "className": "CppTransportVehicule",
                        "objectId": "kQLbIpLBgW"
                    },
                    "ticketNumber": new_ticket
                }
                update_url = f"{myurl}/{object_id}"
                
                update_response = requests.put(update_url, headers=headers, data=json.dumps(update_payload))
                print(f"Updated object {object_id}: {update_response.status_code}")
                sys.stdout.flush()
               
     except Exception as e:
          print(e)
getEventPer("5","2025")