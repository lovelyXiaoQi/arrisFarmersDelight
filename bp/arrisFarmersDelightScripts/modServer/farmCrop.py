# -*- coding: utf-8 -*-
from serverUtils.serverUtils import *
import random

# 定义允许的方块类型常量，提高查找效率
VALID_FARMLAND_BLOCKS = frozenset([
    "minecraft:farmland", "arris:rich_soil_farmland_moist", 
    "arris:rich_soil_farmland", "minecraft:grass_block"
])

VALID_RICE_SUPPORT_BLOCKS = frozenset([
    "minecraft:farmland", "minecraft:grass_block", "minecraft:dirt"
])

VALID_RICE_UPPER_BLOCKS = frozenset([
    "arris:rice_upper_crop_stage0", "arris:rice_upper_crop_stage1",
    "arris:rice_upper_crop_stage2", "arris:rice_upper_crop_stage3"
])

def _clearBlock(blockPos, dimensionId, dropItems=1):
    """清除方块的辅助函数"""
    ServerComp.CreateBlockInfo(levelId).SetBlockNew(blockPos, {"name": "minecraft:air"}, dropItems, dimensionId)

def _isBelowNeighbor(args, neighborPos):
    """检查是否为下方邻居"""
    return neighborPos == (args["posX"], args["posY"] - 1, args["posZ"])

def _isAboveNeighbor(args, neighborPos):
    """检查是否为上方邻居"""
    return neighborPos == (args["posX"], args["posY"] + 1, args["posZ"])

@ListenServer("BlockNeighborChangedServerEvent")
def OnBlockNeighborChanged(args):
    """优化的邻居方块变化处理函数"""
    blockName = args["blockName"]
    blockPos = (args["posX"], args["posY"], args["posZ"])
    dimensionId = args["dimensionId"]
    neighborPos = (args["neighborPosX"], args["neighborPosY"], args["neighborPosZ"])
    neighborName = args["toBlockName"]
    
    # 野生作物处理
    if blockName in WildCropDict:
        # 检查下方方块
        if _isBelowNeighbor(args, neighborPos):
            if neighborName not in WildCropDict[blockName]:
                _clearBlock(blockPos, dimensionId, 1)
                return
        
        # 检查上方雪层
        if neighborName == "minecraft:snow_layer" and _isAboveNeighbor(args, neighborPos):
            _clearBlock(neighborPos, dimensionId, 0)
        return
    
    # 普通作物处理
    if blockName in cropsDict:
        if _isBelowNeighbor(args, neighborPos) and neighborName not in VALID_FARMLAND_BLOCKS:
            _clearBlock(blockPos, dimensionId, 1)
        return
    
    # 水稻支撑处理
    if blockName == "arris:rice_supporting":
        if _isBelowNeighbor(args, neighborPos):
            if neighborName not in VALID_RICE_SUPPORT_BLOCKS:
                _clearBlock(blockPos, dimensionId, 1)
            return
        
        if _isAboveNeighbor(args, neighborPos):
            if neighborName not in VALID_RICE_UPPER_BLOCKS:
                ServerComp.CreateBlockInfo(levelId).SetBlockNew(
                    blockPos, {"name": "arris:rice_stage3"}, 0, dimensionId, False, False)
        return
    
    # 蘑菇丛处理
    if blockName in ["arris:red_mushroom_colony", "arris:brown_mushroom_colony"]:
        if _isBelowNeighbor(args, neighborPos):
            _clearBlock(blockPos, dimensionId, 1)

def _hasWaterNearby(comp, x, y, z, dimensionId, searchRange=4):
    """检查附近是否有水的辅助函数"""
    for testX in range(-searchRange, searchRange + 1):
        for testZ in range(-searchRange, searchRange + 1):
            if testX == 0 and testZ == 0:
                continue
            blockDict = comp.GetLiquidBlock((x + testX, y, z + testZ), dimensionId)
            if blockDict and blockDict["name"] in ["minecraft:water", "minecraft:flowing_water"]:
                return True
    return False

