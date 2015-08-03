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
    return 'CartoonHD.tv'

class CartoonHD(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL = 'http://www.cartoonhd.tv/'
    SEARCH_URL = MAIN_URL + 'ajax/search.php'
    
    MAIN_CAT_TAB = [{'category':'new',            'mode':'',            'title': 'New',       'url':'search.php',    'icon':''},
                    {'category':'movies',         'mode':'movies',      'title': 'Movies',    'url':'search.php',    'icon':''},
                    {'category':'tv_shows',       'mode':'tv_shows',    'title': 'TV shows',  'url':'search.php',    'icon':''},
                    {'category':'search',          'title': _('Search'), 'search_item':True},
                    {'category':'search_history',  'title': _('Search history')} ]
    
    SORT_NAV_TAB = [{'sort_by':'favorites',   'title':'Popular'},
                    {'sort_by':'imdb_rating', 'title':'IMDb rating'},
                    {'sort_by':'yer',         'title':'Year'},
                    {'sort_by':'abc',         'title':'ABC'}]
                    #                    {'sort_by':'trending',    'title':'Trending'}
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'CartoonHD.tv', 'cookie':'cartoonhdtv.cookie'})
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
        printDBG("CartoonHD.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillCategories(self):
        printDBG("CartoonHD.fillCategories")
        self.cacheFilters = {}
        sts, data = self.cm.getPage(self.MAIN_URL)
        if not sts: return
        
        moviesTab = [{'title':'All', 'url':self._getFullUrl('movies')}]
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<a href="http://www.cartoonhd.tv/movies">Movies</a>', '</ul>', False)[1]
        tmp = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            moviesTab.append({'title':item[1], 'url':self._getFullUrl(item[0])})
            
        tvshowsTab = [{'title':'All', 'url':self._getFullUrl('tv-shows')}]
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'TV Shows</a>', '</ul>', False)[1]
        tmp = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            tvshowsTab.append({'title':item[1], 'url':self._getFullUrl(item[0])})
            
        newsTab = [{'title':'New Episodes',           'mode':'movies',   'category':'list_items',   'url':self._getFullUrl('new-shows')}]
        newsTab.append( {'title':'New Movies',        'mode':'movies',   'category':'list_items',   'url':self._getFullUrl('new-movies')} )
        newsTab.append( {'title':'Box Office Movies', 'mode':'movies',   'category':'list_items',   'url':self._getFullUrl('featuredmovies')} )
            
        self.cacheFilters['new']      = newsTab
        self.cacheFilters['movies']   = moviesTab
        self.cacheFilters['tv_shows'] = tvshowsTab
        
    def listMoviesCategory(self, cItem, nextCategory):
        printDBG("CartoonHD.listMoviesCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('movies', []), cItem)
        
    def listTVShowsCategory(self, cItem, nextCategory):
        printDBG("CartoonHD.listTVShowsCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('tv_shows', []), cItem)
        
    def listNewCategory(self, cItem):
        printDBG("CartoonHD.listNewCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem.pop("category", None)
        #cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('new', []), cItem)
            
    def listItems(self, cItem, nextCategory=None):
        printDBG("CartoonHD.listItems")
        page = cItem.get('page', 1)
        
        url = cItem['url'] + '/' + cItem.get('sort_by', '') + '/' + str(page)
        
        sts, data = self.cm.getPage(url, {'header':self.AJAX_HEADER})
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<label for="pagenav">', '</form>', False)[1]
        if '/{0}"'.format(page+1) in nextPage:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="flipBox">', '</main>', False)[1]
        data = data.split('</section>')
        if len(data): del data[-1]
        for item in data:
            url  = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            icon = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            desc = 'IMDb ' + self.cm.ph.getSearchGroups(item, '>([ 0-9.]+?)<')[0] + ', '
            desc += self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', False)[1]
            title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1] )
            if url.startswith('http'):
                params = {'title':title, 'url':url, 'desc':desc, 'icon':icon}
                if nextCategory == None:
                    self.addVideo(params)
                else:
                    params['category'] = nextCategory
                    params2 = dict(cItem)
                    params2.update(params)
                    self.addDir(params2)
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
        
    def listSeasons(self, cItem, nextCategory):
        printDBG("CartoonHD.listSeasons")

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
        printDBG("CartoonHD.listEpisodes")

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
        printDBG("CartoonHD.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        sts, data = self.cm.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return
        
        tor = self.cm.ph.getSearchGroups(data, "tor='([^']+?)'")[0]
        
        q = searchPattern
        post_data = {'q':q, 'limit':100, 'timestamp':str(time.time()).split('.')[0], 'verifiedCheck':tor}
        
        httpParams = dict(self.defaultParams)
        httpParams['header'] =  {'Referer':self.MAIN_URL, 'User-Agent':self.cm.HOST, 'X-Requested-With':'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'}
        sts, data = self.cm.getPage(self.SEARCH_URL, httpParams, post_data=post_data)
        if not sts: return
        try:
            data = byteify(json.loads(data))
            for item in data:
                desc = item['meta']
                if 'Movie' in desc:
                    category = 'video'
                elif 'TV show' in desc:
                    category = 'list_seasons'
                else:
                    category = None
                
                if None != category:
                    title = item['title']
                    url   = item['permalink'].replace('\\/', '/')
                    icon  = item.get('image', '').replace('\\/', '/')
                    if url.startswith('http'):
                        params = {'name':'category', 'title':title, 'url':url, 'desc':desc, 'icon':icon, 'category':category}
                        if category == 'video':
                            self.addVideo(params)
                        else:
                            self.addDir(params)
        except:
            printExc()
    
    def getLinksForVideo(self, cItem):
        printDBG("CartoonHD.getLinksForVideo [%s]" % cItem)
        urlTab = self.cacheLinks.get(cItem['url'],  [])
        if len(urlTab): return urlTab
        self.cacheLinks = {}
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        tor  = self.cm.ph.getSearchGroups(data, "tor='([^']+?)'")[0]
        elid = self.cm.ph.getSearchGroups(data, 'data-movie="([^"]+?)"')[0]
        if '' == elid: elid = self.cm.ph.getSearchGroups(data, 'elid="([^"]+?)"')[0]
        if '' == elid: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Change Source/Quality</option>', '</select>', False)[1]
        hostings = []
        data = re.compile('<option[^>]*?value="([^"]+?)"[^>]*?>([^<]+?)</option>').findall(data)
        for item in data:
            hostings.append({'id':item[0], 'name':item[1]})
        
        httpParams = dict(self.defaultParams)
        httpParams['header'] =  {'Referer':cItem['url'], 'User-Agent':self.cm.HOST, 'X-Requested-With':'XMLHttpRequest', 'Accept':'application/json, text/javascript, */*; q=0.01'}
        if '/movie/' in cItem['url']:
            type = 'getMovieEmb'
        else: type = 'getEpisodeEmb'
        url = 'ajax/embeds.php?action={0}&idEl={1}&token={2}'.format(type, elid, tor)
        sts, data = self.cm.getPage(self._getFullUrl(url), httpParams, None)
        if not sts: return []
        #printDBG('===============================================================')
        #printDBG(data)
        #printDBG('===============================================================')
        try:
            data = byteify(json.loads(data))
            for item in hostings:
                if item['id'] in data:
                    url = data[item['id']].replace('\\/', '/')
                    url = self.cm.ph.getDataBeetwenMarkers(url, 'src="', '"', False, False)[1]
                    if 'googlevideo.com' in url:
                        need_resolve = 0
                    else: need_resolve = 1
                    urlTab.append({'name':item['name'], 'url':url, 'need_resolve':need_resolve})
        except:
            printExc()
        self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("CartoonHD.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
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
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'new':
            self.listNewCategory(self.currItem)
        elif category == 'movies':
            self.listMoviesCategory(self.currItem, 'list_sortnav')
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
        CHostBase.__init__(self, CartoonHD(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('cartoonhdlogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
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
