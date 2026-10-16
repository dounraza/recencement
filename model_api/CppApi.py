from flask import Flask, jsonify, send_file,request,Response,render_template
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity,get_jwt
import json
from datetime import timedelta,datetime,date
from cryptography.fernet import Fernet
import os,signal,io
app = Flask(__name__)

api = Api(app)
jwt = JWTManager(app)
import base64
import pdfkit
import requests
from dotenv import dotenv_values
import calendar
import random
from urllib import response
import urllib
import sys
import model_api.CppApi
from urllib.parse import unquote
from Configuration import Configuration
from concurrent.futures import ThreadPoolExecutor, as_completed
# import logging

# # Configuration du fichier journal
# logging.basicConfig(filename='cppsystem.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from generate_game import generate_game


config_env = dotenv_values(".env")

# config_env = dotenv_values("c:/wamp64/www/extract/cpptransportextract/.env")
cnf= Configuration()
datax=config_env['TOKEN_SEAFILE']
urlseafile=config_env['URL_SEAFILE']
# Set the secret key for encoding the JWT
# app.config['JWT_SECRET_KEY'] = 'xyszakal'  # Change this in a production environment!

# Set the expiration time for tokens (e.g., 15 minutes)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] =timedelta(seconds=120)
# Example user data (in a real application, you would have a user database)
users = {
    'PAY': {
        'password': 'YoIl78n>Hj0(',
        'email': 'pay@cpp-system.com'
     }
}
@jwt_required()
def checkToken() :
    try :
        
        current_user = get_jwt_identity()
        if current_user:
            raw_jwt = get_jwt()
            exp=raw_jwt['exp']
            current_utc_time = datetime.utcnow()
            expiration_time = datetime.utcfromtimestamp(exp)
                # Handle expiration as needed
            if expiration_time < datetime.utcnow():
                print(json.dumps({'fdsd': 'Token has expired'}, indent=2), 401)
                return False
            else :
                value={"logged_in_as":current_user, "message":"OK"}
                json_data = json.dumps(value, indent=2)
                response = Response(json_data, status=200, content_type='application/json')
                print(response)
                return True
        else:
            valueerror={'message': 'No valid token provided'}
            json_data = json.dumps(valueerror, indent=2)
            response = Response(json_data, status=410, content_type='application/json')
            print(response)
            return False
        
    except Exception as e:
        valueerror={'message': e}
        json_data = json.dumps(valueerror, indent=2)
        response = Response(json_data, status=410, content_type='application/json')
        print(response)
        return False
        # return json.dumps({'message': e}), 401
    
# Resource for user login and token generation
class LoginResource(Resource):
    def post(self):
        header=request.headers.get('Authorization').split(" ")
        try :
        
           
            key_secret=config_env['KEY_SECRET_CYPHER'] #key
            if(header[0]=="Basic") :
                value={header[1]}
                response = Response(value, status=403, content_type='application/json')
               
                encMessage=header[1]
                fernet = Fernet(key_secret)
                decMessage = fernet.decrypt(encMessage).decode()
                text_to_encode =decMessage # "YoIl78n>Hj0(:PAY"
                
                # Check if the provided username and password are valid
                text=text_to_encode.split(':')
            
                username=text[1]
                if username in users and users[username]['password'] == text[0]:
                # Create a JWT token
                    access_token = create_access_token(identity=username, expires_delta=app.config['JWT_ACCESS_TOKEN_EXPIRES'])
                    value={
                            "error":False,
                            "access_token": access_token,
                            "validity": 120
                        }
                    json_data = json.dumps(value, indent=2)
            
                    # Create a Flask Response with the JSON data and a custom status code
                    response = Response(json_data, status=200, content_type='application/json')
        
        
                    return response
                else:
                    value={'Invalid credentials'}
                    json_data = json.dumps(value, indent=2)
                    response = Response(json_data, status=410, content_type='application/json')
                    return response
            else :
                value={"Message : Error Authorization" }
                    
                response = Response(value, status=401, content_type='application/json')
                return response
        except Exception as e :
            value={e}
            response = Response(value, status=403, content_type='application/json')
            return response
    
        
           

# Protected resource that requires a valid JWT token
class ProtectedResource(Resource):
    def get(self):
        # Access the identity of the current user with get_jwt_identity
        ch=checkToken()
        if(ch==True) :
            return "ca va marcher"
        else :
            return ch
class InvoiceCpp(Resource):
    def post(self):
        # Access the identity of the current user with get_jwt_identity
        ch=checkToken()
        if(ch==True) :
            data = request.get_json()
            template = data.get('template')
            src = data.get('src')
            datac = data.get('data')
            if(template=='rap') :
                data_ret=route_download(datac,template)
                return data_ret
            if(template=='releve'):
                #Call releve post payement
                data_ret=route_download(datac,template)
                return data_ret
                print('To Do')
            if(template=='facture'):
                data_ret=route_download(datac,template)
              
                return data_ret
                #Call facture post payement
                 
        else :
            return ch   
class GetaDataPay(Resource) :
    def post(self):
        ch=checkToken()
        data=request.get_json()
        # return extractDataPay(data)#data.get('month')
        # extractDataPay()
        # if(ch==True) :
            
        
def route_download(data,template,val=""):
    if(template=="rap") :
        rendered_html=create_releve(data,template)
    if(template=="releve") :
        rendered_html=create_releve(data,template)
    if(template=="facture") :
        rendered_html=create_releve(data,template,val)

    # Get the HTML output
    # input_html_path = os.path.join("templates/templates_pdf/export.html") #render_template("templates_pdf/export.html")
    
        # Build PDF from HTML 
        # pdf = pdfkit.from_string(out, options=options)
        
        # chemin = os.path.join("SeafileTemp","testpdf")
        # pdf.save(chemin)
        # Download the PDF
    return rendered_html
        # return Response(pdf, mimetype="application/pdf")     
