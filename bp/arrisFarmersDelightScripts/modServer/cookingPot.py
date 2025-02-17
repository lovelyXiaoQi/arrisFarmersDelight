# -*- coding: utf-8 -*-
from serverUtils.serverUtils import *
import copy

def CheckScreen(args):
    if not args:
        return
    dimensionId = args.get("dimensionId")
    blockPos = args.get("blockPos")
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
    if blockEntityData:
        blockEntityData["playerId"] = None

@Call()
def SetInventory(args):
    itemsDictMap = args.get("itemsDictMap")
    playerId = args["playerId"]
    inputItemSlot = args["inputItemSlot"]
    vesselItemSlot = args["vesselItemSlot"]
    resultItemSlot = args["resultItemSlot"]
    previewItemSlot = args["previewItemSlot"]
    if itemsDictMap:
        ServerComp.CreateItem(playerId).SetPlayerAllItems(itemsDictMap)
    for i in range(0, 6):
        if inputItemSlot[i] is None:
            inputItemSlot[i] = {}
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(args["dimensionId"], args["blockPos"])
    if blockEntityData:
        blockEntityData["inputItemSlot"] = inputItemSlot
        blockEntityData["vesselItemSlot"] = vesselItemSlot
        blockEntityData["resultItemSlot"] = resultItemSlot
        blockEntityData["previewItemSlot"] = previewItemSlot
        resultItem = CheckCookingPotRecipe(blockEntityData)[0]
        if resultItem:
            blockEntityData["resultItem"] = resultItem
        else:
            CallClient("SetArrowProgress", playerId, {"timer": 10.0})
            blockEntityData["timer"] = 10.0
            blockEntityData["resultItem"] = None

        CheckCookingPotVessel(blockEntityData)

@Call()
def OutputResultItem(args):
    itemDict = args["itemDict"]
    x, y, z = args["blockPos"]
    ServerObj.CreateEngineItemEntity(itemDict, args["dimensionId"], (x + 0.5, y + 1.0, z + 0.5))

@Call()
def PlayerCloseCookingPot(args):
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(args["dimensionId"], args["blockPos"])
    if blockEntityData:
        blockEntityData["playerId"] = None

@Call()
def CookingPotAddFood(args):
    itemsDictMap = dict()
    playerId = args["playerId"]
    blockPos = args["blockPos"]
    dimensionId = args["dimensionId"]
    inputList = args["inputList"]
    indexList = args["indexList"]
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    inputItemSlot = blockEntityData["inputItemSlot"]
    itemList = ServerComp.CreateItem(playerId).GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY, True)
    for index in range(len(inputList)):
        if not inputItemSlot[index]:
            itemDict = copy.deepcopy(itemList[indexList[index]])
            itemDict["count"] = 1
            inputItemSlot[index] = itemDict
            inventoryDict = itemList[indexList[index]]
            inventoryDict["count"] -= 1
            if inventoryDict["count"] <= 0:
                ServerComp.CreateItem(playerId).SetInvItemNum(indexList[index], 0)
                itemList[indexList[index]] = None
            else:
                itemList[indexList[index]] = inventoryDict
        else:
            if inputItemSlot[index] and itemList[indexList[index]] and inputItemSlot[index]["newItemName"] == itemList[indexList[index]]["newItemName"]:
                inputItemSlot[index]["count"] += 1
                inventoryDict = itemList[indexList[index]]
                inventoryDict["count"] -= 1
                if inventoryDict["count"] <= 0:
                    ServerComp.CreateItem(playerId).SetInvItemNum(indexList[index], 0)
                    itemList[indexList[index]] = None
                else:
                    itemList[indexList[index]] = inventoryDict
            else:
                break
    for i in range(0, len(itemList)):
        itemsDictMap[(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY, i)] = itemList[i]
    if itemsDictMap:
        ServerComp.CreateItem(playerId).SetPlayerAllItems(itemsDictMap)
    blockEntityData["inputItemSlot"] = inputItemSlot
    if playerId:
        update = {
            "heatEnable": blockEntityData["heatEnable"],
            "inputItemSlot": blockEntityData["inputItemSlot"],
            "vesselItemSlot": blockEntityData["vesselItemSlot"],
            "resultItemSlot": blockEntityData["resultItemSlot"],
            "previewItemSlot": blockEntityData["previewItemSlot"],
            "blockPos": blockPos,
            "dimensionId": dimensionId
        }
        CallClient("UpdateCookingPot", blockEntityData["playerId"], update)

@ListenServer("ServerItemUseOnEvent")
def OnServerCookingPotItemUse(args):
    blockName = args["blockName"]
    playerId = args["entityId"]
    if blockName == "arris:cooking_pot":
        if SetPlayerUsedCD(playerId) is True:
            return
        if ServerComp.CreatePlayer(args["entityId"]).isSneaking() is False:
            args["ret"] = True

