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
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
###################################################

###################################################
# FOREIGN import
###################################################
import time
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
config.plugins.iptvplayer.streamliveto_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.streamliveto_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry( _("Login") + ": ", config.plugins.iptvplayer.streamliveto_login))
    optionList.append(getConfigListEntry( _("Password") + ": ", config.plugins.iptvplayer.streamliveto_password))
    return optionList


def gettytul():
    return 'StreamLiveTo.tv'

class StreamLiveTo(CBaseHostClass):
    HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    MAIN_URL = 'http://www.streamlive.to/'
    
    MAIN_CAT_TAB = [{'category':'category',        'title': 'Live Channels', 'icon':''},
                    {'category':'search',          'title': _('Search'), 'search_item':True},
                    {'category':'search_history',  'title': _('Search history')} ]

 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'StreamLiveTo.tv', 'cookie':'streamliveto.cookie'})
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheFilters = {}
        
    def _getFullUrl(self, url):
        if 0 < len(url):
            if url.startswith('//'):
                url = 'http:' + url
            elif not url.startswith('http'):
                url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def getPage(self, url, params={}):
        return self.checkBotProtection(url, params)
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("StreamLiveTo.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillCategories(self):
        printDBG("StreamLiveTo.fillCategories")
        self.cacheFilters = {}
        #sts, data = self.getPage(self._getFullUrl('channels/'), self.defaultParams)
        sts, data = self.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return
        
        catTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<select name="category"', '</select>', False)[1]
        tmp = re.compile('<option [^>]*?value="([^"]*?)"[^>]*?>([^<]+?)</option>').findall(tmp)
        for item in tmp:
            catTab.append({'title':item[1], 'cat':urllib.quote(item[0])})
            
        langTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<select name="language"', '</select>', False)[1]
        tmp = re.compile('<option [^>]*?value="([^"]*?)"[^>]*?>([^<]+?)</option>').findall(tmp)
        for item in tmp:
            langTab.append({'title':item[1], 'lang':item[0]})
            
        sortTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<select name="sort"', '</select>', False)[1]
        tmp = re.compile('<option [^>]*?value="([^"]*?)"[^>]*?>([^<]+?)</option>').findall(tmp)
        for item in tmp:
            sortTab.append({'title':item[1], 'lang':item[0]})
            
        self.cacheFilters['cat']  = catTab
        self.cacheFilters['lang'] = langTab
        self.cacheFilters['sort'] = sortTab
        
    def listCategory(self, cItem, nextCategory):
        printDBG("StreamLiveTo.listCategory")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('cat', []), cItem)
        
    def listLanguage(self, cItem, nextCategory):
        printDBG("StreamLiveTo.listLanguage")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('lang', []), cItem)
        
    def listSort(self, cItem, nextCategory):
        printDBG("StreamLiveTo.listSort")
        if {} == self.cacheFilters:
            self.fillCategories()
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get('sort', []), cItem)
            
    def listChannels(self, cItem):
        printDBG("StreamLiveTo.listChannels")
        page = cItem.get('page', 1)
        cat  = cItem.get('cat', '')
        q    = cItem.get('q', '')
        lang = cItem.get('lang', '')
        sort = cItem.get('sort', '')
        
        #url = 'channels/{0}?p={1}&q={2}&lang={3}&sort={4}'.format(cat, page, q, lang, sort)
        url = '{0}?p={1}&q={2}&lang={3}&sort={4}'.format(cat, page, q, lang, sort)
        url = self._getFullUrl(url)

        sts, data = self.getPage(url, self.defaultParams)
        if not sts: return
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(data)
        printDBG("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'class="pages"', '</p>', False)[1]
        if 'p={0}&'.format(page+1) in nextPage:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="clist clearfix">', '</ul>', False)[1]
        data = data.split('</li>')
        if len(data): del data[-1]
        for item in data:
            url  = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            icon = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<strong>', '</strong>', False)[1] )
            if '' == title: title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0] )
            if 'class="premium_only"' in item: title += ' [PREMIUM ONLY]'
            desc = self.cleanHtmlStr( item.split('</strong>')[-1] )
            if url.startswith('http'):
                params = {'title':title, 'url':url, 'desc':desc, 'icon':icon}
                self.addVideo(params)
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("StreamLiveTo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['q'] = urllib.quote(searchPattern)
        self.listChannels(cItem)
    
    def getLinksForVideo(self, cItem):
        printDBG("StreamLiveTo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        videoUrl = cItem['url']
        if videoUrl.startswith('http'):
            sts, data = self.getPage(videoUrl, self.defaultParams)
            if not sts: []
        
            urlTab = self.up.getVideoLinkExt(videoUrl)
            for idx in range(len(urlTab)):
                urlTab[idx]['need_resolve'] = 0
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
        
    def checkBotProtection(self, url, httpParams):
        printDBG("StreamLiveTo.checkBotProtection")
        captchaMarker = 'name="captcha"'
        sts, data = self.cm.getPage(url, httpParams)
        if not sts: return False, None
        if captchaMarker not in data: return True, data
        data     = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<form [^>]+?>'), re.compile('</form>'), True)[1]    
        title    = self.cm.ph.getDataBeetwenMarkers(data, '<h1>', '</h1>')[1]
        question = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('</h1>'), re.compile('</form>'), True)[1]
        
        title = self.cleanHtmlStr(title)
        question = self.cleanHtmlStr(question)
        
        from copy import deepcopy
        params = deepcopy(IPTVMultipleInputBox.DEF_PARAMS)
        params['accep_label'] = _('Send')
        params['title'] = title
        params['list'] = []
        item = deepcopy(IPTVMultipleInputBox.DEF_INPUT_PARAMS)
        item['label_size'] = (550,50 + 25 * question.count('\n'))
        item['title'] = question
        item['input']['text'] = ''
        params['list'].append(item)
        
        retArg = self.sessionEx.waitForFinishOpen(IPTVMultipleInputBox, params)
        printDBG(retArg)
        if retArg and 1 == len(retArg) and retArg[0] and 1 == len(retArg[0]):
            answer = '%s' % retArg[0][0]
            
            newHttpParams = dict(httpParams)
            newHeader = dict(self.HTTP_HEADER)
            newHeader['Referer'] = url
            newHttpParams['header'] = newHttpParams
            
            sts, data = self.cm.getPage(url, newHttpParams, {'captcha':answer})
            if not sts: return False, None
            resultMarker = 'Your answer is wrong.'
            if  resultMarker in data:
                self.sessionEx.open(MessageBox, resultMarker, type = MessageBox.TYPE_ERROR, timeout = 10 )
            else:
                return True, data
        return False, None
        
    def doLogin(self, login, password):
        logged = False
        HTTP_HEADER= dict(self.HTTP_HEADER)
        HTTP_HEADER.update( {'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With' : 'XMLHttpRequest'} )

        post_data = {'username':login, 'password':password, 'accessed_by':'web', 'submit':'Login', 'x':0, 'y':0}
        params    = {'header' : HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True}
        loginUrl  = self.MAIN_URL + 'login.php'
        sts, data = self.cm.getPage( loginUrl, params, post_data)
        if sts and '/logout"' in data:
            logged = True
        return logged
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            login  = config.plugins.iptvplayer.streamliveto_login.value
            passwd = config.plugins.iptvplayer.streamliveto_password .value
            if '' != login.strip() and '' != passwd.strip():
                if not self.doLogin(login, passwd):
                    self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_INFO, timeout = 10 )
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'category':
            self.listCategory(self.currItem, 'language')
        elif category == 'language':
            self.listLanguage(self.currItem, 'sort')
        elif category == 'sort':
            self.listSort(self.currItem, 'list_channels')
        elif category == 'list_channels':
            self.listChannels(self.currItem)
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
        CHostBase.__init__(self, StreamLiveTo(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('streamlivetologo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
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
