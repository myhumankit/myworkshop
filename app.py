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
from flask_caching import Cache
from material.material_app import (
    profile_to_component,
    sheet_to_component,
    cleat_to_component,
    screw_to_component,
    nut_to_component,
    washer_to_component,
)

app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "simple"})
cache_timeout = 60  # 60 seconds = 1 minute

markdownExtra = {
    "tables": True,
    "break-on-newline": True,
    "html-classes": {"table": "table table-striped"},
}


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


@cache.memoize(timeout=cache_timeout)
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
@cache.cached(timeout=cache_timeout)
def index():
    projects = {
        "1": {
            "full_name": "Tenture interactive",
            "github_repository": "tenture-interactive",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Tenture interactive pour inciter un enfant atteint de trouble de spectre autistique léger (TSA) à dormir dans sa chambre en instituant un rituel du coucher.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/tenture-interactive/master/images/tenture-finale.jpg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "2": {
            "full_name": "Support de bras anti gravité",
            "github_repository": "support-de-bras-anti-gravite",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Construire un support articulé permettant à une personne en fauteuil ayant une très faible tonicité musculaire du bras gauche d'en changer la position sans l'aide d'un tiers.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/support-de-bras-anti-gravite/master/images/Bras_antiG_pic1.jpeg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "3": {
            "full_name": "La main à l'oreille",
            "github_repository": "la-main-a-loreille",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Un dispositif sonore interactif à base de tags NFC et de lecteur MP3.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/la-main-a-loreille/master/images/la-main-a-loreille.jpg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "4": {
            "full_name": "Arceau de lit de voyage",
            "github_repository": "arceau-de-lit-de-voyage",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Concevoir et réaliser un arceau de lit pour le voyage, dont la particularité est d'être facilement transportable et qui doit être pliable et/ou démontable.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/arceau-de-lit-de-voyage/master/images/Arceau-en-situation-1.jpg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "5": {
            "full_name": "Té-usb",
            "github_repository": "te-usb",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "C'est un projet visant à créer un câble usb permettant à un téléphone portable d'être chargé par une batterie externe en même temps qu'utilisé avec une souris pour être piloté par un dispositif de contrôle.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/te-usb/master/images/IMG_3905.JPG",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "6": {
            "full_name": "Prise connectée",
            "github_repository": "prise-connectee",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Détournement d’une prise connectée Sonoff. Munie d’un microcontrôleur de type ESP8266, cette prise peut être reprogrammée à l’aide de l’IDE Arduino pour être pilotée en Wifi.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/prise-connectee/master/images/prise-connectee.jpg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "7": {
            "full_name": "Station de documentation",
            "github_repository": "station-de-documentation",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Une boite à lumière, sur une table réglable en hauteur, pour faciliter la documentation des projets du Humanlab.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/station-de-documentation/master/images/station-de-documentation.jpg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "8": {
            "full_name": "Bracelet universel",
            "github_repository": "bracelet-universel",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Un bracelet pour les gouverner tous !",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/bracelet-universel/master/images/proto1.jpg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "9": {
            "full_name": "Pédale clavier souris",
            "github_repository": "pedale-clavier-souris",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Une pédale qui simule l'appui sur une touche de clavier ou sur la souris.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/pedale-clavier-souris/master/images/pedale-clavier-souris.jpg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
        "10": {
            "full_name": "Bouton train",
            "github_repository": "bouton-train",
            "github_organization": "myhumankit",
            "license": "CC BY",
            "short_description": "Un simple bouton pour allumer un jouet pour enfant en forme de train.",
            "featured_image": "https://raw.githubusercontent.com/myhumankit/bouton-train/master/images/bouton-train.jpg",
            "cost": {"value": 0.0, "currency": "EUR"},
            "duration": 0,
        },
    }

    return render_template("index.html", projects=projects)


@app.errorhandler(404)
@cache.cached(timeout=cache_timeout)
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
                                        "component": {
                                            "full_name": "??? "
                                            + input["component"]["slug"]
                                        }
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
                                        "component": {
                                            "full_name": "??? "
                                            + input["component"]["slug"]
                                        }
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
                                    tool = {
                                        "tool": {
                                            "full_name": "??? " + input["tool"]["slug"]
                                        }
                                    }
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
                                    tool = {
                                        "tool": {
                                            "full_name": "??? " + input["tool"]["slug"]
                                        }
                                    }
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

                        if "profile" in input:
                            component, component_item, id = profile_to_component(
                                input["profile"]
                            )

                            step["inputs"][input_index] = component

                            if id in components:
                                # le composant est déjà dans la liste
                                components[id]["quantity"] = (
                                    components[id]["quantity"]
                                    + component_item["component"]["quantity"]
                                )
                            else:
                                components[id] = copy.deepcopy(
                                    component_item["component"]
                                )

                        if "sheet" in input:
                            component, component_item, id = sheet_to_component(
                                input["sheet"]
                            )

                            step["inputs"][input_index] = component

                            if id in components:
                                # le composant est déjà dans la liste
                                components[id]["quantity"] = (
                                    components[id]["quantity"]
                                    + component_item["component"]["quantity"]
                                )
                            else:
                                components[id] = copy.deepcopy(
                                    component_item["component"]
                                )

                        if "cleat" in input:
                            component, component_item, id = cleat_to_component(
                                input["cleat"]
                            )

                            step["inputs"][input_index] = component

                            if id in components:
                                # le composant est déjà dans la liste
                                components[id]["quantity"] = (
                                    components[id]["quantity"]
                                    + component_item["component"]["quantity"]
                                )
                            else:
                                components[id] = copy.deepcopy(
                                    component_item["component"]
                                )

                        if "screw" in input:
                            component, component_item, id = screw_to_component(
                                input["screw"]
                            )

                            step["inputs"][input_index] = component

                            if id in components:
                                # le composant est déjà dans la liste
                                components[id]["quantity"] = (
                                    components[id]["quantity"]
                                    + component_item["component"]["quantity"]
                                )
                            else:
                                components[id] = copy.deepcopy(
                                    component_item["component"]
                                )

                        if "nut" in input:
                            component, component_item, id = nut_to_component(
                                input["nut"]
                            )

                            step["inputs"][input_index] = component

                            if id in components:
                                # le composant est déjà dans la liste
                                components[id]["quantity"] = (
                                    components[id]["quantity"]
                                    + component_item["component"]["quantity"]
                                )
                            else:
                                components[id] = copy.deepcopy(
                                    component_item["component"]
                                )

                        if "washer" in input:
                            component, component_item, id = washer_to_component(
                                input["washer"]
                            )

                            step["inputs"][input_index] = component

                            if id in components:
                                # le composant est déjà dans la liste
                                components[id]["quantity"] = (
                                    components[id]["quantity"]
                                    + component_item["component"]["quantity"]
                                )
                            else:
                                components[id] = copy.deepcopy(
                                    component_item["component"]
                                )

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
@cache.cached(timeout=cache_timeout)
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
@cache.cached(timeout=cache_timeout)
def project_details(organization, repository):

    # fill json with computed datas
    data, error = filling_json_file(organization, repository, "project")

    if error:
        return (
            render_template("error.html", title="400 - Bad Request", error=error),
            400,
        )

    # transform markdown to html
    if "about" in data["project"]:
        data["project"]["about"] = markdown2.markdown(
            data["project"]["about"], extras=markdownExtra
        )

    if "steps" in data["project"]:
        for step in data["project"]["steps"]:
            if "content" in step:
                step["content"] = markdown2.markdown(
                    step["content"], extras=markdownExtra
                )

    # project rendering
    return render_template("project.html", project=data["project"])


@app.route("/<string:organization>/<string:repository>/<string:file>/edit")
@cache.cached(timeout=cache_timeout)
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
@cache.cached(timeout=cache_timeout)
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


@app.route("/<string:organization>/<string:repository>/details")
@cache.cached(timeout=cache_timeout)
def components_portfolio(organization, repository):

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
                step["content"] = markdown2.markdown(
                    step["content"], extras=markdownExtra
                )

    # project rendering
    return render_template("project_detail.html", project=data["project"])
