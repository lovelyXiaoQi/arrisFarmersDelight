# -*- coding: utf-8 -*-
from serverUtils.serverUtils import *

@ListenServer("BlockNeighborChangedServerEvent")
def OnCuttingBoardNeighborChanged(args):
    blockName = args["blockName"]
    if blockName != "arris:cutting_board":
        return
    neighborPos = (args["neighborPosX"], args["neighborPosY"], args["neighborPosZ"])
    if neighborPos != (args["posX"], args["posY"] - 1, args["posZ"]):
        return
    blockPos = (args["posX"], args["posY"], args["posZ"])
    dimensionId = args["dimensionId"]
    neighborName = args["toBlockName"]
    if neighborName == "minecraft:air":
        ServerComp.CreateBlockInfo(levelId).SetBlockNew(blockPos, {"name": "minecraft:air"}, 1, dimensionId)

@ListenServer("ServerItemUseOnEvent")
def OnServerCuttingBoardItemUse(args):
    # 玩家在对方块使用物品之前服务端抛出的事件
    blockName = args["blockName"]
    if blockName == "arris:cutting_board":
        args["ret"] = True

@ListenServer("ServerBlockUseEvent")
def OnServerCuttingBoardBlockUse(args):
    # 使用空手拿取砧板上的物品
    blockName = args["blockName"]
    blockPos = (args["x"], args["y"], args["z"])
    dimensionId = args["dimensionId"]
    playerId = args["playerId"]
    x, y, z = blockPos
    if blockName != "arris:cutting_board":
        return
    if SetPlayerUsedCD(playerId) is True:
        return
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    carriedDict = ServerComp.CreateItem(playerId).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0, True)
    if carriedDict:
        itemType = GetItemType(carriedDict)
        displayEntityId = blockEntityData["displayEntityId"]
        cuttingDict = blockEntityData["cuttingDict"]
        if displayEntityId and cuttingDict:
            result = CuttingBoardDict.get((cuttingDict["newItemName"], cuttingDict["newAuxValue"]))
            if not result:
                return
            if carriedDict["newItemName"] in result["tool"]:
                for resultDict in result["itemList"]:
                    ServerObj.CreateEngineItemEntity(resultDict, dimensionId, (x + 0.5, y + 0.5, z + 0.5))
                ServerObj.DestroyEntity(displayEntityId)
                ToAllPlayerPlaySound(dimensionId, (x, y, z), "ambient.cutting_board.knife")
                SetCarriedDurability(playerId, carriedDict, dimensionId, (x, y, z))
                blockEntityData["cuttingDict"] = None
                blockEntityData["displayEntityId"] = None
        else:
            itemName = carriedDict["newItemName"]
            auxValue = carriedDict["newAuxValue"]
            if itemName == "arris:skillet_item":
                return
            if itemType in ["sword", "axe", "hoe", "shovel", "pickaxe"] or (itemName, auxValue) in CuttingBoardDict:
                ToAllPlayerPlaySound(dimensionId, (x, y, z), "dig.wood")
                SetNotCreateItem(playerId, carriedDict)
                carriedDict["count"] = 1
                blockEntityData["cuttingDict"] = carriedDict
                data = {"blockEntityData": blockEntityData, "blockPos": (x, y, z), "blockAuxValue": args["aux"], "dimensionId": dimensionId}
                CuttingBoardDisplayEntity(carriedDict, playerId, data)
            else:
                ServerComp.CreateGame(playerId).SetOneTipMessage(playerId, "该物品无法放置在砧板上...")
    else:
        displayEntityId = blockEntityData["displayEntityId"]
        cuttingDict = blockEntityData["cuttingDict"]
        if cuttingDict:
            ServerComp.CreateItem(playerId).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, cuttingDict, 0)
            ToAllPlayerPlaySound(dimensionId, blockPos, "armor.equip_leather")
            blockEntityData["cuttingDict"] = None
        if displayEntityId:
            ServerObj.DestroyEntity(displayEntityId)
            blockEntityData["displayEntityId"] = None

@ListenServer("BlockRemoveServerEvent")
def OnCuttingBoardRemove(args):
    # 砧板销毁时触发
    blockName = args["fullName"]
    if blockName != "arris:cutting_board":
        return
    blockPos = (args["x"], args["y"], args["z"])
    dimensionId = args["dimension"]
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
    displayEntityId = blockEntityData["displayEntityId"]
    cuttingDict = blockEntityData["cuttingDict"]
    if displayEntityId:
        ServerObj.DestroyEntity(displayEntityId)
    if cuttingDict:
        ServerObj.CreateEngineItemEntity(cuttingDict, dimensionId, (blockPos[0] + 0.5, blockPos[1] + 0.5, blockPos[2] + 0.5))

