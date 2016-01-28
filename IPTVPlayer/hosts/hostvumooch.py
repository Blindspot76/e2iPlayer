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
#config.plugins.iptvplayer.alltubetv_premium  = ConfigYesNo(default = False)
#config.plugins.iptvplayer.alltubetv_login    = ConfigText(default = "", fixed_size = False)
#config.plugins.iptvplayer.alltubetv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    #if config.plugins.iptvplayer.alltubetv_premium.value:
    #    optionList.append(getConfigListEntry("  alltubetv login:", config.plugins.iptvplayer.alltubetv_login))
    #    optionList.append(getConfigListEntry("  alltubetv hasło:", config.plugins.iptvplayer.alltubetv_password))
    return optionList
###################################################


def gettytul():
    return 'http://vumoo.ch/'

class Vumoo(CBaseHostClass):
    MAIN_URL    = 'http://vumoo.ch/'
    SRCH_URL    = MAIN_URL + 'videos/search/?search='
    DEFAULT_ICON_URL = 'http://pbs.twimg.com/profile_images/559558208411287552/fFKLeLBS.png'
    
    MAIN_CAT_TAB = [{'category':'movies',         'title': _('Movies'),       'url':MAIN_URL,        'icon':DEFAULT_ICON_URL},
                    {'category':'tv_shows_genres','title': _('TV Shows'),     'url':MAIN_URL + 'tv', 'icon':DEFAULT_ICON_URL},
                    {'category':'search',         'title': _('Search'),       'search_item':True},
                    {'category':'search_history', 'title': _('Search history')} 
                   ]
    MOVIES_TAB = [{'category':'movies_genres',   'title':_('Genres')},
                  {'category':'list_movies',     'title':_('HD Movies'),      'url':MAIN_URL + 'videos/category/hd'},
                  {'category':'list_movies',     'title':_('New Releases'),   'url':MAIN_URL + 'videos/category/new-releases'},
                  {'category':'list_movies',     'title':_('Recently Added'), 'url':MAIN_URL + 'videos/category/recently-added'},
                 ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Vumoo', 'cookie':'Vumoo.cookie'})
        self.movieGenresCache = []
        self.tvshowGenresCache = []
        self.seriesCache = []
        self.episodesCache = []
        
    def _getFullUrl(self, url, series=False):
        if not series:
            mainUrl = self.MAIN_URL
        else:
            mainUrl = self.S_MAIN_URL
        if url.startswith('/'):
            url = url[1:]
        if 0 < len(url) and not url.startswith('http'):
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def fillMovieFilters(self, url):
        printDBG("Vumoo.fillMovieFilters")
        self.movieGenresCache = []
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="multi-column-dropdown">', '<a href="/tv">', False)[1]
        data = data.split('</li>')
        for item in data:
            title = self.cleanHtmlStr( item )
            url   = self._getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''', 1, True)[0])
            if url.startswith('http'):
                self.movieGenresCache.append({'title':title, 'url':url})
        
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Vumoo.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
        
    def listMoviesGenres(self, cItem, category):
        printDBG("Vumoo.listMoviesGenres")
        if 0 == len(self.movieGenresCache):
            self.fillMovieFilters(cItem['url'])
        
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.movieGenresCache, cItem)
        
    def fillTvShowFilters(self, url):
        printDBG("Vumoo.fillTvShowFilters")
        self.tvshowGenresCache = []
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Subgenres', '<section', False)[1]
        data = data.split('<li>')
        if len(data): del data[0]
        for item in data:
            title = self.cleanHtmlStr( item )
            url   = self._getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''', 1, True)[0])
            if url.startswith('http'):
                self.tvshowGenresCache.append({'title':title, 'url':url})
        
    def listTvShowsGenres(self, cItem, category):
        printDBG("Vumoo.listTvShowsGenres")
        if 0 == len(self.tvshowGenresCache):
            self.fillTvShowFilters(cItem['url'])
        
        if len(self.tvshowGenresCache):
            tab = [{'title':_('--All--'), 'url':cItem['url']}]
            cItem = dict(cItem)
            cItem['category'] = category
            tab.extend(self.tvshowGenresCache)
            self.listsTab(tab, cItem)
            
    def listItems(self, cItem, category='video'):
        printDBG("Vumoo.listMovies")
        url = cItem['url']
        if '?' in url:
            post = url.split('?')
            url  = post[0]
            post = post[1] 
        else:
            post = ''
        url += '?'
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page=%d&' % page
        if post != '': 
            url += post
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        data = self.cm.ph.getDataBeetwenMarkers(data, '<section ', '</section>', True)[1]
        data = data.split('</article>')
        if len(data): del data[-1]
        
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( item ), 'icon':self._getFullUrl(icon)} )
            if category == 'video':
                self.addVideo(params)
            else:
                params['category'] = category
                self.addDir(params)
            nextPage = True
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listSeasons(self, cItem, category):
        printDBG("Vumoo.listSeasons")
        self.episodesCache = []
        
        baseUrl = cItem['url']
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return 
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tv-details-episodes synopsis-container">', '</ol>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]
        
        seasonsTab = []        
        for item in data:
            tmp = self.cm.ph.getSearchGroups(item, 'season([0-9]+?)-([0-9]+?)[^0-9]', 2)
            sNum = tmp[0]
            eNum = tmp[1]
            
            tmp    = item.split('</span>')
            eUrl   = self.cm.ph.getSearchGroups(item, 'data-click="([^"]+?)"')[0].strip()
            eIcon  = self.cm.ph.getSearchGroups(item, 'data-poster="([^"]+?)"')[0].strip()
            eTitle = self.cleanHtmlStr( tmp[0] )
            eDesc  = self.cleanHtmlStr( tmp[-1] )
            
            if sNum in seasonsTab:
                sIdx = seasonsTab.index(sNum)
            else:
                sIdx = len(seasonsTab)
                # add new season
                seasonsTab.append(sNum)
                self.episodesCache.append([])
                params = dict(cItem)
                params.update({'category':category, 'season_idx':sIdx, 'title':'Season %s' % sNum})
                self.addDir(params)
            
            # add episode to season
            params = {'title':cItem['title'] + ': ' + eTitle, 'icon':self._getFullUrl(eIcon), 'desc':eDesc, 'episode_url':eUrl}
            self.episodesCache[-1].append(params)
        
    def listEpisodes(self, cItem):
        printDBG("Vumoo.listEpisodes")
        seasonIdx = cItem['season_idx']
        
        if seasonIdx >= 0 and seasonIdx < len(self.episodesCache):
            episodesList = self.episodesCache[seasonIdx]
            self.listsTab(episodesList, cItem, 'video')
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url']  = self.SRCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(cItem)
        
    def getLinksForVideo(self, cItem):
        printDBG("Vumoo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        url = cItem['url']
        
        if 'episode_url' in cItem:
            eUrl = cItem['episode_url']
            if eUrl.startswith('http'):
                eUrl = strwithmeta(eUrl, {'Referer':url})
                urlTab.append({'name':'episode', 'url':eUrl, 'need_resolve':0})
        else:
            sts, data = self.cm.getPage(url)
            if not sts: return []
            
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="video">', '</div>', False)[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '</iframe>', False)
            for item in data:
                vidUrl = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
                if 1 != self.up.checkHostSupport(vidUrl): continue 
                urlTab.append({'name':self.up.getHostName(vidUrl), 'url':vidUrl, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Vumoo.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        
        videoUrl = baseUrl
        urlTab = self.up.getVideoLinkExt(videoUrl)
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
        elif category == 'movies':
            self.listsTab(self.MOVIES_TAB, self.currItem)
        elif category == 'movies_genres':
            self.listMoviesGenres(self.currItem, 'list_movies')
        elif category == 'list_movies':
            self.listItems(self.currItem)
    #SERIES
        elif category == 'tv_shows_genres':
            self.listTvShowsGenres(self.currItem, 'list_series')
        elif category == 'list_series':
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
        CHostBase.__init__(self, Vumoo(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('vumoochlogo.png')])
    
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
