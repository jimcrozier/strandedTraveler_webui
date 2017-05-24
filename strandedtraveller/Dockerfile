FROM ubuntu:latest
MAINTAINER Adam Johnson "adam.johnson@us.ibm.com"
RUN apt-get update -y
RUN apt-get install -y wget software-properties-common python-software-properties
RUN wget -qO - http://packages.confluent.io/deb/3.0/archive.key | apt-key add -
RUN add-apt-repository "deb [arch=amd64] http://packages.confluent.io/deb/3.0 stable main"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential libpq-dev ca-certificates librdkafka-dev librdkafka1
RUN apt-get purge --auto-remove -y wget software-properties-common python-software-properties
RUN update-ca-certificates
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]