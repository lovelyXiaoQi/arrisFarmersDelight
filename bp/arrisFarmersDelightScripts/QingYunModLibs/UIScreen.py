# -*- coding: utf-8 -*-
import copy

from SystemApi import *
import mod.client.extraClientApi as clientApi
import ClientApi
_ScreenNode = clientApi.GetScreenNodeCls()
_ButtonCallBackDict = {}
_ButtonCallBack = {
    "ButtonPath": "",
    "ButtonState": [],
    "BackFunc": [],
    "ButtonObj": None
}
_GirdBlockPathDict = {}
_ViewBinder = clientApi.GetViewBinderCls()
_GameTickFunc = []
_TickName = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("TickName")
_PressLongTimeDict = {}
_PressLongBackFuncDict = {}
_PressingCompTimerDict = {}
_LongPressButtonDataList = []
_CompDataLib = {}


class UIScreen(_ScreenNode):
    def __init__(self, ns, nm, par):
        _ScreenNode.__init__(self, ns, nm, par)
        self.NameSpace = ns
        ListenClientEvents("OnScriptTickClient", self.GetToggle)

    def Create(self):
        for ButtonPath in _ButtonCallBackDict:
            ButtonStateList = _ButtonCallBackDict[ButtonPath]["ButtonState"]
            BackFuncList = _ButtonCallBackDict[ButtonPath]["BackFunc"]
            ButtonStateCount = 0
            for BackFunc in BackFuncList:
                ButtonState = ButtonStateList[ButtonStateCount]
                ButtonStateCount += 1
                self.Button_Control(ButtonPath, ButtonState, BackFunc, True)

        def __StopCompTimer(args):
            ButtonPath = args['ButtonPath']
            Timer = _PressingCompTimerDict[ButtonPath]
            ClientComp.CreateGame(levelId).CancelTimer(Timer)
            _PressingCompTimerDict.pop(ButtonPath)
            args["IsPress"] = False
            BackFunc = _PressLongBackFuncDict[ButtonPath]
            BackFunc(args)

        def __StartCompTimer(args):
            ButtonPath = args['ButtonPath']
            PressTime = _PressLongTimeDict[ButtonPath]
            BackFunc = _PressLongBackFuncDict[ButtonPath]
            args["IsPress"] = None
            BackFunc(args)
            args["IsPress"] = True
            Timer = ClientComp.CreateGame(levelId).AddTimer(PressTime, BackFunc, args)
            _PressingCompTimerDict[ButtonPath] = Timer

        for LongPressData in _LongPressButtonDataList:
            uiName, ButtonPath, PressTime, BackFunc = LongPressData
            _PressLongTimeDict[ButtonPath] = PressTime
            _PressLongBackFuncDict[ButtonPath] = BackFunc
            ButtonObj = UIModComp(uiName).GetBaseUIControl(ButtonPath).asButton()
            ButtonObj.AddTouchEventParams({"isSwallow": False})
            ButtonObj.SetButtonTouchDownCallback(__StartCompTimer)
            ButtonObj.SetButtonTouchUpCallback(__StopCompTimer)
            ButtonObj.SetButtonTouchCancelCallback(__StopCompTimer)

    def Button_Control(self, ButtonPath, ButtonState, BackFunc, Reload=False):
        if (not _ButtonCallBackDict[ButtonPath]["ButtonObj"]) or Reload:
            _ButtonCallBackDict[ButtonPath]["ButtonObj"] = self.GetBaseUIControl(ButtonPath).asButton()
            self.GetBaseUIControl(ButtonPath).asButton().AddTouchEventParams({"isSwallow": _ButtonCallBackDict[ButtonPath]["IsSwallow"]})
        ButtonObj = _ButtonCallBackDict[ButtonPath]["ButtonObj"]
        ControlDict = {
            "Down": ButtonObj.SetButtonTouchDownCallback,
            "Up": ButtonObj.SetButtonTouchUpCallback,
            "Cancel": ButtonObj.SetButtonTouchCancelCallback,
            "HoverIn": ButtonObj.SetButtonHoverInCallback,
            "HoverOut": ButtonObj.SetButtonHoverOutCallback,
            "Move": ButtonObj.SetButtonTouchMoveCallback,
            "MoveIn": ButtonObj.SetButtonTouchMoveInCallback,
            "MoveOut": ButtonObj.SetButtonTouchMoveOutCallback
        }
        print ButtonPath, ButtonState, BackFunc
        ControlDict[ButtonState](BackFunc)

    @_ViewBinder.binding(_ViewBinder.BF_BindString, "#tick_text_show")
    def GameTick(self):
        for TickFunc in _GameTickFunc:
            TickFunc()

    def Update(self):
        for Func in _GameTickFunc:
            Func()

    def GetToggle(self):
        if not clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).GetAttr(self.NameSpace+"_"+"ToggleBack"):
            clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).SetAttr(self.NameSpace + "_" + "ToggleBack", {})
        for ToggleControl in clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).GetAttr(self.NameSpace+"_"+"ToggleBack"):
            Toggle = ToggleControl.split("/")
            Last = Toggle.pop()
            NewToggle = ""
            for Tog in Toggle:
                if Tog != "":
                    NewToggle += "/" + Tog

            if not self.GetBaseUIControl(NewToggle): continue

            State = self.GetBaseUIControl(NewToggle).asSwitchToggle().GetToggleState("/" + Last)

            if not clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).GetAttr(self.NameSpace):
                clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).SetAttr(self.NameSpace, {})

            StateData = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).GetAttr(self.NameSpace)

            if State != clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).GetAttr(self.NameSpace).get(ToggleControl, None):
                BackFunc = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).GetAttr(self.NameSpace+"_"+"ToggleBack")[ToggleControl]
                BackFunc(State)

            StateData[ToggleControl] = State

            clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).SetAttr(self.NameSpace, StateData)


