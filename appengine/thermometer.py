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
                    "date":"2014-09-26 12:34:56"
                }

        if len(records) == 1:
            record = records[0]

            response["temperature"] = record.temperature
            response["humidity"] = record.humidity
            response["date"] = record.date.isoformat(' ').split(".")[0]

        self.response.headers["Access-Control-Allow-Origin"] = "*"
        self.response.headers["Content-Type"] = "application/json"
        self.response.write(json.dumps(response))

class Thermometer(webapp2.RequestHandler):
    """Get or update DHTRecords (temperature/humidity/date)    
        GET 
            limit   (default=30)
                the number of returned records

        POST
            temp    (required)
                temperature
            humi    (required)
                humidity
            device  (required)
                this record is recorded by which device.
    """
    def get(self):
        limit = int(self.request.get('limit',30))

        if limit < 1:
            self.abort(403)
        
        records = DHTRecord.query().order(-DHTRecord.date).fetch(limit)

        response = []
        for record in records:
            response.append({
                "temperature":record.temperature,
                "humidity":record.humidity,
                "date" : record.date.isoformat(' ').split(".")[0]
                })

        self.response.headers["Access-Control-Allow-Origin"] = "*"
        self.response.headers["Content-Type"] = "application/json"
        self.response.write(json.dumps(response))

    def post(self):
        temp = self.request.get('temp')
        humi = self.request.get('humi')
        device = self.request.get('device')

        if len(temp) == 0 or len(humi) == 0 or len(device) == 0:
            self.abort(403)
        
        toCST = timedelta(hours=8)

        temp = float(temp)
        humi = float(humi)
    
        dht = DHTRecord(temperature=temp, humidity=humi,date=datetime.now()+toCST)
        dht.put()

        self.response.write(temp)
        self.response.write(humi)
        self.response.write(device)

#
#   Google AppEngine webapp2 Application
#
application = webapp2.WSGIApplication([
    ('/',MainPage),
    ('/thermometer',Thermometer),
    ('/current',Current)],debug=True)

