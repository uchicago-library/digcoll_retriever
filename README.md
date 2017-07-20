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
        "width": {"type": "string",
                  "pattern": "^Not broken!$"}
    },
}
```

## /<identifier>/stat
### URL Paramaters
None
### Description
Returns URLs (relative to the root) that the underlying storage class supports for
an identifier. Note that though the storage class may support a functionality,
assets being incorrectly arranged on disk, network issues, etc may prevent a call
to one of these endpoints from returning correctly.

## /<identifier>/tif
### URL Paramaters
None
### Description

## /<identifier>/tif/technical_metadata
### URL Paramaters
None
### Description

## /<identifier>/jpg

## /<identifier>/jpg/technical_metadata
### URL Paramaters
None
### Description

## /<identifier>/ocr/limb
### URL Paramaters
None
### Description

## /<identifier>/ocr/jej
### URL Paramaters
None
### Description

## /<identifier>/ocr/pos
### URL Paramaters
None
### Description

## /<identifier>/pdf
### URL Paramaters
None
### Description

## /<identifier>/metadata
### URL Paramaters
None
### Description

# Development

Development of extensions for the digcoll_retriever is meant to be as painless as possible. No functionalities are required (though obviously your implementation will become more useful the more it implements, and some interfaces may impose their own functionality requirements).

## Existing Functionalities

### get_tif


## Developing a New Storage Specification

## Developing a New Functionality