def ReloadButtonBack(uiName):
    """
    重载所有按钮注册绑定

    :param uiName: 指定控件的UI命名空间
    """
    UIModComp(uiName).Create()


def UIModComp(uiName):
    """
    获取UI对象实例

    :param uiName: 需要获取的ui实例名称
    :return 获取的ui实例对象
    """
    return clientApi.GetUI(QingYunMod.ModObject.ModName, uiName)


def AddButtonTouch(ButtonPath, ButtonState, BackFunc, IsSwallow=True, uiName=None):
    """
    添加UI中按钮的回调函数，需要传入按钮的路径，触发的状态，以及触发时调用的回调函数

    :param ButtonPath: 按钮的路径
    :param ButtonState: 触发状态(Down：按下，Up：抬起，Cancel：触控外弹起，HoverIn：鼠标进入按钮，HoverOut：鼠标离开按钮，Move：按下按钮移动时，MoveIn：按下按钮进入控件，MoveOut：按下按钮移出控件)
    :param BackFunc: 触发时调用的回调函数
    :param IsSwallow: 是否吞噬点击操作与游戏的交互
    :param uiName: UI命名空间
    """
    if ButtonPath in _ButtonCallBackDict:
        Button = _ButtonCallBackDict[ButtonPath]
        ButtonCount = 0
        for State in Button["ButtonState"]:
            Func = Button["BackFunc"][ButtonCount]
            ButtonCount += 1
            if (ButtonPath == Button["ButtonPath"]) and (ButtonState == State) and (BackFunc.__name__ == Func.__name__):
                if UIModComp(uiName): AddSuperButtonTouch(uiName, ButtonPath, ButtonState, BackFunc)
                print "Reload Button: Button %s State %s Func %s\n" % (ButtonPath, ButtonState, BackFunc.__name__)
                return BackFunc
            else:
                if ButtonCount + 1 >= len(Button["ButtonState"]):
                    Button["ButtonState"].append(ButtonState)
                    Button["BackFunc"].append(BackFunc)
                    Button["IsSwallow"] = IsSwallow
                    return BackFunc
    else:
        Button = {"ButtonPath": ButtonPath, "ButtonState": [], "BackFunc": [], "ButtonObj": None}
        Button["ButtonState"].append(ButtonState)
        Button["BackFunc"].append(BackFunc)
        Button["IsSwallow"] = IsSwallow
        _ButtonCallBackDict[ButtonPath] = Button


def AddButton(ButtonPath, ButtonState, IsSwallow=True, uiName=None):
    """
    添加UI中按钮的回调函数，需要传入按钮的路径，触发的状态，以及触发时调用的回调函数

    :param ButtonPath: 按钮的路径
    :param ButtonState: 触发状态(Down：按下，Up：抬起，Cancel：触控外弹起，HoverIn：鼠标进入按钮，HoverOut：鼠标离开按钮，Move：按下按钮移动时，MoveIn：按下按钮进入控件，MoveOut：按下按钮移出控件)
    :param IsSwallow: 是否吞噬点击操作与游戏的交互
    :param uiName: UI命名空间
    """
    def Add(BackFunc):
        if ButtonPath in _ButtonCallBackDict:
            Button = _ButtonCallBackDict[ButtonPath]
            ButtonCount = 0
            for State in Button["ButtonState"]:
                Func = Button["BackFunc"][ButtonCount]
                ButtonCount += 1
                if (ButtonPath == Button["ButtonPath"]) and (ButtonState == State) and (BackFunc.__name__ == Func.__name__):
                    if UIModComp(uiName): AddSuperButtonTouch(uiName, ButtonPath, ButtonState, BackFunc)
                    print "Reload Button: Button %s State %s Func %s\n" % (ButtonPath, ButtonState, BackFunc.__name__)
                    return BackFunc
                else:
                    if ButtonCount+1 >= len(Button["ButtonState"]):
                        Button["ButtonState"].append(ButtonState)
                        Button["BackFunc"].append(BackFunc)
                        Button["IsSwallow"] = IsSwallow
                        return BackFunc
        else:
            Button = {"ButtonPath": ButtonPath, "ButtonState": [], "BackFunc": [], "ButtonObj": None}
            Button["ButtonState"].append(ButtonState)
            Button["BackFunc"].append(BackFunc)
            Button["IsSwallow"] = IsSwallow
            _ButtonCallBackDict[ButtonPath] = Button
        return BackFunc
    return Add


