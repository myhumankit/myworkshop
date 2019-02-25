#!/usr/bin/python3
import sys
import json
from jsonschema import validate

if len(sys.argv) == 2:
    try:
        with open(sys.argv[1], "r") as file:
            json_schema = json.load(file)
        print("INFO: Valid JSON")
    except Exception as error:
        print("ERROR: Invalid JSON")
        print(error)
