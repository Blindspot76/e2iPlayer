# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/self.HOSTs/ @ 419 - Wersja 636

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CHostBase, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re, urllib
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, fileExists
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
# None

def GetConfigList():
    optionList = []
    # None
    return optionList
###################################################

def gettytul():
    return 'Kreskóweczki'

class Kreskoweczki:
    MAINURL = 'http://www.kreskoweczki.pl'

    MENU_TAB = {
        1: "Kreskówki alfabetycznie",
        2: "Ostatnio uzupełnione",
        3: "Wyszukaj",
        4: "Historia Wyszukiwania"
    }
    def __init__(self):
        self.cm = pCommon.common()
        self.up = urlparser.urlparser()
        self.history = CSearchHistoryHelper('kreskoweczki')
        
        # temporary data
        self.currList = []
        self.currItem = {}

    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        
    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

    def addDir(self, params):
        params['type'] = 'category'
        self.currList.append(params)
        return
        
    def addVideo(self, params):
        params['type'] = 'video'
        self.currList.append(params)
        return

    def setTable(self):
        return self.MENU_TAB

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = { 'name': 'main-menu','category': val, 'title': val, 'icon': ''}
            self.addDir(params)

    def listsABCMenu(self, table):
        for i in range(len(table)):
            params = { 'name': 'abc-menu','category': table[i], 'title': table[i], 'icon': ''}
            self.addDir(params)

    def showTitles(self, letter):
        query_data = {'url': self.MAINURL, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('showTitles EXCEPTION')
            return
        matchAll = re.compile('<ul class="menu" id="categories_block">(.+?)</ul>', re.DOTALL).findall(data)
        if len(matchAll) > 0:
            match = re.compile('<a href=.(.+?). class=.level0. alt=.(.+?) \(([0-9]+?)\).>').findall(matchAll[1])
            if len(match) > 0:
                for i in range(len(match)):
                    addItem = False
                    title = match[i][1].strip()

                    if letter == '0 - 9' and (ord(title[0]) < 65 or ord(title[0]) > 91): addItem = True
                    if (letter == title[0].upper()): addItem = True
                    if int(match[i][2]) == 0: addItem = False
                    if (addItem):
                        params = { 'name': 'episode', 'title': title, 'page': match[i][0], 'icon': ''}
                        self.addDir(params)

    def showParts(self, url):
        query_data = {'url': url, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('showParts EXCEPTION')
            return

        matchAll = re.compile("<div class='list-videos'>(.+?)<br />", re.DOTALL).findall(data)
        if len(matchAll) > 0:
            match = re.compile("<a href='(.+?)' title='(.+?)'><img src='(.+?)'.+?<dt class='series'>.+?title='(.+?)'>", re.DOTALL).findall(matchAll[0])
            if len(match) > 0:
                for i in range(len(match)):
                    serial = match[i][3]
                    title = '%s - %s' % (serial, match[i][1])
                    link = match[i][0]
                    params = {'title': title, 'page': link, 'icon': match[i][2]}
                    self.addVideo(params)
        match2 = re.compile("class='active'>.+?</a>  <a href='(.+?)'").findall(data)
        printDBG(str(match2))
        if len(match2) > 0:
            params = { 'name': 'nextpage', 'title': 'Następna strona', 'page': match2[0], 'icon': ''}
            self.addDir(params)

    def listsHistory(self):
            list = self.history.getHistoryList()
            for item in list:
                params = { 'name': 'history', 'category': 'Wyszukaj', 'title': item, 'plot': 'Szukaj: "%s"' % item, 'icon': ''}
                self.addDir(params)

    def getVideoUrl(self, url):
        videoUrl = ''
        videosTab = []
        vid = re.compile("kreskowka/(.+?)/").findall(url)
        HEADER = {'Referer' : url}
        query_data = {'url': 'http://www.kreskoweczki.pl/fullscreen/', 'header': HEADER, 'return_data': True}
        postdata = {'v_id' : vid[0]}
        try:
            data = self.cm.getURLRequestData(query_data, postdata)
        except:
            printDBG('getVideoUrl EXCEPTION')
            return videosTab
        matchAll = re.compile("Loader.skipBanners(.+?)Loader.skipBanners", re.DOTALL).findall(data)
        printDBG(str(matchAll))
        if len(matchAll) > 0:
            match = re.compile('Loader.loadFlashFile."(.+?)"').findall(matchAll[0])
            if len(match) > 0:
                videoUrl = match[0]
            else:
                match = re.compile('src="(.+?)"').findall(matchAll[0])
                if len(match) > 0:
                    videoUrl = match[0]
                    
        match = re.search('src="(http[^"]+?)"', videoUrl )
        if match:
            videoUrl = match.group(1)
            
        match = re.search("/embed/proxy[^.]+?.php", videoUrl)
        if match:
            sts,data = self.cm.getPage(videoUrl)
            if sts:
                match = re.search('url: "[^?^"]+?\?url=([^"]+?)"', data)
                if match:
                    url = match.group(1)
                    if url.endswith('.m3u8'):
                        printDBG("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
                        return getDirectM3U8Playlist(url)
        else:
            return self.up.getVideoLinkExt(videoUrl)

        return []

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG( "handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
            if -1 == index:
                # use default value
                self.currItem = { "name": None }
                printDBG( "handleService for first self.category" )
            else:
                self.currItem = self.currList[index]

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '')
        icon     = self.currItem.get("icon", '')

        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []

    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.MENU_TAB)
    #KRESKÓWKI ALFABETYCZNIE
        elif category == self.setTable()[1]:
            self.listsABCMenu(self.cm.makeABCList())
        elif name == 'abc-menu':
            self.showTitles(category)
        elif name == 'episode' or name == 'nextpage':
            self.showParts(page)
    #OSTATNIO UZUPEŁNIONE
        elif category == self.setTable()[2]:
            self.showParts(self.MAINURL)
    #WYSZUKAJ
        elif category == self.setTable()[3]:
            text = searchPattern
            self.showParts(self.MAINURL+"/search/?keywords="+urllib.quote_plus(text))
    #HISTORIA WYSZUKIWANIA
        elif category == self.setTable()[4]:
            self.listsHistory()
    #WRONG WAY
        else:
            printDBG('handleService WRONG WAY')

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Kreskoweczki(), True)

    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('kreskoweczkilogo.png') ])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getVideoUrl(self.host.currList[Index]["page"])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN

            if cItem['type'] == 'category':
                if cItem['title'] == 'Wyszukaj':
                    type = CDisplayListItem.TYPE_SEARCH
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                page = cItem.get('page', '')
                if '' != page:
                    hostLinks.append(CUrlItem("Link", page, 1))
                
            title       =  cItem.get('title', '')
            description =  cItem.get('plot', '')
            icon        =  cItem.get('icon', '')
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon )
            hostList.append(hostItem)

        return hostList
    # end convertList

    def getSearchItemInx(self):
        # Find 'Wyszukaj' item
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'Wyszukaj':
                    return i
        except:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                self.host.history.addHistoryItem( pattern )
                self.searchPattern = pattern
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
        return
