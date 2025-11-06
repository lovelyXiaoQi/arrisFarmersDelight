# -*- coding: utf-8 -*-
from serverUtils.serverUtils import *

# 常量定义
MAX_STOVE_SLOTS = 6
DEFAULT_COOK_TIMER = 7
STOVE_ITEM_DROP_HEIGHT = 1.3
TICK_INTERVAL = 20

# 不可烹饪的特殊物品
NON_COOKABLE_ITEMS = frozenset([
    "arris:cutting_board",
    "arris:cooking_pot",
    "arris:skillet_item"
])

def _initStoveSlot(index):
    """初始化单个炉灶槽位的辅助函数"""
    return {"itemDict": None, "cookTimer": DEFAULT_COOK_TIMER}

def _initStoveData():
    """初始化炉灶数据的辅助函数"""
    displayEntityDict = {}
    slotData = {}
    for index in range(MAX_STOVE_SLOTS):
        slotKey = str(index)
        slotData[slotKey] = _initStoveSlot(index)
        displayEntityDict[slotKey] = None
    
    return {
        "cookingIndex": 0,
        "displayEntityDict": displayEntityDict,
        "slots": slotData
    }

def _getStoveBlockEntityData(dimensionId, blockPos):
    """获取炉灶方块实体数据的辅助函数"""
    return ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)

@ListenServer("ServerPlaceBlockEntityEvent")
def OnServerStoveCreate(args):
    """优化的炉灶创建函数"""
    blockName = args["blockName"]
    if blockName not in StoveList:
        return
    
    blockPos = (args["posX"], args["posY"], args["posZ"])
    dimensionId = args["dimension"]
    blockEntityData = _getStoveBlockEntityData(dimensionId, blockPos)
    
    if not blockEntityData:
        return
    
    # 使用辅助函数初始化数据
    initData = _initStoveData()
    blockEntityData["cookingIndex"] = initData["cookingIndex"]
    blockEntityData["displayEntityDict"] = initData["displayEntityDict"]
    
    # 设置槽位数据
    for key, value in initData["slots"].iteritems():
        blockEntityData[key] = value

def _canPlaceOnStove(dimensionId, x, y, z, playerId):
    """检查是否可以在炉灶上放置物品"""
    upBlockDict = ServerComp.CreateBlockInfo(levelId).GetBlockNew((x, y + 1, z), dimensionId)
    if upBlockDict["name"] != "minecraft:air":
        ServerComp.CreateGame(playerId).SetOneTipMessage(playerId, "炉灶上方有方块阻挡...")
        return False
    return True

def _placeItemOnStove(playerId, itemDict, blockEntityData, blockPos, blockAuxValue, dimensionId):
    """在炉灶上放置物品"""
    cookingIndex = blockEntityData["cookingIndex"]
    
    # 重置索引
    if cookingIndex >= MAX_STOVE_SLOTS:
        cookingIndex = 0
        blockEntityData["cookingIndex"] = 0
    
    # 检查槽位是否已占用
    displayEntityDict = blockEntityData["displayEntityDict"]
    if displayEntityDict.get(str(cookingIndex)):
        return False
    
    # 设置槽位数据
    blockEntityData[str(cookingIndex)] = {
        "itemDict": itemDict,
        "cookTimer": DEFAULT_COOK_TIMER
    }
    
    # 扣除物品
    SetNotCreateItem(playerId, itemDict)
    
    # 创建显示实体
    data = {
        "blockEntityData": blockEntityData,
        "blockPos": blockPos,
        "blockAuxValue": blockAuxValue,
        "dimensionId": dimensionId
    }
    StoveDisplayEntity(itemDict, playerId, data)
    ToAllPlayerPlaySound(dimensionId, blockPos, "armor.equip_leather")
    
    # 更新索引
    blockEntityData["cookingIndex"] += 1
    return True

@ListenServer("ServerItemUseOnEvent")
def OnServerStoveItemUse(args):
    """优化的炉灶物品使用处理函数"""
    blockName = args["blockName"]
    if blockName not in StoveList:
        return
    
    playerId = args["entityId"]
    if SetPlayerUsedCD(playerId):
        return
    
    itemDict = args["itemDict"]
    itemName = itemDict["newItemName"]
    dimensionId = args["dimensionId"]
    x, y, z = args["x"], args["y"], args["z"]
    blockPos = (x, y, z)
    
    # 获取方块实体数据
    blockEntityData = _getStoveBlockEntityData(dimensionId, blockPos)
    if not blockEntityData:
        return
    
    # 检查上方是否有阻挡
    if not _canPlaceOnStove(dimensionId, x, y, z, playerId):
        return
    
    # 处理可烹饪物品
    if itemName in CanCookedFoodDict:
        _placeItemOnStove(playerId, itemDict, blockEntityData, blockPos, args["blockAuxValue"], dimensionId)
        return
    
    # 处理不可烹饪物品
    if itemName not in NON_COOKABLE_ITEMS:
        ServerComp.CreateGame(playerId).SetOneTipMessage(playerId, "这个貌似不能烹饪...")

