# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import time
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
    return 'xrysoi.se'

class XrysoiSE(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL = 'http://xrysoi.se/'
    SEARCH_SUFFIX = '?s='
    
    MAIN_CAT_TAB = [{'category':'movies',         'mode':'movies',      'title': 'Ταινιες',   'url':'',    'icon':''},
                    #{'category':'movies',         'mode':'movies',      'title': 'Movies',    'url':'search.php',    'icon':''},
                    #{'category':'tv_shows',       'mode':'tv_shows',    'title': 'TV shows',  'url':'search.php',    'icon':''},
                    {'category':'search',          'title': _('Search'), 'search_item':True},
                    {'category':'search_history',  'title': _('Search history')} ]
    
    SORT_NAV_TAB = [{'sort_by':'favorites',   'title':'Popular'},
                    {'sort_by':'imdb_rating', 'title':'IMDb rating'},
                    {'sort_by':'yer',         'title':'Year'},
                    {'sort_by':'abc',         'title':'ABC'}]
                    #                    {'sort_by':'trending',    'title':'Trending'}
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'XrysoiSE.tv', 'cookie':'XrysoiSEtv.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheFilters = {}
        self.cacheLinks = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("XrysoiSE.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillCategories(self):
        printDBG("XrysoiSE.fillCategories")
        self.cacheFilters = {}
        sts, data = self.cm.getPage(self.MAIN_URL)
        if not sts: return
        
        moviesTab = [{'title':'Όλα', 'url':self._getFullUrl('category/new-good/')}]
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '>Ταινιες<', '</ul>', False)[1]
        tmp = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            if item[0].endswith('collection/'): continue # at now we are not able to handle colletion
            if item[0].endswith('προσεχώς/'): continue # soon, so there is only trailer link available
            moviesTab.append({'title':self.cleanHtmlStr(item[1]), 'url':self._getFullUrl(item[0])})
            
        #tvshowsTab = [{'title':'All', 'url':self._getFullUrl('tv-shows')}]
        #tmp = self.cm.ph.getDataBeetwenMarkers(data, 'TV Shows</a>', '</ul>', False)[1]
        #tmp = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        #for item in tmp:
        #    tvshowsTab.append({'title':item[1], 'url':self._getFullUrl(item[0])})
            
        #newsTab = [{'title':'New Episodes',           'mode':'movies',   'category':'list_items',   'url':self._getFullUrl('new-shows')}]
        #newsTab.append( {'title':'New Movies',        'mode':'movies',   'category':'list_items',   'url':self._getFullUrl('new-movies')} )
        #newsTab.append( {'title':'Box Office Movies', 'mode':'movies',   'category':'list_items',   'url':self._getFullUrl('featuredmovies')} )
            
        #self.cacheFilters['new']      = newsTab
        self.cacheFilters['movies']   = moviesTab
        #self.cacheFilters['tv_shows'] = tvshowsTab
        
    def listMoviesCategory(self, cItem, nextCategory):
        printDBG("XrysoiSE.listMoviesCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('movies', []), cItem)
        
    def listTVShowsCategory(self, cItem, nextCategory):
        printDBG("XrysoiSE.listTVShowsCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('tv_shows', []), cItem)
        
    def listNewCategory(self, cItem):
        printDBG("XrysoiSE.listNewCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem.pop("category", None)
        #cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('new', []), cItem)
            
    def listItems(self, cItem, nextCategory=None):
        printDBG("XrysoiSE.listItems")
        page = cItem.get('page', 1)
        
        url = cItem['url'] 
        if page > 1:
            url += '/page/' + str(page)
        
        if 'url_suffix' in cItem:
            url += cItem['url_suffix']
        
        sts, data = self.cm.getPage(url) #, {'header':self.AJAX_HEADER}
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, "class='pages'", '</div>', False)[1]
        if '>&raquo;<' in nextPage:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="moviefilm">', '<div class="filmborder">', False)[1]
        data = data.split('<div class="moviefilm">')
        for item in data:
            url  = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            icon = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            title  = self.cleanHtmlStr( item )
            if url.startswith('http'):
                params = dict(cItem)
                params.update({'title':title, 'url':url, 'icon':icon})
                if 'search' == cItem.get('mode'):
                    if 'tv-series' in url: continue
                    if '-collection-' in url: continue
                if nextCategory == None:
                    params['mode'] = 'movies'
                    self.addVideo(params)
                else:
                    params['category'] = nextCategory
                    self.addDir(params)
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
        
    def listSeasons(self, cItem, nextCategory):
        printDBG("XrysoiSE.listSeasons")

        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tab selected" id="episodes">', '</select>', False)[1]
        data = re.compile('<option[^>]*?value="([^"]+?)"[^>]*?>([^<]+?)</option>').findall(data)
        for item in data:
            params = dict(cItem)
            url = self._getFullUrl(item[0])
            params.update({'url':url, 'title':item[1], 'show_title':cItem['title'], 'category':nextCategory})
            self.addDir(params)
    
    def listEpisodes(self, cItem):
        printDBG("XrysoiSE.listEpisodes")

        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<li class="episode ">', '</ul>', False)[1]
        data = data.split('<li class="episode ">')
        for item in data:
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"#]+?)"')[0] )
            desc  = self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', False)[1]
            title = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            
            if url.startswith('http'):
                params = {'title':title, 'url':url, 'desc':desc}
                self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("XrysoiSE.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.MAIN_URL
        cItem['url_suffix'] = self.SEARCH_SUFFIX + urllib.quote_plus(searchPattern)
        cItem['mode'] = 'search'
        self.listItems(cItem)
    
    def getLinksForVideo(self, cItem):
        printDBG("XrysoiSE.getLinksForVideo [%s]" % cItem)
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
        self.cacheLinks = {}
        
        mode = cItem.get('mode')
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        # regular links
        sts, linksData = self.cm.ph.getDataBeetwenMarkers(data, '<blockquote class="tr_bq">', '<center>', False)
        if sts:
            linksData = re.compile('href="([^"]+?)"').findall(linksData)
            for item in linksData:
                # only supported hosts will be displayed
                if 1 != self.up.checkHostSupport(item): continue 
                url  = item
                name = self.up.getHostName(url)
                if url.startswith('//'): url += 'http'
                if url.startswith('http'):
                    urlTab.append({'name':name, 'url':url, 'need_resolve':1})
                    
        # trailer link extraction
        sts, trailer = self.cm.ph.getDataBeetwenMarkers(data, 'trailer.png', '</iframe>', False, False)
        if sts:
            trailer = self.cm.ph.getSearchGroups(trailer.lower(), '<iframe[^>]+?src="([^"]+?)"')[0]
            if trailer.startswith('//'): trailer += 'http'
            if trailer.startswith('http'):
                params = {'name':'TRAILER', 'url':trailer, 'need_resolve':1}
                urlTab.append(params)
                # if only TRAILER is available we will add it twice, so user will see that there is no links to full content
                if 1 == len(urlTab): urlTab.append(params)
        
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("XrysoiSE.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("MoviesHDCO.getArticleContent [%s]" % cItem)
        retTab = []
        
        if 'movies' != cItem.get('mode'): return retTab
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<meta property', '<script')
        if not sts: return retTab
        
        icon  = self.cm.ph.getSearchGroups(data, '<meta[^>]*?property="og:image"[^>]*?content="(http[^"]+?)"')[0]
        title = self.cm.ph.getSearchGroups(data, '<meta[^>]*?property="og:title"[^>]*?content="([^"]+?)"')[0]
        desc  = self.cm.ph.getSearchGroups(data, '<meta[^>]*?property="og:description"[^>]*?content="([^"]+?)"')[0]
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':{}}]
        
    def getFavouriteData(self, cItem):
        return json.dumps({'url':cItem['url'], 'mode':cItem.get('mode')}) 
        
    def getLinksForFavourite(self, fav_data):
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except: printExc()
        return links

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'new':
            self.listNewCategory(self.currItem)
        elif category == 'movies':
            self.listMoviesCategory(self.currItem, 'list_items')
        elif category == 'tv_shows':
            self.listTVShowsCategory(self.currItem, 'list_sortnav')
            
        elif category == 'list_sortnav':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_items'
            self.listsTab(self.SORT_NAV_TAB, cItem)
        elif category == 'list_items':
            if mode == 'movies':
                self.listItems(self.currItem)
            else:
                self.listItems(self.currItem, 'list_seasons')
        elif category == 'list_seasons':
            self.listSeasons(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, XrysoiSE(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('xrysoiselogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
        
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
        return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
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
