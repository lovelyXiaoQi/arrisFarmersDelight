# -*- coding: utf-8 -*-
from serverUtils.serverUtils import *
from ..modCommon.modConfig import CookingPotRecipeList
# 导入可调用的3个接口函数
from ..modCommon.modConfig import ArrisFarmersDelightInterface
from ..modCommon.modConfig import ArrisFarmersDelightObtain
from ..modCommon.modConfig import AddCookingPotRecipe

# 用于为Arris内部其它副包提供联动接口
ServerComp.CreateModAttr("arris").SetAttr("ArrisFarmersDelightInterface", ArrisFarmersDelightInterface)
ServerComp.CreateModAttr("arris").SetAttr("ArrisFarmersDelightObtain", ArrisFarmersDelightObtain)
ServerComp.CreateModAttr("arris").SetAttr("ArrisAddCookingPotRecipe", AddCookingPotRecipe)
# 堆肥桶设置监听
ServerComp.CreateBlockUseEventWhiteList(levelId).AddBlockItemListenForUseEvent("minecraft:composter:*")

@ListenServer("ClientLoadAddonsFinishServerEvent")
def ClientLoadAddonsFinish(args):
    # 给新加入的玩家设置CD并重置
    playerId = args["playerId"]
    ServerComp.CreateModAttr(playerId).SetAttr("arrisUsedCD", False)
    CallAllClient("SetCookingPotRecipeList", CookingPotRecipeList)

@ListenServer("ItemUseAfterServerEvent")
def OnRottenTomatoUseAfterServer(args):
    itemDict = args["itemDict"]
    itemName = itemDict["newItemName"]
    if itemName == "arris:rotten_tomato":
        # 发射烂番茄抛射物
        playerId = args["entityId"]
        SetNotCreateItem(playerId, itemDict)
        ServerComp.CreateProjectile(levelId).CreateProjectileEntity(playerId, "arris:rotten_tomato")

@ListenServer("ServerBlockUseEvent")
def OnServerBlockUseCommon(args):
    # 播放橱柜打开声音
    blockName = args["blockName"]
    blockPos = (args["x"], args["y"], args["z"])
    dimensionId = args["dimensionId"]
    playerId = args["playerId"]
    if blockName in cabinetList:
        if SetPlayerUsedCD(playerId) is True:
            return
        ToAllPlayerPlaySound(dimensionId, blockPos, "block.barrel.open")

    elif blockName in pieList:
        if SetPlayerUsedCD(playerId) is True:
            return
        blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, blockPos)
        if blockEntityData:
            blockEntityData["blockStatus"] += 1
            blockStatus = blockEntityData["blockStatus"]
            data = {"name": "variable.mod_pie", "blockPos": blockPos, "molang": blockStatus}
            ToAllPlayerPlaySound(dimensionId, blockPos, "random.eat")
            ServerComp.CreateEffect(playerId).AddEffectToEntity("speed", 30, 1, False)
            playerHunger = ServerComp.CreatePlayer(playerId).GetPlayerHunger()
            playerHunger += 3
            ServerComp.CreatePlayer(playerId).SetPlayerHunger(playerHunger)
            CallAllClient("SetEntityBlockMolang", data)
            if blockEntityData["blockStatus"] == 4.0:
                ServerComp.CreateBlockInfo(levelId).SetBlockNew(blockPos, {"name": "minecraft:air"}, 0, dimensionId)

    elif blockName == "minecraft:composter":
        x, y, z = blockPos
        blockStates = ServerComp.CreateBlockState(levelId).GetBlockStates((x, y, z), dimensionId)
        if blockStates["composter_fill_level"] < 8:
            handItemDict = ServerComp.CreateItem(playerId).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
            if handItemDict:
                itemName = handItemDict["newItemName"]
                itemAux = handItemDict["newAuxValue"]
                item = (itemName, itemAux)
                if item in ComposterItemDict:
                    ToAllPlayerPlaySound(dimensionId, (x + 0.5, y, z + 0.5), "block.composter.fill")
                    ToAllPlayerPlaySound(dimensionId, (x + 0.5, y, z + 0.5), "item.bone_meal.use")
                    CallAllClient("PlayParticle", (x + 0.5, y + 0.8, z + 0.5))
                    SetNotCreateItem(playerId, handItemDict)
                    if ProbabilityFunc(ComposterItemDict[item]) is True:
                        blockStates["composter_fill_level"] += 1
                        ToAllPlayerPlaySound(dimensionId, (x + 0.5, y, z + 0.5), "block.composter.fill_success")
                        ServerComp.CreateBlockState(levelId).SetBlockStates((x, y, z), blockStates, dimensionId)

