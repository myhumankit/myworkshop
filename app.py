from flask import Flask, render_template, redirect, url_for, jsonify
import requests
import json
from jsonschema import validate
from urllib.parse import urlparse
from uuid import uuid4
import hashlib


app = Flask(__name__)


def absolute_url(document, base_url):
    """reads a 'url' key anywere in a json file and update it to a absolute url, if required"""
    if isinstance(document, list):
        i = 0
        for item in document:
            absolute_url(item, base_url)
            i += 1
    elif isinstance(document, dict):
        for k in document.keys():
            if k == "url":
                o = urlparse(document[k])
                if not o.scheme:
                    document[k] = base_url + document[k]
            else:
                absolute_url(document[k], base_url)


def load_github_file(
    organization, repository, file_name, force_validate=True, to_absolute_url=True
):
    """download a json file, check if it validate JSON SCHEMA and replace all relative urls to absolute ones"""
    base_url = "https://raw.githubusercontent.com/{0}/{1}/master/".format(
        organization, repository
    )
    full_file_name = file_name + ".json"
    url = base_url + full_file_name
    r = requests.get(url)
    if r.status_code != 200:
        return {}, {"error": "File not found."}

    # parse json
    try:
        data = r.json()
    except:
        return {}, {"error": "Invalid JSON file"}

    # validate the source according to JSON SCHEMA
    if force_validate:
        # load project's json schema
        with open("project.json", "r") as file:
            json_schema = json.load(file)

        try:
            validate(data, json_schema)
        except Exception as valid_err:
            return (
                {},
                {
                    "error": "Invalid JSON file according to JSON SCHEMA",
                    "message": valid_err,
                },
            )

    # update relative urls to absolute urls
    if to_absolute_url:
        absolute_url(data, base_url)

    return data, 0


def component_complete(component, components_library):
    """Try to complete components caracteristics from components library"""
    if "id" in component:
        for reference_component in components_library["components"]:
            if component["id"] == reference_component["id"]:
                return dict(
                    reference_component, **component
                )  # remplace les clés présentes dans reference_component par celles de component si elles existent
    default_component = {"name": "composant inconnu", "id": str(uuid4()), "quantity": 1}
    return dict(default_component, **component)


@app.route("/")
def index():
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "error.html", title="404 - Not found", error={"error": "404 - Not found"}
        ),
        404,
    )


