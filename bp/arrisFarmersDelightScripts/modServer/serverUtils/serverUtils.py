# -*- coding: utf-8 -*-
from ...QingYunModLibs.ServerMod import *
from ...QingYunModLibs.SystemApi import *
from ...modCommon.modConfig import *
from collections import Counter
import math, random, copy

entityFace = {
    0: (0, -90),
    1: (0, 0),
    2: (0, 90),
    3: (0, 180)
}

def FromAngleGetBlockAux(x1, y1, x2, y2):
    # 计算两点直接的角度并返回特殊值
    dx = x2 - x1
    dy = y2 - y1
    radian = math.atan2(dy, dx)
    angle = math.degrees(radian)
    if -45 < angle < 45:
        aux = 3
    elif 45 < angle < 135:
        aux = 0
    elif 135 < angle < 180 or -180 < angle < -135:
        aux = 1
    else:
        aux = 2
    return aux

def clickBlockFace(x, y, z):
    # 根据点击方块的坐标来判断应该放置方块的坐标
    placePos = {
        0: (x, y - 1, z), # Down
        1: (x, y + 1, z), # Up
        2: (x, y, z - 1), # North
        3: (x, y, z + 1), # South
        4: (x - 1, y, z),  # West
        5: (x + 1, y, z)  # East
    }
    return placePos

def ProbabilityFunc(probability):
    # 以 probability % 的概率返回True否则返回False
    return random.randint(1, 100) <= probability

def ToAllPlayerPlaySound(dmId, pos, soundName):
    # 播放音效
    playerList = serverApi.GetPlayerList()
    for playerId in playerList:
        dimensionId = ServerComp.CreateDimension(playerId).GetEntityDimensionId()
        if dimensionId != dmId:
            continue
        CallClient("OnPlaySound", playerId, {"soundName": soundName, "pos": pos})

def IsFullBackpack(playerId):
    # 检测玩家背包是否已满
    playerAllItems = ServerComp.CreateItem(playerId).GetPlayerAllItems(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY)
    itemList = list(filter(None, playerAllItems))
    return len(itemList) >= 36

def ResetPlayerUsedCD(playerId):
    # 重置CD
    ServerComp.CreateModAttr(playerId).SetAttr("arrisUsedCD", False)

def SetPlayerUsedCD(playerId):
    # 设置CD
    cd = ServerComp.CreateModAttr(playerId).GetAttr("arrisUsedCD")
    if cd:
        return True
    
    # 设置CD并启动重置定时器
    ServerComp.CreateModAttr(playerId).SetAttr("arrisUsedCD", True)
    ServerComp.CreateGame(levelId).AddTimer(0.2, ResetPlayerUsedCD, playerId)
    CallClient("PlayAttackAnimationCommon", playerId, None)
    return False

def SetNotCreateItem(playerId, itemDict):
    # 在非创造模式下，扣除1个玩家手持物品
    gameType = ServerComp.CreateGame(levelId).GetPlayerGameType(playerId)
    if gameType != 1:
        itemDict["count"] -= 1
        ServerComp.CreateItem(playerId).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, itemDict, 0)

def GetItemType(itemDict):
    # 获取物品类型
    if itemDict:
        itemName = itemDict["newItemName"]
        if itemName in platePackagedFoodDict:
            return "food"
        else:
            basicInfo = ServerComp.CreateItem(levelId).GetItemBasicInfo(itemName)
            itemType = basicInfo["itemType"]
            return itemType
    else:
        return None

# 缓存游戏规则检查结果以提高性能
_experimental_holiday_cache = None

def DetectionExperimentalHoliday():
    # 检测是否为假日创造者模式 - 使用缓存提高性能
    global _experimental_holiday_cache
    if _experimental_holiday_cache is None:
        gameRules = ServerComp.CreateGame(levelId).GetGameRulesInfoServer()
        experimental_holiday = gameRules["option_info"]["experimental_holiday"]
        _experimental_holiday_cache = {0: 0, 4: 1, 8: 2, 12: 3} if experimental_holiday else {0: 0, 1: 1, 2: 2, 3: 3}
    return _experimental_holiday_cache

