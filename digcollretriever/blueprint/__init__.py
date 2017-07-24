import logging
from urllib.parse import unquote
from io import BytesIO
from math import floor

from flask import Blueprint, jsonify, send_file
from flask_restful import Resource, Api, reqparse

from PIL import Image

from .lib import determine_identifier_type, sane_transform_args
from digcollretriever_lib.storageinterfaces import StorageInterface
from digcollretriever_lib.exceptions import Error, Omitted

BLUEPRINT = Blueprint('digcollretriever', __name__)

BLUEPRINT.config = {}

API = Api(BLUEPRINT)

log = logging.getLogger(__name__)


def statter(storageKls, identifier):
    # TODO
    # Without more class introspection this gets a little wonky if classes
    # are making their own decisions about whether or not to let dynamic
    # derivatives be created.
    log.debug("Statting storage class for functionalities implementation")
    contexts = []
    if storageKls.get_tif != StorageInterface.get_tif:
        # Take into account dynamic jpg generation
        contexts.append(API.url_for(GetTif, identifier=identifier))
        contexts.append(API.url_for(GetJpg, identifier=identifier))
    if storageKls.get_tif_techmd != StorageInterface.get_tif_techmd:
        contexts.append(API.url_for(GetTifTechnicalMetadata, identifier=identifier))
    if storageKls.get_pdf != StorageInterface.get_pdf:
        contexts.append(API.url_for(GetPdf, identifier=identifier))
    if storageKls.get_jpg != StorageInterface.get_jpg:
        # Take into account dynamic tif generation
        contexts.append(API.url_for(GetJpg, identifier=identifier))
        contexts.append(API.url_for(GetTif, identifier=identifier))
    if storageKls.get_jpg_techmd != StorageInterface.get_jpg_techmd:
        contexts.append(API.url_for(GetJpgTechnicalMetadata, identifier=identifier))
    if storageKls.get_limb_ocr != StorageInterface.get_limb_ocr:
        contexts.append(API.url_for(GetLimbOcr, identifier=identifier))
    if storageKls.get_jej_ocr != StorageInterface.get_jej_ocr:
        contexts.append(API.url_for(GetJejOcr, identifier=identifier))
    if storageKls.get_pos_ocr != StorageInterface.get_pos_ocr:
        contexts.append(API.url_for(GetPosOcr, identifier=identifier))
    return contexts


@BLUEPRINT.errorhandler(Error)
def handle_errors(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


class Root(Resource):
    def get(self):
        return {"Status": "Not broken!"}


class Stat(Resource):
    def get(self, identifier):
        return {"identifier": unquote(identifier),
                "contexts_available": statter(determine_identifier_type(identifier), identifier)}


class GetTif(Resource):
    def get(self, identifier):
        parser = reqparse.RequestParser()
        parser.add_argument('width', type=int, location='args')
        parser.add_argument('height', type=int, location='args')
        parser.add_argument('scale', type=float, location='args')
        args = parser.parse_args()

        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        try:
            # Explicit implementation
            master = Image.open(storage_instance.get_tif(unquote(identifier)))
            log.info("Utilized explicit tif retrieval implementation")
        except Omitted:
            # Produce a derivative, try from pdf first, then jpg
            try:
                master = Image.open(storage_instance.get_pdf(unquote(identifier)))
                log.info("Explicit functionality omitted, created derivative tif from pdf")
            except Omitted:
                master = Image.open(storage_instance.get_jpg(unquote(identifier)))
                log.info("Explicit functionality omitted, created derivative tif from jpg")

        # Transformations
        if args['width'] or args['height'] or args['scale']:
            log.info("Transformation parameter present. Performing transformation.")
            o_width, o_height = master.size
            args = sane_transform_args(args, o_width, o_height)
            if args['width'] and args['height']:
                log.debug("Performing transformation according to explicit width/height")
                master = master.resize((args['width'], args['height']))
            elif args['scale']:
                log.debug("Performing transformation according to scaling constant")
                master = master.resize((floor(o_width * args['scale']),
                                        floor(o_height * args['scale'])))
            log.info("Transformation complete")
        tif = BytesIO()
        log.debug("Saving result to RAM object")
        master.save(tif, "TIFF")
        tif.seek(0)
        log.debug("Returning result image")
        return send_file(
            tif,
            mimetype="image/tif"
        )


class GetJpg(Resource):
    def get(self, identifier):
        parser = reqparse.RequestParser()
        parser.add_argument('width', type=int, location='args')
        parser.add_argument('height', type=int, location='args')
        parser.add_argument('scale', type=float, location='args')
        parser.add_argument('quality', type=int, location='args')
        args = parser.parse_args()

        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)

        try:
            # Explicit implementation
            master = Image.open(storage_instance.get_jpg(identifier))
            log.info("Utilized explicit jpg retrieval implementation")
        except Omitted:
            # Produce a derivative, try tif first, then pdf
            try:
                log.debug("Explicit functionality omitted, creating derivative jpg from tif")
                master = Image.open(storage_instance.get_tif(unquote(identifier)))
                log.info("Explicit functionality omitted, created derivative jpg from tif")
            except Omitted:
                log.debug("Explicit functionality omitted, creating derivative jpg from pdf")
                master = Image.open(storage_instance.get_pdf(unquote(identifier)))
                log.info("Explicit functionality omitted, created derivative jpg from pdf")

        # Transformations
        if args['width'] or args['height'] or args['scale'] or args['quality']:
            log.info("Transformation parameter present. Performing transformation.")
            o_width, o_height = master.size
            args = sane_transform_args(args, o_width, o_height)
            if args['width'] and args['height']:
                log.debug("Performing transformation according to explicit width/height")
                master = master.resize((args['width'], args['height']))
            elif args['scale']:
                log.debug("Performing transformation according to scaling constant")
                master = master.resize((floor(o_width * args['scale']),
                                        floor(o_height * args['scale'])))
            log.info("Transformation complete")
        jpg = BytesIO()
        log.debug("Saving result to RAM object")
        if args['quality'] is None:
            args['quality'] = 95
        master.save(jpg, "JPEG", quality=args['quality'])
        jpg.seek(0)
        log.debug("Returning result image")
        return send_file(
            jpg,
            mimetype="image/jpg"
        )


