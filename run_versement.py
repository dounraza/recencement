from main import main
from Configuration import Configuration
from dotenv import dotenv_values
from datetime import date
import sys,json,datetime,shutil,time,requests,urllib,http.client
import base64
from PIL import Image
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
parse_url=config['URL_DOMAIN']
database_config={
                "username":username,
                "passwd":password,
                "url_serve":url_sql,
                "database":databasename
            }

class run_versement :
     def run_application(self,date):
        self.appid = appid
        self.rest_api_key = rest_api_key
        self.url = url
        self.masterkey = masterkey
        self.headers = {
                "X-Parse-Application-Id": f"{self.appid}",
                "X-Parse-REST-API-Key": f"{self.rest_api_key}",
                "X-Parse-Master-Key": f"{self.masterkey}",
                "Content-Type":"application/json"
            } 
        
        #27/09/2023 
        dateDebut = date+" 00:00:59" 
        dateFin = date+" 23:59:59"
        try : 
          params = urllib.parse.urlencode({"limit":10000000,"where": json.dumps({
                "dateStart": {
                    "$gte": f"{dateDebut}",
                    "$lte": f"{dateFin}",
                },
              
            }),"include":"vehicule"})
          myurl=self.url+'/classes/CppEventTournee'
          result=requests.get(myurl,params=params,headers=self.headers)
        
          x=result.json()
          values=x['results']
          # Créer un dictionnaire pour stocker la somme de chaque bus
          bus_summaries = {} 
          for bus in values:
                traitement_type='Versement'
                commPass=bus['commPass']
                commCash=bus['commCash']
                objectId =bus['vehicule']['objectId']
                cashCA = bus['cashCA']
               
                passCA = bus['passCA']
                totalCA = bus['totalCA']
                vehicule = bus['vehicule']['numero']
                amount2pay=passCA-commPass
                
                # TO DO : search in versement 
                # to Do : get proprio
                
                # Si l'identifiant du bus n'est pas déjà dans le dictionnaire, l'initialiser
                if objectId not in bus_summaries:
                    bus_summaries[objectId] = {"vehicule":"#","type":traitement_type,'cashCA_sum': 0, 'passCA_sum': 0, 'totalCA_sum': 0,'commCash':0,'commPass':0,'amount2pay':0}
                paramProprio=cnf.infoProprio(database_config,vehicule,f"{date}",amount2pay)
          
                # Mettre à jour les sommes pour ce bus
                encoded_data= json.dumps(paramProprio)
                bus_summaries[objectId]['vehicule'] = vehicule 
                bus_summaries[objectId]['type'] = traitement_type   
                bus_summaries[objectId]['date'] = f"{date}" 
                bus_summaries[objectId]['cashCA_sum'] += cashCA
                bus_summaries[objectId]['passCA_sum'] += passCA
                bus_summaries[objectId]['totalCA_sum'] += totalCA   
                bus_summaries[objectId]['commCash'] +=commCash
                bus_summaries[objectId]['commPass'] +=commPass
                bus_summaries[objectId]['amount2pay'] +=amount2pay
                bus_summaries[objectId]['args_prop'] =encoded_data
                
          self.CreateVersementBatch(bus_summaries,objectId)
        except Exception as e:
            print(e)
            return e
            ##
     def CreateVersementBatch(self,data,objectId) :
            headers = {
                    "X-Parse-Application-Id":f"{self.appid}",
                    "X-Parse-REST-API-Key": f"{self.rest_api_key}",
                    "Content-Type": "application/json"
                  
            }
            try :
                for x in data :
                    
                    payload = {
                        "numero": data[x]['vehicule'],
                        "type": data[x]['type'],
                        "cash_amount": str(data[x]['cashCA_sum']),
                        "pass_amount": str(data[x]['passCA_sum']),
                        "commCash_amount": str(data[x]['commCash']),
                        "commPass_amount": str(data[x]['commPass']),
                        "date": data[x]['date'],
                        "pay_amount": str(data[x]['amount2pay']),
                        "total": str(data[x]['totalCA_sum']),
                        "args_props": str(data[x]['args_prop']),
                        "status": "1",
                            
                    }
                    #self.url+
                    response = requests.post("https://qatransport.cpp-system.com/parse/classes/VersemenetBatch", json=payload, headers=headers)
                    if(response.status_code==200) :
                        return response.text
            except Exception as e:
                print(e.status_code)
                return "not"
     def batchAllVersement(self,dateDebut) :
         #Get account proprio 
        url_core = config['CORE_DOMAIN_URL_MP']
        #key bearer
        pri_key_core = config['PRIVATE_KEY_MP']
        pub_key_core =config['PUBLIC_KEY_MP']
        s=pub_key_core+":"+pri_key_core
        datax=base64.b64encode(s.encode('UTF-8')).decode('UTF-8')
        self.appid = appid
        self.rest_api_key = rest_api_key
        self.url = url
        self.masterkey = masterkey
        self.headers={
                    "X-Parse-Application-Id":f"{self.appid}",
                    "X-Parse-REST-API-Key": f"{self.rest_api_key}",
                    "Content-Type": "application/json"
                  
                    }
        try : 
          objEv = []
          objEvsp = ''
          today=dateDebut
          params = urllib.parse.urlencode({"limit":10000000,"where": json.dumps({
                "date":today,
            })})
          myurl=self.url+'/classes/VersemenetBatch'
          result=requests.get(myurl,params=params,headers=self.headers)
          
          x=result.json()
         
          values=x['results']
          for x in values :
              
              separateDate=x["date"].split('/')
              
              vehiculeObjectId=json.loads(x["args_props"])
              paramProprio=vehiculeObjectId
             
              obj=cnf.getObjectIdEventComm(x["date"],vehiculeObjectId["objectIdVehicule"])
              if(obj!='' or obj is not None) :
                            objEv.append(obj)
                            objEvsp+=obj+'|'
              tokenbear=cnf.getTokenCore(datax,url_core)
           
              #send To core demande versement
              cnf.sendValueCore(url_core,paramProprio,tokenbear,database_config,objEvsp,separateDate[1],separateDate[2])
        except Exception as e :
            print(e)
            return ""
         
# dateDebut = "23/08/2023" 
# rv=run_versement()
# response=rv.batchAllVersement(dateDebut)
# print(response)