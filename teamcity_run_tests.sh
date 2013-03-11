#!/bin/bash
virtualenv .
source bin/activate
python setup.py install
nosetests