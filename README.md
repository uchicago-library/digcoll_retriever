# digcoll_retriever

v0.0.1

[![Build Status](https://travis-ci.org/uchicago-library/digcoll_retriever.svg?branch=master)](https://travis-ci.org/uchicago-library/digcoll_retriever) [![Coverage Status](https://coveralls.io/repos/github/uchicago-library/digcoll_retriever/badge.svg?branch=master)](https://coveralls.io/github/uchicago-library/digcoll_retriever?branch=master)

A retriever meant to allow API access to image files on disk and limited supplemental information for arbitrary collecition or exhibition interfaces.

# Debug Quickstart
Set environmental variables appropriately
```
./debug.sh
```

# Docker Quickstart
Inject environmental variables appropriately at either buildtime or runtime
```
# docker build . -t digcollretriever
# docker run -p 5000:80 digcollretriever --name my_digcollretriever
```

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

# Environmental Variables

## Global Required Env Vars
* None

## Global Optional Env Vars
* DIGCOLLRETRIEVER_VERBOSITY: Controls the logging verbosity

## MVOL Owncloud Implementation Required Env Vars
* DIGCOLLRETRIEVER_MVOL_OWNCLOUD_ROOT: The root path for the owncloud installation holding the mvols
* DIGCOLLRETRIEVER_MVOL_OWNCLOUD_USER: The username of the owncloud account which holds the publication shares for the files
* DIGCOLLRETRIEVER_MVOL_OWNCLOUD_SUBPATH: Any subpath below the mvol user account which needs to be traversed before hitting the mvol specification file structure

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

Functionality from StorageInterface not overloaded will signal to the API that it can attempt to use fallback methods in order to satisfy the request (by raising an instance of digcollretriever.blueprint.exceptions.Omitted). If you wish to prevent fallbacks implement a method with the same footprint which raises an exception which is not an instance of digcollretriever.blueprint.exceptions.Omitted.

## Handy Tidbits for Developers

- PIL.Image.open() and Flask.send\_file() both accept either file paths or file like objects (such as instances of io.BytesIO) as inputs
- All the endpoints on the receiving end use urllib.parse.unquote to reconstruct potentially escaped identifiers which are passed via the URLs
- All scaling math uses math.floor()
- All image manipulation and derivative storage is done in RAM. You've been warned.
- Identifiers in the URLs are considered [paths](http://flask.pocoo.org/docs/0.12/quickstart/#variable-rules) by flask to avoid pre-mature URL escaping and interpretation in the URLs.


# Author
Brian Balsamo <balsamo@uchicago.edu>


Image used in tests originally from https://www.flickr.com/photos/fannydesbaumes/35263390573/in/photostream/ CCSA
