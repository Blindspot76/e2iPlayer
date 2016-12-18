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
except Exception: import simplejson as json
from datetime import datetime
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, unpackJS, VIDEOMEGA_decryptPlayerParams
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
        CBaseHostClass.__init__(self, {'history':'StreamComplet', 'cookie_type':'MozillaCookieJar', 'cookie':'StreamComplet.cookie'})
        self.cacheFilters = {}
        self.USER_AGENT = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        self.USER_AGENT2 = "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/44.0 (Chrome)"
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
        
        printDBG("============================ 00 ============================")
        printDBG(data)
        printDBG("============================ 00 ============================")
        
        firstPlayerUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="(http[^"]+?player[^"]+?)"')[0].replace('&#038;', '&')
        sts, data = self.cm.getPage(firstPlayerUrl, params)
        if not sts: return []
        
        printDBG("============================ 01 ============================")
        printDBG(data)
        printDBG("============================ 11 ============================")
        
        secondPlayerUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]*?player[^"]+?)"')[0].replace('&#038;', '&')
        if not self.cm.isValidUrl(secondPlayerUrl):
            secondPlayerUrl = self.up.getDomain(firstPlayerUrl, False) + secondPlayerUrl.replace('../', '')
        sts, data = self.cm.getPage(secondPlayerUrl, params)
        if not sts: return []
        
        printDBG("============================ 02 ============================")
        printDBG(data)
        printDBG("============================ 12 ============================")
        
        tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, "eval(", '</script>')
        for tmp in tmpTab:
            tmp2 = unpackJSPlayerParams(tmp, VIDEOMEGA_decryptPlayerParams, 0, r2=True)
            data += tmp2
        data = data.replace('\\"', '"').replace('\\/', '/')
        
        printDBG("============================ 03 ============================")
        printDBG(data)
        printDBG("============================ 13 ============================")
        
        thirdPlayerUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="(http[^"]+?)"')[0]
        
        return self.up.getVideoLinkExt(thirdPlayerUrl)
        
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
