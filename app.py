from flask import Flask, render_template, redirect, url_for
import requests
import json
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.route('/<string:organisation>/<string:repository>')
def project_details(organisation, repository):

    base_url = "https://raw.githubusercontent.com/{0}/{1}/master/".format(organisation, repository)

    # download project description
    url = base_url + "project.json"
    r = requests.get(url)
    if r.status_code != 200:
        return redirect(url_for('index'))

    # parse json
    try:
        data = r.json()['data']
    except:
        return redirect(url_for('index'))

    if 'featured_image' in data:
        if 'url' in data['featured_image']:
            data['featured_image']['url'] = base_url + data['featured_image']['url']

    return render_template('project.html', data=data)
