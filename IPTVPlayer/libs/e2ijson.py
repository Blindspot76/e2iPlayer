# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify
###################################################

###################################################
# FOREIGN import
###################################################
try:    import json
except Exception: import simplejson as json
e2icjson = None
############################################

def loads(input, utf8=True, noneReplacement=None, baseTypesAsString=False):
    global e2icjson
    if e2icjson == None:
        try:
            from Plugins.Extensions.IPTVPlayer.libs.e2icjson import e2icjson
            e2icjson = e2icjson
        except Exception:
            e2icjson = False
            printExc()

    if e2icjson:
        printDBG(">> cjson ACELERATION")
        out = e2icjson.decode(input, 2 if utf8 else 1)
        if noneReplacement != None or baseTypesAsString != False:
            out = byteify(out, noneReplacement, baseTypesAsString)
    else:
        out = json.loads(input)
        if utf8 or noneReplacement != None or baseTypesAsString != False:
            out = byteify(out, noneReplacement, baseTypesAsString)

    return out

def dumps(input):
    return json.dumps(input)
