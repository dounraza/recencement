import esperclient
from esperclient import TokenApi, ApiClient,EnterpriseApi
from esperclient.rest import ApiException

from openpyxl import Workbook
import os
import io
from dotenv import dotenv_values
import urllib
from flask import Flask, send_file,make_response

  
config = dotenv_values(".env")
# config = dotenv_values("c:/wamp64/www/extract/cpptransportextract/.env")
class CppEsper:
    #config serveur parse
    hostEsper=config['HOST_ESPER']
    #config serveur mysql
    # def connect(self, hostEsper):
    #     self.hostEsper = hostEsper

    #print("--- %s seconds ---" % (time.time() - start_time))
    configuration = esperclient.Configuration()
    enterprise_id=config['ENTREPRISE_ID']
    configuration.host = hostEsper
    configuration.api_key['Authorization'] = config['API_KEY_ESP']
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    #api_instance =  esperclient.EnterpriseApi(esperclient.ApiClient(configuration))
  
    #
    group=config['GROUP_ID_NEW'] #'9e09f507-0351-4ae8-b645-7256114dca7f' #'355287000475883'
    def initialize(self,groups) :
          group=config['GROUP_ID_NEW']
          if groups=="tpeBus" :
               group=config['GROUP_ID_NEW']
          if groups=="tpeCollect" :
               group=config['GROUP_ID_NEW']
          #if groups=="kiosk" :
               

          value=self.getDeviceInGroup(group,groups)
          return value
    def getGroup(self,group):
        api_instance = esperclient.DeviceGroupApi(esperclient.ApiClient(self.configuration))
     #    api_instance = EnterpriseApi(ApiClient(self.configuration))
        try:
               api_response=api_instance.get_all_groups(self.enterprise_id)
               listsdevice=api_response.results
               
               for x in  listsdevice :
                   print(x.id) 
                   print("=>") 
                   print(x.name) 
               # api_response = api_instance.get_enterprise(self.enterprise_id)
               # print(api_response)
        #"(type,x.device_name,x.network_info.imei1,'CPP',x.network_info.phone_number,x.network_info.phone_number,'CPP','nouveau','CPP',1,'0')"
        except ApiException as e:
            return ("Exception when calling TokenApi->get_token_info: %s\n" % e)
    def getDeviceInGroup(self,group,typeMat):
       
        api_instance = esperclient.DeviceApi(esperclient.ApiClient(self.configuration))
        data=''
        try:
            api_response=api_instance.get_all_devices(self.enterprise_id,group=group)
            listsdevice=api_response.results
            workbook = Workbook()
            sheet = workbook.active
            listData=list()
            listData.append(("type","marque","IMEI","owner","phone","mobile","contrat",'etat','price_plan',"responsable","responsable_id","getLocation"))
            for x in listsdevice :
                     listData.append((typeMat,x.device_name,x.network_info['imei1'],'CPP',x.network_info['phoneNumber1'],x.network_info['phoneNumber1'],'CPP','nouveau','CPP',1,'false'))
                    # print(x.network_info['imei1'])
          #   print(type(rows))
            c=tuple(listData)
            temp_file="FilesTemps/data.xlsx"
            real_path = os.path.realpath(temp_file)
            excel_io = io.BytesIO()   
            excel_io.seek(0)
            for row in c:
                sheet.append(row)
            workbook.save(temp_file)
          #   response = make_response(send_file(real_path))
          #   response.headers['Content-Disposition'] = 'attachment; filename=data.xlsx'
           
          #   urllib.request.urlretrieve('http:/localhost/data.xlsx', 'FilesTemps/data.xlsx')
            return send_file(real_path, as_attachment=True)
        except ApiException as e:
            print("Exception when calling TokenApi->get_token_info: %s\n" % e)
    # def getnerateFileXlsx(self,cells):
    #     data=''
    #     try: 
    #          # dataframe Name and Age columns
    #         df = pd.DataFrame({'Name': ['A', 'B', 'C', 'D'],
    #                         'Age': [10, 0, 30, 50]})

    #         # Create a Pandas Excel writer using XlsxWriter as the engine.
    #         writer = pd.ExcelWriter('demo.xlsx', engine='xlsxwriter')
    #         pd
    #         # Convert the dataframe to an XlsxWriter Excel object.
    #         df.to_excel(writer, sheet_name='Sheet1', index=False)

    #         # Close the Pandas Excel writer and output the Excel file.
    #         writer.close()
    #         path = os.getcwd()
    #         print("Le répertoire courant est : " + path)
    #         # récupérer le nom du répertoire courant
    #         repn = os.path.basename(path)
    #         print("Le nom du répertoire est : " + repn)
    #         return path+"=>>"+repn
        except ApiException as e:
            print("Exception when calling TokenApi->get_token_info: %s\n" % e)
        
    