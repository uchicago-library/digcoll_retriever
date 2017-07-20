[![Build Status](https://travis-ci.org/uchicago-library/digcoll_retriever.svg?branch=master)](https://travis-ci.org/uchicago-library/digcoll_retriever) 

# digcoll_retriever
A retriever meant to allow API access to contents of owncloud for arbitrary collecition or exhibition interfaces

# Environmental Variables

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

## /$identifier/ocr/jej
### URL Paramaters
None
### Description
Returns the jej ocr data as text

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

# Development

Development of extensions for the digcoll_retriever is meant to be as painless as possible. No functionalities are required (though obviously your implementation will become more useful the more it implements, and some interfaces may impose their own functionality requirements). Functionalities may either be implemented at the storage level, by writing new methods on the StorageInterface class and implementing them in child classes, or at the service level, writing new endpoints and using storage level functionalities to return results via the web interface.

## Existing Functionalities

### get_tif
#### Arguments
* identifier


#### Return Value


### get_jpg
#### Arguments
* identifier

#### Return Value
A file path or file like object representing the jpg file


### get_pdf
#### Arguments
* identifier

#### Return Value
A file path or file like object representing the pdf file


### get_descriptive_metadata
#### Arguments
* identifier

#### Return Value
A file path or file like object representing the dc.xml file


### get_tif_techmd
#### Arguments
* identifier

#### Return Value
A json object adhering to the previously mentioned json schema, documenting the width and the height of the _existing_ tif image, if one exists.


### get_jpg_techmd
#### Arguments
* identifier

#### Return Value
A json object adhering to the previously mentioned json schema, documenting the width and the height of the _existing_ jpg image, if one exists.


### get_limb_ocr
#### Arguments
* identifier

#### Return Value
A file path or file like object representing the limb ocr file


### get_jej_ocr
#### Arguments
* identifier

#### Return Value
A file path or file like object representing the jej ocr file


### get_pos_ocr
#### Arguments
* identifier

#### Return Value
A file path or file like object representing the pos ocr file
