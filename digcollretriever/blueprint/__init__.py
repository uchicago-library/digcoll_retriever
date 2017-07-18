import logging
from urllib.parse import unquote
from io import BytesIO

from flask import Blueprint, jsonify, send_file
from flask_restful import Resource, Api

from PIL import Image

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


class UnknownIdentifierFormatError(Error):
    err_name = "UnknownIdentifierFormatError"


@BLUEPRINT.errorhandler(Error)
def handle_errors(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


### When not as lazy probably move all the following to lib

# Abstraction class for use with different kinds of identifiers, maybe?
# Futher consideration on this tomorrow, I imagine
class StorageInterface:
    def get_tif(self, identifier):
        pass

    def get_pdf(self, identifier):
        pass

    def get_jpg(self, identifier):
        pass

    def get_limb_ocr(self, identifier):
        pass

    def get_jej_ocr(self, identifier):
        pass

    def get_pos_ocr(self, identifier):
        pass

def get_tif_dimensions(identifier):
    return 0, 0


def get_jpg_dimensions(identifier):
    return 0, 0


def get_tif(identifier):
    return b"not a tif"


def tif_to_jpg(identifier, width, height):
    return b"not a jpg"
#    # There's also Image.open(), depending on if we go with byte streams or paths
#    tif = Image.frombytes(mode, size, (get_tif(identifier)))
#    mem_jpg = BytesIO()
#    tif.save(mem_jpg, format="jpg")
#    mem_jpg.seek(0)
#    return mem_jpg


def is_mvol_identifier(identifier):
    return True if "mvol" in identifier else False


def dummy_id_check(identifier):
    return True


def determine_identifier_type(identifier):
    id_types = {
        "mvol": is_mvol_identifier,
        "other": dummy_id_check
    }

    for x in id_types:
        if id_types[x](identifier):
            return x
    raise UnknownIdentifierFormatError(identifier)


### End stuff that should be moved to lib


class Root(Resource):
    def get(self):
        return {"It worked!": None}


class Stat(Resource):
    def get(self, identifier):
        return {"identifier": unquote(identifier),
                "contexts_available": []}


class GetTif(Resource):
    def get(self, identifier):
        return send_file(b"this isn't really a tif", mimetype="image/tif")


class GetTifTechnicalMetadata(Resource):
    def get(self, identifier):
        width, height = get_tif_dimensions(unquote(identifier))
        return {"width": width,
                "height": height}


class GetJpg(Resource):
    # TODO: Handle paramters on this endpoint for jpg size
    def get(self, identifier):
        return send_file(tif_to_jpg(identifier, 100, 100), mimetype="image/jpg")


class GetJpgTechnicalMetadata(Resource):
    def get(self, identifier):
        width, height = get_jpg_dimensions(unquote(identifier))
        return {"width": width,
                "height": height}


class GetOcr(Resource):
    def get(self, identifier):
        return send_file(b"this is an OCR file", mimetype="text")


class GetJejOcr(Resource):
    def get(self, identifier):
        return send_file(b"this is a jej OCR file", mimetype="text")


class GetPosOcr(Resource):
    def get(self, identifier):
        return send_file(b"this is a pos OCR file", mimetype="text")


class GetPdf(Resource):
    def get(self, identifier):
        return send_file(b"this isn't really a pdf", mimetype="application/pdf")


class GetMetadata(Resource):
    def get(self, identifier):
        return send_file(b"this is a metadata stand in file", mimetype="text")


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
