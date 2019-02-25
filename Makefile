.PHONY: install
install:
	python3 -m virtualenv -p python3 venv
	venv/bin/pip install -r requirements.txt

.PHONY: serve
serve:
	FLASK_APP=app.py venv/bin/flask run

.PHONY: test-json
test-json:
	venv/bin/python3 json-validation.py project.json
