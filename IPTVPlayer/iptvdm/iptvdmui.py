# -*- coding: utf-8 -*-
#
#  IPTV download manager UI
#
#  $Id$
#
#
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, eConnectCallback
from Plugins.Extensions.IPTVPlayer.components.iptvplayer import IPTVStandardMoviePlayer, IPTVMiniMoviePlayer
from Plugins.Extensions.IPTVPlayer.components.iptvextmovieplayer import IPTVExtMoviePlayer
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _

from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvlist import IPTVDownloadManagerList
###################################################

###################################################
# FOREIGN import
###################################################
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from enigma import getDesktop
from enigma import eTimer
from Components.config import config
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
###################################################

#########################################################
#                    GLOBALS
#########################################################
gIPTVDM_listChanged = False

class IPTVDMWidget(Screen):

    sz_w = getDesktop(0).size().width() - 190
    sz_h = getDesktop(0).size().height() - 195
    if sz_h < 500:
        sz_h += 4
    skin = """
        <screen name="IPTVDMWidget" position="center,center" title="IPTV Player download manager" size="%d,%d">
         <ePixmap position="5,9" zPosition="4" size="30,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/icons/red.png" transparent="1" alphatest="on" />
         <ePixmap position="180,9" zPosition="4" size="30,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/icons/yellow.png" transparent="1" alphatest="on" />
         <ePixmap position="385,9" zPosition="4" size="30,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/icons/green.png" transparent="1" alphatest="on" />
         <ePixmap position="590,9" zPosition="4" size="35,30" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/icons/blue.png" transparent="1" alphatest="on" />
         <widget render="Label" source="key_red" position="45,9" size="140,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
         <widget render="Label" source="key_green" position="425,9" size="300,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />            
         <widget name="list" position="5,100" zPosition="2" size="%d,%d" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000" />
         <widget name="titel" position="5,47" zPosition="1" size="%d,23" font="Regular;20" transparent="1"  backgroundColor="#00000000"/>
        </screen>""" %(
            sz_w, sz_h, # size
            sz_w - 10, sz_h - 20, # size list
            sz_w - 135, # size titel
            )
        # <widget render="Label" source="key_yellow" position="220,9" size="180,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        # <widget render="Label" source="key_blue" position="630,9" size="140,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" /> 
    def __init__(self, session, downloadmanager):
        self.session = session
        Screen.__init__(self, session)
        
        self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.event.append(self.__event)

        self["key_red"] = StaticText(_("Stop"))
        self["key_green"] = StaticText(_("Start"))
        # self["key_yellow"] = StaticText("??")
        # self["key_blue"] = StaticText("??")

        self["list"] = IPTVDownloadManagerList()
        self["list"].connectSelChanged(self.onSelectionChanged)
        self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
        {
            "ok": self.ok_pressed,
            "back": self.back_pressed,
            "red": self.red_pressed,
            "green": self.green_pressed,
            "yellow": self.yellow_pressed,
            "blue": self.blue_pressed,
           
        }, -1)

        self["titel"] = Label()
        
        self.DM = downloadmanager
        self.DM.connectListChanged(self.onListChanged)
        self.DM.setUpdateProgress(True)
        self.setManagerStatus()
        
        self.started = 0
        global gIPTVDM_listChanged
        gIPTVDM_listChanged = True
        
        self.onClose.append(self.__onClose)
        self.onShow.append(self.onStart)
            
        #main Timer to refresh liar
        self.mainTimer = eTimer()
        self.mainTimer_conn = eConnectCallback(self.mainTimer.timeout, self.reloadList)
        # every 500ms Proxy Queue will be checked  
        self.mainTimer.start(500)
    #end def __init__(self, session):
    
    def leaveMoviePlayer(self, answer=None, position=None, *args, **kwargs):
        self.DM.setUpdateProgress(True)
        self.session.nav.playService(self.currentService)
        return
    
    def setManagerStatus(self):
        status = _("Manager status: ")
        if self.DM.isRunning():
            self["titel"].setText(status + _("STARTED"))
        else:
            self["titel"].setText(status + _("STOPPED"))
    
    def onListChanged(self):
        global gIPTVDM_listChanged
        gIPTVDM_listChanged = True
        return
        
    def __del__(self):
        printDBG("IPTVDMWidget.__del__ ---------------------------------------")
    
    def __onClose(self):
        # unsubscribe callback functions and break cycles references
        self.DM.disconnectListChanged(self.onListChanged)
        self.DM.setUpdateProgress(False)
        self.DM = None
        try:
            self.mainTimer_conn = None
            self.mainTimer.stop()
            self.mainTimer = None
        except:
            printExc()
        try:
            self.currentService = None
            self.session.nav.event.remove(self.__event)
            self["list"].disconnectSelChanged(self.onSelectionChanged)

            self.onClose.remove(self.__onClose)
            self.onShow.remove(self.onStart)
        except:
            printExc()
 
    def red_pressed(self):
        self.DM.stopWorkThread()
        self.setManagerStatus()
        return

    def green_pressed(self):
        self.DM.runWorkThread()
        self.setManagerStatus()
        return

    def yellow_pressed(self):
        return
 
    def blue_pressed(self):
        return  
    
    def onSelectionChanged(self):      
        return

 
    def back_pressed(self):
        self.close()
        return

    def ok_pressed(self): 
        # wszystkie dostepne opcje
        if 'sh4' == config.plugins.iptvplayer.plarform.value:
            play = []
            play.append((_('Play with [%s] player') % config.plugins.iptvplayer.defaultSH4MoviePlayer.value, 'play', config.plugins.iptvplayer.defaultSH4MoviePlayer.value))
            play.append((_('Play with [%s] player') % config.plugins.iptvplayer.alternativeSH4MoviePlayer.value, 'play', config.plugins.iptvplayer.alternativeSH4MoviePlayer.value))
        elif 'mipsel' == config.plugins.iptvplayer.plarform.value:
            play = []
            play.append((_('Play with [%s] player') % config.plugins.iptvplayer.defaultMIPSELMoviePlayer.value, 'play', config.plugins.iptvplayer.defaultMIPSELMoviePlayer.value))
            play.append((_('Play with [%s] player') % config.plugins.iptvplayer.alternativeMIPSELMoviePlayer.value, 'play', config.plugins.iptvplayer.alternativeMIPSELMoviePlayer.value))   
        elif 'i686' == config.plugins.iptvplayer.plarform.value:
            play = []
            play.append((_('Play with [%s] player') % config.plugins.iptvplayer.defaultI686MoviePlayer.value, 'play', config.plugins.iptvplayer.defaultI686MoviePlayer.value))
            play.append((_('Play with [%s] player') % config.plugins.iptvplayer.alternativeI686MoviePlayer.value, 'play', config.plugins.iptvplayer.alternativeI686MoviePlayer.value))             
        else:
            if config.plugins.iptvplayer.NaszPlayer.value == "mini":
                player = 'mini'
            else:
                player = 'standard'
            play = ((_("Play file"), 'play', player),)
        
        cont   = ((_('Continue downloading'), 'continue'),)
        retry  = ((_('Download again'), 'retry'),)
        stop   = ((_('Stop downloading'), 'stop'),)
        remove = ((_('Remove file'), 'remove'),)
        delet  = ((_('Remove item'), 'delet'),)
        move   = ((_('Promote item'), 'move'),)
            
        options = []
        item = self.getSelItem()
        if item != None:
            if DMHelper.STS.DOWNLOADED == item.status:
                options.extend(play)
                options.extend(remove)
                options.extend(retry)
            elif DMHelper.STS.INTERRUPTED == item.status:
                options.extend(play)
                #options.extend(cont)
                options.extend(retry)
                options.extend(remove)
            elif DMHelper.STS.DOWNLOADING == item.status:
                options.extend(play)
                options.extend(stop)
            elif DMHelper.STS.WAITING == item.status:
                options.extend(move)
                options.extend(delet)
            elif DMHelper.STS.ERROR == item.status:
                options.extend(retry)
                options.extend(remove)
            
            self.session.openWithCallback(self.makeActionOnDownloadItem, ChoiceBox, title=_("Select action"), list=options)
        
        return
        
    def makeActionOnDownloadItem(self, ret):
        item = self.getSelItem()
        if None != ret and None != item:
            printDBG("makeActionOnDownloadItem " + ret[1] + (" for downloadIdx[%d]" % item.downloadIdx) )
            if ret[1] == "play":
                # when we watch we no need update sts
                self.DM.setUpdateProgress(False)
                player = ret[2]
                if "mini" == player:
                    self.session.openWithCallback(self.leaveMoviePlayer, IPTVMiniMoviePlayer, item.fileName, item.fileName)
                elif "exteplayer" == player:
                    self.session.openWithCallback(self.leaveMoviePlayer, IPTVExtMoviePlayer, item.fileName, item.fileName, None, 'eplayer')
                elif "extgstplayer" == player:
                    self.session.openWithCallback(self.leaveMoviePlayer, IPTVExtMoviePlayer, item.fileName, item.fileName, None, 'gstplayer')
                else:
                    self.session.openWithCallback(self.leaveMoviePlayer, IPTVStandardMoviePlayer, item.fileName, item.fileName)
            elif ret[1] == "continue":
                self.DM.continueDownloadItem(item.downloadIdx)
            elif ret[1] == "retry":
                self.DM.retryDownloadItem(item.downloadIdx)
            elif ret[1] == "stop":
                self.DM.stopDownloadItem(item.downloadIdx)
            elif ret[1] == "remove":
                self.DM.removeDownloadItem(item.downloadIdx)
            elif ret[1] == "delet":
                self.DM.deleteDownloadItem(item.downloadIdx)
            elif ret[1] == "move":
                self.DM.moveToTopDownloadItem(item.downloadIdx)   
 
    def getSelIndex(self):
        currSelIndex = self["list"].getCurrentIndex()
        return currSelIndex

    def getSelItem(self):
        currSelIndex = self["list"].getCurrentIndex()
        if len(self.currList) <= currSelIndex:
            printDBG("ERROR: getSelItem there is no item with index: %d, listOfItems.len: %d" % (currSelIndex, len(self.currList)))
            return None
        return self.currList[currSelIndex]
        
    def getSelectedItem(self):
        sel = None
        try:
            sel = self["list"].l.getCurrentSelection()[0]
        except:return None
        return sel
        
    def onStart(self):
        if self.started == 0:
            # pobierz liste
            self.started = 1
        return

    def reloadList(self):
        global gIPTVDM_listChanged
        if True == gIPTVDM_listChanged:
            printDBG("IPTV_DM_UI reloadList")
            self["list"].hide()
            gIPTVDM_listChanged = False
            # get current List from api
            self.currList = self.DM.getList()
            self["list"].setList([ (x,) for x in self.currList])
            self["list"].show()
    #end reloadList
            

    def hideWindow(self):
        self.visible = False
        self.hide()

    def showWindow(self):
        self.visible = True
        self.show()          

    def Error(self, error = None):
        pass
        
    def __event(self, ev):
        pass
#class IPTVPlayerWidget