import base64
import sys
from datetime import date
import json
import datetime
import datasql
import time
from Configuration import Configuration
from dotenv import dotenv_values
from main import main
config = dotenv_values(".env")

# config = dotenv_values("c:/wamp64/www/extract/cpptransportextract/.env")
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

#core config
url_core = config['CORE_DOMAIN_URL_MP']
#key bearer
pri_key_core = config['PRIVATE_KEY_MP']
url_core = config['CORE_DOMAIN_URL_MP']
pub_key_core =config['PUBLIC_KEY_MP']
s=pub_key_core+":"+pri_key_core
datax=base64.b64encode(s.encode('UTF-8')).decode('UTF-8')
sqlstate=datasql.ConfigurationSql()
sqlstate.connect(database_config['url_serve'],database_config['username'],database_config['passwd'],database_config['database'])
      
cnf= Configuration()
cnf.connect(appid,rest_api_key,masterkey,url)
# debutdate=sys.argv[1]
# findate=sys.argv[2]
class Versement:
    def versementPy(self,debutdate,findate):
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

        start = date(year,month,dayd)
        end = date(year1, month1, dayd1)
        value=(end-start).days

        periods = value+1
        daterangeversement = []
        listProp = []
        objEv = []
        objEvsp = ''
        for day in range(periods):
            datep = (start + datetime.timedelta(days = day)).isoformat()
            daterangeversement.append(datep)
        for x in daterangeversement :
            separateDate1=x.split('-')
            month1=(separateDate1[1])
            year1=(separateDate1[0])
            dayd1=(separateDate1[2])
            formatedDate=str(dayd1)+"/"+str(month1)+"/"+str(year1)
            value=cnf.getAllVehicule(formatedDate)
            dateVehicule=list(set(value))
            for y in dateVehicule :
                proprio=sqlstate.getListIdProp(y)
                if proprio!="" : 
                    listProp.append(proprio)
        print(daterangeversement)
        start_time = time.time()
        amount=0
        for propx in list(set(listProp)) :
            vehicu=sqlstate.getListVehiculesProp((3))
            
            for x in vehicu :
                    ca=0
                    comm=0
                    for dt in daterangeversement :
                        separateDate1=dt.split('-')
                        month1=(separateDate1[1])
                        year1=(separateDate1[0])
                        dayd1=(separateDate1[2])
                        formatedDate=str(dayd1)+"/"+str(month1)+"/"+str(year1)
                        ca+=cnf.getCAParBus(formatedDate,x)
                        
                        # ca+=cnf.getRembBus(formatedDate,x)
                        comm+=cnf.getCommissionParBus(formatedDate,x)
                        obj=cnf.getObjectIdEventComm(formatedDate,x)
                        if(obj!='' or obj is not None) :
                            objEv.append(obj)
                            objEvsp+=obj+'|'
                    if(int(ca)>0) :
                        amount=ca-comm
                        if(int(amount)<=0) :
                                pass
                            #check event jours 
                        else :
                            paramProprio=cnf.infoProprio(database_config,x,formatedDate,amount)
                            tokenbear=cnf.getTokenCore(datax,url_core)
                            print(paramProprio)
                            #print('-')
                            #print('--------##----------##-------------')
                            #prop=cnf.sendValueCore(url_core,paramProprio,tokenbear,database_config,objEvsp,year1,month1)
                
        
            return("Versement bien envoyé avec succès! "+"\n--- %s seconds ---" % (time.time() - start_time))
# dateDebut = sys.argv[1]
# dateFin = sys.argv[2]
# data1={
#         "dateDebut":dateDebut,
#         "dateFin":dateFin,
#     }  
 
# v=main()
# p=v.extractDataw(data1)
# v=Versement()
# v.ExtractSupport(dateDebut,dateFin)

# dateDebut = sys.argv[1]
# dateFin = sys.argv[2]
# data1={
#         "dateDebut":dateDebut,
#         "dateFin":dateFin,
#     }  
# # print(data1)  
# p=v.extractDataw(data1)
# p=cnf.getVehiculeAll(database_config)
# for x in p :   
#cnf.getAllVehicule("16/01/2023")#getCommissionParExtract(database_config,"2022-11-01","2022-11-30",x)
# dateDebut = sys.argv[1]
# dateFin = sys.argv[2]
# separateDate=dateDebut.split('-')
# month=int(separateDate[1])
# year=int(separateDate[0])
# dayd=int(separateDate[2])
# separateDate1=dateFin.split('-')
# month1=int(separateDate1[1])
# year1=int(separateDate1[0])
# dayd1=int(separateDate1[2])
# start = date(year,month,dayd)
# end = date(year1, month1, dayd1)
# value=(end-start).days
# periods = value+1
# daterangeversement = []
# for day in range(periods):
#         datep = (start + datetime.timedelta(days = day)).isoformat()
#         daterangeversement.append(datep)
# # 

# for x in daterangeversement :
#     separateDate1=x.split('-')
#     month1=(separateDate1[1])
#     year1=(separateDate1[0])
#     dayd1=(separateDate1[2])
#     formatedDate=str(dayd1)+"/"+str(month1)+"/"+str(year1)
#     cnf.SoldeVersement(formatedDate)
# cnf.ExtractSupport(dateDebut,dateFin) 
