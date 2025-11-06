# -*- coding: utf-8 -*-
from serverUtils.serverUtils import *

# 常量定义
DEFAULT_COOK_TIMER = 7
TICK_INTERVAL = 20
NON_COOKABLE_SKILLET_ITEMS = frozenset([
    "arris:spatula",
    "arris:cutting_board",
    "arris:cooking_pot",
    "arris:skillet_item"
])
SHELF_BLOCKS = frozenset([
    "minecraft:campfire",
    "minecraft:fire",
    "minecraft:soul_fire",
    "minecraft:soul_campfire",
    "minecraft:lava",
    "minecraft:flowing_lava"
])

# 辅助函数
def _getSkilletBlockEntityData(dimensionId, blockPos):
    """获取煎锅方块实体数据，返回None如果不存在"""
    return ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)

def _getDownBlockName(blockPos, dimensionId):
    """获取下方方块名称"""
    x, y, z = blockPos
    return ServerComp.CreateBlockInfo(levelId).GetBlockNew((x, y - 1, z), dimensionId)["name"]

def _canCookOnSkillet(itemName):
    """检查物品是否可以在煎锅上烹饪"""
    return itemName in CanCookedFoodDict

def _updateSkilletStates(blockEntityData, downBlockName, blockPos, dimensionId):
    """更新煎锅状态(热源和架子)"""
    # 更新架子状态
    blockEntityData["shelfEnable"] = 1.0 if downBlockName in SHELF_BLOCKS else 0.0
    data = {"molang": blockEntityData["shelfEnable"], "blockPos": blockPos, "name": "variable.mod_shelf"}
    CallAllClient("SetEntityBlockMolang", data)
    
    # 更新热源状态
    hasHeat = downBlockName in CanProvideHeatBlockList
    blockEntityData["heatEnable"] = hasHeat
    blockEntityData["heatParticleEnable"] = 1.0 if hasHeat else 0.0
    blockEntityData["cookTimer"] = DEFAULT_COOK_TIMER if not hasHeat else blockEntityData.get("cookTimer", DEFAULT_COOK_TIMER)
    
    data = {"molang": blockEntityData["heatParticleEnable"], "blockPos": blockPos, "name": "variable.mod_heat"}
    CallAllClient("SetEntityBlockMolang", data)

def _addItemToSkillet(blockEntityData, carriedDict, playerId, blockPos, aux, dimensionId, downBlockName):
    """将物品添加到煎锅"""
    blockEntityData["cookingDict"] = carriedDict
    data = {
        "blockEntityData": blockEntityData,
        "blockPos": blockPos,
        "blockAuxValue": aux,
        "dimensionId": dimensionId
    }
    SkilletDisplayEntity(carriedDict, playerId, data)
    
    gameType = ServerComp.CreateGame(levelId).GetPlayerGameType(playerId)
    if gameType != 1:
        ServerComp.CreateItem(playerId).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, None, 0)
    
    blockEntityData["cookTimer"] = DEFAULT_COOK_TIMER
    sound = "ambient.skillet.addfood" if downBlockName in CanProvideHeatBlockList else "armor.equip_leather"
    ToAllPlayerPlaySound(dimensionId, blockPos, sound)

def _removeItemFromSkillet(blockEntityData, playerId, blockPos, dimensionId):
    """从煎锅移除物品"""
    cookingDict = blockEntityData["cookingDict"]
    if cookingDict:
        ServerComp.CreateItem(playerId).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, cookingDict, 0)
        ToAllPlayerPlaySound(dimensionId, blockPos, "armor.equip_leather")
        blockEntityData["cookingDict"] = None
    
    displayEntityList = blockEntityData["displayEntityList"]
    if displayEntityList:
        for entityId in displayEntityList:
            ServerObj.DestroyEntity(entityId)
        blockEntityData["displayEntityList"] = None
    
    blockEntityData["cookTimer"] = DEFAULT_COOK_TIMER

def _getDisplayIndexByCount(count):
    """根据数量获取显示实体索引"""
    if count == 0:
        return 0
    elif count == 1:
        return 1
    elif 2 <= count <= 16:
        return 2
    elif 17 <= count <= 32:
        return 3
    elif 33 <= count <= 48:
        return 4
    return 0

