# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/self.HOSTs/ @ 419 - Wersja 636

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, remove_html_markup, CSelOneLink, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
import re
from urllib import unquote_plus
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
    return 'Anime-Shinden'

#ToDo:
#  Obsługa playlist

class AnimeShinden(CBaseHostClass):
    MAINURL = 'http://www.anime-shinden.info'
    SERVICE_MENU_TABLE = {
        1: "Lista anime (alfabetycznie)",
        2: "Lista anime (wg. gatunku)",
    }
    def __init__(self):
        CBaseHostClass.__init__(self)

    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = { 'name': 'main-menu','category': val, 'title': val, 'icon': ''}
            self.addDir(params)
        
    def listsABCMenu(self, table):
        for i in range(len(table)):
            params = { 'name': 'abc-menu','category': table[i], 'title': table[i], 'icon': ''}
            self.addDir(params)
        
    def listsGenre(self, url):
        sts, data = self.cm.getPage(url)
        if not sts: return
        r = re.compile('<input id=".+?"  type="checkbox" name="genre.." value="(.+?)">').findall(data)
        if len(r)>0:
            for i in range(len(r)):
                params = { 'name': 'genset', 'title': unquote_plus(r[i]), 'page':r[i], 'icon': ''}
                self.addDir(params)
        
    def getAnimeList(self, url):
        sts, data = self.cm.getPage(self.MAINURL+url)
        if not sts: return
        r = re.compile('<dl class="sub-nav">(.+?)</body>', re.DOTALL).findall(data)
        if len(r)>0:
            r2 = re.compile('<a href="'+self.MAINURL+'/(.+?.html)">(.+?) </a>').findall(r[0])
            if len(r2)>0:
                for i in range(len(r2)):
                    value = r2[i]
                    title = self.cm.html_entity_decode(value[1])
                    params = { 'name': 'episodelist', 'title': title, 'page': value[0], 'icon': ''}
                    self.addDir(params)

    def getEpisodeList(self, url):
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '><div id="news-id', '</td>', False)[1]
            data = re.findall('<a href="[^"]+?(/[^"]+?.html)"[^>]*?>(.+?)</a>', data)
            for item in data:
                if '<!--' not in item[1]:
                    params = { 'title': self.cleanHtmlStr(item[1]), 'page': 'http:' + item[0], 'icon': ''}
                    self.addVideo(params)

    def getLinkParts(self,data):
        valTab = []
        src = re.compile("flashvars=.+?hd\.file=(.+?)&").findall(data)
        if len(src) < 1:
            src = re.compile('flashvars="streamer=(.+?)"').findall(data)
        if len(src) < 1:
            src = re.compile('src="(.+?)"').findall(data)
        for i in range(len(src)):
            if len(src) > 1:
                prefix = 'Część '+ str(i+1) + " "
            else:
                prefix = ''
            if 1 == self.up.checkHostSupport(src[i]):
                valTab.append({'name': ( prefix + self.up.getHostName(src[i]) ), 'url': src[i]})
        return valTab

    def getHostingTable(self,url):
        valTab = []
        videoID = ''
        sts, data = self.cm.getPage(url)
        if not sts: return []
        match = re.compile('class="video_tabs".+?>(.+?)</div>\n', re.DOTALL).findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                linkVideos = self.getLinkParts(match[i])
                valTab.extend(linkVideos)
            return valTab
        else:
            printDBG('getHostingTable brak hostingu - nie dodano jeszcze tego wideo. Zapraszamy w innym terminie.')
        return valTab

    '''
    def getVideoPart(self,link):
        if len(link) == 1:
            return link[0][0]
        elif len(link) > 1:
            d = xbmcgui.Dialog()
            item = d.select("Wybierz część", self.cm.getItemTitles(link))
            print str(item)
            if item != -1:
                linkVideo = str(link[item][0])
                log.info("final link: " + linkVideo)
                return linkVideo
        else:
            printDBG('getVideoPart - nie dodano jeszcze tego wideo.')
    '''

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '')
        icon     = self.currItem.get("icon", '')

        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []

        if str(page)=='None' or page=='': page = '0'

    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #LISTA ANIME (Alfabetycznie)
        elif category == self.setTable()[1]:
            self.listsABCMenu(self.cm.makeABCList())
        elif name == 'abc-menu':
            self.getAnimeList('/animelist/index.php?letter=' + category)
    #LISTA ANIME (wg. Gatunku)
        elif category == self.setTable()[2]:
            self.listsGenre(self.MAINURL+'/animelist/index.php')
        elif name == 'genset':
            self.getAnimeList('/animelist/index.php?genre[]=' + page)
    #LISTA ODCINKÓW
        elif name == 'episodelist':
            url = self.MAINURL + '/' + page
            self.getEpisodeList(url)
            
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AnimeShinden(), False)

    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir('animeshindenlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlItems = self.host.getHostingTable(self.host.currList[Index]["page"])
        for item in urlItems:
            retlist.append(CUrlItem(item['name'], item['url'], 1))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        if url != None and url != '':
            ret = self.host.up.getVideoLink( url )
            list = []
            if ret:
                list.append(ret)
            return RetHost(RetHost.OK, value = list)
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    def convertList(self, cList):
        hostList = []
        
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN

            if cItem['type'] == 'category':
                type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                page = cItem.get('page', '')
                if '' != page:
                    hostLinks.append(CUrlItem("Link", page, 1))
                
            title       =  self.host.cleanHtmlStr( cItem.get('title', '') )
            description =  self.host.cleanHtmlStr( cItem.get('plot', '') )
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

