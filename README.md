[![Build Status](https://travis-ci.org/uchicago-library/digcoll_retriever.svg?branch=master)](https://travis-ci.org/uchicago-library/digcoll_retriever)

# digcoll_retriever
A retriever meant to allow API access to image files on disk and limited supplemental information for arbitrary collecition or exhibition interfaces.

# Quickstart Example Using Owncloud Storage Interface and the MVOL File System Specification
```
$ git clone https://github.com/uchicago-library/digcoll_retriever.git
$ cd digcoll_retriever
$ pip install -r requirements.txt
$ python setup.py install
$ DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_ROOT="/absolute/path/to/oc/root/here" DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_USER="your_oc_username" DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_SUBPATH="A Unit Name" ./nginx_launch.sh
```
**Warning** this script will overwrite anything at /etc/nginx/nginx.conf - alter the script if you are running an nginx server for any other reason, or need to run this service in concert with others on the same host.

# Docker Quickstart with Owncloud Storage Interface and the Mvol File System Specification
```
# docker build . --build-arg DIGCOLL_RETRIEVER_SECRET_KEY=itsasecret -t digcoll_retriever
# docker run -p 5000:5000 -e DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_ROOT=/owncloud_root -e DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_USER=ldr_oc_admin -e DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_SUBPATH="Preservation Unit" -v $(pwd)/sandbox/mock_oc_root:/owncloud_root digcoll_retriever
```
Note that the environmental variable provided as DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_ROOT should match the volume mount inside of the container. In the above example it is assumed you're running docker run from the git repo directory, and will use the test data.

# Environmental Variables / Configuration

## Global Required Env Vars
* None

## Global Optional Env Vars
* DIGCOLL_RETRIEVER_VERBOSITY: Controls the logging verbosity
* DIGCOLL_RETRIEVER_HOST: The host address to bind to. Defaults to 0.0.0.0
* DIGCOLL_RETRIEVER_PORT: The port to bind to. Defaults to 5000.
* DIGCOLL_RETRIEVER_WORKERS: The number of workers for gunicorn to spawn if using gunicorn_launch.sh. Defaults to 4.
* DIGCOLL_RETRIEVER_TIMEOUT: The time, in seconds, for gunicorn to wait before timing out a connection if using gunicorn_launch.sh. Defaults to 30.

## MVOL Owncloud Implementation Required Env Vars
* DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_ROOT: The root path for the owncloud installation holding the mvols
* DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_USER: The username of the owncloud account which holds the publication shares for the files
* DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_SUBPATH: Any subpath below the mvol user account which needs to be traversed before hitting the mvol specification file structure


# Endpoints

## /
### URL Paramaters
* None
### Description
The root, for testing purposes. Should always return a response that satisfies
```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "status": {"type": "string",
                  "pattern": "^Not broken!$"}
    }
}
```

## /$identifier/stat
### URL Paramaters
* None
### Description
Returns URLs (relative to the root) that the underlying storage class supports for
an identifier. Note that though the storage class may support a functionality,
assets being incorrectly arranged on disk, network issues, etc may prevent a call
to one of these endpoints from returning correctly.

## /$identifier/tif
### URL Paramaters
* width (optional): An integer value for width of the returned image in pixels. Default is native width
* height (optional): An integer value for height of the returned image in pixels. Default is native height
* scale (optional): A float such that 0 < scale < 2 defining a scaling constant to resize the image by. Default is 1.
### Description
Returns binary tif image data, optionally transforming the returned image in response to the URL parameters.

## /$identifier/tif/technical_metadata
### URL Paramaters
* None
### Description
Returns JSON formatted data representing the width and height of the native tif image in the following form:
```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "width": {"type": "integer"},
        "height": {"type": "integer"}
    }
}
```

## /$identifier/jpg
### URL Paramters
* width (optional): An integer value for width of the returned image in pixels. Default is native width
* height (optional): An integer value for height of the returned image in pixels. Default is native height
* scale (optional): A float such that 0 < scale < 2 defining a scaling constant to resize the image by. Default is 1.
* quality (optional): An integer such that 0 < quality < 95 defining the quality of the returned jpg. See documentation about jpg quality metrics externally.
### Description
Returns binary jpg image data, optionally transforming the returned image in response to the URL parameters.


## /$identifier/jpg/technical_metadata
### URL Paramaters
* None
### Description
Returns JSON formatted data representing the width and height of the native tif image in the following form:
```
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "width": {"type": "integer"},
        "height": {"type": "integer"}
    }
}
```

## /$identifier/ocr/limb
### URL Paramaters
* None
### Description
Returns the limb ocr data as text

## /$identifier/ocr/pos
### URL Paramaters
* None
### Description
Returns the pos ocr data as text

## /$identifier/pdf
### URL Paramaters
* None
### Description
Returns binary pdf image data, transformations are not currently supported.

## /$identifier/metadata
### URL Paramaters
* None
### Description
Returns the DC metadata

## Handy Tidbits for Developers

- PIL.Image.open() and Flask.send\_file() both accept either file paths or file like objects (such as instances of io.BytesIO) as inputs
- All the endpoints on the receiving end use urllib.parse.unquote to reconstruct potentially escaped identifiers which are passed via the URLs
- All scaling math uses math.floor()
- All image manipulation and derivative storage is done in RAM. You've been warned.
- Identifiers in the URLs are considered [paths](http://flask.pocoo.org/docs/0.12/quickstart/#variable-rules) by flask to avoid pre-mature URL escaping and interpretation in the URLs.

### Developing a New Endpoint

When implementing a new endpoint generally follow the example of using digcollretriever.blueprint.lib.get_identifier_type() in order to return the class which handles the identifier and providing the digcollretriever.blueprint.BLUEPRINT.config dictionary to the classes \_\_init\_\_ in order to instantiate an instance of the StorageInterface class. 


### Developing a New Storage Interface

The storage interface classes provide the following methods.

```
claim_identifier
get_tif
get_tif_techmd
get_pdf
get_jpg
get_jpg_techmd
get_limb_ocr
get_pos_ocr
get_descriptive_metadata
```

To implement a new StorageInterface class navigate to the digcollretriever.blueprint.lib.storageinterfaces module and write a new child class inheriting from StorageInterface. The StorageInterface class itself defines the method footprint and individual method signatures and return values which are expected by the digcollretriever API.

Functionality from StorageInterface not overloaded will signal to the API that it can attempt to use fallback methods in order to satisfy the request (by raising an instance of digcollretriever.blueprint.lib.exceptions.Omitted). If you wish to prevent fallbacks implement a method with the same footprint which raises an exception which is not an instance of digcollretriever.blueprint.lib.exceptions.Omitted.

Image used in tests originally from https://www.flickr.com/photos/fannydesbaumes/35263390573/in/photostream/ CCSA
