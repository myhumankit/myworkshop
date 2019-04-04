import math
import hashlib

"""
density in kg / m³
cost in € / kg
"""

material_dict = {
    "steel": {"full_name": "acier", "density": 7850, "cost": 5},
    "stainless steel": {"full_name": "inox", "density": 8010, "cost": 6},
    "aluminum": {"full_name": "aluminium", "density": 2700, "cost": 20},
    "copper": {"full_name": "cuivre", "density": 8950, "cost": 20},
    "fir": {"full_name": "sapin", "density": 1000, "cost": 1.5},
    "pine": {"full_name": "pin", "density": 1000, "cost": 1.5},
    "cedar": {"full_name": "cêdre", "density": 1000, "cost": 1.5},
    "poplar": {"full_name": "peuplier", "density": 1000, "cost": 1.5},
    "oak": {"full_name": "chêne", "density": 1000, "cost": 1.5},
    "redwood": {"full_name": "séquoia", "density": 1000, "cost": 1.5},
    "fir plywood": {"full_name": "contreplaqué sapin", "density": 450, "cost": 5.5},
    "pine plywood": {"full_name": "contreplaqué pin", "density": 450, "cost": 5.5},
    "cedar plywood": {"full_name": "contreplaqué cêdre", "density": 450, "cost": 5.5},
    "poplar plywood": {
        "full_name": "contreplaqué peuplier",
        "density": 450,
        "cost": 5.5,
    },
    "oak plywood": {"full_name": "contreplaqué chêne", "density": 450, "cost": 5.5},
    "redwood plywood": {
        "full_name": "contreplaqué séquoia",
        "density": 450,
        "cost": 5.5,
    },
    "MDF": {"full_name": "MDF", "density": 750, "cost": 1.7},
    "HDF": {"full_name": "HDF", "density": 800, "cost": 1.7},
    "OSB": {"full_name": "OSB", "density": 650, "cost": 2.5},
    "OSB 1": {"full_name": "OSB 1", "density": 650, "cost": 2.5},
    "OSB 2": {"full_name": "OSB 2", "density": 650, "cost": 2.5},
    "OSB 3": {"full_name": "OSB 3", "density": 650, "cost": 2.5},
    "OSB 4": {"full_name": "OSB 4", "density": 650, "cost": 2.5},
    "PMMA": {"full_name": "PMMA", "density": 1190, "cost": 14},
    "PMMA opaque": {"full_name": "PMMA opaque", "density": 1190, "cost": 14},
    "PMMA translucent": {"full_name": "PMMA translucide", "density": 1190, "cost": 14},
    "PMMA transparent": {"full_name": "PMMA transparent", "density": 1190, "cost": 14},
    "PMMA fluorescent": {"full_name": "PMMA fluorescent", "density": 1190, "cost": 14},
    "PVC": {"full_name": "PVC", "density": 1380, "cost": 0},
    "PE": {"full_name": "PE", "density": 950, "cost": 0},
    "Dibond": {"full_name": "Dibond", "density": 1000, "cost": 0},
    "glass": {"full_name": "verre", "density": 2500, "cost": 0},
    "foam": {"full_name": "mousse", "density": 40, "cost": 0},
    "cardboard": {"full_name": "carton", "density": 210, "cost": 0},
}


