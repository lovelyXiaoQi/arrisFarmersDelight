from ...ClientMod import *
class KeyBoardData:
    KeyBoardFuncMap = dict()
    GamePadFuncMap = dict()


@LoadingComponent
class KeyBoardPlugins(BaseComponent):
    def __init__(self):
        BaseComponent.__init__(self)

    @BaseComponent.ComponentListenEvent("OnKeyPressInGame")
    def OnKeyPress(self, args):
        KeyValue = args['key']
        isDown = args["isDown"]
        for keyBind in KeyBoardData.KeyBoardFuncMap:
            keyValue, state, funcName = keyBind.split("_")
            if KeyValue == keyValue and isDown == state:
                BindData = KeyBoardData.KeyBoardFuncMap[keyBind]
                func = BindData["func"]
                param = BindData["param"]
                func(param)

    @BaseComponent.ComponentListenEvent("OnGamepadKeyPressClientEvent")
    def OnGamePadPress(self, args):
        KeyValue = str(args['key'])
        isDown = args["isDown"]
        for keyBind in KeyBoardData.GamePadFuncMap:
            keyValue, state, funcName = keyBind.split("_")
            if KeyValue == keyValue and isDown == state:
                BindData = KeyBoardData.GamePadFuncMap[keyBind]
                func = BindData["func"]
                param = BindData["param"]
                func(param)

    def AddKeyFuncBind(self, keyValue, func, param=None, state="1"):
        BindData = {
            "func": func,
            "param": param
        }
        KeyBoardData.KeyBoardFuncMap["%s_%s_%s" % (keyValue, state, func.__name__)] = BindData

    def RemoveKeyFuncBind(self, keyValue, func, state="1"):
        if "%s_%s_%s" % (keyValue, state, func.__name__) in KeyBoardData.KeyBoardFuncMap:
            KeyBoardData.KeyBoardFuncMap.pop("%s_%s_%s" % (keyValue, state, func.__name__))

    def AddGamePadFuncBind(self, keyValue, func, param=None, state="1"):
        BindData = {
            "func": func,
            "param": param
        }
        KeyBoardData.GamePadFuncMap["%s_%s_%s" % (keyValue, state, func.__name__)] = BindData

    def RemoveGamePadFuncBind(self, keyValue, func, state="1"):
        if "%s_%s_%s" % (keyValue, state, func.__name__) in KeyBoardData.GamePadFuncMap:
            KeyBoardData.GamePadFuncMap.pop("%s_%s_%s" % (keyValue, state, func.__name__))


def AddKeyFuncBind(keyValue, func, param=None, state="1"):
    KeyBoardPlugins = GetComponent("KeyBoardPlugins") #type:KeyBoardPlugins
    KeyBoardPlugins.AddKeyFuncBind(keyValue, func, param, state)


def RemoveKeyFuncBind(keyValue, func, state="1"):
    KeyBoardPlugins = GetComponent("KeyBoardPlugins") #type:KeyBoardPlugins
    KeyBoardPlugins.RemoveKeyFuncBind(keyValue, func, state)


def AddGamePadFuncBind(keyValue, func, param=None, state="1"):
    KeyBoardPlugins = GetComponent("KeyBoardPlugins") #type:KeyBoardPlugins
    KeyBoardPlugins.AddGamePadFuncBind(keyValue, func, param, state)


def RemoveGamePadFuncBind(keyValue, func, state="1"):
    KeyBoardPlugins = GetComponent("KeyBoardPlugins") #type:KeyBoardPlugins
    KeyBoardPlugins.RemoveGamePadFuncBind(keyValue, func, state)