@ListenServer("ServerBlockUseEvent")
def OnServerSkilletBlockUse(args):
    # 早期返回：检查方块类型
    if args["blockName"] != "arris:skillet":
        return
    
    # 早期返回：检查玩家冷却
    playerId = args["playerId"]
    if SetPlayerUsedCD(playerId):
        return
    
    # 早期返回：检查方块实体数据
    blockPos = (args["x"], args["y"], args["z"])
    dimensionId = args["dimensionId"]
    blockEntityData = _getSkilletBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    
    carriedDict = ServerComp.CreateItem(playerId).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0, True)
    
    # 情况1：手持物品
    if carriedDict:
        _handleAddItemToSkillet(carriedDict, blockEntityData, playerId, blockPos, args["aux"], dimensionId, args)
    # 情况2：空手
    else:
        _handleRemoveItemFromSkillet(blockEntityData, playerId, blockPos, dimensionId)

def _handleAddItemToSkillet(carriedDict, blockEntityData, playerId, blockPos, aux, dimensionId, args):
    """处理向煎锅添加物品"""
    # 早期返回：已有显示实体
    if blockEntityData["displayEntityList"]:
        return
    
    itemName = carriedDict["newItemName"]
    
    # 可烹饪物品
    if _canCookOnSkillet(itemName):
        downBlockName = _getDownBlockName(blockPos, dimensionId)
        _addItemToSkillet(blockEntityData, carriedDict, playerId, blockPos, aux, dimensionId, downBlockName)
        return
    
    # 特殊物品（允许通过）
    if itemName in NON_COOKABLE_SKILLET_ITEMS:
        args["ret"] = True
        return
    
    # 不可烹饪物品
    ServerComp.CreateGame(playerId).SetOneTipMessage(playerId, "这个貌似不可以进行烹饪...")

def _handleRemoveItemFromSkillet(blockEntityData, playerId, blockPos, dimensionId):
    """处理从煎锅移除物品"""
    _removeItemFromSkillet(blockEntityData, playerId, blockPos, dimensionId)

@ListenServer("ServerItemUseOnEvent")
def OnServerSkilletItemUse(args):
    """玩家在对方块使用物品之前服务端抛出的事件"""
    itemDict = args["itemDict"]
    itemName = itemDict["newItemName"]
    
    # 早期返回：检查物品类型
    if itemName != "arris:skillet_item":
        return
    
    # 早期返回：检查目标方块类型（禁止在这些方块上放置）
    blockName = args["blockName"]
    if blockName in ["minecraft:frame", "minecraft:glow_frame", "arris:cutting_board"]:
        return
    
    playerId = args["entityId"]
    
    # 早期返回：检查玩家冷却
    if SetPlayerUsedCD(playerId):
        return
    
    # 处理放置煎锅
    _placeSkilletBlock(args, itemDict, playerId)

def _placeSkilletBlock(args, itemDict, playerId):
    """放置煎锅方块"""
    dimensionId = args["dimensionId"]
    x, y, z = args["x"], args["y"], args["z"]
    face = args["face"]
    
    # 计算放置位置
    placePos = clickBlockFace(x, y, z)
    setPos = placePos[face]
    
    # 早期返回：检查目标位置是否为空气
    placeBlock = ServerComp.CreateBlockInfo(levelId).GetBlockNew(setPos, dimensionId)["name"]
    if placeBlock != "minecraft:air":
        return
    
    # 计算方块朝向
    pX, pY, pZ = ServerComp.CreatePos(playerId).GetFootPos()
    aux = DetectionExperimentalHoliday()
    blockAux = aux.get(FromAngleGetBlockAux(x, z, pX, pZ), FromAngleGetBlockAux(x, z, pX, pZ))
    
    # 放置方块
    blockDict = {"name": itemChangeBlockDict[itemDict["newItemName"]]}
    SetNotCreateItem(playerId, itemDict)
    ServerComp.CreateBlockInfo(levelId).SetBlockNew(setPos, blockDict, 0, dimensionId)
    
    # 设置方块状态
    blockStates = ServerComp.CreateBlockState(levelId).GetBlockStates(setPos, dimensionId)
    if blockStates:
        blockStates["direction"] = blockAux
        ServerComp.CreateBlockState(levelId).SetBlockStates(setPos, blockStates, dimensionId)

@ListenServer("BlockNeighborChangedServerEvent")
def OnSkilletNeighborChanged(args):
    # 早期返回：检查方块类型
    if args["blockName"] != "arris:skillet":
        return
    
    # 早期返回：只关心下方邻居变化
    blockPos = (args["posX"], args["posY"], args["posZ"])
    neighborPos = (args["neighborPosX"], args["neighborPosY"], args["neighborPosZ"])
    if neighborPos != (args["posX"], args["posY"] - 1, args["posZ"]):
        return
    
    # 早期返回：检查方块实体数据
    dimensionId = args["dimensionId"]
    blockEntityData = _getSkilletBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    
    # 更新煎锅状态
    _updateSkilletStates(blockEntityData, args["toBlockName"], blockPos, dimensionId)

