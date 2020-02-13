import sys
import os
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
import json
import pyodbc
import socket
from threading import Lock

# Initialize Flask
app = Flask(__name__)

# Setup Flask Restful framework
api = Api(app)
parser = reqparse.RequestParser()
parser.add_argument('customer')

class ConnectionManager(object):    
    __instance = None
    __conn_index = 0
    __conn_dict = {}
    __lock = Lock()

    def __new__(cls):
        if ConnectionManager.__instance is None:
            ConnectionManager.__instance = object.__new__(cls)        
        return ConnectionManager.__instance    

    def getConnection(self):
        self.__lock.acquire()
        self.__conn_index += 1    
        
        if self.__conn_index > 9:
            self.__conn_index = 0        

        if not self.__conn_index in self.__conn_dict.keys():
            application_name = ";APP={0}-{1}".format(socket.gethostname(), self.__conn_index)        
            conn = pyodbc.connect(os.environ['SQLAZURECONNSTR_WWIF'] + application_name)
            self.__conn_dict.update( { self.__conn_index: conn } )

        result = self.__conn_dict[self.__conn_index]
        self.__lock.release()                

        return result

class Queryable(Resource):
    def executeQueryJson(self, verb, payload=None):
        result = {}  
        conn = ConnectionManager().getConnection()
        cursor = conn.cursor()    
        entity = type(self).__name__.lower()
        procedure = f"web.{verb}_{entity}"
        try:
            if payload:
                cursor.execute(f"EXEC {procedure} ?", json.dumps(payload))
            else:
                cursor.execute(f"EXEC {procedure}")

            result = cursor.fetchone()

            if result:
                result = json.loads(result[0])                           
            else:
                result = {}

            cursor.commit()    
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        finally:    
            cursor.close()

        return result

# Customer Class
class Customer(Queryable):
    def get(self, customer_id):     
        customer = {}
        customer["CustomerID"] = customer_id
        result = self.executeQueryJson("get", customer)   
        return result, 200
    
    def put(self):
        args = parser.parse_args()
        customer = json.loads(args['customer'])
        result = self.executeQueryJson("put", customer)
        return result, 201

    def patch(self, customer_id):
        args = parser.parse_args()
        customer = json.loads(args['customer'])
        customer["CustomerID"] = customer_id        
        result = self.executeQueryJson("patch", customer)
        return result, 202

    def delete(self, customer_id):       
        customer = {}
        customer["CustomerID"] = customer_id
        result = self.executeQueryJson("delete", customer)
        return result, 202

# Customers Class
class Customers(Queryable):
    def get(self):     
        result = self.executeQueryJson("get")   
        return result, 200
    
    
# Create API routes
api.add_resource(Customer, '/customer', '/customer/<customer_id>')
api.add_resource(Customers, '/customers')
