from ast import Try
import sys
import mysql.connector
from dotenv import dotenv_values
config = dotenv_values(".env")
port=int(config['DB_PORT'])
class ConfigurationSql:
    def connect(self,host,user,password,database):
        self.host=host
        self.user=user
        self.port=port
        self.password=password
        self.database=database
    def insertEventJours(self,data,date,vehicule,month,year) :
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
        
        try :
            
            mycursor = mydb.cursor()
            sql = "INSERT INTO event_jours (objectIdVehicule, vehicule,date,nb_tourne,day,month,annee,cash_nombre,cpp_nombre,totalClient,annulation_nombre,somme_prix,somme_cash,somme_cpp,statusVersementCpp,billetage,status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            val = data
            mycursor.execute(sql, val)
            mydb.commit()
            return ''   
            
            
        except Exception as e :
             print(e)
    def insertVersementJours(self,data) :
        
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
        
        try :
             mycursor = mydb.cursor()
             print(data)   
             sql = "INSERT INTO suivi_versements (montant,proprietaire_id,vehicule,date,year,month,status,type_paiement,other_number,nom_banque,numero_compte,operateur,dateEntre,ReferenceVersement,ReferencePaiement,objectIdParamEventComm,idDemandeVersement) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s)"
             val = data
             mycursor.execute(sql, val)
                     
             mydb.commit()
             print("send data  versement to  mysql with successfully!")
        except Exception  as e :
             print(e)
    def insertIncidentJours(self,database_config,p) :
        
        mydb = mysql.connector.connect(
            host=f"{database_config['url_serve']}",
            user=f"{database_config['username']}",
            port=port,
            password=f"{database_config['passwd']}",
            database=f"{database_config['database']}",
            charset="utf8mb4",
            use_unicode=True
        )
       
        try :
             mycursor = mydb.cursor()
             sql="INSERT INTO eventincident (type,target,date,vehicule,duration,montant,comments,month,year,realDate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"
             val=p
             mycursor.execute(sql,val)
             mydb.commit()
             
             print("Insertion incident avec success")        
             return 'ok'
        except Exception as e  :
             print(e)
             return str(e)
             
    def getLastDateIs(self) :
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            # host=f"{database_config['url_serve']}",
            # user=f"{database_config['username']}",
            # password=f"{database_config['passwd']}",
            # database=f"{database_config['database']}",
        )
        myresult="dd/mm/YYYY"
        try :
             mycursor = mydb.cursor()
             sql="SELECT * FROM eventincident ORDER BY id DESC LIMIT 1"
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
             for x in myresult:
                 p=x[3]
             return p    
        except :
             return myresult
    def getArretSql(self) :
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            # host=f"{database_config['url_serve']}",
            # user=f"{database_config['username']}",
            # password=f"{database_config['passwd']}",
            # database=f"{database_config['database']}",
        )
        myresult=[]
        p=[]
        i=0
        try :
             mycursor = mydb.cursor()
             sql="SELECT * FROM ligne_stations where objectIdParse !='' "
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
             
             for x in myresult:
                p.append(x)
                
             return p
        except :
             return p
    def getInfoProp(self,datavehicule,dateLimit,amount):
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True,
          
            )
        try :
             mycursor = mydb.cursor()
            #  sql = "SELECT * FROM vehicules WHERE objectIdParse = '"+f"{datavehicule}"+"'"
             sql="SELECT \
                vehicules.*, \
                proprietaires.*\
                FROM vehicules \
                INNER JOIN proprietaires ON vehicules.proprietaire_id= proprietaires.id WHERE vehicules.num_immatriculation = '"+f"{datavehicule}"+"'"
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
            
             for x in myresult:
               
                tp="BNK"
                if x[62]=='Mobile Money':
                    tp="MBM"
                pdv="j+1"
                if x[64]=='1 day':
                    pdv="j+1"
                    datenow=""
                #else get params proprio Todo
                
                prop={
                    "objectIdVehicule":x[10],
                    "vehicule":x[0],
                    "idProp":x[38],
                    "nomProp":x[39]+" "+x[40],
                    "firstname":x[40],
                    "phone":x[43],
                    "idadelya":x[46],
                    #tp
                    "type_payement":"CSH",
                    "periodicity":pdv,
                    "limit":datenow,
                    "operateur":x[73],
                    "amount":amount
                }
            
             return prop
        except Exception as e :
             print(e)   
             #print("Erreur  get Info Proprio")
    def getVehicule(self):
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            
            )
        try :
            mycursor = mydb.cursor()
            sql = "SELECT * FROM vehicules WHERE actif = 'oui' AND objectIdParse != '' AND validation = 'oui'"
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            p=[]
           
            for x in myresult:
                p.append(x[10])
             
            return p
        except :
             print("Erreur  get Info vehic")

    def infopropriotocore(self,id):
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
        try :
             mycursor = mydb.cursor()
            # sql = "SELECT * FROM vehicules WHERE objectIdParse = '"+f"{datavehicule}"+"'"
             sql="SELECT *\
                FROM proprietaires \
                WHERE id = '"+f"{id}"+"'"
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
             for x in myresult:
               
                tp="BNK"
                if x[24]=='Mobile Money':
                    tp="MBM"
                pdv="j+1"
                if x[26]=='1 day':
                    pdv="j+1"
                #else get params proprio Todo
                dataprop={
                        "id_prop":x[0],
                        "idAdelya":x[8],
                        "phone":x[5],
                        "type_paiement":tp,
                        "periodiciteVersement":pdv,
                        "nom_operat":x[35],
                        "nom_banque":x[23],
                        "other_number":x[5],
                        "rib":x[21]
                }
             
             return dataprop
        except :
             print("Erreur serveur 500")

    def getPapiers(self,data):
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
        try :
             mydata=[]
             mycursor = mydb.cursor()
            # sql = "SELECT * FROM vehicules WHERE objectIdParse = '"+f"{datavehicule}"+"'"
             sql="SELECT *\
                FROM papier_suivi_vehicules \
                WHERE dateFin < '"+f"{data}"+"'"
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
             for x in myresult:

                datapaps={
                        "type":x[1],
                        "date":x[5],
                        "vehicule":x[6],
                        "libelle":x[3],
                        "status":'expired'
                }
                if(x[5]!="") :
                    mydata.append(datapaps)
             
             return mydata
        except :
             print("Erreur serveur 500")
             return []
    def getNumeroProprio(self,vehicule):
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
        try :
             mydata=[]
             mycursor = mydb.cursor()
             sql = "SELECT * FROM vehicules WHERE actif='oui' AND validation='oui' AND num_immatriculation = '"+f"{vehicule}"+"'"
            #  sql="SELECT *\
            #     FROM papier_suivi_vehicules \
            #     WHERE dateFin < '"+f"{data}"+"'"
             sql="SELECT \
                vehicules.*, \
                proprietaires.*\
                FROM vehicules \
                INNER JOIN proprietaires ON vehicules.proprietaire_id= proprietaires.id WHERE vehicules.num_immatriculation = '"+f"{vehicule}"+"'"
         
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
             
             for x in myresult:
                numero=x[43]
             return numero
        except :
             print("Erreur serveur 500")
             return ''
    
    def getListIdProp(self,datavehicule):
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",  
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
        try :
             mycursor = mydb.cursor()
            # sql = "SELECT * FROM vehicules WHERE objectIdParse = '"+f"{datavehicule}"+"'"
             sql="SELECT \
                vehicules.*, \
                proprietaires.*\
                FROM vehicules \
                INNER JOIN proprietaires ON vehicules.proprietaire_id= proprietaires.id WHERE vehicules.objectIdParse = '"+f"{datavehicule}"+"'"
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
          
             for x in myresult:
                 prop=x[33]
                
             return (prop)
        except :
             return ""
    def getListVehiculesProp(self,id):
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
        try :
             mycursor = mydb.cursor()
             sql = "SELECT * FROM vehicules WHERE proprietaire_id = '"+f"{id}"+"'"

             mycursor.execute(sql)
             myresult = mycursor.fetchall()
             vehicu=[]     
             for x in myresult:
                if(x[10]!='') :
                    vehicu.append(x[10])  
             return vehicu 
        except :
             print("Erreur get vehicules")  
             return []   
    def getListVehiculesAll(self,database_config):
        mydb = mysql.connector.connect(
            host=f"{database_config['url_serve']}",
            user=f"{database_config['username']}",
            port=f"{self.port}",
            password=f"{database_config['passwd']}",
            database=f"{database_config['database']}",
            charset="utf8mb4",
            use_unicode=True
            )
        try :
             mycursor = mydb.cursor()
             sql = "SELECT * FROM vehicules WHERE objectIdParse !='' AND actif = 'oui' AND validation ='oui' "

             mycursor.execute(sql)
             myresult = mycursor.fetchall()
             vehicu=[]     
             for x in myresult:
                if(x[10]!='') :
                    vehicu.append(x[10])
                
             
             
             return vehicu
        except :
             print("Erreur get vehicules")     
    def updateArret(self,locate,object,arret,quart) :
        mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
        try :
            mycursor = mydb.cursor()

            #sql = "UPDATE ligne_stations SET zone_gps = '"+str(locate)+"' WHERE objectIdParse='"+f"{object}"+"'"
            sql = "UPDATE ligne_stations SET zone_gps = '"+str(locate)+"',objectIdParse = '"+str(object)+"' WHERE nom_station='"+f"{arret}"+"' AND nom_quartier = '"+f"{quart}"+"'"
            mycursor.execute(sql)

            mydb.commit()

            print(mycursor.rowcount, "record(s) affected")
        except :
             print("Erreur update")  
    def getMonthPointage(self,text) :
            mydb = mysql.connector.connect(
            host=f"{self.host}",
            user=f"{self.user}",
            port=f"{self.port}",
            password=f"{self.password}",
            database=f"{self.database}",
            charset="utf8mb4",
            use_unicode=True
            )
            mycursor = mydb.cursor()
            sql="INSERT INTO eventpointage(dateStart,month,year,status,type,fullName,objectId,endStart,dateValidation,hourly,idService,reason,pointageObjectId,idValideur,realDate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            val=text
            mycursor.execute(sql,val)
            mydb.commit()
            print("created with successfully!")
    def getMonthCommission(self,database_config,text) :
           
            mydb = mysql.connector.connect(
            host=f"{database_config['url_serve']}",
            user=f"{database_config['username']}",
            port=f"{self.port}",
            password=f"{database_config['passwd']}",
            database=f"{database_config['database']}",
            charset="utf8mb4",
            use_unicode=True
            )
            try :
                mycursor = mydb.cursor()
                sql="INSERT INTO restit_commission (amount,amount_eff,amount_rest,vehicule,month,year,status,realDate,ca_pass_nv,versement_eff) VALUES (%s, %s,%s, %s, %s, %s, %s,%s,%s,%s)"
                val=text
                mycursor.execute(sql,val)
                # mydb.commit()
                print("created with successfully!")
            except Exception as e :
                print (str(e))
    def getEventJours(self,database_config,data):
        mydb = mysql.connector.connect(
            host=f"{database_config['url_serve']}",
            user=f"{database_config['username']}",
            port=port,
            password=f"{database_config['passwd']}",
            database=f"{database_config['database']}",
            charset="utf8mb4",
            use_unicode=True
            )
        try :
            
             mycursor = mydb.cursor()
             sql = f"SELECT * FROM event_jours WHERE date = '{data['date']}' AND vehicule = '{data['vehicule']}'"
             mycursor.execute(sql)
             myresult = mycursor.fetchall()
             id=''
             sql = f"SELECT * FROM vehicules WHERE num_immatriculation = '{data['vehicule']}'"
             mycursor.execute(sql)
             vehicules = mycursor.fetchall()
             objectidVehicule=''
             for x in vehicules:
                 if(x[10!='']):
                    objectidVehicule=x[10]
                
             if  myresult:
                for x in myresult:
                    if(x[0]!='') :
                        id=x[0]
                        sql = "UPDATE event_jours SET cash_nombre = '" + str(data['cash_nombre']) + "', cpp_nombre = '" + str(data['cpp_nombre']) + "', totalClient = '" + str(data['totalClient']) + "', somme_cash = '" + str(data['somme_cash']) + "', somme_cpp = '" + str(data['somme_cpp']) + "', somme_prix = '" + str(data['somme_prix']) + "' WHERE id = '" + str(id) + "'"
                        mycursor.execute(sql)
                        mydb.commit()
               
                        print(mycursor.rowcount, "record(s) affected")
                  
             else :
                #  {insert}
                print('#')
                sql = "INSERT INTO event_jours (objectidVehicule,vehicule,date,nb_tourne,day,month,annee,cash_nombre, cpp_nombre, totalClient,annulation_nombre, somme_cash, somme_cpp, somme_prix,billetage) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, %s, %s, %s, %s, %s, %s)"
                values = (objectidVehicule,data['vehicule'],data['date'],data['tour'],0,'4','2024',data['cash_nombre'], data['cpp_nombre'], data['totalClient'],'0', data['somme_cash'], data['somme_cpp'], data['somme_prix'],'')
                mycursor.execute(sql, values)

                # Validation de la transaction
                mydb.commit()
                print("new row inserted")
              
        except Exception as e:
             print(e)        