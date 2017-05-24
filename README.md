This repository contains the web app portion of the IBM Stranded Traveller demonstration, a sales asset for the Travel & Transportation vertical in the Distribution industry. The primary component is a Flask application `app.py`.

**Building**
`$ docker build -t strandedtraveller strandedtraveller/`

**Option A: Running Locally**
`docker run -p 5000:5000 -e POSTGRES_HOST='postgres.example.org' -e MONGO_HOST='mongo.example.org' -e KAFKA_USER='<user>' -e KAFKA_PASSWORD='<pass>' strandedtraveller'`

**Option B: Run on IBM Bluemix**
`docker tag strandedtraveller registry.ng.bluemix.net/<your_namespace>/strandedtraveller
docker push registry.ng.bluemix.net/<your_namespace>/strandedtraveller
cf ic run -p <assigned-ip>:80:80 -m 1024 -e POSTGRES_HOST='postgres.example.org' -e MONGO_HOST='mongo.example.org' -e KAFKA_USER='<user>' -e KAFKA_PASSWORD='<pass>' -e FLASK_PORT=80 registry.ng.bluemix.net/<your_namespace>/strandedtraveller`

**Environment Variables**
These environment variables are used to configure the container. For each variable, the default value is given; if the given value is appropriate then there is no need to set that variable.
`FLASK_PORT="5000"
POSTGRES_HOST="localhost"
POSTGRES_DB_NAME="airline-demo"
POSTGRES_USER="airline-demo"
POSTGRES_PASSWORD="IBMDem0s!"
POSTGRES_PORT="5432"
MONGO_HOST="localhost"
MONGO_DB_NAME="airline-demo"
MONGO_USER="airline-demo"
MONGO_PASSWORD="IBMDem0s!"
MONGO_PORT="27017"
KAFKA_TOPIC="airline-demo-events"
KAFKA_BOOTSTRAP_SERVERS = "kafka01-prod01.messagehub.services.us-south.bluemix.net:9093, kafka02-prod01.messagehub.services.us-south.bluemix.net:9093, kafka03-prod01.messagehub.services.us-south.bluemix.net:9093, kafka04-prod01.messagehub.services.us-south.bluemix.net:9093, kafka05-prod01.messagehub.services.us-south.bluemix.net:9093"
KAFKA_USER=""
KAFKA_PASSWORD=""
WATSON_CONVERSATION_USERNAME=""
WATSON_CONVERSATION_PASSWORD=""
WATSON_CONVERSATION_WORKSPACE_ID=""
WATSON_CONVERSATION_WORKSPACE_ID_CN=""`

**Created By**
Hans Uhlig
Brian Dragunas
Adam Johnson