import sys
import time
from Configuration import Configuration
from urllib import response
import urllib
import uuid
#import requests
import urllib.parse
import datetime
from datetime import date
import requests
import json
from CppEsper import CppEsper
from dotenv import dotenv_values
class main :
  def extractDataw(self,datex) :
            separateDate=str(datex['dateDebut']).split('-')
            month1=int(separateDate[1])
            month3=str(separateDate[1])
            year1=separateDate[0]
            dayd1=separateDate[2]
            datebegin=str(dayd1)+"/"+str(month3)+"/"+str(year1) 
            separateDate1=str(datex['dateFin']).split('-')
            month2=int(separateDate1[1])
            month4=str(separateDate1[1])
            year2=separateDate1[0]
            dayd2=separateDate1[2]
            datefend=str(dayd2)+"/"+str(month4)+"/"+str(year2)
           
            config = dotenv_values(".env")
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
            cnf= Configuration()
            cnf.connect(appid,rest_api_key,masterkey,url)
            datebeg= str(datebegin)+" 00:00:00"
            dateend= str(datefend)+" 23:59:00"
            separateDate2=datebegin.split('/')
            month=int(separateDate2[1])
            year=separateDate2[2]
            start_time = time.time()
      
            # p=cnf.getEven(datebeg,dateend,database_config,month,year)
            p=cnf.getEventTournee(datebeg,dateend,database_config,month,year)
            # print(p)
            # return (p+"\n--- %s seconds ---")
            return "Event created with sucesfully!"

# esp=CppEsper()
# esp.getGroup('KOFIAMA')
# dateb="03/11/2022"
# separateDate=dateb.split('/')
# supportIncidents=[]
# url = "https://bus.cpp-system.com/api/"
# masterkey = ">UZ6Fdu>Up:xwNMQ"
# rest_api_key="{h)P>3x^{QN=7Ks("
# headers = {
#             "X-Parse-Application-Id": "CPP_BUS_PROD",
#             "X-Parse-REST-API-Key": "{h)P>3x^{QN=7Ks(",
#             "X-Parse-Master-Key": ">UZ6Fdu>Up:xwNMQ",
#             "Content-Type": "application/json"
#         }
# try :  
#     datedebut=dateb+" 00:00:00"
#     dateend=dateb+" 23:59:00"
#     params = urllib.parse.urlencode({"limit":10000,"where": json.dumps({
#     "date": {
#                         "$gte": f"{datedebut}",
#                         "$lte": f"{dateend}",
#                   }
#                   }),"include":"type"})
#     myurl=url+'/classes/CppTransportIncident'
#     result=requests.get(myurl,params=params,headers=headers)
#     x=result.json()
#     values=x['results']
#     for x in values :
#       supportIncidents.append(x['objectId'])
#     print (list(set(supportIncidents)))
# except :
#     print('error')

# start = date(2022, 10, 1)
# end = date(2022, 10, 25)
# value=(end-start).days

# periods = value+1
# daterange = []
# for day in range(periods):
#    date = (start + datetime.timedelta(days = day)).isoformat()
#    daterange.append(date)
# print(daterange)