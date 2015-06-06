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
   
def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'movie4k.to'

class Movie4kTO(CBaseHostClass):
    MAIN_URL    = 'http://www.movie4k.to/'
    SRCH_URL    = MAIN_URL + 'searchAutoCompleteNew.php?search='
    GENRES_URL  = MAIN_URL + 'movies-genre-%s-{0}.html'
    ALL_ABC_URL = MAIN_URL + 'movies-all-%s-{0}.html'
    MAIN_CAT_TAB = [{'category':'cat_movies',            'title': _('Movies'),     'icon':''},
                    #{'category':'cat_tv_shows',          'title': _('TV shows'),   'icon':''},
                    {'category':'search',                'title': _('Search'), 'search_item':True},
                    {'category':'search_history',        'title': _('Search history')} ]
                    
    MOVIES_CAT_TAB = [{'category':'cat_movies_list1',    'title': _('Cinema movies'),  'icon':'', 'url':MAIN_URL+'index.php'},
                      {'category':'cat_movies_list2',    'title': _('Latest updates'), 'icon':'', 'url':MAIN_URL+'movies-updates.html' },
                      {'category':'cat_movies_abc',      'title': _('All movies'),     'icon':'', 'url':MAIN_URL+'movies-all.html' },
                      {'category':'cat_movies_genres',   'title': _('Genres'),         'icon':'', 'url':MAIN_URL+'genres-movies.html' } ]

    def __init__(self):
        printDBG("Movie4kTO.__init__")
        CBaseHostClass.__init__(self, {'history':'Movie4kTO', 'cookie':'Movie4kTO.cookie'})
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem):
        printDBG("Movie4kTO.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def listsMovies1(self, cItem):
        printDBG("Movie4kTO.listsMovies1")
        url  = self._getFullUrl(cItem['url'])
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="maincontent2">', '</body>', False)
        if not sts: return
        data = data.split('<div id="maincontent2">')
        
        for item in data:
            sts, item = self.cm.ph.getDataBeetwenMarkers(item, '<div id="xline">', '<div id="xline">', False)
            if not sts: continue
            
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            
            title  = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            if '' == title: self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            lang = self.cm.ph.getSearchGroups(item, 'watch in ([^"]+?)"')[0] 
            if '' != lang: title += ' ({0})'.format(lang)
            
            desc  = self.cm.ph.getDataBeetwenMarkers(item, 'class="info">', '</div>', False)[1]

            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
            
    def listsMovies2(self, cItem):
        printDBG("Movie4kTO.listsMovies2")
        page = cItem.get('page', 1)
        baseUrl  = self._getFullUrl(cItem['url'])
        if '{0}' in baseUrl: url = baseUrl.format(page)
        else: url = baseUrl
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        if '{0}' in baseUrl:
            tmp = baseUrl.format(page+1).split('/')[-1]
            if tmp in data: nextPage = True
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<TD width="550" id="tdmovies">', '</TABLE>', False)
        if not sts: return
        
        descRe = re.compile('<TD[^>]+?>(.+?)</TD>', re.DOTALL)
        data = data.split('<TD width="550" id="tdmovies">')
        for item in data:
            
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cm.ph.getSearchGroups(item, '<a [^>]+?>([^<]+?)</a>')[0]
            desc = ''
            try: 
                tmp = descRe.findall(item)
                for t in tmp: 
                    if 'watch on' not in t: desc += ' ' + t 
                desc = desc.replace('&nbsp;', ' ')
            except: printExc()
            
            lang = self.cm.ph.getSearchGroups(item, 'src="/img/([^"]+?)_small.png"')[0].replace('us', '').replace('_', '').replace('flag', '')
            if '' == lang: lang = 'eng'
            if '' != lang: title += ' ({0})'.format(lang)

            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':''} )
                self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_("Next page"), 'page':page+1} )
            self.addDir(params)
        
    def listsMoviesABC(self, cItem, category):
        printDBG("Movie4kTO.listsMoviesABC")
        TAB = ['#1','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','R','S','T','U','V','W','X','Y','Z']
        for item in TAB:
            url = Movie4kTO.ALL_ABC_URL % item[-1]
            params = dict(cItem)
            params.update( {'title':item[0], 'url':self._getFullUrl(url), 'category': category} )
            self.addDir(params)
        
    def listsMoviesGenres(self, cItem, category):
        printDBG("Movie4kTO.listsMoviesGenres")
        url  = self._getFullUrl(cItem['url'])
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<TABLE id="tablemovies" cellpadding=5 cellspacing=5>', '</TABLE>', False)
        if not sts: return
        
        data = data.split('</TR>')
        if len(data): del data[-1]
        for item in data:
            
            genreID = self.cm.ph.getSearchGroups(item, '"movies-genre-([0-9]+?)-')[0]
            title   = self.cleanHtmlStr( item ).replace('Random', '')

            if '' != genreID and '' != title:
                url = Movie4kTO.GENRES_URL % genreID
                params = dict(cItem)
                params.update( {'title':title, 'url':self._getFullUrl(url), 'category': category} )
                self.addDir(params)
        
    def listCategories(self, cItem, category):
        printDBG("Movie4kTO.listCategories")
        sts, data = self.cm.getPage(Movie4kTO.MAIN_URL)
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
        printDBG("Movie4kTO.listVideosFromCategory")
        page = cItem.get('page', 1)
        url  = cItem['url'] + "/{0},{1}.html".format(page, config.plugins.iptvplayer.Movie4kTO_sort.value)
        
        sts, data = self.cm.getPage(url)
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
        printDBG("Movie4kTO.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        url = Movie4kTO.SRCH_URL + urllib.quote(searchPattern)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        data = data.split('</TD>')
        if len(data): del data[-1]
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if '' != url:
                params = dict(cItem)
                params.update( {'name':'category', 'category':'cat_movies_list2', 'title':self.cleanHtmlStr( item ), 'url':self._getFullUrl(url)} )
                self.addDir(params)
        
    def getArticleContent(self, cItem):
        printDBG("Movie4kTO.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        title = self.cm.ph.getSearchGroups(data, 'title" content="([^"]+?)"')[0]
        icon = self.cm.ph.getSearchGroups(data, 'image" content="([^"]+?)"')[0]
        desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="moviedescription">', '</div>', False)[1] )
        
        return [{'title':title, 'text':desc, 'images':[]}]
    
    def getLinksForVideo(self, cItem):
        printDBG("Movie4kTO.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        
        if 'links = new Array();' in data:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'links = new Array();', '</table>', False)
            if not sts: return urlTab
            data = data.replace('\\"', '"')
            data = re.compile(']="(.+?)";', re.DOTALL).findall(data)
        else:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<tr id="tablemoviesindex2">', '</table>', False)
            if not sts: return urlTab
            data = data.split('<tr id="tablemoviesindex2">')

        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = self.cleanHtmlStr( item )
            title += ' ' + self.cm.ph.getSearchGroups(item, '/img/smileys/([0-9]+?)\.gif')[0]
            
            if '' != url and '' != title:
                urlTab.append({'name':title, 'url':self._getFullUrl(url)})
            
        return urlTab
        
    def getVideoLinks(self, url):
        printDBG("Movie4kTO.getVideoLinks [%s]" % url)
        urlTab = []
        
        sts, data = self.cm.getPage(url)
        if not sts: return urlTab
        
        videoUrl = self.cm.ph.getSearchGroups(data, '<a target="_blank" href="([^"]+?)"')[0]
        urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Movie4kTO.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Movie4kTO.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

    #MAIN MENU
        if None == name:
            self.listsTab(Movie4kTO.MAIN_CAT_TAB, {'name':'category'})
    #MOVIES
        elif 'cat_movies' == category:
            self.listsTab(Movie4kTO.MOVIES_CAT_TAB, self.currItem)
        elif 'cat_movies_list1' == category:
            self.listsMovies1(self.currItem)
        elif 'cat_movies_list2' == category:
            self.listsMovies2(self.currItem)
        elif 'cat_movies_genres' == category:
            self.listsMoviesGenres(self.currItem, 'cat_movies_list2')
        elif 'cat_movies_abc' == category:
            self.listsMoviesABC(self.currItem, 'cat_movies_list2')
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
        CHostBase.__init__(self, Movie4kTO(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('movie4ktologo.png')])
    
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
            title  = item.get('title', '')
            text   = item.get('text', '')
            images = item.get("images", [])
            retlist.append( ArticleContent(title = title, text = text, images =  images) )
        return RetHost(RetHost.OK, value = retlist)
    # end getArticleContent
    
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"), "filmy"))
        #searchTypesOptions.append(("Seriale", "seriale"))
    
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