class GetJpgThumbnail(Resource):
    def get(self, identifier):
        parser = reqparse.RequestParser()
        parser.add_argument('width', type=int, location='args', required=True)
        parser.add_argument('height', type=int, location='args', required=True)
        parser.add_argument('quality', type=int, location='args')
        args = parser.parse_args()
        # Bandaid
        args['scale'] = None

        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)

        try:
            # Explicit implementation
            master = Image.open(storage_instance.get_jpg(identifier))
            log.info("Utilized explicit jpg retrieval implementation")
        except Omitted:
            # Produce a derivative, try tif first, then pdf
            try:
                log.debug("Explicit functionality omitted, creating derivative jpg from tif")
                master = Image.open(storage_instance.get_tif(unquote(identifier)))
                log.info("Explicit functionality omitted, created derivative jpg from tif")
            except Omitted:
                log.debug("Explicit functionality omitted, creating derivative jpg from pdf")
                master = Image.open(storage_instance.get_pdf(unquote(identifier)))
                log.info("Explicit functionality omitted, created derivative jpg from pdf")

        # Transformations
        log.info("Performing transformation.")
        o_width, o_height = master.size
        args = sane_transform_args(args, o_width, o_height)
        master.thumbnail((args['width'], args['height']))
        log.info("Transformation complete")
        if args['quality'] is None:
            args['quality'] = 95
        thumb = BytesIO()
        log.debug("Saving result to RAM object")
        master.save(thumb, "JPEG", quality=args['quality'])
        thumb.seek(0)
        log.debug("Returning result image")
        return send_file(
            thumb,
            mimetype="image/jpg"
        )


class GetPdf(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)

        # PDFs have to be explicit at the moment, and don't
        # support transformation because of (I believe) the following
        # issues in Pillow:
        # https://github.com/python-pillow/Pillow/issues/1630
        # https://github.com/python-pillow/Pillow/issues/2049
        #
        # TODO: When/if the above are fixed follow the same
        # formula as the tif and jpg endpoints here for dynamic
        # generation if no explicit option is available
        # TODO: Test if this effects generating things _from_ pdf

        log.info("Utilizing explicit pdf retrieval implementation")
        return send_file(storage_instance.get_pdf(unquote(identifier)))


class GetTifTechnicalMetadata(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        log.info("Attempting to retrieve tif technical metadata")
        return storage_instance.get_tif_techmd(unquote(identifier))


class GetJpgTechnicalMetadata(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        log.info("Attempting to retrieve jpg technical metadata")
        return storage_instance.get_jpg_techmd(unquote(identifier))


class GetMetadata(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        log.debug("Utilizing explict descriptive metadata retrieval implementation")
        return send_file(
            storage_instance.get_descriptive_metadata(unquote(identifier)),
            mimetype="text/xml"
        )


class GetLimbOcr(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        log.debug("Utilizing explicit limb OCR retreival implementation")
        return send_file(
            storage_instance.get_limb_ocr(unquote(identifier)),
            mimetype="text"
        )


class GetJejOcr(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        # TODO
        return send_file(
            storage_instance.get_jej_ocr(unquote(identifier)),
            mimetype="text"
        )


class GetPosOcr(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        log.debug("Utilizing explicit POS OCR retrieval implementation")
        return send_file(
            storage_instance.get_pos_ocr(unquote(identifier)),
            mimetype="text"
        )


@BLUEPRINT.record
def handle_configs(setup_state):
    app = setup_state.app
    BLUEPRINT.config.update(app.config)
    if BLUEPRINT.config.get('DEFER_CONFIG'):
        log.debug("DEFER_CONFIG set, skipping configuration")
        return

    if BLUEPRINT.config.get("VERBOSITY"):
        log.debug("Setting verbosity to {}".format(str(BLUEPRINT.config['VERBOSITY'])))
        logging.basicConfig(level=BLUEPRINT.config['VERBOSITY'])
    else:
        log.debug("No verbosity option set, defaulting to WARN")
        logging.basicConfig(level="WARN")


API.add_resource(Root, "/")
API.add_resource(Stat, "/<path:identifier>/stat")
API.add_resource(GetTif, "/<path:identifier>/tif")
API.add_resource(GetTifTechnicalMetadata, "/<path:identifier>/tif/technical_metadata")
API.add_resource(GetJpg, "/<path:identifier>/jpg")
API.add_resource(GetJpgThumbnail, "/<path:identifier>/jpg/thumb")
API.add_resource(GetJpgTechnicalMetadata, "/<path:identifier>/jpg/technical_metadata")
API.add_resource(GetLimbOcr, "/<path:identifier>/ocr/limb")
API.add_resource(GetJejOcr, "/<path:identifier>/ocr/jej")
API.add_resource(GetPosOcr, "/<path:identifier>/ocr/pos")
API.add_resource(GetPdf, "/<path:identifier>/pdf")
API.add_resource(GetMetadata, "/<path:identifier>/metadata")