@ListenServer("ServerBlockUseEvent")
def OnServerCookingPotBlockUse(args):
    blockName = args["blockName"]
    blockPos = (args["x"], args["y"], args["z"])
    dimensionId = args["dimensionId"]
    playerId = args["playerId"]
    if blockName == "arris:cooking_pot":
        if SetPlayerUsedCD(playerId) is True:
            return
        blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
        if ServerComp.CreatePlayer(playerId).isSneaking() is True:
            return
        if not blockEntityData:
            return
        if blockEntityData["playerId"] is None:
            blockEntityData["playerId"] = playerId
            data = {
                "heatEnable": blockEntityData["heatEnable"],
                "inputItemSlot": blockEntityData["inputItemSlot"],
                "vesselItemSlot": blockEntityData["vesselItemSlot"],
                "resultItemSlot": blockEntityData["resultItemSlot"],
                "previewItemSlot": blockEntityData["previewItemSlot"],
                "blockPos": blockPos,
                "dimensionId": dimensionId
            }
            CallClient("CookingPotUsedEvent", playerId, data)
        else:
            CallClient("CheckPlayerScreen", playerId, {"blockPos": blockPos, "dimensionId": dimensionId}, CheckScreen)
            ServerComp.CreateGame(playerId).SetOneTipMessage(playerId, "已有玩家正在使用这个厨锅\n如有误判请再次点击")

@ListenServer("ServerBlockEntityTickEvent")
def OnCookingPotTick(args):
    if args["blockName"] != "arris:cooking_pot":
        return
    dimensionId = args["dimension"]
    blockPos = (args["posX"], args["posY"], args["posZ"])
    if ServerComp.CreateTime(levelId).GetTime() % 2 == 0:
        blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
        if not blockEntityData:
            return
        resultItem = CheckCookingPotRecipe(blockEntityData)[0]
        if resultItem:
            blockEntityData["resultItem"] = resultItem
        else:
            blockEntityData["resultItem"] = None
        if blockEntityData["heatEnable"] is True and blockEntityData["resultItem"]:
            previewItemSlot = blockEntityData["previewItemSlot"]
            resultItem = blockEntityData["resultItem"]

            itemName = resultItem["newItemName"]
            auxValue = resultItem["newAuxValue"]
            basicInfo = ServerComp.CreateItem(levelId).GetItemBasicInfo(itemName, auxValue)
            maxStackSize = basicInfo["maxStackSize"]
            if previewItemSlot[0] and previewItemSlot[0].get("count") >= maxStackSize:
                return
            if not previewItemSlot[0] or resultItem["newItemName"] == previewItemSlot[0].get("newItemName"):
                inputItemSlot = blockEntityData["inputItemSlot"]
                playerId = blockEntityData["playerId"]
                blockEntityData["timer"] -= 0.1
                if blockEntityData["timer"] <= 0.1:
                    blockEntityData["timer"] = 10.0
                    pushItemList = CheckCookingPotRecipe(blockEntityData)[1]
                    vesselItemSlot = blockEntityData["vesselItemSlot"]
                    if vesselItemSlot[0] and vesselItemSlot[0]["count"] == 0:
                        blockEntityData["vesselItemSlot"] = [None]
                    if pushItemList:
                        for pushItem in pushItemList:
                            output = {"newItemName": pushItem[0], "newAuxValue": pushItem[1], "count": 1}
                            ServerObj.CreateEngineItemEntity(output, dimensionId, (args["posX"] + 0.5, args["posY"] + 1.0, args["posZ"] + 0.5))
                    for index in range(0, len(inputItemSlot)):
                        itemDict = inputItemSlot[index]
                        if itemDict != {}:
                            if itemDict["count"] <= 1:
                                itemDict = {}
                            else:
                                itemDict["count"] -= 1
                            inputItemSlot[index] = itemDict
                            blockEntityData["inputItemSlot"] = inputItemSlot
                    if not previewItemSlot[0]:
                        blockEntityData["previewItemSlot"] = [blockEntityData["resultItem"]]
                    else:
                        if not resultItem:
                            return
                        count = previewItemSlot[0]["count"] + resultItem["count"]
                        previewItemSlot[0]["count"] = count
                        blockEntityData["previewItemSlot"] = previewItemSlot
                    update = {
                        "heatEnable": blockEntityData["heatEnable"],
                        "inputItemSlot": blockEntityData["inputItemSlot"],
                        "vesselItemSlot": blockEntityData["vesselItemSlot"],
                        "resultItemSlot": blockEntityData["resultItemSlot"],
                        "previewItemSlot": blockEntityData["previewItemSlot"],
                        "blockPos": blockPos,
                        "dimensionId": dimensionId
                    }
                    CallClient("UpdateCookingPot", blockEntityData["playerId"], update)
                args["timer"] = blockEntityData["timer"]
                if playerId:
                    CallClient("SetArrowProgress", playerId, {"timer": blockEntityData["timer"]})
        else:
            blockEntityData["timer"] = 10.0

