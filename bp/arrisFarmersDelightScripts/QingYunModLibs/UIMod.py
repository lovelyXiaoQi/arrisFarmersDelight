# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
import math
import SystemApi
import UIScreen
_UINameList = []
_PluginsUINameList = []
_Touch_Motion_X_Dict = dict()
_Touch_Motion_Y_Dict = dict()
_ControlMotion = {}
_MovingSpeed = ()
_OldPos = None
_TimeCold = True
_Touch = False


@SystemApi.ListenClient("UiInitFinished")
def __UiInitFinished(event):
    for uiName in _UINameList:
        clientApi.RegisterUI(SystemApi.QingYunMod.ModObject.ModName, uiName, SystemApi.QingYunMod.ModObject.ModName + '.' + uiName + '.' + "UIScreen", uiName + '.main')
        clientApi.CreateUI(SystemApi.QingYunMod.ModObject.ModName, uiName, {"isHud": 1})

    for UI in _PluginsUINameList:
        uiName = UI[0]
        PluginsName = UI[1]
        clientApi.RegisterUI(SystemApi.QingYunMod.ModObject.ModName, uiName, SystemApi.QingYunMod.ModObject.ModName + '.QingYunModLibs.Plugins.' + PluginsName + "." + uiName + '.' + "UIScreen", uiName + '.main')
        clientApi.CreateUI(SystemApi.QingYunMod.ModObject.ModName, uiName, {"isHud": 1})

    @UIScreen.AddGameTick
    def __TickFunc():
        __TouchMoving()
        TouchBack()


def __TouchMoving():
    if _Touch:
        X, Y = clientApi.GetTouchPos()
        Scroll_View = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("Scroll_View")
        if not Scroll_View: return
        for View_Key in Scroll_View:
            Scroll_ViewBlockPath = Scroll_View[View_Key]["BlockPath"]
            uiName = Scroll_View[View_Key]["uiName"]
            MoveModel = Scroll_View[View_Key]["MoveModel"]
            ModName = Scroll_View[View_Key].get("ModName", None)
            if ModName != SystemApi.QingYunMod.ModObject.ModName: continue
            if not UIScreen.GetVisible(uiName, View_Key): continue
            if MoveModel == "vertical":
                Pos_X, Pos_Y = UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).GetPosition()
                Pos = (Pos_X, Y + _Touch_Motion_Y_Dict.get(View_Key, 0))
                UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

            if MoveModel == "horizontally":
                Pos_X, Pos_Y = UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).GetPosition()
                Pos = (X + _Touch_Motion_X_Dict.get(View_Key, 0), Pos_Y)
                UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

            Rotate = Scroll_View[View_Key]["Rotate"]
            if not Rotate: return
            Pos_X, Pos_Y = UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).GetPosition()
            RotateValue = math.tan(math.radians(Rotate))
            Pos_X = Pos_Y*-RotateValue
            Pos = (Pos_X, Pos_Y)
            UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)


def TouchBack():
    Scroll_View = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("Scroll_View")
    if not Scroll_View: return
    for View_Key in Scroll_View:
        Scroll_ViewBlockPath = Scroll_View[View_Key]["BlockPath"]
        uiName = Scroll_View[View_Key]["uiName"]
        MoveModel = Scroll_View[View_Key]["MoveModel"]
        ModName = Scroll_View[View_Key].get("ModName", None)
        if ModName != SystemApi.QingYunMod.ModObject.ModName: continue
        if not UIScreen.GetVisible(uiName, View_Key): continue
        BPX, BPY = UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).GetPosition()
        BSX, BSY = Scroll_View[View_Key]["Size"]
        BMNX = BPX
        BMXX = BPX + BSX
        BMNY = BPY
        BMXY = BPY + BSY
        SPX, SPY = UIScreen.UIModComp(uiName).GetBaseUIControl(View_Key).GetPosition()
        SSX, SSY = Scroll_View[View_Key]["TouchSize"]
        SMNX = SPX
        SMXX = SPX + SSX
        SMNY = SPY
        SMXY = SPY + SSY
        Fps = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId()).GetFps()
        if MoveModel == "horizontally":
            if BMNX < SMNX - 50:
                Pos = (BMNX, BPY)
                UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

            if BMXX > SMXX + 50:
                Pos = (SMXX + 50, BPY)
                UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

            if not _Touch:
                if BMNX < SMNX:
                    Pos = (round(BMNX + (SMNX - BMNX) / (1.5*Fps), 2), BPY)
                    UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

                if BMXX > SMXX:
                    Pos = (round(BMXX - (BMXX - SMXX) / (1.5*Fps), 2), BPY)
                    UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

        if MoveModel == "vertical":
            if BMNY >= SMNY + 100:
                Pos = (BPX, SMNY + 100)
                UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

            elif BMXY <= SMXY - 101:
                Pos = (BPX, SMNY - (BSY - (SSY - 100)))
                UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

            if not _Touch:
                if BMNY >= SMNY:
                    Pos = (BPX, BMNY - round((BMNY - SMNY)/(1.5*Fps), 2))
                    UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

                elif BMXY <= SMXY:
                    MustStick = SMNY - (BSY - (SSY))
                    Pos = (BPX, BMNY + round((MustStick-BMNY)/(1.5*Fps), 2))
                    UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)

        Rotate = Scroll_View[View_Key]["Rotate"]
        if not Rotate: return
        Pos_X, Pos_Y = UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).GetPosition()
        RotateValue = math.tan(math.radians(Rotate))
        Pos_X = Pos_Y * -RotateValue
        Pos = (Pos_X, Pos_Y)
        UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).SetPosition(Pos)


