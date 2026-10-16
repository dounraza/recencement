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
config = dotenv_values(".env")

# config = dotenv_values("c:/wamp64/www/extract/cpptransportextract/.env")
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
class run_program:
     def run_application(self,debutdate,findate):
          datex={
            "dateDebut":debutdate,
            "dateFin":findate,
          }
         
          separateDate=debutdate.split('-')
          month=int(separateDate[1])
          year=int(separateDate[0])
          dayd=int(separateDate[2])
          start = date(year,month,dayd)
          separateDate1=findate.split('-')
          month1=int(separateDate1[1])
          year1=int(separateDate1[0])
          dayd1=int(separateDate1[2])
          end = date(year1, month1, dayd1)
       
          value=(end-start).days

          periods = value+1
          daterange = []
          for day in range(periods):
              datep = (start + datetime.timedelta(days = day)).isoformat()
              daterange.append(datep)
          for x in daterange :
            datex={
            "dateDebut":x,
            "dateFin":x,
            }
            
            value_extract=prog.extractDataw(datex)
            value_pointage=cnf.ExtractPointage(database_config, x, x)
            value_incident=cnf.getIncidentS(database_config,x)
            value_cotisation=cnf.getCotisation(x,database_config)
            # data_ret=value_cotisation
            data_ret=debutdate+"=> \n"+value_cotisation+"=> \n"+findate
          return data_ret
          print("## Debut  de l'extraction pointage ## ")
          # cnf.ExtractPointage(database_config, debutdate, findate)
          print("## Fin  de l'extraction pointage ##")
          print("## Debut  de l'extraction event jour  ## ")
          prog.extractDataw(datex)
          print("## Fin  de l'extraction  event jour  ##")
          
          print("*************************************")
          print("## Debut  de l'extraction commission ##")
          # p=cnf.getVehiculeAll(database_config)
          # for x in p :
          #  com=cnf.getCommissionParExtract(database_config,str(f"{debutdate}"),str(f"{findate}"),x)
          print("## Fin  de l'extraction commission ##")
          print("*************************************")
          print("## Debut  de l'extraction incident ##")
           #debut
          separateDate=debutdate.split('-')
          month=int(separateDate[1])
          year=int(separateDate[0])
          dayd=int(separateDate[2])
          datecc=str(dayd)+"/"+str(month)+"/"+str(year)
            #fin
          separateDate1=findate.split('-')
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
          # for day in range(periods):
          #     datep = (start + datetime.timedelta(days = day)).isoformat()
          #     daterange.append(datep)
          # for x in daterange :
          #     value=cnf.getIncidentS(database_config,x)
          print("## Fin  de l'extraction incident ##")
          sys.stdout.flush()

# dateDebut = sys.argv[1]
# dateFin = sys.argv[2]
# v=run_program()
# v.run_application(dateDebut,dateFin)