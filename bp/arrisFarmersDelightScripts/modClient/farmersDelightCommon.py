# -*- coding: utf-8 -*-
from ..QingYunModLibs.ClientMod import *
from ..QingYunModLibs.SystemApi import *
from ..modCommon.modConfig import *
from ..jeiLinkage import *

playerId = clientApi.GetLocalPlayerId()
isJump = None
isClickingBlock = ()

recipeDict = {
    "arris:wheat_dough": {"itemName": "minecraft:bucket", "count": 1, "auxValue": 0},
    "arris:milk_bottle": {"itemName": "minecraft:bucket", "count": 1, "auxValue": 0},
    "arris:honey_cookie": {"itemName": "minecraft:glass_bottle", "count": 1, "auxValue": 0},
    "arris:stuffed_potato": {"itemName": "minecraft:glass_bottle", "count": 1, "auxValue": 0},
    "arris:salmon_roll": {"itemName": "minecraft:bowl", "count": 1, "auxValue": 0},
    "arris:cod_roll": {"itemName": "minecraft:bowl", "count": 1, "auxValue": 0}
}

@Call(playerId)
def OnPlaySound(args):
    soundName = args["soundName"]
    pos = args["pos"]
    ClientComp.CreateCustomAudio(levelId).PlayCustomMusic(soundName, pos, 1, 1, False, None)

@Call(playerId)
def PlayParticle(pos):
    ClientComp.CreateParticleSystem(None).Create("minecraft:crop_growth_emitter", pos)

@Call(playerId)
def SetEntityBlockMolang(args):
    pos = args["blockPos"]
    molang = args["molang"]
    name = args["name"]
    print args
    ClientComp.CreateBlockInfo(levelId).SetEnableBlockEntityAnimations(pos, True)
    ClientComp.CreateBlockInfo(levelId).SetBlockEntityMolangValue(pos, name, molang)

@Call(playerId)
def SetItemDisplayMolang(args):
    entityId = args["entityId"]
    itemType = args["itemType"]
    if itemType:
        comp = ClientComp.CreateQueryVariable(entityId)
        if itemType == "" or itemType == "food":
            comp.Set('query.mod.item_display_mode', 0.0)
        elif itemType == "block":
            comp.Set('query.mod.item_display_mode', 1.0)
        else:
            comp.Set('query.mod.item_display_mode', 2.0)

@Call(playerId)
def PlayAttackAnimationCommon(args):
    ClientComp.CreatePlayer(playerId).Swing()

@ListenClient("AddEntityClientEvent")
def OnAddEntityClient(args):
    entityName = args["engineTypeStr"]
    if entityName == "arris:item_display":
        CallServer("GetEntityCarriedItem", args["id"])

@ListenClient("LoadClientAddonScriptsAfter")
def LoadAddon(args):
    ClientComp.CreateQueryVariable(levelId).Register('query.mod.item_display_mode', 0.0)
    ClientComp.CreateQueryVariable(levelId).Register('query.mod.item_display_animation', 0.0)

@ListenClient("UiInitFinished")
def UiGuideBookInit(args):
    clientApi.RegisterUI("arris", "farmerDelightGuideBook", uiGuideBookPath, uiGuideBookScreen)
    FarmersDelightJeiLinkageInit()

@ListenClient("ClientItemTryUseEvent")
def OnClientItemTryUse(args):
    itemDict = args["itemDict"]
    if itemDict["newItemName"] == "arris:farmer_delight_guide_book":
        ClientComp.CreateCustomAudio(levelId).PlayCustomMusic("item.book.page_turn", (1, 1, 1), 1, 1, False, playerId)
        clientApi.PushScreen("arris", "farmerDelightGuideBook")

@ListenClient("ActorAcquiredItemClientEvent")
def OnActorAcquiredItem(args):
    itemDict = args["itemDict"]
    acquireMethod = args["acquireMethod"]
    if acquireMethod == 2:
        itemName = itemDict["newItemName"]
        if itemName in recipeDict:
            dimensionId = ClientComp.CreateGame(levelId).GetCurrentDimension()
            playerPos = ClientComp.CreatePos(playerId).GetFootPos()
            giveItemDict = recipeDict[itemName]
            data = {
                "itemDict": giveItemDict,
                "playerId": playerId,
                "dimensionId": dimensionId,
                "playerPos": playerPos
            }
            CallServer("PlayerShapedRecipe", data)

@ListenClient("ClientJumpButtonPressDownEvent")
def ClientJumpButtonPressDown(args):
    global isJump
    isJump = True
    data = {"playerId": playerId, "isJump": isJump}
    CallServer("SetPlayerIsJumpExtra", data)

@ListenClient("ClientJumpButtonReleaseEvent")
def ClientJumpButtonRelease(args):
    global isJump
    isJump = False
    data = {"playerId": playerId, "isJump": isJump}
    CallServer("SetPlayerIsJumpExtra", data)

@ListenClient("ModBlockEntityLoadedClientEvent")
def OnBlockEntityLoaded(args):
    blockPos = (args["posX"], args["posY"], args["posZ"])
    blockName = args["blockName"]
    comp = ClientComp.CreateBlockInfo(levelId)
    blockEntityData = comp.GetBlockEntityData(blockPos)
    if not blockEntityData:
        return
    if blockName in ["arris:skillet", "arris:cooking_pot"]:
        comp.SetEnableBlockEntityAnimations(blockPos, True)
        heatParticleEnableData = blockEntityData["exData"].get("heatParticleEnable")
        if heatParticleEnableData:
            blockHeatValue = heatParticleEnableData["__value__"]
            comp.SetBlockEntityMolangValue(blockPos, "variable.mod_heat", blockHeatValue)
        shelfEnableData = blockEntityData["exData"].get("shelfEnable")
        if shelfEnableData:
            blockShelfEnable = shelfEnableData["__value__"]
            comp.SetBlockEntityMolangValue(blockPos, "variable.mod_shelf", blockShelfEnable)
    elif blockName in ["arris:apple_pie", "arris:chocolate_pie", "arris:sweet_berry_cheesecake"]:
        blockPieStatus = blockEntityData["exData"]["blockStatus"]["__value__"]
        comp.SetEnableBlockEntityAnimations(blockPos, True)
        comp.SetBlockEntityMolangValue(blockPos, "variable.mod_pie", blockPieStatus)
