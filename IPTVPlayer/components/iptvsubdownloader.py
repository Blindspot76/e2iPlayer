# -*- coding: utf-8 -*-
#

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, IsValidFileName, GetTmpDir, GetSubtitlesDir, GetIconDir
from Plugins.Extensions.IPTVPlayer.tools.iptvfavourites import IPTVFavourites
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CFavItem, CDisplayListItem
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Plugins.Extensions.IPTVPlayer.components.iptvlist import IPTVMainNavigatorList
from Plugins.Extensions.IPTVPlayer.components.cover import Cover3
from Plugins.Extensions.IPTVPlayer.libs.pCommon import CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.subproviders.opensubtitlesorg import OpenSubOrgProvider
from Components.Language import language
from Components.config import config
###################################################

###################################################
# FOREIGN import
###################################################
from enigma import getDesktop, gRGB
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.Label import Label
from Components.ActionMap import ActionMap
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction
from Screens.VirtualKeyBoard import VirtualKeyBoard
###################################################


class IPTVSubDownloaderWidget(Screen):
    sz_w = getDesktop(0).size().width() - 190
    sz_h = getDesktop(0).size().height() - 195
    if sz_h < 500: sz_h += 4
    skin = """
        <screen name="IPTVSubDownloaderWidget" position="center,center" title="%s" size="%d,%d">
         <widget name="icon_red"    position="5,9"   zPosition="4" size="30,30" transparent="1" alphatest="on" />
         <widget name="icon_yellow" position="180,9" zPosition="4" size="30,30" transparent="1" alphatest="on" />
         <widget name="icon_green"  position="355,9" zPosition="4" size="30,30" transparent="1" alphatest="on" />
         
         <widget name="label_red"     position="45,9"  size="175,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
         <widget name="label_yellow"  position="220,9" size="175,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
         <widget name="label_green"   position="395,9" size="175,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
         
         <widget name="list"  position="5,80"  zPosition="2" size="%d,%d" scrollbarMode="showOnDemand" transparent="1"  backgroundColor="#00000000" />
         <widget name="title" position="5,47"  zPosition="1" size="%d,23" font="Regular;20"            transparent="1"  backgroundColor="#00000000"/>
         
         <widget name="console"      position="10,%d"   zPosition="2" size="%d,160" valign="center" halign="center"   font="Regular;24" transparent="0" foregroundColor="white" backgroundColor="black"/>
        </screen>""" %(
            _("Subtitles downloader"),
            sz_w, sz_h, # size
            sz_w - 10, sz_h - 105, # size list
            sz_w - 135, # size title
            (sz_h - 160)/2, sz_w - 20, # console
            )
            
    def __init__(self, session, params={}):
        # params: vk_title, movie_title
        self.session = session
        Screen.__init__(self, session)
        
        self.params = params
        self.params['login']    = config.plugins.iptvplayer.opensuborg_login.value
        self.params['password'] = config.plugins.iptvplayer.opensuborg_password.value
        
        self.onShown.append(self.onStart)
        self.onClose.append(self.__onClose)
        
        self.subProvider = OpenSubOrgProvider()
        
        self["title"]         = Label(" ")
        self["console"]       = Label(" ")
        
        self["label_red"]     = Label(_("Cancel"))
        self["label_yellow"]  = Label(_("Move group"))
        self["label_green"]   = Label(_("Apply"))
        
        self["icon_red"]     = Cover3()
        self["icon_yellow"]  = Cover3()
        self["icon_green"]   = Cover3()
        
        self["list"] = IPTVMainNavigatorList()
        self["list"].connectSelChanged(self.onSelectionChanged)
        
        self["actions"] = ActionMap(["ColorActions", "SetupActions", "WizardActions", "ListboxActions"],
            {
                "cancel": self.keyExit,
                "ok"    : self.keyOK,
                "red"   : self.keyRed,
                "yellow": self.keyYellow,
                "green" : self.keyGreen,
            }, -2)
        
        self.iconPixmap = {}
        for icon in ['red', 'yellow', 'green']:
            self.iconPixmap[icon] = LoadPixmap(GetIconDir(icon+'.png'))
            
        self.movieTitle = ''
        self.stackList  = []
        self.stackItems = []
        
        try:
            self.defaultLanguage = language.getActiveLanguage().split('_')[0]
        except:
            self.defaultLanguage = 'en'
    
        self.listMode = False
        self.downloadedSubFilePath = ''
        self.loginPassed = False
        
    def __onClose(self):
        self["list"].disconnectSelChanged(self.onSelectionChanged)
        self.subProvider.terminate()
        
    def loadIcons(self):
        try:
            for icon in self.iconPixmap:
                self['icon_'+icon].setPixmap(self.iconPixmap[icon])
        except: printExc()
        
    def hideButtons(self, buttons=['red', 'yellow', 'green']):
        try:
            for button in buttons:
                self['icon_'+button].hide()
                self['label_'+button].hide()
        except: printExc()
        
    def showButtons(self, buttons=['red', 'yellow', 'green']):
        try:
            for button in buttons:
                self['icon_'+button].show()
                self['label_'+button].show()
        except: printExc()
    
    def onStart(self):
        self.onShown.remove(self.onStart)
        self.setTitle( _("Subtitles provider: %s") % self.subProvider.getName() )
        self.loadIcons()
        self.doLogin()
        
    def setListMode(self, sts=False):
        if False == sts:
            self['list'].hide()
            self["title"].hide()
            self.hideButtons()
            self.showButtons(['red'])
        else:
            self["console"].hide()
            self["console"].setText(" ")
            
        self.listMode = sts
            
    def doLogin(self):
        self.loginPassed = False
        self.setListMode(False)
        if '' != self.params.get('login', ''):
            user, password = self.params.get('login', ''), self.params.get('password', '')
            self["console"].setText(_('Login user "%s" into %s') % (self.params.get('login', ''), self.subProvider.getName()))
        else: 
            user, password = '', ''
            self["console"].setText(_('Request token from %s') % self.subProvider.getName())
        self["console"].show()
        
        self.subProvider.doLogin(self.doLoginCallback, user, password, self.defaultLanguage)
        
    def doLoginCallback(self, sts):
        if not sts:
            sts = self.subProvider.getLastApiError()
            self["console"].setText( _('Error occurs.\n[%s]') % (sts['message']) )
        else:
            self.loginPassed = True
            self.session.openWithCallback(self.getMovieTitleCallBack, VirtualKeyBoard, title=self.params.get('vk_title', _("Confirm title of the movie")), text=CParsingHelper.getNormalizeStr( self.params.get('movie_title', '') ))
        
        
    def getMovieTitleCallBack(self, title):
        if isinstance(title, basestring): 
            self.movieTitle = title
            self.doSearchMovie()
        else:
            self.close(None)
    
    def doSearchMovie(self):
        self.setListMode(False)
        self.stackItems = []
        self.stackList  = []
        self["console"].setText(_('Search for movie "%s"') % self.movieTitle)
        self["console"].show()
        self.subProvider.doSearchMovie(self.doSearchMovieCallback, self.movieTitle)
        
    def doSearchMovieCallback(self, sts, data):
        if not sts:
            sts = self.subProvider.getLastApiError()
            self["console"].setText( _('Error occurs.\n[%s]') % (sts['message']) )
        elif len(data):
            self.stackList.append({'type':'movie', 'list':data})
            self.displayList()
        else:
            self["console"].setText(_('Movie "%s" has not been found.') % self.movieTitle)
            
    def doGetLanguageForSubtitle(self):
        self.setListMode(False)
        self["console"].setText(_('Get supported languages list.'))
        self["console"].show()
        self.subProvider.doGetLanguages(self.doGetLanguageForSubtitleCallback, self.defaultLanguage)
        
    def doGetLanguageForSubtitleCallback(self, sts, data):
        if not sts:
            sts = self.subProvider.getLastApiError()
            self["console"].setText( _('Error occurs.\n[%s]') % (sts['message']) )
        elif len(data):
            self.stackList.append({'type':'lang', 'list':data})
            self.displayList()
        else:
            self["console"].setText(_('An unknown error has occurred.'))
            
    def doSearchSubtitle(self, item, lang):
        self.setListMode(False)
        self["console"].setText(_('Search for subitile for "%s"') % item.name)
        self["console"].show()
        self.subProvider.doSearchSubtitle(self.doSearchSubtitleCallback, item.privateData, lang)
        
    def doSearchSubtitleCallback(self, sts, data):
        if not sts:
            sts = self.subProvider.getLastApiError()
            self["console"].setText( _('Error occurs.\n[%s]') % (sts['message']) )
        elif len(data):
            self.stackList.append({'type':'sub', 'list':data})
            self.displayList()
        else:
            self["console"].setText(_('Subtitles not found.'))
            
    def doDownloadSubtitle(self, item):
        self.setListMode(False)
        self["console"].setText(_('Download subtitle "%s"') % item.name)
        self["console"].show()
        tmpDir = GetTmpDir()
        subDir = GetSubtitlesDir() 
        self.subProvider.doDowanloadSubtitle(self.doDownloadSubtitleCallback, item.privateData, tmpDir, subDir)
        
    def doDownloadSubtitleCallback(self, sts, fileName):
        if not sts:
            sts = self.subProvider.getLastApiError()
            self["console"].setText( _('Error occurs.\n[%s]') % (sts['message']) )
        elif len(fileName) > 0:
            self["console"].setText(_('Subtitles downloaded successfully. [%s]') % fileName)
            self.downloadedSubFilePath = fileName
            self.showButtons(['green'])
        else:
            self["console"].setText(_('An unknown error has occurred.'))

    def displayList(self, activeIdx=0):
        list = []
        tmpList = self.stackList[-1]['list']
        type    = self.stackList[-1]['type']
        
        if type == 'movie':
            self["title"].setText(_("Select movie"))
        elif type == "lang":
            self["title"].setText(_("Select language"))
        elif type == "sub":
            self["title"].setText(_("Select subtitles to download"))
        
        self["title"].show()
        
        for item in tmpList:
            dItem = CDisplayListItem(name = clean_html(item['title']), type=CDisplayListItem.TYPE_CATEGORY)
            dItem.privateData = item['private_data']
            list.append( (dItem,) )
        self["list"].setList(list)
        self["list"].show()
        try: self["list"].moveToIndex(activeIdx)
        except: pass
        
        self.setListMode(True)
        
    def onSelectionChanged(self):
        pass
        
    def keyExit(self):
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>> len(self.stackList)[%d] self.listMode[%r]" % (len(self.stackList), self.listMode))
        if False == self.listMode:
            self.subProvider.cancelRequest()
            self.setListMode(False)
            if len(self.stackItems):
                activeIdx = self.stackItems[-1]['idx']
                del self.stackItems[-1]
                self.displayList(activeIdx)
                return
            elif self.loginPassed:
                self.doLoginCallback(True)
                return
        elif 1 < len(self.stackList):
            activeIdx = self.stackItems[-1]['idx']
            del self.stackItems[-1]
            del self.stackList[-1]
            self.displayList(activeIdx)
            return
        elif self.loginPassed:
            self.doLoginCallback(True)
            return
        self.close(None)
            
    def keyOK(self):
        if False == self.listMode: return
        idx, item = self.getSelectedItem()
        if None != item:
            type = self.stackList[-1]['type']
            self.stackItems.append({'item':item, 'idx':idx, 'type':type})
            if type == 'movie':
                self.doGetLanguageForSubtitle()
            elif type == 'lang':
                self.doSearchSubtitle(self.stackItems[-2]['item'], item.privateData)
            elif type == 'sub':
                self.doDownloadSubtitle(item)
            else:
                printExc(type)
            
    def keyRed(self):
        self.close(None)
    
    def keyYellow(self):
        pass
        
    def keyGreen(self):
        try: 
            if self["icon_green"].visible:
                track = {'title':'', 'lang':'', 'path':self.downloadedSubFilePath}
                for item in self.stackItems:
                    printDBG(">>>>>>>>>> item[%s]" % item)
                    type = item['type']
                    data = item['item']
                    if type == 'lang':
                        track['lang'] = data.privateData.get('SubLanguageID', '')
                    elif type == 'sub':
                        track['title'] = data.name
                        track['id']    = data.privateData.get('IDSubtitle', '')
                self.close(track)
        except: printExc()
    
    def getSelectedItem(self):
        try: idx = self["list"].getCurrentIndex()
        except: idx = 0
        sel = None
        try: 
            if self["list"].visible:
                sel = self["list"].l.getCurrentSelection()[0]
                if None != sel:
                    return idx, sel
        except: 
            printExc()
            sel = None
        return -1, None

'''
    obj = OpenSubOrg()
    sts = obj.logIn('iptvplayer', '3xwg4kyx')
    printDBG(">>>>>>>>> login status: [%s]" % sts)
    sts, data = obj.searchMoviesOnIMDB('Back to the Future')
    printDBG(">>>>>>>>> searchMoviesOnIMDB status: [%s] data[%s]" % (sts, data))
    sts, data = obj.searchSubtitlesByIMDbID(data[0]['id'], 'pol')
    printDBG(">>>>>>>>> searchSubtitlesByIMDbID status: [%s] data[%s]" % (sts, data))
'''
    