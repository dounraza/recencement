from main import main
from Configuration import Configuration
import sys
from dotenv import dotenv_values
from datetime import date
import json
import datetime
import rarfile
from PIL import Image
import shutil
import time
import requests
import os;
import openpyxl
from openpyxl import Workbook,load_workbook
import datasql

config = dotenv_values(".env")
prog= main()
cnf= Configuration()

url_sql=config['URL_MYSQL']
username=config['USER_MYSQL']
password=config['PASSWORD']
databasename=config['DATABASE_NAME']
appid=config['PARSE_APP_ID']
rest_api_key=config['PARSE_API_KEY_REST']
masterkey=config['PARSE_MASTER_KEY']
url=config['URL_DOMAIN']
database_config={
                "username":username,
                "passwd":password,
                "url_serve":url_sql,
                "database":databasename
            }
cnf.connect(appid, rest_api_key, masterkey, url)            
class alignement:
     def alignement_data(self):
        from datetime import datetime
        file_path = 'myfiles/ca17.xlsx'  # Replace with the path to your file
       
        if os.path.isfile(file_path):
            # Charger le classeur Excel
            workbook = openpyxl.load_workbook(file_path)

            # Sélectionner la feuille active
            sheet = workbook.active
            sheet.delete_rows(0)
            # Itérer sur chaque ligne et colonne
            for row in sheet.iter_rows(values_only=True):
                date=str(row[0]).split(' ')
                date_obj = datetime.strptime(date[0], "%Y-%m-%d")
                
                date_formatted = date_obj.strftime("%d/%m/%Y")

                data={
                        "cash_nombre":row[3],
                        "tour":row[4],
                        "cpp_nombre":row[5],
                        "totalClient":int(row[3])+int(row[5]),
                        "somme_cash":row[2],
                        "somme_cpp":row[6],
                        "somme_prix":int(row[6])+int(row[2]),
                        "date":date_formatted,
                        "vehicule":row[1]
                }
                self.get_event_data(data)
                    # print(str(cell).encode('utf-8'))  # Imprimer la valeur de chaque cellule, avec une tabulation entre chaque cellule
              # Aller à la ligne après chaque ligne de données

            # Fermer le classeur Excel
            workbook.close()
        else:
            print("Le fichier spécifié n'existe pas.")
                
     def get_event_data(self,data):
        sqlstate=datasql.ConfigurationSql()
        # print(data['date'])
        sqlstate.getEventJours(database_config,data)

  

# dateDebut = sys.argv[1]
# dateFin = sys.argv[2]
v=alignement()
v.alignement_data()