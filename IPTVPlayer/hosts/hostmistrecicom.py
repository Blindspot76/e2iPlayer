# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import unescapeHTML
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
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
    return 'http://www.mistreci.com/'

class MistreciCom(CBaseHostClass):
    MAIN_URL    = 'http://www.mistreci.com/'
    SRCH_URL    = MAIN_URL + 'rezultatet-e-kerkimit/?searchmistreci='
    DEFAULT_ICON_URL = 'http://www.mistreci.com/wp-content/uploads/2015/11/logo.png'
    
    MAIN_CAT_TAB = [{'category':'list_items',     'title': _('Home'),           'url':MAIN_URL,      'icon':DEFAULT_ICON_URL},
                    {'category':'search',         'title': _('Search'),         'search_item':True,  'icon':DEFAULT_ICON_URL},
                    {'category':'search_history', 'title': _('Search history'), 'icon':DEFAULT_ICON_URL} 
                   ]

 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'MistreciCom', 'cookie':'MistreciCom.cookie'})
        
    def _getFullUrl(self, url, series=False):
        if not series:
            mainUrl = self.MAIN_URL
        else:
            mainUrl = self.S_MAIN_URL
        if url.startswith('/'):
            url = url[1:]
        if 0 < len(url) and not url.startswith('http'):
            url = mainUrl + url
        return url
        
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("MistreciCom.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listItems(self, cItem, category='videos'):
        printDBG("MistreciCom.listItems")
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<!-- Video Box Start -->', '<!-- Video Box End -->', False, True)
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if url == '': continue
            title = self.cm.ph.getDataBeetwenMarkers(item, '<h4', '</h4>')[1]
            if title == '': continue
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            desc = ''
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': desc, 'icon':self._getFullUrl(icon)} )
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = self.SRCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(cItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("MistreciCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        videoUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="(http[^"]+?)"', 1, True)[0]
        if '' != videoUrl:
            urlTab = self.up.getVideoLinkExt(videoUrl)
        for idx in range(len(urlTab)):
            urlTab[idx]['need_resolve'] = 0
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
    #MOVIES
        elif category == 'list_items':
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
        CHostBase.__init__(self, MistreciCom(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('mistrecicomlogo.png')])
    
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
