import logging
from urllib.parse import unquote
from io import BytesIO
import re
from os.path import join
from math import floor

from flask import Blueprint, jsonify, send_file
from flask_restful import Resource, Api, reqparse

from PIL import Image

try:
    from redis import StrictRedis
    REDIS_SUPPORT = True
except ImportError:
    REDIS_SUPPORT = False

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


class UnsupportedContextError(Error):
    err_name = "UnsupportedContextError"


@BLUEPRINT.errorhandler(Error)
def handle_errors(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


# When not as lazy probably move all the following to lib


class RedisCache:
    def __init__(self, redis, ttl=1800):
        self.redis = redis
        self.ttl = ttl

    def cache_data(self, key, data):
        if isinstance(data, BytesIO):
            self.redis.set(key, data.read(), ex=self.ttl)
            data.seek(0)
        elif isinstance(data, str):
            # Hope its a filepath!
            with open(data) as f:
                self.redis.set(key, f.read(), ex=self.ttl)

    def cache_str(self, key, data):
        self.redis.set(key, data, ex=self.ttl)

    def get(self, key):
        v = self.redis.get(key)
        # The data was accessed, bump its ttl back up
        if v is not None:
            self.redis.pexpire(key, self.ttl)
        return v


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
    raise UnknownIdentifierFormatError(identifier)


def statter(storageKls, identifier):
    # TODO
    # Without more class introspection this gets a little wonky if classes
    # are making their own decisions about whether or not to let dynamic
    # derivatives be created.
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
        raise ValueError()
    # If height or width is omitted use the original
    if args['height'] or args['width']:
        if args['height'] and not args['width']:
            args['width'] = o_width
        if args['width'] and not args['height']:
            args['height'] = o_height
    # Quality for jpgs only goes to 95. See Pillow docs
    # and talk about jpg compression
    try:
        if args['quality'] is not None:
            if args['quality'] > 95:
                args['quality'] = 95
        else:
            args['quality'] = 95
    except KeyError:
        pass
    # Lets all agree to never make something twice as big
    # as the original is, okay? Good.
    if args['height'] is not None:
        if args['height'] > (2 * o_height):
            args['height'] = 2 * o_height
    if args['width'] is not None:
        if args['width'] > (2 * o_width):
            args['width'] = 2 * o_width
    if args['scale'] is not None:
        if args['scale'] > 2:
            args['scale'] = 2
    # And how about we but some bottom bounds on here to,
    # say dimensions no lower than 10x10 and scaling no lower
    # than 1%
    if args['width'] is not None:
        if args['width'] < 10:
            args['width'] = 10
    if args['height'] is not None:
        if args['height'] < 10:
            args['height'] = 10
    if args['scale'] is not None:
        if args['scale'] < .1:
            args['scale'] = .1

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
        except Omitted:
            # Produce a derivative, try from pdf first, then jpg
            try:
                master = Image.open(storage_instance.get_pdf(unquote(identifier)))
            except Omitted:
                master = Image.open(storage_instance.get_jpg(unquote(identifier)))

        # Transformations
        o_width, o_height = master.size
        args = sane_transform_args(args, o_width, o_height)
        if BLUEPRINT.config.get("REDIS_CACHE") is not None:
            print("Checking cache")
            cached = BLUEPRINT.config["REDIS_CACHE"].get("{}::{}::{}".format(
                identifier, str(args['width']), str(args['height'])))
            if cached:
                print("Found it")
                return send_file(BytesIO(cached), mimetype="image/tif")
        if args['width'] and args['height']:
            master = master.resize((args['width'], args['height']))
        elif args['scale']:
            master = master.resize((floor(o_width * args['scale']), floor(o_height * args['scale'])))
        tif = BytesIO()
        master.save(tif, "TIFF")
        tif.seek(0)
        if BLUEPRINT.config.get("REDIS_CACHE") is not None:
            print("Sending result to cache")
            BLUEPRINT.config['REDIS_CACHE'].cache_data(
                "{}::{}::{}".format(identifier, str(args['width']), str(args['height'])),
                tif
            )
        return send_file(
            tif,
            mimetype="image/tif"
        )


class GetTifTechnicalMetadata(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return storage_instance.get_tif_techmd(unquote(identifier))


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
        except Omitted:
            # Produce a derivative, try tif first, then pdf
            try:
                master = Image.open(storage_instance.get_tif(unquote(identifier)))
            except Omitted:
                master = Image.open(storage_instance.get_pdf(unquote(identifier)))

        # Transformations
        o_width, o_height = master.size
        args = sane_transform_args(args, o_width, o_height)
        if args['width'] and args['height']:
            master = master.resize((args['width'], args['height']))
        elif args['scale']:
            master = master.resize((floor(o_width * args['scale']), floor(o_height * args['scale'])))
        jpg = BytesIO()
        master.save(jpg, "JPEG", quality=args['quality'])
        jpg.seek(0)
        return send_file(
            jpg,
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

        return send_file(storage_instance.get_pdf(unquote(identifier)))


class GetMetadata(Resource):
    def get(self, identifier):
        storage_kls = determine_identifier_type(unquote(identifier))
        storage_instance = storage_kls(BLUEPRINT.config)
        return send_file(
            storage_instance.get_descriptive_metadata(unquote(identifier)),
            mimetype="text/xml"
        )


@BLUEPRINT.record
def handle_configs(setup_state):
    app = setup_state.app
    BLUEPRINT.config.update(app.config)
    if BLUEPRINT.config.get('DEFER_CONFIG'):
        return

    if REDIS_SUPPORT:
        if BLUEPRINT.config.get("REDIS_HOST") is not None:
            BLUEPRINT.config['REDIS_CACHE'] = \
                RedisCache(
                    StrictRedis(
                        host=BLUEPRINT.config['REDIS_HOST'],
                        port=BLUEPRINT.config.get('REDIS_PORT', 6379),
                        db=BLUEPRINT.config.get("REDIS_DB", 0)
                    )
                )

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
