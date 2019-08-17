#!/bin/sh
pip install twine
python setup.py sdist
twine check dist/*
python -m twine upload dist/* --username tommyod --password $TWINE --skip-existing