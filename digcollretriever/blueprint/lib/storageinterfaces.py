from os.path import join
import re
from PIL import Image

from ..exceptions import Omitted

# NOTE: When implementing your identifier schema be sure that the set of
# all valid identifiers from other schemas is disjoint from the set of
# valid identifiers in your schema.
# Also probably don't get too greedy with taking up the good "namespaces".


class StorageInterface:
    """
    A base class for StorageInterface classes to inherit from.
    Provides convenience methods which raise dicollretriever_lib.exceptions.Omitted.
    Provides method signatures and documentation in each method pertaining
    to implementing said method in your own subclass
    """
    @classmethod
    def claim_identifier(cls, identifier):
        """
        Must be either a static or class method which returns boolean True
        in instances where the interface class can/should handle an identifier,
        and otherwise boolean False

        __Args__

        1) identifier (str): An identifier

        __Return Values__

        * (bool): A boolean representation of whether or not this StorageInterface
            should be used to handle requests pertaining to the identifier.
        """
        return False

    def __init__(self, conf):
        """
        Instantiates an instance of the StorageInterface class.

        __Args__
        1) conf (dict): The configuration dictionary from the API. Will include
            all relevant environmental variables provided to the API at runtime.
        """
        raise NotImplementedError()

    def get_tif(self, identifier):
        """
        Return a tif image, or raise Omitted to trigger fallback functionality

        __Args__
        1) identifier (str): The identifier of the tif

        __Return Values__
        * a filepath (str/bytes) to a tif file on disk
        * OR
        * a file-like object containing the tif data
        """
        raise Omitted()

    def get_tif_techmd(self, identifier):
        """
        Returns a dict providing metadata about a tif
        which exists natively (eg, is not created dynamically), which
        minimally satisfies the following schema when serialized to JSON:

        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "width": {"type": "int"},
                "height": {"type": "int"}
            }
        }

        Width and height should be the dimensions of the image in pixels.

        __Args__
        1) identifier (str): The identifier of the tif

        __Return Values__
        * (dict) The dictionary as described above.
        """
        raise Omitted()

    def get_pdf(self, identifier):
        """
        Return a pdf file, or raise Omitted to trigger fallback functionality
        """
        raise Omitted()

    def get_jpg(self, identifier):
        """
        Return a jpg file, or raise Omitted to trigger fallback functionality

        __Args__
        1) identifier (str): The identifier of the jpg

        __Return Values__
        * a filepath (str/bytes) to a jpg file on disk
        * OR
        * a file-like object containing the jpg data
        """
        raise Omitted()

    def get_jpg_techmd(self, identifier):
        """
        Returns a dict providing metadata about a jpg
        which exists natively (eg, is not created dynamically), which
        minimally satisfies the following schema when serialized to JSON:

        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "width": {"type": "int"},
                "height": {"type": "int"}
            }
        }

        Width and height should be the dimensions of the image in pixels.

        __Args__
        1) identifier (str): The identifier of the jpg

        __Return Values__
        * (dict) The dictionary as described above.
        """
        raise Omitted()

    def get_limb_ocr(self, identifier):
        """
        # TODO
        """
        raise Omitted()

    def get_descriptive_metadata(self, identifier):
        """
        Returns DublinCore XML descriptive metadata about an intellectual unit

        # TODO flesh this out more, generate real DC specification?

        __Args__
        1) identifier (str): The identifier of the intellectual unit

        __Return Values__
        * (filepath/file like object) a DC xml record
        """
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
        if re.match("^flattifdir-[a-z0-9]+$", identifier):
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
        if re.match("^flatjpgdir-[a-z0-9]+$", identifier):
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
        if re.match("^flatjpgdirnobadtifs-[a-z0-9]+$", identifier):
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
        return join(self.build_dir_path(identifier), identifier + ".pdf")

    def get_descriptive_metadata(self, identifier):
        return join(self.build_dir_path(identifier), identifier + ".dc.xml")


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
        return join(self.build_dir_path(identifier), "TIFF", identifier + ".tif")

    def get_tif_techmd(self, identifier):
        tif = Image.open(self.get_tif(identifier))
        width, height = tif.size
        return {"width": width, "height": height}

    def get_limb_ocr(self, identifier):
        return join(self.build_dir_path(identifier), "ALTO", identifier + ".xml")
