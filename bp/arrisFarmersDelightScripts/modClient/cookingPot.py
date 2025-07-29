# -*- coding: utf-8 -*-
from ..QingYunModLibs.ClientMod import *
from ..QingYunModLibs.SystemApi import *

playerId = clientApi.GetLocalPlayerId()
NativeScreenManager = clientApi.GetNativeScreenManagerCls()
NativeScreenManager.instance().RegisterScreenProxy("arrisCookingPot.arrisCookingPotMain", "arrisFarmersDelightScripts.proxys.arrisCookingPotProxy.arrisCookingPotProxy")

@ListenClient("ClientBlockUseEvent")
def OnClientBlockUsed(args):
    blockName = args["blockName"]
    if blockName != "arris:cooking_pot":
        return
    x, y, z = args["x"], args["y"], args["z"]
    ClientComp.CreateModAttr(playerId).SetAttr("arrisUsedCookingPotPos", (x, y, z))

@ListenClient("PushScreenEvent")
def OnPushScreen(args):
    if args["screenDef"] != "arrisCookingPot.arrisCookingPotMain":
        return
    if ClientComp.CreatePlayerView(levelId).GetUIProfile() == 0:
        return
    CreateTimer(0.1, clientApi.PopTopUI, False)
    ClientComp.CreateTextNotifyClient(levelId).SetLeftCornerNotify('§a[农夫乐事]\n§e需要将UI档案设置为§b"经典"§e模式才能正常使用厨锅!')