def profile_to_component(profile):
    if profile["section"]["type"] == "round":
        full_name = "Rond {}, Ø {} mm".format(
            material_dict[profile["material"]]["full_name"],
            profile["section"]["diameter"],
        )

        short_description = full_name

        section = math.pi * (profile["section"]["diameter"]) ** 2

    elif profile["section"]["type"] == "pipe":
        full_name = "Tube {}, Ø {} mm, ép. {} mm".format(
            material_dict[profile["material"]]["full_name"],
            profile["section"]["diameter"],
            profile["section"]["thickness"],
        )

        short_description = full_name

        section = math.pi * (
            (profile["section"]["diameter"] / 2) ** 2
            - (profile["section"]["diameter"] / 2 - profile["section"]["thickness"])
            ** 2
        )

    elif profile["section"]["type"] == "square_bar":
        full_name = "Profilé carré {0}, {1} x {1} mm".format(
            material_dict[profile["material"]]["full_name"], profile["section"]["width"]
        )

        short_description = full_name

        section = profile["section"]["width"] ** 2

    elif profile["section"]["type"] == "square_tube":
        full_name = "Tube carré {0}, {1} x {1} mm, ép. {2} mm".format(
            material_dict[profile["material"]]["full_name"],
            profile["section"]["width"],
            profile["section"]["thickness"],
        )

        short_description = full_name

        section = (profile["section"]["width"] ** 2) - (
            (profile["section"]["width"] - 2 * profile["section"]["thickness"]) ** 2
        )

    elif profile["section"]["type"] == "rectangular_bar":
        full_name = "Profilé rectangulaire {}, {} x {} mm".format(
            material_dict[profile["material"]]["full_name"],
            profile["section"]["long_width"],
            profile["section"]["short_width"],
        )

        short_description = full_name

        section = profile["section"]["long_width"] * profile["section"]["short_width"]

    elif profile["section"]["type"] == "rectangular_tube":
        full_name = "Tube rectangulaire {}, {} x {} mm, ép. {} mm".format(
            material_dict[profile["material"]]["full_name"],
            profile["section"]["long_width"],
            profile["section"]["short_width"],
            profile["section"]["thickness"],
        )

        short_description = full_name

        section = (
            profile["section"]["long_width"] * profile["section"]["short_width"]
        ) - (
            (profile["section"]["long_width"] - 2 * profile["section"]["thickness"])
            * (profile["section"]["short_width"] - 2 * profile["section"]["thickness"])
        )

    elif profile["section"]["type"] == "equal_leg_angle":
        full_name = "Cornière {0}, {1} x {1} mm, ép. {2} mm".format(
            material_dict[profile["material"]]["full_name"],
            profile["section"]["leg_length"],
            profile["section"]["thickness"],
        )

        short_description = full_name

        section = (
            2 * profile["section"]["leg_length"] * profile["section"]["thickness"]
            - profile["section"]["thickness"] ** 2
        )

    elif profile["section"]["type"] == "unequal_leg_angle":
        full_name = "Cornière {}, {} x {} mm, ép. {} mm".format(
            material_dict[profile["material"]]["full_name"],
            profile["section"]["long_leg_length"],
            profile["section"]["short_leg_length"],
            profile["section"]["thickness"],
        )

        short_description = full_name

        section = (
            profile["section"]["long_leg_length"] * profile["section"]["thickness"]
            + profile["section"]["short_leg_length"] * profile["section"]["thickness"]
            - profile["section"]["thickness"] ** 2
        )

    else:
        full_name = "Profilé inconnu"
        short_description = full_name
        section = 0

    if "color" in profile:
        full_name = "{} ({})".format(full_name, profile["color"])

    id = hashlib.md5(full_name.encode("UTF-8")).hexdigest()

    # kg/m = kg/m³ * (mm² - m²)
    mass = material_dict[profile["material"]]["density"] * (section * 0.000001)

    # €/m = €/kg * kg/m
    cost = material_dict[profile["material"]]["cost"] * mass

    component = {
        "component": {
            "full_name": "{}, L = {} mm".format(full_name, profile["length"]),
            "short_description": short_description,
            "quantity": profile["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "id": id,
            "mass": {"unit": "kg", "value": mass},
        }
    }

    component_item = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": round(profile["quantity"] * profile["length"] * 0.001, 3),
            "unit": "m",
            "cost": {"currency": "EUR", "value": cost},
            "mass": {"unit": "kg", "value": mass},
            "github_organization": "",
            "github_repository": "",
            "slug": "",
        }
    }

    return component, component_item, id


def cleat_to_component(cleat):
    if cleat["section"]["type"] == "round":
        full_name = "Tasseau rond {}, Ø {} mm".format(
            material_dict[cleat["material"]]["full_name"], cleat["section"]["diameter"]
        )

        short_description = full_name

        section = math.pi * (cleat["section"]["diameter"]) ** 2

    elif cleat["section"]["type"] == "square_bar":
        full_name = "Tasseau carré {0}, {1} x {1} mm".format(
            material_dict[cleat["material"]]["full_name"], cleat["section"]["width"]
        )

        short_description = full_name

        section = cleat["section"]["width"] ** 2

    elif cleat["section"]["type"] == "rectangular_bar":
        full_name = "Tasseau rectangulaire {}, {} x {} mm".format(
            material_dict[cleat["material"]]["full_name"],
            cleat["section"]["long_width"],
            cleat["section"]["short_width"],
        )

        short_description = full_name

        section = cleat["section"]["long_width"] * cleat["section"]["short_width"]

    else:
        full_name = "Profilé inconnu"
        short_description = full_name
        section = 0

    if "color" in cleat:
        full_name = "{} ({})".format(full_name, cleat["color"])

    id = hashlib.md5(full_name.encode("UTF-8")).hexdigest()

    # kg/m = kg/m³ * (mm² - m²)
    mass = material_dict[cleat["material"]]["density"] * (section * 0.000001)

    # €/m = €/kg * kg/m
    cost = material_dict[cleat["material"]]["cost"] * mass

    component = {
        "component": {
            "full_name": "{}, L = {} mm".format(full_name, cleat["length"]),
            "short_description": short_description,
            "quantity": cleat["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "id": id,
            "mass": {"unit": "kg", "value": mass},
        }
    }

    component_item = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": round(cleat["quantity"] * cleat["length"] * 0.001, 3),
            "unit": "m",
            "cost": {"currency": "EUR", "value": cost},
            "mass": {"unit": "kg", "value": mass},
            "github_organization": "",
            "github_repository": "",
            "slug": "",
        }
    }

    return component, component_item, id


