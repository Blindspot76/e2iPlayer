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
    optionList.append(getConfigListEntry(_("By default, sort by:"), config.plugins.iptvplayer.movieshdco_sortby))
    return optionList
###################################################


def gettytul():
    return 'movieshd.co'

class MoviesHDCO(CBaseHostClass):
    MAIN_URL    = 'http://movieshd.co/'
    #SRCH_SERIES_URL    = MAIN_URL + 'seriale/search'
    SRCH_MOVIES_URL    = MAIN_URL + 'page/{page}/?s='
    
    MAIN_CAT_TAB = [{'category':'genres_movies',      'title': _('Movies'),          'url':MAIN_URL + 'genre', 'icon':'http://pbs.twimg.com/profile_images/545684030885093377/Hfd166Di.jpeg'},
                    #{'category':'latest_series',      'title': _('Latest series'), 'url':MAIN_URL, 'icon':''},
                    #{'category':'genres_series',      'title': _('Series'), 'url':MAIN_URL+'seriale', 'icon':''},
                    {'category':'search',             'title': _('Search'), 'search_item':True},
                    {'category':'search_history',     'title': _('Search history')} ]
                    
    MOVIES_SORT_BY = [{'title':_('Lastest'),     'sort_by':'date'  },
                      {'title':_('most viewed'), 'sort_by':'views' },
                      {'title':_('longest'),     'sort_by':'duree' },
                      {'title':_('top rated'),   'sort_by':'rate'  },
                      {'title':_('random'),      'sort_by':'random'},
                     ]
    
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'MoviesHDCO', 'cookie':'movieshdco.cookie'})
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        
        if self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("MoviesHDCO.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listGenres(self, cItem, category):
        printDBG("MoviesHDCO.listMoviesGenres")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        data = CParsingHelper.getDataBeetwenMarkers(data, '<ul class="listing-cat">', '</ul>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]
        tmpList = []
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cleanHtmlStr(item)
            tmpList.append({'title': title, 'icon':self._getFullUrl(icon), 'url':self._getFullUrl(url)+'/page/{page}?display=tube&filtre={sort_by}'})
        if len(tmpList):
            tmpList.insert(0,  {'title': _("***Any***"), 'url':self.MAIN_URL+'/page/{page}?display=tube&filtre={sort_by}'})
        
        mainItem = dict(cItem)
        mainItem.update({'category':category})
        self.listsTab(tmpList, mainItem)
        
    def addSortBy(self, cItem, category):
        printDBG("MoviesHDCO.addSortBy")
        mainItem = dict(cItem)
        mainItem.update({'category':category})
        self.listsTab(self.MOVIES_SORT_BY, mainItem)
        
    def listMovies(self, cItem):
        printDBG("MoviesHDCO.listMovies")
        
        page    = cItem.get('page', 1)
        sort_by = cItem.get('sort_by', config.plugins.iptvplayer.movieshdco_sortby.value)
        url     = cItem['url'].format(page=page, sort_by=sort_by) 
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if '"nextLink":"' in data:
            nextPage = True
        else: nextPage = False
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<ul class="listing-videos listing-tube">', '</ul>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]

        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'title': title, 'url':self._getFullUrl(url), 'icon':self._getFullUrl(icon)})
            self.addVideo(params)
            
        if nextPage:
            params = dict(cItem)
            params.update({'title': _('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("MoviesHDCO.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        if searchType == 'series':
            pass
        else:
            params = dict(cItem)
            params['url'] = self.SRCH_MOVIES_URL + urllib.quote_plus(searchPattern)
            self.listMovies(params)
        
    def getArticleContent(self, cItem):
        printDBG("MoviesHDCO.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<table id="imdbinfo">', '</table>', False)
        if not sts: return retTab
        
        tmp = data.split('</tr>')
        if len(tmp) < 2: return retTab
        
        title = self.cleanHtmlStr(tmp[0])
        if '' == title: icon = self.cm.ph.getSearchGroups(tmp[1], 'alt="([^"]+?)"')[0]
        icon  = self.cm.ph.getSearchGroups(tmp[1], 'src="([^"]+?)"')[0]
        desc  = self.cm.ph.getDataBeetwenMarkers(tmp[1], '<b>Plot:</b>', '</td>', False)[1]
        
        otherInfo = {}
        tmpTab = [{'mark':'<b>Rating:</b>',   'key':'rating'},
                  {'mark':'<b>Director:</b>', 'key':'director'},
                  {'mark':'<b>Writer:</b>',   'key':'writer'},
                  {'mark':'<b>Stars:</b>',    'key':'stars'},
                  {'mark':'<b>Runtime:</b>',  'key':'duration'},
                  {'mark':'<b>Rated:</b>',    'key':'rated'},
                  {'mark':'<b>Genre:</b>',    'key':'genre'},
                  {'mark':'<b>Released:</b>', 'key':'released'},
        ]
        for item in tmpTab:
            val = self.cm.ph.getDataBeetwenMarkers(tmp[1], item['mark'], '</td>', False)[1]
            if '' != val: otherInfo[item['key']] =  self.cleanHtmlStr(val)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':otherInfo}]
        
    def getLinksForVideo(self, cItem):
        printDBG("MoviesHDCO.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="video-embed">', '</div>', False)[1]
        oneLink = CParsingHelper.getDataBeetwenMarkers(data, 'data-rocketsrc="', '"', False)[1]
        if oneLink.startswith('//'):
            oneLink = 'http:' + oneLink
        
        if 'videomega.tv/validatehash.php?' in oneLink:
            sts, data = self.cm.getPage(oneLink, {'header':{'Referer':cItem['url'], 'User-Agent':'Mozilla/5.0'}})
            if not sts: return urlTab
            data = self.cm.ph.getSearchGroups(data, 'ref="([^"]+?)"')[0]
            if '' == data: return urlTab
            oneLink = 'http://videomega.tv/view.php?ref={0}&width=700&height=460&val=1'.format(data)
            
        if '' == oneLink: return urlTab
        name = self.up.getHostName(oneLink)
        urlTab.append({'name':name, 'url':oneLink, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Movie4kTO.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        if '' != baseUrl: 
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
        elif category == 'genres_movies':
            self.listGenres(self.currItem, 'add_movies_sort_by')
        elif category == 'add_movies_sort_by':
            self.addSortBy(self.currItem, 'list_movies')
        elif category == 'list_movies':
            self.listMovies(self.currItem)
    #SERIES
        #elif category == 'genres_series':
        #    self.listGenres(self.currItem, 'list_series')
        #elif category == 'list_series':
        #    self.listSeries(self.currItem, 'list_episodes')
        #elif category == 'list_episodes':
        #    self.listEpisodes(self.currItem)
        #elif category == 'latest_series':
        #    self.listLatestSeries(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, MoviesHDCO(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('movieshdcologo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

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
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)

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
        #searchTypesOptions.append((_("Movies"), "movies"))
        #searchTypesOptions.append((_("Series"), "series"))
    
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
