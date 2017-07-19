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
