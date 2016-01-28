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
config.plugins.iptvplayer.solarmovie_episode_as_tvshow  = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Treat episode as TV Show", config.plugins.iptvplayer.solarmovie_episode_as_tvshow))
    return optionList
###################################################


def gettytul():
    return 'https://www.solarmovie.ph/'

class SolarMovie(CBaseHostClass):
    MAIN_URL    = 'https://www.solarmovie.ph/'
    SRCH_URL    = MAIN_URL + 'advanced-search/?q%5Btitle%5D={0}&q%5Bis_series%5D='
    DEFAULT_ICON_URL = 'http://static.solarmovie.ph/images/thumb150.png'
    
    MAIN_CAT_TAB = [{'category':'movies',         'title': _('Movies'),       'url':MAIN_URL + 'movies/',  'icon':DEFAULT_ICON_URL},
                    {'category':'tv_shows',       'title': _('TV Shows'),     'url':MAIN_URL + 'tv',       'icon':DEFAULT_ICON_URL},
                    {'category':'search',         'title': _('Search'),       'search_item':True},
                    {'category':'search_history', 'title': _('Search history')} 
                   ]
    MOVIES_TAB = [{'category':'movies_genres',   'title':_('Genres')},
                  {'category':'list_movies',     'title':_('New Movies'),      'url':MAIN_URL + 'popular-new-movies.html'},
                  {'category':'list_movies',     'title':_('HD Movies'),       'url':MAIN_URL + 'popular-hd-movies.html'},
                  {'category':'list_movies',     'title':_('Most popular'),    'url':MAIN_URL + 'popular-movies.html'},
                  {'category':'list_movies',     'title':_('Latest Movies'),    'url':MAIN_URL + 'latest-movies.html'},
                  #{'category':'list_movies',     'title':_('Coming Soon'),    'url':MAIN_URL + 'coming-soon/'},
                 ]
    TV_SHOWS_TAB = [{'category':'tv_shows_genres', 'title':_('Genres')},
                    {'category':'list_series',     'title':_('New TV Episodes'),      'url':MAIN_URL + 'popular-new-tv-shows.html'},
                    {'category':'list_series',     'title':_('Most popular'),    'url':MAIN_URL + 'popular-tv-shows.html'},
                    {'category':'list_series',     'title':_('Latest TV Episodes'),    'url':MAIN_URL + 'latest-tv-shows.html'},
                    #{'category':'list_series',     'title':_('Coming Soon'),    'url':MAIN_URL + 'coming-soon/tv/'},
                   ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'SolarMovie', 'cookie':'SolarMovie.cookie'})
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
        
    def _fillFilters(self, url):
        printDBG("SolarMovie._fillFilters")
        table = []
        sts, data = self.cm.getPage(url)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="sliderWrapper">', '</ul>', False)[1]
        data = data.split('</li>')
        for item in data:
            title = self.cleanHtmlStr( item )
            url   = self._getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''', 1, True)[0])
            if url.startswith('http'):
                table.append({'title':title, 'url':url})
        return table
        
    def fillMovieFilters(self, url):
        printDBG("SolarMovie.fillMovieFilters")
        self.movieGenresCache = self._fillFilters(url)
        return
        
    def fillTvShowFilters(self, url):
        printDBG("SolarMovie.fillTvShowFilters")
        self.tvshowGenresCache = self._fillFilters(url)
        return
        
    def listsTab(self, tab, cItem, type='dir'):
        printDBG("SolarMovie.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
        
    def listMoviesGenres(self, cItem, category):
        printDBG("SolarMovie.listMoviesGenres")
        if 0 == len(self.movieGenresCache):
            self.fillMovieFilters(cItem['url'])
        
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.movieGenresCache, cItem)
        
    def listTvShowsGenres(self, cItem, category):
        printDBG("SolarMovie.listTvShowsGenres")
        if 0 == len(self.tvshowGenresCache):
            self.fillTvShowFilters(cItem['url'])
        
        if len(self.tvshowGenresCache):
            tab = []
            cItem = dict(cItem)
            cItem['category'] = category
            tab.extend(self.tvshowGenresCache)
            self.listsTab(tab, cItem)
            
    def listItems(self, cItem, category='video'):
        printDBG("SolarMovie.listMovies")
        url = cItem['url']
        if '?' in url:
            post = url.split('?')
            url  = post[0]
            post = post[1] 
        else:
            post = ''
        page = cItem.get('page', 1)
        if page > 1:
            url += '?page=%d&' % page
        elif post != '':
            url += '?'
        if post != '': 
            url += post
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        if ('page=%d"' % (page + 1)) in data:
            nextPage = True
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="coverList">', '<div id="sidebar">', False)[1]#<hr
        data = data.split('<span class="wrapper">')
        if len(data): del data[0]
        
        for item in data:
            tmp    = item.split('<span class="name">')
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'data-original="([^"]+?)"')[0]
            #title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            title  = self.cleanHtmlStr( tmp[-1] )
            
            if category != 'video' and '/season-' in url and config.plugins.iptvplayer.solarmovie_episode_as_tvshow.value:
                url = url.split('/season-')[0]
                #title = self.cm.ph.getSearchGroups(title, '.+?s[0-9]+?e[0-9]+? (.+?)$')[0].strip()
                title = url.split('/')[-1].replace('-', ' ').title()
                url += '/'
            params = dict(cItem)
            params.update( {'title': title, 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( tmp[0].replace('</li>', ' | ') ), 'icon':self._getFullUrl(icon)} )
            if category == 'video' or '/episode-' in url:
                self.addVideo(params)
            else:
                params['category'] = category
                self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listSeasons(self, cItem, category):
        printDBG("SolarMovie.listSeasons")
        self.episodesCache = []
        
        baseUrl = cItem['url']
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return 
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="js-episode">', '</div>', False)
        seasonsTab = []        
        for item in data:
            eUrl   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0].strip()
            
            tmp = self.cm.ph.getSearchGroups(eUrl, 'season-([0-9]+?)/episode-([0-9]+?)/', 2)
            sNum = tmp[0]
            eNum = tmp[1]
            
            eTitle = self.cm.ph.getDataBeetwenMarkers(item, '<span class="epname">', '</a>')[1]
            eDesc  = self.cleanHtmlStr( item.split('</select>')[-1] )
            
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
            params = {'title':cItem['title'] + ': s%se%s ' % (sNum.zfill(2), eNum.zfill(2)) + self.cleanHtmlStr( eTitle ), 'desc':eDesc, 'url':self._getFullUrl(eUrl)}
            self.episodesCache[-1].append(params)
        
    def listEpisodes(self, cItem):
        printDBG("SolarMovie.listEpisodes")
        seasonIdx = cItem['season_idx']
        
        if seasonIdx >= 0 and seasonIdx < len(self.episodesCache):
            episodesList = self.episodesCache[seasonIdx]
            self.listsTab(episodesList, cItem, 'video')
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = self.SRCH_URL.format( urllib.quote_plus(searchPattern) )
        
        if 'movies' == searchType:
            cItem['url'] += '1'
            category = 'video'
        else:
            cItem['url'] += '2'
            category = 'list_seasons'
            
        self.listItems(cItem, category)
        
    def getLinksForVideo(self, cItem):
        printDBG("SolarMovie.getLinksForVideo [%s]" % cItem)
        urlTab = []
        url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return urlTab
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr id="link_', '</tr>', True)
        for item in data:
            tmp = self.cm.ph.getSearchGroups(item, '<a[^>]*?href="([^"]*?/link/[^"]+?)"[^>]*?>([^<]+?)<', 2)
            if '' == tmp[0].strip(): 
                continue 
            title = tmp[1].strip()
            title += ' ' + self.cleanHtmlStr( item.split('</a>')[-1] )
            urlTab.append({'name':title, 'url':self._getFullUrl(tmp[0]), 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("SolarMovie.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        
        videoUrl = ''
        if '/link/' in baseUrl:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return []
            data = self.cm.ph.getDataBeetwenMarkers(data, 'fullyGreenButton', '</a>', False)[1]
            url = self.cm.ph.getSearchGroups(data, 'href="([^"]*?/link/play/[^"]+?)"')[0]
            sts, data = self.cm.getPage(self._getFullUrl(url))
            if not sts: return []
            videoUrl = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="(http[^"]+?)"', 1, True)[0]
        
        if '' != videoUrl:
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})

    def getArticleContent(self, cItem):
        printDBG("SolarMovie.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        title = self.cm.ph.getDataBeetwenMarkers(data, '</select>', '</div>', False)[1]
        desc  = self.cm.ph.getDataBeetwenMarkers(data, '<p class="description"', '</p>', True)[1]
        icon  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="coverImage">', '</div>', False)[1]
        icon  = self.cm.ph.getSearchGroups(icon, 'href="([^"]*?\.jpg)"')[0]
        
        descData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="overViewBox">', '</div>', False)[1].split('</dl>')
        printDBG(descData)
        descTabMap = {"Directors":    "director",
                      "Cast":         "actors",
                      "Genres":       "genre",
                      "Country":      "country",
                      "Release Date": "released",
                      "Duration":     "duration"}
        
        otherInfo = {}
        for item in descData:
            item = item.split('</dt>')
            if len(item) < 2: continue
            key = self.cleanHtmlStr( item[0] ).replace(':', '').strip()
            val = self.cleanHtmlStr( item[1] )
            if key in descTabMap:
                otherInfo[descTabMap[key]] = val
        
        imdbRating = self.cm.ph.getDataBeetwenMarkers(data, '<div class="imdbRating', '</p>', True)[1]
        solarRating = self.cm.ph.getDataBeetwenMarkers(data, '<div class="solarRating', '</p>', True)[1]
        
        otherInfo['rating'] = self.cleanHtmlStr( imdbRating )
        otherInfo['rated'] = self.cleanHtmlStr( solarRating )
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':otherInfo}]
        
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
        elif category == 'tv_shows':
            self.listsTab(self.TV_SHOWS_TAB, self.currItem)
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
        CHostBase.__init__(self, SolarMovie(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('solarmovielogo.png')])
    
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
        cItem = self.host.currList[Index]
        
        if cItem['type'] != 'video' and cItem['category'] != 'list_seasons':
            return RetHost(retCode, value=retlist)
        hList = self.host.getArticleContent(cItem)
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
        searchTypesOptions.append((_("Movies"), "movies"))
        searchTypesOptions.append((_("Series"), "series"))
        
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
