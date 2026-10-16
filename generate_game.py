from __future__ import print_function
from main import main
from Configuration import Configuration
from dotenv import dotenv_values
from datetime import date
import sys,json,datetime,shutil,time,requests,urllib,http.client,os,signal,io
import base64
import openpyxl
from openpyxl import Workbook,load_workbook
from datetime import datetime
import time
import mimetypes
import sib_api_v3_sdk

from sib_api_v3_sdk.rest import ApiException

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

class generate_game :
     def run_application_extract(self,datedebut,dateFin):
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
        dateDebut = datedebut+" 00:00:59" 
        dateFin = dateFin+" 23:59:59"
        pb=[]
        data={}
        try : 
          params = urllib.parse.urlencode({"limit":10000000,"where": json.dumps({
                "year":"2023",
                "month":"10",
                "date": {
                    "$gte": f"{dateDebut}",
                    "$lte": f"{dateFin}",
                },
                
            }),"include":"vehicule"})
          myurl=self.url+'/classes/CppTransportEvent'
          result=requests.get(myurl,params=params,headers=self.headers) 
          x=result.json()
          values=x['results']
          # Créer un dictionnaire pour stocker la somme de chaque ticket
          
          for i in range(len(values)):
            if values[i]['type'] in ["CASH","CPP"]:
                if values[i]['transacType'] in ["OK","CASH_COLIS","CASH_SPECIAL","PASS_COLIS","PASS_SPECIAL"]:
                    # print(ticket['date'])
                    # print(ticket['vehicule']['numero'])
                    separateDate=values[i]['ticketNumber'].split('-')
                    try:
                        ticket=separateDate[1]
                    except :
                        ticket=separateDate[0]
                    
                data[i]={"date":str(values[i]['date']),"plaque":str(values[i]['vehicule']['numero'].upper()),"ticketNumber":str(ticket)}   
                pb.append(data[i])
          self.createExcelData(pb)
                       
            # pb.append(data)
            # print(pb)
        except Exception as e:
            print(e)
            return e
     def createExcelData(self,data1) :
        
        workbook = Workbook()
        sheet = workbook.active
        listData=list()
        date_courante = datetime.now()
        date_name=date_courante.strftime("%Y-%m-%d")
        #check file if exist 
        nameFile=str(date_name)+"_tickets_game.xlsx"
        file_path = 'files/'+nameFile  # Replace with the path to your file
       
        if os.path.isfile(file_path):
            workbook1 = openpyxl.load_workbook(file_path)
            
            sheet1 = workbook1.active
            
            for x in data1 :
                data=[[x['date'],x['plaque'],x['ticketNumber']]]
            for row_data in data:
                sheet1.append(row_data)
                workbook1.save(filename=file_path)
        else:
            listData.append(("DATE","PLAQUE","TICKET"))
            try :
                for x in data1 :
                    listData.append((x['date'],x['plaque'],x['ticketNumber']))
                c=tuple(listData)
                temp_file="files/"+date_name+"_tickets_game"+".xlsx"
                real_path = os.path.realpath(temp_file)
                excel_io = io.BytesIO()   
                excel_io.seek(0)
                for row in c:
                    sheet.append(row)
                    workbook.save(temp_file)
            except Exception as e :
                return print(e)
        # self.sendMail(nameFile,str(date_name))
     def sendMail(self,nameFile,date,types,email):
        #api key sending blue
        api_key = config['API_KEY_BREVO']
        # Set the SendinBlue API endpoint for sending an email.
        sendinblue_url =config['URL_SENDINBLUE'] 
        if email == "" :
            email_sends= {"email":"razafimandimbydoun@gmail.com","name":"doun"}
        else :
            email_sends=[{"email":email,"name":"Andry Michel"}]#[{"email":"razafimandimbydoun@gmail.com","name":"doun"}]
      
        #0 game
        #1 Recencements 
      
        if(types==0) :
            nameFile=str(date)+"_tickets_game.xlsx"
            mime_types=".xlsx"
            file_path = 'files/'+nameFile
            sub_message="File Extract Ticket number  : "
            mail_addr=[
                    {"email":"razafimandimbydoun@gmail.com","name":"doun"},
                    {"email":"andry.razafindraibe@cpp-system.com","name":"Andry Michel"}
            ]   
            sub_message="<p>CPP-SYSTEM</p><br/>MANAGER<br/>CPP SYSTEM MADAGASCAR<br/>+261 34 61 931 97/ +261 32 03 138 83<br/><img src='https://qacseafile.cpp-system.com/pictures?xys=Cpp-Transport/test|4DOMxN4bSqWUEB0hhftj.jpg'width='50' height='50'/><br/><p>Bureau N° 3 Immeuble JACARANDA</p><br/><p>Ambatonakanga, 101-ANTANANARIVO</p>"
       
        if(types==1) :
            mime_types=".xlsx"
            # nameFile=str(date)+"_tickets_game.xlsx"
            file_path = os.path.join("FilesRecencement",nameFile)
            # file_path = 'FilesRecencement/'+nameFile    
            sub_message="Recencement le : "
            mail_addr=email_sends
            sub_message="<p>CPP-SYSTEM</p><br/>MANAGER<br/>CPP SYSTEM MADAGASCAR<br/>+261 34 61 931 97/ +261 32 03 138 83<br/><img src='https://qacseafile.cpp-system.com/pictures?xys=Cpp-Transport/test|4DOMxN4bSqWUEB0hhftj.jpg'width='50' height='50'/><br/><p>Bureau N° 3 Immeuble JACARANDA</p><br/><p>Ambatonakanga, 101-ANTANANARIVO</p>"
       
            contentT="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if(types==3) :
            mime_types=".csv"
            file_path = os.path.join(nameFile) 
            sub_message="RAPPORT : "
            # email_sends= {"email":"razafimandimbydoun@gmail.com","name":"doun"}
            mail_addr=email_sends
            sub_message="<p>CPP-SYSTEM</p><br/>MANAGER<br/>CPP SYSTEM MADAGASCAR<br/>+261 34 61 931 97/ +261 32 03 138 83<br/><img src='https://qacseafile.cpp-system.com/pictures?xys=Cpp-Transport/test|4DOMxN4bSqWUEB0hhftj.jpg'width='50' height='50'/><br/><p>Bureau N° 3 Immeuble JACARANDA</p><br/><p>Ambatonakanga, 101-ANTANANARIVO</p>"
       
            contentT="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if(types==2) :
            nameFile=nameFile+".pdf"
            mime_types=".pdf"
            file_path = 'PdfFiles/'+nameFile
            sub_message1="facture mois de"
             #"Facture mois de   : "
            mail_addr=email_sends  
            contentT="application/pdf"
            sub_message="<p>CPP-SYSTEM</p><br/>SALES MANAGER<br/>CPP SYSTEM MADAGASCAR<br/>+261 34 61 931 97/ +261 32 03 138 83<br/><img src='https://qacseafile.cpp-system.com/pictures?xys=Cpp-Transport/test|4DOMxN4bSqWUEB0hhftj.jpg'width='50' height='50'/><br/><p>Bureau N° 3 Immeuble JACARANDA</p><br/><p>Ambatonakanga, 101-ANTANANARIVO</p>"
       
        #config mail 
        mail=mail_addr

        name_sender="Cpp System Madagascar"
         #ou no_replyed@cpp-system.com service.pay@cpp-system.com
        mail_sender="no_replyed@cpp-system.com"
        # Define your email content and recipient information.send data 
      
        # Guess the MIME type of the file
        headers = {
            'api-key': api_key,
            'Content-Type': 'application/json',
        } 
        if(types!=1) :
            with open(file_path, 'rb') as file:
                file_content = file.read()
            file_content_base64 = base64.b64encode(file_content).decode('utf-8')
            email_data = {
            "sender": {"name": name_sender, "email": mail_sender},
            "to": mail,
            "subject": "CPP-SYSTEM",
            "htmlContent":sub_message,
            "attachment": [
                            {
                                        "content": file_content_base64,
                                        "name": nameFile,
                                        "type": contentT
                                    }
                        ]
             }
            response = requests.post(sendinblue_url, headers=headers, json=email_data)
        else :
            # files = {"file": open(file_path, "rb")}   
            # file_content_base64 = base64.b64encode(file_path).decode('utf-8')
            email_data = {
            "sender": {"name": name_sender, "email": mail_sender},
            "to": [{"email": "razafimandimbydoun@gmail.com"}],
            "subject": "RECENCEMENT CPP-SYSTEM",
            "htmlContent":sub_message,
             "attachment": [
                {
                    "name": nameFile,
                    "content": base64.b64encode(open(file_path, "rb").read()).decode("utf-8")
                }
            ]
             
            }
           
            response = requests.post(sendinblue_url, headers=headers, json=email_data)
            sys.stdout.flush()   
        if response.status_code == 201:
            #delete file 
            print("Email sent successfully")
            sys.stdout.flush()
            os.remove(file_path)
        else:
            print(f"Email sending failed with status code: {response.status_code}")
            sys.stdout.flush()
            print(response.json()) 
# gg=generate_game()
# gg.run_application_extract("04/10/2023","11/10/2023")