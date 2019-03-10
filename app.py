from flask import Flask, render_template, redirect, url_for, jsonify
import requests
import json
from jsonschema import validate
from urllib.parse import urlparse
from uuid import uuid4
import hashlib
import copy
import markdown2
import humanize

app = Flask(__name__)


@app.context_processor
def utility_processor():
    def format_duration(duration):
        return humanize.naturaldelta(duration)

    return dict(format_duration=format_duration)


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
    projects = {
        "1": {
            "full_name": "Bracelet universel",
            "github_repository": "bracelet-universel",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Un bracelet pour les gouverner tous !",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/bracelet-universel/master/images/proto1.jpg",
            "cost": {"value": 23.626, "currency": "EUR"},
            "duration": 3600,
        },
        "2": {
            "full_name": "Pédale clavier souris",
            "github_repository": "pedale-clavier-souris",
            "github_organization": "myhumankit",
            "short_description": "Une pédale qui simule l'appui sur une touche de clavier ou sur la souris.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/pedale-clavier-souris/master/images/pedale-clavier-souris.jpg",
            "cost": {"value": 0, "currency": "EUR"},
            "duration": 2100,
        },
        "3": {
            "full_name": "Bouton train",
            "github_repository": "bouton-train",
            "github_organization": "myhumankit",
            "short_description": "Un simple bouton pour allumer un jouet pour enfant en forme de train.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/bouton-train/master/images/bouton-train.jpg",
            "cost": {"value": 0, "currency": "EUR"},
            "duration": 0,
        },
    }

    return render_template("index.html", projects=projects)


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "error.html", title="404 - Not found", error={"error": "404 - Not found"}
        ),
        404,
    )


def filling_json_file(organization, repository, file):
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
        tools = {}
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
                                    input["component"]["slug"],
                                )
                                if error:
                                    component = {
                                        "component": {"full_name": "Unknown component"}
                                    }
                                id = hashlib.md5(
                                    input["component"]["github_organization"].encode(
                                        "UTF-8"
                                    )
                                    + input["component"]["github_repository"].encode(
                                        "UTF-8"
                                    )
                                    + input["component"]["slug"].encode("UTF-8")
                                ).hexdigest()
                            else:
                                component, error = load_github_file(
                                    organization, repository, input["component"]["slug"]
                                )
                                if error:
                                    component = {
                                        "component": {"full_name": "Unknown component"}
                                    }
                                id = hashlib.md5(
                                    organization.encode("UTF-8")
                                    + repository.encode("UTF-8")
                                    + input["component"]["slug"].encode("UTF-8")
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

                            for key in ["quantity", "slug"]:
                                component["component"][key] = input["component"][key]

                            data["project"]["steps"][step_index]["inputs"][input_index][
                                "component"
                            ] = copy.deepcopy(component["component"])

                            data["project"]["steps"][step_index]["inputs"][input_index][
                                "component"
                            ]["id"] = id

                            if id in components:
                                # le composant est déjà dans la liste
                                components[id]["quantity"] = (
                                    components[id]["quantity"]
                                    + component["component"]["quantity"]
                                )
                            else:
                                components[id] = copy.deepcopy(component["component"])

                        if "tool" in input:
                            if ("github_repository" in input["tool"]) and (
                                "github_organization" in input["tool"]
                            ):
                                tool, error = load_github_file(
                                    input["tool"]["github_organization"],
                                    input["tool"]["github_repository"],
                                    input["tool"]["slug"],
                                )
                                if error:
                                    tool = {"tool": {"full_name": "Unknown tool"}}
                                id = hashlib.md5(
                                    input["tool"]["github_organization"].encode("UTF-8")
                                    + input["tool"]["github_repository"].encode("UTF-8")
                                    + input["tool"]["slug"].encode("UTF-8")
                                ).hexdigest()
                            else:
                                tool, error = load_github_file(
                                    organization, repository, input["tool"]["slug"]
                                )
                                if error:
                                    tool = {"tool": {"full_name": "Unknown tool"}}
                                id = hashlib.md5(
                                    organization.encode("UTF-8")
                                    + repository.encode("UTF-8")
                                    + input["tool"]["slug"].encode("UTF-8")
                                ).hexdigest()

                            # on ajoute les clés de l'outil input
                            if ("github_organization" in input["tool"]) and (
                                "github_repository" in input["tool"]
                            ):
                                tool["tool"]["github_organization"] = input["tool"][
                                    "github_organization"
                                ]
                                tool["tool"]["github_repository"] = input["tool"][
                                    "github_repository"
                                ]
                            else:
                                tool["tool"]["github_organization"] = organization
                                tool["tool"]["github_repository"] = repository

                            for key in ["slug"]:
                                tool["tool"][key] = input["tool"][key]

                            data["project"]["steps"][step_index]["inputs"][input_index][
                                "tool"
                            ] = copy.deepcopy(tool["tool"])

                            data["project"]["steps"][step_index]["inputs"][input_index][
                                "tool"
                            ]["id"] = id

                            if id not in tools:
                                # l'outil n'est pas encore dans la liste
                                tools[id] = copy.deepcopy(tool["tool"])

                        input_index += 1

                step_index += 1

        # total cost calculation
        value = 0
        currency = "EUR"
        for id in components:
            if "cost" in components[id]:
                if components[id]["cost"]["currency"] == currency:
                    value += (
                        components[id]["cost"]["value"] * components[id]["quantity"]
                    )
                elif components[id]["cost"]["currency"] == "USD":
                    value += (
                        0.89
                        * components[id]["cost"]["value"]
                        * components[id]["quantity"]
                    )

        # add computed datas to project datas
        data["project"]["computed"] = {
            "duration": duration,
            "cost": {"value": value, "currency": currency},
            "components": components,
            "tools": tools,
            # "skills": skills,
        }

    return data, 0


@app.route("/api/v1/<string:organization>/<string:repository>/<string:file>")
def project_details_file_json(organization, repository, file):

    # fill json with computed datas
    data, error = filling_json_file(organization, repository, file)

    if error:
        return (
            render_template("error.html", title="400 - Bad Request", error=error),
            400,
        )

    # project rendering
    return jsonify(data)


@app.route("/<string:organization>/<string:repository>")
def project_details(organization, repository):

    # fill json with computed datas
    data, error = filling_json_file(organization, repository, "project")

    if error:
        return (
            render_template("error.html", title="400 - Bad Request", error=error),
            400,
        )

    # transform markdown to html
    if "steps" in data["project"]:
        for step in data["project"]["steps"]:
            if "content" in step:
                step["content"] = markdown2.markdown(step["content"])

    # project rendering
    return render_template("project.html", project=data["project"])


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
