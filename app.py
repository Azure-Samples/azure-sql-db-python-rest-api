import sys
import os
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
import json
import pyodbc
from threading import Lock

# Initialize Flask
app = Flask(__name__)

# Setup Flask Restful framework
api = Api(app)
parser = reqparse.RequestParser()
parser.add_argument('customer')

conn_index = 0
conn_list = list()

for c in range(10):
    conn = pyodbc.connect(os.environ['SQLAZURECONNSTR_WWIF'])
    conn_list.append(conn)

lock = Lock()

def getConnection():
    global conn_index
    
    lock.acquire()
    conn_index += 1
    lock.release()
    
    if conn_index > 9:
        conn_index = 0        
    return conn_list[conn_index]

class Queryable(Resource):
    def executeQueryJson(self, verb, payload=None):
        result = {}        
        conn = getConnection()
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
