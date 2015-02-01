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
from Plugins.Extensions.IPTVPlayer.components.cover import SimpleAnimatedCover, Cover
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetIconDir, eConnectCallback
from Plugins.Extensions.IPTVPlayer.components.iptvplayer import IPTVStandardMoviePlayer, IPTVMiniMoviePlayer
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import DownloaderCreator
###################################################

###################################################
# FOREIGN import
###################################################
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from enigma import getDesktop
from enigma import eTimer
from Components.config import config
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Label import Label
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
import os
###################################################

class IPTVPicturePlayerWidget(Screen):
    NUM_OF_ICON_FRAMES = 8
    #######################
    #       SIZES
    #######################
    # screen size
    # we do not want borders, so make the screen lager than a desktop
    sz_w = getDesktop(0).size().width() 
    sz_h = getDesktop(0).size().height()
    # percentage
    s_w = 120
    s_h = 120
    # icon
    i_w = 128
    i_h = 128
    # console
    c_w = sz_w
    c_h = 80
    # picture 
    p_w = sz_w-20
    p_h = sz_h-20
    #######################
    #     POSITIONS
    #######################  
    start_y = (sz_h - (i_h + c_h)) / 2 
    # percentage
    s_x = (sz_w - s_w) / 2
    s_y = start_y + (i_h - s_h) / 2
    # icon
    i_x = (sz_w - i_w) / 2
    i_y = start_y
    # console
    c_x = 0
    c_y = i_y + i_h
    # picture 
    p_x = 10
    p_y = 10
    
    printDBG("[IPTVPicturePlayerWidget] desktop size %dx%d" % (sz_w, sz_h) )
    skin = """
        <screen name="IPTVPicturePlayerWidget"  position="center,center" size="%d,%d" title="IPTV Picture Player...">
         <widget name="status"     size="%d,%d"   position="%d,%d"  zPosition="5" valign="center" halign="center"  font="Regular;21" backgroundColor="black" transparent="1" /> #foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"
         <widget name="console"    size="%d,%d"   position="%d,%d"  zPosition="5" valign="center" halign="center"  font="Regular;21" backgroundColor="black" transparent="1" />
         <widget name="icon"       size="%d,%d"   position="%d,%d"  zPosition="4" transparent="1" alphatest="on" />
         <widget name="picture"    size="%d,%d"   position="%d,%d"  zPosition="6" transparent="1" alphatest="on" />
        </screen>""" %( sz_w, sz_h,         # screen
                        s_w, s_h, s_x, s_y, # status
                        c_w, c_h, c_x, c_y, # console
                        i_w, i_h, i_x, i_y, # icon
                        p_w, p_h, p_x, p_y  # picture
                      )
   
    def __init__(self, session, url, pathForRecordings, pictureTitle):
        self.session = session
        Screen.__init__(self, session)
        self.onStartCalled = False
        
        self.recordingPath = pathForRecordings
        try:
            self.filePath = os.path.join(pathForRecordings, '.iptv_buffering.jpg')
        except:
            self.filePath = ''
            printExc()
            
        self.url           = url
        self.pictureTitle  = pictureTitle
       
        self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
        {
            "back": self.back_pressed
        }, -1)     

        self["status"]  = Label()
        self["console"] = Label()
        self["icon"]    = SimpleAnimatedCover()
        self["picture"] = Cover()

        # prepare icon frames path
        frames = []
        for idx in range(1,self.NUM_OF_ICON_FRAMES+1): frames.append( GetIconDir('/buffering/buffering_%d.png' % idx) )
        self["icon"].loadFrames(frames) 
        
        self.inMoviePlayer = False
        self.canRunMoviePlayer = False # used in function updateDisplay, so must be first initialized
        #main Timer
        self.mainTimer = eTimer()
        self.mainTimerEnabled = False
        self.mainTimer_conn = eConnectCallback(self.mainTimer.timeout, self.updateDisplay)
        self.mainTimerInterval = 100 # by default 0,1s
        # download
        self.downloader = DownloaderCreator(self.url)
        
        self.onClose.append(self.__onClose)
        self.onLayoutFinish.append(self.doStart)
        
    #end def __init__(self, session):
    
    def __del__(self):
        printDBG('IPTVPicturePlayerWidget.__del__ --------------------------------------')
        
    def __onClose(self):
        printDBG('IPTVPicturePlayerWidget.__onClose ------------------------------------')
        self.onEnd()
        self.mainTimer_conn = None
        self.mainTimer = None

        self.onClose.remove(self.__onClose)
        self.onLayoutFinish.remove(self.doStart)
 
    def onStart(self):
        '''
            this method is called once like __init__ but in __init__ we cannot display MessageBox
        '''
        self["picture"].hide()
        self["console"].setText(self.pictureTitle)
        self["status"].setText(_("Pobieranie"))
        self._cleanedUp()
        if self.downloader:
            self.downloader.isWorkingCorrectly(self._startDownloader)
        else:
            self.session.openWithCallback(self.close, MessageBox, _("Downloading cannot be started.\n Invalid URI[%s].") % self.url, type = MessageBox.TYPE_ERROR, timeout = 10)

    def _startDownloader(self, sts, reason):
        if sts:
            url,downloaderParams = DMHelper.getDownloaderParamFromUrl(self.url)
            self.downloader.subscribeFor_Finish(self.downloaderEnd)
            self.downloader.start(url, self.filePath, downloaderParams)
            self.setMainTimerSts(True)
        else:
            self.session.openWithCallback(self.close, MessageBox, _("Downloading cannot be started.\n Downloader [%s] not working properly.\n Status[%s]") % (self.downloader.getName(), reason.strip()), type = MessageBox.TYPE_ERROR, timeout = 10 )        
        
    def onEnd(self, withCleanUp=True):
        self.setMainTimerSts(False)
        if self.downloader:
            self.downloader.unsubscribeFor_Finish(self.downloaderEnd)
            downloader = self.downloader
            self.downloader = None
            downloader.terminate()
            downloader = None
        if withCleanUp:
            self._cleanedUp()

    def back_pressed(self):
        self.close()

    def downloaderEnd(self, status):
        if None != self.downloader:
            self.onEnd(False)
            if DMHelper.STS.DOWNLOADED == status:
                self["status"].setText(_("£adowanie"))
                self["picture"].decodeCover(self.filePath, self.decodePictureEnd, ' ')
            else:
                self.session.openWithCallback(self.close, MessageBox, (_("Downloading file [%s] problem.") % self.url) + (" sts[%r]" % status), type=MessageBox.TYPE_ERROR, timeout=10)

    def decodePictureEnd(self, ret={}):
        if None == ret.get('Pixmap', None):
            self.session.openWithCallback(self.close, MessageBox, _("Downloading file [%s] problem.") % self.filePath, type=MessageBox.TYPE_ERROR, timeout=10)        
        else:
            self["status"].hide()
            self["console"].hide()
            self["icon"].hide()
            self["picture"].updatePixmap(ret.get('Pixmap', None), ret.get('FileName', self.filePath))
            self["picture"].show()
            self.setMainTimerSts(False)

    def setMainTimerSts(self, start):
        try:
            if start:
                if not self.mainTimerEnabled:
                    self.mainTimer.start(self.mainTimerInterval)
                    self.mainTimerEnabled = True
                    self.updateDisplay()
            else:
                if self.mainTimerEnabled:
                    self.mainTimer.stop()
                    self.mainTimerEnabled = False
        except:
            printExc("IPTVPicturePlayerWidget.setMainTimerSts status[%r] EXCEPTION" % start)
            
    def updateDisplay(self):
        printDBG("updateDisplay")
        if not self.mainTimerEnabled:
            printDBG("updateDisplay aborted - timer stopped")
            return
        self["icon"].nextFrame()
        return
        
    def _cleanedUp(self):
        if fileExists(self.filePath):
            try: os.remove(self.filePath)
            except: printDBG('Problem with removing old buffering file')
            
    def doStart(self):
        if not self.onStartCalled:
            self.onStartCalled = True
            self.onStart()

#class IPTVPlayerWidget