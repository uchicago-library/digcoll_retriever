import logging
from urllib.parse import unquote

from flask import Blueprint, jsonify
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename

BLUEPRINT = Blueprint('digcollretriever', __name__)

BLUEPRINT.config = {}

API = Api(BLUEPRINT)

log = logging.getLogger(__name__)


class Error(Exception):
    err_name = "Error"
    status_code = 500
    message = ""

    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def to_dict(self):
        return {"message": self.message,
                "error_name": self.err_name}


@BLUEPRINT.errorhandler(Error)
def handle_errors(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


class Root(Resource):
    def get(self):
        return {"It worked!": None}


class Stat(Resource):
    def get(self, identifier):
        return {"Stat": unquote(identifier)}


class GetTif(Resource):
    def get(self, identifier):
        return {"GetTif": unquote(identifier)}


class GetTifTechnicalMetadata(Resource):
    def get(self, identifier):
        return {"GetTifTechnicalMetadata": unquote(identifier)}


class GetJpg(Resource):
    # Handle paramters on this endpoint for jpg size
    def get(self, identifier):
        return {"GetJpg": unquote(identifier)}


class GetJpgTechnicalMetadata(Resource):
    def get(self, identifier):
        return {"GetJpgTechnicalMetadata": unquote(identifier)}


class GetOcr(Resource):
    def get(self, identifier):
        return {"GetOcr": unquote(identifier)}


class GetJejOcr(Resource):
    def get(self, identifier):
        return {"GetJejOcr": unquote(identifier)}


class GetPosOcr(Resource):
    def get(self, identifier):
        return {"GetPosOcr" :unquote(identifier)}


class GetPdf(Resource):
    def get(self, identifier):
        return {"GetPDF": unquote(identifier)}


class GetMetadata(Resource):
    def get(self, identifier):
        return {"GetMetadata": unquote(identifier)}


@BLUEPRINT.record
def handle_configs(setup_state):
    app = setup_state.app
    BLUEPRINT.config.update(app.config)
    if BLUEPRINT.config.get('DEFER_CONFIG'):
        return

    if BLUEPRINT.config.get("VERBOSITY"):
        logging.basicConfig(level=BLUEPRINT.config['VERBOSITY'])
    else:
        logging.basicConfig(level="WARN")


API.add_resource(Root, "/")
API.add_resource(Stat, "/<path:identifier>/stat")
API.add_resource(GetTif, "/<path:identifier>/tif")
API.add_resource(GetTifTechnicalMetadata, "/<path:identifier>/tif/technical_metadata")
API.add_resource(GetJpg, "/<path:identifier>/jpg")
API.add_resource(GetJpgTechnicalMetadata, "/<path:identifier>/jpg/technical_metadata")
API.add_resource(GetOcr, "/<path:identifier>/ocr")
API.add_resource(GetJejOcr, "/<path:identifier>/ocr/jej")
API.add_resource(GetPosOcr, "/<path:identifier>/ocr/pos")
API.add_resource(GetPdf, "/<path:identifier>/pdf")
API.add_resource(GetMetadata, "/<path:identifier>/metadata")
