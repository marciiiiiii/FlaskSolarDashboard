from bokeh.core.property.dataspec import value
from bokeh.models.annotations import Label, Title
from SolarInfo import app
from flask import render_template
import requests
from requests.exceptions import Timeout
import json
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.models import AnnularWedge, ColumnDataSource, LabelSet
from bokeh.palettes import Category20c
from math import pi
import pandas as pd
import numpy as np
from bokeh.transform import cumsum
from bokeh.themes import Theme
from bokeh.io import curdoc
from bokeh.models import BoxAnnotation

#routes verkörpern die einzelnen Websites 
#zuerst kommt ganz allgemein @app.route('/') -> darunter können belibig viele andere erstellt werden z.B. homepage, About page etc.
@app.route('/')
@app.route('/home', methods=['GET', 'POST']) #get und post method um daten anzufragen (für meine Anfrage eigentlich nur Post nötig)
def home_page():

        #Funktion für Post request wird für alle webserver ausgeführt -> dictionary wird zurückgegeben, dann wird in dictionary nach benötigtem wert gesucht
        datenWr1 = post_request('http://192.168.1.38/solar_api/v1/GetInverterRealtimeData.cgi?Scope=Device&DeviceID=1&DataCollection=CommonInverterData')
        wr1 = datenWr1['Body']['Data']['PAC']['Value'] 

        datenWr2 = post_request('http://192.168.1.37/solar_api/v1/GetInverterRealtimeData.cgi?Scope=Device&DeviceID=1&DataCollection=CommonInverterData')
        wr2 = datenWr2['Body']['Data']['PAC']['Value'] 

        wrges = wr1 + wr2
        
        #request funktion für SmartPi (summierter Wert zurückgegeben)
        smartPi = get_smartPi('http://192.168.1.31:1080/api/1/power/now','http://192.168.1.31:1080/api/2/power/now','http://192.168.1.31:1080/api/3/power/now')
        immerPositivPi, anzeigetextPi = SmartPiWert(smartPi)

        #Funkrion zur berechnung Eigenverbrauch
        Eigenverbrauch = ber_Eigenverbr(wr1, wr2, smartPi)

        #AUsgabe der benötigten Datein für Bokeh Chart (script, html, css, JS)

        #Bokeh Donut wechselrichter
        donutWr = donutChart(wrges, 20000)
        scriptWr, divWr = components(donutWr)
        cdn_js_Wr = CDN.js_files[0]
        cdn_css_Wr = CDN.css_files

        #Bokeh Donut Eigenverbrauch
        donutEig = donutChart(Eigenverbrauch, 10000)
        scriptEig, divEig = components(donutEig)
        cdn_js_Eig = CDN.js_files[0]
        cdn_css_Eig = CDN.css_files

        #Bokeh Donut SmartPi
        donutSmart = donutChart(immerPositivPi, 20000)
        scriptSmart, divSmart = components(donutSmart)
        cdn_js_Smart = CDN.js_files[0]
        cdn_css_Smart = CDN.css_files


        #erste roue Funktion rendert das home.html tmplate und gibt alle benötgten Werte weiter
        return render_template('home.html', response=smartPi, AnzeigetextPi = anzeigetextPi,
                                scriptchartWr = scriptWr, divchartWr = divWr, cdn_css_Wr = cdn_css_Wr, cdn_js_Wr = cdn_js_Wr, #Donut Wechselrichter
                                scriptchartEig = scriptEig, divchartEig = divEig, cdn_css_Eig = cdn_css_Eig, cdn_js_Eig = cdn_js_Eig,  #Donut Eigenverbrauch
                                scriptchartSmart = scriptSmart, divchartSmart = divSmart, cdn_css_Smart = cdn_css_Smart, cdn_js_Smart = cdn_js_Smart
                                ) 
   