def pay_cpp(data_post):
    
    from datetime import datetime

    # Obtenir la date actuelle
    now = datetime.now()

    # Extraire le mois et l'année
    current_month = now.month
    current_year = now.year
   
    if request.method == 'POST':
        #data company et partner
        company=data_post['company']
        partner=data_post['partner']
        id_transactions=data_post['transaction_id']
        month=int(data_post['month'])
        year=int(data_post['year'])
    elif request.method == 'GET':
        #data company et partner
        company="7qXmlUm1EE"
        partner="liwlKgNjkE"
        month=4#int(current_month)
        year=int(current_year)
    
    try :
        type_trs="TRANSACTION"
        url = config_env['PARSE_URL_PAY']
        appid = config_env['PARSE_APP_ID_PAY']
        masterkey = config_env['PARSE_MASTER_KEY_PAY']
        rest_api_key=config_env['PARSE_API_REST_KEY_PAY']
        headers = {
            "X-Parse-Application-Id": f'{appid}',
            "X-Parse-REST-API-Key":  f'{rest_api_key}',
            "X-Parse-Master-Key":  f'{masterkey}',
            "Content-Type": "application/json"
        }
        if id_transactions:
            if "" in id_transactions:
                value_data={
                    "month":int(month),
                    "year":int(year),
                    "company": {'__type': 'Pointer', 'className': 'Company', 'objectId': company},
                    "partner": {'__type': 'Pointer', 'className': 'CompanyCustomer', 'objectId':partner},
                    "type":type_trs
                }
                return  value_data
            else :
                value_data={
                        "month":int(month),
                        "year":int(year),
                        "company": {'__type': 'Pointer', 'className': 'Company', 'objectId': company},
                        "partner": {'__type': 'Pointer', 'className': 'CompanyCustomer', 'objectId':partner},
                        "type":type_trs,
                        "transaction":{"$in":id_transactions}
                }
                # return  value_data   
        params = urllib.parse.urlencode({"limit":100000,"where": json.dumps(value_data),"include":"company,customer,partner.customer,transaction,transaction.status"})
        myurl=url+'/classes/PartnerEvent'
        result=requests.get(myurl,params=params,headers=headers)
          # print("Status : "+str(result.status_code))
        x=result.json()
        data=[]  
        values=x['results']
       
        p=0
        numbill = random.randint(0, 10000)   
        from datetime import date
        date_emis = date.today()
        status="Payé"
        id_partner=""
        amountTotal=0
        if values :
            for x in values :
                    #info Partenaire
                    if 'partner' not in x :
                        data = {
                                'succes': False,
                                'message': "Partenaire not Found",
                            }
                        return data, 404
                    if 'company' not in x :
                        data = {
                                'succes': False,
                                'message': "Company not Found",
                            }
                        return data, 404
                    if 'transaction' not in x :
                        data = {
                                'succes': False,
                                'message': "Transaction not Found",
                            }
                        return data, 404
                    adrress_part=x.get('partner', {}).get('customer', {}).get('address') if 'partner' in x and 'customer' in x['partner'] else None 
                    email_part=x.get('partner', {}).get('customer', {}).get('email') if 'partner' in x and 'customer' in x['partner'] else None 
                    phone_part=x.get('partner', {}).get('customer', {}).get('phone') if 'partner' in x and 'customer' in x['partner'] else None 
                    repres_name=x['company']['name']
                    logo=x['company']['logo'] if x.get('company') and x['company'].get('logo') is not None else ''
                    phone_company=x['company']['phone']
                    email_company=x['company']['email']
                    address=x['company']['address'] 
                    #info Company
                    data_v={
                        #info Comp
                        "name":repres_name ,
                        "logo":logo ,
                        "phone":phone_company,
                        "address":address,
                        "email":email_company ,
                        #info Part
                        "name_partner":x['partner']['customer']['firstname'] ,
                        "address_part":adrress_part if adrress_part else "-",
                        "email_partner":email_part if email_part else "-",
                        "phone_partner":phone_part if phone_part else "-",
                        #transaca
                        "amount_initial":x['transaction']['amount_initial'] ,
                        "month":x['month'] ,
                        "year":x['year'] ,
                        "numbill":numbill ,
                        "status":x['transaction']['status']['name']
                        
                    }
                    
                    data.append(data_v)
                    p+=1
                    # # Begin info company
                   
                    # #  End info company
                    # # TO DO Begin info partner

                    repres_name_partner=x['partner']['customer']['firstname'] 
                    address_part=adrress_part if adrress_part else "-"    
                    phone_partner=phone_part if phone_part else "-"
                    email_partner=email_part if email_part else "-"
                
                    #   End info partner
                    amount=int(x['transaction']['amount_initial']) 
                    amountTotal=amountTotal+amount
                    month=x['month']
                    year=x['year']
                    tva=0
                    partiel=1  #1 if true ,if false  mensuel
                    sum_ttc=0
                    types=x['type']
            
                    num_bill=str(numbill)
                    
                    total_operation=p
                    ref="CPP-FACT-TRS-"+str(month)+str(year)+"-"+str(num_bill)
                    label="POST PAY pour les "+str(x['type'])+"  mois de"     
                    if(str(x['type'])=="COMMISSION"):
                        ref="CPP-FACT-COMM-"+str(month)+str(year)+"-"+str(num_bill) 
            data_pay_transac={
                                "objectIdCore":x['objectId'],
                                "amount":amountTotal,
                                "company":x['company']['objectId'],
                                "repres_name_partner":x['partner']['customer']['firstname'] ,
                                "phone_partner":phone_partner ,
                                "email_partner":email_partner,
                                "month":int(month),
                                "year":int(year)
                    }  
          
            objectId=model_api.CppApi.create_transact_payre(data_pay_transac)  
            ref_ident="ref_test"
            if(objectId != "#|#"):
                components = objectId.split('|')
                ref_ident=components[1]
            # rendered_html = render_template('templates_pdf/facture.html',partiel=partiel,label=label,record=values,amountTotal=amountTotal,url_image=logo,date_emis=date_emis,total_operation=total_operation,company=repres_name,phone_company=phone_company,email_company=email_company,status=status,tva=tva,sum_ttc=sum_ttc,amount=amount,partner=id_partner,partner_name=repres_name_partner,partner_phone=phone_partner,partner_email=email_partner,ref=ref,month=month,year=year)   
            rendered_html = render_template(
                    'templates_pdf/facture.html',
                    partiel=partiel,
                    label=label,
                    sum_ttc=str(amount),
                    record=values,
                    components=ref_ident,
                    amountTotal=amountTotal,
                    url_image=logo,
                    date_emis=date_emis,
                    total_operation=total_operation,
                    company=repres_name,
                    phone_company=phone_company,
                    email_company=email_company,
                    adress_part=address_part,
                    status=status,
                    tva=tva,
                    amount=amount,
                    partner=id_partner,
                    partner_name=repres_name_partner,
                    partner_phone=phone_partner,
                    partner_email=email_partner,
                    ref=ref,
                    month=month,
                    year=year
            )
            rendered=generate_pdf(rendered_html,year,month,num_bill)
            return rendered
        else :
            data = {
                    'succes': False,
                    'message': "Data  is empty",
                }
            return data, 400 
    except Exception as e :
        # print(e)
        data = {
                    'succes': False,
                    'message':e.__traceback__,
        }
        return (data)
