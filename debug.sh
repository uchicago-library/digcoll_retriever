#!/bin/sh

APP_SAVE=$FLASK_APP
export FLASK_APP=digcollretriever
python -m flask run
export FLASK_APP=$APP_SAVE