def Reback():
    global _TimeCold
    _TimeCold = True


def AddUI(uiName):
    """
    创建一个新的UI(注意：UI脚本文件名和UI布局json命名需要与uiName相同，这样规范命名格式是为了更简便的注册)

    :param uiName: 创建的UI名称
    """
    global _UINameList
    _UINameList.append(uiName)


def AddUIForPlugins(uiName, PluginsName):
    """
    创建一个新的UI(专用于插件UI注册，注意：UI脚本文件名和UI布局json命名需要与uiName相同，这样规范命名格式是为了更简便的注册)

    :param uiName: 创建的UI名称
    """
    global _PluginsUINameList
    UI = [uiName, PluginsName]
    _PluginsUINameList.append(UI)


@SystemApi.ListenClient("GetEntityByCoordEvent")
def GetEntityByCoordEvent(event):
    global _Touch
    X, Y = clientApi.GetTouchPos()
    '''
    ModAttr中的Scroll_View是已经注册的滑动框数据
    '''
    Scroll_View = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("Scroll_View")
    if not Scroll_View: return
    for View_Key in Scroll_View:
        Scroll_ViewScreenPath = View_Key
        Scroll_ViewBlockPath = Scroll_View[View_Key]["BlockPath"]
        uiName = Scroll_View[View_Key]["uiName"]
        ModName = Scroll_View[View_Key].get("ModName", None)
        if ModName != SystemApi.QingYunMod.ModObject.ModName: continue
        if not UIScreen.GetVisible(uiName, Scroll_ViewScreenPath): continue
        Pos_X, Pos_Y = UIScreen.GetCompMustPosition(uiName, Scroll_ViewScreenPath)
        if not Scroll_View[View_Key]["TouchSize"]:
            continue
        Size_X, Size_Y = Scroll_View[View_Key]["TouchSize"]
        PosX, PosY = UIScreen.UIModComp(uiName).GetBaseUIControl(Scroll_ViewBlockPath).GetPosition()
        _Touch_Motion_X_Dict[View_Key] = PosX - X
        _Touch_Motion_Y_Dict[View_Key] = PosY - Y
        if Pos_X < X < abs(Size_X) + Pos_X and Pos_Y < Y < abs(Size_Y) + Pos_Y:
            _Touch = True


@SystemApi.ListenClient("GetEntityByCoordReleaseClientEvent")
def GetEntityByCoordRelease(event):
    global _Touch
    _Touch = False
    for ControlData in _ControlMotion:
        Control = _ControlMotion[ControlData]
        Control["Touch"] = False


@SystemApi.ListenClient("GetEntityByCoordEvent")
def GetEntityByCoordEventForTouchMoving(args):
    if not clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("TouchMoving"):
        return
    TouchMoving = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("TouchMovingControl")
    if not TouchMoving: return
    for TouchValue in TouchMoving:
        X, Y = clientApi.GetTouchPos()
        Scroll_ViewBlockPath = TouchValue["ControlPath"]
        uiName = TouchValue["uiName"]
        ModName = TouchValue["ModName"]
        PosX, PosY = UIScreen.GetCompMustPosition(uiName, Scroll_ViewBlockPath, ModName)
        Size_X, Size_Y = clientApi.GetUI(ModName, uiName).GetBaseUIControl(Scroll_ViewBlockPath).GetSize()
        if PosX < X < Size_X + PosX and PosY < Y < Size_Y + PosY:
            _ControlMotion[Scroll_ViewBlockPath] = {"Motion": (-Size_X / 2, -Size_Y / 2), "Touch": True}
            return


@SystemApi.ListenClient("OnScriptTickClient")
def __TouchMovingForControl():
    if not clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("TouchMoving"):
        return
    TouchMoving = clientApi.GetEngineCompFactory().CreateModAttr(clientApi.GetLevelId()).GetAttr("TouchMovingControl")
    for TouchValue in TouchMoving:
        X, Y = clientApi.GetTouchPos()
        Scroll_ViewBlockPath = TouchValue["ControlPath"]
        uiName = TouchValue["uiName"]
        if Scroll_ViewBlockPath not in _ControlMotion:
            continue
        Touch = _ControlMotion[Scroll_ViewBlockPath]["Touch"]
        if not Touch: continue
        Mx, My = _ControlMotion[Scroll_ViewBlockPath]["Motion"]
        Pos = (X + Mx, Y + My)
        try:
            UIScreen.SetCompMustPosition(uiName, Scroll_ViewBlockPath, Pos)
        except:
            return


print "\n%s[QyMod] UIMod加载完毕" % SystemApi.Bcolors.SUC
