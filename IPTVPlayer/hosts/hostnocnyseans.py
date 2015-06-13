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
#config.plugins.iptvplayer.nocnyseans_premium  = ConfigYesNo(default = False)
#config.plugins.iptvplayer.nocnyseans_login    = ConfigText(default = "", fixed_size = False)
#config.plugins.iptvplayer.nocnyseans_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    #if config.plugins.iptvplayer.nocnyseans_premium.value:
    #    optionList.append(getConfigListEntry("  nocnyseans login:", config.plugins.iptvplayer.nocnyseans_login))
    #    optionList.append(getConfigListEntry("  nocnyseans hasło:", config.plugins.iptvplayer.nocnyseans_password))
    return optionList
###################################################


def gettytul():
    return 'nocnyseans.pl'

class NocnySeansPL(CBaseHostClass):
    MAIN_URL    = 'http://nocnyseans.pl/'
    SRCH_SERIES_URL    = MAIN_URL + 'seriale/search'
    SRCH_MOVIES_URL    = MAIN_URL + 'filmy/search'
    VIDEO_URL          = MAIN_URL + 'film/video'
    
    MAIN_CAT_TAB = [{'category':'genres_movies',      'title': _('Movies'), 'url':MAIN_URL+'filmy', 'icon':''},
                    {'category':'genres_series',      'title': _('Series'), 'url':MAIN_URL+'seriale', 'icon':''},
                    {'category':'search',             'title': _('Search'), 'search_item':True},
                    {'category':'search_history',     'title': _('Search history')} ]
                    
    MOVIES_CAT_TAB = [{'category':'list_movies',     'title':  'Ostatnio zaktualizowane', 'url':MAIN_URL+'tab/1/', 'icon':MAIN_URL + 'wp-content/themes/tvseries3/images/ostatnio-zaktualizowane.png'},
                      {'category':'list_movies',     'title':  'Nowe filmy',              'url':MAIN_URL+'tab/2/', 'icon':MAIN_URL + 'wp-content/themes/tvseries3/images/ostatnio-ogladane.png'},
                      {'category':'list_movies',     'title':  'Najpopularniejsze',       'url':MAIN_URL+'tab/3/', 'icon':MAIN_URL + 'wp-content/themes/tvseries3/images/najpopularniejsze.png'},
                      {'category':'list_movies',     'title':  'Najwyżej oceniane',       'url':MAIN_URL+'tab/4/', 'icon':MAIN_URL + 'wp-content/themes/tvseries3/images/najwyzej-oceniane.png'},
                      {'category':'year_movies',     'title':  'Rok produkcji',           'url':MAIN_URL+'rok-produkcji/'},
                      {'category':'genres_movies',   'title': _('Genres'),                'url':MAIN_URL+'gatunki/'},
                      {'category':'search',          'title': _('Search'), 'search_item':True},
                      {'category':'search_history',  'title': _('Search history')}                      ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'NocnySeansPL', 'cookie':'playtube.cookie'})

        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("NocnySeansPL.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listGenres(self, cItem, category):
        printDBG("NocnySeansPL.listMoviesGenres")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        data = CParsingHelper.getDataBeetwenMarkers(data, '<h2>Kategorie</h2>', '</ul>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]
        tmpList = []
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title  = self.cleanHtmlStr(item)
            tmpList.append({'title': title, 'url':self._getFullUrl(url)})
        if len(tmpList):
            tmpList.insert(0,  {'title': "**Wszystkie***"})
        
        mainItem = dict(cItem)
        mainItem.update({'category':category})
        self.listsTab(tmpList, mainItem)
            
    def _listItemsTab(self, cItem, category):
        printDBG("NocnySeansPL._listItemsTab")
        page = cItem.get('page', 1)
        url = cItem['url']
        tmp = url.split('?')
        if page > 1: tmp[0] += '/strona/%s' % page
        url = '?'.join(tmp)
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="list', '<footer>', False)[1]
        data = data.split('<div class="row">')
        if len(data): del data[0]
        
        if len(data) and ('/strona/{0}"'.format(page+1)) in data[-1]:
            nextPage = True
        else: nextPage = False
        
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = CParsingHelper.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1]
            desc   = CParsingHelper.getDataBeetwenMarkers(item, '<p class="description">', '</p>', False)[1]
            cats   = CParsingHelper.getDataBeetwenMarkers(item, '<p class="categories">', '</p>', False)[1]
            if cats.replace('Kategorie:', '').strip() != '': desc = cats + ', ' + desc
            
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
        printDBG("NocnySeansPL.listMovies")
        self._listItemsTab(cItem, 'video')
            
    def listSeries(self, cItem, category):
        printDBG("NocnySeansPL.listSeries")
        self._listItemsTab(cItem, category)
        
    def listEpisodes(self, cItem):
        printDBG("NocnySeansPL.listEpisodes")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="serial-series">', '<div class="film-bottom">', False)[1]
        
        # get seasons
        data = data.split('<div class="row">')
        if len(data): del data[0]
        episodesList = [] 
        for seanon in data:
            tmp = seanon.split('<div class="row row-episode">')
            seasonTitle = self.cleanHtmlStr(tmp[0].split('</div>')[0]).replace(':', ' ').strip()
            if len(tmp): del tmp[0]
            for item in tmp:
                episodesNum = self.cm.ph.getSearchGroups(item, '>([0-9]+?)<', 1)[0]
                titleAndUrl = self.cm.ph.getSearchGroups(item, '<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>', 2)
                title = seasonTitle + ':'
                if episodesNum != '' and (episodesNum+' ') not in titleAndUrl[1]:
                    title += ' {0}.'.format(episodesNum)
                title += ' {0}.'.format(titleAndUrl[1])
                episodesList.append({'title':title, 'url':titleAndUrl[0]})
        episodesList.reverse()
        self.listsTab(episodesList, cItem, 'video')
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("NocnySeansPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        url = urllib.quote(searchPattern)
        if searchType == 'movies':
            url = NocnySeansPL.SRCH_MOVIES_URL + '/' + url
        elif searchType == 'series':
            url = NocnySeansPL.SRCH_SERIES_URL + '/' + url
        else:
            printExc("NocnySeansPL.listSearchResult NO ENTRY")
            return
        cItem.update({'url':url})
        if searchType == 'movies':
            self.listMovies(cItem)
        elif searchType == 'series':
            self.listSeries(cItem, 'list_episodes')
        
    '''
    def getArticleContent(self, cItem):
        printDBG("NocnySeansPL.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div id="contentwrap">', '<div class="entry">', True)
        title = CParsingHelper.getDataBeetwenMarkers(data, '<h3 style="line-height: 30px;">', '</h3>', False)[1]
        icon = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
        
        desc = self.cm.ph.rgetDataBeetwenMarkers(data, 'block;">', '<div class="entry">', False)[1]
        #desc = self.cm.ph.getDataBeetwenMarkers(data, 'block;"><p>', '</p>', False)[1]
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[]}]
    '''
        
    def getLinksForVideo(self, cItem):
        printDBG("NocnySeansPL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return 
        
        oneLink = CParsingHelper.getDataBeetwenMarkers(data, 'id="film-content"', '</div>', False)[1]
        data = CParsingHelper.getDataBeetwenMarkers(data, 'class="tabpanel">', '<div class="film-bottom">', False)[1]
        versions = CParsingHelper.getDataBeetwenMarkers(data, 'role="tablist">', '</ul>', False)[1]
        versions = re.compile('href="#([^"]+?)"[^>]*?>([^<])</a>').findall(versions)
        printDBG('versions: %s' % versions)
        if 0:
            data = data.split('class="tab-pane container-fluid"')
            if len(data): del data[0]
            
            for item in data:
                # find version
                version = ''
                for ver in versions:
                    if ver[0] in item:
                        version = ver[1]
                        break
                links = item.split('<div class="row">')
                if len(links): del links[0]
                for link in links:
                    title = version 
                    hash = self.cm.ph.getSearchGroups(link, 'data-hash="([^"]+?)"', 1)[0]
                    title += ' ' + self.cleanHtmlStr( link )
                    url = strwithmeta(NocnySeansPL.VIDEO_URL, {'hash':hash, 'Referer':cItem['url']}) 
                    urlTab.append({'name':title, 'url':url})
        
        if 0 == len(urlTab):
            url = re.compile('src="([^"]+?)"', re.IGNORECASE).search(oneLink)
            if url:
                url = strwithmeta(url.group(1)) 
                title = ''
                if len(versions):
                    title = versions[0][1] + ' '
                    title += ' '
                title += self.up.getHostName(url)
                urlTab.append({'name':title, 'url':url})
        
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Movie4kTO.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        url = ''
        if baseUrl == NocnySeansPL.VIDEO_URL:
            HTTP_HEADER= { 'User-Agent':'Mozilla/5.0' }
            HTTP_HEADER['Referer'] = baseUrl.meta['Referer']
            sts, data = self.cm.getPage(NocnySeansPL.VIDEO_URL, {'header' : HTTP_HEADER}, {'hash':baseUrl.meta['hash']})
            if not sts: return urlTab
            printDBG(data)
            url = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"', 1)[0]
        else:
            url = baseUrl
        
        if '' != url: 
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
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
    #MOVIES
        elif category == 'genres_movies':
            self.listGenres(self.currItem, 'list_movies')
        elif category == 'list_movies':
            self.listMovies(self.currItem)
    #SERIES
        elif category == 'genres_series':
            self.listGenres(self.currItem, 'list_series')
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, NocnySeansPL(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('nocnyseanslogo.png')])
    
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
    '''
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
    '''
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Movies"), "movies"))
        searchTypesOptions.append((_("Series"), "series"))
    
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