def sheet_to_component(sheet):
    full_name = "Plaque {}, ép. {} mm".format(
        material_dict[sheet["material"]]["full_name"], sheet["thickness"]
    )
    short_description = full_name

    if "color" in sheet:
        full_name = "{} ({})".format(full_name, sheet["color"])

    id = hashlib.md5(full_name.encode("UTF-8")).hexdigest()

    # kg/m² = kg/m³ * (mm -> m)
    mass = material_dict[sheet["material"]]["density"] * (sheet["thickness"] * 0.001)

    # €/m² = €/kg * kg/m²
    cost = material_dict[sheet["material"]]["cost"] * mass

    component = {
        "component": {
            "full_name": "{}, {} x {} mm".format(
                full_name, sheet["length"], sheet["width"]
            ),
            "short_description": short_description,
            "quantity": sheet["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "id": id,
            "mass": {"unit": "kg", "value": mass},
        }
    }

    component_item = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": round(
                sheet["quantity"]
                * (sheet["length"] * 0.001)
                * (sheet["width"] * 0.001),
                3,
            ),
            "unit": "m²",
            "cost": {"currency": "EUR", "value": cost},
            "mass": {"unit": "kg", "value": mass},
            "github_organization": "",
            "github_repository": "",
            "slug": "",
        }
    }

    return component, component_item, id


def screw_to_component(screw):
    full_name = "Vis {}{}{}".format(
        screw["head"], screw["head_option"], screw["driving"]
    )

    if "extremity" in screw:
        full_name = "{} {}".format(full_name, screw["extremity"])

    full_name = "{}, {}{}-{}".format(
        full_name, screw["threading"], screw["diameter"], screw["length"]
    )

    if "threaded_length" in screw:
        full_name = "{}-{}".format(full_name, screw["threaded_length"])

    if "quality" in screw:
        full_name = "{}, {}".format(full_name, screw["quality"])
    else:
        full_name = "{}, {}".format(full_name, screw["material"])

    short_description = full_name

    id = hashlib.md5(full_name.encode("UTF-8")).hexdigest()

    mass = 0

    cost = 0

    component = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": screw["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "id": id,
            "mass": {"unit": "kg", "value": mass},
        }
    }

    component_item = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": screw["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "mass": {"unit": "kg", "value": mass},
            "github_organization": "",
            "github_repository": "",
            "slug": "",
        }
    }

    return component, component_item, id


def nut_to_component(nut):
    full_name = "Écrou {} {}{}, {}".format(
        nut["type"], nut["threading"], nut["diameter"], nut["material"]
    )

    short_description = full_name

    id = hashlib.md5(full_name.encode("UTF-8")).hexdigest()

    mass = 0

    cost = 0

    component = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": nut["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "id": id,
            "mass": {"unit": "kg", "value": mass},
        }
    }

    component_item = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": nut["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "mass": {"unit": "kg", "value": mass},
            "github_organization": "",
            "github_repository": "",
            "slug": "",
        }
    }

    return component, component_item, id


def washer_to_component(washer):
    full_name = "Rondelle {} Ø{}, {}".format(
        washer["type"], washer["diameter"], washer["material"]
    )

    short_description = full_name

    id = hashlib.md5(full_name.encode("UTF-8")).hexdigest()

    mass = 0

    cost = 0

    component = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": washer["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "id": id,
            "mass": {"unit": "kg", "value": mass},
        }
    }

    component_item = {
        "component": {
            "full_name": full_name,
            "short_description": short_description,
            "quantity": washer["quantity"],
            "unit": "1",
            "cost": {"currency": "EUR", "value": cost},
            "mass": {"unit": "kg", "value": mass},
            "github_organization": "",
            "github_repository": "",
            "slug": "",
        }
    }

    return component, component_item, id