def create_releve(data,template,val="") :
   
    # 
    random_number = random.randint(0, 9999)
    # # Convert the number to a string and fill with leading zeros
    num = str(random_number).zfill(4)
        #date 
    year=str(data['year'])

    month=str(data['month'])
    if (template=="rap"):
        #CPP system
        url_logo="https://qacseafile.cpp-system.com/pictures?xys=Cpp-Transport/test|4DOMxN4bSqWUEB0hhftj.jpg"
        current_date = datetime.now()
        date = current_date.strftime("%d/%m/%Y")
        #info prepose
        name=data['name']
        cooperative= data['cooperative']
        #generate 
      
        try :
            values1 = json.loads(data['data'])
        except Exception as e :
            values1=data['data']

        # Obtenez le nombre de jours dans le mois actuel
        days_in_month = calendar.monthrange(int(data['year']), int(data['month']))[1]
        #ref  dfdfd
        
        # Generate a random integer between 1 and 100
        num = random.randint(0, 10000)
        #calcule selon mois 
        periode="01/"+month+"/"+year+"   "+str(days_in_month)+"/"+month+"/"+year
        if(template=="rap") :
            import copy
            ref="CPP-RAP-"+str(month)+str(year)+str(num)
            record=[]
            designt=["Salaire de base total","Prime d'activité","Prime Pub","Total Salaire","Avance","Reste à payer","Panier repas théorique","Panier repas declarer","Revenu","Cotisation"]
            designation=[]
            #get values 
            # values1=json.loads(data['data'])
            for x in values1:
                # values = values1.get(x, {}).copy()
                # record.append(values)
                value = values1.get(x)
                if isinstance(value, dict):  # Check if the value is a dictionary
                    values = value.copy()  # Make a copy if it's a dictionary
                    record.append(values)
            salaire=data['salaire']
            totalsalaire=0
            #data money
            currency=" Ariary"
            #calcule
            sb=str('{:,}'.format(data['sb'])) +currency
            sbj=data['sb']
            njt=data['njt']
            for desing in designt:
                amount=0
                if(desing=="Salaire de base total"):
                    amount=njt*sbj
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                if(desing=="Prime d'activité"):
                    amount=data['totalprime']
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                if(desing=="Prime Pub"):
                    amount=data['totalprimepub']
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                if(desing=="Avance"):
                    amount=0
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                #TO DO :AVANCE,RESTE PAYER ,
                if(desing=="Reste à payer"):
                    amount=0
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                if(desing=="Panier repas"):
                    amount=0
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                if(desing=="Panier repas declarer"):
                    amount=0
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                if(desing=="Revenu"):
                    amount=0
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                if(desing=="Cotisation"):
                    amount=0
                    values1={
                        "designation": desing,
                        "amount":amount,
                    }
                    designation.append(values1)
                if(desing=="Total Salaire"):
                    
                    values1={
                        "designation": desing,
                        "amount":totalsalaire,
                    }
                    designation.append(values1)
                totalsalaire+=amount
            fonction=data['role']
            rendered_html = render_template('templates_pdf/export.html',url_image=url_logo, name=name,sb=sb,njt=njt,salaire=salaire,cooperative=cooperative,fonction=fonction,ref=ref,record=record,designation=designation,periode=periode,date=date,year=year)
           
            rendered=generate_pdf(rendered_html,year,month,num)
            return rendered
    if(template=="releve") :
        #generer le releve a du company pour chaque partenaire 
        #get info Company
        name="JUMBO-ANALAKELY"
        url_logo="https://qacseafile.cpp-system.com/pictures?xys=Cpp-pub/test|R8EfB9Gz7lDAApKX13GS.png"
        #get info partner
        partner="ORANGE"#partner
        date=month+"/"+year
        #generate ref
        ref="CPP-RAS-"+month+year+num   
        #get Methode de payement 
        mpt="POST-PAYMENT"
        #get status of the payement 
        status="En cours"
        #get data du  company pour chaque partenaire ou  all 
        record=[]
        # values1=json.loads(data['data'])

        rendered_html = render_template('templates_pdf/releve_pay.html',url_image=url_logo, company=name,status=status,mpt=mpt,partner=partner,ref=ref,record=record,date=date,year=year)
        rendered=generate_pdf(rendered_html,year,month)
        return rendered
    if(template=="facture") :
        try :

            data_post={
                "company":data['company'],
                "partner":data['idPartenaire'],
                "transaction_id":data['transaction_id'],
                "month":str(month),
                "year":str(year)
            }
            rendered=pay_cpp(data_post)
            # from datetime import date
            # date_emis = date.today()
            #     #get data  if commission  or  post pay 
            # url_logo="https://qacseafile.cpp-system.com/pictures?xys=Cpp-pub/test|R8EfB9Gz7lDAApKX13GS.png"
            # values=getCppPayConfigBill(data,val)
            # print('nen')
            # sys.stdout.flush()
            # for x in  values :
            #     tva=x['tva']
            #     partiel=int(x['partiel'])  #1 if true ,if false  mensuel
            #     sum_ttc=x['sum_ttc']
            #     types=x['type']
            #     amount=x['total']
            #     repres_name=x['repres_name']
            #     logo=x['logo']
            #     id_partner=x['id_partner']
            #     month=x['month']
            #     year=x['year']
            #     amountTotal=x['amountTotal']
            #     phone_company=x['phone_company']
            #     email_company=x['email_company']
            #     phone_partner=x['phone_partner']
            #     email_partner=x['email_partner']
            #     num_bill=str(x['num_bill'])
            #     status=str(x['status'])
            #     total_operation=x["total_operation"]
            #     ref="CPP-FACT-TRS"+str(month)+str(year)+str(num_bill)
            #     label="POST PAY pour les "+str(x['type'])+"  mois de"     
            #     if(str(x['type'])=="COMMISSION"):
            #         ref="CPP-FACT-COMM"+str(month)+str(year)+str(num_bill)
            
            
            # rendered_html = render_template('templates_pdf/facture.html',partiel=partiel,label=label,record=values,amountTotal=amountTotal,url_image=logo,date_emis=date_emis,total_operation=total_operation,company=repres_name,phone_company=phone_company,email_company=email_company,status=status,tva=tva,sum_ttc=sum_ttc,amount=amount,partner=id_partner,partner_phone=phone_partner,partner_email=email_partner,ref=ref,month=month,year=year)
                
            # rendered=generate_pdf(rendered_html,year,month,num_bill)

            return rendered
        except Exception as e :
            print(e)
            data = {
                    'succes': False,
                    'message': "Une erreur est survenue",
            }
            return data, 400 
