import logging
from urllib.parse import unquote
from io import BytesIO
import re
from os.path import join
from math import floor

from flask import Blueprint, jsonify, send_file
from flask_restful import Resource, Api, reqparse

from PIL import Image

BLUEPRINT = Blueprint('digcollretriever', __name__)

BLUEPRINT.config = {}

API = Api(BLUEPRINT)

log = logging.getLogger(__name__)


class Omitted(Exception):
    """
    Descendants of StorageInterface raise this when a
    particular functionality hasn't been implemented
    deliberately in order to trigger fall through functionalities.
    If you want to completely prevent fall throughs raise something
    that isn't this exception in the method.

    eg:

    class YesFallThroughBehavior(StorageInterface):
        # This class will produce tifs from jpgs
        def __init__(self, config):
            pass

        def get_jpg(self, identifier):
            return "/jpgs/this_one.jpg"

    class NoFallThroughBehavior(StorageInterface):
        # This class wont produce tifs from jpgs
        def __init__(self, config):
            pass

        def get_tif(self, identifier):
            raise NotImplementedError()

        def get_jpg(self, identifier):
            return "/jpgs/this_one.jpg"
    """
    pass


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
    message = "No handlers found for that identifier"


class UnsupportedContextError(Error):
    err_name = "UnsupportedContextError"
    message = "That context isn't supported for this endpoint!"


class ContextError(Error):
    err_name = "ContextError"
    message = "Something went wrong trying to access that context!"


class MutuallyExclusiveParametersError(Error):
    err_name = "MutuallyExclusiveParametersError"


@BLUEPRINT.errorhandler(Error)
def handle_errors(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


# When not as lazy probably move all the following to lib

class StorageInterface:
    @classmethod
    def claim_identifier(cls, identifier):
        return False

    def __init__(self, conf):
        pass

    def get_tif(self, identifier):
        raise Omitted()

    def get_tif_techmd(self, identifier):
        raise Omitted()

    def get_pdf(self, identifier):
        raise Omitted()

    def get_jpg(self, identifier):
        raise Omitted()

    def get_jpg_techmd(self, identifier):
        raise Omitted()

    def get_limb_ocr(self, identifier):
        raise Omitted()

    def get_jej_ocr(self, identifier):
        raise Omitted()

    def get_pos_ocr(self, identifier):
        raise Omitted()

    def get_descriptive_metadata(self, identifier):
        raise Omitted()


class FlatTifDirStorageInterface(StorageInterface):
    """
    An example implementation of another storage interface class.
    This one will take a directory full of tifs with only lowercase
    letters and numbers in their file names and serve them as tifs
    and jpgs via the web interface.
    """
    @classmethod
    def claim_identifier(cls, identifier):
        if re.match("^flattifdir-[a-z0-9]+$"):
            return True

    def __init__(self, conf):
        self.root = conf['FLAT_TIF_DIR_ROOT']

    def get_tif(self, identifier):
        return join(self.root, identifier[11:] + ".tif")


class FlatJpgDirStorageInterface(StorageInterface):
    """
    An example implementation of another storage interface class.
    This one will take a directory full of jpgs with only lowercase
    letters and numbers in their file names and serve them as tifs
    and jpgs via the web interface.
    """
    @classmethod
    def claim_identifier(cls, identifier):
        if re.match("^flatjpgdir-[a-z0-9]+$"):
            return True

    def __init__(self, conf):
        self.root = conf['FLAT_JPG_DIR_ROOT']

    def get_jpg(self, identifier):
        return join(self.root, identifier[11:] + ".jpg")


class FlatJpgDirNoBadTifsStorageInterface(FlatJpgDirStorageInterface):
    """
    A subclass of the above, which will refuse to produce tifs
    from jpgs dynamically
    """
    @classmethod
    def claim_identifier(cls, identifier):
        if re.match("^flatjpgdirnobadtifs-[a-z0-9]+$"):
            return True

    def get_tif(self, identifier):
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
        MvolLayer4StorageInterface,
        FlatTifDirStorageInterface,  # Example implementation
        FlatJpgDirStorageInterface,  # Example implementation
        FlatJpgDirNoBadTifsStorageInterface  # Example implementation
    ]

    for x in id_types:
        if x.claim_identifier(identifier):
            return x
    raise UnknownIdentifierFormatError()


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


def sane_transform_args(args, o_width, o_height):
    # Scale and width/height are mutually exclusive
    if (args['height'] or args['width']) and args['scale']:
        log.warn(
            "Received a request containing scale in conjuction with width or height"
        )
        raise MutuallyExclusiveParametersError(
            "Scale can not be used in conjunction with width or height"
        )
    # If height or width is omitted use the original
    if args['height'] or args['width']:
        if args['height'] and not args['width']:
            args['width'] = o_width
            log.debug("Assuming width as default")
        if args['width'] and not args['height']:
            args['height'] = o_height
            log.debug("Assuming height as default")
    # Quality for jpgs only goes to 95. See Pillow docs
    # and talk about jpg compression
    try:
        if args['quality'] is not None:
            if args['quality'] > 95:
                args['quality'] = 95
                log.info("Quality > 95 passed. Capping value")
        else:
            args['quality'] = 95
    except KeyError:
        pass
    # Lets all agree to never make something twice as big
    # as the original is, okay? Good.
    if args['height'] is not None:
        if args['height'] > (2 * o_height):
            args['height'] = 2 * o_height
            log.info("Height > 2 * original passed. Capping value")
    if args['width'] is not None:
        if args['width'] > (2 * o_width):
            args['width'] = 2 * o_width
            log.info("Width > 2 * original passed. Capping value")
    if args['scale'] is not None:
        if args['scale'] > 2:
            args['scale'] = 2
            log.info("Scale > 2 passed. Capping value")
    # And how about we but some bottom bounds on here to,
    # say dimensions no lower than 10x10 and scaling no lower
    # than 1%
    if args['width'] is not None:
        if args['width'] < 10:
            args['width'] = 10
            log.info("Width < 10 passed. Capping value")
    if args['height'] is not None:
        if args['height'] < 10:
            args['height'] = 10
            log.info("Height < 10 passed. Capping value")
    if args['scale'] is not None:
        if args['scale'] < .01:
            args['scale'] = .01
            log.info("Scale < .01 passed. Capping value")
    return args


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
                master = Image.open(storage_instance.get_tif(unquote(identifier)))
                log.info("Explicit functionality omitted, created derivative jpg from tif")
            except Omitted:
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
                master = Image.open(storage_instance.get_tif(unquote(identifier)))
                log.info("Explicit functionality omitted, created derivative jpg from tif")
            except Omitted:
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
