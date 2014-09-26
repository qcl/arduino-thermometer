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

class DHTRecord(ndb.Model):
    temperature = ndb.FloatProperty()
    humidity    = ndb.FloatProperty()
    date        = ndb.DateTimeProperty(auto_now_add=True)



#
class MainPage(webapp2.RequestHandler):
    def get(self):
        temp = 30

        template_values = {
            'temp':temp
        }

        template = JINJA_ENVIRONMENT.get_template("index.html")

        self.response.write(template.render(template_values))

class Current(webapp2.RequestHandler):
    """Get current (latest) temperature and humidity."""

    def get(self):
        records = DHTRecord.query().order(-DHTRecord.date).fetch(1)

        response = {
                    "temperature":0.0,
                    "humidity":0.0,
                    "date":"2014-09-26"
                }

        toCST = timedelta(hours=8)

        if len(records) == 1:
            record = records[0]

            response["temperature"] = record.temperature
            response["humidity"] = record.humidity
            response["date"] = (record.date + toCST).isoformat()

        self.response.write(json.dumps(response))

        

#
class Thermometer(webapp2.RequestHandler):
    
    #
    def get(self):
        # TODO
        pass

    # 
    def post(self):
        temp = self.request.get('temp')
        humi = self.request.get('humi')
        device = self.request.get('device')

        #if len(temp) == 0 or len(humi) == 0 or len(device) == 0:
        #    self.abort(403)

        temp = float(temp)
        humi = float(humi)
    
        dht = DHTRecord(temperature=temp, humidity=humi)
        dht.put()

        self.response.write(temp)
        self.response.write(humi)
        self.response.write(device)

#
application = webapp2.WSGIApplication([
    ('/',MainPage),
    ('/thermometer',Thermometer),
    ('/current',Current)],debug=True)