@ListenServer("ServerPlaceBlockEntityEvent")
def OnServerCookingPotCreate(args):
    blockName = args["blockName"]
    blockPos = (args["posX"], args["posY"], args["posZ"])
    dimensionId = args["dimension"]
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
    if blockName == "arris:cooking_pot":
        if blockEntityData:
            inputItem = [{} for i in range(0, 6)]
            blockEntityData["inputItemSlot"] = inputItem
            blockEntityData["vesselItemSlot"] = [None]
            blockEntityData["resultItemSlot"] = [None]
            blockEntityData["previewItemSlot"] = [None]
            blockEntityData["playerId"] = None
            blockEntityData["timer"] = 10.0
            blockEntityData["blockPos"] = blockPos
            blockEntityData["dimensionId"] = dimensionId
            blockDict = ServerComp.CreateBlockInfo(levelId).GetBlockNew((args["posX"], args["posY"] - 1, args["posZ"]), dimensionId)
            blockName = blockDict["name"]
            if blockName in ["minecraft:campfire", "minecraft:fire", "minecraft:soul_fire", "minecraft:soul_campfire", "minecraft:lava", "minecraft:flowing_lava"]:
                blockEntityData["shelfEnable"] = 1.0
            else:
                blockEntityData["shelfEnable"] = 0.0
            data = {"molang": blockEntityData["shelfEnable"], "blockPos": blockPos, "name": "variable.mod_shelf"}
            CallAllClient("SetEntityBlockMolang", data)

            if blockName in CanProvideHeatBlockList:
                blockEntityData["heatEnable"] = True
                blockEntityData["heatParticleEnable"] = 1.0
            else:
                blockEntityData["heatEnable"] = False
                blockEntityData["heatParticleEnable"] = 0.0
            data = {"molang": blockEntityData["heatParticleEnable"], "blockPos": blockPos, "name": "variable.mod_heat"}
            CallAllClient("SetEntityBlockMolang", data)

@ListenServer("BlockNeighborChangedServerEvent")
def OnCookingPotNeighborChanged(args):
    blockName = args["blockName"]
    blockPos = (args["posX"], args["posY"], args["posZ"])
    dimensionId = args["dimensionId"]
    neighborPos = (args["neighborPosX"], args["neighborPosY"], args["neighborPosZ"])
    if blockName == "arris:cooking_pot" and neighborPos == (args["posX"], args["posY"] - 1, args["posZ"]):
        blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
        if blockEntityData:
            neighborName = args["toBlockName"]
            if neighborName in ["minecraft:campfire", "minecraft:fire", "minecraft:soul_fire", "minecraft:soul_campfire", "minecraft:lava", "minecraft:flowing_lava"]:
                blockEntityData["shelfEnable"] = 1.0
            else:
                blockEntityData["shelfEnable"] = 0.0
            data = {"molang": blockEntityData["shelfEnable"], "blockPos": blockPos, "name": "variable.mod_shelf"}
            CallAllClient("SetEntityBlockMolang", data)

            if neighborName in CanProvideHeatBlockList:
                blockEntityData["heatEnable"] = True
                blockEntityData["heatParticleEnable"] = 1.0
            else:
                blockEntityData["heatEnable"] = False
                blockEntityData["heatParticleEnable"] = 0.0
            data = {"molang": blockEntityData["heatParticleEnable"], "blockPos": blockPos, "name": "variable.mod_heat"}
            CallAllClient("SetEntityBlockMolang", data)
            if blockEntityData["playerId"]:
                update = {
                    "heatEnable": blockEntityData["heatEnable"],
                    "inputItemSlot": blockEntityData["inputItemSlot"],
                    "vesselItemSlot": blockEntityData["vesselItemSlot"],
                    "resultItemSlot": blockEntityData["resultItemSlot"],
                    "previewItemSlot": blockEntityData["previewItemSlot"],
                    "blockPos": blockPos,
                    "dimensionId": dimensionId
                }
                CallClient("UpdateCookingPot", blockEntityData["playerId"], update)

@ListenServer("BlockRemoveServerEvent")
def OnCookingPotRemoveServer(args):
    blockName = args["fullName"]
    if blockName == "arris:cooking_pot":
        blockPos = (args["x"], args["y"], args["z"])
        dimensionId = args["dimension"]
        blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
        if blockEntityData:
            inputItemSlot = blockEntityData["inputItemSlot"]
            vesselItemSlot = blockEntityData["vesselItemSlot"]
            resultItemSlot = blockEntityData["resultItemSlot"]
            spawnItemPos = (args["x"] + 0.5, args["y"] + 0.5, args["z"] + 0.5)
            spawnItemList = []
            for itemDict in inputItemSlot:
                spawnItemList.append(itemDict)
            if vesselItemSlot[0]:
                spawnItemList.append(vesselItemSlot[0])
            if resultItemSlot[0]:
                spawnItemList.append(resultItemSlot[0])
            for itemDict in spawnItemList:
                ServerObj.CreateEngineItemEntity(itemDict, dimensionId, spawnItemPos)
