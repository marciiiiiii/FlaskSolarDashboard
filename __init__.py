from flask import Flask, render_template, jsonify
import requests
from requests.exceptions import Timeout
import json
from apscheduler.schedulers.background import BackgroundScheduler 
from bokeh.plotting import figure, output_file, show
from bokeh.resources import CDN
from bokeh.models import AnnularWedge, ColumnDataSource, LabelSet
from bokeh.palettes import Category20c
from bokeh.embed import components
from math import pi
import pandas as pd
import numpy as np
from bokeh.transform import cumsum
from bokeh.themes import Theme
from bokeh.io import curdoc
from bokeh.models import BoxAnnotation

app = Flask(__name__, static_folder="FlaskSolar/.vscode/SolarInfo/static")


from SolarInfo import routes