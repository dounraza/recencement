import sys
import time
from Configuration import Configuration
from dotenv import dotenv_values

  
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
cnf= Configuration()
cnf.connect(appid,rest_api_key,masterkey,url)
#datebeg= str(sys.argv[1])+" 00:00:00"
##dateend= str(sys.argv[2])+" 23:59:0#0"
#separateDate=sys.argv[1].split('/')#
#month=int(separateDate[1])
#year=separateDate[2]
#start_time = time.time()
#cnf.getEvent(datebeg,dateend,database_config,month,year)
arret=cnf.getArretLists(database_config)
print(arret)
#print("--- %s seconds ---" % (time.time() - start_time))