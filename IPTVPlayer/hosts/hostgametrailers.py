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
import re
import urllib
import base64
try:    import json
except: import simplejson as json
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
config.plugins.iptvplayer.movieshdco_sortby = ConfigSelection(default = "date", choices = [("date", _("Lastest")), ("views", _("Most viewed")), ("duree", _("Longest")), ("rate", _("Top rated")), ("random", _("Tandom"))]) 

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'GameTrailers'

class GameTrailers(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL = "http://www.gametrailers.com/"
    SEARCH_URL = MAIN_URL + "search"
    GAMES_OF_MONTH_URL = MAIN_URL + 'games/dk31tx/gt-release-calendar/videos-trailers'
    
    MAIN_ICON = "http://images.eurogamer.net/2012/articles//a/1/4/9/4/8/9/0/GT_Logo_Front.jpg/EG11/thumbnail/360x200/"
    
    MAIN_CAT_TAB = [{'category':'filters',         'mode':'',        'title': 'Videos',               'url':MAIN_URL + 'videos-trailers', 'icon':MAIN_ICON},
                    {'category':'shows',           'mode':'shows',   'title': 'Shows',                'url':MAIN_URL + 'shows',           'icon':MAIN_ICON},
                    {'category':'filters',         'mode':'',        'title': 'Reviews',              'url':MAIN_URL + 'reviews',         'icon':MAIN_ICON},
                    {'category':'filters',         'mode':'',        'title': 'Games of the month',   'url':GAMES_OF_MONTH_URL,           'icon':MAIN_ICON},
                    {'category':'platforms',       'mode':'',        'title': 'Platforms',            'url':MAIN_URL,                     'icon':MAIN_ICON},
                    {'category':'search',          'title': _('Search'), 'search_item':True},
                    {'category':'search_history',  'title': _('Search history')} ]
                    
    SORT_BY_TAB = [{'title':'Most Viewed', 'sort_by':'most_viewed'},
                   {'title':'Most Recent', 'sort_by':'most_recent'}]
    
    IMAGE_QUALITY = 'width=160&height=90&crop=true&quality=.91'
    
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'GameTrailers', 'cookie':'gametrailers.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def _getFullUrl(self, url, mode):
        if url.startswith('//'):
            url = 'http:' + url
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URLS[mode] + url
        
        if self.MAIN_URLS[mode].startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def _getValue(self, item, name):
        return self.cm.ph.getSearchGroups(item, '<meta itemprop="%s" content="([^"]+?)"' % name)[0]
        
    def addIconQuality(self, iconUrl):
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % iconUrl)
        if iconUrl.startswith('http') and iconUrl.endswith('?'):
            return iconUrl + self.IMAGE_QUALITY
        return ''
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("GameTrailers.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listPlatforms(self, cItem, nextCategory):
        printDBG("GameTrailers.listPlatforms")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="platform_nav">', '</ul>', False)[1]
        data = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>(.+?)</a>').findall(data)
        for item in data:
            if 'mobile-apps' in item[0]: continue
            params = dict(cItem)
            params.update({'title':self.cleanHtmlStr( item[1] ), 'category':nextCategory, 'url':item[0]})
            self.addDir(params)
    
    def getFilters(self, cItem, nextCategory):
        printDBG("GameTrailers.getFilters")
        
        if 'filters' in cItem:
            for item in cItem['filters']:
                params = dict(cItem)
                params.update({'title':item['title'], 'category':nextCategory, 'sub_items':item['sub_items']})
                self.addDir(params)
            return
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        baseUrl = self.cm.ph.getDataBeetwenMarkers(data, 'line_listing_results.init("', '"', False)[1]
        cItem = dict(cItem)
        cItem['base_url'] = baseUrl
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % baseUrl)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'class="filter_main_type">', '</div>', False)[1]
        data = data.split('class="filter_main_type">')
        mainFiltersTab = []
        for mainFilter in data:
            mainTitle = self.cm.ph.getDataBeetwenMarkers(mainFilter, '<h5>', '</h5>', False)[1]
            if '<ul class="sub_filter_group">' in mainFilter:
                subFilterData = mainFilter.split('<li class="facet_wrapper">')
                if len(subFilterData) > 0:
                    del subFilterData[0]
            else:
                subFilterData = [mainFilter]
            subFiltersTab = []
            for subFilter in subFilterData:
                #printDBG("====================================================")
                #printDBG(subFilter)
                #printDBG("====================================================")
                subTitle = self.cm.ph.getDataBeetwenMarkers(subFilter, '<h6>', '</h6>', False)[1]
                subItems = re.compile('<span class="[^"]+?" name="([^"]+?)" value="([^"]+?)">([^<]+?)<span>').findall(subFilter)
                subItemsTab = []
                for item in subItems:
                    subItemsTab.append({"_name":item[0], "_value":item[1], "title":item[2]})
                if len(subItemsTab):
                    subFiltersTab.append({'title':subTitle, 'sub_items':subItemsTab})
            if len(subFiltersTab) == 1:
                params = dict(cItem)
                params.update({'title':mainTitle, 'category':nextCategory, 'sub_items':subItemsTab})
                self.addDir(params)
            elif len(subFiltersTab) > 0:
                params = dict(cItem)
                params.update({'title':mainTitle, 'filters':subFiltersTab})
                self.addDir(params)
                
    def listShows(self, cItem, nextCategory):
        printDBG("GameTrailers.listPlatforms")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<span class="latest_item">', '<div id="mod_"', False)[1]
        data = data.split('<span class="latest_item">')
        for item in data:
            params = dict(cItem)
            params['category'] = nextCategory
            params['title']    = self._getValue(item, 'name')
            params['url']      = self._getValue(item, 'url')
            params['icon']     = self.addIconQuality(self._getValue(item, 'image'))
            params['desc']     = self.cleanHtmlStr( item )
            self.addDir(params)

    def listShowItems(self, cItem):
        printDBG("GameTrailers.listShowItems")
        if 'base_url' not in cItem:
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return
            baseUrl = self.cm.ph.getDataBeetwenMarkers(data, 'data-url="', '"', False)[1]
            cItem = dict(cItem)
            cItem['base_url'] = baseUrl
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % baseUrl)
        self.listItems(cItem)

    def listItems(self, cItem, nextCategory=None):
        printDBG("GameTrailers.listItems")
        page = cItem.get('page', 1)
        url  = cItem['base_url']
        if '&' in url: url += '&'
        else: url += '?'
        if 1 == page:
            url += 'sortBy={0}'.format(cItem.get('sort_by', 'undefined'))
            if '_name' in cItem: url += '&{0}={1}'.format(cItem['_name'], cItem['_value'])
            elif '_name_value' in cItem: url += '&{0}'.format(cItem['_name_value'])
        else:
            url += 'currentPage={0}'.format(page)
        cItem = dict(cItem)
        cItem['Referer'] = url
            
        post_data = cItem.get('post_data', None)
        httpParams = dict(self.defaultParams)
        ContentType =  cItem.get('Content-Type', None)
        Referer = cItem.get('Referer', None)
        if None != Referer: httpParams['header'] =  {'Referer':Referer, 'User-Agent':self.cm.HOST}
        else: {'User-Agent':self.cm.HOST}
        
        sts, data = self.cm.getPage(url, httpParams, post_data)
        if not sts: return
        p1 = '<li class="pagination_holder">'
        p2 = '<div class="pagination">'
        if p1 in data:
            data = data.split(p1)
        else:
            data = data.split(p2)
        
        nextPage = False
        if len(data) > 1:
            if 'href="?currentPage={0}"'.format(page + 1) in data[1]:
                nextPage = True
        
        data = data[0]
        if 'search' == cItem.get('mode', ''):
            if 'user_movies' == cItem['search_tab']:
                m1 = '<div class="content"'
            else:
                m1 = '<div class="holder"'
            self.listSearchVideoItems(cItem, data, m1)
        else:
            self.listVideoItems(cItem, data)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page + 1})
            self.addDir(params)
            
    def listSearchVideoItems(self, cItem, data, m1):
        data = data.split(m1)
        if len(data): del data[0]
        
        for item in data:
            params = self._mapItemBase('<'+item)
            if '' == params['url']: continue
            self.addVideo(params)
    
    def listVideoItems(self, cItem, data):
        data = data.split('</li>')
        if len(data): del data[-1]
        
        for item in data:
            params = self._mapItemBase(item)
            if '' == params['url']: continue
            self.addVideo(params)
    
    def _mapItemBase(self, item):
        params = {}
        url   = self.cm.ph.getSearchGroups(item, '<a href="([^"]+?)" class="thumbnail">')[0]
        if '' == url: url   = self.cm.ph.getSearchGroups(item, '<a class="watch[^"]*?" href="([^"]+?)"')[0]
        params['url'] = url
        
        params['title'] = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1] + ' ' + self.cm.ph.getDataBeetwenMarkers(item, '<h4>', '</h4>', False)[1])
        if '' == params['title']:
            params['title'] = self._getValue(item, "name")
        icon = self.addIconQuality(self._getValue(item, "thumbnailUrl"))
        if '' == icon: icon = self.cm.ph.getSearchGroups(item, '<img class="thumbnail" src="([^"]+?)"')[0]
        if '' == icon: icon = self.addIconQuality(self._getValue(item, "image"))
        if '' == icon: icon = self.cm.ph.getSearchGroups(item, '<img src="([^"]+?)"')[0]
        if '' == icon: icon = self.MAIN_ICON
        params['icon']  = icon
        params['desc']  = self.cleanHtmlStr( item )
        return params
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("GameTrailers.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        url = self.SEARCH_URL + '?keywords=' + urllib.quote_plus(searchPattern)
        post_data = cItem.get('post_data', None)
        httpParams = dict(self.defaultParams)
        ContentType =  cItem.get('Content-Type', None)
        Referer = cItem.get('Referer', None)
        if None != Referer: httpParams['header'] =  {'Referer':Referer, 'User-Agent':self.cm.HOST}
        else: {'User-Agent':self.cm.HOST}
        
        sts, data = self.cm.getPage(url, httpParams, post_data)
        if not sts: return
        
        promotionId = self.cm.ph.getSearchGroups(data, 'promotionId=([^/]+?)/')[0].replace('"', '').replace("'", "") + '/'
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="module_tabs">', '</ul>', False)[1]
        data = data.split('</a>')
        for item in data:
            sts, tab = self.cm.ph.getDataBeetwenMarkers(item, 'class="tab_', '"', False)
            if not sts: continue
            if tab not in ['videos', 'reviews', 'user_movies']: continue
            title = self.cleanHtmlStr( item )
            baseUrl = self.MAIN_URL  + 'feeds/search/child/{0}/?keywords={1}&tabName={2}'.format(promotionId, urllib.quote_plus(searchPattern), tab)
            params = {'name':'category', 'base_url':baseUrl, 'title':title, 'mode':'search', 'search_tab':tab}
            params['category'] = 'list_sort_by'
            self.addDir(params)
            
    
    def getLinksForVideo(self, cItem):
        printDBG("GameTrailers.getLinksForVideo [%s]" % cItem)
        urlTab = []
        videoUrl = cItem['url']
        urlTab = self.up.getVideoLinkExt(videoUrl)
        for idx in range(len(urlTab)):
            urlTab[idx]['need_resolve'] = 0
        return urlTab
        
    def getFavouriteData(self, cItem):
        return json.dumps(cItem['url'])
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo(fav_data)

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        filters  = self.currItem.get("filters", {})
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        cItem = self.currItem
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'filters':
            self.getFilters(self.currItem, 'list_filters')
            if 1 == len(self.currList):
                cItem = self.currList[0]
                self.currList = []
                category = 'list_filters'
        if category == 'list_filters':
            self.listsTab(cItem.get('sub_items', []), {'name':'category', 'category':'list_sort_by', 'icon':self.MAIN_ICON, 'base_url':cItem['base_url']})
            if 1 == len(self.currList):
                cItem = self.currList[0]
                self.currList = []
                category = 'list_sort_by'
        if category == 'list_sort_by':
            cItem = dict(cItem)
            if 'shows' == cItem.get('mode', ''):
                cItem['category'] = 'list_show_items'
            else: cItem['category'] = 'list_videos'
            self.listsTab(self.SORT_BY_TAB, cItem)
        elif category == 'list_videos':
            self.listItems(self.currItem)
        elif category == 'shows':
            self.listShows(self.currItem, 'list_sort_by')
        elif category == 'list_show_items':
            self.listShowItems(self.currItem)
        elif category == 'platforms':
            self.listPlatforms(self.currItem, 'filters')
            
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
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
        CHostBase.__init__(self, GameTrailers(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('gametrailerslogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"),    "movie"))
        #searchTypesOptions.append((_("TV Series"), "tv_serie"))
        #searchTypesOptions.append((_("Anime"),     "anime"))
        
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