def generate_pdf(render,year,month,num_bill) :
    import traceback
    try :
        path_wkhtmltopdf=config_env['WKHTMLTOPDF_SRC']

        # PDF options
        options = {
            'quiet': False,
            "orientation": "portrait",
            "page-size": "A4",
            "margin-top": "1.0cm",
            "margin-right": "1.0cm",
            "margin-bottom": "1.0cm",
            "margin-left": "1.0cm",
            "encoding": "UTF-8",
            "enable-local-file-access": "",
        }
        nameDirectory='File_cpp_pdf'
        if num_bill == "" :
            num=random.randint(0, 9999)
        else :
            num=num_bill
        name_fact=str(year)+"_"+str(month)+"_"+str(num)
        nameFile=str(name_fact)+'.pdf'
       
        # nameFile='test2.pdf'
        output_pdf_path = os.path.join("PdfFiles",nameFile)
        # Configuration de pdfkit
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        #23.2 -> 24.2

        pdfkit.from_string(render, output_pdf_path,options=options, configuration=config)
        datax=config_env['TOKEN_SEAFILE']
        urlseafile=config_env['URL_SEAFILE']
        token=cnf.getTokenSeafile(datax, urlseafile)
      
        namefilesup=cnf.sendFile(token, urlseafile,nameDirectory,output_pdf_path,"")
        # os.remove(nameFilex)
        # formatted_url = unquote(namefilesup)
        response_data = {
        'message':namefilesup,
        'succes': True
         } 
        return jsonify(response_data) 
    except Exception as e:
        error_message = traceback.format_exc()
        print(error_message)
        response_data = {
        'url_files':error_message,
        'succes': False
         } 
        return jsonify(response_data) 


def extractDataPay(data):
   print('##### Extract Data Post PAYMENT #####')
   try :
        #get Company  PAY 
        liste_de_magasins=getDataMerchant(data)       
        # liste_de_magasins1=[{'objectid': '7qXmlUm1EE', 'name': 'MITIA', 'repres_name': 'Mitia', 'email': 'tiavina.mirana@yopmail.com', 'phone': '0349327673', 'idAdelya': 31612, 'month': 12,'year': 2023}]
        with ThreadPoolExecutor() as executor:
            # num_processes = executor._max_workers
            executor.map(EventPay,liste_de_magasins)
            print("### End Extraction #####")
            return {
                "code":200,
                "nombre_processus":0,#num_processes,
                "msg":"success",
            }
   except Exception as e :
       print(e)
       return e 

#get Company
def getDataMerchant(data) :
    month=int(data['month'])
    year=int(data['year'])
    #TO Do : if exist id company get 
    url=config_env['PARSE_URL_PAY']
    headers={
                        "X-Parse-Application-Id":config_env['PARSE_APP_ID_PAY'],
                        "X-Parse-REST-API-Key":config_env['PARSE_API_REST_KEY_PAY'],
                        "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_PAY'],
                        "Content-Type": "application/json"
                    
            }
    url_get=url+'classes/Company'
   
    status="wyyamTxgzs"
    params = urllib.parse.urlencode({"limit":100000,"where": json.dumps({
              "id_adelya": {"$ne": ""},
              'status': {'__type': 'Pointer', 'className': 'Status', 'objectId': f"{status}"}
              })
              })#,"include": "partner,company,transaction,customer"
    result=requests.get(url_get,params=params,headers=headers)
    x=result.json()
    get_merchant=x['results']
    data_merchant=[]
    for xc in get_merchant :
        if "id_adelya" in xc :
            values={
                "objectid":xc["objectId"],
                "name":xc["name"],
                "repres_name":xc["representant_name"],
                "email":xc["email"],
                "phone":xc["phone"],
                "idAdelya":xc["id_adelya"],
                "month":month,
                "year":year,
            }
            data_merchant.append(values)
 
    return data_merchant

    # except Exception as e :
    #     print (e)
def EventPay(data):
    month=data['month']
    year=data['year']
    types="TRANSACTION"
    url=config_env['PARSE_URL_PAY']
    appid = config_env['PARSE_APP_ID_PAY']
    masterkey = config_env['PARSE_MASTER_KEY_PAY']
    rest_api_key=config_env['PARSE_API_REST_KEY_PAY']
    headers = {
                  "X-Parse-Application-Id":f"{appid}",
                  "X-Parse-REST-API-Key": f"{rest_api_key}",
                  "X-Parse-Master-Key": f"{masterkey}",
                  "Content-Type": "application/json"
              }
    #if post event
    
    try :
        typestrans="R4jHT7BuZK" #type trans post payment R4jHT7BuZK
        params = urllib.parse.urlencode({"limit":10,"where": json.dumps({
                "year":int(year),
                "month":int(month),
                "type":types,
                "company": {'__type': 'Pointer', 'className': 'Company', 'objectId': f"{data['objectid']}"},
                "payement_mean": {'__type': 'Pointer', 'className': 'CppPaymentMean', 'objectId': f"{typestrans}"}
                }),"include": "partner,company,transaction"})#customer
        myurl=url+'classes/PartnerEvent'
       
        result=requests.get(myurl,params=params,headers=headers)
        x=result.json()
        values=x['results']
        if(len(values)>0) :
       
            data1=[]
            detailsTransact=[]
            var_commission=0
            amount_commission=0
            total_montant=0
            periode="J+30",
            num=random.randint(0, 9999)
            ref_fact="FACT-CPP-"+str(year)+"_"+str(month)+"_"+str(num)
            ref_pmt=""
            pmt_meth=""#MM , BNK
            psp_name=""# TLM,ORG,ART,BNI,BOA,BMOI,MCB
            numero_mm="" #numero mobile money
            rib="" #numero mobile money
            email="#"
            record={}
            transcation='TRANSACTION'
            if data['email'] is not None :
                email=data['email'] 
            for value in values :  
                #get Commission var total
                var_commission+=float(value['transaction']['commission_var'])      
                amount_commission+=float(value['transaction']['amount_commission'])
                total_montant+=float(value['transaction']['amount_initial'])
                        #get amount_commission
                        #sum  amount total 
                        #{ref et montant ,card ,type ,comment,id client et name client,date,objectId Transac}
                company=value['company']['objectId'] 
                id_adelya=value['company']['id_adelya'] 
                partner=value['partner']['company']["objectId"]
                logo = value['company']['logo'] if 'company' in value and 'logo' in value['company'] else ""
                val={
                            "reference":value['transaction']['reference_paiement'],
                            "amount":value['transaction']['amount_initial'],
                            "type":value['transaction']['type'],
                            "motif":value['transaction']['motif'],
                            "id_client":value['transaction']['objects']['Client']['objectId'],
                            "card":value['transaction']['objects']['Client']['cardnumber'],   
                            "commission_var":value['transaction']['commission_var'],
                            "amount_commission":value['transaction']['amount_commission'],
                            "transaction_id":value['transaction']['objectId'],
                    }
                detailsTransact.append(val)
            record={
                            "src":"CPP-PAY",
                            "type":transcation,
                            "company_pay":company,
                            "id_adelya_company":int(id_adelya),
                            "id_partner":partner, #orange
                            "logo":logo,
                            "month":int(month),
                            "year":int(year),
                            "total":total_montant,
                            "total_commission":amount_commission,
                            "total_commission_var":var_commission,
                            "status":0,
                            "periode_paiement":"j+30",
                            "date_payement":"date+30",
                            "args":json.dumps(detailsTransact),
                            "ref_facture":ref_fact,
                            "ref_paiement":ref_pmt,
                            "payment_method": pmt_meth,#MM , BNK
                            "id_external_transac": "Null",#MM , BNK
                            "psp_name": psp_name,# TLM,ORG,ART,BNI,BOA,BMOI,MCB
                            "cc1":numero_mm, #numero mobile money
                            "cc2":rib, #numero rib
                            "cc3":"", #other
                            "cc4":"", #null if type transaction and value id if commission
                            "sended":False, #send to company
                            "url_invoice":"", #url
                            "email":"razafimandimbydoun@gmail.com",#email,
                            "num_bill":str(num), #numero
                }
            data1.append(record)
            if data1 is not None :
                return  sendValueToCore(data1,"")
    except Exception as e :
        print(e)
        return e
   
