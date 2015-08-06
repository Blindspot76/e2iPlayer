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
config.plugins.iptvplayer.anyfilmspl_sortby   = ConfigSelection(default = "1", choices = [("1", _("Added date")), ("2", _("Rating")), ("3", _("View count"))]) 

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Sort by:"), config.plugins.iptvplayer.anyfilmspl_sortby))
    return optionList
###################################################


def gettytul():
    return 'anyfilms.pl'

class AnyFilmsPL(CBaseHostClass):
    MAIN_URL    = 'http://anyfilms.pl/'
    SRCH_URL    = MAIN_URL + '?s='
    
    MAIN_CAT_TAB = [{'category':'cat_movies',      'title': _('Movies'), 'icon':'http://funkyimg.com/i/Xcji.png'},
                    #{'category':'cat_series',      'title': _('Series'), 'icon':'http://www.tvseriesonline.pl/wp-content/themes/tvseries3/images/tvseriesonline.png'},
                    {'category':'search',          'title': _('Search'), 'search_item':True},
                    {'category':'search_history',  'title': _('Search history')} ]
                    
    MOVIES_CAT_TAB = [{'category':'list_movies',     'title':  'Ostatnio zaktualizowane', 'url':MAIN_URL+'tab/1/', 'icon':MAIN_URL + 'wp-content/themes/tvseries3/images/ostatnio-zaktualizowane.png'},
                      {'category':'list_movies',     'title':  'Nowe filmy',              'url':MAIN_URL+'tab/2/', 'icon':MAIN_URL + 'wp-content/themes/tvseries3/images/ostatnio-ogladane.png'},
                      {'category':'list_movies',     'title':  'Najpopularniejsze',       'url':MAIN_URL+'tab/3/', 'icon':MAIN_URL + 'wp-content/themes/tvseries3/images/najpopularniejsze.png'},
                      {'category':'list_movies',     'title':  'Najwyżej oceniane',       'url':MAIN_URL+'tab/4/', 'icon':MAIN_URL + 'wp-content/themes/tvseries3/images/najwyzej-oceniane.png'},
                      {'category':'year_movies',     'title':  'Rok produkcji',           'url':MAIN_URL+'rok-produkcji/'},
                      {'category':'genres_movies',   'title': _('Genres'),                'url':MAIN_URL+'gatunki/'},
                      {'category':'search',          'title': _('Search'), 'search_item':True},
                      {'category':'search_history',  'title': _('Search history')}                      ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'AnyFilmsPL', 'cookie':'playtube.cookie'})

        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem):
        printDBG("AnyFilmsPL.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def listMovies(self, cItem, m1='<article id="post'):
        printDBG("AnyFilmsPL.listMovies")
        
        page = cItem.get('page', 1)
        url = cItem['url']
        tmp = url.split('?')
        if page > 1: tmp[0] += '/page/%s' % page
        url = '?'.join(tmp)
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        data = CParsingHelper.getDataBeetwenMarkers(data, m1, '<div id="right-column">', False)[1]
        data = data.split(m1)
        
        if len(data) > 0 and ('page/{0}/'.format(page+1)) in data[-1]:
            nextPage = True
        else: nextPage = False
        langReObj = re.compile('src="[^"]+?/([^/]+?)\.png"[^>]*?class="catlang"')
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        for item in data:
            desc    = CParsingHelper.getDataBeetwenMarkers(item, '<div class="over">', '<div class="over-down">', False)[1]
            tmp    = CParsingHelper.getDataBeetwenMarkers(item, '<div class="over-down">', '</div>', False)[1]
            url    = self.cm.ph.getSearchGroups(tmp, 'href="([^"]+?)"')[0]
            title  = self.cleanHtmlStr(tmp)
            langs  = langReObj.findall(tmp)
            if 0 < len(langs): title += ' [{0}]'.format(', '.join(langs))
            tmp    = item.split('<div style="display')[-1]
            icon   = self.cm.ph.getSearchGroups(tmp, 'src="([^"]+?\.jpg)"')[0]
            
            date  = CParsingHelper.getSearchGroups(tmp, 'data.png"[^>]*?>([^<]+?)</div>')[0]
            views = CParsingHelper.getSearchGroups(tmp, 'odslon.png"[^>]*?>([^<]+?)</div>')[0]
            desc  = 'Data: {0}, Wyświetleń: {1}, {2}'.format(date, views, desc)

            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title': title, 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc ), 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
            
    def listMovies2(self, cItem, m1='#f5f5f5"  id="post'):
        printDBG("AnyFilmsPL.listMovies2")
        page = cItem.get('page', 1)
        url = cItem['url']
        if 'rok' not in url:
            url += '/sort/%s' % config.plugins.iptvplayer.anyfilmspl_sortby.value
        if page > 1: url += '/page/%s' % page
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        data = CParsingHelper.getDataBeetwenMarkers(data, m1, '<div id="right-column">', False)[1]
        data = data.split(m1)
        
        if len(data) > 0 and ('page/{0}/'.format(page+1)) in data[-1]:
            nextPage = True
        else: nextPage = False
        langReObj = re.compile('src="[^"]+?/([^/]+?)\.png"')
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        for item in data:
            tmp    = item.split('display: block;">')
            icon   = self.cm.ph.getSearchGroups(tmp[0], 'src="([^"]+?\.jpg)"')[0]
            url    = self.cm.ph.getSearchGroups(tmp[1], 'href="([^"]+?)"')[0]
            title  = self.cleanHtmlStr(tmp[1]+'>')
            desc  = '> '.join( tmp[1:] )
            langs = CParsingHelper.getDataBeetwenMarkers(tmp[-1], '<b>Dostępne wersje:', '</div>', False)[1]
            langs  = langReObj.findall(langs)
            if 0 < len(langs): title += ' [{0}]'.format(', '.join(langs))

            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'title': title, 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc.replace('Loading...', '') ), 'icon':self._getFullUrl(icon)} )
                self.addVideo(params)
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnyFilmsPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem.update({'url':AnyFilmsPL.SRCH_URL + urllib.quote(searchPattern)})
        self.listMovies(cItem)
        
    def getArticleContent(self, cItem):
        printDBG("AnyFilmsPL.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div id="contentwrap">', '<div class="entry">', True)
        title = CParsingHelper.getDataBeetwenMarkers(data, '<h3 style="line-height: 30px;">', '</h3>', False)[1]
        icon = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
        
        desc = self.cm.ph.rgetDataBeetwenMarkers(data, 'block;">', '<div class="entry">', False)[1]
        #desc = self.cm.ph.getDataBeetwenMarkers(data, 'block;"><p>', '</p>', False)[1]
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[]}]
        
    def getLinksForVideo(self, cItem):
        printDBG("AnyFilmsPL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts:
            # no cookie file?
            sts, data = self.getPage(cItem['url'])
            if not sts: return urlTab

        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'id="kontener">', '</ul>', False)
        if not sts: return urlTab
        data = data.split('<li ')
        if len(data): del data[0]
        
        reLinksObj = re.compile('href="([^"]+?)"')
        for langs in data:
            lang = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(langs, '<h5>', '</h5>', False)[1] )
            
            tmp = reLinksObj.findall(langs)
            for item in tmp:
                if '://' not in item: continue
                urlTab.append({'name':'{0}: {1}'.format(lang, self.up.getHostName(item)), 'url':item})
        return urlTab
        
    def listYearsCat(self, cItem, category):
        printDBG("AnyFilmsPL.listYearsCat [%s]" % cItem)
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="entry">', '<div id="right-column">', False)[1]
        data = re.compile('<a[^>]*?href="([^"]+?)"[^>]*?title="([^"]+?)"').findall(data)
        
        for item in data:
            params = dict(cItem)
            params.update({'category':category, 'title':self.cleanHtmlStr(item[1]), 'url':self._getFullUrl(item[0]) })
            self.addDir(params)
        
    def lisMovieGenres(self, cItem, category):
        printDBG("AnyFilmsPL.lisMovieGenres [%s]" % cItem)
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '#f5f5f5">', '<div id="right-column">', False)[1]
        data = data.split('#f5f5f5">')
        
        for idx in range(len(data)):
            item   = data[idx] 
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?\.jpg)"')[0]
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            tmp    = item.split('<div style="line-height: 1;">') 
            title  = self.cleanHtmlStr(tmp[0])
            itemCounts = self.cm.ph.getSearchGroups(item, 'Liczba filmów\:[^0-9]+?([0-9]+?)[^0-9]')[0]
            if len(itemCounts): title += ' [{0}]'.format(itemCounts)
            desc  = tmp[1]
            if idx < (len(data)-1): desc += '>'
            
            if '' != url and '' != title:
                params = dict(cItem)
                params.update( {'category':category, 'title': title, 'url':self._getFullUrl(url), 'desc': self.cleanHtmlStr( desc.replace('Loading...', '') ), 'icon':self._getFullUrl(icon)} )
                self.addDir(params)
        
    def getVideoLinks(self, url):
        printDBG("Movie4kTO.getVideoLinks [%s]" % url)
        urlTab = []
        
        videoUrl = url
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
        #if name == None:
        #    self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})  
        #el
        if category == "cat_movies" or name == None:
            self.listsTab(self.MOVIES_CAT_TAB, self.currItem)         
    #MOVIES LIST
        elif category == "list_movies":
            self.listMovies(self.currItem)
        elif category == "list_movies2":
            self.listMovies2(self.currItem)
    #CATEGORIES
        elif category == "year_movies":
            self.listYearsCat(self.currItem, "list_movies2")
        elif category == "genres_movies":
            self.lisMovieGenres(self.currItem, "list_movies2")
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
        CHostBase.__init__(self, AnyFilmsPL(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('anyfilmslogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
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
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)

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