def AddSuperButtonTouch(uiName, ButtonPath, ButtonState, BackFunc, IsSwallow=True):
    """
    添加UI中按钮的回调函数，需要传入按钮的路径，触发的状态，以及触发时调用的回调函数(强制添加按钮回调，可能造成按钮重复注册回调，非必须情况请尽量不要使用)

    :param ButtonPath: 按钮的路径
    :param ButtonState: 触发状态(Down：按下，Up：抬起，Cancel：触控外弹起，HoverIn：鼠标进入按钮，HoverOut：鼠标离开按钮，Move：按下按钮移动时，MoveIn：按下按钮进入控件，MoveOut：按下按钮移出控件)
    :param BackFunc: 触发时调用的回调函数
    :param IsSwallow: 是否吞噬点击操作与游戏的交互
    """
    ButtonObj = UIModComp(uiName).GetBaseUIControl(ButtonPath).asButton()
    ButtonObj.AddTouchEventParams({"isSwallow": IsSwallow})
    ControlDict = {
        "Down": ButtonObj.SetButtonTouchDownCallback,
        "Up": ButtonObj.SetButtonTouchUpCallback,
        "Cancel": ButtonObj.SetButtonTouchCancelCallback,
        "HoverIn": ButtonObj.SetButtonHoverInCallback,
        "HoverOut": ButtonObj.SetButtonHoverOutCallback,
        "Move": ButtonObj.SetButtonTouchMoveCallback,
        "MoveIn": ButtonObj.SetButtonTouchMoveInCallback,
        "MoveOut": ButtonObj.SetButtonTouchMoveOutCallback
    }
    ControlDict[ButtonState](BackFunc)


def AddSuperButton(uiName, ButtonPath, ButtonState, IsSwallow=True):
    """
    添加UI中按钮的回调函数，需要传入按钮的路径，触发的状态，以及触发时调用的回调函数(强制添加按钮回调，可能造成按钮重复注册回调，非必须情况请尽量不要使用)

    :param uiName: UI命名空间
    :param ButtonPath: 按钮的路径
    :param ButtonState: 触发状态(Down：按下，Up：抬起，Cancel：触控外弹起，HoverIn：鼠标进入按钮，HoverOut：鼠标离开按钮，Move：按下按钮移动时，MoveIn：按下按钮进入控件，MoveOut：按下按钮移出控件)
    :param IsSwallow: 是否吞噬点击操作与游戏的交互
    """
    def Add(BackFunc):
        ButtonObj = UIModComp(uiName).GetBaseUIControl(ButtonPath).asButton()
        ButtonObj.AddTouchEventParams({"isSwallow": IsSwallow})
        ControlDict = {
            "Down": ButtonObj.SetButtonTouchDownCallback,
            "Up": ButtonObj.SetButtonTouchUpCallback,
            "Cancel": ButtonObj.SetButtonTouchCancelCallback,
            "HoverIn": ButtonObj.SetButtonHoverInCallback,
            "HoverOut": ButtonObj.SetButtonHoverOutCallback,
            "Move": ButtonObj.SetButtonTouchMoveCallback,
            "MoveIn": ButtonObj.SetButtonTouchMoveInCallback,
            "MoveOut": ButtonObj.SetButtonTouchMoveOutCallback
        }
        ControlDict[ButtonState](BackFunc)
        return BackFunc
    return Add


def SetScreenVisible(uiName, Visible=True):
    """
    设置UI是否显示在屏幕上，True为显示，False为不显示

    :param uiName: 需要进行操作的UI名称
    :param Visiable: 是否显示（True为显示，False为不显示）
    """
    UIModComp(uiName).SetScreenVisible(Visible)


def SetVisible(uiName, CompPath, Visible=True):
    """
    设置某控件是否显示在UI上，True为显示，False为不显示

    :param uiName: 需要进行操作的UI名称
    :param CompPath: 控件路径
    :param Visible: 是否显示（True为显示，False为不显示）
    """
    UIModComp(uiName).GetBaseUIControl(CompPath).SetVisible(Visible)


def GetVisible(uiName, CompPath):
    """
    获取某控件是否显示在UI上，返回值为显示状态，True为显示，False为不显示

    :param uiName: 需要进行操作的UI名称
    :param CompPath: 控件路径
    :return: 显示状态（True为显示，False为不显示）
    """
    return UIModComp(uiName).GetBaseUIControl(CompPath).GetVisible()


def GetIsHud(uiName):
    """
    获取该UI的输入模式（0：不穿透触控模式，1：穿透触控模式）

    :param str uiName: 需要进行操作的UI名称
    :return: 输入模式
    """
    return UIModComp(uiName).GetIsHud()


def SetIsHud(uiName, IsHud=0):
    """
    设置该UI的输入模式（0：不穿透触控模式，1：穿透触控模式）

    :param str uiName: 需要进行操作的UI名称
    :param int IsHud: 输入模式
    :return:
    """
    UIModComp(uiName).SetIsHud(IsHud)


