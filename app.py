from flask import Flask, render_template, redirect, url_for
import requests
import json
from jsonschema import validate
from urllib.parse import urlparse

app = Flask(__name__)

@app.context_processor
def utility_processor():
    def format_url(url, base_url):
        """Tranform a local url to a global url, if required."""
        o = urlparse(url)
        if not o.scheme:
            return base_url + url
        else:
            return url
    return dict(format_url=format_url)

@app.route("/")
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    #return render_template('404.html'), 404
    return render_template('error.html', title='404 - Not found', details='404 - Not found'), 404

@app.route('/<string:organisation>/<string:repository>')
def project_details(organisation, repository):

    base_url = "https://raw.githubusercontent.com/{0}/{1}/master/".format(organisation, repository)

    # download project description
    url = base_url + "project.json"
    r = requests.get(url)
    if r.status_code != 200:
        return render_template('error.html', title='400 - Bad Request', details='Project not found.'), 400

    # parse json
    try:
        data = r.json()
    except:
        return render_template('error.html', title='400 - Bad Request', details='The source file is not a valid JSON.'), 400

    with open("./project.json", "r") as file:
        json_schema = json.load(file)

    # validate the source according to JSON SCHEMA
    try:
        validate(data, json_schema)
    except Exception as valid_err:
        return render_template('error.html', title='400 - Bad Request', details='The source file is not a valid JSON.', message=valid_err), 400

    # project rendering
    return render_template('project.html', project=data['project'], base_url=base_url)
