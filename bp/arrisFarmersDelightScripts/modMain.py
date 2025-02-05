# -*- coding: utf-8 -*-
from QingYunModLibs.ModInit.QingYunMod import *
Mod = QingYunMod()
Mod.InitMod("arrisFarmersDelightScripts")

serverSystem = [
    "modServer.farmersDelightCommon",
    "modServer.cookingPot",
    "modServer.effect",
    "modServer.ropeAndNet",
    "modServer.farmCrop",
    "modServer.platePackagedFood",
    "modServer.skillet",
    "modServer.cuttingBoard",
    "modServer.stove"
]

clientSystem = [
    "modClient.farmersDelightCommon",
    "modClient.cookingPot"
]

for sys in serverSystem:
    Mod.ServerInit(sys)
for sys in clientSystem:
    Mod.ClientInit(sys)
