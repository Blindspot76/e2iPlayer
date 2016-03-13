# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getF4MLinksWithMeta, getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html, _unquote
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
import time
import re
import urllib
import unicodedata
import string
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

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://kisscartoon.me/'

class KissCartoonMe(CBaseHostClass):
    USER_AGENT = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36'
    HEADER = {'User-Agent': USER_AGENT, 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL = 'http://kisscartoon.me/'
    DEFAULT_ICON = "http://kisscartoon.so/wp-content/uploads/2015/12/logo.png"
    
    MAIN_CAT_TAB = [{'category':'home',            'title': _('Home'),              'url':MAIN_URL,                     'icon':DEFAULT_ICON},
                    {'category':'list_cats',       'title': _('Catrtoon list'),     'url':MAIN_URL+'CartoonList',       'icon':DEFAULT_ICON},
                    {'category':'search',          'title': _('Search'), 'search_item':True,                            'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),                                        'icon':DEFAULT_ICON} ]
    SORT_BY_TAB = [{'title':_('Sort by alphabet')},
                   {'title':_('Sort by popularity'), 'sort_by':'MostPopular'},
                   {'title':_('Latest update'),      'sort_by':'LatestUpdate'},
                   {'title':_('New cartoon'),        'sort_by':'Newest'}]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'kisscartoon.me', 'cookie':'kisscartoonme.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheHome = {}
        self.cache = {}
        
    def calcAnswer(self, data):
        sourceCode = data
        try:
            code = compile(sourceCode, '', 'exec')
        except:
            printExc()
            return 0
        vGlobals = {"__builtins__": None, 'string': string, 'int':int, 'str':str}
        vLocals = { 'paramsTouple': None }
        try:
            exec( code, vGlobals, vLocals )
        except:
            printExc()
            return 0
        return vLocals['a']
        
    def getPage(self, baseUrl, params={}, post_data=None):
        url = baseUrl
        header = {'Referer':url, 'User-Agent':self.USER_AGENT, 'Accept-Encoding':'text'}
        header.update(params.get('header', {}))
        params.update({'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE, 'header':header})
        sts, data = self.cm.getPage(url, params, post_data)
        
        current = 0
        while current < 3:
            if not sts and None != data:
                start_time = time.time()
                current += 1
                doRefresh = False
                try:
                    verData = data.fp.read()
                    printDBG("===============================================================")
                    printDBG(verData)
                    printDBG("===============================================================")
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
                    
                    answer = self.calcAnswer('\n'.join(expresion)) + len('kisscartoon.me')
                    refreshData = data.fp.info().get('Refresh', '')
                    
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
                    params2['header'] = {'Referer':url, 'User-Agent':self.USER_AGENT, 'Accept-Encoding':'text'}
                    printDBG("Time spent: [%s]" % (time.time() - start_time))
                    time.sleep(5-(time.time() - start_time))
                    printDBG("Time spent: [%s]" % (time.time() - start_time))
                    sts, data = self.cm.getPage(verUrl, params2, post_data)
                except:
                    printExc()
            else:
                break
        return sts, data
    
    def _getFullUrl(self, url):
        if url == '':
            return url
            
        if url.startswith('.'):
            url = url[1:]
        
        if url.startswith('//'):
            url = 'http:' + url
        else:
            if url.startswith('/'):
                url = url[1:]
            if not url.startswith('http'):
                url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)
        newUrl = ''
        idx = 0
        while idx < len(url):
            if 128 < ord(url[idx]):
                newUrl += urllib.quote(url[idx])
            else:
                newUrl += url[idx]
            idx += 1
        return newUrl #.replace('¡', '%C2%A1')
        
    def _urlWithCookie(self, url):
        url = self._getFullUrl(url)
        if url == '': return ''
        cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
        return strwithmeta(url, {'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data).strip()
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("KissCartoonMe.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir' and 'video' != item.get('category', ''):
                self.addDir(params)
            else: self.addVideo(params)
            
    def _getItems(self, data, sp='', forceIcon=''):
        printDBG("listHome._getItems")
        if '' == sp: 
            sp = "<div style='position:relative'"
        data = data.split(sp)
        if len(data): del data[0]
        tab = []
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=["']([^"^']+?)["']''')[0]
            if '' == url: continue
            title = self.cm.ph.getDataBeetwenMarkers(item, '<span class="title">', '</span>', False)[1]
            if '' == title: title = self.cm.ph.getDataBeetwenMarkers(item, '<a ', '</a>')[1]
            if forceIcon == '': icon  = self.cm.ph.getSearchGroups(item, '''src=["']([^"^']+?)["']''')[0]
            else: icon = forceIcon
            desc  = self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', False)[1]
            if '' == desc: desc = '<'+item
            tab.append({'title':self.cleanHtmlStr(title), 'url':self._getFullUrl(url), 'icon':self._urlWithCookie(icon), 'desc':self.cleanHtmlStr(desc)})
        return tab
            
    def listHome(self, cItem, category):
        printDBG("listHome.listHome [%s]" % cItem)
        
        #http://kisscartoon.me/Home/GetNextUpdatedCartoon
        #POSTDATA {id:50, page:10}

        self.cacheHome = {}
        self.sortTab = []
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="tabmenucontainer">', '</div>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li>', '</li>')
        
        tabs = []
        for item in tmp:
            tabId = self.cm.ph.getSearchGroups(item, '''showTabData\('([^']+?)'\)''')[0]
            tabTitle = self.cleanHtmlStr(item)
            tabs.append({'id':tabId, 'title':tabTitle})
        
        printDBG(tabs)
        
        tmp2 = self.cm.ph.getDataBeetwenMarkers(data, '<div id="subcontent">', '<div class="clear">', False)[1]
        tmp2 = tmp2.split('<div id="tab-')
        if len(tmp2): del tmp2[0]
        for item in tmp2:
            # find tab id and title
            tabId = item[:item.find('"')].replace('-', '')
            cTab = None
            for tab in tabs:
                if tabId == tab['id']:
                    cTab = tab
                    break
            if cTab == None: 
                printDBG('>>>>>>>>>>>>>>>>>> continue tabId[%s]' % tabId)
                continue
            # check for more item
            moreUrl = self.cm.ph.getSearchGroups(item, '''<a href="([^"]+?)">More\.\.\.</a>''')[0]
            if moreUrl != '':
                params = dict(cItem)
                params.update({'category':category, 'title':tab['title'], 'url':self._getFullUrl(moreUrl)})
                self.addDir(params)
                continue
            itemsTab = self._getItems(item)
            if len(itemsTab):
                self.cacheHome[tab['id']] = itemsTab
                params = dict(cItem)
                params.update({'category':'list_cached_items', 'tab_id':tab['id'], 'title':tab['title']})
                self.addDir(params)
            
    def listCats(self, cItem, category):
        printDBG("KissCartoonMe.listCats [%s]" % cItem)
        self.cache = {}
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        # alphabet
        cacheKey = 'alphabet'
        self.cache[cacheKey] = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="alphabet">', '</div>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a ', '</a>')
        for item in tmp:
            url = self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''')[0]
            if '://' not in url and not url.startswith('/'):
                url = 'CartoonList/' + url
            title = self.cleanHtmlStr(item)
            self.cache[cacheKey].append({'title':title, 'url':self._getFullUrl(url)})
        if len(self.cache[cacheKey]) > 0:
            params = dict(cItem)
            params.update({'category':category, 'title':_('Alphabetically'), 'cache_key':cacheKey})
            self.addDir(params)
        
        # left tab
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="rightBox">', '<div class="clear', False)
        for item in tmp:
            catTitle = self.cm.ph.getDataBeetwenMarkers(item, '<div class="barTitle">', '</div>', False)[1]
            if catTitle == '': continue
            self.cache[catTitle] = []
            tmp2 = self.cm.ph.getAllItemsBeetwenMarkers(item, '<a ', '</a>')
            for item2 in tmp2:
                url  = self.cm.ph.getSearchGroups(item2, '''href="([^"]+?)"''')[0]
                title = self.cleanHtmlStr(item2)
                desc  = self.cm.ph.getSearchGroups(item2, '''title="([^"]+?)"''')[0]
                self.cache[catTitle].append({'title':title, 'desc':desc, 'url':self._getFullUrl(url)})
            
            if len(self.cache[catTitle]) > 0:
                params = dict(cItem)
                params.update({'category':category, 'title':self.cleanHtmlStr(catTitle), 'cache_key':catTitle})
                self.addDir(params)
        
    def listSubCats(self, cItem, category):
        printDBG("KissCartoonMe.listSubCats [%s]" % cItem)
        tab = self.cache[cItem['cache_key']]
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
            
    def _urlAppendPage(self, url, page, sortBy, keyword=''):
        post_data = None
        if '' != keyword:
            post_data = {'keyword':keyword}
        if sortBy != '':
            if not url.endswith('/'):
                url += '/'
            url += sortBy+'/'
        if page > 1:
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += 'page=%d' % page
        return post_data, url
        
    def listItems(self, cItem, category):
        printDBG("KissCartoonMe.listItems [%s]" % cItem)
        page = cItem.get('page', 1)
        sort_by   = cItem.get('sort_by', '')
        post_data, url = self._urlAppendPage(cItem['url'], page, sort_by, cItem.get('keyword', ''))
        sts, data = self.getPage(url, {}, post_data)
        if not sts: return
        
        nextPage = False
        if ('page=%d"' % (page+1)) in data:
            nextPage = True
            
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Latest episode', '</table>')[1]
        data = self._getItems(data, '<tr')
        
        params = dict(cItem)
        params['category'] = category
        self.listsTab(data, params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def listEpisodes(self, cItem):
        printDBG("KissCartoonMe.listEpisodes [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url']) 
        if not sts: return
        
        printDBG(data)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Day Added', '</table>')[1]
        data = self._getItems(data, '<tr', cItem.get('icon', ''))
        
        params = dict(cItem)
        params['category'] = 'video'
        self.listsTab(data, params, 'video')
        
        
    def getLinksForVideo(self, cItem):
        printDBG("KissCartoonMe.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.getPage(cItem['url']) 
        if not sts: return urlTab
        
        tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, 'asp.wrap(', ')', False)
        for tmp in tmpTab:
            tmp = tmp.strip()
            if tmp.startswith('"'):
                tmp = tmp[1:-1]
            else:
                tmp = self.cm.ph.getSearchGroups(data, '''var %s =[^'^"]*?["']([^"^']+?)["']''')[0]
            if tmp == '': continue
            try:
                tmp = base64.b64decode(tmp)
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a ', '</a>')
                for item in tmp:
                    url  = self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''')[0]
                    if 'googlevideo.com' not in url: continue
                    name = self.cleanHtmlStr(item)
                    urlTab.append({'name':name, 'url':url, 'need_resolve':0})
            except:
                printExc()
                continue
        
        tmpTab = self.cm.ph.getDataBeetwenMarkers(data, '<select id="selectQuality">', '</select>', False)
        tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, '<option', '</option>')
        for item in tmpTab:
            url  = self.cm.ph.getSearchGroups(item, '''value="([^"]+?)"''')[0]
            if '' == url: continue
            try:
                url = base64.b64decode(url)
            except:
                continue
            if '://' not in url: continue
            name = self.cleanHtmlStr(item)
            urlTab.append({'name':name, 'url':url, 'need_resolve':0})
            
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe ', '>', withMarkers=True, caseSensitive=False)
        for item in data:
            url  = self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^'^"]+?)['"]''',  grupsNum=1, ignoreCase=True)[0]
            url = self._getFullUrl(url)
            if url.startswith('http') and 'facebook.com' not in url and 1 == self.up.checkHostSupport(url):
                urlTab.append({'name': self.up.getHostName(url), 'url':url, 'need_resolve':1})
                
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("KissCartoonMe.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if videoUrl.startswith('http'):
            urlTab.extend(self.up.getVideoLinkExt(videoUrl))
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("KissCartoonMe.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem.update({'keyword':searchPattern, 'url':self._getFullUrl('/Search/Cartoon')})
        self.listItems(cItem, 'list_episodes')

    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
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
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'home':
            self.listHome(self.currItem, 'list_items')
        elif category == 'list_cached_items':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_episodes'
            self.listsTab(self.cacheHome.get(cItem.get('tab_id'), []), cItem)
        elif category == 'list_cats':
            self.listCats(self.currItem, 'list_sub_cats')
        elif category == 'list_sub_cats':
            if self.currItem.get('cache_key', '') == 'alphabet':
                self.listSubCats(self.currItem, 'list_items')
            else:
                self.listSubCats(self.currItem, 'list_sort_tab')
        elif category == 'list_sort_tab':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_items'
            self.listsTab(self.SORT_BY_TAB, cItem)
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, KissCartoonMe(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('kisscartoonme.png')])
    
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
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
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