def _growCrop(comp, blockName, x, y, z, dimensionId):
    """作物生长的统一处理函数"""
    # 特殊作物处理字典
    specialCrops = {
        "arris:budding_tomatoes_stage6": ("arris:rope", "arris:tomatoes_vine_stage0"),
        "arris:tomatoes_vine_stage3": ("arris:rope", "arris:tomatoes_vine_stage0"),
    }
    
    if blockName in specialCrops:
        requiredBlock, newBlock = specialCrops[blockName]
        blockDict = comp.GetBlockNew((x, y + 1, z), dimensionId)
        if blockDict["name"] == requiredBlock:
            comp.SetBlockNew((x, y + 1, z), {"name": newBlock}, 0, dimensionId, False, False)
    elif blockName == "arris:rice_stage3":
        blockDict = comp.GetBlockNew((x, y + 1, z), dimensionId)
        if blockDict["name"] == "minecraft:air":
            comp.SetBlockNew((x, y, z), {"name": "arris:rice_supporting"}, 0, dimensionId, False, False)
            comp.SetBlockNew((x, y + 1, z), {"name": "arris:rice_upper_crop_stage0"}, 0, dimensionId, False, False)
    else:
        # 普通作物生长
        comp.SetBlockNew((x, y, z), {"name": cropsDict[blockName]}, 0, dimensionId, False, False)

def _processMushroomGrowth(x, y, z, dimensionId):
    """蘑菇生长处理"""
    blockStates = ServerComp.CreateBlockState(levelId).GetBlockStates((x, y, z), dimensionId)
    growth = blockStates.get("arris:growth", 0)
    if growth < 7:
        blockStates["arris:growth"] = growth + 1
        ServerComp.CreateBlockState(levelId).SetBlockStates((x, y, z), blockStates, dimensionId)

@ListenServer("BlockRandomTickServerEvent")
def OnBlockRandomTick(args):
    """优化的随机Tick处理函数"""
    blockName = args["fullName"]
    x, y, z = args["posX"], args["posY"], args["posZ"]
    dimensionId = args["dimensionId"]
    comp = ServerComp.CreateBlockInfo(levelId)
    
    # 作物生长处理
    if blockName in cropsDict and 9 <= args["brightness"] <= 15:
        _growCrop(comp, blockName, x, y, z, dimensionId)
        return
    
    # 富饶农田处理
    if blockName == "arris:rich_soil_farmland":
        if _hasWaterNearby(comp, x, y, z, dimensionId):
            comp.SetBlockNew((x, y, z), {"name": "arris:rich_soil_farmland_moist"}, 0, dimensionId, False, False)
        return
    
    # 湿润的富饶农田处理
    if blockName == "arris:rich_soil_farmland_moist":
        # 检查水源
        if not _hasWaterNearby(comp, x, y, z, dimensionId):
            comp.SetBlockNew((x, y, z), {"name": "arris:rich_soil_farmland"}, 0, dimensionId, False, False)
            return
        
        # 加速上方作物生长
        upBlock = comp.GetBlockNew((x, y + 1, z), dimensionId)
        upBlockName = upBlock["name"]
        
        if upBlockName in cropsDict:
            data = {
                "blockName": upBlockName,
                "playerId": None,
                "itemDict": None,
                "dimensionId": dimensionId,
                "blockPos": (x, y + 1, z)
            }
            CropAccelerateTheRipening(data, "rich_soil_farmland")
        
        # 处理生长状态
        blockStates = ServerComp.CreateBlockState(levelId).GetBlockStates((x, y + 1, z), dimensionId)
        if blockStates:
            growth = blockStates.get("arris:growth")
            if growth is not None and growth < 7:
                blockStates["arris:growth"] = growth + 1
                ServerComp.CreateBlockState(levelId).SetBlockStates((x, y + 1, z), blockStates, dimensionId)
                soundPos = (x + 0.5, y + 1.5, z + 0.5)
                ToAllPlayerPlaySound(dimensionId, soundPos, "item.bone_meal.use")
                CallAllClient("PlayParticle", soundPos)
        return
    
    # 蘑菇丛生长处理
    if blockName in ["arris:red_mushroom_colony", "arris:brown_mushroom_colony"]:
        _processMushroomGrowth(x, y, z, dimensionId)

VALID_RICE_PLANTING_BLOCKS = frozenset([
    "minecraft:dirt", "minecraft:grass_block", "arris:rich_soil"
])

VALID_MUSHROOM_BLOCKS = frozenset([
    "arris:organic_compost_stage0", "arris:organic_compost_stage1",
    "arris:organic_compost_stage2", "arris:organic_compost_stage3", "arris:rich_soil"
])

