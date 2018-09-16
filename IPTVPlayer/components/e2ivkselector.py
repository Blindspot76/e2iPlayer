# -*- coding: utf-8 -*-
#
#  Keyboard Selector
#
#  $Id$
#
# 
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc
from Components.config import config

def GetVirtualKeyboard():
    type = config.plugins.iptvplayer.osk_type.value
    
    if type in ['own', '']:
        try:
            from enigma import getDesktop
            if getDesktop(0).size().width() >= 1050:
                from Plugins.Extensions.IPTVPlayer.components.e2ivk import E2iVirtualKeyBoard
                return E2iVirtualKeyBoard
        except Exception:
            printExc()

    try:
        from Screens.VirtualKeyBoard import VirtualKeyBoard
        return VirtualKeyBoard
    except Exception:
        printExc()
