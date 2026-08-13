from helpers.write_component_helper import WriteComponentHelper

default_config = {
    "include_methods": [
        lambda file: WriteComponentHelper(file).provide_idented_flow("Response anycast(Request r)", [
            "int i = 0",
            "mutex(pointerLock){ i = addressPointer++ % remotes.arrayLength }",
            "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
            "return rpcUtil.make(reqWrapper)"
        ]),
        lambda file: WriteComponentHelper(file).provide_idented_flow("Response[] nonBlockingBroadcastList(Request r)", [
            "NonBlockRPC nbrpc = new NonBlockRPC()",
            "return nbrpc.nonBlockingBroadcastList(r, remotes)"
        ]),
    ] 
}

strategy_configs = {
    "replicate": {
        "dependencies": [
            { "lib": "libs.network.rpc.RPCUtil", "alias": "rpcUtil" },
            { "lib": "data.json.JSONEncoder", "alias": "je" },
            { "lib": "libs.utils.Constants", "alias": None },
            { "lib": "libs.network.rpc.NonBlockRPC", "alias": "nbrpcLib" }
        ],
        "charachteristics": {
            "weak": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response broadcast(Request r)", [
                    "Response res = nonBlockingBroadcastList(r)[0]",
                    "return res"
                ])
            ],
            "strong": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response broadcast(Request r)", [
                    "Response res = nonBlockingBroadcastList(r)[0]",
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
            { "lib": "libs.utils.Constants", "alias": None },
            { "lib": "libs.network.rpc.NonBlockRPC", "alias": "nbrpcLib" }
        ],
        "charachteristics": {
            "weak": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response hashcast(Request r, int hashKey)", [
                    "int i = 0",
                    "mutex(pointerLock){ i = hashKey % remotes.arrayLength }",
                    "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                    "return rpcUtil.make(reqWrapper)"
                ])
            ],
            "strong": [
                lambda file: WriteComponentHelper(file).provide_idented_flow("Response hashcast(Request r, int hashKey)", [
                    "int i = 0",
                    "mutex(pointerLock){ i = hashKey % remotes.arrayLength }",
                    "RequestWrapper reqWrapper = new RequestWrapper(remotes[i], r)",
                    "return rpcUtil.make(reqWrapper)"
                    # WriteComponentHelper(file).provide_idented_flow("mutex(pointerLock)", [
                    # ])
                ])
            ],
        },
        "methods": {
            "write_one": "hashcast",
            "write_many": ("split", "hashcast"),
            "read_one": "hashcast",
            "read_many": ("combine", "nonBlockingBroadcastList"),
            "global": "nonBlockingBroadcastList",
        }
    }
}
