import unittest
import json
from os import environ, getcwd
from os.path import join
from urllib.parse import quote

import jsonschema

# Defer any configuration to the tests setUp()
environ['DIGCOLLRETRIEVER_DEFER_CONFIG'] = "True"

import digcollretriever
from digcollretriever.blueprint.lib.schemas import \
    techmd_schema, stat_schema, root_schema


class Tests(unittest.TestCase):
    def setUp(self):
        self.app = digcollretriever.app.test_client()
        digcollretriever.blueprint.BLUEPRINT.config = {
            "MVOL_OWNCLOUD_ROOT": join(getcwd(), "sandbox", "mock_oc_root"),
            "MVOL_OWNCLOUD_USER": "ldr_oc_admin",
            "MVOL_OWNCLOUD_SUBPATH": "Preservation Unit",
            "DEBUG": True
        }

    def tearDown(self):
        # Perform any tear down that should
        # occur after every test
        pass

    def response_200_json(self, rv):
        self.assertEqual(rv.status_code, 200)
        rt = rv.data.decode()
        rj = json.loads(rt)
        return rj

    def response_200(self, rv):
        self.assertEqual(rv.status_code, 200)
        return rv

    def testPass(self):
        self.assertEqual(True, True)

    def testVersionAvailable(self):
        x = getattr(digcollretriever, "__version__", None)
        self.assertTrue(x is not None)

    def testVersion(self):
        version_response = self.app.get("/version")
        self.assertEqual(version_response.status_code, 200)
        version_json = json.loads(version_response.data.decode())
        api_reported_version = version_json['version']
        self.assertEqual(
            digcollretriever.blueprint.__version__,
            api_reported_version
        )

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

    def testGetPDF(self):
        rv = self.response_200(
            self.app.get("/{}/pdf".format(quote("mvol-0001-0002-0003")))
        )


if __name__ == "__main__":
    unittest.main()