def _processStoveSlot(slotIndex, blockEntityData, dropPos, dimensionId):
    """处理单个炉灶槽位的烹饪逻辑"""
    slotKey = str(slotIndex)
    slotData = blockEntityData.get(slotKey)
    
    if not slotData or not slotData.get("itemDict"):
        return
    
    # 减少烹饪计时器
    slotData["cookTimer"] -= 1
    blockEntityData[slotKey] = slotData
    
    # 检查是否烹饪完成
    if slotData["cookTimer"] > 0:
        return
    
    # 生成烹饪结果
    itemDict = slotData["itemDict"]
    cookedItemName = CanCookedFoodDict.get(itemDict["newItemName"])
    
    if cookedItemName:
        output = {
            "itemName": cookedItemName,
            "auxValue": itemDict.get("newAuxValue", 0),
            "count": 1
        }
        ServerObj.CreateEngineItemEntity(output, dimensionId, dropPos)
    
    # 清理槽位
    blockEntityData[slotKey] = _initStoveSlot(slotIndex)
    
    # 销毁显示实体
    displayEntityDict = blockEntityData.get("displayEntityDict", {})
    entityId = displayEntityDict.get(slotKey)
    if entityId:
        ServerObj.DestroyEntity(entityId)
        displayEntityDict[slotKey] = None
        blockEntityData["displayEntityDict"] = displayEntityDict

@ListenServer("ServerBlockEntityTickEvent")
def OnStoveTick(args):
    """优化的炉灶Tick处理函数"""
    if args["blockName"] not in StoveList:
        return
    
    # 只在每秒处理一次（每20个tick）
    if ServerComp.CreateTime(levelId).GetTime() % TICK_INTERVAL != 0:
        return
    
    dimensionId = args["dimension"]
    blockPos = (args["posX"], args["posY"], args["posZ"])
    blockEntityData = _getStoveBlockEntityData(dimensionId, blockPos)
    
    if not blockEntityData:
        return
    
    # 计算掉落位置
    dropPos = (args["posX"] + 0.5, args["posY"] + STOVE_ITEM_DROP_HEIGHT, args["posZ"] + 0.5)
    
    # 处理所有槽位
    for index in range(MAX_STOVE_SLOTS):
        _processStoveSlot(index, blockEntityData, dropPos, dimensionId)
    
    # 重置烹饪索引
    if blockEntityData.get("cookingIndex", 0) >= MAX_STOVE_SLOTS:
        blockEntityData["cookingIndex"] = 0

def _dropStoveItems(blockEntityData, dropPos, dimensionId):
    """掉落炉灶中的所有物品"""
    for index in range(MAX_STOVE_SLOTS):
        slotData = blockEntityData.get(str(index))
        if not slotData:
            continue
        
        itemDict = slotData.get("itemDict")
        if itemDict:
            ServerObj.CreateEngineItemEntity(itemDict, dimensionId, dropPos)

def _destroyStoveDisplayEntities(blockEntityData):
    """销毁炉灶的所有显示实体"""
    displayEntityDict = blockEntityData.get("displayEntityDict")
    if not displayEntityDict:
        return
    
    for slotKey, entityId in displayEntityDict.iteritems():
        if entityId:
            ServerObj.DestroyEntity(entityId)

@ListenServer("BlockRemoveServerEvent")
def OnStoveRemove(args):
    """优化的炉灶移除处理函数"""
    blockName = args["fullName"]
    if blockName not in StoveList:
        return
    
    blockPos = (args["x"], args["y"], args["z"])
    dimensionId = args["dimension"]
    blockEntityData = _getStoveBlockEntityData(dimensionId, blockPos)
    
    if not blockEntityData:
        return
    
    # 掉落所有物品
    dropPos = (args["x"] + 0.5, args["y"] + 0.5, args["z"] + 0.5)
    _dropStoveItems(blockEntityData, dropPos, dimensionId)
    
    # 销毁所有显示实体
    _destroyStoveDisplayEntities(blockEntityData)