def Clone(uiName, CompPath, ParentPath, NewName, syncRefresh=True, forceUpdate=True):
    """
    克隆一个已有的控件，修改它的名称，并将它挂接到指定的父节点上，目前文本、图片、按钮控件的克隆控件表现正常，其他复杂控件的克隆控件可能存在运行问题，建议在json编写的过程中，手动复制一份对应控件使用

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要复制的控件路径
    :param str ParentPath: 新控件的父控件路径
    :param str NewName: 新控件的控件名
    :return: 是否成功克隆控件, 新控件的路径
    """
    NewCompPath = ParentPath + "/" + NewName
    return UIModComp(uiName).Clone(CompPath, ParentPath, NewName, syncRefresh, forceUpdate), NewCompPath


def SetCompPosition(uiName, CompPath, Position, FollowType="none", PosModel=False):
    """
    设置某一控件的偏移锚点坐标，可以设置为比例形式或者绝对值形式的坐标

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要设置坐标的控件路径
    :param dict Position: 设置的坐标偏移量(屏幕左上角为（0，0）且往右下延申坐标系)
    :param str FollowType: 比例跟随的控件
    :param bool PosModel: 设置为比例或者绝对值坐标
    """
    if PosModel:
        UIModComp(uiName).GetBaseUIControl(CompPath).SetFullPosition("x", {"followType": FollowType,
                                                                           "relativeValue": Position['x']})
        UIModComp(uiName).GetBaseUIControl(CompPath).SetFullPosition("y", {"followType": FollowType,
                                                                           "relativeValue": Position['y']})

    else:
        UIModComp(uiName).GetBaseUIControl(CompPath).SetFullPosition("x", {"followType": FollowType,
                                                                           "absoluteValue": Position['x']})
        UIModComp(uiName).GetBaseUIControl(CompPath).SetFullPosition("y", {"followType": FollowType,
                                                                           "absoluteValue": Position['y']})


def GetCompPosition(uiName, CompPath):
    """
    获取某一控件的偏移锚点坐标，可以获取比例形式或者绝对值形式的坐标

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要获取坐标的控件路径
    :return: 获取的控件偏移锚点坐标
    """
    SizeDict = {}
    for pos in ["x", "y"]:
        Dict = UIModComp(uiName).GetBaseUIControl(CompPath).GetFullSize(pos)
        SizeDict[pos] = Dict
    return SizeDict


def GetCompMustPosition(uiName, CompPath, ModName=QingYunMod.ModObject.ModName):
    """
    获取某一控件的绝对全局屏幕坐标

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要获取坐标的控件路径
    """
    Pos_X = 0
    Pos_Y = 0
    ParentPath = str(CompPath).split("/")
    for Num in range(1, len(str(CompPath).split("/"))):
        NewComp = ""
        for Comp in ParentPath:
            if Comp == "":
                continue
            NewComp = NewComp + "/" + Comp
        X, Y = clientApi.GetUI(ModName, uiName).GetBaseUIControl(NewComp).GetPosition()
        Pos_X = Pos_X + X
        Pos_Y = Pos_Y + Y
        ParentPath.pop(-1)
    CompData = GetCompData(uiName, CompPath)
    if CompData: CompData.NowPos = (Pos_X, Pos_Y)
    return Pos_X, Pos_Y


def SetCompMustPosition(uiName, CompPath, Pos):
    """
    设置某一控件的绝对全局屏幕坐标

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要设置坐标的控件路径
    :param tuple Pos: 控件绝对坐标
    """
    Pos_X, Pos_Y = Pos
    ParentPath = str(CompPath).split("/")
    for Num in range(1, len(str(CompPath).split("/"))):
        ParentPath.pop(-1)
        NewComp = ""
        for Comp in ParentPath:
            if Comp == "":
                continue
            NewComp = NewComp + "/" + Comp
        X, Y = UIModComp(uiName).GetBaseUIControl(NewComp).GetPosition()
        Pos_X = Pos_X - X
        Pos_Y = Pos_Y - Y
    UIModComp(uiName).GetBaseUIControl(CompPath).SetPosition((Pos_X, Pos_Y))


def SetCompAlpha(uiName, CompPath, Alpha=1.0):
    """
    设置某一控件的透明度

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要设置透明度控件的路径
    :param float Alpha: 透明度，取值0-1之间，0表示完全透明，1表示完全不透明
    """
    GetCompData(uiName, CompPath).NowAlpha = Alpha
    UIModComp(uiName).GetBaseUIControl(CompPath).SetAlpha(Alpha)


def GetCompAlpha(uiName, CompPath):
    """
    获取某一控件的透明度

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要获取透明度控件的路径
    """
    CompData = GetCompData(uiName, CompPath)
    if not CompData: return
    return CompData.NowAlpha


def GetCompSize(uiName, CompPath):
    """
    获取某一控件的大小

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要获取大小信息的控件路径
    """
    CompData = GetCompData(uiName, CompPath)
    Size = UIModComp(uiName).GetBaseUIControl(CompPath).GetSize()
    if not CompData: return Size
    CompData.NowScale = Size
    return CompData.NowScale


def SetCompSize(uiName, CompPath, Size, resizeChildren=False):
    """
    设置某一控件的大小

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要设置大小的控件路径
    :param tuple Size: 需要设置的大小(x, y)
    """
    CompData = GetCompData(uiName, CompPath)
    UIModComp(uiName).GetBaseUIControl(CompPath).SetSize(Size, resizeChildren)
    CompData.NowScale = Size


