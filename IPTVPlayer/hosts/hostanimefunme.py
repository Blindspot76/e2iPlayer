# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
import re
import urllib
import urlparse
import unicodedata
import string
import base64
try:    import json
except: import simplejson as json
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
config.plugins.iptvplayer.animefunme_language = ConfigSelection(default = "en", choices = [("en", _("English")), ("es", _("Spanish"))])

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Language:"), config.plugins.iptvplayer.animefunme_language))
    return optionList
###################################################


def gettytul():
    return 'http://animefun.me/'

class AnimeFunME(CBaseHostClass):
    USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'animefun.me', 'cookie':'animefunme.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_URL = 'http://animefun.me/'
        new  = 'new/'
        most = 'most_viewed/'
        if config.plugins.iptvplayer.animefunme_language.value == 'es':
            new  = 'nuevo/'
            most = 'mas_visto/'
            lang = 'es/'
            self.SEARCH_URL = self.MAIN_URL +'es/buscar/?s='
        else:
            lang = ''
            self.SEARCH_URL = self.MAIN_URL +'search/?s='
        
        self.DEFAULT_ICON  = "http://img.youtube.com/vi/BtWo7GiDVMQ/mqdefault.jpg"
        self.MAIN_CAT_TAB = [{'category':'list_sortby', 'title': _('Top'),            'url':self.MAIN_URL+lang+'top/',            'icon':self.DEFAULT_ICON},
                             {'category':'list_items',  'title': _('New'),            'url':self.MAIN_URL+lang+new,               'icon':self.DEFAULT_ICON},
                             {'category':'list_items',  'title': _('Most Viewed'),    'url':self.MAIN_URL+lang+most,              'icon':self.DEFAULT_ICON},
                             {'category':'list_items2', 'title': _('Latest Update'),  'url':self.MAIN_URL+lang+'latest_update/',  'icon':self.DEFAULT_ICON},
                             {'category':'list_abc',    'title': _('Anime List'),     'url':self.MAIN_URL+lang+'anime_list/',     'icon':self.DEFAULT_ICON},
                             {'category':'categories',  'title': _('Genres'),         'url':self.MAIN_URL+lang+new,               'icon':self.DEFAULT_ICON},
                             {'category':'search',          'title': _('Search'), 'search_item':True, 'icon':self.DEFAULT_ICON},
                             {'category':'search_history',  'title': _('Search history'),             'icon':self.DEFAULT_ICON} ]
                        
        self.SORT_BY_TAB = [{'title':_('Create Date'), 'sortby':'newest'},
                            {'title':_('Views'),       'sortby':'mostviewed'}]
 
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        else:
            if 0 < len(url) and not url.startswith('http'):
                url =  self.MAIN_URL + url
            if not self.MAIN_URL.startswith('https://'):
                url = url.replace('https://', 'http://')
                
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)
        return url
        
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
        header = {'Referer':url, 'User-Agent':self.USER_AGENT, 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'pl,en-US;q=0.7,en;q=0.3', 'Accept-Encoding':'gzip, deflate'}
        header.update(params.get('header', {}))
        params.update({'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE, 'header':header})
        sts, data = self.cm.getPage(url, params, post_data)
        
        current = 0
        while current < 3:
            if not sts and None != data:
                #if current == 0:
                #    url = 'http://animefun.me/'
                #    params['header']['Referer'] = url
                #    params['load_cookie'] = False 
                #    sts, data = self.cm.getPage(url, params, post_data)
                current += 1
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
                    
                    answer = self.calcAnswer('\n'.join(expresion)) + 11
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
                    params2['header'] = {'Referer':url, 'User-Agent':self.USER_AGENT, 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'pl,en-US;q=0.7,en;q=0.3', 'Accept-Encoding':'gzip, deflate'}
                    sleep(4)
                    sts, data = self.cm.getPage(verUrl, params2, post_data)
                except:
                    printExc()
            else:
                break
        #if current > 0:
        #    params['header']['Referer'] = baseUrl
        #    sts, data = self.cm.getPage(baseUrl, params, post_data)
        return sts, data
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("AnimeFunME.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("AnimeFunME.listCategories")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        tab = []
        if cItem.get('category', '') == 'list_abc':
            data = self.cm.ph.getDataBeetwenMarkers(data, 'alphabet', '<table ', False)[1]
        else:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="genres_list">', '</ul>', False)[1]
        data = re.compile('''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)<''').findall(data)
        for item in data:
            title = self.cleanHtmlStr(item[1])
            url   = self._getFullUrl(item[0])
            tab.append({'title':title, 'url':url})
            
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(tab, cItem)
            
    def listItems(self, cItem, nextCategory='explore_item', type="1"):
        printDBG("AnimeFunME.listItems")
        page = cItem.get('page', 1)
        url = cItem['url']
        tmp = url.split('?')
        url = tmp[0]
        if len(tmp)>1: query = tmp[1]
        else: query = ''
        
        if page > 1:
            url += '/%d/' % page
        
        if 'sortby' in cItem:
            url += '?sortby=' + cItem['sortby']
        
        if '?' in url: url += '&'
        else: url += '?'
        url += query
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, "pagination", '</ol>', False)[1]
        if ('<span>%d</span>' % (page+1)) in nextPage:
            nextPage = True
        else:
            nextPage = False
        if type == '1':
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li class="updatesli">', '</li>')
        else:
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr style="background-', '</tr>')
            
        for item in data:
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h3 class="title">', '</h3>', True)[1] )
            if title == '': title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<a ', '</a>', True)[1] )
            desc  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, 'animedetail="', '"', False)[1] )
            if url.startswith('http'):
                icon = strwithmeta(icon, {'Cookie':self.cm.getCookieHeader(self.COOKIE_FILE), 'User-Agent':self.USER_AGENT})
                params = dict(cItem)
                params.update({'title':title, 'url':url, 'icon':icon, 'desc':desc})
                if nextCategory == 'video':
                    self.addVideo(params)
                else:
                    params['category'] = nextCategory
                    self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("AnimeFunME.exploreItem")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        # trailer
        videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
        videoUrl = self._getFullUrl(videoUrl)
        if videoUrl.startswith('http'):
            params = dict(cItem)
            params.update({'title':_('Preview'), 'url':videoUrl})
            self.addVideo(params)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'listing', '</table>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a ', '</a>')
        for item in data:
            title = self.cleanHtmlStr(self.cleanHtmlStr(item).replace('\r', ' ').replace('\n', ' '))
            if title == "": title = cItem['title']
            videoUrl = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''', 1, True)[0]
            videoUrl = self._getFullUrl(videoUrl)
            if not videoUrl.startswith('http'): continue
            params = dict(cItem)
            params.update({'title':title, 'url':videoUrl})
            self.addVideo(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("AnimeFunME.getLinksForVideo [%s]" % cItem)
        urlTab = [] 
        
        if 'animefun.me' not in cItem['url']:
            return [{'name':'', 'url':cItem['url'], 'need_resolve':1}]
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '#player_load', 'success', False)[1]
        url       = self.cm.ph.getSearchGroups(data, '''url: ['"]([^'^"]+?)['"]''')[0]
        post_data = self.cm.ph.getSearchGroups(data, '''data: ['"]([^"^']+?)['"]''')[0]
        
        sts, data = self.getPage(url, {'raw_post_data':True, 'header':{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'}}, post_data)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'anime_download', '<script ', False)[1]
        data = re.compile('''<a[^>]+?href=['"](http[^"^']+?)['"][^>]*?>([^<]+?)<''').findall(data)
        for item in data:
            urlTab.append({'name':item[1], 'url':item[0], 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("AnimeFunME.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        
        if '/vload/' in videoUrl:
            header = {'Referer':videoUrl, 'User-Agent':self.USER_AGENT, 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'pl,en-US;q=0.7,en;q=0.3', 'Accept-Encoding':'gzip, deflate'}
            params= {'return_data':False, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE, 'header':header}
            try:
                sts, response = self.cm.getPage(videoUrl, params)
                url = response.geturl()
                response.close()
                urlTab.append({'name':'', 'url':url, 'need_resolve':0})
            except:
                printExc()
        elif videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnimeFunME.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL + urllib.quote(searchPattern)
        self.listItems(cItem)

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
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_sortby')
        elif category == 'list_abc':
            self.listCategories(self.currItem, 'list_items3')
        if category == 'list_sortby':
            cItem = dict(self.currItem)
            cItem['category'] = 'list_items'
            self.listsTab(self.SORT_BY_TAB, cItem)
        elif category == 'list_items':
                self.listItems(self.currItem)
        elif category == 'list_items2':
                self.listItems(self.currItem, nextCategory="video", type="2")
        elif category == 'list_items3':
                self.listItems(self.currItem, type="2")
    #EXPLORE ITEM
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
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
        # for now we must disable favourites due to problem with links extraction for types other than movie
        CHostBase.__init__(self, AnimeFunME(), True, favouriteTypes=[]) #, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('animefunmelogo.png')])
    
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
        
    #def getArticleContent(self, Index = 0):
    #    retCode = RetHost.ERROR
    #    retlist = []
    #    if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
    #
    #    hList = self.host.getArticleContent(self.host.currList[Index])
    #    for item in hList:
    #        title      = item.get('title', '')
    #        text       = item.get('text', '')
    #        images     = item.get("images", [])
    #        othersInfo = item.get('other_info', '')
    #        retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
    #    return RetHost(RetHost.OK, value = retlist)
    
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