def sendValueToCore(data2,types) :
    url=config_env['PARSE_BASE_URL_CORE']
    if(types=="") :
        types="TRANSACTION"
   #check if exist month and year and company and partner and amount
    headers={
                            "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                            "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                            "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                            "Content-Type": "application/json"
                        
            }
    store_url=url+'/endpoint/classes/CppPayBilling'
    try :
            try : 
                data1=data2[0]
            except :
                data1=data2
            print("store billing")
            store_billing=requests.post(store_url,json=data1,headers=headers, timeout=120)
            print(store_billing)
            #1-schedule create ligne transaction, type FAC
            # create_transact_pay(data1)
            #update batch 
            #2-update transaction fils par objectId  transaction (1) et  batch core
            #3-generate facture de comm et transact

            # datac={
            #     "company":data1['company_pay'],
            #     "idAdelyaCompany":data1['id_adelya_company'],
            #     "idPartenaire":data1['id_partner'],
            #     "year":data1['year'],
            #     "month":data1['month']     
            # }
            # create_releve(datac,"facture")
            if(store_billing.status_code==201):
                return  "Success"
            else :
                print(store_billing.text)
                return {
                        "msg":store_billing.text,
                        "status":store_billing.status_code
                 }
    except  Exception as e :
            print(e)
            return  e
            
def getCppPayConfigBill(data,val="") :
    
    month=int(data['month'])
    year=int(data['year'])
    company=data['company']
    
    # if val !="" :
    #     id_transactions=val 
    # else :
    id_transactions=data['transaction_id']
    idPartenaire=data['idPartenaire']

    #TO Do : if exist id company get 
    url=config_env['PARSE_BASE_URL_CORE']
   
    if(len(id_transactions)>0) :
        numbill = random.randint(0, 10000)      
        print('retrieve the specified transaction')
        sys.stdout.flush()
        headers={
                                "X-Parse-Application-Id":config_env['PARSE_APP_ID_PAY'],
                                "X-Parse-REST-API-Key":config_env['PARSE_API_REST_KEY_PAY'],
                                "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_PAY'],
                                "Content-Type": "application/json"
                            
                }
        url_pay=config_env["PARSE_HOST_PAY"]
        url_get=url_pay+'/endpoint/classes/Transaction'
        params = urllib.parse.urlencode({"limit":100000,"where": json.dumps({
                "objectId":{"$in":id_transactions}
                })
                ,"include": "company,status"})
       
        result=requests.get(url_get,params=params,headers=headers)
      
        x=result.json()
        get_data=x['results']
        data_merchant=[]
        amount=0
        url_logo="https://qacseafile.cpp-system.com/pictures?xys=Cpp-pub/test|R8EfB9Gz7lDAApKX13GS.png"
        amountTotal=0
        try :
            if  get_data:
                for xc in get_data :
                    #count transaction 
                    countoperation=1#int(len(id_transactions))
                    #Get Company
                    # txtvalue=getInfoMErchant(xc["company"])
                    # info=txtvalue.split('|')
                    # #get Partner
                    # txtvalue1=getInfoMErchant(xc["id_partner"])
                    # info_part=txtvalue1.split('|')
                    amount=int(xc['amount_initial'])
                    tva=(amount*0.2)
                    sum_ttc=amount+tva
                    logo = xc['company']['logo'] if 'company' in xc and 'logo' in xc['company'] else url_logo
                    amountTotal+=amount
                    values={
                            "objectId":xc["objectId"],
                            "type":xc["type"],
                            "num_bill":numbill,#set num bill 
                            "total":amount,
                            "amountTotal":amountTotal,
                            "tva":tva,
                            "sum_ttc":sum_ttc,
                            "repres_name":xc["company"]["name"],#jumbo,cpp
                            "phone_company":xc["company"]["phone"],#jumbo,cpp
                            "email_company":xc["company"]["email"],#jumbo,cpp
                            "idAdelya":xc["company"]["id_adelya"],
                            "logo":logo,
                            "id_partner":"#",#orange ,jumbo 
                            "phone_partner":"#",#orange ,jumbo 
                            "email_partner":"#",#orange ,jumbo 
                            "month":month,
                            "year":year,
                            "motif":xc['motif'],
                            "cardnumber":xc['objects']['Client']['cardnumber'],
                            "partiel":1,
                            "status":xc['status']['name'],
                            "total_operation":countoperation
                    }
                    data_merchant.append(values)
                return data_merchant
            else :
                print('INFO MARCHAND IS NULL')
                return data_merchant.append([])
        except Exception as e :
            print (e)
    else :
        headers={
                                "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                                "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                                "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                                "Content-Type": "application/json"
                            
                    }
        url_get=url+'/endpoint/classes/CppPayBilling'

        params = urllib.parse.urlencode({"limit":1000000,"where": json.dumps({
                "id_partner":idPartenaire,
                "company_pay":company,
                "month":month,
                "year":year
                })
                })#,"include": "partner,company,transaction,customer"
    
        result=requests.get(url_get,params=params,headers=headers)
        x=result.json()
        get_data=x['results']
        data_merchant=[]
        amount=0
        
        try :
            for xc in get_data :
                #count transaction 
                dic=json.loads(xc['args'])
                countoperation=countOperation(dic)
                #Get Company
                
                txtvalue=getInfoMErchant(xc["company_pay"])
                info=txtvalue.split('|')
                #get Partner
                txtvalue1=getInfoMErchant(xc["id_partner"])
                info_part=txtvalue1.split('|')
                amount=int(xc['total'])
                tva=(amount*0.2)
                sum_ttc=amount+tva
                values={
                        "type":xc["type"],
                        "num_bill":xc["num_bill"],
                        "total":amount,
                        "tva":tva,
                        "sum_ttc":sum_ttc,
                        "repres_name":info[0],#jumbo,cpp
                        "phone_company":info[3],#jumbo,cpp
                        "email_company":info[2],#jumbo,cpp
                        "idAdelya":xc["id_adelya_company"],
                        "logo":xc["logo"],
                        "id_partner":info_part[0],#orange ,jumbo 
                        "phone_partner":info_part[3],#orange ,jumbo 
                        "email_partner":info_part[2],#orange ,jumbo 
                        "month":month,
                        "year":year,
                        "partiel":0,
                        "motif":"",
                        "cardnumber":"",
                        "total_operation":countoperation
                }
                data_merchant.append(values) 
                #[{'type': 'TRANSACTION', 'total': 25000, 'tva': 5000.0, 'sum_ttc': 30000.0, 'repres_name': '7qXmlUm1EE', 'idAdelya': 31596, 'logo': 'https://qacseafile.cpp-system.com/pictures?xys=Cpp-Pay/7qXmlUm1EE|JdVw877TNumFy14mGybC.jpg', 'id_partner':'egDrk4xDcT', 'month': 12, 'year': 2023}]
                print(data_merchant)
            return data_merchant
        except Exception as e :
            print (e)