#berechnung des Eigenverbrauchs (wechselrichter 1+2 + Smart Pi wert (kann auch negativ sein))
def ber_Eigenverbr(wr1, wr2, SmartPi):
    Eigenverbrauch = None

    Eigenverbrauch = wr1+wr2+(SmartPi)
    return Eigenverbrauch 

#post request in Fehlerbehandlung (try, expect)
#1. request url (timeout nach 3.05 sec)
#2. rückgabe wird in textdatei gewandelt
#3. json.loads gibt dictionary zurück (kann durchsucht werden) -> dieser Wert wird ausgegeben 
def post_request(url):
    try: 
        response = requests.post(url, timeout=3.05)
        Jresponse = response.text
        json_dict = json.loads(Jresponse)
    except requests.exceptions.RequestException:
        json_dict = None
    
    return json_dict

# SmartPi daten werden angefragt und summiert
#1. alle 3 Werte für SmartPi anfragen(3 Phasen)
#2. Daten aus zurückgegebenen Dictionary filtern ([0]->enthaltene Liste im dictionary ['dataset']-> dictionary kann nach strings durchsucht werden)
#3. summieren der Werte -> Rückgabe eines gesamten Wertes
def get_smartPi(url1, url2, url3):
    smartPi = None

    datenSmartPi1 = post_request(url1)
    datenSmartPi2 = post_request(url2)
    datenSmartPi3 = post_request(url3)
    
    smartPi1 = datenSmartPi1['datasets'][0]['phases'][0]['values'][0]['data']
    smartPi2 = datenSmartPi2['datasets'][0]['phases'][0]['values'][0]['data']
    smartPi3 = datenSmartPi3['datasets'][0]['phases'][0]['values'][0]['data']

    smartPi = smartPi1+smartPi2+smartPi3

    return round(smartPi,2)

#Donut Diagramm mit Bokeh erstellt
def donutChart(wert, max):
    wertGes = wert
    wertRest = max - wertGes

    

    chart_colors = ['#B36F60', '#D4CECD']


    x = {
        'Wert' : round(wertGes,2),
        'freie Kapazität' : round(wertRest,2)
        }
    R = 0.4
    data = (pd.Series(x)
            .reset_index(name='value')
            .rename(columns={'index': 'Power'})
            .assign(end_angle=lambda d: np.cumsum(d['value'] / d['value'].sum() * 2 * pi),
                    start_angle=lambda d: np.pad(d['end_angle'], (1, 0))[:-1],  #np.pad -> array wird erweitert, sodass es mit dem array [end_angle]übereinstimmt
                    color=chart_colors[:len(x)],
                    label_x=lambda d: R * 1.0 * np.cos(d['start_angle']),
                    label_y=lambda d: R * 0.8 * np.sin(d['start_angle'])))
    
    source = ColumnDataSource(data)

    p_range = (-R * 1.2, R * 1.2)
    p_size = 500

    p = figure(plot_height=p_size, plot_width=p_size, toolbar_location=None,
            x_range=p_range, y_range=p_range,
            tools="hover", tooltips="@Power: @value")

    for r in [p.xaxis, p.yaxis, p.grid]:
        r.visible = False
    
    p.annular_wedge(x=0, y=0, inner_radius=0.15, outer_radius=0.25,
        start_angle='start_angle', end_angle='end_angle',
        line_color="white", fill_color='color', source=source, direction="anticlock")

    # lable_prozent = value/wrges *100 

    p.add_layout (  Label(x=0, y=0, x_offset= 0,y_offset= -5, text=str(round(wertGes)), text_align='center', text_font_size='24px', text_font_style='normal', text_color = '#FFFFFF', render_mode='canvas'))
    curdoc().theme = Theme('SolarInfo/static/themes/theme.yaml')
    curdoc().add_root(p)
    
    return p

def SmartPiWert(smartPi):
    

    if smartPi <= 0:
        s = smartPi * -1
        text = "Eingespeiste Energie"
    
    else:
        s = smartPi
        text = " gezogene Energie aus Stromnetz"



    return s, text
