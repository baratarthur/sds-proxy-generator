from helpers.write_component_helper import WriteComponentHelper

default_config = {
    "include_methods": [
        lambda file: WriteComponentHelper(file).provide_idented_flow("Response[] broadcastList(Request r)", [
            "Response res[] = new Response[]()",
            WriteComponentHelper(file).provide_idented_flow("for(int i = 0; i < remotes.arrayLength; i++)", [
                "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                "Response singleRes = rpcUtil.make(reqWrapper)",
                "res = new Response[](res, singleRes)"
            ]),
            "return res"
        ]),
        lambda file: WriteComponentHelper(file).provide_idented_flow("Response anycast(Request r)", [
            "int i = addressPointer++ % remotes.arrayLength",
            "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
            "return rpcUtil.make(reqWrapper)"
        ])
    ] 
}

strategy_configs = {
    "replicate": {
        "dependencies": [
            { "lib": "libs.network.rpc.RPCUtil", "alias": "rpcUtil" },
            { "lib": "data.json.JSONEncoder", "alias": "je" },
            { "lib": "libs.utils.Constants", "alias": None }
        ],
        "charachteristics": {
            "weak": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response broadcast(Request r)", [
                    "Response res",
                    WriteComponentHelper(file).provide_idented_flow("mutex(pointerLock)", [
                        WriteComponentHelper(file).provide_idented_flow("for(int i = 0; i < remotes.arrayLength; i++)", [
                            "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                            "res = rpcUtil.make(reqWrapper)"
                        ])
                    ]),
                    "return res"
                ])
            ],
            "strong": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response broadcast(Request r)", [
                    "Response res",
                    WriteComponentHelper(file).provide_idented_flow("mutex(pointerLock)", [
                        WriteComponentHelper(file).provide_idented_flow("for(int i = 0; i < remotes.arrayLength; i++)", [
                            "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                            "res = rpcUtil.make(reqWrapper)"
                        ])
                    ]),
                    "return res"
                ])
            ]
        },
        "methods": {
            "write": "broadcast",
            "read": "anycast",
        }
    },
    "fragment": {
        "dependencies": [
            { "lib": "libs.network.rpc.RPCUtil", "alias": "rpcUtil" },
            { "lib": "data.json.JSONEncoder", "alias": "je" },
            { "lib": "libs.utils.Constants", "alias": None }
        ],
        "charachteristics": {
            "weak": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response hashcast(Request r, int hashKey)", [
                    "int i = hashKey % remotes.arrayLength",
                    "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                    "return rpcUtil.make(reqWrapper)"
                ])
            ],
            "strong": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response hashcast(Request r, int hashKey)", [
                    WriteComponentHelper(file).provide_idented_flow("mutex(pointerLock)", [
                        "int i = hashKey % remotes.arrayLength",
                        "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                        "return rpcUtil.make(reqWrapper)"
                    ])
                ])
            ],
        },
        "methods": {
            "write_one": "hashcast",
            "write_many": ("split", "hashcast"),
            "read_one": "hashcast",
            "read_many": ("combine", "broadcastList")
        }
    }
}