def GetCompData(uiName, CompPath):
    """
    获取某一控件的组件类

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 控件路径
    """
    CompData = _CompDataLib.get(uiName + "|" + CompPath, None)
    if not CompData:
        try:
            Pos = GetCompMustPosition(uiName, CompPath)
            CompData = _CompData(uiName, CompPath, Pos, 1.0)
        except:
            print Bcolors.ERROR + "No Comp %s" % CompData
    return CompData


def RemoveComponent(uiName, CompPath):#删除组件
    """
    动态删除某一控件

    :param str uiName: 需要进行操作的UI名称
    :param str CompPath: 需要删除的控件路径
    """
    ParentPath = ""
    PathList = str(CompPath).split("/")
    PathList.pop()
    for Comp in PathList:
        if Comp != "":
            ParentPath = ParentPath + "/" + Comp
    UIModComp(uiName).RemoveComponent(CompPath, ParentPath)


class __Gird(object):
    def __init__(self, uiname, GirdScreenPath, BlockPath):
        self.BlockNum = 0
        self.uiName = uiname
        self.GirdScreenPath = GirdScreenPath
        self.BlockPath = BlockPath

    def CreateGird(self, BlockNum_X, BlockNum_Y, TestBySelf=True, PosModel=False, Interval_X=0, Interval_Y=0, Point_X=0, Point_Y=0, Motion_X=0, Motion_Y=0):
        GirdBlockDict = _GirdBlockPathDict.get(self.GirdScreenPath, {})
        for GirdBlock in GirdBlockDict:
            RemoveComponent(self.uiName, GirdBlock)
        _GirdBlockPathDict[self.GirdScreenPath] = {}
        GirdBlockPath = {}
        for X in range(1, BlockNum_X+1):
            for Y in range(1, BlockNum_Y+1):
                if TestBySelf:
                    NewBlockPath = self.AddBlock()
                    GirdBlockPath[str(X)+"."+str(Y)] = NewBlockPath
                    SetCompPosition(self.uiName, NewBlockPath, {"x": round((100/float(BlockNum_X))/100*(X-1), 2)+float(Point_X)/100, "y": round((100/float(BlockNum_Y))/100*(Y-1), 2)+float(Point_Y)/100}, "parent", PosModel)
                    Data = ({"x": round((100/float(BlockNum_X))/100*(X-1), 2)+float(Point_X)/100, "y": round((100/float(BlockNum_Y))/100*(Y-1), 2)+float(Point_Y)/100}, "parent", PosModel)
                    _GirdBlockPathDict[self.GirdScreenPath][NewBlockPath] = Data

                else:
                    NewBlockPath = self.AddBlock()
                    GirdBlockPath[str(X)+"."+str(Y)] = NewBlockPath
                    if not PosModel:
                        SetCompPosition(self.uiName, NewBlockPath, {"x": Interval_X * (X - 1)+Point_X+Motion_X*(Y - 1), "y": -Interval_Y * (Y - 1)+Point_Y+Motion_Y*(X - 1)}, "none", PosModel)
                        Data = ({"x": Interval_X * (X - 1)+Point_X+Motion_X*(Y - 1), "y": -Interval_Y * (Y - 1)+Point_Y+Motion_Y*(X - 1)}, "none", PosModel)
                    else:
                        SetCompPosition(self.uiName, NewBlockPath, {"x": float(Interval_X * (X - 1))/100+float(Point_X)/100+float(Motion_X*(Y - 1))/100, "y": float(-Interval_Y * (Y - 1))/100+float(Point_Y)/100+float(Motion_X*(Y - 1))/100}, "parent", PosModel)
                        Data = ({"x": float(Interval_X * (X - 1))/100+float(Point_X)/100+float(Motion_X*(Y - 1))/100, "y": float(-Interval_Y * (Y - 1))/100+float(Point_Y)/100+float(Motion_X*(Y - 1))/100}, "parent", PosModel)
                    _GirdBlockPathDict[self.GirdScreenPath][NewBlockPath] = Data
        UIModComp(self.uiName).UpdateScreen()
        SetCompPosition(self.uiName, self.BlockPath, {"x": 10000, "y": 10000}, "parent", False)
        return GirdBlockPath

    def InSideGird(self):
        GirdBlockList = _GirdBlockPathDict.get(self.GirdScreenPath, {})
        for GirdBlock in GirdBlockList:
            RemoveComponent(self.uiName, GirdBlock)

    def ShowGird(self):
        GirdBlockDict = _GirdBlockPathDict.get(self.GirdScreenPath, {})
        for GirdBlock in GirdBlockDict:
            Data = GirdBlockDict[GirdBlock]
            a, b, c = Data
            NewBlockName = str(GirdBlock).split("/")[-1]
            Default, NewBlockPath = Clone(self.uiName, self.BlockPath, self.GirdScreenPath, NewBlockName, False, True)
            SetCompPosition(self.uiName, NewBlockPath, a, b, c)
        UIModComp(self.uiName).UpdateScreen()

    def AddBlock(self):
        BlockName = str(self.BlockPath).split("/")[-1]
        self.BlockNum += 1
        NewBlockName = BlockName+str(self.BlockNum)
        Default, NewBlockPath = Clone(self.uiName, self.BlockPath, self.GirdScreenPath, NewBlockName, False, True)
        return NewBlockPath


