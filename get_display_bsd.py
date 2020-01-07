import cherrypy
import os.path
import redis
import pickle
import json
import csv
import sys
import io
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import datetime
from datetime import date,timedelta
import requests
from io import BytesIO
from zipfile import ZipFile
env = Environment(loader=FileSystemLoader('templates'))


class getDisplayBSD:
    def get_csv(self,url,filename):
        r = requests.get(url+filename, stream =True)
        try:
            z = ZipFile(io.BytesIO(r.content))
            z.extractall()
        except:
            return -1
        pass
        return True

    def read_csv_data(self,csv_file, sc_code, sc_name, Open, high, low, close):
        with open(csv_file, encoding='utf-8') as csvf:
            csv_data = csv.reader(csvf)
            next(csv_data, None)
            return [(r[sc_code], r[sc_name], r[Open], r[high], r[low], r[close]) for r in csv_data]

    def store_data(self,conn, data):
        
        for i in data:
            conn.setnx(i[0], i[1])
        return data

    def index(self):
        print("in INDEX")
        conn = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=10)
        print(conn)
        outdata = []
        columns = (0, 1,2,3,4,5) if len(sys.argv) < 4 else (int(x) for x in sys.argv[2:5])
        dt = pd.date_range(start=datetime.date.today()- timedelta(days = 2), periods=10, freq='B')

        if datetime.date.today() in dt:
            latestDate = datetime.date.today().strftime("%d%m%y")
        else:
            latestDate = dt.min().strftime("%d%m%y")
        url = "https://www.bseindia.com/download/BhavCopy/Equity/"
        #EQ131219_CSV.ZIP
        filename = "EQ"+latestDate+"_CSV.ZIP"
        file = "EQ"+latestDate+".CSV"
        fileGenerate = self.get_csv(url,filename)
        if fileGenerate:
            if fileGenerate == -1:
                updatedDate = datetime.date.today()- timedelta(days = 1)
                dateFormatted = updatedDate.strftime("%d%m%y")
                filename = "EQ"+dateFormatted+"_CSV.ZIP"
                file = "EQ"+dateFormatted+".CSV"
                fileGenerate = self.get_csv(url,filename)
            columns = (0,1,4,5,6,7) if len(sys.argv) < 4 else (int(x) for x in sys.argv[2:4])
            data = self.read_csv_data(file,*columns)
        tmpl = env.get_template('index.html')
        return tmpl.render(list=json.dumps(self.store_data(conn, data)))

    index.exposed = True

configfile = os.path.join(os.path.dirname(__file__),'server.conf')
print(configfile)
cherrypy.config.update({
    'server.socket_host':'0.0.0.0',
    'server.socket_port': 80, # default port is 8080 you can chage default port number here
})
cherrypy.quickstart(getDisplayBSD(),config = configfile)