@ListenServer("OnEntityInsideBlockServerEvent")
def OnEntityInsideBasketServer(args):
    # 将篮子内的掉落物吸取进篮子内
    blockName = args["blockName"]
    entityId = args["entityId"]
    if blockName == "arris:basket":
        identifier = ServerComp.CreateEngineType(entityId).GetEngineTypeStr()
        if identifier == "minecraft:item":
            itemDict = ServerComp.CreateItem(levelId).GetDroppedItem(entityId)
            blockPos = (args["blockX"], args["blockY"], args["blockZ"])
            dimensionId = ServerComp.CreateDimension(entityId).GetEntityDimensionId()
            for index in range(0, 27):
                containerItem = ServerComp.CreateItem(levelId).GetContainerItem(blockPos, index, dimensionId)
                if containerItem is None:
                    ServerComp.CreateItem(levelId).SpawnItemToContainer(itemDict, index, blockPos, dimensionId)
                    DesEntityServer(entityId)
                    break

@ListenServer("ServerItemUseOnEvent")
def OnServerItemUseCommon(args):
    # 玩家在对方块使用物品之前服务端抛出的事件
    itemDict = args["itemDict"]
    itemName = itemDict["newItemName"]
    dimensionId = args["dimensionId"]
    x = args["x"]
    y = args["y"]
    z = args["z"]
    blockName = args["blockName"]
    if blockName in ["arris:cutting_board", "arris:cabbages_stage7", "arris:budding_tomatoes_stage6", "arris:tomatoes_vine_stage3"]:
        args["ret"] = True

    if itemName in WildCropDict:
        # 野生作物正确放置
        face = args["face"]
        faceDict = clickBlockFace(x, y, z)
        pos = faceDict[face]
        blockDict = ServerComp.CreateBlockInfo(levelId).GetBlockNew((pos[0], pos[1] - 1, pos[2]), dimensionId)
        blockName = blockDict["name"]
        if blockName not in WildCropDict[itemName]:
            args["ret"] = True
        if itemName == "arris:wild_rice":
            # 单独判断野生稻米的放置条件
            upBlockDict = ServerComp.CreateBlockInfo(levelId).GetBlockNew((pos[0], pos[1] + 1, pos[2]), dimensionId)
            upBlockName = upBlockDict["name"]
            if upBlockName != "minecraft:air":
                args["ret"] = True

    if itemName in itemChangeBlockDict:
        if blockName not in ["minecraft:frame", "minecraft:glow_frame", "arris:cutting_board"]:
            playerId = args["entityId"]
            if SetPlayerUsedCD(playerId) is True:
                return
            face = args["face"]
            placePos = clickBlockFace(x, y, z)
            setPos = placePos[face]
            pX, pY, pZ = ServerComp.CreatePos(playerId).GetFootPos()
            aux = DetectionExperimentalHoliday()
            blockAux = aux.get(FromAngleGetBlockAux(x, z, pX, pZ), FromAngleGetBlockAux(x, z, pX, pZ))
            blockDict = {"name": itemChangeBlockDict[itemName]}
            placeBlock = ServerComp.CreateBlockInfo(levelId).GetBlockNew(setPos, dimensionId)["name"]
            if placeBlock == "minecraft:air":
                SetNotCreateItem(playerId, itemDict)
                ServerComp.CreateBlockInfo(levelId).SetBlockNew(setPos, blockDict, 0, dimensionId)
                blockStates = ServerComp.CreateBlockState(levelId).GetBlockStates(setPos, dimensionId)
                if blockStates:
                    blockStates["direction"] = blockAux
                    ServerComp.CreateBlockState(levelId).SetBlockStates(setPos, blockStates, dimensionId)
                blockEntityData = ServerComp.CreateBlockEntityData(levelId).GetBlockEntityData(dimensionId, setPos)
                if blockEntityData and itemChangeBlockDict[itemName] in pieList:
                    ToAllPlayerPlaySound(dimensionId, setPos, "dig.cloth")
                    blockEntityData["blockStatus"] = 0.0
                    blockEntityData["setMolang"] = False

@ListenServer("DestroyBlockEvent")
def OnDestroyBlockCommon(args):
    # 当方块已经被玩家破坏时触发该事件
    blockName = args["fullName"]
    if blockName in ["minecraft:double_plant", "minecraft:tallgrass", "arris:sandy_shrub", "arris:rich_soil_wheat7", "arris:rice_upper_crop_stage3", "arris:rice_supporting"]:
        dimensionId = args["dimensionId"]
        playerId = args["playerId"]
        gameType = ServerComp.CreateGame(levelId).GetPlayerGameType(playerId)
        if gameType == 1:
            return
        pos = (args["x"] + 0.5, args["y"], args["z"] + 0.5)
        if ProbabilityFunc(30) is True:
            itemDict = {
                "itemName": "arris:straw",
                "count": 1,
                "auxValue": 0
            }
            ServerObj.CreateEngineItemEntity(itemDict, dimensionId, pos)

