# Proxy Generator project
---
This repository is dedicated to improve the proxy generator of Self-Distributing Systems (SDS), here you may encounter the code necessary to auto-generate SDS proxy base on their .didl files. Check out the following topics on how to use it

## Usage
---
download this project inside yours, and just run ```python3 run sds-proxy-generator``` in the main forlder.

## DIDL definition
---
the DIDL definition is based on the following file:

```{
    "outputFolder": "component/output/folder",
    "remoteName": "define-a-name",
    "componentFile": "path/to/component.dn",
    "dependencies": [
        { "lib": "data.IntUtil", "alias": "iu" },
        { "lib": "utils.IntArrayUtil", "alias": "iau" }
    ],
    "attributes": {
        "state": {"type": "State", "calculateWith": "method"}
    },
    "methods": {
        "changeStateMethod": {
            "returnType": "void",
            "parameters": [
                {"name": "newState", "type": "State", "store": true}
            ]
        },
        "method": {
            "returnType": "State",
            "returnParser": "je.jsonToArray({}, typeof(State))",
            "remoteReturnParser": "je.jsonFromArray({})",
            "parameters": [
                {"name": "number", "type": "int", "store": true}
            ]
        }
        
    }
}
```