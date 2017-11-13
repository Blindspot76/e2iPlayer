# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, GetCookieDir, GetDefaultLang
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.recaptcha_v2 import UnCaptchaReCaptcha
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################
# FOREIGN import
###################################################
import re
from Components.config import config, ConfigYesNo, ConfigText, ConfigSelection, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.ekinotvPREMIUM = ConfigYesNo(default = False)
config.plugins.iptvplayer.ekinotv_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.ekinotv_password = ConfigText(default = "", fixed_size = False)

config.plugins.iptvplayer.ekinotv_sortby = ConfigSelection(default = "data-dodania", choices = [("alfabetycznie", "nazwy"), ("ocena", "oceny"),("odslony", "ilości odsłon"),("data-dodania", "daty dodania"),("data-premiery", "daty premiery"), ('data-aktualizacji', 'daty aktualizacji')])            
config.plugins.iptvplayer.ekinotv_sortorder = ConfigSelection(default = "desc", choices = [("desc", "malejąco"),("asc", "rosnąco")]) 

def GetConfigList():
    optionList = []
    #optionList.append(getConfigListEntry("Użytkownik PREMIUM Ekino TV?", config.plugins.iptvplayer.ekinotvPREMIUM))
    #if config.plugins.iptvplayer.ekinotvPREMIUM.value:
    #    optionList.append(getConfigListEntry("    Ekino TV login:", config.plugins.iptvplayer.ekinotv_login))
    #    optionList.append(getConfigListEntry("    Ekino TV hasło:", config.plugins.iptvplayer.ekinotv_password))
    optionList.append(getConfigListEntry("Sortuj według:", config.plugins.iptvplayer.ekinotv_sortby))
    optionList.append(getConfigListEntry("Kolejność wyświetlania:", config.plugins.iptvplayer.ekinotv_sortorder))
    return optionList
###################################################

def gettytul():
    return 'http://ekino-tv.pl/'