@ListenServer("EntityDieLoottableServerEvent")
def OnEntityDieLoottableCommon(args):
    # 使用刀杀死牛、鸡后掉落物翻倍,猪概率掉落火腿
    attackerId = args["attacker"]
    dieEntityId = args["dieEntityId"]
    entityName = ServerComp.CreateEngineType(attackerId).GetEngineTypeStr()
    if entityName == "minecraft:player":
        entityName = ServerComp.CreateEngineType(dieEntityId).GetEngineTypeStr()
        handItemDict = ServerComp.CreateItem(attackerId).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
        if handItemDict and handItemDict["newItemName"] in knifeList:
            itemList = args["itemList"]
            if entityName in ["minecraft:cow", "minecraft:chicken"]:
                for index in range(0, len(itemList)):
                    itemDict = itemList[index]
                    itemDict["count"] *= 2
                    itemList[index] = itemDict
                args["itemList"] = itemList
                args["dirty"] = True
            elif entityName == "minecraft:pig":
                if ProbabilityFunc(80) is True:
                    hamDict = {"itemName": "arris:ham", "count": 1}
                    itemList.append(hamDict)
                    args["itemList"] = itemList
                    args["dirty"] = True

@ListenServer("PlayerAttackEntityEvent")
def PlayerAttackEntityCommon(args):
    playerId = args["playerId"]
    itemDict = ServerComp.CreateItem(playerId).GetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
    victimId = args["victimId"]
    if itemDict:
        if itemDict["newItemName"] == "arris:skillet_item":
            dimensionId = ServerComp.CreateDimension(playerId).GetEntityDimensionId()
            pos = ServerComp.CreatePos(playerId).GetFootPos()
            ToAllPlayerPlaySound(dimensionId, pos, "ambient.skillet.attack_strong")

@ListenServer("PlayerFeedEntityServerEvent")
def PlayerFeedEntityServerCommon(args):
    itemDict = args["itemDict"]
    entityId = args["entityId"]
    comp = ServerComp.CreateEffect(entityId)
    if itemDict["newItemName"] == "arris:dog_food":
        comp.AddEffectToEntity("speed", 300, 0, True)
        comp.AddEffectToEntity("strength", 300, 0, True)
        comp.AddEffectToEntity("resistance", 300, 0, True)
        playerId = args["playerId"]
        ServerComp.CreateItem(playerId).SpawnItemToPlayerInv({"itemName": "minecraft:bowl", 'count': 1}, playerId)
    elif itemDict["newItemName"] == "arris:horse_feed":
        comp.AddEffectToEntity("speed", 300, 1, True)
        comp.AddEffectToEntity("jump_boost", 300, 0, True)

@ListenServer("HealthChangeBeforeServerEvent")
def OnHealthChangeBeforeCommon(args):
    # 防止展示物品的实体被Kill
    entityId = args["entityId"]
    identifier = ServerComp.CreateEngineType(entityId).GetEngineTypeStr()
    if identifier == "arris:item_display":
        args["cancel"] = True

@ListenServer("WillTeleportToServerEvent")
def OnWillTeleportToServerCommon(args):
    # 阻止展示物品的实体被传送走。
    entityId = args["entityId"]
    identifier = ServerComp.CreateEngineType(entityId).GetEngineTypeStr()
    if identifier == "arris:item_display":
        args["cancel"] = True

@ListenServer("WillAddEffectServerEvent")
def OnWillAddEffectServerCommon(args):
    # 阻止展示物品的实体被给予药水效果。
    entityId = args["entityId"]
    identifier = ServerComp.CreateEngineType(entityId).GetEngineTypeStr()
    if identifier == "arris:item_display":
        args["cancel"] = True

@ListenServer("DamageEvent")
def OnDamageCommon(args):
    # 物品展示实体修复器
    playerId = args["srcId"]
    entityId = args["entityId"]
    entityName = ServerComp.CreateEngineType(entityId).GetEngineTypeStr()
    if entityName in ["arris:item_display", "arris:corpse_display"]:
        carriedDict = ServerComp.CreateItem(playerId).GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
        if carriedDict and carriedDict["newItemName"] == "arris:item_display_destroy":
            DesEntityServer(entityId)
            ServerComp.CreateGame(playerId).SetOneTipMessage(playerId, "§7物品展示实体 §a删除成功!")
            ServerComp.CreateItem(playerId).SetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, {}, 0)

@Call()
def PlayerShapedRecipe(args):
    itemDict = args["itemDict"]
    dimensionId = args["dimensionId"]
    playerPos = args["playerPos"]
    ServerObj.CreateEngineItemEntity(itemDict, dimensionId, playerPos)

@Call()
def GetEntityCarriedItem(entityId):
    itemDict = ServerComp.CreateItem(entityId).GetEntityItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0)
    if itemDict:
        itemType = GetItemType(itemDict)
        itemName = itemDict["newItemName"]
        auxValue = itemDict["newAuxValue"]
        key = (itemName, auxValue)
        if key in CuttingBoardDict:
            exceptional = CuttingBoardDict[key].get("type")
            if exceptional is not None:
                itemType = exceptional
            CallAllClient("SetItemDisplayMolang", {"itemType": itemType, "entityId": entityId})
    else:
        CallAllClient("SetItemDisplayMolang", {"itemType": None, "entityId": entityId})