def CheckCookingPotRecipe(inputItemSlot):
    # 检查厨锅内的物品是否符合配方 - 优化版本
    inputItemList = []
    for itemDict in inputItemSlot:
        if itemDict != {}:
            tupleRecipe = (itemDict["newItemName"], itemDict["newAuxValue"])
            inputItemList.append(tupleRecipe)
    
    # 如果没有输入物品，直接返回
    if not inputItemList:
        return None, None
    
    # 转换为Counter进行快速比较
    inputCounter = Counter(inputItemList)
    
    for RecipeDict in CookingPotRecipeList:
        for recipe in RecipeDict["Recipe"]:
            if Counter(recipe) == inputCounter:
                resultItem = {
                    "newItemName": RecipeDict["CookResult"][0], 
                    "newAuxValue": RecipeDict["CookResult"][1], 
                    "count": 1
                }
                pushItemList = RecipeDict.get("PushItem")
                return resultItem, pushItemList
    
    return None, None

def GetDisplayEntityCarriedItemType(itemDict):
    if not itemDict:
        return 0
    
    itemType = GetItemType(itemDict)
    itemName = itemDict["newItemName"]
    auxValue = itemDict["newAuxValue"]
    key = (itemName, auxValue)
    
    # 检查是否在CuttingBoardDict中有特殊定义
    if key in CuttingBoardDict:
        exceptional = CuttingBoardDict[key].get("type")
        if exceptional is not None:
            itemType = exceptional

    # 统一的类型判断逻辑
    if not itemType or itemType == "" or itemType == "food":
        return 0
    elif itemType == "block":
        return 1
    else:
        return 2

def StoveDisplayEntity(itemDict, playerId, data):
    posList = [
        (0.25, 0.27),
        (0.5, 0.27),
        (0.75, 0.27),
        (0.25, 0.73),
        (0.5, 0.73),
        (0.75, 0.73)
    ]
    itemDict["count"] = 1
    blockEntityData = data["blockEntityData"]
    x, y, z = data["blockPos"]
    dimensionId = data["dimensionId"]
    blockAuxValue = data["blockAuxValue"]
    aux = DetectionExperimentalHoliday()
    blockAux = aux.get(blockAuxValue, blockAuxValue)
    displayEntityDict = blockEntityData["displayEntityDict"]
    if blockEntityData["cookingIndex"] >= 6:
        blockEntityData["cookingIndex"] = 0
    cookingIndex = blockEntityData["cookingIndex"]
    relativePos = posList[cookingIndex]
    Id = ServerObj.CreateEngineEntityByTypeStr("arris:item_display", (x + relativePos[0], y + 0.953, z + relativePos[1]), entityFace[blockAux], dimensionId)
    displayEntityDict[str(cookingIndex)] = Id
    ServerComp.CreateEntityEvent(Id).TriggerCustomEvent(Id, "arris:set_small")
    blockEntityData["displayEntityDict"] = displayEntityDict
    blockEntityData[str(cookingIndex)] = {"itemDict": itemDict, "cookTimer": 7}
    ServerComp.CreateItem(Id).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, itemDict, 0)

    itemType = GetDisplayEntityCarriedItemType(itemDict)
    ServerComp.CreateEntityDefinitions(Id).SetVariant(int(itemType))

def SkilletDisplayEntity(itemDict, playerId, data):
    count = itemDict["count"]
    blockEntityData = data["blockEntityData"]
    displayEntityList = []
    x, y, z = data["blockPos"]
    dimensionId = data["dimensionId"]
    blockAuxValue = data["blockAuxValue"]
    aux = DetectionExperimentalHoliday()
    blockAux = aux.get(blockAuxValue, blockAuxValue)
    step = -0.037
    # 使用更高效的数量映射计算
    if count <= 0:
        num = 0
    elif count == 1:
        num = 1
    elif count <= 16:
        num = 2
    elif count <= 32:
        num = 3
    elif count <= 48:
        num = 4
    elif count <= 64:
        num = 5
    else:
        num = 5
    for i in range(0, num):
        step += 0.037
        Id = ServerObj.CreateEngineEntityByTypeStr("arris:item_display", (x + random.uniform(0.43, 0.57), y + step, z + random.uniform(0.43, 0.57)), entityFace[blockAux], dimensionId)
        displayEntityList.append(Id)
        displayDict = copy.deepcopy(itemDict)
        displayDict["count"] = 1
        ServerComp.CreateItem(Id).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, displayDict, 0)
        itemType = GetDisplayEntityCarriedItemType(displayDict)
        ServerComp.CreateEntityDefinitions(Id).SetVariant(int(itemType))
    blockEntityData["displayEntityList"] = displayEntityList