MUSHROOM_COLONY_MAP = {
    "minecraft:brown_mushroom": "arris:brown_mushroom_colony",
    "minecraft:red_mushroom": "arris:red_mushroom_colony"
}

def _plantRice(playerId, itemDict, blockName, x, y, z, dimensionId, face):
    """水稻种植处理"""
    if SetPlayerUsedCD(playerId):
        return
    
    if blockName not in VALID_RICE_PLANTING_BLOCKS or face != 1:
        ServerComp.CreateGame(playerId).SetOneTipMessage(playerId, "水稻貌似无法种植在这个方块上...")
        return
    
    upBlock = ServerComp.CreateBlockInfo(levelId).GetBlockNew((x, y + 1, z), dimensionId)
    if upBlock["name"] != "minecraft:water":
        ServerComp.CreateGame(playerId).SetOneTipMessage(playerId, "水稻需要种植在静止的水中")
        return
    
    SetNotCreateItem(playerId, itemDict)
    soundPos = (x + 0.5, y + 1, z + 0.5)
    ToAllPlayerPlaySound(dimensionId, soundPos, "dig.grass")
    ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y + 1, z), {"name": "arris:rice_stage0"}, 0, dimensionId, False, False)

def _useBoneMeal(playerId, itemDict, blockName, x, y, z, dimensionId):
    """骨粉使用处理"""
    if SetPlayerUsedCD(playerId):
        return
    
    # 处理生长状态
    blockStates = ServerComp.CreateBlockState(levelId).GetBlockStates((x, y, z), dimensionId)
    if blockStates:
        growth = blockStates.get("arris:growth")
        if growth is not None and growth < 7:
            growth += random.randint(2, 4)
            blockStates["arris:growth"] = min(growth, 7)
            ServerComp.CreateBlockState(levelId).SetBlockStates((x, y, z), blockStates, dimensionId)
            particlePos = (x + 0.5, y + 0.5, z + 0.5)
            CallAllClient("PlayParticle", particlePos)
            ToAllPlayerPlaySound(dimensionId, particlePos, "item.bone_meal.use")
            SetNotCreateItem(playerId, itemDict)
    
    # 处理作物催熟
    if blockName in cropsDict:
        data = {
            "blockName": blockName,
            "playerId": playerId,
            "itemDict": itemDict,
            "dimensionId": dimensionId,
            "blockPos": (x, y, z)
        }
        CropAccelerateTheRipening(data)

def _plantMushroom(playerId, itemDict, itemName, x, y, z, dimensionId):
    """蘑菇种植处理"""
    if SetPlayerUsedCD(playerId):
        return
    
    mushroomType = MUSHROOM_COLONY_MAP.get(itemName)
    if not mushroomType:
        return
    
    SetNotCreateItem(playerId, itemDict)
    ToAllPlayerPlaySound(dimensionId, (x + 0.5, y + 0.5, z + 0.5), "dig.grass")
    ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y + 1, z), {"name": mushroomType}, 0, dimensionId, False, False)

@ListenServer("ServerItemUseOnEvent")
def OnServerItemUse(args):
    """优化的物品使用处理函数"""
    itemDict = args["itemDict"]
    itemName = itemDict["newItemName"]
    dimensionId = args["dimensionId"]
    x, y, z = args["x"], args["y"], args["z"]
    playerId = args["entityId"]
    blockName = args["blockName"]
    face = args["face"]
    
    # 水稻种植
    if itemName == "arris:rice":
        _plantRice(playerId, itemDict, blockName, x, y, z, dimensionId, face)
        return
    
    # 骨粉使用
    if itemName == "minecraft:bone_meal":
        _useBoneMeal(playerId, itemDict, blockName, x, y, z, dimensionId)
        return
    
    # 蘑菇种植
    if face == 1 and blockName in VALID_MUSHROOM_BLOCKS and itemName in MUSHROOM_COLONY_MAP:
        _plantMushroom(playerId, itemDict, itemName, x, y, z, dimensionId)

# 种子到作物的映射字典
SEEDS_TO_CROP_MAP = {
    "minecraft:wheat_seeds": "arris:rich_soil_wheat0",
    "minecraft:beetroot_seeds": "arris:rich_soil_beetroot0",
    "minecraft:potato": "arris:rich_soil_potatoes0",
    "minecraft:carrot": "arris:rich_soil_carrots0",
    "minecraft:torchflower_seeds": "arris:rich_soil_torchflower0",
}