class __Scroll_View(object):
    def __init__(self, uiName, Scroll_ViewScreenPath, BlockPath):
        self.uiName = uiName
        self.Scroll_ViewScreenPath = Scroll_ViewScreenPath
        self.BlockPath = BlockPath
        if not clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("Scroll_View"):
            clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).SetAttr("Scroll_View", {})

    def RegisterScroll_View(self, MoveModel, TestBySelf, Size, TouchSize, Rotate):
        if MoveModel in ["horizontally", "vertical"]:
            UIModComp(self.uiName).GetBaseUIControl(self.Scroll_ViewScreenPath).SetClipsChildren(True)
            Scroll_ViewDict = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("Scroll_View")
            Scroll_ViewDict[self.Scroll_ViewScreenPath] = {
                "BlockPath": self.BlockPath,
                "MoveModel": MoveModel,
                "uiName": self.uiName,
                "IsMoving": False,
                "Rotate": Rotate,
                "ModName": QingYunMod.ModObject.ModName
            }
            if TestBySelf:
                Scroll_ViewDict[self.Scroll_ViewScreenPath]["Size"] = UIModComp(self.uiName).GetBaseUIControl(self.BlockPath).GetSize()
                Scroll_ViewDict[self.Scroll_ViewScreenPath]["TouchSize"] = UIModComp(self.uiName).GetBaseUIControl(self.Scroll_ViewScreenPath).GetSize()
            else:
                Scroll_ViewDict[self.Scroll_ViewScreenPath]["Size"] = Size
                Scroll_ViewDict[self.Scroll_ViewScreenPath]["TouchSize"] = TouchSize

            clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).SetAttr("Scroll_View", Scroll_ViewDict)


def CreateGird(uiName, GirdScreenPath, BlockPath, param):
    """
    创建一个动态表格(网格)控件

    :param str uiName: 需要进行操作的UI名称
    :param str GirdScreenPath: 表格基类面板的控件路径
    :param str BlockPath: 表格内容的模板控件路径
    :param dict param: 表格生成格式参数{'blockNum_x': 表格的横坐标大小, 'blockNum_y': 表格的纵坐标大小, 'testBySelf': 表格排列是否自适应, 'posModel': 坐标参数的数值类型(True为相对于父控件的比例值，False为绝对值，默认False), 'interval_x': 横坐标控件之间的间隔, 'interval_y': 纵坐标控件之间的间隔, 'point_x': 表格内容的横坐标起点, 'point_y': 表格内容的纵坐标起点 }

    :return: 返回生成的内容控件路径字典以及网格对象
    """
    BlockNum_X = param['blockNum_x']
    BlockNum_Y = param['blockNum_y']
    TestBySelf = param.get('testBySelf', True)
    PosModel = param.get('posModel', False)
    Interval_X = param.get('interval_x', 0)
    Interval_Y = param.get('interval_y', 0)
    point_x = param.get('point_x', 0)
    point_y = param.get('point_y', 0)
    Motion_X = param.get('Motion_X', 0)
    Motion_Y = param.get('Motion_Y', 0)
    GirdObj = __Gird(uiName, GirdScreenPath, BlockPath)
    return GirdObj.CreateGird(BlockNum_X, BlockNum_Y, TestBySelf, PosModel, Interval_X, Interval_Y, point_x, point_y, Motion_X, Motion_Y), GirdObj


def CreateScroll_View(uiName, Scroll_ViewScreenPath, BlockPath, MoveModel, TestBySelf=True, Size=None, TouchSize=None, Rotate=0):
    """
    创建一个滑动框控件(可与动态网格控件混用)

    :param str uiName: UI命名空间
    :param str Scroll_ViewScreenPath: 滑动框画布控件路径(可见大小取决于画布大小)
    :param str BlockPath: 滑动块内容控件路径(可滑动展示的部分)
    :param str MoveModel: 滑动模式(竖直方向："vertical"， 水平方向："horizontally")
    :param bool TestBySelf: 自适应布局
    :param tuple Size: 滑动框显示内容大小(如已经启动了TestBySelf自适应布局，则无需再传入该值)
    :param tuple TouchSize: 滑动框触控范围大小，用于确定可调整滑动框的点击范围大小(TestBySelf自适应布局启动后会如不设置会自动于Size大小同步)
    :param float Rotate: 滚动列表倾斜的角度大小
    """
    __Scroll_View(uiName, Scroll_ViewScreenPath, BlockPath).RegisterScroll_View(MoveModel, TestBySelf, Size, TouchSize, Rotate)


def AddGameTickFunc(Func):
    """
    添加UITick函数绑定

    :param Func: 需要绑定的函数
    """
    if Func in _GameTickFunc:
        _GameTickFunc.remove(Func)
    _GameTickFunc.append(Func)


def AddGameTick(Func):
    """
    添加UITick函数绑定(装饰器函数)

    :param Func: 需要绑定的函数
    """
    if Func in _GameTickFunc:
        _GameTickFunc.remove(Func)
    _GameTickFunc.append(Func)


