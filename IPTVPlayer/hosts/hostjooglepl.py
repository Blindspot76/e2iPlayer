# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.sha1Hash import SHA1
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
from binascii import hexlify
import re
import urllib
import time
import random
try:    import simplejson as json
except: import json
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
    return 'joogle.pl'

class JooglePL(CBaseHostClass):
    MAIN_URL   = 'http://joogle.pl/'
    SEARCH_URL = MAIN_URL + 'szukaj'
    FILMS_URL  = MAIN_URL + 'filmy-online/' 
    SERIES_URL = MAIN_URL + 'seriale-online/'
    MAIN_CAT_TAB = [{'category':'films_list_categories', 'title':_('Filmy'),   'url': FILMS_URL},
                    {'category':'series_list_abc',       'title':_('Seriale'), 'url': SERIES_URL},
                    {'category':'search',                'title':_('Search'), 'search_item':True},
                    {'category':'search_history',        'title':_('Search history')} ]
    
    def __init__(self):
        printDBG("JooglePL.__init__")
        CBaseHostClass.__init__(self, {'history':'Joogle.pl'})
        self.cacheFilters = []
        self.cacheSeries = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        return url

    def listsTab(self, tab, cItem):
        printDBG("JooglePL.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def listFilmsCategories(self, cItem, category):
        printDBG("JooglePL.listFilmsCategories")
        self.cacheFilters = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        def _getFilters(data, m1, m2):
            data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
            data = re.compile('data-id="([0-9]+?)"[^>]*?>([^<]+?)<').findall(data)
            if len(data):
                data.insert(0, ('all', _('--Wszystkie--')))
            return data

        catsData = _getFilters(data, '<ul id="filter-category">', '</ul>')
        for item in catsData:
            params = dict(cItem)
            params.update({'category':category, 'title':item[1]})
            if 'all' != item[0]: params['cat_id'] = item[0]
            self.addDir(params)
            
        # prepare YERS filers to not request once again web page
        self.cacheFilters = _getFilters(data, '<ul id="filter-year">', '</ul>')

    def listFilmsYears(self, cItem, category):
        printDBG("JooglePL.listFilmsYers")
        
        for item in self.cacheFilters:
            params = dict(cItem)
            params.update({'category':category, 'title':item[1]})
            if 'all' != item[0]: params['year_id'] = item[0]
            self.addDir(params)
 
    def listFilms(self, cItem):
        printDBG("JooglePL.listFilms")
        url = JooglePL.FILMS_URL
        if 'cat_id' in cItem: url += 'kategoria[%s]+' %  cItem['cat_id']
        if 'year_id' in cItem: url += 'rok[%s]+' %  cItem['year_id']
        if 'page'in cItem: url += 'strona[%s]+' % cItem['page']
        page = cItem.get('page', 1)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        if ('strona[%s]+' % page) in data:
            haveNextPage = True
        else: haveNextPage = False
        
        errorMessage = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="alert alert-danger">', '</div>', False)[1] )
        if len(errorMessage): SetIPTVPlayerLastHostError(errorMessage)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'box-with-movies">', '<div class="row">', False)[1]
        data = data.split('box-with-movies">')
       
        for item in data:
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="title">', '</div>', False)[1] )
            info   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="info">', '</div>', False)[1] )
            desc   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="description">', '</div>', False)[1] )
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':'%s [%s]' %(title, info), 'url':self._getFullUrl(url), 'desc':desc, 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
                
        if haveNextPage:
            params = dict(cItem)
            params.update({'title':_("Następna strona"), 'page':page+1})
            self.addDir(params)
            
    def listSearchFilms(self, cItem, searchPattern):
        searchPattern = urllib.quote_plus(searchPattern)
        post_data = {'search':searchPattern}
        sts, data = self.cm.getPage(JooglePL.SEARCH_URL, {}, post_data)
        if not sts: return
        data = data.split('</a>')
        for item in data:
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            if '' == title: title = str.capitalize( url.split('/')[-1].replace('-', ' ') )
            desc   =  ''
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'desc':desc, 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
                
    def listSeriesABC(self, cItem, category):
        printDBG("JooglePL.listFilms")
        seriesABC = self._fillSeriesCache(cItem['url'])
        if len(seriesABC):
            params = dict(cItem)
            params.update({'category':category, 'title':_('--Wszystkie--'), 'cat_id':'all'})
            self.addDir(params)
            for item in seriesABC:
                params = dict(cItem)
                params.update({'category':category, 'title':item + (' [%d]' % len(self.cacheSeries[item]) ), 'cat_id':item})
                self.addDir(params)

    def _fillSeriesCache(self, url):
        printDBG("JooglePL._fillSeriesCache")
        sts, data = self.cm.getPage(url)
        if not sts: return []
        self.cacheSeries = {'all':[]}
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="list">', '</ul>', False)[1]
        data = data.split('</li>')
        seriesABC = []
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="(http[^"]+?)"')[0]
            title = self.cleanHtmlStr(item)
            
            try: 
                cat_id = ''
                if not self.cm.ph.isalpha(title, 0):
                    cat_id = '0-9'
                else:
                    cat_id = self.cm.ph.getNormalizeStr(title, 0).upper()
                    
                if cat_id not in seriesABC:
                    seriesABC.append(cat_id)
                
                if cat_id not in self.cacheSeries:
                    self.cacheSeries[cat_id] = []
                self.cacheSeries[cat_id].append({'title':title, 'url':url})
                self.cacheSeries['all'].append({'title':title, 'url':url})
            except: 
                printExc()
        return seriesABC
    
    def listSeries(self, cItem, category):
        printDBG("JooglePL.listSeries")
        series = self.cacheSeries.get(cItem['cat_id'], [])
        for item in series:
            params = dict(cItem)
            params.update({'category':category, 'title':item['title'], 'url':item['url']})
            self.addDir(params)
            
    def listEpisodes(self, cItem):
        printDBG("JooglePL.listEpisodes")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        headerData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="poster">', '<ul class="episode-list">', False)[1]
        icon = self._getFullUrl( self.cm.ph.getSearchGroups(headerData, 'src="([^"]+?)"')[0] )
        desc = self.cleanHtmlStr(headerData)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="episode-list">', '</ul>', False)[1]
        data = data.split('</li>')
        season = ''
        for item in data:
            if 'class="season"' in item:
                season = self.cleanHtmlStr(item + '</li>')
            elif 'class="episode"' in item:
                title = season + ' ' + self.cleanHtmlStr(item + '</li>')
                url   =  self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
                params = dict(cItem)
                params.update( {'title':title, 'url':url, 'desc':desc, 'icon':icon} )
                self.addVideo(params)
                
    def listSearchSeries(self, cItem, searchPattern, category):
        keywordList = self.cm.ph.getNormalizeStr(searchPattern).upper().split(' ')
        keywordList = set(keywordList)
        if len(keywordList):
            series = self.cacheSeries.get('all', [])
            if 0 == len(series):
                self._fillSeriesCache(JooglePL.SERIES_URL)
                series = self.cacheSeries.get('all', [])
            for item in series:
                txt = self.cm.ph.getNormalizeStr( item['title'] ).upper()
                txtTab = txt.split(' ')
                matches = 0
                for word in keywordList:
                    if word in txt: matches += 1
                    if word in txtTab: matches += 10
                if 0 < matches:
                    params = dict(cItem)
                    params.update({'category':category, 'title':item['title'], 'url':item['url'], 'matches':matches})
                    self.addDir(params)
            self.currList.sort(key=lambda item: item['matches'], reverse=True)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("JooglePL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        if 'filmy' == searchType:
            self.listSearchFilms(cItem, searchPattern)
        else:
            self.listSearchSeries(cItem, searchPattern, 'series_list_episodes')
    
    def getLinksForVideo(self, cItem):
        printDBG("JooglePL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player-content">', '</div>', True)
        if not sts:
            SetIPTVPlayerLastHostError(_("Cannot find player content"))
            return []
        playerUrl = self._getFullUrl( self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0] )
        if playerUrl == '': 
            SetIPTVPlayerLastHostError(self.cleanHtmlStr(data))
            return []
        sts, data = self.cm.getPage(playerUrl, {'Referer':cItem['url']})
        if not sts: return []
        
        directVideoUrl = self.cm.ph.getSearchGroups(data, 'file=(http[^"]+?)"')[0]
        if directVideoUrl != '': 
            urlTab.append({'name':'Direct', 'url':directVideoUrl})
        else:
            proxyUrl = self.cm.ph.getSearchGroups(data, 'proxy.link=(http[^"]+?)"')[0]
            if proxyUrl != '': urlTab.extend(self.up.getVideoLinkExt(proxyUrl))
            
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('JooglePL.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "JooglePL.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(JooglePL.MAIN_CAT_TAB, {'name':'category'})
    #FILMS
        elif 'films_list_categories' == category:
            self.listFilmsCategories(self.currItem, 'films_list_years')
        elif 'films_list_years' == category:
            self.listFilmsYears(self.currItem, 'films_list')
        elif 'films_list' == category:
            self.listFilms(self.currItem)
    #SERIES
        elif 'series_list_abc' == category:
            self.listSeriesABC(self.currItem, 'series_list_series')
        elif 'series_list_series' == category:
            self.listSeries(self.currItem, 'series_list_episodes')
        elif 'series_list_episodes' == category:
            self.listEpisodes(self.currItem)
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
        CHostBase.__init__(self, JooglePL(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('jooglepllogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] not in ['audio', 'video']:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            name = self.host.cleanHtmlStr( item["name"] )
            url  = item["url"]
            retlist.append(CUrlItem(name, url, need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append(("Filmy",  "filmy"))
        searchTypesOptions.append(("Seriale","seriale"))
        
        for cItem in cList:
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
                
            title       =  self.host.cleanHtmlStr( cItem.get('title', '') )
            description =  self.host.cleanHtmlStr( cItem.get('desc', '') )
            icon        =  self.host.cleanHtmlStr( cItem.get('icon', '') )
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)

        return hostList
    # end convertList

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