def getInfoMErchant(data) :
    url=config_env['PARSE_URL_PAY']
    headers={
                        "X-Parse-Application-Id":config_env['PARSE_APP_ID_PAY'],
                        "X-Parse-REST-API-Key":config_env['PARSE_API_REST_KEY_PAY'],
                        "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_PAY'],
                        "Content-Type": "application/json"
                    
            }
    url_get=url+'/classes/Company'
    status="wyyamTxgzs"
    value="#|#|#|#"
    if(data!="CPP-SYSTEM"):
        params = urllib.parse.urlencode({"limit":1,"where": json.dumps({
                "id_adelya": {"$ne": ""},
                "objectId": data,
                'status': {'__type': 'Pointer', 'className': 'Status', 'objectId': f"{status}"}
                })
                })#,"include": "partner,company,transaction,customer"
    
        result=requests.get(url_get,params=params,headers=headers)
        x=result.json()
        get_merchant=x['results']
        data_merchant=[]
        
        for xc in get_merchant :
        
                # values={
                #     "objectid":xc["objectId"],
                #     "name":xc["name"],
                #     "repres_name":xc["representant_name"],
                #     "email":xc["email"],
                #     "phone":xc["phone"],
                #     "idAdelya":xc["id_adelya"],
                # }
            value=xc["name"]+"|"+xc["representant_name"]+"|"+xc["email"]+"|"+xc["phone"]

                # data_merchant.append(values)
            print(value)
    if(data=="CPP-SYSTEM"):
        value="CPP-SYSTEM|JOHARY EVELYN|cppsystem@cpp-system.com|03434343434"
    return value
def sendFilesBilling() :
    url=config_env['PARSE_BASE_URL_CORE']
    headers={
                            "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                            "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                            "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                            "Content-Type": "application/json"
                        
            }
   
    url_get=url+'/endpoint/classes/CppPayBilling'
    params = urllib.parse.urlencode({"limit":1000,"where": json.dumps({
              "sended":False
              })
    })
    result=requests.get(url_get,params=params,headers=headers)
    x=result.json()
    get_data=x['results']
   
    try :
        result=requests.get(url_get,params=params,headers=headers)
        x=result.json()
        get_data=x['results']
        for xc in  get_data :
            pdf_name=str(xc['year'])+"_"+str(xc['month'])+"_"+xc['num_bill']
            types=2
            date=''
            #get mail #
            cnf=generate_game()
            if xc['email'] != "#" :
                email=xc['email']
                cnf.sendMail(pdf_name,date,types,email)
            else :
                print("Adresse mail is not defined")
    except Exception as e  :
        print((e))
        return 
    
    # print(result)
    
def update_batch(data,Oid,data2,ident) :
    url=config_env['PARSE_BASE_URL_CORE']   
    #check if exist month and year and company and partner and amount
    headers={
                            "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                            "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                            "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                            "Content-Type": "application/json"
                        
            }
    store_url=url+'/endpoint/classes/CppPayBilling/'+data
    try :
          
            imgQr="https://chart.googleapis.com/chart?chs=200x200&cht=qr&chl=https://qapay.cpp-system.com/portal/"+str(ident)+"&choe=UTF-8"
        
            if(Oid!=""):
                data1={
                    "id_external_transac": Oid,
                    "ident": imgQr,
                }
                print("store billing")
                store_billing=requests.put(store_url,json=data1,headers=headers, timeout=120)
                #1-schedule create ligne transaction, type FAC
                #2-update transaction fils par objectId  transaction (1) et  batch core
                #3-generate facture de comm et transac
              
                route_download(data2,"facture",Oid) 
                if(store_billing.status_code==201):
                    print("Generate facture avec succes ! ")
                    return  True
                else :
                    print(store_billing.text)
                    return  False
            else :
                return False
    except  Exception as e :
            print(e.text)
            return  False

        
