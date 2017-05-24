import json, signal, atexit, os
from flask import Flask, render_template, request, url_for, abort
from datetime import datetime
from misc_stuff import *
app = Flask(__name__)
demoNoSQL = DemoNoSQLDatabase()
#kafka = KafkaProducer()

#move this to external json
customers = {
    "delta": {
        "name": "Delta",
        "code": "DL",
        "css": "customer/delta-style.css",
        "loyaltyProgramName": "SkyMiles",
        "largeActivityThreshold": 100,
        "generic": 0
    },
    # "united": {
    #     "name": "United",
    #     "code": "UA",
    #     "css": "customer/united-style.css",
    #     "loyaltyProgramName": "MileagePlus",
    #     "largeActivityThreshold": 100,
    #     "generic": 0
    # },
    "american": {
        "name": "American",
        "code": "AA",
        "css": "customer/american-style.css",
        "loyaltyProgramName": "AAdvantage",
        "largeActivityThreshold": 70,
        "generic": 0
    },
    "southwest": {
        "name": "Southwest",
        "code": "WN",
        "css": "customer/southwest-style.css",
        "loyaltyProgramName": "Rapid Rewards",
        "largeActivityThreshold": 200,
        "generic": 0
    },
    "generic": {
        "name": "Agile",
        "code": "DL",
        "css": "customer/agile-style.css",
        "loyaltyProgramName": "Kanban Rewards",
        "largeActivityThreshold": 40,
        "generic": 1
    }
}
@app.route("/issue-dashboard/<airlineName>")
def issue_dashboard(airlineName):
    if (airlineName not in customers):
        return "Error: No customer '%s' defined." % (airlineName,)
    else:
        customer = customers[airlineName]
        demoNoSQL.delete_all_offers(customer["code"])
        mapPairs = demoDB.get_map_pairs(customer["code"])
        airports = demoDB.get_airports(customer["code"])
        return render_template('dashboard.html', customer=customer, mapPairs=mapPairs, airports=airports)

@app.route("/")
def list_airlines():
    customersCopy = customers.copy()
    del customersCopy['generic']
    return render_template('home.html', customers=customersCopy)
        
@app.route("/issues")
def issues():
    the_date = datetime.utcfromtimestamp(float(request.args.get('date')))
    the_window = int(request.args.get('window'))
    the_airline_code = request.args.get('airline_code')
    the_issues = demoDB.get_issues(the_date, the_window, the_airline_code)
    #fix time formatting to look like 2016-09-19T05:37:00 
    for issue in the_issues:
        issue['scheduled_departure_utc']=issue['scheduled_departure_utc'].replace(" ", "T")
        issue['scheduled_departure_local']=issue['scheduled_departure_local'].replace(" ", "T")
        print 
    return json.dumps(the_issues)

@app.route("/offers")
def offers():
    the_date = datetime.utcfromtimestamp(float(request.args.get('date', 0)))
    the_flight_number = int(request.args.get('flight_number', 0))
    the_airline_code = request.args.get('airline_code', "")
    is_generic = request.args.get('is_generic', 0)
    the_offers = demoNoSQL.get_offers(the_airline_code, the_flight_number, the_date)
    if (is_generic):
        for offer in the_offers:
            offer['flightAirlineName'] = customers['generic']['name']
    return json.dumps(the_offers)

@app.route("/currentPassengerBeingViewed")
def currentPassengerBeingViewed():
    return json.dumps(passengerBeingViewed)

passengerBeingViewed = { 'flightAirlineCode': '', 'passengerId': 0, 'flightDate': '1970-01-01', 'flightNumber':0 }
@app.route("/setCurrentPassengerBeingViewed")
def setCurrentPassengerBeingViewed():
    passengerBeingViewed['flightAirlineCode'] = request.args.get('airline_code', "")
    passengerBeingViewed['flightDate']  = datetime.utcfromtimestamp(float(request.args.get('date', 0))).strftime("%Y-%m-%d")
    passengerBeingViewed['flightNumber'] = int(request.args.get('flight_number', 0))
    passengerBeingViewed['passengerId'] = request.args.get('passenger_id', 0)
    return "{}"
    
#@app.route("/spark-talker")
#def spark_talker():
#    messageToSend = json.loads(request.args.get('message','{}'))
#    kafka.sendMessage(app.config['KAFKA_TOPIC'], messageToSend)
#    return "{}"

@app.route("/watson")
def watsonLastPassenger():
    return watson_talk("en", mostRecentPassenger)

@app.route("/watson/<language>/<passengerExceptionID>")
def watson_talk(language, passengerExceptionID):
    isGeneric = request.args.get('isGeneric', 0)
    return render_template('watson.html', passengerExceptionID=passengerExceptionID, language=language, isGeneric=isGeneric)

