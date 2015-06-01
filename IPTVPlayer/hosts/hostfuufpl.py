# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetLogoDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
try:    import json
except: import simplejson as json
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
config.plugins.iptvplayer.fuufpl_sort = ConfigSelection(default = "newest", choices = [("newest", _("newest")), ("year", _("year"))])
   
def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("SORT"), config.plugins.iptvplayer.fuufpl_sort))
    return optionList
###################################################

def gettytul():
    return 'fuuf.pl'

class FuufPL(CBaseHostClass):
    MAIN_URL   = 'http://fuuf.pl/'
    SRCH_URL   = MAIN_URL + 'XML?act=search_movie'
    MAIN_CAT_TAB = [{'category':'categories',            'title': 'Kategorie',     'icon':''},
                    {'category':'search',                'title': _('Search'), 'search_item':True},
                    {'category':'search_history',        'title': _('Search history')} ]
    
    def __init__(self):
        printDBG("FuufPL.__init__")
        CBaseHostClass.__init__(self, {'history':'fuufpl', 'cookie':'fuufpl.cookie'})
        self.cacheFilters = []
        self.cacheSeries = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        return url

    def listsTab(self, tab, cItem):
        printDBG("FuufPL.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)

    def listCategories(self, cItem, category):
        printDBG("FuufPL.listCategories")
        sts, data = self.cm.getPage(FuufPL.MAIN_URL)
        if not sts: return
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'aria-labelledby="menu_select">', '</ul>', False)
        if not sts: return
        data = data.split('</li>')
        if len(data): del data[-1]
        
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            url    = url[0:url.rfind('/')]
            title  = self.cleanHtmlStr( item )
            
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'category':category} )
                self.addDir(params)
        
    def listVideosFromCategory(self, cItem):
        printDBG("FuufPL.listVideosFromCategory")
        page = cItem.get('page', 1)
        url  = cItem['url'] + "{0},{1}.html".format(page, config.plugins.iptvplayer.fuufpl_sort.value)
        
        sts, data = self.cm.getPage(FuufPL.MAIN_URL)
        if not sts: return
        
        if '"Następna"' in data: nextPage = True
        else: nextPage = False
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="col-md-2" style="margin-bottom: 35px;">', '<script>', False)
        if not sts: return
        
        data = data.split('<div class="col-md-2" style="margin-bottom: 35px;">')
        if len(data): del data[0]
        
        for item in data:
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            if '' == title: title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   =  ''
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'desc':desc, 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
                
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Następna strona'), 'page':page+1} )
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("FuufPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        post_data = {'q':searchPattern}
        sts, data = self.cm.getPage(FuufPL.SRCH_URL, {}, post_data)
        if not sts: return
        
        try:
            data = byteify( json.loads(data) )
            for item in data:
                url   = item['url']
                title = self.cleanHtmlStr( item['name'] )
                icon  = self.cm.ph.getSearchGroups(item['name'], 'src="([^"]+?)"')[0]
                
                if '' != url and '' != title:
                    params = dict(cItem)
                    params.update( {'title':title, 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon)} )
                    self.addVideo(params)
        except: 
            printExc()
            SetIPTVPlayerLastHostError(_("Parsing search result failed."))
        
    def getArticleContent(self, cItem):
        printDBG("FuufPL.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        title = self.cm.ph.getSearchGroups(data, 'title" content="([^"]+?)"')[0]
        icon = self.cm.ph.getSearchGroups(data, 'image" content="([^"]+?)"')[0]
        desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<small itemprop="description">', '</small>', False)[1] )
        
        return [{'title':title, 'text':desc, 'images':[]}]
    
    def getLinksForVideo(self, cItem):
        printDBG("FuufPL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        http_params = {'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIE_FILE}
        sts, data = self.cm.getPage(self.MAIN_URL, http_params)
        if not sts: return urlTab
        
        http_params.update({'load_cookie': True})
        sts, data = self.cm.getPage(cItem['url'], http_params)
        if not sts: return urlTab
        
        try:
            PHPSESSID = self.cm.getCookieItem(self.COOKIE_FILE, 'PHPSESSID')
        except:
            printExc()
            SetIPTVPlayerLastHostError(_("Not valid cookie: [%s]") % self.COOKIE_FILE)
            return urlTab
        
        url = self.cm.ph.getSearchGroups(data, 'file: "(http[^"]+?)"')[0]
        if '' == url:  return urlTab
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> url[%s]" % url)
        
        retUrl = strwithmeta( url )
        retUrl.meta['Referer'] = 'http://static.fuuf.pl/player/jwplayer.flash.swf'
        retUrl.meta['Cookie']  = "PHPSESSID={0}".format(PHPSESSID)
       
        urlTab.append({'name':'fuuf.pl', 'url':retUrl})
            
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('FuufPL.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "FuufPL.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

    #MAIN MENU
        if None == name:
            self.listsTab(FuufPL.MAIN_CAT_TAB, {'name':'category'})
    #CATEGORIES
        elif 'categories' == category:
            self.listCategories(self.currItem, 'list_videos')
    #LIST_VIDEOS
        elif 'list_videos' == category:
            self.listVideosFromCategory(self.currItem)
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
        CHostBase.__init__(self, FuufPL(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('fuufpllogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title  = item.get('title', '')
            text   = item.get('text', '')
            images = item.get("images", [])
            retlist.append( ArticleContent(title = title, text = text, images =  images) )
        return RetHost(RetHost.OK, value = retlist)
    # end getArticleContent
    
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
    
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
