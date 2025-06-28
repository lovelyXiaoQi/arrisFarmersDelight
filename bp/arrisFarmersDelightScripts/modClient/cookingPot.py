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
