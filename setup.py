from setuptools import setup, find_packages


def readme():
    with open("README.md", 'r') as f:
        return f.read()


setup(
    name="digcollretriever",
    description="A retriever meant to allow API access to image files on disk and " +
    "limited supplemental information for arbitrary collecition or exhibition interfaces.",
    version="0.0.1",
    long_description=readme(),
    author="Brian Balsamo",
    author_email="balsamo@uchicago.edu",
    packages=find_packages(
        exclude=[
        ]
    ),
    include_package_data=True,
    url='https://github.com/uchicago-library/digcollretriever',
    install_requires=[
        'flask>0',
        'flask_env',
        'flask_restful',
        'jsonschema',
        'pillow'
    ],
    tests_require=[
        'pytest'
    ],
    test_suite='tests'
)
