# -*- coding: utf-8 -*-
from ..QingYunModLibs.ClientMod import *
from ..QingYunModLibs.SystemApi import *
from ..modCommon.modConfig import *

playerId = clientApi.GetLocalPlayerId()
uiNode = None
cookingPotRecipeList = None

@ListenClient("UiInitFinished")
def CookingPotUiInit(args):
    clientApi.RegisterUI("arrisFarmersDelight", "uiCookingPot", uiCookingPotPath, uiCookingPotScreen)

@ListenClient("ActorAcquiredItemClientEvent")
def OnCookingPotActorAcquiredItem(args):
    global uiNode
    uiNode = clientApi.GetUI("arrisFarmersDelight", "uiCookingPot")
    if uiNode:
        uiNode.UpdatePlayerInventory(None)

@ListenClient("GridComponentSizeChangedClientEvent")
def OnCookingPotGridComponentSizeChanged(args):
    inputModeId = ClientComp.CreatePlayerView(levelId).GetToggleOption(clientApi.GetMinecraftEnum().OptionId.INPUT_MODE)
    if inputModeId == 0:  # 键鼠操作
        RECIPE_SCROLL = "/main/variables_button_mappings_and_controls/safezone_screen_matrix/inner_matrix/safezone_screen_panel/root_screen_panel/padding_bg/option_bg/scroll_view/scroll_mouse/scroll_view/stack_panel/background_and_viewport/scrolling_view_port/scrolling_content"
    elif inputModeId == 1: # 触摸屏操作
        RECIPE_SCROLL = "/main/variables_button_mappings_and_controls/safezone_screen_matrix/inner_matrix/safezone_screen_panel/root_screen_panel/padding_bg/option_bg/scroll_view/scroll_touch/scroll_view/panel/background_and_viewport/scrolling_view_port/scrolling_content"
    else:
        RECIPE_SCROLL = None
    if args["path"] == RECIPE_SCROLL:
        uiNode.GetFoodRecipeBook()

@ListenClient("OnKeyPressInGame")
def OnCookingPotKeyPressInGame(args):
    if not uiNode:
        return
    if args["isDown"] == "1" and args["key"] == "27":
        clientApi.PopScreen()
        data = {"blockPos": uiNode.blockPos, "dimensionId": uiNode.dimensionId}
        CallServer("PlayerCloseCrabTrap", data)

@ListenClient("OnScriptTickNonChaseFrameClient")
def OnScriptTickNonChaseFrame():
    if not uiNode:
        return
    uiNode.GameTick()

@Call(playerId)
def SetCookingPotRecipeList(args):
    global cookingPotRecipeList
    cookingPotRecipeList = args

@Call(playerId)
def SetArrowProgress(args):
    global uiNode
    uiNode = clientApi.GetUI("arrisFarmersDelight", "uiCookingPot")
    timer = args.get("timer")
    if uiNode:
        uiNode.SetArrowProgress(timer)
    else:
        return args

@Call(playerId)
def CookingPotUsedEvent(args):
    global uiNode
    args["CookingPotRecipeList"] = cookingPotRecipeList
    uiNode = clientApi.PushScreen("arrisFarmersDelight", "uiCookingPot", args)

@Call(playerId)
def UpdateCookingPot(data):
    global uiNode
    uiNode = clientApi.GetUI("arrisFarmersDelight", "uiCookingPot")
    if uiNode:
        uiNode.UpdateCookingPot(data)

@Call(playerId)
def CheckPlayerScreen(args):
    if uiNode:
        return None
    else:
        return args