def CuttingBoardDisplayEntity(itemDict, playerId, data):
    blockEntityData = data["blockEntityData"]
    dimensionId = data["dimensionId"]
    blockAuxValue = data["blockAuxValue"]
    x, y, z = data["blockPos"]
    aux = DetectionExperimentalHoliday()
    blockAux = aux.get(blockAuxValue, blockAuxValue)
    Id = ServerObj.CreateEngineEntityByTypeStr("arris:item_display", (x + 0.5, y, z + 0.5), entityFace[blockAux], dimensionId)
    displayDict = copy.deepcopy(itemDict)
    ServerComp.CreateItem(Id).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, displayDict, 0)
    blockEntityData["displayEntityId"] = Id
    itemType = GetDisplayEntityCarriedItemType(itemDict)
    basicInfo = ServerComp.CreateItem(levelId).GetItemBasicInfo(itemDict["newItemName"])
    ServerComp.CreateEntityDefinitions(Id).SetVariant(int(itemType))

def CheckCookingPotVessel(blockEntityData, blockPos, dimensionId):
    # 检查厨锅内的容器是否符合并更新
    x, y, z = blockPos
    previewItemSlot = blockEntityData["previewItemSlot"][0]
    vesselItemSlot = ServerComp.CreateItem(levelId).GetContainerItem(blockPos, 6, dimensionId)

    for RecipeDict in CookingPotRecipeList:
        cookResult = RecipeDict["CookResult"]
        vessel = RecipeDict.get("Vessel")
        resultItemName = cookResult[0]
        resultAuxValue = cookResult[1]

        vesselDict = {"newItemName": vessel[0], "newAuxValue": vessel[1]} if vessel else {}

        if previewItemSlot and previewItemSlot.get("newItemName") == resultItemName:
            # 获取物品基础信息
            basicInfo = ServerComp.CreateItem(levelId).GetItemBasicInfo(resultItemName, resultAuxValue)
            maxStackSize = basicInfo["maxStackSize"]
            resultItemSlot = ServerComp.CreateItem(levelId).GetContainerItem(blockPos, 7, dimensionId)
            
            # 检查结果槽位是否可用
            if resultItemSlot and resultItemSlot["newItemName"] != resultItemName:
                return
            if resultItemSlot and resultItemSlot["count"] >= maxStackSize:
                return
            
            previewItemCount = previewItemSlot["count"]
            blockEntityData["previewItemSlot"] = [None]
            
            if not vessel:
                # 无容器的情况
                resultCount = previewItemCount if not resultItemSlot else previewItemCount + resultItemSlot["count"]
                ServerComp.CreateItem(levelId).SpawnItemToContainer({"newItemName": resultItemName, "newAuxValue": resultAuxValue, "count": resultCount, "enchantData": []}, 7, blockPos, dimensionId)
                CreateEntityServer("minecraft:xp_orb", (x + 0.5, y + 1, z + 0.5), (0, 0), dimensionId)
                
            elif vesselItemSlot and vesselDict.get("newItemName") == vesselItemSlot.get("newItemName"):
                # 有容器的情况
                count = vesselItemSlot["count"] - previewItemSlot["count"]
                
                if count >= 0:
                    vesselItemSlot["count"] = count
                    ServerComp.CreateItem(levelId).SpawnItemToContainer(vesselItemSlot, 6, blockPos, dimensionId)
                    resultCount = previewItemCount if not resultItemSlot else previewItemCount + resultItemSlot["count"]
                else:
                    previewItemSlot["count"] = abs(count)
                    blockEntityData["previewItemSlot"] = [previewItemSlot]
                    ServerComp.CreateItem(levelId).SpawnItemToContainer({}, 6, blockPos, dimensionId)
                    resultCount = vesselItemSlot["count"] if not resultItemSlot else abs(count) + resultItemSlot["count"]

                ServerComp.CreateItem(levelId).SpawnItemToContainer(7, {"newItemName": resultItemName, "newAuxValue": resultAuxValue, "count": resultCount, "enchantData": []}, blockPos, dimensionId)
                CreateEntityServer("minecraft:xp_orb", (x + 0.5, y + 1, z + 0.5), (0, 0), dimensionId)

def SetCarriedDurability(playerId, itemDict, dimensionId, pos):
    # 设置手持物品耐久-1
    gameType = ServerComp.CreateGame(levelId).GetPlayerGameType(playerId)
    if gameType != 1:
        if GetItemType(itemDict) in ["", "block"]:
            return
        itemDict["durability"] -= 1
        if itemDict["durability"] <= 0:
            ToAllPlayerPlaySound(dimensionId, pos, "random.break")
            ServerComp.CreateItem(playerId).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, None, 0)
        else:
            ServerComp.CreateItem(playerId).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, itemDict, 0)
