from array import array
from ast import dump
import http.client
import json
from posixpath import split
from time import strftime
from urllib import response
import urllib
import uuid
import datetime
import base64
import sys,os,io
from datetime import date
#import requests
import urllib.parse
from dotenv import dotenv_values
import requests
import openpyxl
import csv
import multiprocessing
from openpyxl import Workbook,load_workbook

from dotenv import dotenv_values
config = dotenv_values(".env")
class event: 
    def traiter_donnees_multiprocessing(self,donnees, num_processus, output_file):
        # Diviser les données en chunks
        chunk_size = len(donnees) // num_processus
        chunks = [donnees[i:i+chunk_size] for i in range(0, len(donnees), chunk_size)]

        # Créer les processus
        processus = []
        for chunk in chunks:
            p = multiprocessing.Process(target=self.ecrire_donnees_csv, args=(chunk, output_file))
            processus.append(p)
            p.start()

        # Attendre que tous les processus se terminent
        for p in processus:
            p.join()
    def ecrire_donnees_csv(self,chunk, output_file):
        with open(output_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile,delimiter=';')
            writer.writerows(chunk)
    def getEventParBus(self,date):
        from datetime import datetime
        URL_DOMAIN=config['URL_DOMAIN']
        PARSE_APP_ID=config['PARSE_APP_ID'] 
        PARSE_MASTER_KEY= config['PARSE_MASTER_KEY'] 
        PARSE_API_KEY_REST=config['PARSE_API_KEY_REST']

        self.appid = PARSE_APP_ID
        self.rest_api_key = PARSE_API_KEY_REST
        self.url = URL_DOMAIN
        self.masterkey = PARSE_MASTER_KEY
        self.headers = {
                "X-Parse-Application-Id": f"{self.appid}",
                "X-Parse-REST-API-Key": f"{self.rest_api_key}",
                "X-Parse-Master-Key": f"{self.masterkey}",
                "Content-Type": "application/json"
            }
        dataj=[]
        date_obj = datetime.strptime(date, "%d/%m/%Y")
          
            # Extraire le mois de l'objet datetime
        month = date_obj.month
        year = date_obj.year
       
        try :  
            dateb=date+" 00:00:59"
            dateend=date+" 23:59:00"
          
            params = urllib.parse.urlencode({"limit":1000000,"where": json.dumps({
                "date": {
                    "$gte": f"{dateb}",
                    "$lte": f"{dateend}",
                },
               
                "transacType":"OK",
                "cancelled":False,
                "month":str(month),
                "year":str(year), 
            }),"include":"vehicule,arret"})
            myurl=self.url+'/classes/CppTransportEvent'
            result=requests.get(myurl,params=params,headers=self.headers)
            x=result.json()
            values=x['results']
            nb=1
            donnees = [["vehicule","date","localisation","Arret","Type","TicketNumber","Nombre"]]
            for x in values :
                if(x['type'] in ['CASH','PASS']):
                    numero=x['vehicule']['numero'] if x['vehicule']['numero'] is not None else "#"
                    dates=x['date'] if x['date'] is not None else "#"
                    latitude=x['localisation']['latitude'] if x['localisation']['latitude'] is not None else "0"
                    longitude=x['localisation']['longitude'] if x['localisation']['longitude'] is not None else "0"
                    arret=x['arret']['arret'] if x['arret']['arret'] is not None else "CPP-SYSTEM"
                    arret=x['arret']['arret'] if x['arret']['arret'] is not None else "CPP-SYSTEM"
                    type=x['type'] if x['type'] is not None else "CASH"
                    ticket=x['ticketNumber'] if x['ticketNumber'] is not None else "#"
                    values_ytype = [numero, dates, str(latitude)+","+str(longitude),arret,type,ticket,nb]
                    donnees.append(values_ytype)
                
            return  donnees
        except Exception as e:
            # dataj.append({})
            print(e)
            sys.stdout.flush()

    def createCsvData(self,data1) :
        from datetime import datetime
        import csv
        # Obtention de la date et de l'heure actuelles
        maintenant = datetime.now()
        workbook = Workbook()
        sheet = workbook.active
        listData=list()
        date_courante = maintenant
        date_name=maintenant.strftime("%Y-%m-%d")
        #check file if exist 
        nameFile=str(date_name)+"_event_details.csv"
        file_path = 'event/'+nameFile
        donnees_existants = []
        with open(file_path, 'r', newline='') as fichier_csv:
            reader = csv.reader(fichier_csv, delimiter=';')
            for ligne in reader:
                donnees_existants.append(ligne)
        donnees = donnees_existants + data1
        with open(file_path, 'w', newline='') as fichier_csv:
            writer = csv.writer(fichier_csv, delimiter=';')
            for ligne in donnees:
                writer.writerow(ligne)

        # file_path = 'event/'+nameFile  # Replace with the path to your file
       
        # if os.path.isfile(file_path):
        #     workbook1 = openpyxl.load_workbook(file_path)
            
        #     sheet1 = workbook1.active
            
        #     for x in data1 :
        #         data=[[x['vehicule'],x['date'],x['localisation'],x['Arret'],x['type'],str(x['Nombre'])]]
        #     for row_data in data:
        #         sheet1.append(row_data)
        #         workbook1.save(filename=file_path)
        # else:
            
        #     listData.append(("vehicule","date","localisation","Arret","type","Nombre"))
        #     try :
        #         for x in data1 :
        #             listData.append((x['vehicule'],x['date'],x['localisation'],x['Arret'],x['type'],str(x['Nombre'])))
        #         c=tuple(listData)
        #         temp_file="event/"+date_name+"_event_details"+".xlsx"
        #         real_path = os.path.realpath(temp_file)
        #         excel_io = io.BytesIO()   
        #         excel_io.seek(0)
        #         for row in c:
        #             sheet.append(row)
        #             workbook.save(temp_file)
        #     except Exception as e :
        #     
        #     return print(e)
if __name__ == '__main__':
    event1=event()
    from datetime import datetime, timedelta
    #To do  (01 a 23)
    # dates='01/05/2024'
    date_debut = datetime.strptime('12/05/2024', '%d/%m/%Y')
    date_fin = datetime.strptime('23/05/2024', '%d/%m/%Y')

    # Tableau pour stocker les dates
    dates_array = []

    # Boucle pour générer les dates
    current_date = date_debut
    while current_date <= date_fin:
        dates_array.append(current_date)
        current_date += timedelta(days=1)

    # Affichage des dates pour vérification
    for date in dates_array:
        dates=date.strftime('%d/%m/%Y')
        print(dates)
        donnees=event1.getEventParBus(dates)
            # Nombre de processus à utiliser
        if donnees is not None :
            num_processus = 4

                # Nom du fichier de sortie
            output_file = 'event/donnees1.csv'

                # Appeler la fonction de traitement multi-processing
            event1.traiter_donnees_multiprocessing(donnees, num_processus, output_file)
            print("success")
            sys.stdout.flush()