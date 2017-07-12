import unittest
from os import environ


# Differ all configuration of the app
# to the tests setUp() function

environ['DIGCOLL_RETRIEVER_DEFER_CONFIG'] = "True"

import digcollretriever


class DigCollRetrieverTests(unittest.TestCase):
    def testPass(self):
        pass


if __name__ == '__main__':
    unittest.main()