@app.route('/watson/message/<language>/<passengerExceptionID>', methods=['POST'])
def watson_message(language, passengerExceptionID):
    global mostRecentPassenger
    mostRecentPassenger = passengerExceptionID

    content = request.json
    message = content['message']
    context = content['context']
    is_generic = content['isGeneric']
    context['lang'] = language
    if 'passengerFile' not in context:
        passengerFile = demoNoSQL.get_offers_with_exception_id(passengerExceptionID)
        if (len(passengerFile) < 1):
            return json.dumps({"context": context, "response": "Couldn't find any offers for this passenger."})
        context['passengerFile'] = passengerFile[0]
        if (is_generic):
            context['passengerFile']['flightAirlineName'] = customers['generic']['name']
        tmp = [("<li>"+ a + "<button>Option " + str(idx+1) + "</button></li>") for idx, a in enumerate(context['passengerFile']['passengerOffers'])]
        context['passengerFile']['passengerOffersHTML'] = "<ul>" + ("\n".join(tmp)) + "</ul>"    
    try:
        context, response = watson.send_message(context, message)
    except APIException as e:
        print e
        context, response = watson.send_message({}, "no")

    return json.dumps({"context": context, "response": response})


if __name__ == "__main__":
    #set configuration stuff from environment variables
    app.config['DEBUG'] = True
    app.config['FLASK_PORT'] = int(os.getenv('FLASK_PORT', "5000"))
    app.config['POSTGRES_HOST'] = os.getenv('POSTGRES_HOST', "localhost")
    app.config['POSTGRES_DB_NAME'] = os.getenv('POSTGRES_DB_NAME', "airline-demo")
    app.config['POSTGRES_USER'] = os.getenv('POSTGRES_USER', "airline-demo")
    app.config['POSTGRES_PASSWORD'] = os.getenv('POSTGRES_PASSWORD', "IBMDem0s!")
    app.config['POSTGRES_PORT'] = int(os.getenv('POSTGRES_PORT', "5432"))
    app.config['MONGO_HOST'] = os.getenv('MONGO_HOST', "localhost")
    app.config['MONGO_DB_NAME'] = os.getenv('MONGO_DB_NAME', "airline-demo")
    app.config['MONGO_USER'] = os.getenv('MONGO_USER', "airline-demo")
    app.config['MONGO_PASSWORD'] = os.getenv('MONGO_PASSWORD', "IBMDem0s!")
    app.config['MONGO_PORT'] = int(os.getenv('MONGO_PORT', "27017"))
    app.config['KAFKA_TOPIC'] = os.getenv('KAFKA_TOPIC', "airline-demo-events")
    app.config['KAFKA_BOOTSTRAP_SERVERS'] = os.getenv('KAFKA_TOPIC', 'kafka01-prod01.messagehub.services.us-south.bluemix.net:9093, \
                                                                      kafka02-prod01.messagehub.services.us-south.bluemix.net:9093, \
                                                                      kafka03-prod01.messagehub.services.us-south.bluemix.net:9093, \
                                                                      kafka04-prod01.messagehub.services.us-south.bluemix.net:9093, \
                                                                      kafka05-prod01.messagehub.services.us-south.bluemix.net:9093')
    app.config['KAFKA_USER'] = os.getenv('KAFKA_USER', "")
    app.config['KAFKA_PASSWORD'] = os.getenv('KAFKA_PASSWORD', "")
    app.config['SSL_CERT_PATH'] = os.getenv('SSL_CERT_PATH', "/etc/ssl/certs")
    app.config['WATSON_CONVERSATION_USERNAME'] = os.getenv('WATSON_CONVERSATION_USERNAME', "")
    app.config['WATSON_CONVERSATION_PASSWORD'] = os.getenv('WATSON_CONVERSATION_PASSWORD', "")
    app.config['WATSON_CONVERSATION_WORKSPACE_ID'] = os.getenv('WATSON_CONVERSATION_WORKSPACE_ID', "")
    app.config['WATSON_CONVERSATION_WORKSPACE_ID_CN'] = os.getenv('WATSON_CONVERSATION_WORKSPACE_ID_CN', "")
    
    demoDB = DemoDatabase(  host=app.config['POSTGRES_HOST'], 
                            database=app.config['POSTGRES_DB_NAME'], 
                            user=app.config['POSTGRES_USER'], 
                            password=app.config['POSTGRES_PASSWORD'],
                            port=app.config['POSTGRES_PORT'])
    
    demoNoSQL.connect( host=app.config['MONGO_HOST'], 
                    database=app.config['MONGO_DB_NAME'], 
                    user=app.config['MONGO_USER'], 
                    password=app.config['MONGO_PASSWORD'],
                    port=app.config['MONGO_PORT'])
    
   
    workspaceIDs = {"en": app.config['WATSON_CONVERSATION_WORKSPACE_ID'],
                    "cn": app.config['WATSON_CONVERSATION_WORKSPACE_ID_CN']}
                    
    #kafka.connect(bootstrap_servers=app.config['KAFKA_BOOTSTRAP_SERVERS'], 
    #              ssl_cert_path = app.config['SSL_CERT_PATH'],
    #              username = app.config['KAFKA_USER'],
    #              password = app.config['KAFKA_PASSWORD'])
    watson = WatsonConversation(workspaceIDs, app.config['WATSON_CONVERSATION_USERNAME'], app.config['WATSON_CONVERSATION_PASSWORD'])
    mostRecentPassenger = "none"
    app.run(host='0.0.0.0', port=app.config['FLASK_PORT'], threaded=True, use_reloader=False)