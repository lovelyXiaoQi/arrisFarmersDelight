# -*- coding: utf-8 -*-
from QingYunModLibs.ClientMod import *
from QingYunModLibs.SystemApi import *
from modCommon.modConfig import *

def CuttingBoardHandleFunc(recipeControl, recipe, uiNode=None, itemName=None):
    data = recipe["recipe"]["output"]
    inputItem = recipe["recipe"]["input"]
    inputRender = recipeControl.GetChildByPath("/bg/stack_panel/cutting_board_panel/cutting_board_bg/jeiInputFoodRender/item_cell/item/item_renderer")
    inputRender.asItemRenderer().SetUiItem(inputItem[0], inputItem[1])
    tool = data["tool"]
    toolRender = recipeControl.GetChildByPath("/bg/stack_panel/cutting_board_panel/jeiKnifeRenderer/item_cell/item/item_renderer")
    toolRender.asItemRenderer().SetUiItem(tool[0], 0)
    grid = recipeControl.GetChildByPath("/bg/stack_panel/output_panel/grid")
    grid.asGrid().SetGridDimension((len(data["itemList"]), 1))
    for index in xrange(len(data["itemList"])):
        outputItemData = data["itemList"][index]
        count = outputItemData.get("count", 1)
        outputItemName = outputItemData["itemName"]
        outputItemRender = recipeControl.GetChildByPath("/bg/stack_panel/output_panel/grid/jeiInputItemRender" + str(index + 1) + "/item_cell/item/item_renderer")
        if not outputItemRender:
            continue
        outputItemRender.asItemRenderer().SetUiItem(outputItemName, 0)
        label = recipeControl.GetChildByPath("/bg/stack_panel/output_panel/grid/jeiInputItemRender" + str(index + 1) + "/item_cell/item/stack_count_label")
        label.asLabel().SetText(str(count))

def LoopCuttingBoardHandleFunc(recipeControl, recipe, uiNode=None, itemName=None):
    recipe["index"] += 1
    data = recipe["recipe"]["output"]
    tool = data["tool"]
    if recipe["index"] >= len(tool):
        recipe["index"] = 0
    toolRender = recipeControl.GetChildByPath("/bg/stack_panel/cutting_board_panel/jeiKnifeRenderer/item_cell/item/item_renderer")
    toolRender.asItemRenderer().SetUiItem(tool[recipe["index"]], 0)

def CookingPotHandleFunc(recipeControl, recipe, uiNode=None, itemName=None):
    if not recipe["Recipe"]:
        return
    inputNum = len(recipe["Recipe"][0])
    for index in xrange(inputNum):
        inputItemData = recipe["Recipe"][0][index]
        inputRender = recipeControl.GetChildByPath("/bg/stack_panel/input_panel/jeiInputItemRender" + str(index + 1) + "/item_cell/item/item_renderer")
        inputRender.SetVisible(True)
        inputRender.asItemRenderer().SetUiItem(inputItemData[0], inputItemData[1])
    for index in xrange(inputNum, 6):
        inputRender = recipeControl.GetChildByPath("/bg/stack_panel/input_panel/jeiInputItemRender" + str(index + 1) + "/item_cell/item/item_renderer")
        inputRender.SetVisible(False)
    vessel = recipe["Vessel"]
    inputRender = recipeControl.GetChildByPath("/bg/stack_panel/output_panel/jeiVesselItemRender/item_cell/item/item_renderer")
    inputRender.asItemRenderer().SetUiItem(vessel[0], vessel[1])
    cookResult = recipe["CookResult"]
    inputRender = recipeControl.GetChildByPath("/bg/stack_panel/output_panel/jeiOutputItemRender/item_cell/item/item_renderer")
    inputRender.asItemRenderer().SetUiItem(cookResult[0], cookResult[1])

def LoopCookingPotHandleFunc(recipeControl, recipe, uiNode=None, itemName=None):
    recipe["index"] += 1
    if recipe["index"] >= len(recipe["Recipe"]):
        recipe["index"] = 0
    index = recipe["index"]
    inputNum = len(recipe["Recipe"][index])
    for i in xrange(inputNum):
        inputItemData = recipe["Recipe"][index][i]
        inputRender = recipeControl.GetChildByPath("/bg/stack_panel/input_panel/jeiInputItemRender" + str(i + 1) + "/item_cell/item/item_renderer")
        inputRender.SetVisible(True)
        inputRender.asItemRenderer().SetUiItem(inputItemData[0], inputItemData[1])
    for i in xrange(inputNum, 6):
        inputRender = recipeControl.GetChildByPath("/bg/stack_panel/input_panel/jeiInputItemRender" + str(i + 1) + "/item_cell/item/item_renderer")
        inputRender.SetVisible(False)

def SkilletAndStoveHandleFunc(recipeControl, recipe, uiNode=None, itemName=None):
    outputItem = recipe["output"]
    inputItem = recipe["input"]
    inputRender = recipeControl.GetChildByPath("/bg/jeiInputItemRender/item_cell/item/item_renderer")
    inputRender.asItemRenderer().SetUiItem(inputItem, 0)
    outputRender = recipeControl.GetChildByPath("/bg/jeiOutputItemRender/item_cell/item/item_renderer")
    outputRender.asItemRenderer().SetUiItem(outputItem, 0)

