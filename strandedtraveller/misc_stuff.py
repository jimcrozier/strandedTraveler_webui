import psycopg2, json, requests
from pymongo import MongoClient
from datetime import datetime
#from confluent_kafka import Producer
from requests.auth import HTTPBasicAuth

#class KafkaProducer(object):
#    def __init__(self):
#        pass
#    
#    def connect(self, bootstrap_servers, ssl_cert_path, username, password):
#        self.config = {'bootstrap.servers': bootstrap_servers,
#                           'ssl.ca.location': ssl_cert_path,
#                           'sasl.mechanisms': 'PLAIN',
#                           'sasl.username': username,
#                           'sasl.password': password,
#                           'security.protocol': 'sasl_ssl',
#                           'batch.num.messages': 1}
#
#    def sendMessage(self, topic, message):
#        tempVal = json.dumps(message).encode('utf-8')
#        p = Producer(self.config)
#        p.produce(topic, tempVal)
#        p.flush()


def safe_nosql_call(call):
    def _safe_nosql_call(*args, **kwargs):
        for i in xrange(5):
            try:
                return call(*args, **kwargs)
            except pymongo.AutoReconnect:
                time.sleep(0.2*pow(2, i))
        print 'Error: Failed operation!'
    return _safe_nosql_call

class DemoNoSQLDatabase(object):
    """Handles all interactions with the NoSQL document store."""
    def __init__(self):
        super(DemoNoSQLDatabase, self).__init__()
    def connect(self, host, database, user, password, port):
        connStr = ("mongodb://" + user + ":" + password + "@" 
                        + host + ":" + str(port) + "/" + database)
        self.connection = MongoClient(connStr, connect=False)
        self.db = self.connection['airline-demo']
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
    
    @safe_nosql_call
    def get_offers(self, airline_code, flight_number, date):
        query = {}
        query['flightNumber'] = flight_number
        query['flightDate'] = date.strftime("%Y-%m-%d")
        query['flightAirlineCode'] = airline_code
        result = self.db['offers'].find(query)
        allOffers = []
        for offer in result:
            offer['_id'] = str(offer['_id'])
            allOffers.append(offer)
        return allOffers
     
    @safe_nosql_call    
    def get_offers_with_exception_id(self, passengerExceptionID):
        query = {}
        query['passengerExceptionId'] = passengerExceptionID
        result = self.db['offers'].find(query)
        allOffers = []
        for offer in result:
            offer['_id'] = str(offer['_id'])
            allOffers.append(offer)
        return allOffers
        
    @safe_nosql_call
    def delete_all_offers(self, airline_code):
        query = {}
        query['flightAirlineCode'] = airline_code
        self.db['offers'].delete_many(query)
    def __del__(self):
        self.disconnect()


class DemoDatabase(object):
    """Handles all interactions with the database."""
    def __init__(self, host, database, user, password, port=5432):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self._connect()
        
    def _connect(self):
        self.connection = psycopg2.connect(host=self.host, database=self.database, user=self.user, password=self.password, port=self.port)

    def disconnect(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
    
    def get_map_pairs(self, airline_code):
        query = "SELECT * FROM map_pairs WHERE airline_code=%s;"
        return self._resultAsList(query, (airline_code,))
    
    def get_airports(self, airline_code):
        query = """SELECT DISTINCT airports.*, temp.activity
                   FROM airports, (
                       SELECT origin, count(*) AS activity 
                       FROM flights WHERE airline_code=%s
                       GROUP BY origin
                   ) 
                   AS temp WHERE airport=temp.origin;"""
        return self._resultAsList(query, (airline_code,))
    def get_issues(self, issueDate, issueWindow, airline_code):
        dStr = issueDate.strftime("%Y-%m-%d %H:%M")
        query = """ SELECT flights.*, airplanes.*, CAST(LEAST(pass.passenger_count, FLOOR(airplanes.seat_count*0.9)) AS int) AS passengers_affected 
                    FROM flights, airplanes, 
                            (SELECT flights.flight_number, flights.scheduled_departure_utc, flights.airline_code, count(manifests.*) AS passenger_count 
                             FROM flights, manifests
                                WHERE flights.scheduled_departure_utc>%s
                                    AND flights.scheduled_departure_utc<=(timestamp %s + interval '%s seconds') 
                                    AND (flights.departure_delay > 60 or flights.cancelled=1 )
                                    AND manifests.flight_number = flights.flight_number
                                    AND manifests.airline_code = flights.airline_code
                                    AND manifests.flight_date = DATE(flights.scheduled_departure_utc)
                                    AND flights.airline_code=%s 
                                GROUP BY flights.scheduled_departure_utc, flights.flight_number, flights.airline_code) as pass 
                    WHERE flights.airline_code = pass.airline_code 
                        AND flights.flight_number = pass.flight_number 
                        AND flights.scheduled_departure_utc=pass.scheduled_departure_utc 
                        AND flights.tail_number = airplanes.tail_number;"""
                        
        return self._resultAsList(query, (dStr, dStr, issueWindow, airline_code))
        
    def _resultAsList(self, query, vals):
        def _getResult(self, query, vals):
            cur = self.connection.cursor()
            cur.execute(query, vals)
            result = cur.fetchall()
            columns = cur.description
            cur.close()
            retList = []
            for record in result:
                recordDict = {}
                for idx, column in enumerate(columns):
                    key = column.name
                    val = record[idx]
                    if (type(val) == datetime):
                        val = str(val)
                    recordDict[key] = val
                retList.append(recordDict)
            return retList
        try:
            result = _getResult(self, query, vals)
        except (psycopg2.InterfaceError, psycopg2.OperationalError, psycopg2.DatabaseError) as e:
            print e
            print "DemoDatabase attempting to reconnect."
            self.disconnect()
            self._connect()
            result = _getResult(self, query, vals)
        
        return result    
    
    def __del__(self):
        self.disconnect()
    
class APIException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
        
class WatsonConversation(object):
    BASE_URL = "https://gateway.watsonplatform.net/conversation/api/v1/workspaces"
    VERSION_DATE = "2016-07-11"
    def __init__(self, workspaceIDs, username, password):
        self.username = username
        self.password = password
        self.workspaceIDs = workspaceIDs
    def send_message(self, context, message):
        lang = context["lang"]
        conversationURL = self.BASE_URL + "/" + self.workspaceIDs[lang] + "/message?version=" + self.VERSION_DATE
        if (len(context) > 0):
            payload = {"input": { "text": message }, "context": context }
        else:
            payload = {"input": { "text": message }}

        auth = HTTPBasicAuth(self.username, self.password)
        headers = {"Content-Type": "application/json"}
        r = requests.post(conversationURL, data=json.dumps(payload), auth=auth, headers=headers)
        r.raise_for_status()
        response = r.json()
        if ("context" not in response):
            raise APIException("Expected context missing from Conversation API response: %s" % (str(response),))
        if ("output" not in response) or ("text" not in response["output"]) or (len(response["output"]['text'])<1):
            raise APIException("Expected output missing from Conversation API response: %s" % (str(response),))            
        return (response["context"], response["output"]["text"][0])       