# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import copy
import re
import urllib
import base64
try:    import json
except: import simplejson as json
from datetime import datetime
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://streamcomplet.com/'

class StreamComplet(CBaseHostClass):
    MAIN_URL    = 'http://www.streamcomplet.com/'
    SRCH_URL    = MAIN_URL + '?s='
    DEFAULT_ICON_URL = 'http://streamcomplet.com/wp-content/themes/streaming/logo/logo.png'
    
    MAIN_CAT_TAB = [{'category':'categories',     'title': _('Categories'),     'icon':DEFAULT_ICON_URL, 'filters':{}},
                    {'category':'search',         'title': _('Search'),         'icon':DEFAULT_ICON_URL, 'search_item':True},
                    {'category':'search_history', 'title': _('Search history'), 'icon':DEFAULT_ICON_URL } 
                   ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'StreamComplet', 'cookie':'StreamComplet.cookie'})
        self.cacheFilters = {}
        self.USER_AGENT = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html'}
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def _getFullUrl(self, url):
        mainUrl = self.MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("StreamComplet.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)

    def listCategories(self, cItem, category):
        printDBG("StreamComplet.listCategories")
        sts, data = self.cm.getPage(self.MAIN_URL)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="menu-menu" class="menu">', '</ul>', False)[1]
        
        data = re.compile('<a href="([^"]+?)"[^>]*?>([^<]+?)<').findall(data)
        for item in data:
            params = dict(cItem)
            params.update({'category':category, 'title':item[1].strip(), 'url':self._getFullUrl(item[0])})
            self.addDir(params)
    
    def listItems(self, cItem):
        printDBG("StreamComplet.listItems")
        
        tmp = cItem['url'].split('?')
        url = tmp[0]
        if len(tmp) > 1:
            arg = tmp[1]
        else: arg = ''
        
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%s/' % page
        if '' != arg:
            url += '?' + arg
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        if ('/page/%s/' % (page+1)) in data:
            nextPage = True
        m1 = '<div class="moviefilm">'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '<div class="filmborder">', False)[1]
        data = data.split(m1)
        for item in data:
            params = dict(cItem)
            params = dict(cItem)
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            title = self.cleanHtmlStr( title )
            if title == '': continue
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            desc  = self.cleanHtmlStr( item )
            params.update({'title':title, 'icon':self._getFullUrl(icon), 'desc':desc, 'url':self._getFullUrl(url)})
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':cItem.get('page', 1)+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = self.SRCH_URL + searchPattern
        self.listItems(cItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("StreamComplet.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        params = dict(self.defaultParams)
        header = dict(self.HEADER)
        header['Referer'] = cItem['url']
        params['header'] = header
        
        sts, data = self.cm.getPage(cItem['url'], params)
        if not sts: return []
        
        if 0:
            adminData = self.cm.ph.getDataBeetwenMarkers(data, 'jQuery.ajax({', '});', False)[1]
            adminUrl  = self.cm.ph.getSearchGroups(adminData, "url:'([^']+?)'")[0] 
            adminUrl += '?' + self.cm.ph.getSearchGroups(adminData, "data:'([^']+?)'")[0] 
            
            header = dict(self.HEADER)
            header['X-Requested-With'] = 'XMLHttpRequest'
            header['Referer'] = cItem['url']
            paramsAdmin = dict(self.defaultParams)
            paramsAdmin['header'] = header
            sts, adminData = self.cm.getPage(adminUrl, paramsAdmin)
            printDBG('>>>>>>>>>>>>>> adminData[%s]' % adminData)
            
            projekktor_controlbar={"muted":false,"volume":0.5};
        
        playerUrl = self.cm.ph.getSearchGroups(data, 'src="(http[^"]+?player[^"]+?)"')[0]
        #printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> playerUrl[%s]" % playerUrl)
        
        movieId = self.cm.ph.getSearchGroups(playerUrl+'/', 'f=([0-9]+?)/')[0]
        if movieId != '':
            playerUrl = 'http://m.ok.ru/video/' + movieId
            sts, data = self.cm.getPage(playerUrl, params)
            if not sts: return []
            videoUrl = self.cm.ph.getSearchGroups(data, 'href="(http[^"]+?moviePlaybackRedirect[^"]+?)"')[0].replace('&amp;', '&')
            videoUrl = self.up.decorateUrl(videoUrl, {'User-Agent':self.USER_AGENT})
            return [{'name':'vimeo.me', 'url':videoUrl, 'need_resolve':0}]
        
        playerUrl = playerUrl.replace('&#038;', '&')
        sts, data = self.cm.getPage(playerUrl, params)
        if not sts: return []
        
        videoUrl = self.cm.ph.getSearchGroups(data, """src:[^'^"]+?['"]([^'^"]+?)['"]""")[0]
        if videoUrl == '' or videoUrl == 'vimplevideo.mp4': return []
        
        videoUrl = 'http://media.vimple.me/playeryw.swf/' + videoUrl
        videoUrl = self.up.decorateUrl(videoUrl, {'User-Agent':self.USER_AGENT})
        return [{'name':'vimeo.me', 'url':videoUrl, 'need_resolve':0}]
        
        
        tmp = self.up.getVideoLinkExt(cItem['url'])
        for item in tmp:
            item['need_resolve'] = 0
            urlTab.append(item)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'items')
    #ITEMS
        elif category == 'items':
            self.listItems(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, StreamComplet(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('ustreamtvlogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie  
        
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
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

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
