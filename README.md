[![Build Status](https://travis-ci.org/uchicago-library/digcoll_retriever.svg?branch=master)](https://travis-ci.org/uchicago-library/digcoll_retriever)

# digcoll_retriever
A retriever meant to allow API access to contents of owncloud for arbitrary collecition or exhibition interfaces

# Environmental Variables

## Global Required Env Vars
* None

## Global Optional Env Vars
* DIGCOLL_RETRIEVER_VERBOSITY: Controls the logging verbosity
* DIGCOLL_RETRIEVER_HOST: The host address for gunicorn to bind to if using gunicorn_debug.sh. Defaults to 0.0.0.0
* DIGCOLL_RETRIEVER_PORT: The port for gunicorn to bind to if using gunicorn_debug.sh. Defaults to 5000.
* DIGCOLL_RETRIEVER_WORKERS: The number of workers for gunicorn to spawn if using gunicorn_debug.sh. Defaults to 4.
* DIGCOLL_RETRIEVER_TIMEOUT: The time, in seconds, for gunicorn to wait before timing out a connection if using gunicorn_debug.sh. Defaults to 30.

## MVOL Owncloud Implementation Required Env Vars
* DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_ROOT: The root path for the owncloud installation holding the mvols
* DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_USER: The username of the owncloud account which holds the publication shares for the files
* DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_SUBPATH: Any subpath below the mvol user account which needs to be traversed before hitting the mvol specification file structure

# Example of how to run for testing/demos

```
$ DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_ROOT=/home/brian/sandbox/mock_oc_root DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_USER=ldr_oc_admin DIGCOLL_RETRIEVER_MVOL_OWNCLOUD_SUBPATH=Preservation\ Unit bash debug.sh
```

# Endpoints

## /
### URL Paramaters
None
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
None
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
None
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
None
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
None
### Description
Returns the limb ocr data as text

## /$identifier/ocr/pos
### URL Paramaters
None
### Description
Returns the pos ocr data as text

## /$identifier/pdf
### URL Paramaters
None
### Description
Returns binary pdf image data, transformations are not currently supported.

## /$identifier/metadata
### URL Paramaters
None
### Description
Returns the DC metadata

## Handy tidbits for Developers

- PIL.Image.open() and Flask.send\_file() both accept either file paths or file like objects (such as instances of io.BytesIO) as inputs
- All the endpoints on the receiving end use urllib.parse.unquote to reconstruct potentially escaped identifiers which are passed via the URLs
- All scaling math uses math.floor()
- All image manipulation and derivative storage is done in RAM. You've been warned.
- Identifiers in the URLs are considered [paths](http://flask.pocoo.org/docs/0.12/quickstart/#variable-rules) by flask to avoid pre-mature URL escaping and interpretation in the URLs.

### Developing a New Endpoint

When implementing a new endpoint generally follow the example of using digcollretriever.blueprint.lib.get_identifier_type() in order to return the class which handles the identifier and providing the digcollretriever.blueprint.BLUEPRINT.config dictionary to the classes \_\_init\_\_ in order to instantiate an instance of the StorageInterface class. 


### Developiong a new Storage Interface

The storage interface classes provide the following methods.

```
claim_identifier
get_tif
get_tif_techmd
get_pdf
get_jpg
get_jpg_techmd
get_limb_ocr
get_jej_ocr
get_pos_ocr
get_descriptive_metadata
```

Further information on the StorageInterface classes, and the expected method behavior, can be found [in the digcollretriever_lib repository](https://github.com/uchicago-library/digcollretriever_lib)


Image used in tests originally from https://www.flickr.com/photos/fannydesbaumes/35263390573/in/photostream/ CCSA
