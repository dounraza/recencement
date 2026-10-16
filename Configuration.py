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
import sys
from datetime import date
#import requests
import urllib.parse
from dotenv import dotenv_values
import requests
import datasql

config = dotenv_values(".env")

# config = dotenv_values("c:/wamp64/www/extract/cpptransportextract/.env")
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
class Configuration:
  def connect(self, appid, rest_api_key,masterkey,url):
    self.appid = appid
    self.rest_api_key = rest_api_key
    self.url = url
    self.masterkey = masterkey
    self.headers = {
            "X-Parse-Application-Id": f"{self.appid}",
            "X-Parse-REST-API-Key": f"{self.rest_api_key}",
            "X-Parse-Master-Key": f"{self.masterkey}",
            "Content-Type": "application/json"
        }
	
  def getEvent(self,dateb,dateend,database_config,month,year):
     
     try :  
         
          params = urllib.parse.urlencode({"limit":1000000,"where": json.dumps({
                "date": {
                    "$gte": f"{dateb}",
                    "$lte": f"{dateend}",
                },
                "month":str(month),
                "year":str(year),
                "cancelled":False,
            }),"include":"vehicule"})
          myurl=self.url+'/classes/CppTransportEvent'
          
          result=requests.get(myurl,params=params,headers=self.headers)
          # print("Status : "+str(result.status_code))
          x=result.json()
          
          values=x['results']

          vehicule=[]
         
          sqlstate=datasql.ConfigurationSql()
            
          sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
          
          tab=[]
          
          for x in  values :
               if 'vehicule' in x:
                  vehicule.append(x['vehicule']['objectId'])
               
         
          objectIdvehicule=list(set(vehicule))
         
          for x in  objectIdvehicule :
              for y in  values :
                if 'vehicule' in y:
                  if x == y['vehicule']['objectId'] :
                   
                    xdate=y['date'].split(" ")
                    #tab={'date':xdate[0],'vehicule':x}
                    #print(xdate[0])
                    
                    tab.append(str(xdate[0])+"|"+x)
                  
                    
                    
                    #tab["vehicule"].append(x)
         
          eventVehicuList=list(set(tab))
          if (len(eventVehicuList))!=0 :
              for x in  eventVehicuList :
                eventCurrent=x.split('|')
               
                #vehicule,date,month1,year1
                valuetext=self.setData(values,eventCurrent[1],eventCurrent[0],str(month),str(year))
             
                sqlstate.insertEventJours(valuetext,eventCurrent[1],eventCurrent[0],str(month),str(year))
          return ''
          return ("Extraction  entre "+dateb+" à "+dateend+" avec succès \n")    
     except Exception as e: 
          print (e)    
  def getEventTournee(self,dateb,dateend,database_config,month,year):
     
     try :  
          
          params = urllib.parse.urlencode({"limit":1000000,"where": json.dumps({
                "dateStart": {
                    "$gte": f"{dateb}",
                    "$lte": f"{dateend}",
                },
                "status":{"$ne":"FIN DE SERVICE"} ,
            }),"include":"vehicule"})
          myurl=self.url+'/classes/CppEventTournee'
          
          result=requests.get(myurl,params=params,headers=self.headers)
          # print("Status : "+str(result.status_code))
          x=result.json()
          
          values=x['results']

          vehicule=[]
         
          sqlstate=datasql.ConfigurationSql()
            
          sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
          
          tab=[]
          for x in  values :
               if 'vehicule' in x:
                  vehicule.append(x['vehicule']['objectId'])
               
         
          objectIdvehicule=list(set(vehicule))
          
          for x in  objectIdvehicule :
              for y in  values :
                if 'vehicule' in y:
                  if x == y['vehicule']['objectId'] :
                   
                    xdate=y['dateStart'].split(" ")
                    #tab={'date':xdate[0],'vehicule':x}
                    #print(xdate[0])
                    
                    tab.append(str(xdate[0])+"|"+x)
                  
                    
                    
                    #tab["vehicule"].append(x)
         
          eventVehicuList=list(set(tab))
          if (len(eventVehicuList))!=0 :
              for x in  eventVehicuList :
                eventCurrent=x.split('|')
               
                #vehicule,date,month1,year1
                valuetext=self.setDataTourne(values,eventCurrent[1],eventCurrent[0],str(month),str(year))
             
                sqlstate.insertEventJours(valuetext,eventCurrent[1],eventCurrent[0],str(month),str(year))
          return ''
          return ("Extraction  entre "+dateb+" à "+dateend+" avec succès \n")    
     except Exception as e: 
          print (e)    
  def setData(self,values,vehicule,date,month1,year1):
    cash=0
    cpp=0
    nb_tournne=self.getInforTourne(vehicule,date)
    month=month1
    year=year1
    montancCash=0
    montancCpp=0
    nb_annulation=0
    billet=[]
    for x in  values :
        #to do fonction billetage to json
        if 'vehicule' in x:
          if (x['vehicule']['objectId'])==vehicule :
            numero_imm=x["vehicule"]["numero"]
            datev=x['date'].split(" ")
            if(datev[0]) == date :
              if x['transacType'] in ["OK","CASH_COLIS","PASS_COLIS","CASH_SPECIAL","PASS_SPECIAL","CASH_GRATUIT","PASS_GRATUIT"]:
                  billet.append(x['fvalue'])
                  if x['type']=="CASH" :
                    cash+=1
                    if(x["fvalue"]!="0") :
                      montancCash+=(abs(float(x["fvalue"])))
                  if x['type']=="CPP" :
                    cpp+=1
                    if(x["fvalue"]!="0") :
                      montancCpp+=(abs(float(x["fvalue"])))
              if x['transacType']=="CANCELLATION" :
                nb_annulation+=1
            
    billetage=dict([(n, billet.count(n)) for n in set(billet)])
    text=(vehicule,numero_imm,date,str(nb_tournne),"0",str(month),str(year),str(cash),str(cpp),str(cash+cpp),str(nb_annulation),float(montancCpp+montancCash),float(montancCash),float(montancCpp),'non versé',str(billetage),0)
    return text
  def setDataTourne(self,values,vehicule,date,month1,year1):
    cash=0
    cpp=0
    nb_tournne=self.getInforTourne(vehicule,date)
    month=month1
    year=year1
    montancCash=0
    montancCpp=0
    nb_annulation=0
    billet=[]
    
    for x in  values :
        if 'vehicule' in x:
            if (x['vehicule']['objectId'])==vehicule :
                numero_imm=x["vehicule"]["numero"]
                datev=x['dateStart'].split(" ")
                if(datev[0]) == date :
                      # billet.append(x['amountDetails'])
                      if 'cashCount' in x:
                        cash+=int(x['cashCount'])
                      if 'cashCA' in x:
                        montancCash+=(abs(float(x["cashCA"])))
                      else:
                        montancCash+=0
                      
              
                      if 'passCount' in x:
                        cpp+=(abs(float(x["passCount"])))
                      else:
                        cpp+=0
                      if 'passCA' in x:
                        montancCpp+=(abs(float(x["passCA"])))
                      else:
                        montancCpp+=0
                      if 'cancelCount' in x:
                        nb_annulation+=(abs(float(x["cancelCount"])))
                      else:
                        nb_annulation+=0
                
     # billetage=dict([(n, billet.count(n)) for n in set(billet)])
    text=(vehicule,numero_imm,datev[0],str(nb_tournne),"0",str(month),str(year),str(cash),str(cpp),str(cash+cpp),str(nb_annulation),float(montancCpp+montancCash),float(montancCash),float(montancCpp),'non versé',"",0)
    return text 
            
  def getEventParBus(self,dateb,dateend,month,year):
     try :  
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({
                "date": {
                    "$gte": f"{dateb}",
                    "$lte": f"{dateend}",
                },
                "month":str(month),
                "year":str(year)
            })})
          myurl=self.url+'/classes/CppTransportEvent'
          result=requests.get(myurl,params=params,headers=self.headers)
          x=result.json()
          values=x['results']
          vehicule=[]
      
     except :
          print("An exception occurred")
  def getArretLists(self,database_config) :
      sqlstate=datasql.ConfigurationSql()
      sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
      objectId=sqlstate.getArretSql()
      myurl=self.url+'/classes/CppBusArret'
      for x in range(1,431,1) :
          # params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({'objectId':f"{objectId[x][8]}"})
          #     })
 
          # result=requests.get(myurl,params=params,headers=self.headers)
          # px=result.json()
          # values=px['results']
          #if not values:
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({'arret':f"{objectId[x][1]}",'quartier':f"{objectId[x][5]}"})
              })
          result=requests.get(myurl,params=params,headers=self.headers)
          px=result.json()
          values=px['results']
          for x in values :
             if "location" in x:
              location="{lat :"+str(x['location']['latitude'])+", lng :"+str(x['location']['longitude'])+"}"
              sqlstate.updateArret(location,x['objectId'],x['arret'],x['quartier']) 
           
      print("#")
          
                  
  def getCommissionParBus(self,dateb,vehicule):
     sommecomm=0
     try :  
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({"realDate": dateb,'vehicule': {'__type': 'Pointer', 'className': 'CppTransportVehicule', 'objectId': f"{vehicule}"}})
          })
          myurl=self.url+'/classes/CppCommissionEvent'
          result=requests.get(myurl,params=params,headers=self.headers)
          x=result.json()
          values=x['results']
          for x in values :
            if x['type']=="commission" :
                if x['status']=="en attente" :
                  sommecomm+=abs(float(x['montant']))
         
          return sommecomm
     except :
          print("An exception occurred")
  def SoldeVersement(self,date) :
          myurl=self.url+'/classes/CppCommissionEvent'
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({"status": "en attente","realDate":f"{date}"})
          })    
          result=requests.get(myurl,params=params,headers=self.headers)
          da=result.json()
          values=da['results']
          datArray=[]
          for x in values :
             if x != None :
               self.updateSolde(x['objectId']) 

  def updateSolde(self,objectId) :
          myurl=self.url+'/classes/CppCommissionEvent/'+f"{objectId}"
          custom_json = {"status": "Versement terminé","raison":"Demande de versement Manuel (cash)"}
          p=requests.put(myurl, data = json.dumps(custom_json),headers=self.headers)
          return p
  def getCommissionetCAParBus(self,dateb,vehicule):
     sommecomm=0
     sommecpp=0
     sommecommenc=0
     sommecommvalid=0
     params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({"realDate": dateb,'vehicule': {'__type': 'Pointer', 'className': 'CppTransportVehicule', 'objectId': f"{vehicule}"}})
          })
     myurl=self.url+'/classes/CppCommissionEvent'
     print(self)
     result=requests.get(myurl,params=params,headers=self.headers)
     x=result.json()
     values=x['results']
    
     try :
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({"realDate": dateb,'vehicule': {'__type': 'Pointer', 'className': 'CppTransportVehicule', 'objectId': f"{vehicule}"}})
          })
          myurl=self.url+'/classes/CppCommissionEvent'
          result=requests.get(myurl,params=params,headers=self.headers)
          x=result.json()
          values=x['results']
          for x in values :
            if x['type']=="commission" :
                if x['status']=="en attente" :
                  sommecomm+=abs(float(x['montant']))
                if x['status']=="en cours" :
                  sommecommenc+=abs(float(x['montant']))
                if x['status']=="terminée" :
                  sommecommvalid+=abs(float(x['montant']))
            if x['type']=="CA" :
                if x['status']=="en attente" :
                  sommecpp+=abs(float(x['cppCA']))
          #som,enc,valid,ca getMonthCommission
          
          return str(sommecomm)+"|"+str(sommecommenc)+"|"+str(sommecommvalid)+"|"+str(sommecpp)+"|"+str(dateb)
     except Exception as e :
          print(e)
          return str(sommecomm)+"|"+str(sommecommenc)+"|"+str(sommecommvalid)+"|"+str(sommecpp)+"|"+str(dateb)
  def getCommissionParExtract(self,database_config,dateb,datef,vehicule):
    separateDate=dateb.split('-')
    month=int(separateDate[1])
    year=int(separateDate[0])
    dayd=int(separateDate[2])
    datecc=separateDate[2]+"/"+separateDate[1]+"/"+separateDate[0]
    #fin
    separateDate1=datef.split('-')
    month1=int(separateDate1[1])
    year1=int(separateDate1[0])
    dayd1=int(separateDate1[2])
    datefin=separateDate1[2]+"/"+separateDate1[1]+"/"+separateDate1[0]
   
     #get list date#
    start = date(year,month,dayd)
    end = date(year1, month1, dayd1)
    value=(end-start).days

    periods = value+1
    daterangeversement = []
    sqlstate=datasql.ConfigurationSql()
    sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
   
    for day in range(periods):
        datep = (start + datetime.timedelta(days = day)).strftime("%d/%m/%Y")
        daterangeversement.append(datep)
    try :  
          for x in daterangeversement :
              sommecomm=self.getCommissionetCAParBus(x,vehicule)
         
          # sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
              valus=sommecomm.split('|')
              text=(str(valus[0]),str(valus[1]),str(valus[2]),str(vehicule),str(month),str(year),"","",str(valus[3]),"0")
              sqlstate.getMonthCommission(database_config,text)
    except Exception as e :
          print(e)
  def getCAParBus(self,dateb,vehicule):
     sommeca=0
     try :  
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({"realDate": dateb,'vehicule': {'__type': 'Pointer', 'className': 'CppTransportVehicule', 'objectId': f"{vehicule}"}})
          })
          myurl=self.url+'/classes/CppCommissionEvent'
          result=requests.get(myurl,params=params,headers=self.headers)
          x=result.json()
          values=x['results']
          for x in values :
            if x['type']=="CA" :
               if(x['status'])=="en attente" :
                  sommeca+=abs(float(x['cppCA']))
                 

          return sommeca
     except :
          print('Get CA error  '+str(f"{vehicule}"))
          return 0
  def getPaps(self,database_config,data) :
      sqlstate=datasql.ConfigurationSql()
      try :
          sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
          suivi=sqlstate.getPapiers(data)    
          return suivi 
      except Exception as e :
          print(e)
          return ""
     
     
  def sendSmsviaCpp(self,url_core,database_config,vehicule,data) :
      sqlstate=datasql.ConfigurationSql()
      try :
          sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
          numero=sqlstate.getNumeroProprio(vehicule)    
          header = {
                  "Content-Type": "application/json",
                  "Accept": "*/*",
                  "X-CORE-AGENT": database_config['core_agent']
              }
            
          datajson={
                "source": "TRANSPORT",
                "to": f"{numero}",
                "template": "null",
                "data": 'Votre '+f"{data}"+" sur la véhicule "+f'{vehicule}'+" est expiré!"
            }
          # print(datajson)
          response = requests.post(url_core+"/api/sms", json=datajson, headers=header, timeout=120)
          if response.status_code == 200 :
              datasuccess=response.json()
              print(datasuccess)
          else :
              print(response.text)
      except Exception as e :
          print(e)
          return ""
  def getVehiculeAll(self,database_config) :
      sqlstate=datasql.ConfigurationSql()
      sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
      vehi=sqlstate.getVehicule()
      return vehi
  def getObjectIdEventComm(self,dateb,vehicule):
     obj=""
     self.appid = appid
     self.rest_api_key = rest_api_key
     self.url = url
     self.masterkey = masterkey
     self.headers = {
            "X-Parse-Application-Id": f"{self.appid}",
            "X-Parse-REST-API-Key": f"{self.rest_api_key}",
            "X-Parse-Master-Key": f"{self.masterkey}",
            "Content-Type": "application/json"
        }
     try :  
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({"realDate": dateb,'vehicule': {'__type': 'Pointer', 'className': 'CppTransportVehicule', 'objectId': f"{vehicule}"}})
          })
          myurl=self.url+'/classes/CppCommissionEvent'
          result=requests.get(myurl,params=params,headers=self.headers)
          x=result.json()
          values=x['results']
          for x in values :
            if x['type']=="CA" :
              if(x['status'])=="en attente" :
                  if(x['sourceCA'])=="cash-cpp" :
                      obj=x['objectId']
                      
          return obj
     except Exception as e:
          print(e)

  def getAllVehicule(self,dateb):
    
     sommecomm=0
     separateDate=dateb.split('/')
     month=int(separateDate[1])
     year=separateDate[2]
     
     vehicle=[]
     try :  
          datedebut=dateb+" 00:00:00"
          dateend=dateb+" 23:59:00"
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({
            "date": {
                    "$gte": f"{datedebut}",
                    "$lte": f"{dateend}",
                },
                "cancelled":True,
                "month":str(month),
                "year":str(year)}),
          })
          myurl=self.url+'/classes/CppTransportEvent'
          result=requests.get(myurl,params=params,headers=self.headers)
          x=result.json()
          values=x['results']
          p=0
          for x in values :
            #print("uuid: "+x['uniqueId']+"| date : "+x['date']+"| montant :"+x['fvalue'])
            vehicle.append(x['vehicule']['objectId'])
          return (list(set(vehicle)))
     except :
          return vehicle
  def getIncidentS(self,database_config,dateb) :
     separateDate=dateb.split('-')
     month=int(separateDate[1])
     month1=separateDate[1]
     year=separateDate[0]
     dayd=separateDate[2]
     date=str(dayd)+"/"+str(month1)+"/"+str(year)
    #fin
     supportIncidents=[]
     url = self.url
     masterkey = self.masterkey
     rest_api_key=self.rest_api_key
     appid=self.appid
     sqlstate=datasql.ConfigurationSql()
     headers = {
                  "X-Parse-Application-Id":f"{appid}",
                  "X-Parse-REST-API-Key": f"{rest_api_key}",
                  "X-Parse-Master-Key": f"{masterkey}",
                  "Content-Type": "application/json"
              }
              
     try :  
          datedebut=date+" 00:00:00"
          dateend=date+" 23:59:00"
          dat=[]
          params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({
            "date": {
                    "$gte": f"{datedebut}",
                    "$lte": f"{dateend}",
                }
                 }),"include":"type,vehicleId"})
          myurl=url+'/classes/CppTransportIncident'
          result=requests.get(myurl,params=params,headers=headers)
          x=result.json()
         
          values=x['results']
          if not values :
             pass
          else :
              for p in values :
              #if(p['type']['target']=="S"):
                  dat=str(p['date']).split(' ')
                  text=(str(p['type']['type']),str(p['type']['target']),str(p['date']),str(p['vehicleId']['numero']),str(p['duration']),str(p['amount']),str(p['comments']),str(month),str(year),str(dat[0]))
                  # print(text)
                  
                  sqlstate.insertIncidentJours(database_config,text)
               
          return "Extraction incident with successfully!"
     except Exception as e :
          return "Error Extraction incident!"
  def getCotisation(self,datedebut,database_config):
        separateDate=datedebut.split('-')
        month=int(separateDate[1])
        month1=separateDate[1]
        year=separateDate[0]
        dayd=separateDate[2]
        date=str(dayd)+"/"+str(month1)+"/"+str(year)
        url = self.url
        masterkey = self.masterkey
        rest_api_key=self.rest_api_key
        appid=self.appid
        sqlstate=datasql.ConfigurationSql()
        headers = {
                  "X-Parse-Application-Id":f"{appid}",
                  "X-Parse-REST-API-Key": f"{rest_api_key}",
                  "X-Parse-Master-Key": f"{masterkey}",
                  "Content-Type": "application/json"
        }      
        sqlstate=datasql.ConfigurationSql()
        params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({
            "realDate": f"{date}",
            "status":'collected',
            "type":'contribution',
            }),"include":"vehicule,commissionParamExt"})
        myurl=url+'/classes/CppCommissionEvent'
        result=requests.get(myurl,params=params,headers=headers)
        x=result.json()
        amount=0
        values=x['results']
        dasp=date.split('/')
        if not values :
             amount=0
        else :
              for p in values :
                  vehicule=p['vehicule']['numero']
                  amount=float(p['montant'])
                  text=("contribution",'O',str(datedebut),str(vehicule),"N/A",str(amount),str(amount),str(dasp[1]),str(dasp[2]),str(datedebut))
                  sqlstate.insertIncidentJours(database_config,text)
        return  "insertion avec succes!"      
  def getArretInfo(self,database_config,objectId) :
     url = self.url
     masterkey = self.masterkey
     rest_api_key=self.rest_api_key
     appid=self.appid
     sqlstate=datasql.ConfigurationSql()
     headers = {
                  "X-Parse-Application-Id":f"{appid}",
                  "X-Parse-REST-API-Key": f"{rest_api_key}",
                  "X-Parse-Master-Key": f"{masterkey}",
                  "Content-Type": "application/json"
              }
     try :
           params = urllib.parse.urlencode({"limit":1,"where":json.dumps({"objectId":f"{objectId}"})})
           myurl=self.url+'/classes/CppBusArret'
           result=requests.get(myurl,params=params,headers=self.headers)
           x=result.json()    
     except :
           print('error')
  def infoProprio(self,database_config,vehicule,dated,amount):
     try :  
           sqlstate=datasql.ConfigurationSql() 
           sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
           proprio=sqlstate.getInfoProp(vehicule,dated,amount) 
           return proprio
     except :
          print("An exception occurred")
  def infoinfopropriotocore(self,database_config,id,dated):
     
     try :  
           sqlstate=datasql.ConfigurationSql() 
           sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
           proprio=sqlstate.infopropriotocore(id) 
           return proprio
     except :
          print("An excepction occurred")

  def dataProprio(self,database_config,id):
     try :  
           sqlstate=datasql.ConfigurationSql() 
           sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
           proprio=sqlstate.infoproprio(id)
           return proprio
     except :
          print("An exception occurred")
  def getTokenCore(self,basic,url_core):
    try :
        #access_token = token.get('access_token')
        header = {
            "Authorization": "Basic "+basic
        }
        
        response = requests.post(url_core+"/api/oauth/token", json={}, headers=header, timeout=120)
        
        if response.status_code == 200 :
             databear=response.json()
             return databear["access_token"]
        else :
             print(response.text)
    except:
        pass
  def checkServerSeafile(self) :
    # try :
    #    header = {
    #          "accept: */*",
    #          "accept-language: en-US,en;q=0.8",
    #          "content-type:multipart/form-data",
    #     }
    #    url="https://qacseafile.cpp-system.com"
    #    response = requests.get(url+"/api2/ping",params={},headers=header)
       
    #    if response.status_code == 200 :
    #          datajson=response.json()
    #          return (datajson)
    #    else :
    #          return (response.text)
    # except Exception as e:
    #       print(e)
    #       return "" 
    header = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.8",
            "content-type": "multipart/form-data"

        }
    url="https://qafile.cpp-system.com"
    response = requests.get(url+"/api2/ping",headers=header)
       
    if response.status_code == 200 :
          datajson=response.json()
          if(datajson=='pong'):
             return 1
          else :
             return 0
    else :
          print(response)
          return 0
  def getTokenSeafile(self,basic,url) :
    try :
      header = {
            "Authorization": "Basic "+basic
        }
      
      response = requests.post(url+"getpayload", json={}, headers=header, timeout=120)
      if response.status_code == 200 :
             databear=response.json()
             return databear["access_token"]
      else :
             print(response.text)
    except :
        pass
  def deleteFileExist(self,nameFiles,check=0) :
    try :
      basic=config['AUTH_BASIC']
      header = {
            "Authorization":"Token "+basic,
            "accept":"application/json"

        }
      
      
      #repo staging 5a52e40e-7c03-481d-8480-3d7395569d03
      #repo prod 5a52e40e-7c03-481d-8480-3d7395569d03
      parentDir=config['PARENT_DIR']#"Cpp-Transport"
      repo="5a52e40e-7c03-481d-8480-3d7395569d03"
      ser=config['URL_SEAFILE_FILE']
      if check==1 :
         ser=config['URL_SEAFILE_FILE_PRO']
      path=parentDir+'/'+nameFiles+'/'+nameFiles+'.json'
      url=ser+"api2/repos/"+repo+"/file/?p=/"+path
      jsondata={
          "repo-id":repo,
          "p":path
      }
      response = requests.delete(url, json=jsondata, headers=header, timeout=120)
    
      print(response.text)
      sys.stdout.flush()

      if response.status_code == 200 :
             databear=response.json()
             return databear
      if response.status_code == 404 :
           print(response.status_code)
           pass
      else :
             print(response.text)
             pass
    except Exception as e:
        print(e)
        pass
  def createDirectory(self,basicc,url,nameDirectory,parentdir="") :
    try :

      header = {
            "Authorization":"Basic "+basicc,
            "Content-Type":"application/json"
        }
      
      jsondata={
          "parent_dir":parentdir,
          "src":"TRP",
          "idSeafile":nameDirectory,
      } 
      response=requests.post(url+"createDirectory",json=jsondata,headers=header,timeout=1500) 
      
   
      if response.status_code == 200 :
             datac=response.json()
             return datac
      else :
             print(response.text)
    except :
        pass
  def getContenuFiles(self,basicc,url,nameDirectory,src) :
      try :

        header = {
              "Authorization":"Basic "+basicc,
              "Content-Type":"application/json"
          }
        
        jsondata={
            "parent_dir":"",
            "src":src,
            "idSeafile":nameDirectory,
        } 
  
        response=requests.post(url+"getContents",json=jsondata,headers=header,timeout=1500) 
       
   
        if response.status_code == 200 :
              datac=response.json()
              return datac
        else :
              print(response.status_code)
      except :
        print(response.text)
  def sendFileJson(self,basicc,url,nameDirectory,datajson) :
    try :

      header = {
            "Authorization":"Basic "+basicc,
            "Content-Type":"application/json"
        }
      jsondata={
          "parent_dir":"",
          "src":"TRP",
          "idSeafile": nameDirectory,
          "datajson":datajson
      }  
      response = requests.post(url+"createjsonFiles", json=jsondata, headers=header, timeout=1500)
        
      if response.status_code == 200 :
             datac=response.json()
             return datac
      else :
             return(response.text)
    except :
        return (response)
  def sendFile(self,bearer,url,nameDirectory,files1,parentDir="") :
    try :
      new_name1=nameDirectory.replace(' ','')
      n=new_name1.replace('/','')
      header = {
            "Authorization": "Bearer "+bearer
        } 
      params={
        "parent_dir":parentDir,
        "src":"TRP",
        "name":n
      }
      
      with open(files1, "rb") as f:
           files = {"files": f}
    # Send POST request
        # Faire quelque chose avec le contenu du fichier, par exemple, l'afficher
           response = requests.post(
                              url+"upload",
                              files=files,
                              headers=header,
                              data=params,
                              timeout=120,
                          )
      if response.status_code == 200 :
              databear=response.json()
              # print("Upload Image is successfully :  "+databear['message'])
              return databear['message']
      else :
          print(response)
          return "ERROR"
    except Exception as e:
        print(e)
        return ""
  def sendValueCore(self,url_core,data,bearer,database_config,event,year,month):
      #to do 18/2022
      
      if(data['type_payement']=='CSH') :
        dataop="CPP"
      else :
        dataop=data['operateur']
      
      ref=str(uuid.uuid4())
      data1= {
                "source_app"        : "TRP", 
                "date_limit"        : "",
                "account_payee"     : data['phone'],
                "id_ad_payee"       : int(data['idadelya']),
                "psp_name"          : dataop,
                "payment_method"    : data['type_payement'],
                "label"             : "Versement de véhicule "+data['vehicule']+" par CASH",
                "operation_external": ref, 
                "amount"            : data['amount']
      }
      print(data1)
      try :
            
      
            
            header = {
                "Authorization": "Bearer "+bearer
            }
            print(header)
            objectIdDemande=""
            sqlstate=datasql.ConfigurationSql() 
            sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
            
            try :
                 print("########### Demande de versement "+data['vehicule']+" ###############") 
                 response = requests.post(url_core+"/api/demand/versement", json=data1, headers=header, timeout=120)
                 if(response.status_code==200): 
                    objectIdDemande=self.sendVersementParse(data)
                    text=(data['amount'],data['idProp'],str(data['vehicule']),str(data['limit']),month,year,"En attente de traitement",data['type_payement'],data['phone'],"","",data['operateur'],str(data['limit']),ref,"",event,objectIdDemande)
                    #print(text)
                    sqlstate.insertVersementJours(text)
                    print ('Demande de versement avec succes!') 
                 else :
                    print (response.text) 
            except Exception as e:
                print(e)
          
                 
      except Exception as e:
            print(e)
  def sendInfoCore(self,url_core,data,bearer):
      mp={
              "id": "1",
              "payment_type":data["type_paiement"],
              "account_number":data['other_number'],
              "provider":data['nom_operat'],
           }
      data1={
            "id_adelya":data['idAdelya'],
            "id_transport":data['id_prop'],
            "period":data['periodiciteVersement'],
            "default_payment": "1",
            "payments":[mp]
            
            }
      try :
           
            header = {
                "Authorization": "Bearer "+bearer
            }
            
            response = requests.post(url_core+"/api/subscription/transport", json=data1, headers=header, timeout=1500)
            #print(response.status_code)
            if response.status_code == 200 :
                print('Info sent with successfuly!')
            else :
                print('Error 500')
                 
      except:
        pass
  def getInforVehicule(self,objectId) :
    try :
            params = urllib.parse.urlencode({"limit":1,"where":json.dumps({"objectId":f"{objectId}"})})
            myurl=self.url+'/classes/CppTransportVehicule'
            result=requests.get(myurl,params=params,headers=self.headers)
            x=result.json()
            values=x['results']
            print(values)
    except :
      return objectId
  def getListVehicule1(self,database_config) :
    sqlstate=datasql.ConfigurationSql() 
    sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
    vehic=sqlstate.getListVehiculesAll(database_config)
    return (vehic)
  

  def sendVersementParse(self,data) :
        try :
            myurl=self.url+'/classes/CppCommissionEvent'
            params={
                        "montant":str(data["amount"]),
                        "realDate":str(data["limit"]),
                        "type":"Versement",
                        "cppCA":"0",
                        "cashCA":"0",
                        "user":str(data["idProp"])+"_"+data["firstname"],
                        "raison":"Demande de versement manuel (CASH)",
                        "entite":"CPP",
                        "nbTicket":"0",
                        "sourceCA":"cpp",
                        "status":"En cours",
            }
            result=requests.post(myurl,json=params, headers=self.headers, timeout=1500)
            obj=result.json()
            print("Data sent to parse") 
            print(result.status_code) 
            return obj['objectId']
        except :
            print("Data sent to parse") 
            print(result.status_code)     
  
  def getInforTourne(self,objectId,date) :
    try :
            params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({
              "dateStart": {
                    "$gte": f"{date}"+" 00:00:01",
                    "$lte": f"{date}"+" 23:59:59",
                },
              'vehicule': {'__type': 'Pointer', 'className': 'CppTransportVehicule', 'objectId': f"{objectId}"}
            
              })
              })
            myurl=self.url+'/classes/CppEventTournee'
            result=requests.get(myurl,params=params,headers=self.headers)
            x=result.json()
            values=x['results']
            tabtour=[]
            for x in values :
              if x['tourId'] != "FIN DE SERVICE" :
                  tourFirst=x['tourId'].split("_")
                  tabtour.append(int(tourFirst[0]))
      
            return max(list(set(tabtour)))
    except :
      return 0
  def getLastDateExtractionIS(self,cnf) :
    try :
          sqlstate=datasql.ConfigurationSql()
          sqlstate.connect(cnf['url_serve'],cnf['username'],cnf['passwd'],cnf['database'])
        
          datec=sqlstate.getLastDateIs()
          return datec
    except :
      return 0
  def ExtractPointage(self,cnf,date,datef) :
   
    try :
          
          separateDate=date.split('-')
          month=int(separateDate[1])
          year=separateDate[0]
          day=separateDate[2]
       
          sqlstate=datasql.ConfigurationSql()
          sqlstate.connect(cnf['url_serve'],cnf['username'],cnf['passwd'],cnf['database']) 
          params = urllib.parse.urlencode({"limit":1000000,"where": json.dumps({
              "DatePointage": {
                    "$gte": f"{date}"+" 00:00:01",
                    "$lte": f"{datef}"+" 23:59:59",
                },
              }),"include": "IdMember"})
          myurl=self.url+'/classes/CppPartnerPointage'
          result=requests.get(myurl,params=params,headers=self.headers)
          x=result.json()
          values=x['results']
          tabtour=[]
          for x in values :
            separateDateesc=x['DatePointage'].split(' ')
            separatesEvent=separateDateesc[0].split('-')
            month1=str(separatesEvent[1])
            year1=separatesEvent[0]
            day1=separatesEvent[2]
            realDate=str(day1)+"/"+str(month1)+"/"+year1
            valideur=''
            if 'IdValideur' in x :
                valideur=x['IdValideur']['objectId'] 
            if x['IdMember']['type'] in ['chauffeur','receveur'] :
              text=(x['startAt'],month,year,x['status'],x['IdMember']['type'],x['IdMember']['fullName'],x['IdMember']['objectId'],x['endAt'],x['DatePointage'],x['Hourly'],x['idService'],x['reason'],x['objectId'],valideur,realDate)
              sqlstate.getMonthPointage(text)
          return  'Pointage created with successfully!'
    except Exception as e :
         print(e)
         return  'Pointage is not created!'
  def getTaskToken(self) :
    try :
      # return 'tr'
      repo_id=""
      url="https://qafile.cpp-system.com/api/v2.1/repos/"+repo_id+"/zip-task/"
      header = {
                  "Content-Type":"application/json",
                
              }
            
      datajson={
                "parent_dir": "",
                "dirents": ""
            }
          # print(datajson)
      response = requests.post(url+"", json=datajson, headers=header, timeout=120)
       
    except Exception as e :
      print(e)
 
    