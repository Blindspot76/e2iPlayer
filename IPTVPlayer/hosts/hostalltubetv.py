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
    return 'alltube.tv'

class AlltubeTV(CBaseHostClass):
    MAIN_URL    = 'http://alltube.tv/'
    SRCH_URL    = MAIN_URL + 'szukaj'
    
    MAIN_CAT_TAB = [{'category':'latest_added',       'title': _('Latest added'),  'url':MAIN_URL,                   'icon':''},
                    {'category':'genres_movies',      'title': _('Movies'),        'url':MAIN_URL+'filmy-online/',   'icon':''},
                    {'category':'cat_series',         'title': _('Series'),        'url':MAIN_URL+'seriale-online/', 'icon':''},
                    {'category':'list_movies',        'title': _('Junior'),        'url':MAIN_URL+'filmy-online/',  'cat':'5', 'icon':'', 'mtype':True},
                    {'category':'list_rank',          'title': _('Ranking'),       'url':MAIN_URL+'ranking', 'icon':''},
                    {'category':'search',             'title': _('Search'), 'search_item':True},
                    {'category':'search_history',     'title': _('Search history')} ]
                    
    LAST_ADDED_TAB = [{'category':'latest_added_movies',  'title': _('Movies'),        'url':MAIN_URL, 'icon':''},
                      {'category':'latest_added_series',  'title': _('Series'),        'url':MAIN_URL, 'icon':''} ]
                      
    SERIES_CAT_TAB = [{'category':'list_series_abc',  'title': _('ABC'),                        'url':MAIN_URL, 'icon':''},
                      {'category':'list_series',      'title': _('All'), 'letter':'all',        'url':MAIN_URL, 'icon':''} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'AlltubeTV', 'cookie':'alltubetv.cookie'})
        self.filterCache = {}
        self.seriesCache = {}
        self.seriesLetters = []
        self.episodesCache = []
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("AlltubeTV.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def _listItemsTab(self, cItem, m1, m2, sp, category='video'):
        printDBG("AlltubeTV._listItemsTab >>>>>>> cItem[%r]" % cItem)
        
        url = cItem['url']
        if '' != cItem.get('cat', ''):
            url += 'kategoria[%s]+' % cItem['cat']
        if '' != cItem.get('ver', ''):
            url += 'wersja[%s]+' % cItem['ver']
        if '' != cItem.get('year', ''):
            url += 'rok[%s]+' % cItem['year']
        page = cItem.get('page', 1)
        if page > 1:
            url += 'strona[%s]+' % page
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('strona[%s]+' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        #printDBG("DAAAAAAAAAAAAAA [%s]" % data)
        data = data.split(sp)
        if len(data): del data[0]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<div class="title">', '</div>', False)[1]
            if '' == title: 
                title = self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1]
            if '' == title: 
                title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   = self.cm.ph.getDataBeetwenMarkers(item, '<div class="description">', '</div>', False)[1]
            if '' == desc:
                desc = item.split('<p>')[-1]
            
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
            if category != 'video':
                params['category'] = category
                self.addDir(params)
            else: self.addVideo(params)
            
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listLatestAddedMovies(self, cItem):
        printDBG("AlltubeTV.listLatestAddedMovies")
        self._listItemsTab(cItem, 'statnio dodane filmy', '<div class="col-sm-6">', '<div class="item clearfix">', category='video')
        
    def listLatestAddedSeries(self, cItem, category):
        printDBG("AlltubeTV.listLatestAddedSeries")
        self._listItemsTab(cItem, 'statnio dodane seriale', '<div class="col-sm-6">', '<div class="item clearfix">', category)
            
    def fillFilterCache(self, url):
        sts, data = self.cm.getPage(url)
        if not sts: return
        def _getFilters(m1, m2, key):
            tab = []
            dat = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
            dat = re.compile('<li[^>]*?data-id="([^>]+?)"[^>]*?>([^>]+?)</li>').findall(dat)
            for item in dat:
                tab.append({key:item[0], 'title':item[1]})
            if len(tab):
                tab.insert(0, {'title':_('All')})
            return tab
        self.filterCache['category'] = _getFilters('<ul id="filter-category">', '</ul>', 'cat')
        self.filterCache['version']  = _getFilters('<ul id="filter-version">', '</ul>', 'ver')
        self.filterCache['year']     = _getFilters('<ul id="filter-year">', '</ul>', 'year')
        
    def listFilters(self, cItem, filter, category):
        printDBG("AlltubeTV.listFilters")
        tab = self.filterCache.get(filter, [])
        if 0 == len(tab):
            self.fillFilterCache(self.MAIN_URL + 'filmy-online/')
            tab = self.filterCache.get(filter, [])
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
        
    def _listItemsTab2(self, cItem, category='video'):
        printDBG("AlltubeTV._listItemsTab >>>>>>> cItem[%r]" % cItem)
        url = cItem['url']
        if '' != cItem.get('cat', ''):
            url += 'kategoria[%s]+' % cItem['cat']
        if '' != cItem.get('ver', ''):
            url += 'wersja[%s]+' % cItem['ver']
        if '' != cItem.get('year', ''):
            url += 'rok[%s]+' % cItem['year']
        page = cItem.get('page', 1)
        if page > 1:
            url += 'strona[%s]+' % page
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('strona[%s]+' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        data = CParsingHelper.getDataBeetwenMarkers(data, 'name="filter-year">', '<div class="container">', False)[1]
        data = data.split('<div class="col-sm-6">')
        if len(data): del data[0]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            
            title  = tmp[0]
            desc   = tmp[1]
            
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
            if category != 'video':
                params['category'] = category
                self.addDir(params)
            else: self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listMovies(self, cItem):
        printDBG("AlltubeTV.listMovies")
        if cItem.get('mtype', False):
            self._listItemsTab(cItem, '<div id="list-movie">', '<div class="col-sm-12">', '<div class="col-xs-3 col-md-2">', category='video')
        else:
            self._listItemsTab(cItem, '<div class="col-sm-8">', '<div class="col-sm-12">', '<div class="border-box clearfix">', category='video')
        
    def fillSeriesCache(self, url):
        printDBG("AlltubeTV.fillSeriesCache")
        self.seriesCache = {}
        self.seriesLetters = []
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = CParsingHelper.getDataBeetwenMarkers(data, '<ul class="term-list clearfix">', '</ul>', False)[1]
        data = re.compile('<li[^>]*?data-letter="([^"]+)"[^>]*?>[^<]*?<a[^>]*?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(data)
        for item in data:
            letter = item[0]
            url    = item[1]
            title  = item[2]
            if letter not in self.seriesCache:
                self.seriesCache[letter] = []
                self.seriesLetters.append({'title':letter,  'letter':letter})
            self.seriesCache[letter].append({'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url)})
        for idx in range(len(self.seriesLetters)):
            letter = self.seriesLetters[idx]['letter']
            self.seriesLetters[idx]['title'] = letter + ' [%d]' % len(self.seriesCache[letter]) 
            
    def listSeriesABC(self, cItem, category):
        printDBG("AlltubeTV.listSeriesABC")
        if 0 == len(self.seriesLetters):
            self.fillSeriesCache(self.MAIN_URL + 'seriale-online/')
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.seriesLetters, cItem)
        
    def listSeries(self, cItem, category):
        printDBG("AlltubeTV.listSeries")
        
        if 0 == len(self.seriesLetters):
            self.fillSeriesCache(self.MAIN_URL + 'seriale-online/')
        
        if 'all' == cItem['letter']:
            letters = self.seriesLetters
        else:
            letters = [cItem]
        for item in letters:
            letter = item['letter']
            tab = self.seriesCache.get(letter, [])
            cItem = dict(cItem)
            cItem['category'] = category
            self.listsTab(tab, cItem)
        
    def listAllSeries(self):
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 

        data = CParsingHelper.getDataBeetwenMarkers(data, '<ul class="term-list">', '</ul>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]

        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = ''
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( item ), 'url':self._getFullUrl(url), 'desc': '', 'icon':self._getFullUrl(icon)} )
            params['category'] = category
            self.addDir(params)
            
    def listSeasons(self, cItem, category):
        printDBG("AlltubeTV.listSeasons")
        self.episodesCache = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        seriesTitle =  self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="col-xs-12 col-sm-9">', '</h3>', False)[1] )
        if '' == seriesTitle: seriesTitle = cItem['title']    
        
        desc = self.cm.ph.getDataBeetwenMarkers(data, '<div class="custome-panel clearfix">', '</div>', False)[1]
        icon = self.cm.ph.getSearchGroups(desc, 'src="([^"]+?)"')[0]
        desc = self.cleanHtmlStr( desc )
        icon = self._getFullUrl( icon )
        
        if '' == icon: icon = cItem.get('icon', '')
        if '' == desc: desc = cItem.get('desc', '')
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="col-sm-4">', '<script>', False)[1]
        data = data.split('</ul>')
        for season in data:
            seasonTitle = self.cm.ph.getDataBeetwenMarkers(season, '<h3>', '</h3>', False)[1].strip()
            episodes = re.compile('<li[^>]*?class="episode"[^>]*?><a[^>]*?href="([^"]+?)">([^<]+?)</a></li>').findall( season )
            sort = True
            episodesList = []
            for item in episodes:
                try:
                    tmp = self.cm.ph.getSearchGroups(item[0], 'odcinek-([0-9]+?)-sezon-([0-9]+?)[^0-9]', 2)
                    season  = int(tmp[1])
                    episode = int(tmp[0])
                except:
                    printExc()
                    season  = 0
                    episode = 0
                    sort    = False
                episodesList.append( {'title': seriesTitle + ': ' + self.cleanHtmlStr( item[1] ), 'url':self._getFullUrl(item[0]), 'desc':  desc, 'icon':icon, 'season':season, 'episode':episode})
            if sort:
                episodesList.sort(key=lambda item: item['season']*1000 + item['episode'])#, reverse=True)
                #episodesList.reverse()
            if len(episodesList):
                params = dict(cItem)
                params.update({'category':category, 'season_idx':len(self.episodesCache), 'title':seasonTitle, 'desc':  desc, 'icon':icon})
                self.addDir(params)
                self.episodesCache.append(episodesList)
        
    def listEpisodes(self, cItem):
        printDBG("AlltubeTV.listEpisodes")
        seasonIdx = cItem['season_idx']
        
        if seasonIdx >= 0 and seasonIdx < len(self.episodesCache):
            episodesList = self.episodesCache[seasonIdx]
            self.listsTab(episodesList, cItem, 'video')
        
    def listRanking(self, cItem):
        printDBG("AlltubeTV.listRanking")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<tbody>', '</tbody>', False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<strong>', '</strong>', False)[1]
            if '' == title: title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            desc   = self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', False)[1]
            rank   = self.cm.ph.getSearchGroups(item, '>([0-9.]+?)<')[0]
            
            params = dict(cItem)
            params.update( {'title': self.cleanHtmlStr( title ), 'url':self._getFullUrl(url), 'desc': rank + ', ' + self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
            self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AlltubeTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        post_data = {'search':searchPattern}
        sts, data = self.cm.getPage(self.SRCH_URL, {}, post_data)
        if not sts: return
        
        if searchType == 'movies':
            key = 'film'
        elif searchType == 'series':
            key = 'serial'
            
        data = re.compile('<a[^>]*?href="([^"]*?/%s/[^"]*?)"[^>]*?>([^<]+?)<' % key).findall(data)
        for item in data:
            if item[0] == '': continue
            params = dict(cItem)
            params.update( {'title':self.cleanHtmlStr( item[1] ), 'url':self._getFullUrl(item[0])} )
            if searchType == 'movies':
                self.addVideo(params)
            elif searchType == 'series':
                params['category'] =  'list_seasons'
                self.addDir(params)
        return
        
        data = data.split('</a>')
        if len(data): del data[-1]
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]*?/%s/[^"]*?)"' % key)[0]
            if '' == url: continue
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            
            title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<b>', '</b>', False)[1] )
            if '' == title: title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0] )
            if '' == title: title = self.cm.ph.getSearchGroups(url, '/%s/([^"/]*?)[/"]' % key)[0].replace('-', ' ').capitalize()
            desc  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '</b>', '</p>', False)[1] )

            params = dict(cItem)
            params.update( {'title':title, 'url':self._getFullUrl(url), 'desc':desc, 'icon':self._getFullUrl(icon)} )
            if searchType == 'movies':
                self.addVideo(params)
            elif searchType == 'series':
                params['category'] =  'list_seasons'
                self.addDir(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("AlltubeTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tbody>', '</tbody>', False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            try:
                url  = self.cm.ph.getSearchGroups(item, 'data-iframe="([^"]+?)"')[0]
                url  = base64.b64decode(url)
                name = self.cleanHtmlStr(item)
                urlTab.append({'name':name, 'url':url, 'need_resolve':1})
            except:
                printExc()
        
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Movie4kTO.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        url = ''
        if self.MAIN_URL in baseUrl:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return []
            url = self.cm.ph.getDataBeetwenMarkers(data, 'src="', '"', False, False)[1]
        else:
            url = baseUrl
        
        if '' != url: 
            videoUrl = url
            if url.startswith('//'):
                videoUrl = 'http:' + videoUrl
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
        elif category == 'genres_movies':
            self.listFilters(self.currItem, 'category', 'list_version_filter')
        elif category == 'list_version_filter':
            self.listFilters(self.currItem, 'version', 'list_yer_filter')
        elif category == 'list_yer_filter':
            self.listFilters(self.currItem, 'year', 'list_movies')
        elif category == 'list_movies':
            self.listMovies(self.currItem)
        elif category == 'list_rank':
            self.listRanking(self.currItem)
    #SERIES
        elif category == 'cat_series':
            self.listsTab(self.SERIES_CAT_TAB, {'name':'category'})
        elif category == 'list_series_abc':
            self.listSeriesABC(self.currItem, 'list_series')
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_seasons')
        elif category == 'list_seasons':
            self.listSeasons(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
    #LATEST ADDED
        elif category == 'latest_added':
            self.listsTab(self.LAST_ADDED_TAB, {'name':'category'})
        elif category == 'latest_added_movies':
            self.listLatestAddedMovies(self.currItem)
        elif category == 'latest_added_series':
            self.listLatestAddedSeries(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, AlltubeTV(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('nocnyseans2logo.png')])
    
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
    '''
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title  = item.get('title', '')
            text   = item.get('text', '')
            images = item.get("images", [])
            retlist.append( ArticleContent(title = title, text = text, images =  images) )
        return RetHost(RetHost.OK, value = retlist)
    # end getArticleContent
    '''
    
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
