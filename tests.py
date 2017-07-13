import unittest
import json
from os import environ
from urllib.parse import quote

# Defer all configuration of the app
# to the tests setUp() function
environ['DIGCOLL_RETRIEVER_DEFER_CONFIG'] = "True"
import digcollretriever


class DigCollRetrieverTests(unittest.TestCase):
    def setUp(self):
        self.app = digcollretriever.app.test_client()

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

    def testGetJpg(self):
        rv = self.response_200(
            self.app.get("/{}/jpg".format(quote("mvol/0001/0001/0001")))
        )

    def testGetJpgStats(self):
        rv = self.response_200(
            self.app.get("/{}/jpg/stats".format(quote("mvol/0001/0001/0001")))
        )

    def testGetTif(self):
        rv = self.response_200(
            self.app.get("/{}/tif".format(quote("mvol/0001/0001/0001")))
        )

    def testGetTifStats(self):
        rv = self.response_200(
            self.app.get("/{}/tif/stats".format(quote("mvol/0001/0001/0001")))
        )

    def testGetMetadata(self):
        rv = self.response_200(
            self.app.get("/{}/metadata".format(quote("mvol/0001/0001/0001")))
        )

    def testGetOCR(self):
        rv = self.response_200(
            self.app.get("/{}/ocr".format(quote("mvol/0001/0001/0001")))
        )

    def testGetJejOCR(self):
        rv = self.response_200(
            self.app.get("/{}/ocr/jej".format(quote("mvol/0001/0001/0001")))
        )

    def testGetPDF(self):
        rv = self.response_200(
            self.app.get("/{}/pdf".format(quote("mvol/0001/0001/0001")))
        )


if __name__ == '__main__':
    unittest.main()