@app.route("/api/v1/<string:organization>/<string:repository>/<string:file>")
def project_details_file_json(organization, repository, file):
    # load project datas
    data, error = load_github_file(organization, repository, file)
    if error:
        return (
            render_template("error.html", title="400 - Bad Request", error=error),
            400,
        )

    # if project -> some datas are computed
    if "project" in data:
        duration = 0
        components = {}
        tools = []
        # skills = []

        if "steps" in data["project"]:
            step_index = 0
            for step in data["project"]["steps"]:
                # calculation of cumulative duration
                if "duration" in step:
                    duration += step["duration"]

                # on complete les informations sur les inputs
                if "inputs" in step:
                    input_index = 0
                    for input in step["inputs"]:
                        if "component" in input:
                            # on récupère le composant cible
                            if ("github_repository" in input["component"]) and (
                                "github_organization" in input["component"]
                            ):
                                component, error = load_github_file(
                                    input["component"]["github_organization"],
                                    input["component"]["github_repository"],
                                    input["component"]["id"],
                                )
                                if error:
                                    component = {"component": {"full_name": "Unknown"}}
                                id = hashlib.md5(
                                    input["component"]["github_organization"].encode(
                                        "UTF-8"
                                    )
                                    + input["component"]["github_repository"].encode(
                                        "UTF-8"
                                    )
                                    + input["component"]["id"].encode("UTF-8")
                                ).hexdigest()
                            else:
                                component, error = load_github_file(
                                    organization, repository, input["component"]["id"]
                                )
                                if error:
                                    component = {"component": {"full_name": "Unknown"}}
                                id = hashlib.md5(
                                    organization.encode("UTF-8")
                                    + repository.encode("UTF-8")
                                    + input["component"]["id"].encode("UTF-8")
                                ).hexdigest()

                            # on ajoute les clés du composant input
                            if ("github_organization" in input["component"]) and (
                                "github_repository" in input["component"]
                            ):
                                component["component"]["github_organization"] = input[
                                    "component"
                                ]["github_organization"]
                                component["component"]["github_repository"] = input[
                                    "component"
                                ]["github_repository"]
                            else:
                                component["component"][
                                    "github_organization"
                                ] = organization
                                component["component"]["github_repository"] = repository

                            for key in ["quantity", "id"]:
                                component["component"][key] = input["component"][key]

                            data["project"]["steps"][step_index]["inputs"][input_index][
                                "component"
                            ] = component

                            if id in components:
                                # le composant est déjà dans la liste
                                components[id]["quantity"] += component["component"][
                                    "quantity"
                                ]
                            else:
                                components[id] = component["component"]

                            # c = {}
                            # c.update(component)
                            # c.update(input)

                            # c = {**input, **component}
                            # component["component"]["quantity"] = input["component"]["quantity"]

                            # components[id] = component["component"]

                            # components.append(component)
                        if "tool" in input:
                            # data["project"]["steps"][step_index]["inputs"][input_index]["tool"] = '{"bingo"}'
                            tools.append(
                                data["project"]["steps"][step_index]["inputs"][
                                    input_index
                                ]["tool"]
                            )
                        input_index += 1

                step_index += 1

            # calculation of the B.O.M.

            # calculation of the required skills

        # add computed datas to project datas
        data["project"]["computed"] = {
            "duration": duration,
            "components": components,
            "tools": tools,
            # "skills": skills,
        }

    # project rendering
    return jsonify(data)


@app.route("/<string:organization>/<string:repository>")
def project_details(organization, repository):
    # load project datas
    project, error = load_github_file(organization, repository, "project")
    if error:
        return (
            render_template("error.html", title="400 - Bad Request", error=error),
            400,
        )

    # load local libraries
    components_library, error = load_github_file(organization, repository, "components")
    if error:
        components_library = {"components": []}

    # some datas are computed
    duration = 0
    components = []
    skills = []

    if "steps" in project["project"]:
        step_index = 0
        for step in project["project"]["steps"]:
            # calculation of cumulative duration
            if "duration" in step:
                duration += step["duration"]

            # on complete les informations sur les composants par ceux issus de la librairie
            if "components" in step:
                component_index = 0
                for component in step["components"]:
                    project["project"]["steps"][step_index]["components"][
                        component_index
                    ] = component_complete(component, components_library)
                    component_index += 1

            step_index += 1

        # calculation of the B.O.M.
        for step in project["project"]["steps"]:
            if "components" in step:
                for component in step["components"]:
                    components.append(component)

        # calculation of the required skills
        for step in project["project"]["steps"]:
            if "skills" in step:
                for skill in step["skills"]:
                    skills.append(skill)

    # add computed datas to project datas
    project["project"]["computed"] = {
        "duration": duration,
        "components": components,
        "skills": skills,
    }

    # project rendering
    return render_template("project.html", project=project["project"])


@app.route("/<string:organization>/<string:repository>/<string:file>/edit")
def project_details_edit(organization, repository, file):

    # load project datas
    project, error = load_github_file(
        organization, repository, file, to_absolute_url=False
    )
    if error:
        return (
            render_template("error.html", title="400 - Bad Request", error=error),
            400,
        )

    # load project's json schema
    with open("project.json", "r") as file:
        json_schema = json.load(file)

    # project rendering
    return render_template(
        "project_edit.html",
        project=json.dumps(project),
        json_schema=json.dumps(json_schema),
    )


@app.route("/new")
def project_details_new():

    # load project's json schema
    with open("project.json", "r") as file:
        json_schema = json.load(file)

    # project rendering
    return render_template(
        "project_edit.html",
        project='{"project":{}}',
        json_schema=json.dumps(json_schema),
    )
