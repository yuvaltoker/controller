#!/bin/bash

python report-generator-test.py &
python app-test.py &

python controller.py