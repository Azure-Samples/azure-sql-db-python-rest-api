import sys
import os
import json
import pyodbc
import socket
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from threading import Lock
from tenacity import *
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import ProbabilitySampler
import logging

# Initialize Flask
app = Flask(__name__)

# Setup Azure Monitor
if 'APPINSIGHTS_KEY' in os.environ:
    middleware = FlaskMiddleware(
        app,
        exporter=AzureExporter(connection_string="InstrumentationKey={0}".format(os.environ['APPINSIGHTS_KEY'])),
        sampler=ProbabilitySampler(rate=1.0),
    )

# Setup Flask Restful framework
api = Api(app)
parser = reqparse.RequestParser()
parser.add_argument('customer')

# Implement manual connection pooling
class ConnectionManager(object):    
    __instance = None
    __conn_index = 0
    __conn_dict = {}
    __lock = Lock()

    def __new__(cls):
        if ConnectionManager.__instance is None:
            ConnectionManager.__instance = object.__new__(cls)        
        return ConnectionManager.__instance    

    def is_retriable(self, value):
        # https://docs.microsoft.com/en-us/sql/odbc/reference/appendixes/appendix-a-odbc-error-codes
        RETRY_CODES = [  
            "08S01",    # ODBC - Communication link failure
            "8001",   
            "42000",       
            "1204",   # The instance of the SQL Server Database Engine cannot obtain a LOCK resource at this time. Rerun your statement when there are fewer active users. Ask the database administrator to check the lock and memory configuration for this instance, or to check for long-running transactions.
            "1205",   # Transaction (Process ID) was deadlocked on resources with another process and has been chosen as the deadlock victim. Rerun the transaction
            "1222",   # Lock request time out period exceeded.
            "49918",  # Cannot process request. Not enough resources to process request.
            "49919",  # Cannot process create or update request. Too many create or update operations in progress for subscription "%ld".
            "49920",  # Cannot process request. Too many operations in progress for subscription "%ld".
            "4060",   # Cannot open database "%.*ls" requested by the login. The login failed.
            "4221",   # Login to read-secondary failed due to long wait on 'HADR_DATABASE_WAIT_FOR_TRANSITION_TO_VERSIONING'. The replica is not available for login because row versions are missing for transactions that were in-flight when the replica was recycled. The issue can be resolved by rolling back or committing the active transactions on the primary replica. Occurrences of this condition can be minimized by avoiding long write transactions on the primary.

            "40143",  # The service has encountered an error processing your request. Please try again.
            "40613",  # Database '%.*ls' on server '%.*ls' is not currently available. Please retry the connection later. If the problem persists, contact customer support, and provide them the session tracing ID of '%.*ls'.
            "40501",  # The service is currently busy. Retry the request after 10 seconds. Incident ID: %ls. Code: %d.
            "40540",  # The service has encountered an error processing your request. Please try again.
            "40197",  # The service has encountered an error processing your request. Please try again. Error code %d.
            "10929",  # Resource ID: %d. The %s minimum guarantee is %d, maximum limit is %d and the current usage for the database is %d. However, the server is currently too busy to support requests greater than %d for this database. For more information, see http://go.microsoft.com/fwlink/?LinkId=267637. Otherwise, please try again later.
            "10928",  # Resource ID: %d. The %s limit for the database is %d and has been reached. For more information, see http://go.microsoft.com/fwlink/?LinkId=267637.
            "10060",  # An error has occurred while establishing a connection to the server. When connecting to SQL Server, this failure may be caused by the fact that under the default settings SQL Server does not allow remote connections. (provider: TCP Provider, error: 0 - A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond.) (Microsoft SQL Server, Error: 10060)
            "10054",  # The data value for one or more columns overflowed the type used by the provider.
            "10053",  # Could not convert the data value due to reasons other than sign mismatch or overflow.
            "233",    # A connection was successfully established with the server, but then an error occurred during the login process. (provider: Shared Memory Provider, error: 0 - No process is on the other end of the pipe.) (Microsoft SQL Server, Error: 233)
            "64",
            "20",
            "0"
            ]
        result = value in RETRY_CODES
        return result
    
    def __getConnection(self):
        self.__lock.acquire()
        idx = self.__conn_index + 1        
        if idx > 9: idx = 0                              
        self.__conn_index = idx
        self.__lock.release()                

        if not idx in self.__conn_dict.keys():
            application_name = ";APP={0}-{1}".format(socket.gethostname(), idx)  
            conn = pyodbc.connect(os.environ['SQLAZURECONNSTR_WWIF'] + application_name)                  
            self.__lock.acquire()
            self.__conn_dict.update( { idx: conn } )
            self.__lock.release() 
        else:
            self.__lock.acquire()
            conn = self.__conn_dict[idx]
            self.__lock.release() 
        
        return (idx, conn)   

    def __removeConnection(self, idx):
        self.__lock.acquire()
        if idx in self.__conn_dict.keys():
            del(self.__conn_dict[idx])
        self.__lock.release()    

    def __removeConnections(self):
        self.__lock.acquire()
        self.__conn_dict.clear()
        self.__lock.release()    

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(10), after=after_log(app.logger, logging.DEBUG))
    def executeQueryJSON(self, procedure, payload=None):
        result = {}  
        try:
            (idx, conn) = self.__getConnection()
            app.logger.info(f"Connection Index: {idx}")

            cursor = conn.cursor()

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
        except pyodbc.Error as e:            
            if isinstance(e, pyodbc.ProgrammingError) or isinstance(e, pyodbc.OperationalError):
                app.logger.error(f"Error: {e.args[0]}")
                if self.is_retriable(e.args[0]):
                    # If there is a "Communication Link Failure" error, 
                    # then all connections must be removed
                    # as all will be in an invalid state
                    if (e.args[0] == "08S01"):
                        self.__removeConnections() 
                    else:
                        self.__removeConnection(idx) 
                    raise                        

        return result

class Queryable(Resource):
    def executeQueryJson(self, verb, payload=None):
        result = {}  
        entity = type(self).__name__.lower()
        procedure = f"web.{verb}_{entity}"
        result = ConnectionManager().executeQueryJSON(procedure, payload)
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