RICH_FARMLAND_BLOCKS = frozenset([
    "arris:rich_soil_farmland_moist", "arris:rich_soil_farmland"
])

@ListenServer("ItemUseOnAfterServerEvent")
def OnItemUseOnAfter(args):
    """优化的物品使用后处理函数"""
    playerId = args["entityId"]
    itemDict = args["itemDict"]
    dimensionId = args["dimensionId"]
    x, y, z = args["x"], args["y"], args["z"]
    face = args["face"]
    blockName = args["blockName"]
    itemName = itemDict["newItemName"]
    
    if SetPlayerUsedCD(playerId):
        return
    
    # 富饶土壤锄地
    if blockName == "arris:rich_soil":
        itemType = GetItemType(itemDict)
        if itemType == "hoe":
            SetCarriedDurability(playerId, itemDict, dimensionId, (x, y, z))
            ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y, z), {"name": "arris:rich_soil_farmland"}, 0, dimensionId, False, False)
            ToAllPlayerPlaySound(dimensionId, (x, y, z), "use.gravel")
        return
    
    # 富饶农田种植
    if blockName in RICH_FARMLAND_BLOCKS and face == 1:
        upBlock = ServerComp.CreateBlockInfo(levelId).GetBlockNew((x, y + 1, z), dimensionId)
        if upBlock["name"] != "minecraft:air":
            return
        
        cropName = SEEDS_TO_CROP_MAP.get(itemName)
        if cropName:
            ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y + 1, z), {"name": cropName}, 0, dimensionId, False, False)
            ToAllPlayerPlaySound(dimensionId, (x + 0.5, y + 1, z + 0.5), "dig.grass")
            SetNotCreateItem(playerId, itemDict)

def _harvestTomato(playerId, x, y, z, dimensionId, carriedDict, blockName, resetStage, args):
    """番茄采摘统一处理"""
    if SetPlayerUsedCD(playerId):
        return
    
    itemName = carriedDict.get("newItemName") if carriedDict else None
    soundPos = (x + 0.5, y + 1, z + 0.5)
    
    # 骨粉使用
    if itemName == "minecraft:bone_meal":
        blockDict = ServerComp.CreateBlockInfo(levelId).GetBlockNew((x, y + 1, z), dimensionId)
        if blockDict["name"] == "arris:rope":
            ToAllPlayerPlaySound(dimensionId, soundPos, "item.bone_meal.use")
            CallAllClient("PlayParticle", soundPos)
            # 藤蔓番茄需要生成新藤蔓
            if blockName == "arris:tomatoes_vine_stage3":
                ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y + 1, z), {"name": "arris:tomatoes_vine_stage0"}, 0, dimensionId, False, False)
    else:
        # 采摘番茄
        blockPos = (x + 0.5, y, z + 0.5)
        count = random.randint(1, 2)
        ServerObj.CreateEngineItemEntity({"itemName": "arris:tomato", "count": count}, dimensionId, blockPos)
        ToAllPlayerPlaySound(dimensionId, blockPos, "block.sweet_berry_bush.pick")
        ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y, z), {"name": resetStage}, 0, dimensionId, False, False)
    
    args["ret"] = True

def _harvestCabbage(playerId, x, y, z, dimensionId, args):
    """卷心菜采摘处理"""
    if SetPlayerUsedCD(playerId):
        return
    
    blockPos = (x + 0.5, y, z + 0.5)
    count = random.randint(1, 2)
    ServerObj.CreateEngineItemEntity({"itemName": "arris:cabbage_leaf", "count": count}, dimensionId, blockPos)
    ToAllPlayerPlaySound(dimensionId, blockPos, "block.sweet_berry_bush.pick")
    ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y, z), {"name": "arris:cabbages_stage3"}, 0, dimensionId, False, False)
    args["ret"] = True

def _growRiceWithBoneMeal(playerId, x, y, z, dimensionId, carriedDict):
    """用骨粉催熟水稻"""
    if SetPlayerUsedCD(playerId):
        return
    
    if not carriedDict:
        return
    
    itemName = carriedDict.get("newItemName")
    if itemName == "minecraft:bone_meal":
        blockDict = ServerComp.CreateBlockInfo(levelId).GetBlockNew((x, y + 1, z), dimensionId)
        if blockDict["name"] == "minecraft:air":
            soundPos = (x + 0.5, y + 1, z + 0.5)
            ToAllPlayerPlaySound(dimensionId, soundPos, "item.bone_meal.use")
            CallAllClient("PlayParticle", soundPos)
            ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y + 1, z), {"name": "arris:rice_upper_crop_stage0"}, 0, dimensionId, False, False)