def GetCuttingBoardRecipesByResult(itemName, itemAux=0):
    recipeList = []
    for inputItem, data in CuttingBoardDict.items():
        for outputItemData in data["itemList"]:
            outputName = outputItemData.get("itemName")
            outputAux = outputItemData.get("itemAux", 0)
            if outputName != itemName or outputAux != itemAux:
                continue
            recipeList.append({"recipe": {"output": data, "input": inputItem}})
    return recipeList

def GetCuttingBoardRecipesByInput(itemName, itemAux=0):
    recipeList = []
    for inputItem, data in CuttingBoardDict.items():
        if inputItem[0] == itemName and inputItem[1] == itemAux:
            recipeList.append({"recipe": {"output": data, "input": inputItem}})
        for tool in data["tool"]:
            if tool != itemName:
                continue
            recipeList.append({"recipe": {"output": data, "input": inputItem}})
    return recipeList

def GetCookingPotRecipesByResult(itemName, itemAux=0):
    recipeList = []
    for recipe in CookingPotRecipeList:
        outputItem = recipe["CookResult"]
        if outputItem[0] != itemName or outputItem[1] != itemAux:
            continue
        recipeList.append(recipe)
    return recipeList

def GetCookingPotRecipesByInput(itemName, itemAux=0):
    recipeList = []
    for recipe in CookingPotRecipeList:
        for inputData in recipe["Recipe"]:
            for inputItem in inputData:
                if inputItem[0] != itemName or inputItem[1] != itemAux or recipe in recipeList:
                    continue
                recipeList.append(recipe)
        vessel = recipe["Vessel"]
        if vessel[0] == itemName and vessel[1] == itemAux and recipe not in recipeList:
            recipeList.append(recipe)
    return recipeList

def GetSkilletAndStoveRecipesByResult(itemName, itemAux=0):
    recipeList = []
    for inputItem, outputItem in CanCookedFoodDict.items():
        if outputItem != itemName:
            continue
        recipeList.append({"input": inputItem, "output": outputItem})
    return recipeList

def GetSkilletAndStoveRecipesByInput(itemName, itemAux=0):
    recipeList = []
    for inputItem, outputItem in CanCookedFoodDict.items():
        if inputItem != itemName:
            continue
        recipeList.append({"input": inputItem, "output": outputItem})
    return recipeList

def FarmersDelightJeiLinkageInit():
    jeiLinkage = clientApi.ImportModule("arrisJeiScripts.jeiLinkage")
    if not jeiLinkage:
        return
    func = jeiLinkage.arrisJeiLinkage
    for tagName, data in jeiData.items():
        func(tagName, data)

    jeiLinkage.arrisJeiAddItemRecipesByResult("cutting_board", GetCuttingBoardRecipesByResult)
    jeiLinkage.arrisJeiAddItemRecipesByInput("cutting_board", GetCuttingBoardRecipesByInput)
    jeiLinkage.arrisJeiAddItemRecipesByResult("cooking_pot", GetCookingPotRecipesByResult)
    jeiLinkage.arrisJeiAddItemRecipesByInput("cooking_pot", GetCookingPotRecipesByInput)
    jeiLinkage.arrisJeiAddItemRecipesByResult("stove", GetSkilletAndStoveRecipesByResult)
    jeiLinkage.arrisJeiAddItemRecipesByInput("stove", GetSkilletAndStoveRecipesByInput)
    jeiLinkage.arrisJeiAddItemRecipesByResult("skillet", GetSkilletAndStoveRecipesByResult)
    jeiLinkage.arrisJeiAddItemRecipesByInput("skillet", GetSkilletAndStoveRecipesByInput)

jeiData = {
    "cutting_board": {
        "item": ("arris:cutting_board", 0),
        "y_size": 47,
        "ui_control": "jei_farmers_delight.jeiCuttingBoardRecipe",
        "func": CuttingBoardHandleFunc,
        "loop_func": LoopCuttingBoardHandleFunc,
        "mode": "gridChanged",
        "text": "砧板"
    },
    "cooking_pot": {
        "item": ("arris:cooking_pot", 0),
        "y_size": 65,
        "ui_control": "jei_farmers_delight.jeiCookingPotRecipe",
        "func": CookingPotHandleFunc,
        "loop_func": LoopCookingPotHandleFunc,
        "mode": "gridChanged",
        "text": "厨锅"
    },
    "stove": {
        "item": ("arris:stove", 0),
        "y_size": 55,
        "ui_control": "jei_farmers_delight.jeiSkilletAndStoveRecipe",
        "func": SkilletAndStoveHandleFunc,
        "text": "炉灶"
    },
    "skillet": {
        "item": ("arris:skillet", 0),
        "y_size": 55,
        "ui_control": "jei_farmers_delight.jeiSkilletAndStoveRecipe",
        "func": SkilletAndStoveHandleFunc,
        "text": "煎锅"
    }
}
