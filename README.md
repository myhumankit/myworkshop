# myworkshop
A documentation generator for open hardware projects.

## Features
 * Generate beautiful documentation for open hardware projects from source files stored on GitHub!

## Getting started

### Requirements
 * python 3.6 or higher (package _python3_);
 * Flask 1.0.2 or higher;

We strongly recommend to install a virtualenv:

```
$ python3 -m virtualenv -p python3 venv
$ source venv/bin/activate
$ pip install Flask
$ pip install requests
$ pip install jsonschema
```

To run the application locally:

```
$ export FLASK_APP=app.py
$ flask run
```

## Tech/framework used
 * [Flask](http://flask.pocoo.org/)

## Versioning
We use [SemVer](http://semver.org/) for versioning. See the [CHANGELOG.md](CHANGELOG.md) file for details.

## Contributing
If you'd like to contribute, please raise an issue or fork the repository and use a feature branch. Pull requests are warmly welcome.

## Licensing
The code in this project is licensed under MIT license. See the [LICENSE](LICENSE) file for details.

## Contributors
 * **Julien Lebunetel** - [jlebunetel](https://github.com/jlebunetel)