@ListenServer("ServerBlockUseEvent")
def OnServerBlockUse(args):
    """优化的方块使用处理函数"""
    blockName = args["blockName"]
    x, y, z = args["x"], args["y"], args["z"]
    dimensionId = args["dimensionId"]
    playerId = args["playerId"]
    carriedDict = ServerComp.CreateItem(playerId).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
    
    # 成熟的番茄采摘
    if blockName == "arris:budding_tomatoes_stage6":
        _harvestTomato(playerId, x, y, z, dimensionId, carriedDict, blockName, "arris:budding_tomatoes_stage3", args)
    
    # 藤蔓番茄采摘
    elif blockName == "arris:tomatoes_vine_stage3":
        _harvestTomato(playerId, x, y, z, dimensionId, carriedDict, blockName, "arris:tomatoes_vine_stage0", args)
    
    # 卷心菜采摘
    elif blockName == "arris:cabbages_stage7":
        _harvestCabbage(playerId, x, y, z, dimensionId, args)
    
    # 水稻催熟
    elif blockName == "arris:rice_stage3":
        _growRiceWithBoneMeal(playerId, x, y, z, dimensionId, carriedDict)

# 作物生长配置 - 数据驱动方式，格式: (作物前缀, 最大生长阶段)
CROP_GROWTH_CONFIG = {
    "arris:cabbages_stage": 7,
    "arris:budding_tomatoes_stage": 6,
    "arris:tomatoes_vine_stage": 3,
    "arris:onions_stage": 3,
    "arris:rich_soil_wheat": 7,
    "arris:rich_soil_beetroot": 3,
    "arris:rich_soil_carrots": 3,
    "arris:rich_soil_potatoes": 3,
    "arris:rice_stage": 3,
    "arris:rice_upper_crop_stage": 3,
    "arris:rich_soil_torchflower": 2,
}

def CropAccelerateTheRipening(data, mode=None):
    """优化的作物催熟函数 - 使用数据驱动方式"""
    blockName = data["blockName"]
    playerId = data["playerId"]
    itemDict = data["itemDict"]
    dimensionId = data["dimensionId"]
    x, y, z = data["blockPos"]
    
    # 提取作物前缀和当前阶段
    if not blockName or len(blockName) < 2:
        return
    
    try:
        currentStage = int(blockName[-1])
    except ValueError:
        return
    
    cropPrefix = blockName[:-1]
    
    # 检查是否为可催熟的作物
    maxStage = CROP_GROWTH_CONFIG.get(cropPrefix)
    if maxStage is None:
        return
    
    # 检查是否已达到最大阶段
    if currentStage >= maxStage:
        return
    
    # 计算生长数量
    growthAmount = 1 if mode == "rich_soil_farmland" else random.randint(2, 3)
    
    # 扣除物品
    if playerId:
        SetNotCreateItem(playerId, itemDict)
    
    # 计算新阶段
    newStage = min(currentStage + growthAmount, maxStage)
    newBlockName = cropPrefix + str(newStage)
    
    # 更新方块
    ServerComp.CreateBlockInfo(levelId).SetBlockNew((x, y, z), {"name": newBlockName}, 0, dimensionId, False, False)
    
    # 播放音效和粒子
    soundPos = (x + 0.5, y, z + 0.5)
    ToAllPlayerPlaySound(dimensionId, soundPos, "item.bone_meal.use")
    CallAllClient("PlayParticle", soundPos)

@ListenServer("DestroyBlockEvent")
def OnDestroyBlock(args):
    # 防止精准采集挖掘龙腿掉落
    blockName = args["fullName"]
    if blockName not in ["arris:brown_mushroom_colony", "arris:red_mushroom_colony"]:
        return
    playerId = args["playerId"]
    handItemDict = ServerComp.CreateItem(playerId).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0, True)
    if handItemDict is None:
        return
    enchantData = handItemDict.get("enchantData")
    if not enchantData:
        return
    for enchant in enchantData:
        if enchant[0] == 16:
            dropItemList = args["dropEntityIds"]
            for Id in dropItemList:
                ServerObj.DestroyEntity(Id)
