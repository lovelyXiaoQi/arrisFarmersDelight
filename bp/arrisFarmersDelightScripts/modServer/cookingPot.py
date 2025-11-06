# -*- coding: utf-8 -*-
from serverUtils.serverUtils import *
import copy

@ListenServer("ServerPlaceBlockEntityEvent")
def OnServerCookingPotCreate(args):
    blockName = args["blockName"]
    if blockName != "arris:cooking_pot":
        return
        
    blockPos = (args["posX"], args["posY"], args["posZ"])
    dimensionId = args["dimension"]
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return

    # 初始化实体数据
    blockEntityData["previewItemSlot"] = [{}]
    blockEntityData["timer"] = 10.0

    blockDict = ServerComp.CreateBlockInfo(levelId).GetBlockNew((args["posX"], args["posY"] - 1, args["posZ"]), dimensionId)
    blockName = blockDict["name"]
    if blockName in ["minecraft:fire", "minecraft:campfire", "minecraft:soul_fire", "minecraft:soul_campfire", "minecraft:lava", "minecraft:flowing_lava"]:
        blockEntityData["shelfEnable"] = 1.0
    else:
        blockEntityData["shelfEnable"] = 0.0
    data = {"molang": blockEntityData["shelfEnable"], "blockPos": blockPos, "name": "variable.mod_shelf"}
    CreateTimer(0.1, CallAllClient, False, "SetEntityBlockMolang", data)

    if blockName in CanProvideHeatBlockList:
        blockEntityData["heatEnable"] = True
        blockEntityData["heatParticleEnable"] = 1.0
    else:
        blockEntityData["heatEnable"] = False
        blockEntityData["heatParticleEnable"] = 0.0
    data = {"molang": blockEntityData["heatParticleEnable"], "blockPos": blockPos, "name": "variable.mod_heat"}
    CreateTimer(0.1, CallAllClient, False, "SetEntityBlockMolang", data)

@ListenServer("BlockNeighborChangedServerEvent")
def OnCookingPotNeighborChanged(args):
    blockName = args["blockName"]
    blockPos = (args["posX"], args["posY"], args["posZ"])
    dimensionId = args["dimensionId"]
    neighborPos = (args["neighborPosX"], args["neighborPosY"], args["neighborPosZ"])
    
    # 只处理烹饪锅下方方块的变化
    if blockName != "arris:cooking_pot" or neighborPos != (args["posX"], args["posY"] - 1, args["posZ"]):
        return
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
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

@ListenServer("ServerBlockEntityTickEvent")
def OnCookingPotTick(args):
    if args["blockName"] != "arris:cooking_pot":
        return
    
    dimensionId = args["dimension"]
    blockPos = (args["posX"], args["posY"], args["posZ"])
    blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    
    # 一次性收集所有物品槽数据，减少API调用
    inputItemSlot = []
    emptySlots = 0
    for index in range(6):
        itemDict = ServerComp.CreateItem(levelId).GetContainerItem(blockPos, index, dimensionId)
        if not itemDict:
            itemDict = {}
            emptySlots += 1
        inputItemSlot.append(itemDict)
    
    CheckCookingPotVessel(blockEntityData, blockPos, dimensionId)
    
    # 如果所有槽位都为空，重置计时器并返回
    if emptySlots >= 6:
        blockEntityData["timer"] = 10.0
        return
    
    resultItem, pushItemList = CheckCookingPotRecipe(inputItemSlot)

    if blockEntityData["heatEnable"] and resultItem:
        previewItemSlot = blockEntityData["previewItemSlot"]
        itemName = resultItem["newItemName"]
        auxValue = resultItem["newAuxValue"]
        basicInfo = ServerComp.CreateItem(levelId).GetItemBasicInfo(itemName, auxValue)
        maxStackSize = basicInfo["maxStackSize"]

        # 检查预览槽位是否已满
        if previewItemSlot[0] and previewItemSlot[0].get("count") >= maxStackSize:
            return
            
        # 检查是否可以添加到预览槽位
        if not previewItemSlot[0] or resultItem["newItemName"] == previewItemSlot[0].get("newItemName"):
            blockEntityData["timer"] -= 0.05
            if blockEntityData["timer"] <= 0.05:
                blockEntityData["timer"] = 10.0

                # 处理抛出的物品
                if pushItemList:
                    dropPos = (args["posX"] + 0.5, args["posY"] + 1.0, args["posZ"] + 0.5)
                    for pushItem in pushItemList:
                        output = {"newItemName": pushItem[0], "newAuxValue": pushItem[1], "count": 1}
                        ServerObj.CreateEngineItemEntity(output, dimensionId, dropPos)

                # 从输入槽位扣除材料
                for index, itemDict in enumerate(inputItemSlot):
                    if not itemDict:
                        continue
                    itemDict["count"] -= 1
                    ServerComp.CreateItem(levelId).SpawnItemToContainer(itemDict, index, blockPos, dimensionId)

                if not previewItemSlot[0]:
                    blockEntityData["previewItemSlot"] = [resultItem]
                else:
                    if not resultItem:
                        return
                    count = previewItemSlot[0]["count"] + resultItem["count"]
                    previewItemSlot[0]["count"] = count
                    blockEntityData["previewItemSlot"] = previewItemSlot
    else:
        blockEntityData["timer"] = 10.0

@Call()
def CookingPotAddFood(args):
    itemsDictMap = dict()
    playerId = args["playerId"]
    blockPos = args["blockPos"]
    dimensionId = args["dimensionId"]
    inputList = args["inputList"]
    indexList = args["indexList"]

    inputItemSlot = []
    for index in range(7):
        itemDict = ServerComp.CreateItem(levelId).GetContainerItem(blockPos, index, dimensionId)
        if not itemDict:
            itemDict = {}
        inputItemSlot.append(itemDict)
    playerAllItemList = ServerComp.CreateItem(playerId).GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY, True)
    for index in range(len(inputList)):
        if not inputItemSlot[index]:
            itemDict = copy.deepcopy(playerAllItemList[indexList[index]])
            itemDict["count"] = 1
            inputItemSlot[index] = itemDict
            inventoryDict = playerAllItemList[indexList[index]]
            inventoryDict["count"] -= 1
            if inventoryDict["count"] <= 0:
                ServerComp.CreateItem(playerId).SetInvItemNum(indexList[index], 0)
                playerAllItemList[indexList[index]] = None
            else:
                playerAllItemList[indexList[index]] = inventoryDict
        else:
            if inputItemSlot[index] and playerAllItemList[indexList[index]] and inputItemSlot[index]["newItemName"] == playerAllItemList[indexList[index]]["newItemName"]:
                inputItemSlot[index]["count"] += 1
                inventoryDict = playerAllItemList[indexList[index]]
                inventoryDict["count"] -= 1
                if inventoryDict["count"] <= 0:
                    ServerComp.CreateItem(playerId).SetInvItemNum(indexList[index], 0)
                    playerAllItemList[indexList[index]] = None
                else:
                    playerAllItemList[indexList[index]] = inventoryDict
            else:
                break
    for i in range(0, len(playerAllItemList)):
        itemsDictMap[(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY, i)] = playerAllItemList[i]
    
    if itemsDictMap:
        ServerComp.CreateItem(playerId).SetPlayerAllItems(itemsDictMap)
    for index, itemDict in enumerate(inputList):
        ServerComp.CreateItem(levelId).SpawnItemToContainer(itemDict, index, blockPos, dimensionId)