def batch_related_transaction():
    url=config_env['PARSE_BASE_URL_CORE']
    
    #check if exist month and year and company and partner and amount
    headers={
                            "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                            "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                            "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                            "Content-Type": "application/json"
                        
            }
    store_url=url+'/endpoint/classes/CppPayBilling'
    try :
            #1 get all args 
            params = urllib.parse.urlencode({"limit":100000000,"where": json.dumps({
              "id_external_transac": "Null",
             #   'status': {'__type': 'Pointer', 'className': 'Status', 'objectId': f"{status}"}
              })
             })
            record=[]
            result=requests.get(store_url,params=params,headers=headers)
            x=result.json()
            data_merc=x['results']
            for x in data_merc :
                record.append(x)
               
            #2 related transaction  with line fac
            return record
    except  Exception as e :
            print(e)
            return []
def updateSendMail(data) :
    url=config_env['PARSE_BASE_URL_CORE']   
    #check if exist month and year and company and partner and amount
    headers={
                            "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                            "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                            "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                            "Content-Type": "application/json"
                        
            }
    store_url=url+'/endpoint/classes/CppPayBilling/'+data
    try :
            if(Oid!=""):
                data1={
                    "sended": True
                }
                store_billing=requests.put(store_url,json=data1,headers=headers, timeout=120)
                #1-schedule create ligne transaction, type FAC
                #2-update transaction fils par objectId  transaction (1) et  batch core
                #3-generate facture de comm et transac
                if(store_billing.status_code==201):
                    return  True
                else :
                    print(store_billing.text)
                    return  False
            else :
                return False
    except  Exception as e :
            print(e.text)
            return  False
def countOperation(data) :
    transaction_counts = {}
    count=0
    for entry in data:
        transaction_id = entry["transaction_id"]
        transaction_counts[transaction_id] = transaction_counts.get(transaction_id, 0) + 1
    for transaction_id, count in transaction_counts.items():
        print(f"Transaction ID: {transaction_id}, Count: {count}")
    return count
def commissionBatch(data):
   
    month=int(data['month'])
    year=int(data['year'])
    company=data['company']
    # idPartenaire=data['idPartenaire']
    #TO Do : if exist id company get 
   
    url=config_env['PARSE_BASE_URL_CORE']
    headers={
                            "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                            "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                            "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                            "Content-Type": "application/json"
                        
                }
    url_get=url+'/endpoint/classes/CppPayBilling'
    params = urllib.parse.urlencode({"limit":100000,"where": json.dumps({
              "company_pay" : {
                    "$in":company
              },
              "type":"TRANSACTION",
              "month":month,
              "year":year
              })
              })#,"include": "partner,company,transaction,customer"
    
    result=requests.get(url_get,params=params,headers=headers)
    
    x=result.json()
   
    get_data=x['results']
   
    # d=[]
    # value={}
    # for x in get_data :
    #     value={
    #         "src":x['src'],
    #         "id":x['objectId'],
    #         "logo":x['logo'],
    #         "id_partner":x['id_partner'],
    #         "company_pay":x['company_pay'],
    #         "month":data['month'],
    #         "year":data['year'],
    #         "args":x['args']
    #     }
    # d.append(value)
     
    # return d
    # try :
    #     for x in get_data :
    #         value={
    #             "src":x['src'],
    #             "id":x['objectId'],
    #             "logo":x['logo'],
    #             "id_partner":x['id_partner'],
    #             "company_pay":x['company_pay'],
    #             "montant":x['amount_commission'],
    #             "month":data['month'],
    #             "year":data['year'],
    #             "args":x['args']
    #         }
    #         d.append(value)
    # except Exception as e :
    #     return e.text
    return get_data
def batch_transaction_commission(data):
    url=config_env['PARSE_BASE_URL_CORE']
    
    #check if exist month and year and company and partner and amount
    headers={
                            "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                            "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                            "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                            "Content-Type": "application/json"
                        
            }
    store_url=url+'/endpoint/classes/CppPayBilling'
    try :
            #1 get all args 
            params = urllib.parse.urlencode({"limit":100000000,"where": json.dumps({
              "month": data['month'],
              "year": data['year'],
             #   'status': {'__type': 'Pointer', 'className': 'Status', 'objectId': f"{status}"}
              })
             })
            record=[]
            result=requests.get(store_url,params=params,headers=headers)
            x=result.json()
            data_merc=x['results']
            for x in data_merc :
                record.append(x['company_pay'])
               
            #2 related transaction  with line fac
            return record
    except  Exception as e :
            print(e)
            return e
    
def getTokenPay() :
    try :
        url=config_env['URL_PAY']+"/api/oauth/token"
        auth_pay_basic=config_env['BTK']
        headers ={
            "Authorization": "Basic "f"{auth_pay_basic}",
            "Content-Type":"application/json"
        }
        result=requests.post(url,json={}, headers=headers, timeout=1500)
        if(result.status_code==200) :
            x=result.json()
            return x['access_token']
    except Exception as e :    
        print(e)
        return ''
def create_transact_payre(data) :
    #if post event
    print("add transaction facture")
    try :
        #{'__type': 'Pointer', 'className': 'Status', 'objectId': f"{status}"}
        #to do : get payement mean
        payement_mean="L8Q1ThEet5" #PSP
        #to do : get status
           # "payment_mean": {'__type': 'Pointer', 'className': 'CppPaymentMean', 'objectId': f"{payement_mean}"} ,
                        # "status": {'__type': 'Pointer', 'className': 'Status', 'objectId': f"{status}"} ,
                        # "source_app": "CPP-PAY",
                        # "month": data['month'],
                        # "year": data['year'],
                        # "type": "FAC",
                        # "operation": "CASHIN",
                        # "motif": "Facture post paiement mois de "+str(month),
                        # "amount_initial": int(data['amount']),
                        # "company": {'__type': 'Pointer', 'className': 'Company', 'objectId': f"{data['company']}" },
        status="UCmT43PVNd" #En attente
        data2 = {
                    "payment_mean": "DFR",
                    "source_app": "PAY",
                    "type": "FAC",
                    "operation": "CASHIN",
                    "motif": "Reglement Facture de post Paiement",
                    "amount_initial": data['amount'],
                    "company": data['company']
                }
      
        token=getTokenPay()
        #send Paiment DFR Chez pay
        data={
            'token':token,
            'args':data2 
        }
        idnt=sendTransactionPay(data)
        if(idnt != '#|#') :
            return idnt
        else :
            pass
            return '#|#'
    except  Exception as e :
        return '#|#'
