# -*- coding: utf-8 -*-
# qcl's Arduino Thermometer
# Qing-Cheng Li
#
import os
import cgi
import json

import jinja2
import webapp2

from datetime import timedelta
from datetime import datetime
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

#
#   Models
#

class APIKey(ndb.Model):
    """API Keys, some API need it to prevent over quota."""
    key = ndb.StringProperty()

class DHTRecord(ndb.Model):
    """Record the `temperature' and `humidity' in `date'
        temperature : float
        humidity    : float
        date        : datetime.datetime
    """
    temperature = ndb.FloatProperty()
    humidity    = ndb.FloatProperty()
    date        = ndb.DateTimeProperty()




#
#   Views
#

class MainPage(webapp2.RequestHandler):
    def get(self):
        template_values = {
        }

        template = JINJA_ENVIRONMENT.get_template("index.html")

        self.response.write(template.render(template_values))

#
#   APIs
#

class Current(webapp2.RequestHandler):
    """Get current (latest) temperature and humidity.
        GET 
            return the latest DHTRecord as json
    """

    def get(self):
        records = DHTRecord.query().order(-DHTRecord.date).fetch(1)

        response = {
                    "temperature":0.0,
                    "humidity":0.0,
                    "date":"2014-09-26T12:34:56"
                }

        if len(records) == 1:
            record = records[0]

            response["temperature"] = record.temperature
            response["humidity"] = record.humidity
            response["date"] = record.date.isoformat(" ").split(".")[0]

        self.response.headers["Access-Control-Allow-Origin"] = "*"
        self.response.headers["Content-Type"] = "application/json"
        self.response.write(json.dumps(response))

class Thermometer(webapp2.RequestHandler):
    """Get or update DHTRecords (temperature/humidity/date)    
        GET 
            limit   (optional, default=30, max=1000)
                the number of returned records
            start   (optional)  [TODO]
                the start time of DHT records, format is YYYY-MM-DDTHH:MM:SS
            end     (optional)  [TODO]
                the end time of DHT records, format is YYYY-MM-DDTHH:MM:SS

        POST
            key     (required)
                API Key
            temp    (required)
                temperature
            humi    (required)
                humidity
            device  (required)
                this record is recorded by which device.
    """
    def get(self):
        # TODO - query by date range
        limit = int(self.request.get('limit',60))

        if limit < 1 or limit > 1000:
            self.abort(403)
        
        records = DHTRecord.query().order(-DHTRecord.date).fetch(limit)

        response = []
        for record in records:
            response.append({
                "temperature":record.temperature,
                "humidity":record.humidity,
                "date" : record.date.isoformat().split(".")[0]
                })

        response.reverse()

        self.response.headers["Access-Control-Allow-Origin"] = "*"
        self.response.headers["Content-Type"] = "application/json"
        self.response.write(json.dumps(response))

    def post(self):
        key  = self.request.get('key')
        temp = self.request.get('temp')
        humi = self.request.get('humi')
        device = self.request.get('device')

        if len(key) == 0 or len(temp) == 0 or len(humi) == 0 or len(device) == 0:
            self.abort(403)

        # Check API Key 
        apiKey = APIKey.query(APIKey.key == key).fetch(1)
        if len(apiKey) == 0:
            self.abort(403)

        toCST = timedelta(hours=8)

        temp = float(temp)
        humi = float(humi)
    
        dht = DHTRecord(temperature=temp, humidity=humi,date=datetime.now()+toCST)
        dht.put()

        self.response.headers["Content-Type"] = "application/json"
        self.response.write(json.dumps({"success":True,"data":{"humidity":humi,"temperature":temp,"device":device,"key":key}}))

#
#   Google AppEngine webapp2 Application
#
application = webapp2.WSGIApplication([
    ('/',MainPage),
    ('/thermometer',Thermometer),
    ('/current',Current)],debug=True)

