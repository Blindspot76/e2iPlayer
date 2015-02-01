# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import time
import random
try:    import simplejson as json
except: import json


###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################

###################################################

###################################################
# Config options for HOST
###################################################
def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'Anime-Odcinki.pl'

class AnimeOdcinki(CBaseHostClass):
    MAINURL  = 'http://www.anime-odcinki.pl/'
    SEARCH_URL = MAINURL + 'infusions/video/search.php?find='
    MAIN_CAT_TAB = [{ 'category':'list_letters',   'title':'Lista anime',        'url':'Manga/viewpage.php?page_id=4'       },
                    { 'category':'list_letters',   'title':'Lista filmów',       'url':'viewpage.php?page_id=1869'          },
                    { 'category':'list_items',     'title':'Ostation dodane',    'url':'infusions/video/recent_videos.php'  },
                    { 'category':'list_items',     'title':'Najwyżej ocenione',  'url':'infusions/video/top_rated.php'      },
                    { 'category':'list_items',     'title':'Popularne odcinki',  'url':'infusions/video/popular_videos.php' },
                    { 'category':'Wyszukaj',       'title':'Wyszukaj'             },
                    { 'category':'Historia wyszukiwania', 'title':'Historia wyszukiwania'} ]
                    
    
    def __init__(self):
        printDBG("AnimeOdcinki.__init__")
        CBaseHostClass.__init__(self, {'history':'AnimeOdcinki.com'})
            
    def _checkNexPage(self, data):
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagenav">', '</ul>', False)[1]
        if 'Go to next page' in data and '<a href=' in data:
            return True
        else:
            return False
            
    def _resolveUrl(self, url, currPath=''):
        if not url.startswith('http') and '' != url:
            if '' == currPath:
                return AnimeOdcinki.MAINURL + url
            else:
                return currPath + url
        else:
            return url
            
    def listsTab(self, tab, cItem):
        printDBG("AnimeOdcinki.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
                
    def listsLetters(self, cItem, category):
        printDBG('AnimeOdcinki.listsLetters start')
        url = AnimeOdcinki.MAINURL + cItem['url']
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="entry">', '</table>', False)[1]
            data = re.findall('<a href="([^"]+?)"><strong>([^<])</strong></a>', data)
            for item in data:
                params = dict(cItem)
                params.update({'title':item[1], 'url':item[0], 'category':category})
                self.addDir(params)
                
    def listsAnimes(self, cItem, category):
        printDBG('AnimeOdcinki.listsAnimes start')
        url = AnimeOdcinki.MAINURL + cItem['url']
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul><li class="lista">', '</div>', False)[1]
            data = re.findall('<a href="([^"]+?)"[^>]*?>([^<]+?)</a>', data)
            for item in data:
                params = dict(cItem)
                params.update({'title':item[1], 'url':item[0], 'category':category})
                self.addDir(params)
                
    def listEpisodes(self, cItem):
        printDBG('AnimeOdcinki.listEpisodes start')
        url = self._resolveUrl(cItem['url'])
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, "<div class='main-body floatfix'>", "<a id='comments'", False)[1]
            icon = self._resolveUrl( self.cm.ph.getSearchGroups(data, """src=['"]([^"^']+?\.jpg)['"]""")[0] )
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<thead>', '<!', False)[1])
            trailer = self.cm.ph.getSearchGroups(data, """href=['"](http[^"^']+?youtu[^"^']+?)['"]""")[0]
            if '' != trailer:
                params = dict(cItem)
                params.update({'title':_('Zwiastun'), 'url':trailer, 'desc':desc, 'icon':icon})
                self.addVideo(params)
            #data = self.cm.ph.getDataBeetwenMarkers(data, 'w:', '</div>', False)[1]
            data = re.findall("""<a href=['"]([^"^']+?)['"][^>]*?>([^<]+?)<""", data)
            for item in data:
                if '' != item[1] and 'anime-odcinki.pl' in self._resolveUrl(item[0]):
                    params = dict(cItem)
                    params.update({'title':item[1], 'url':item[0], 'desc':desc, 'icon':icon})
                    self.addVideo(params)
                    
    def listItems(self, cItem):
        printDBG('AnimeOdcinki.listItems start')     
        page     = cItem.get('page', 0)
        url = self._resolveUrl(cItem['url']) + '?rowstart=%d' % (page * 20) 
        currPath = url[:url.rfind('/')] + '/'
        sts, data = self.cm.getPage(url)
        if sts:
            try: pagesNum = int(self.cm.ph.getSearchGroups(data, "Strona[^;]+?;([0-9]+?):")[0])-1
            except: pagesNum = 0 
            data = self.cm.ph.getDataBeetwenMarkers(data, '</tr></table><table cellpadding', "class='main-footer-top", True)[1]
            data = data.split('</tr></table>')
            if len(data): del data[0]
            if len(data): del data[-1]
            for item in data:
                params = dict(cItem)
                tmp = self.cm.ph.getSearchGroups(item, """<a href=["']([^'^"]+?)["']>([^<]+?)</a>""", 2)
                if '' != tmp[0] and '' != tmp[1]:                
                    icon =  self._resolveUrl(self.cm.ph.getSearchGroups(item, """src=['"]([^"^']+?)['"]""")[0], currPath)
                    desc = self.cleanHtmlStr(item)
                    params.update({'title':tmp[1], 'url':self._resolveUrl(tmp[0], currPath), 'icon':icon, 'desc':desc})
                    self.addVideo(params)
            if pagesNum > page:
                params = dict(cItem)
                params.update({'title':'Następna strona', 'page':page+1})
                self.addDir(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnimeOdcinki.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        url = AnimeOdcinki.SEARCH_URL + searchPattern.replace(' ', '+')
        currPath = url[:url.rfind('/')] + '/'
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, "value='Find Video'></form>", "class='main-footer-top")[1]
            data = data.split("<table cellpadding='0'")
            if len(data): del data[0]
            if len(data): data[-1] += '>'
            for item in data:
                params = dict(cItem)
                url = self.cm.ph.getSearchGroups(item, """<a href=["']([^'^"]+?)["']""")[0]
                title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, "<strong>", "</strong>")[1])
                if '' != url and '' != title:                
                    icon =  self._resolveUrl(self.cm.ph.getSearchGroups(item, """src=['"]([^"^']+?)['"]""")[0], currPath)
                    desc = self.cleanHtmlStr('<'+item)
                    params.update({'title':title, 'url':self._resolveUrl(url, currPath), 'icon':icon, 'desc':desc})
                    self.addVideo(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("AnimeOdcinki.getLinksForVideo [%s]" % cItem['url'])
        if len(cItem.get('url_cache', [])):
            return cItem['url_cache']
        urlTab = []
        url = self._resolveUrl(cItem['url'])
        if 'anime-odcinki.pl' in url:
            sts, data = self.cm.getPage(url)
            if sts:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="switcher-panel"></div>', "<a id='comments'")[1]
                players = data.split('<div id="player')
                del players[0]
                for player in players:
                    playerUrl = self.cm.ph.getSearchGroups(player, """src=['"]([^"^']+?)['"]""")[0]
                    if '' != playerUrl:
                        tmpTab = self.up.getVideoLinkExt(playerUrl)
                        urlTab.extend(tmpTab)
        else:
            urlTab = self.up.getVideoLinkExt(url)
        if len(urlTab):
            cItem['url_cache'] = urlTab
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('AnimeOdcinki.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "AnimeOdcinki.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        return
        if None == name:
            self.listsTab(AnimeOdcinki.MAIN_CAT_TAB, {'name':'category'})
    #LIST LETTERS
        elif 'list_letters' == category:
            self.listsLetters(self.currItem, 'anime_list')
    #FILMS LETTERS
        elif 'anime_list' == category:
            self.listsAnimes(self.currItem, 'episodes_list')
    #LIST EPISODES
        elif 'episodes_list' == category:
            self.listEpisodes(self.currItem)
    #LIST ITEMS
        elif 'list_items' == category:
            self.listItems(self.currItem)
    #WYSZUKAJ
        elif category in ["Wyszukaj", "search_next_page"]:
            self.listSearchResult(self.currItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
        else:
            printExc()

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AnimeOdcinki(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('animeodcinkilogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append(("Items", "items"))
        #searchTypesOptions.append(("Channel", "channel"))
    
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if cItem['type'] == 'category':
                if cItem['title'] == 'Wyszukaj':
                    type = CDisplayListItem.TYPE_SEARCH
                    possibleTypesOfSearch = searchTypesOptions
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  cItem.get('title', '')
            description =  clean_html(cItem.get('desc', '')) + clean_html(cItem.get('plot', ''))
            icon        =  cItem.get('icon', '')
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
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
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
