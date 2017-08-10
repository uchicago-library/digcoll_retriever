# Schema for validating responses from the technical metadata endpoints
techmd_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "width": {"type": "integer"},
        "height":  {"type": "integer"}
    },
}

# Schema for validating responses from the stat endpoints
stat_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "identifier": {"type": "string",
                       "pattern": "^.+$"},
        "contexts_available": {"type": "array",
                               "items": {"type": "string",
                                         "pattern": "^.*$"},
                               "minItems": 0}
    }
}

# Schema for validating responses from the root endpoint
root_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "status": {"type": "string",
                  "pattern": "^Not broken!$"}
    }
}
