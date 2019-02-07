from flask import Flask, render_template, redirect, url_for
import requests
import json
from jsonschema import validate
from urllib.parse import urlparse
from uuid import uuid4

app = Flask(__name__)


def load_github_file(organisation, repository, file_name):
    # download file
    base_url = "https://raw.githubusercontent.com/{0}/{1}/master/".format(organisation, repository)
    full_file_name = file_name + '.json'
    url = base_url + full_file_name
    r = requests.get(url)
    if r.status_code != 200:
        return {}, {'error': 'File not found.'}

    # parse json
    try:
        data = r.json()
    except:
        return {}, {'error': 'Invalid JSON file'}

    with open(full_file_name, "r") as file:
        json_schema = json.load(file)

    # validate the source according to JSON SCHEMA
    try:
        validate(data, json_schema)
    except Exception as valid_err:
        return {}, {'error': 'Invalid JSON file according to JSON SCHEMA', 'message': valid_err}

    data['base_url'] = base_url
    return data, 0


def component_complete(component, components_library):
    """Try to complete components caracteristics from components library"""
    if 'id' in component:
        for reference_component in components_library['components']:
            if component['id'] == reference_component['id']:
                return dict(reference_component, **component) # remplace les clés présentes dans reference_component par celles de component si elles existent
    default_component = {
        'name': 'composant inconnu',
        'id': str(uuid4()),
        'quantity': 1
    }
    return dict(default_component, **component)


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
    return render_template('error.html', title='404 - Not found', error={'error': '404 - Not found'}), 404


@app.route('/<string:organisation>/<string:repository>')
def project_details(organisation, repository):
    # load project datas
    project, error = load_github_file(organisation, repository, 'project')
    if error:
        return render_template('error.html', title='400 - Bad Request', error=error), 400

    # load local libraries
    components_library, error = load_github_file(organisation, repository, 'components')
    if error:
        components_library = {"components": []}

    # some datas are computed
    duration = 0
    components = []
    skills = []

    if 'steps' in project['project']:
        step_index = 0
        for step in project['project']['steps']:
            # calculation of cumulative duration
            if 'duration' in step:
                duration += step['duration']

            # on complete les informations sur les composants par ceux issus de la librairie
            if 'components' in step:
                component_index = 0
                for component in step['components']:
                    project['project']['steps'][step_index]['components'][component_index] = component_complete(component, components_library)
                    component_index += 1

            step_index += 1

        # calculation of the B.O.M.
        for step in project['project']['steps']:
            if 'components' in step:
                for component in step['components']:
                    components.append(component)

        # calculation of the required skills
        for step in project['project']['steps']:
            if 'skills' in step:
                for skill in step['skills']:
                    skills.append(skill)


    # add computed datas to project datas
    project['project']['computed'] = {
        "duration": duration,
        "components": components,
        "skills": skills
    }

    project['project']['base_url'] = project['base_url']

    # project rendering
    return render_template('project.html', project=project['project'])