def AddToggleBack(uiName, ToggleControl, BackFunc):
    """
    添加开关交互回调绑定

    :param uiName: 指定开关控件UI命名控件
    :param ToggleControl: 指定开关控件路径(控件需填写到核心开关控件处，一般为"/this_toggle")
    :param BackFunc: 开关交互触发绑定的回调函数
    """
    ToggleBackDict = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).GetAttr(uiName+"_"+"ToggleBack")
    if not ToggleBackDict:
        ToggleBackDict = {}
    ToggleBackDict[ToggleControl] = BackFunc
    clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).SetAttr(uiName+"_"+"ToggleBack", ToggleBackDict)


def AddToggle(uiName, ToggleControl):
    """
    添加开关交互回调绑定(装饰器函数)

    :param uiName: 指定开关控件UI命名控件
    :param ToggleControl: 指定开关控件路径(控件需填写到核心开关控件处，一般为"/this_toggle")
    """
    def Add(BackFunc):
        ToggleBackDict = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).GetAttr(
            uiName + "_" + "ToggleBack")
        if not ToggleBackDict:
            ToggleBackDict = {}
        ToggleBackDict[ToggleControl] = BackFunc
        clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLocalPlayerId()).SetAttr(
            uiName + "_" + "ToggleBack", ToggleBackDict)
        return BackFunc
    return Add


def AddLongPressBack(uiName, ButtonPath, PressTime, BackFunc):
    """
    添加长按绑定按钮，可将某个按钮绑定长按交互功能

    :param uiName: 指定按钮所处的UI命名控件
    :param ButtonPath: 指定控件的相对UI根节点路径
    :param PressTime: 长按响应时间
    :param BackFunc: 各交互状态触发的回调函数
    """
    LongPressData = [uiName, ButtonPath, PressTime, BackFunc]
    _LongPressButtonDataList.append(LongPressData)


def AddSuperLongPressBack(uiName, ButtonPath, PressTime, BackFunc):
    """
    添加长按绑定按钮，可将某个按钮绑定长按交互功能(强制超添加，建议在动态添加按钮时使用)

    :param uiName: 指定按钮所处的UI命名控件
    :param ButtonPath: 指定控件的相对UI根节点路径
    :param PressTime: 长按响应时间
    :param BackFunc: 各交互状态触发的回调函数
    """
    _PressLongTimeDict[ButtonPath] = PressTime
    _PressLongBackFuncDict[ButtonPath] = BackFunc
    ButtonObj = UIModComp(uiName).GetBaseUIControl(ButtonPath).asButton()
    ButtonObj.AddTouchEventParams({"isSwallow": False})
    ButtonObj.SetButtonTouchDownCallback(__StartCompTimer)
    ButtonObj.SetButtonTouchUpCallback(__StopCompTimer)
    ButtonObj.SetButtonTouchCancelCallback(__StopCompTimer)


def __StopCompTimer(args):
    ButtonPath = args['ButtonPath']
    Timer = _PressingCompTimerDict[ButtonPath]
    ClientComp.CreateGame(levelId).CancelTimer(Timer)
    _PressingCompTimerDict.pop(ButtonPath)
    args["IsPress"] = False
    BackFunc = _PressLongBackFuncDict[ButtonPath]
    BackFunc(args)


def __StartCompTimer(args):
    ButtonPath = args['ButtonPath']
    PressTime = _PressLongTimeDict[ButtonPath]
    BackFunc = _PressLongBackFuncDict[ButtonPath]
    args["IsPress"] = None
    BackFunc(args)
    args["IsPress"] = True
    Timer = ClientComp.CreateGame(levelId).AddTimer(PressTime, BackFunc, args)
    _PressingCompTimerDict[ButtonPath] = Timer


def AddButtonTouchMoving(uiName, ControlPath):
    """
    添加指定控件以供拖动操作

    :param uiName: 指定控件所处的ui命名控件
    :param ControlPath: 指定控件的节点路径
    """
    TouchMoving = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("TouchMovingControl")
    if not TouchMoving:
        clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).SetAttr("TouchMovingControl", [])
    TouchMoving = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("TouchMovingControl")
    Data = {
        "ControlPath": ControlPath,
        "uiName": uiName,
        "ModName": QingYunMod.ModObject.ModName
    }
    TouchMoving.append(Data)


def TouchMovingModel(State):
    """
    设置拖动按钮模式开启状态

    :param State: 开启状态(True为可拖动，False为不可拖动)
    """
    clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).SetAttr("TouchMoving", State)


def RemoveGameTickFunc(Func):
    """
    注销UITick函数绑定

    :param Func: 需要注销的函数
    """
    if Func not in _GameTickFunc: return
    _GameTickFunc.remove(Func)


