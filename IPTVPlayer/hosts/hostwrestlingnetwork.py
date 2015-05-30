# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.sha1Hash import SHA1
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
from binascii import hexlify
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
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
from Components.config import config, ConfigSelection, getConfigListEntry
###################################################


###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.wrestling_net_sort = ConfigSelection(default = "", choices = [("", _("DEFAULT")), ("views", _("VIEWS")),("date", _("DATE"))])
   
def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("SORT"), config.plugins.iptvplayer.TVN24httpType))
    return optionList
###################################################

def gettytul():
    return 'wrestling-network.net'

class WrestlingNet(CBaseHostClass):
    MAIN_URL   = 'http://wrestling-network.net/'
    BASE_IMAGE = MAIN_URL + 'public/images/'
    
    MAIN_CAT_TAB = [{'category':'latest',   'url':"",                           'title': _("LATEST VIDEOS"),     'icon':''},
                    {'category':'tag',      'url':"tag/show-replay",             'title': _("SHOW REPLAY"),       'icon':''},
                    {'category':'category', 'url':"category/wwe-network",        'title': _("WWE NETWORK"),       'icon':''},
                    {'category':'category', 'url':"category/wwe",                'title': _("WWE"),               'icon':''},
                    {'category':'category', 'url':"category/wwe/wwe-raw",        'title': _("RAW"),               'icon':BASE_IMAGE+'2013/03/348-529x300.jpg'},
                    {'category':'category', 'url':"category/wwe/wwe-smackdown",  'title': _("SMACKDOWN"),         'icon':BASE_IMAGE+'2013/03/347-529x300.jpg'},
                    {'category':'category', 'url':"category/wwe/wwe-nxt",        'title': _("NXT"),               'icon':BASE_IMAGE+'2013/03/3953-529x300.jpg'},
                    {'category':'category', 'url':"category/lucha-underground",  'title': _("LUCHA UNDERGROUND"), 'icon':BASE_IMAGE+'2015/01/lucha_underground-533x300.jpg'},
                    {'category':'category', 'url':"category/njpw",               'title': _("NJPW"),              'icon':BASE_IMAGE+'2015/04/NJPW-copy-554x300.jpg'},
                    {'category':'category', 'url':"category/tna",                'title': _("TNA"),               'icon':BASE_IMAGE+'2015/03/WN-TNA-563x300.jpg'},
                    {'category':'search',                'title':_('Search'), 'search_item':True},
                    {'category':'search_history',        'title':_('Search history')} ]
    
    def __init__(self):
        printDBG("WrestlingNet.__init__")
        CBaseHostClass.__init__(self, {'history':'wrestling-network.net'})
        self.cacheFilters = []
        self.cacheSeries = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        return url

    def listsTab(self, tab, cItem):
        printDBG("WrestlingNet.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)

    def listLatestVideos(self, cItem, category):
        printDBG("WrestlingNet.listLatestVideos")
        self._listVideos(cItem)
        
    def listVideosByTag(self, cItem, category):
        printDBG("WrestlingNet.listVideosByTag")
        self._listVideos(cItem)
        
    def listVideosByCategory(self, cItem, category):
        printDBG("WrestlingNet.listVideosByCategory")
        self._listVideos(cItem)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("WrestlingNet.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        cItem.update({'srch':'?s=' + searchPattern})
        self._listVideos(cItem)
    
    #def _listVideos(self, cItem, m1='class="item', m2='</div></div></div></div><div', sp='class="item'):
    def _listVideos(self, cItem, m1='<div id="post-', m2='end .loop-content', sp='<div id="post-'):
        printDBG("WrestlingNet._listVideos")
        
        page = cItem.get('page', 1)
        url = cItem.get('url', '')
        if page > 1:
            url += '/page/%s' % page
        url += cItem.get('srch', '')
        if '?' in url: url += '&'
        else: url += '?'
        url += 'orderby=' + config.plugins.iptvplayer.wrestling_net_sort.value
        url = self._getFullUrl(url)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        if ('/page/%s?' % (page+1)) in data:
            nextPage = True
        else: nextPage = False
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, True)
        if not sts:
            SetIPTVPlayerLastHostError(_("WrestlingNet._listVideos - no markers [m1][m2] found!"))
            return
        
        data = data.split(sp)
        if len(data): del data[0]
        for item in data:
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            if '' == title: title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   =  self.cleanHtmlStr('<' + item + '>')
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'desc':desc, 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
        
        if nextPage:
            params = params = dict(cItem)
            params.update({'title':_("Następna strona"), 'page':page+1})
            self.addDir(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("WrestlingNet.getLinksForVideo [%s]" % cItem)
        urlTab = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'entry-content', 'video-meta-info', True) #'id="more-'
        if not sts:
            SetIPTVPlayerLastHostError(_("Please visit '%s' from using web-browser form the PC. If links are available please report this problem.\nEmail: samsamsam@o2.pl") % cItem['url'])
            return urlTab
            
        data = data.split('<h2>')
        if len(data): del data[0]
        re_links = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>')
        for item in data:
            type = self.cleanHtmlStr( item.split('</h2>')[0] )
            
            links = re_links.findall(item)
            for link in links:
                urlTab.append({'name':type + ' ' + link[1], 'url':link[0]})
            
        return urlTab
        
    def getResolvedURL(self, url):
        printDBG("WrestlingNet.getResolvedURL [%s]" % url)
        urlTab = []
        sts, data = self.cm.getPage(url)
        if not sts: return urlTab
        
        videoUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
        if not videoUrl:
            videoUrl = self.cm.ph.getSearchGroups(data, "file: '([^']+?)'")[0]
            if '.m3u8' in videoUrl:
                urlTab = getDirectM3U8Playlist(videoUrl, checkExt=True)
            
        urlTab = self.up.getVideoLinkExt( videoUrl )
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('WrestlingNet.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "WrestlingNet.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

    #MAIN MENU
        if None == name:
            self.listsTab(WrestlingNet.MAIN_CAT_TAB, {'name':'category'})
    #LATEST
        elif 'latest' == category:
            self.listLatestVideos(self.currItem, '')
    #TAG
        elif 'tag' == category:
            self.listVideosByTag(self.currItem, '')
    #CATEGORY
        elif 'category' == category:
            self.listVideosByCategory(self.currItem, '')
    #WYSZUKAJ
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, WrestlingNet(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('wrestlingnetworklogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getResolvedURL(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append(("Filmy",  "filmy"))
        #searchTypesOptions.append(("Seriale","seriale"))
        
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if 'category' == cItem['type']:
                if cItem.get('search_item', False):
                    type = CDisplayListItem.TYPE_SEARCH
                    possibleTypesOfSearch = searchTypesOptions
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
            elif 'more' == cItem['type']:
                type = CDisplayListItem.TYPE_MORE
            elif 'audio' == cItem['type']:
                type = CDisplayListItem.TYPE_AUDIO
                
            if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO]:
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  self.host.cleanHtmlStr( cItem.get('title', '') )
            description =  self.host.cleanHtmlStr( cItem.get('desc', '') )
            icon        =  self.host.cleanHtmlStr( cItem.get('icon', '') )
            
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
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
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
