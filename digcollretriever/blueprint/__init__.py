import logging
from urllib.parse import unquote
from io import BytesIO
import re
from os.path import join

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


class UnsupportedContextError(Error):
    err_name = "UnsupportedContextError"


@BLUEPRINT.errorhandler(Error)
def handle_errors(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


# When not as lazy probably move all the following to lib

# Abstraction class for use with different kinds of identifiers, maybe?
# Futher consideration on this tomorrow, I imagine
class StorageInterface:
    @classmethod
    def claim_identifier(cls, identifier):
        return False

    def __init__(self, conf):
        pass

    def get_tif(self, identifier):
        raise NotImplementedError()

    def get_tif_techmd(self, identifier):
        raise NotImplementedError()

    def get_pdf(self, identifier):
        raise NotImplementedError()

    def get_jpg(self, identifier, width=600, height=480):
        raise NotImplementedError()

    def get_jpg_techmd(self, identifier):
        raise NotImplementedError()

    def get_limb_ocr(self, identifier):
        raise NotImplementedError()

    def get_jej_ocr(self, identifier):
        raise NotImplementedError()

    def get_pos_ocr(self, identifier):
        raise NotImplementedError()

    def get_descriptive_metadata(self, identifier):
        raise NotImplementedError()


class MvolLayer1StorageInterface(StorageInterface):
    @classmethod
    def claim_identifier(cls, identifier):
        if re.match("^mvol-[0-9]{4}$", identifier):
            return True

    def __init__(self, conf):
        pass


class MvolLayer2StorageInterface(StorageInterface):
    @classmethod
    def claim_identifier(cls, identifier):
        if re.match("^mvol-[0-9]{4}-[0-9]{4}$", identifier):
            return True

    def __init__(self, conf):
        pass


class MvolLayer3StorageInterface(StorageInterface):
    @classmethod
    def claim_identifier(cls, identifier):
        if re.match("^mvol-[0-9]{4}-[0-9]{4}-[0-9]{4}$", identifier):
            return True

    def __init__(self, conf):
        self.MVOL_OWNCLOUD_ROOT = conf['MVOL_OWNCLOUD_ROOT']
        self.MVOL_OWNCLOUD_USER = conf['MVOL_OWNCLOUD_USER']
        self.MVOL_OWNCLOUD_SUBPATH = conf['MVOL_OWNCLOUD_SUBPATH']

    def build_dir_path(self, identifier):
        return join(
            self.MVOL_OWNCLOUD_ROOT,
            "data",
            self.MVOL_OWNCLOUD_USER,
            "files",
            self.MVOL_OWNCLOUD_SUBPATH,
            "mvol",
            identifier.split("-")[1],
            identifier.split("-")[2],
            identifier.split("-")[3]
        )

    def get_pdf(self, identifier):
        return join(self.build_dir_path(identifier), identifier+".pdf")

    def get_descriptive_metadata(self, identifier):
        return join(self.build_dir_path(identifier), identifier+".dc.xml")


class MvolLayer4StorageInterface(StorageInterface):
    @classmethod
    def claim_identifier(cls, identifier):
        if re.match("^mvol-[0-9]{4}-[0-9]{4}-[0-9]{4}_[0-9]{4}$", identifier):
            return True

    def __init__(self, conf):
        self.MVOL_OWNCLOUD_ROOT = conf['MVOL_OWNCLOUD_ROOT']
        self.MVOL_OWNCLOUD_USER = conf['MVOL_OWNCLOUD_USER']
        self.MVOL_OWNCLOUD_SUBPATH = conf['MVOL_OWNCLOUD_SUBPATH']

    def build_dir_path(self, identifier):
        return join(
            self.MVOL_OWNCLOUD_ROOT,
            "data",
            self.MVOL_OWNCLOUD_USER,
            "files",
            self.MVOL_OWNCLOUD_SUBPATH,
            "mvol",
            identifier.split("-")[1],
            identifier.split("-")[2],
            identifier.split("-")[3].split("_")[0]
        )

    def get_tif(self, identifier):
        return join(self.build_dir_path(identifier), "TIFF", identifier+".tif")

    def get_tif_techmd(self, identifier):
        tif = Image.open(self.get_tif(identifier))
        width, height = tif.size
        return {"width": width, "height": height}

    def get_jpg(self, identifier, width=600, height=480):
        # Dynamically generate the jpg from the tif
        tif = Image.open(self.get_tif(identifier))
        outfile = BytesIO()
        tif.save(outfile, "JPEG", quality=100)
        outfile.seek(0)
        return outfile
        # Static output
        #  return join(self.build_dir_path(identifier), "JPEG", identifier+".jpg")

    def get_jpg_techmd(self, identifier):
        jpg = Image.open(self.get_jpg(identifier))
        width, height = jpg.size
        return {"width": width, "height": height}

    def get_limb_ocr(self, identifier):
        return join(self.build_dir_path(identifier), "ALTO", identifier+".xml")

    def get_jej_ocr(self, identifier):
        pass

    def get_pos_ocr(self, identifier):
        pass


def determine_identifier_type(identifier):
    id_types = [
        MvolLayer1StorageInterface,
        MvolLayer2StorageInterface,
        MvolLayer3StorageInterface,
        MvolLayer4StorageInterface
    ]

    for x in id_types:
        if x.claim_identifier(identifier):
            return x
    raise UnknownIdentifierFormatError(identifier)


def statter(storageKls, identifier):
    contexts = []
    if storageKls.get_tif != StorageInterface.get_tif:
        contexts.append(API.url_for(GetTif, identifier=identifier))
    if storageKls.get_tif_techmd != StorageInterface.get_tif_techmd:
        contexts.append(API.url_for(GetTifTechnicalMetadata, identifier=identifier))
    if storageKls.get_pdf != StorageInterface.get_pdf:
        contexts.append(API.url_for(GetPdf, identifier=identifier))
    if storageKls.get_jpg != StorageInterface.get_jpg:
        contexts.append(API.url_for(GetJpg, identifier=identifier))
    if storageKls.get_jpg_techmd != StorageInterface.get_jpg_techmd:
        contexts.append(API.url_for(GetJpgTechnicalMetadata, identifier=identifier))
    if storageKls.get_limb_ocr != StorageInterface.get_limb_ocr:
        contexts.append(API.url_for(GetLimbOcr, identifier=identifier))
    if storageKls.get_jej_ocr != StorageInterface.get_jej_ocr:
        contexts.append(API.url_for(GetJejOcr, identifier=identifier))
    if storageKls.get_pos_ocr != StorageInterface.get_pos_ocr:
        contexts.append(API.url_for(GetPosOcr, identifier=identifier))
    return contexts


# End stuff that should be moved to lib


class Root(Resource):
    def get(self):
        return {"Status": "Not broken!"}


class Stat(Resource):
    def get(self, identifier):
        return {"identifier": unquote(identifier),
                "contexts_available": statter(determine_identifier_type(identifier), identifier)}


class GetTif(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return send_file(
            storage_instance.get_tif(unquote(identifier)),
            mimetype="image/tif"
        )


class GetTifTechnicalMetadata(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return storage_instance.get_tif_techmd(unquote(identifier))


class GetJpg(Resource):
    # TODO: Handle paramters on this endpoint for jpg size
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return send_file(
            storage_instance.get_jpg(unquote(identifier)),
            mimetype="image/jpg"
        )


class GetJpgTechnicalMetadata(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return storage_instance.get_jpg_techmd(unquote(identifier))


class GetLimbOcr(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return send_file(
            storage_instance.get_limb_ocr(unquote(identifier)),
            mimetype="text"
        )


class GetJejOcr(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return send_file(
            storage_instance.get_jej_ocr(unquote(identifier)),
            mimetype="text"
        )


class GetPosOcr(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return send_file(
            storage_instance.get_pos_ocr(unquote(identifier)),
            mimetype="text"
        )


class GetPdf(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return send_file(
            storage_instance.get_pdf(unquote(identifier)),
            mimetype="application/pdf"
        )


class GetMetadata(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return send_file(
            storage_instance.get_descriptive_metadata(unquote(identifier)),
            mimetype="text"
        )


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
API.add_resource(GetLimbOcr, "/<path:identifier>/ocr/limb")
API.add_resource(GetJejOcr, "/<path:identifier>/ocr/jej")
API.add_resource(GetPosOcr, "/<path:identifier>/ocr/pos")
API.add_resource(GetPdf, "/<path:identifier>/pdf")
API.add_resource(GetMetadata, "/<path:identifier>/metadata")
