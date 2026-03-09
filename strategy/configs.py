from helpers.write_component_helper import WriteComponentHelper

strategy_configs = {
    "replicate": {
        "dependencies": [
            { "lib": "libs.network.rpc.RPCUtil", "alias": "rpcUtil" },
            { "lib": "data.json.JSONEncoder", "alias": "je" },
            { "lib": "libs.adaptation.AddressHandler", "alias": "ah" },
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
                ]),
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response anycast(Request r)", [
                    "int i = addressPointer++ % remotes.arrayLength",
                    "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                    "return rpcUtil.make(reqWrapper)"
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
                ]),
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response anycast(Request r)", [
                     WriteComponentHelper(file).provide_idented_flow("mutex(pointerLock)", [
                        "int i = addressPointer++ % remotes.arrayLength",
                        "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                        "return rpcUtil.make(reqWrapper)"
                    ])
                ])
            ]
        },
        "methods": {
            "write": "broadcast",
            "read": "anycast",
            "no_state": "anycast"
        }
    },
    "fragment": {
        "dependencies": [
            { "lib": "libs.network.rpc.RPCUtil", "alias": "rpcUtil" },
            { "lib": "data.json.JSONEncoder", "alias": "je" },
            { "lib": "libs.adaptation.AddressHandler", "alias": "ah" },
            { "lib": "libs.utils.Constants", "alias": None }
        ],
        "charachteristics": {
            "weak": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response hashcast(Request r, int hashKey)", [
                    "int i = hashKey % remotes.arrayLength",
                    "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                    "return rpcUtil.make(reqWrapper)"
                ]),
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response anycast(Request r)", [
                    "int i = addressPointer++ % remotes.arrayLength",
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
                ]),
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response anycast(Request r)", [
                    WriteComponentHelper(file).provide_idented_flow("mutex(pointerLock)", [
                        "int i = addressPointer++ % remotes.arrayLength",
                        "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                        "return rpcUtil.make(reqWrapper)"
                    ])
                ])
            ],
        },
        "methods": {
            "write": "hashcast",
            "read": "hashcast",
            "no_state": "anycast"
        }
    }
}