@ListenServer("ServerPlaceBlockEntityEvent")
def OnServerSkilletCreate(args):
    # 早期返回：检查方块类型
    if args["blockName"] != "arris:skillet":
        return
    
    blockPos = (args["posX"], args["posY"], args["posZ"])
    dimensionId = args["dimension"]
    
    # 播放放置音效
    ToAllPlayerPlaySound(dimensionId, blockPos, "dig.stone")
    
    # 早期返回：检查方块实体数据
    blockEntityData = _getSkilletBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    
    # 获取下方方块并更新状态
    downBlockName = _getDownBlockName(blockPos, dimensionId)
    blockEntityData["cookTimer"] = DEFAULT_COOK_TIMER
    _updateSkilletStates(blockEntityData, downBlockName, blockPos, dimensionId)

@ListenServer("ServerBlockEntityTickEvent")
def OnSkilletTick(args):
    # 早期返回：检查方块类型
    if args["blockName"] != "arris:skillet":
        return
    
    # 早期返回：只在每秒执行一次
    if ServerComp.CreateTime(levelId).GetTime() % TICK_INTERVAL != 0:
        return
    
    dimensionId = args["dimension"]
    blockPos = (args["posX"], args["posY"], args["posZ"])
    
    # 早期返回：检查方块实体数据
    blockEntityData = _getSkilletBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    
    # 早期返回：需要有热源
    if not blockEntityData["heatEnable"]:
        return
    
    # 早期返回：需要有烹饪物品
    if not blockEntityData["cookingDict"]:
        return
    
    # 处理烹饪逻辑
    _processSkilletCooking(blockEntityData, dimensionId, args["posX"], args["posY"], args["posZ"])

def _processSkilletCooking(blockEntityData, dimensionId, x, y, z):
    """处理煎锅烹饪逻辑"""
    blockEntityData["cookTimer"] -= 1.0
    
    # 早期返回：未完成烹饪
    if blockEntityData["cookTimer"] > 1.0:
        return
    
    cookingDict = blockEntityData["cookingDict"]
    cookingDict["count"] -= 1
    
    # 销毁对应的显示实体
    _destroyDisplayEntity(blockEntityData["displayEntityList"], cookingDict["count"])
    
    # 重置烹饪计时器
    blockEntityData["cookTimer"] = DEFAULT_COOK_TIMER
    
    # 生成烹饪产物
    output = {
        "itemName": CanCookedFoodDict[cookingDict["newItemName"]],
        "auxValue": cookingDict["newAuxValue"],
        "count": 1,
    }
    ServerObj.CreateEngineItemEntity(output, dimensionId, (x + 0.5, y + 0.3, z + 0.5))
    
    # 清理空的烹饪数据
    if cookingDict["count"] <= 0:
        blockEntityData["displayEntityList"] = None
        blockEntityData["cookingDict"] = None

def _destroyDisplayEntity(displayEntityList, remainingCount):
    """根据剩余数量销毁对应的显示实体"""
    if not displayEntityList:
        return
    
    index = _getDisplayIndexByCount(remainingCount)
    try:
        entityId = displayEntityList[index]
        ServerObj.DestroyEntity(entityId)
    except (IndexError, KeyError):
        pass

@ListenServer("BlockRemoveServerEvent")
def OnSkilletRemove(args):
    """方块在销毁时触发"""
    # 早期返回：检查方块类型
    if args["fullName"] != "arris:skillet":
        return
    
    blockPos = (args["x"], args["y"], args["z"])
    dimensionId = args["dimension"]
    
    # 获取方块实体数据
    blockEntityData = _getSkilletBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    
    # 销毁显示实体
    _destroyAllDisplayEntities(blockEntityData.get("displayEntityList"))
    
    # 掉落烹饪物品
    _dropCookingItem(blockEntityData.get("cookingDict"), dimensionId, args["x"], args["y"], args["z"])

def _destroyAllDisplayEntities(displayEntityList):
    """销毁所有显示实体"""
    if not displayEntityList:
        return
    
    for entityId in displayEntityList:
        ServerObj.DestroyEntity(entityId)

def _dropCookingItem(cookingDict, dimensionId, x, y, z):
    """掉落烹饪物品"""
    if not cookingDict:
        return
    
    ServerObj.CreateEngineItemEntity(cookingDict, dimensionId, (x + 0.5, y + 0.5, z + 0.5))
