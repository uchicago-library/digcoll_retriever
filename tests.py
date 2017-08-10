import unittest
import json
from os import environ, getcwd
from os.path import join
from urllib.parse import quote
import jsonschema

# Defer all configuration of the app
# to the tests setUp() function
environ['DIGCOLL_RETRIEVER_DEFER_CONFIG'] = "True"
import digcollretriever
from digcollretriever.blueprint.lib.schemas import \
    techmd_schema, stat_schema, root_schema


class DigCollRetrieverMvolStorageNoJpgTests(unittest.TestCase):
    def setUp(self):
        self.app = digcollretriever.app.test_client()
        digcollretriever.blueprint.BLUEPRINT.config = {
            "MVOL_OWNCLOUD_ROOT": join(getcwd(), "sandbox", "mock_oc_root"),
            "MVOL_OWNCLOUD_USER": "ldr_oc_admin",
            "MVOL_OWNCLOUD_SUBPATH": "Preservation Unit"
        }

    def tearDown(self):
        pass

    def response_200_json(self, rv):
        self.assertEqual(rv.status_code, 200)
        rt = rv.data.decode()
        rj = json.loads(rt)
        return rj

    def response_200(self, rv):
        self.assertEqual(rv.status_code, 200)
        return rv

    def testGetRoot(self):
        rv = self.app.get("/")
        rj = self.response_200_json(rv)
        jsonschema.validate(rj, root_schema)

    def testGetStat(self):
        rj = self.response_200_json(
            self.app.get("/{}/stat".format(quote("mvol-0001-0002-0003")))
        )
        jsonschema.validate(rj, stat_schema)

    def testGetJpg(self):
        rv = self.response_200(
            self.app.get("/{}/jpg".format(quote("mvol-0001-0002-0003_0001")))
        )

    def testGetTif(self):
        rv = self.response_200(
            self.app.get("/{}/tif".format(quote("mvol-0001-0002-0003_0001")))
        )

    def testGetTifTechnicalMetadata(self):
        rj = self.response_200_json(
            self.app.get("/{}/tif/technical_metadata".format(quote("mvol-0001-0002-0003_0001")))
        )
        jsonschema.validate(rj, techmd_schema)

    def testGetMetadata(self):
        rv = self.response_200(
            self.app.get("/{}/metadata".format(quote("mvol-0001-0002-0003")))
        )

    def testGetLimbOCR(self):
        rv = self.response_200(
            self.app.get("/{}/ocr/limb".format(quote("mvol-0001-0002-0003_0001")))
        )

    def testGetPOSOCR(self):
        rv = self.response_200(
            self.app.get("/{}/ocr/pos".format(quote("mvol-0001-0002-0003_0001")))
        )

    def testGetPDF(self):
        rv = self.response_200(
            self.app.get("/{}/pdf".format(quote("mvol-0001-0002-0003")))
        )


if __name__ == '__main__':
    unittest.main()