class EkinoTv(CBaseHostClass):
    
    def __init__(self):
        printDBG("EkinoTv.__init__")
        CBaseHostClass.__init__(self, {'history':'EkinoTv.tv', 'cookie':'ekinotv.cookie'})
        self.MAIN_URL = 'http://ekino-tv.pl/'
        self.DEFAULT_ICON_URL = self.getFullUrl('/views/img/logo.png')
        self.SEARCH_URL    = self.getFullUrl('/search/')
        self.FILMS_CAT_URL = self.getFullUrl('/movie/cat/')  
        
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'X-Forwarded-For':'77.252.101.15', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_CAT_TAB = [{'category':'list_cats',             'title': 'Filmy',           'url':self.FILMS_CAT_URL},
                             {'category':'series_abc',            'title': 'Seriale',         'url':self.getFullUrl('/serie/')},
                             {'category':'list_movies',           'title': 'Dla dzieci',      'url':self.FILMS_CAT_URL, 'cat':'2,3,5,6'},
                             {'category':'search',                'title': _('Search'), 'search_item':True},
                             {'category':'search_history',        'title': _('Search history')} ]
        
        self.SORT_MAP  = {'data-dodania':'add',
                          'data-aktualizacji':'update',
                          'data-premiery':'premiera',
                          'data-premiery':'premiera',
                          'odslony':'views',
                          'ocena':'rate',
                          'alfabetycznie':'alfa',}
        
        self.cacheMovieFilters = {'cats':[], 'vers':[], 'years':[]}
        self.loggedIn = False
       
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urlparse.urljoin(baseUrl, url)
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
            
    def _checkNexPage(self, data, page):
        if -1 != data.find('strona[%s]' % page):
            return True
        else: return False
    
    ###################################################
    def _fillMovieFilters(self):
        self.cacheMovieFilters = { 'cats':[], 'vers':[], 'years':[]}
        sts, data = self.getPage(self.FILMS_CAT_URL)
        if not sts: return
        
        # fill cats
        dat = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="movieCategories">', '</ul>', False)[1]
        dat = re.compile('<a[^"]+?href="[^"]+?kategoria\[([0-9]+?)\][^>]*?>([^<]+?)<').findall(dat)
        for item in dat:
            self.cacheMovieFilters['cats'].append({'title': self.cleanHtmlStr(item[1]), 'cat': item[0]})
            
        # fill vers
        dat = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="quality"', '</ul>', False)[1]
        dat = re.compile('<li[^>]+?data-id="([^"]+?)"[^>]*?>(.+?)</li>').findall(dat)
        for item in dat:
            self.cacheMovieFilters['vers'].append({'title': self.cleanHtmlStr(item[1]), 'ver': item[0]})
            
        # fill years
        dat = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="filtyear">', '</ul>', False)[1]
        dat = re.compile('<li[^>]+?data-id="([^"]+?)"[^>]*?>(.+?)</li>').findall(dat)
        for item in dat:
            self.cacheMovieFilters['years'].append({'title': self.cleanHtmlStr(item[1]), 'year': item[0]})
    
    ###################################################
    def listMovieFilters(self, cItem, category):
        printDBG("EkinoTv.listMovieFilters")
        
        filter = cItem['category'].split('_')[-1]
        if 0 == len(self.cacheMovieFilters[filter]):
            self._fillMovieFilters()
        if len(self.cacheMovieFilters[filter]) > 0:
            filterTab = [{'title':'--Wszystkie--'}]
            filterTab.extend(self.cacheMovieFilters[filter])
            self.listsTab(filterTab, cItem, category)
        
    def listsTab(self, tab, cItem, category=None):
        printDBG("EkinoTv.listsTab")
        for item in tab:
            params = dict(cItem)
            if None != category:
                params['category'] = category
            params.update(item)
            self.addDir(params)
            
    def _addItems(self, cItem, dataTab, category='video'):
        for item in dataTab:
            item = item.split('</span>')
            title = self.cleanHtmlStr('<' + item[0])
            ids = self.cm.ph.getSearchGroups(item[0], 'id="([^"]+?)"')[0].split('-')
            if len(ids) > 2 and '' != ids[-1]:
                title += ' [%s]' % (ids[-1])
            url    = self.cm.ph.getSearchGroups(item[0], 'href="([^"]+?)"')[0]
            icon   = self.cm.ph.getSearchGroups(item[0], 'src="([^"]+?jpg)"')[0]
            if url == '': continue
            params = dict(cItem)
            params.update({'title':self.cleanHtmlStr(title), 'url':self.getFullUrl(url), 'icon': self.getFullIconUrl(icon), 'desc': self.cleanHtmlStr(item[-1])})
            if category == 'video':
                self.addVideo(params)
            else:
                params['category'] = category
                self.addDir(params)
        
    def listMovies(self, cItem):
        printDBG("EkinoTv.listMovies")
        
        # prepare url
        sortby    = config.plugins.iptvplayer.ekinotv_sortby.value          
        sortorder = config.plugins.iptvplayer.ekinotv_sortorder.value
        page = cItem.get('page', 1)
        url  = cItem['url'] + 'strona[%s]+sort[%s]+method[%s]+' % (page, self.SORT_MAP[sortby], sortorder)
        
        for item in [('cat', 'kategoria'), ('ver', 'wersja'), ('year', 'rok')]:
            if item[0] in cItem:
                url += '%s[%s]+' % (item[1], cItem[item[0]])
        
        sts, data = self.getPage(url)
        if not sts: return
        
        # parse data
        nextPage = self._checkNexPage(data, page+1)
        sp = '<div class="movies-list-item"'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div id="pager">', False)[1]
        data = data.split(sp)
        self._addItems(cItem, data)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
                
    def listsSeriesABC(self, cItem, category):
        printDBG('EkinoTv.listsSeriesABC start')
        sts, data = self.getPage(cItem['url'])
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="serialsmenu">', '</ul>', False)[1]
            data = re.compile('<a[^"]+?href="([^"]+?)"[^>]*?><span class="name">([^<]+?)</span><span class="count">([^<]+?)<').findall(data)
            for item in data:
                params = dict(cItem)
                params.update({'category':category, 'title':'%s (%s)' % (item[1], item[2]), 'url':self.getFullUrl(item[0])})
                self.addDir(params)
                
    def listsSeries(self, cItem, category):
        printDBG('EkinoTv.listsSeries start')
        page = cItem.get('page', 1)
        url  = cItem['url'] + ',strona=%s' % page
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = False
        if (',strona=%s"' % (page+1)) in data:
            nextPage = True
        
        sp = '<div class="movies-list-item"'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, '<div id="pager">', False)[1]
        data = data.split(sp)
        self._addItems(cItem, data, category)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
                
    def listEpisodes(self, cItem):
        printDBG('EkinoTv.listEpisodes start')
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="list-series"', '<br style="clear:both">', False)[1]
        data = data.split('</ul>')
        if len(data): del data[-1]
        for season in data:
            sTitle = self.cm.ph.getDataBeetwenMarkers(season, '<p>', '</p>', False)[1]
            eData = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(season)
            for eItem in eData:
                s = self.cm.ph.getSearchGroups(eItem[0], 'season\[([0-9]+?)\]')[0]
                e = self.cm.ph.getSearchGroups(eItem[0], 'episode\[([0-9]+?)\]')[0]
                title = '%s s%se%s %s' % (cItem['title'], s.zfill(2), e.zfill(2), eItem[1])
                params = dict(cItem)
                params.update({'title':title, 'url':self.getFullUrl(eItem[0])})
                self.addVideo(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("EkinoTv.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = searchPattern.replace(' ', '+')
        
        sts, data = self.getPage(self.SEARCH_URL, {}, {'search_field':searchPattern})
        if not sts: return
        
        if 'movies' == searchType:
            sp = '<div class="movies-list-item"'
            data = self.cm.ph.getDataBeetwenMarkers(data, sp, 'Znalezione seriale', False)[1]
            data = data.split(sp)
            self._addItems(cItem, data)
        else:
            sp = '<div class="movies-list-item"'
            data = self.cm.ph.getDataBeetwenMarkers(data, 'Znalezione seriale', '<br style="clear:both">', False)[1]
            data = data.split(sp)
            if len(data): del data[0]
            self._addItems(cItem, data, 'series_episodes')

    def getLinksForVideo(self, cItem):
        printDBG("EkinoTv.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        baseVidUrl = self.cm.ph.getSearchGroups(data, '''src=['"]([^'^"]*?/watch/[^'^"]*?)['"]''')[0]
        if baseVidUrl == '': baseVidUrl = 'watch/f/'
        
        if 'dmcabitch.jpg' in data:
            message = self.cm.ph.getDataBeetwenMarkers(data, '<div class="playerContainer"', '<br style="clear:both">', True)[1]
            SetIPTVPlayerLastHostError(self.cleanHtmlStr(message))
            return []
        
        playersData = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="players"', '</ul>', False)[1]
        
        playersData = playersData.split('</li>')
        if len(playersData): del playersData[-1]
        players = []
        for pItem in playersData:
            pItem = self.cm.ph.getDataBeetwenMarkers(pItem, '<li>', '</a>', False)[1]
            title = self.cleanHtmlStr(pItem)
            id = self.cm.ph.getSearchGroups(pItem, 'href="#([^"]+?)"')[0]
            title += ' ' + self.cm.ph.getSearchGroups(pItem, 'title="([^"]+?)"')[0]
            players.append({'title':title, 'id':id})
            
        #printDBG(players)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="tab-content">', '<script>', False)[1]
        data = data.split('</div>')
        if len(data): del data[-1]
        #printDBG(data)
        for item in data:
            id  = self.cm.ph.getSearchGroups(item, 'id="([^"]+?)"')[0]
            playerParams = self.cm.ph.getSearchGroups(item, '''ShowPlayer[^"^']*?['"]([^"^']+?)['"]\s*\,\s*['"]([^"^']+?)['"]''', 2)
            url = ''
            if playerParams[0] != '' and playerParams[1] != '':
                url = baseVidUrl + '/'.join(playerParams)
            if url == '': url = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            url = self.getFullUrl(url)
            if url == '' or url.split('.')[-1] in ['jpg', 'jepg', 'gif']:
                continue
            for p in players:
                if p['id'] == id:
                    urlTab.append({'name':p['title'], 'url':strwithmeta(url, {'Referer':cItem['url']}), 'need_resolve':1})
                    break
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("EkinoTv.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        urlParams = dict(self.defaultParams)
        urlParams['header'] = dict(urlParams['header'])
        urlParams['header']['Referer'] = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        urlParams['handle_recaptcha'] = True
        urlParams['with_metadata'] = True
        
        url = baseUrl
        tries = 0
        while self.up.getDomain(self.getMainUrl()) in self.up.getDomain(url) and tries < 4:
            tries += 1
            
            sts, data = self.getPage(baseUrl, urlParams)
            if not sts: return []
            
            baseUrl = baseUrl.meta.get('url', baseUrl)
            url = baseUrl
            
            if self.up.getDomain(self.getMainUrl()) not in self.up.getDomain(url):
                break
            
            if 'recaptcha' in data:
                SetIPTVPlayerLastHostError(_('Link protected with google recaptcha v2.')) 
                sitekey  = self.cm.ph.getSearchGroups(data, 'data-sitekey="([^"]+?)"')[0]
                if sitekey == '': sitekey = self.cm.ph.getSearchGroups(data, '''['"]?sitekey['"]?\s*:\s*['"]([^"^']+?)['"]''')[0]
                if sitekey != '':
                    recaptcha = UnCaptchaReCaptcha(lang=GetDefaultLang())
                    recaptcha.HTTP_HEADER['Referer'] = baseUrl
                    token = recaptcha.processCaptcha(sitekey)
                    if token != '':
                        vUrl = self.getFullUrl('/watch/verify.php')
                        urlParams['header']['Referer'] = baseUrl
                        sts, data = self.getPage(vUrl, urlParams, {'verify':token})
                    else:
                        break
            
            sts, data = self.getPage(url, urlParams)
            if not sts: return urlTab
            
            if 'recaptcha' in data:
                SetIPTVPlayerLastHostError(_('Link protected with google recaptcha v2.')) 
                continue
            
            url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0])
            if not self.cm.isValidUrl(url):
                url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''var\s+url\s*=\s*['"]([^'^"]+?)['"]''')[0])
            printDBG("|||"  + url)
        
        if self.cm.isValidUrl(url): 
            urlTab = self.up.getVideoLinkExt(url)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('EkinoTv.handleService start') 
                
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "EkinoTv.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
    #FILMS CATEGORIES
        elif 'list_cats' == category:
            self.listMovieFilters(self.currItem, 'list_vers')
        elif 'list_vers' == category:
            self.listMovieFilters(self.currItem, 'list_years')
        elif 'list_years' == category:
            self.listMovieFilters(self.currItem, 'list_movies')
        elif 'list_movies' == category:
            self.listMovies(self.currItem)
    #FILMS LETTERS
        elif 'series_abc' == category:
            self.listsSeriesABC(self.currItem, 'series_list')
    #LIST SERIALS
        elif 'series_list' == category:
            self.listsSeries(self.currItem, 'series_episodes')
        elif 'series_episodes' == category:
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
        CHostBase.__init__(self, EkinoTv(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