def sendTransactionPay(data) :
    try :
            url=config_env['URL_PAY']+"/api/transactions"
            auth_pay_bear=data['token']
            headers ={
                "Authorization":"Bearer "f"{auth_pay_bear}",
                "Content-Type":"application/json"
            }
            print("url : "+url)
            print(data['args'])
            print(headers)

            result=requests.post(url,json=data['args'], headers=headers, timeout=1500)
            x=result.json()
            print(x)
            sys.stdout.flush()
            if(result.status_code==200) :
                if(x['data'] is not None ):
                    obj=x['data']['objectId']
                    identification=x['data']['identification']
                    return str(obj)+"|"+str(identification)
    except Exception as e :    
        print(str(e))
        sys.stdout.flush()
        return '#|#'
   
def testSchedule(): 
    url=config_env['PARSE_BASE_URL_CORE']
   #check if exist month and year and company and partner and amount
    headers={
                            "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                            "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                            "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                            "Content-Type": "application/json"
                        
            }
    store_url=url+'/endpoint/classes/TestSchedule'
    try :
            data1={
                "test":"OK OK"
            }
            requests.post(store_url,json=data1,headers=headers, timeout=120)
            print('ok')
            return 'ok'
    except Exception as  e :
        data1={
                "test":str(e)
        }
        requests.post(store_url,json=data1,headers=headers, timeout=120)
        return 'not ok'
class RapportMyCpp(Resource):
    def post(self):
        # Access the identity of the current user with get_jwt_identity
        # ch=checkToken()
        # if(ch==True) :
        import csv
        ch=checkToken()
        if(ch==True) :
            data = request.get_json()
            if data is not None :
                card = data.get('cardnumber')
                service = data.get('service')
                partner = data.get('partner')
                month = data.get('month')
                year = data.get('year')
                types_ret = data.get('types_ret')#csv or pdf
                mail = data.get('mail')# mail
                url=config_env['PARSE_BASE_URL_CORE']
                headers={
                                        "X-Parse-Application-Id":config_env['PARSE_APP_ID_CORE'],
                                        "X-Parse-REST-API-Key":config_env['PARSE_REST_KEY_CORE'],
                                        "X-Parse-Master-Key":config_env['PARSE_MASTER_KEY_CORE'],
                                        "Content-Type": "application/json"
                                    
                        }
                url_get=url+'/endpoint/classes/Commande'
                value={
                    "customer_adelya_id":{"$in":partner},
                    "reference_service":service,
                    "month":month,
                    "year":year
                }
                
                include_relations=["items"]
                params = urllib.parse.urlencode({"limit":10000000,"where": json.dumps(value),"include":",".join(include_relations)
                    })#,"include": "partner,company,transaction,customer"
        
                result=requests.get(url_get,params=params,headers=headers)
                x=result.json()
                get_data=x['results']
                relation_objects = []
                with ThreadPoolExecutor(max_workers=20) as executor:  # Adjust max_workers as needed
                    futures = [executor.submit(fetch_relation_objects, commande, url, headers) for commande in get_data]
                    relation_objects = []
                    for future in as_completed(futures):
                        result = future.result()
                        relation_objects.extend(result)     

                # generate_game().sendMail(namefile,'',2)
                random_integer = random.randint(1, 10000)       
                namefile=str(random_integer)+"_"+service+"_"+str(month)+"_"+str(year) 
                colonnes = [ 'name', 'montant', 'card', 'nfield3', 'createdAt', 'updatedAt', 'customer_adelya_id', 'month', 'year', 'mode', 'reference']
                try :
                    directory0="csvFiles"
                    if not os.path.isdir(directory0):
                          os.mkdir(directory0)
                except :
                    pass
                chemin_fichier_csv = 'csvFiles/'+namefile+'.csv'
                # Ouvrir le fichier CSV en mode écriture
                with open(chemin_fichier_csv, mode='w', newline='') as fichier_csv:
                    # Créer un objet écrivain CSV
                    ecrivain_csv = csv.DictWriter(fichier_csv, fieldnames=colonnes)
                    # Écrire l'en-tête (noms de colonnes) dans le fichier CSV
                    ecrivain_csv.writeheader()
                    # Boucle sur les données et écrire chaque ligne dans le fichier CSV
                    for ligne in relation_objects:
                        sys.stdout.flush()
                        ecrivain_csv.writerow(ligne)

                cnf=generate_game()
                if types_ret=="csv" :
                    types=3
                    email=mail
                    cnf.sendMail(chemin_fichier_csv,"",types,email) 
                
                    response = jsonify({'message': 'Report send with success!', 'status': 200})
                    # Set the status code of the response
                    response.status_code = 200
                    return response
                if types_ret=="pdf" :
                    response = jsonify({'message': 'template not found', 'status': 404})
                    # Set the status code of the response
                    response.status_code = 404
                    return response
                else:
                    response = jsonify({'message': 'Verifier le type de retour', 'status': 401})
                    # Set the status code of the response
                    response.status_code = 401
                    return response
        else :     
                response = jsonify({'message': 'Get  new token or  token is expired', 'status': 403})
                # Set the status code of the response
                response.status_code = 403
                return response
def fetch_relation_objects(commande, url, headers):
    id=commande.get('customer_adelya_id')
    month=commande.get('month')
    year=commande.get('year')
    mode=commande.get('mode')
    reference=commande.get('reference_service')
    relation_info = commande.get("items", {})
    if relation_info.get("__type") == "Relation":
            class_name = relation_info.get("className")
            relation_query_url = f"{url}/endpoint/classes/{class_name}"
            relation_query_params = {
                "where": json.dumps({
                    "$relatedTo": {
                        "object": {
                            "__type": "Pointer",
                            "className": "Commande",
                            "objectId": commande["objectId"]
                        },
                        "key": "items"
                    }
                })
            }
            relation_result = requests.get(relation_query_url, params=relation_query_params, headers=headers)
            relation_data = relation_result.json()
            # adelya
            # commande.get('customer_adelya_id')
            if  relation_data.get('results')  is not None :
                for rel in  relation_data.get('results') :
                    rel["montant"] = rel.pop('nfield1')
                    rel["card"] = rel.pop('nfield2')
                    rel.pop('status', None)
                    rel.pop('objectId', None)
                    rel["customer_adelya_id"]=id
                    rel["month"]=month
                    rel["year"]=year
                    rel["mode"]=mode
                    rel["reference"]=reference
                return relation_data.get('results', [])
    return []