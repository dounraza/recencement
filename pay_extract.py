import sys
import time
from Configuration import Configuration
from urllib import response
import urllib
import uuid
import urllib.parse
import datetime
from datetime import date
import requests
import json
import pandas as pd
from dotenv import dotenv_values
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, Column, String, Integer, MetaData, Table
from sqlalchemy.orm import sessionmaker
config = dotenv_values(".env")

# config = dotenv_values("c:/wamp64/www/extract/cpptransportextract/.env")
class pay_extract :
  
# Exemple de fonction pour traiter les données d'un magasin
  def process_store_transaction(store_data):
    url=config['PARSE_BASE_URL_CORE']
    headers={
                        "X-Parse-Application-Id":config['PARSE_APP_ID_CORE'],
                        "X-Parse-REST-API-Key":config['PARSE_REST_KEY_CORE'],
                        "X-Parse-Master-Key":config['PARSE_MASTER_KEY_CORE'],
                        "Content-Type": "application/json"
                    
            }
   
    
    try :
        year=2023
        month=11
        #search merchant
        merchant_search={
                "idAdelya": int(store_data['idGroupAdelya'])
        }

        params_merchant = urllib.parse.urlencode({"limit":10000,"where": json.dumps(merchant_search)})
        myurl_merchant=url+'/endpoint/classes/Merchant'
        result_merchant=requests.get(myurl_merchant,params=params_merchant,headers=headers)
        x=result_merchant.json()
        # {'__type': 'Pointer', 'className': 'Networks', 'objectId': 'rqsdyKPUyL'}
        value_result=x['results']
        for p in value_result :
            k=p['objectId']
     
        #search data demand
        param_search={
                "id_ad_payee": int(store_data['idGroupAdelya']),
                "source_app": store_data['src'],
                "year": year,
                "month": month
                }
        
        params = urllib.parse.urlencode({"limit":10000,"where": json.dumps(param_search),"include":"status"})
        myurl=url+'/endpoint/classes/Demand'
        result=requests.get(myurl,params=params,headers=headers)
        x=result.json()
        values=x['results']
        args=[]
        amount_total=0
        ref_billing=str(year)+"_"+str(month)+"_"+"001"
        for records in values:
            if(records['status']['value']==4) :
                amount_total+=float(records['amount'])
                if(records['transaction_reference'] == '') :
                    ref =""
                else : ref=str(records['transaction_reference'])
                data={
                    "objectId":records['objectId'],
                    "amount":records['amount'],
                    "id_ad_payee":records['id_ad_payee'],
                    "operation_type":records['operation_type'],
                    "transaction_reference":ref,
                    "payment_method":records['payment_method'],
                    "status":records['status']['value'],
                    "payment_method":records['payment_method'],
                    "cardnumber_payer":records['cardnumber_payer'],
                    }
                json_string = json.dumps(data)
                args.append(json_string)
        #data store
        data_store={
            "amount":amount_total,
            "num_bill":"1",
            "ref":ref_billing,
            "month":month,
            "year":year,
            "merchant":{'__type': 'Pointer', 'className': 'Merchant', 'objectId': k},
            "merchant_id_adelya":store_data["idGroupAdelya"],
            "args":str(args),
            "date":"20/11/2023",
            "status":2,
            "url_invoice":""
        }
        #store billing
    
        store_url=url+'/endpoint/classes/MerchantBilling'
    
        store_billing=requests.post(store_url,json=data_store,headers=headers, timeout=120)
        print(store_billing)
        return "Data created SuccessFully!"
    except Exception as e:
        print(e)
    #Total amount|month|year|merchant|merchant_id_adelya|args|url_invoice|status|date
  #metaData (Liste des Magasins)
  liste_de_magasins = [
    {'nom': 'COMDATA','idGroupAdelya':'31596' ,'src': 'PAY'},
    {'nom': 'CTM','idGroupAdelya':'24674' ,'src': 'PAY'},
    # ... Ajoutez les données des autres magasins
  ]

  with ThreadPoolExecutor() as executor:
    num_processes = executor._max_workers
    executor.map(process_store_transaction,liste_de_magasins)