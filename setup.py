from setuptools import setup, find_packages

def readme():
    with open("README.md", 'r') as f:
        return f.read()

setup(
    name = "digcollretriever",
    description = "A web API for accessing digital assets",
    long_description = readme(),
    packages = find_packages(
        exclude = [
        ]
    ),
    dependency_links = [
        'https://github.com/uchicago-library/digcollretriever_lib' +
        '/tarball/master#egg=digcollretriever_lib'
    ],
    install_requires = [
        'flask>0',
        'flask_env',
        'flask_restful',
        'jsonschema',
        'pillow',
        'digcollretriever_lib'
    ],
)
