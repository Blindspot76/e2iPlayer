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
import string
try:    import json
except Exception: import simplejson as json
from time import sleep
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
    return 'movieshd.tv'

class MoviesHDCO(CBaseHostClass):
    MAIN_URL    = 'http://movieshd.tv/'
    #SRCH_SERIES_URL    = MAIN_URL + 'seriale/search'
    SRCH_MOVIES_URL    = MAIN_URL + 'page/{page}?s='
    
    MAIN_CAT_TAB = [{'category':'genres_movies',      'title': _('Movies'),          'url':MAIN_URL + 'categories', 'icon':'http://pbs.twimg.com/profile_images/545684030885093377/Hfd166Di.jpeg'},
                    #{'category':'latest_series',      'title': _('Latest series'), 'url':MAIN_URL, 'icon':''},
                    #{'category':'genres_series',      'title': _('Series'), 'url':MAIN_URL+'seriale', 'icon':''},
                    {'category':'search',             'title': _('Search'), 'search_item':True},
                    {'category':'search_history',     'title': _('Search history')} ]
                    
    MOVIES_SORT_BY = [{'title':_('Lastest'),     'sort_by':'date'  },
                      {'title':_('most viewed'), 'sort_by':'views' },
                      {'title':_('longest'),     'sort_by':'duree' },
                      #{'title':_('top rated'),   'sort_by':'rate'  },
                      {'title':_('random'),      'sort_by':'random'},
                     ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'MoviesHDCO', 'cookie':'movieshdco.cookie'})
    
    def calcAnswer(self, data):
        sourceCode = data
        try:
            code = compile(sourceCode, '', 'exec')
        except Exception:
            printExc()
            return 0
        vGlobals = {"__builtins__": None, 'string': string, 'int':int, 'str':str}
        vLocals = { 'paramsTouple': None }
        try:
            exec( code, vGlobals, vLocals )
        except Exception:
            printExc()
            return 0
        return vLocals['a']
    
    def getPage(self, url, params={}, post_data=None):
        params.update({'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE, 'header':{'Referer':url, 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0', 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'pl,en-US;q=0.7,en;q=0.3', 'Accept-Encoding':'gzip, deflate'}})
        sts, data = self.cm.getPage(url, params, post_data)
        
        current = 0
        while current < 10:
            current += 1
            if not sts and None != data:
                doRefresh = False
                try:
                    verData = data.fp.read()
                    dat = self.cm.ph.getDataBeetwenMarkers(verData, 'setTimeout', 'submit()', False)[1]
                    tmp = self.cm.ph.getSearchGroups(dat, '={"([^"]+?)"\:([^}]+?)};', 2)
                    varName = tmp[0]
                    expresion= ['a=%s' % tmp[1]]
                    e = re.compile('%s([-+*])=([^;]+?);' % varName).findall(dat)
                    for item in e:
                        expresion.append('a%s=%s' % (item[0], item[1]) )
                    
                    for idx in range(len(expresion)):
                        e = expresion[idx]
                        e = e.replace('!+[]', '1')
                        e = e.replace('!![]', '1')
                        e = e.replace('=+(', '=int(')
                        if '+[]' in e:
                            e = e.replace(')+(', ')+str(')
                            e = e.replace('int((', 'int(str(')
                            e = e.replace('(+[])', '(0)')
                            e = e.replace('+[]', '')
                        expresion[idx] = e
                    
                    #printDBG("-------------------------------------")
                    #printDBG(expresion)
                    #printDBG("-------------------------------------")
                    answer = self.calcAnswer('\n'.join(expresion)) + 11
                    #printDBG("-------------------------------------")
                    #printDBG(answer)
                    #printDBG("-------------------------------------")
                    #printDBG(data.fp.info())
                    #printDBG(verData)
                    refreshData = data.fp.info().get('Refresh', '')
                    #verUrl = self._getFullUrl( refreshData.split('URL=')[1] )
                    
                    verData = self.cm.ph.getDataBeetwenMarkers(verData, '<form ', '</form>', False)[1]
                    verUrl =  self._getFullUrl( self.cm.ph.getSearchGroups(verData, 'action="([^"]+?)"')[0] )
                    get_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', verData))
                    get_data['jschl_answer'] = answer
                    verUrl += '?'
                    for key in get_data:
                        verUrl += '%s=%s&' % (key, get_data[key])
                    verUrl = self._getFullUrl( self.cm.ph.getSearchGroups(verData, 'action="([^"]+?)"')[0] ) + '?jschl_vc=%s&pass=%s&jschl_answer=%s' % (get_data['jschl_vc'], get_data['pass'], get_data['jschl_answer'])
                    params2 = dict(params)
                    params2['load_cookie'] = True
                    params2['save_cookie'] = True
                    params2['header'] = {'Referer':url, 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0', 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'pl,en-US;q=0.7,en;q=0.3', 'Accept-Encoding':'gzip, deflate'}
                    sleep(4)
                    sts, data = self.cm.getPage(verUrl, params2, post_data)
                except Exception:
                    printExc()
            else:
                break
        return sts, data
        
    def getPage2(self, url, params={}, post_data=None):
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0'}
        params.update({'header':HTTP_HEADER})
        
        if 'movieshd.' in url:
            printDBG(url)
            proxy = 'http://www.proxy-german.de/index.php?q={0}&hl=240'.format(urllib.quote_plus(url))
            params['header']['Referer'] = proxy
            url = proxy
        #sts, data = self.cm.getPage(url, params, post_data)
        #printDBG(data)
        return self.cm.getPage(url, params, post_data)
        
    def _getFullUrl(self, url):
        if 'proxy-german.de' in url:
            url = urllib.unquote(url.split('?q=')[1])
            
        if url.startswith('//'):
            url = 'http:' + url
        elif 0 < len(url) and not url.startswith('http'):
            if url.startswith('/'): url = url[1:]
            url =  self.MAIN_URL + url
        
        #if self.MAIN_URL.startswith('https://'):
        #    url = url.replace('https://', 'http://')
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
        tmpList = [{'title': _("***Any***"), 'url':self.MAIN_URL+'/page/{page}?display=tube&filtre={sort_by}'}]
        if 1:
            sts, data = self.getPage(cItem['url'])
            if not sts: return 
            data = CParsingHelper.getDataBeetwenMarkers(data, '<ul class="listing-cat">', '</ul>', False)[1]
            data = data.split('</li>')
            if len(data): del data[-1]
            for item in data:
                url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
                icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
                title  = self.cleanHtmlStr(item)
                tmpList.append({'title': title, 'icon':self._getFullUrl(icon), 'url':self._getFullUrl(url)+'/page/{page}?display=tube&filtre={sort_by}'})
        
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
        
        sort_by = cItem.get('sort_by', config.plugins.iptvplayer.movieshdco_sortby.value)
        page    = cItem.get('page', 1)
        url = cItem['url']
        if 1 == page:
            url = url.replace('/page/{page}', '')
            url = url.format(sort_by=sort_by) 
        else:
            url = url.format(page=page, sort_by=sort_by) 
        
        sts, data = self.getPage(url)
        if not sts: return 
        
        if '"nextLink":"' in data:
            nextPage = True
        else: nextPage = False
        
        m = '<ul class="listing-videos listing-tube">'
        if m not in data:
            m = '<li class="border-radius-5 box-shadow">'

        data = CParsingHelper.getDataBeetwenMarkers(data, m, '</ul>', False)[1]
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
        
        if 'url' not in cItem: return []
        
        sts, data = self.getPage(cItem['url'])
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
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return urlTab
        
        #printDBG(data)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="video-embed">', '</div>', False)[1]
        tmp  = self.cm.ph.getDataBeetwenMarkers(data, '<tbody>', '</tbody>')[1]
        tmp  = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<tr>', '</tr>')
        
        for item in tmp:
            title  = self.cleanHtmlStr( item )
            vidUrl = self.cm.ph.getSearchGroups(item, '''<a[^>]*?href="([^"]+?)"''', 1, True)[0]
            if not vidUrl.startswith('http'): continue
            urlTab.append({'name':title, 'url':vidUrl, 'need_resolve':1})
        if len(urlTab):
            return urlTab
        data = data.split('</')
        idx = 0
        for item in data:
            if idx > 0:
                item = '</' + item 
            idx += 1
            title  = self.cleanHtmlStr( item )
            vidUrl = self.cm.ph.getSearchGroups(item, '''<source[^>]*?src="([^"]+?)"[^>]*?video/mp4[^>]*?''', 1, True)[0]
            need_resolve = 1
            if vidUrl != '':
                need_resolve = 0
            
            if vidUrl == '': vidUrl = self.cm.ph.getSearchGroups(item, '<iframe[^>]+?src="([^"]+?)"', 1, True)[0]
            if vidUrl == '': vidUrl = self.cm.ph.getSearchGroups(item, '<script[^>]+?src="([^"]+?)"', 1, True)[0]
            if vidUrl == '': vidUrl = self.cm.ph.getDataBeetwenMarkers(item, 'data-rocketsrc="', '"', False)[1]

            if vidUrl.startswith('//'):
                vidUrl = 'http:' + vidUrl
            
            vidUrl = self._getFullUrl(vidUrl)
            if 'videomega.tv/validatehash.php?' in vidUrl:
                sts, dat = self.cm.getPage(vidUrl, {'header':{'Referer':cItem['url'], 'User-Agent':'Mozilla/5.0'}})
                if not sts: return urlTab
                dat = self.cm.ph.getSearchGroups(dat, 'ref="([^"]+?)"')[0]
                if '' == dat: return urlTab
                vidUrl = 'http://videomega.tv/view.php?ref={0}&width=700&height=460&val=1'.format(dat)
            
            if '' != vidUrl:
                if title == '': title = self.up.getHostName(vidUrl)
                urlTab.append({'name':title, 'url':vidUrl, 'need_resolve':need_resolve})
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
        except Exception:
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
        except Exception:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