class _CompData(object):
    """
    控件组件类，存储了组件的相关信息数据等，以及组件自身的功能实现逻辑，且实例化之后，对应的控件对象可使用GetCompData获取
    """
    def __init__(self, uiName, CompPath, Pos=(0, 0, 0), Alpha=1.0):
        self.uiName = uiName
        self.CompPath = CompPath
        self.DefaultPos = Pos
        self.DefaultAlpha = Alpha
        self.DefaultScale = GetCompSize(uiName, CompPath)
        self.NowPos = Pos
        self.NowAlpha = Alpha
        self.NowScale = GetCompSize(uiName, CompPath)
        if uiName+"|"+CompPath in _CompDataLib:
            del _CompDataLib[uiName + "|" + CompPath]
        _CompDataLib[uiName+"|"+CompPath] = self
        self.ClientTickFuncDict = {
            "UpdateCompPos": None,
            "UpdateCompScale": None,
            "UpdateCompAlpha": None
        }

    def ClientTick(self):
        if self.ClientTickFuncDict["UpdateCompPos"]:
            self.ClientTickFuncDict["UpdateCompPos"]()

        if self.ClientTickFuncDict["UpdateCompScale"]:
            self.ClientTickFuncDict["UpdateCompScale"]()

        if self.ClientTickFuncDict["UpdateCompAlpha"]:
            self.ClientTickFuncDict["UpdateCompAlpha"]()

    def DestroyAnimation(self, AnimationType):
        self.ClientTickFuncDict[AnimationType] = None

    def OpenAnimation(self, Function):
        self.ClientTickFuncDict[Function.__name__] = Function

    def __del__(self):
        RemoveGameTickFunc(self.ClientTick)

    def SetCompMovingAnimation(self, TargetPos, BeginningPos=(0, 0), AnimationTime=1):
        """
        设置控件播放位移动画
        :param TargetPos: 位移的终点坐标(绝对全局坐标)
        :param BeginningPos: 位移的起点坐标(绝对全局坐标)
        :param AnimationTime: 动画持续时间
        """
        self.NowPos = BeginningPos
        if self.ClientTick not in _GameTickFunc:
            AddGameTickFunc(self.ClientTick)
        SetCompMustPosition(self.uiName, self.CompPath, self.NowPos)
        self.DestroyAnimation("UpdateCompPos")

        def UpdateCompPos():
            BPX, BPY = self.NowPos
            TPX, TPY = TargetPos
            Mx = TPX - BPX
            My = TPY - BPY
            if abs(Mx+My) < 0.01:
                self.DestroyAnimation("UpdateCompPos")
                self.NowPos = TargetPos
            else:
                Fps = ClientApi.Generic.Tool.GetFps()
                self.NowPos = (BPX+Mx / (Fps * AnimationTime), BPY+My / (Fps * AnimationTime))

            SetCompMustPosition(self.uiName, self.CompPath, self.NowPos)

        self.OpenAnimation(UpdateCompPos)

    def SetCompAlphaAnimation(self, TargetAlpha, BeginningAlpha=0.0, AnimationTime=1):
        """
        设置控件播放透明度动画
        :param TargetAlpha: 位移的终点Alpha(透明度，取值0-1之间，0表示完全透明，1表示完全不透明)
        :param BeginningAlpha: 位移的起点Alpha(透明度，取值0-1之间，0表示完全透明，1表示完全不透明)
        :param AnimationTime: 动画持续时间
        """
        self.NowAlpha = BeginningAlpha
        if self.ClientTick not in _GameTickFunc:
            AddGameTickFunc(self.ClientTick)
        SetCompAlpha(self.uiName, self.CompPath, self.NowAlpha)
        self.DestroyAnimation("UpdateCompAlpha")

        def UpdateCompAlpha():
            Motion = TargetAlpha-self.NowAlpha
            if abs(Motion) <= 0.01:
                self.DestroyAnimation("UpdateCompAlpha")
                self.NowAlpha = TargetAlpha
            else:
                Fps = ClientApi.Generic.Tool.GetFps()
                self.NowAlpha += Motion/(AnimationTime*Fps)

            SetCompAlpha(self.uiName, self.CompPath, self.NowAlpha)

        self.OpenAnimation(UpdateCompAlpha)

    def SetCompScaleAnimation(self, TargetScale=(0, 0), BeginningScale=(0, 0), AnimationTime=1, resizeChildren=False):
        """
        设置控件播放缩放动画
        :param TargetScale: 缩放的最终大小
        :param BeginningScale: 缩放的初始大小
        :param AnimationTime: 动画持续时间
        """
        self.NowScale = BeginningScale
        if self.ClientTick not in _GameTickFunc:
            AddGameTickFunc(self.ClientTick)
        SetCompSize(self.uiName, self.CompPath, self.NowScale)
        self.DestroyAnimation("UpdateCompScale")

        def UpdateCompScale():
            BPX, BPY = self.NowScale
            TPX, TPY = TargetScale
            Mx = TPX - BPX
            My = TPY - BPY
            if abs(Mx+My) < 0.01:
                self.DestroyAnimation("UpdateCompScale")
                self.NowScale = TargetScale
            else:
                Fps = ClientApi.Generic.Tool.GetFps()
                self.NowScale = (BPX+Mx / (Fps * AnimationTime), BPY+My / (Fps * AnimationTime))

            SetCompSize(self.uiName, self.CompPath, self.NowScale, resizeChildren)

        self.OpenAnimation(UpdateCompScale)


print "\n%s[QyMod] UIScreen加载完毕" % Bcolors.SUC