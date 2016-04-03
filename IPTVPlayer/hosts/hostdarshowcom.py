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
import time
import re
import urllib
import unicodedata
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
    return 'http://darshow.com/'

class DarshowCom(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL      = 'http://www.darshow.com/'
    SEARCH_URL    = MAIN_URL
    DEFAULT_ICON  = "http://www.darshow.com/templates/style/images/logo.png"
    
    MAIN_CAT_TAB = [{'category':'search',          'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),             'icon':DEFAULT_ICON} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  DarshowCom.tv', 'cookie':'darshowcom.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cacheSubCategory = []
        self.cacheLinks = {}
        
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
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("DarshowCom.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listsMainMenu(self, cItem, category1, category2):
        printDBG("DarshowCom.listsMainMenu")
        self.cacheSubCategory = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<nav class="header-nav"', '</nav>')[1]
        data = data.split('<li class="drop-xs')
        if len(data): del data[0]
        
        for part in data:
            idx1 = part.find('<ul>')
            idx2 = part.find('</ul>')
            if idx1 == -1 or idx2 == -1 or idx2 < idx1:
                continue
            tmp      = self.cm.ph.getSearchGroups(part[0:idx1], '''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)<''', 2)
            mainUrl  = tmp[0]
            mainName = self.cleanHtmlStr( tmp[1] )
            
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(part[idx1:idx2], '<li>', '</li>')
            tab = []
            for item in tmp:
                url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
                title = self.cleanHtmlStr( item )
                if not url.startswith('http'):
                    continue
                tab.append({'title':title, 'url':url})
            
            params = dict(cItem)
            if len(tab):
                params.update({'category':category1,'title':mainName, 'sub_cat_idx':len(self.cacheSubCategory)})
                self.addDir(params)
                self.cacheSubCategory.append(tab)
                
            elif len(mainUrl) and mainUrl[0] != '#':
                mainUrl = self._getFullUrl( mainUrl )
                params.update({'category':category2,'title':mainName, 'url':mainUrl})
                self.addDir(params)
            
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(part[idx2:], '<li>', '</li>')
            printDBG("******************************************************")
            printDBG(tmp)
            printDBG("******************************************************")
            for item in tmp:
                mainUrl  = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0]
                mainName = self.cleanHtmlStr( item )
                if mainUrl.startswith('#') or 'feedback' in mainUrl:
                    continue
                if len(mainUrl):
                    params = dict(cItem)
                    params.update({'category':category2, 'title':mainName, 'url':self._getFullUrl( mainUrl )})
                    self.addDir(params)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("DarshowCom.listCategories")
        if 'sub_cat_idx' not in cItem: return
        idx = cItem['sub_cat_idx']
        if idx > -1 and idx < len(self.cacheSubCategory):
            cItem = dict(cItem)
            cItem['category'] = nextCategory
            self.listsTab(self.cacheSubCategory[idx], cItem)
            
    def listItems(self, cItem, nextCategory='explore_item'):
        printDBG("DarshowCom.listItems")
        page      = cItem.get('page', 1)
        post_data = cItem.get('post_data', None) 
        url       = cItem['url'] 
        
        sts, data = self.cm.getPage(url, {}, post_data)
        if not sts: return
        
        nextPageUrl = self.cm.ph.getDataBeetwenMarkers(data, '<span class="navigation">', '</div>', False)[1]
        nextPageUrl = self.cm.ph.getSearchGroups(nextPageUrl, '<a[^>]+?href="([^"]+?)">%s</a>' % (page+1))[0]
        if '#' == nextPageUrl:
            if '&' in url and post_data == None:
                nextPageUrl = url.split('&search_start')[0] + '&search_start=%s' % (page+1)
            elif post_data != None:
                nextPageUrl = url
        
        m1   = '<div class="new_movie'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '</article>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, m1, '</section>')
        for item in data:
            title = self.cm.ph.getSearchGroups(item, '''title=['"]([^"^']+?)['"]''')[0]
            icon  =  self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
            if icon.startswith('['): 
                icon = ''
            else:
                icon = self._getFullUrl( icon )
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            if url.startswith('http'):
                params = dict(cItem)
                params.update({'title':self.cleanHtmlStr(title), 'url':url, 'icon':icon, 'desc':''})
                if nextCategory != 'video':
                    params['category'] = nextCategory
                    self.addDir(params)
                else:
                    self.addVideo(params)
        
        if nextPageUrl.startswith('http'):
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':cItem.get('page', 1)+1, 'url':self._getFullUrl(nextPageUrl)})
            self.addDir(params)
            
    def exploreItem(self, cItem, category):
        printDBG("DarshowCom.exploreItem")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        params = dict(cItem)
        params['title'] = _('Trailer')
        self.addVideo(params)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="article-head">', '<div role="tabpanel">', False)[1]
        icon = self.cm.ph.getSearchGroups(data, '''src=['"]([^"^']+?)['"]''')[0]
        url  = self._getFullUrl( self.cm.ph.getSearchGroups(data, '''href=['"](https?://on\.[^"^']+?)['"]''')[0] )
        params = dict(cItem)
        params.update({'title':_('Episodes'), 'url':url, 'category':category, 'icon':icon, 'desc':self.cleanHtmlStr(data)})
        self.addDir(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("DarshowCom.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        # get tabs names
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<li id="player-tab" ', '<li class="pull-right">')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>') 
        tabsNames = []
        for item in tmp:
            tabsNames.append(self.cleanHtmlStr(item))
        
        idx = data.find('<div class="tab-content"')
        if idx == -1:
            return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data[idx:], '<div role="tabpanel"', '</div>', False)
        if len(data) != len(tabsNames):
            printDBG('>>>>>>>>>>>>>>>>>>>ERROR<<<<<<<<<<<<<<<<<<<<')
            printDBG('>>>>>>>>>>>>>>>>>>> Something is wrong len(data)[%d] != len(tabsNames)[%d] !!!' % (len(data), len(tabsNames)) )
        
        for idx in range(len(data)):
            item = data[idx]
            if idx < len(tabsNames):
                tabName = tabsNames[idx]
            else:
                tabName = 'ERROR'
            
            url = ''
            if 'ViP' in tabName:
                # vip links are not supported
                continue
            elif 'روابط التحميل' in tabName:
                # download links not supported
                continue
            elif 'إعلان الفيلم' in tabName:
                # trailer
                url = self.cm.ph.getSearchGroups(item, '''file:[^"^']*?["'](http[^'^"]+?)["']''')[0]
                title = _('[Trailer]') + ' ' + tabName
            elif 'باقي السيرفرات' in tabName:
                # diffrents servers
                servers   = re.compile('''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)<''').findall(item)
                for server in servers:
                    url   = self._getFullUrl( server[0] )
                    title = tabName + ' ' + self.cleanHtmlStr( server[1] )
                    if url.startswith('http'):
                        urlTab.append({'name':title, 'url':url, 'need_resolve':1})
                url = ''
            elif 'iframe' in item:
                url = self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
                title = tabName
            
            url = self._getFullUrl( url )
            if url.startswith('http'):
                params = {'name':title, 'url':url, 'need_resolve':1}
                if 'الإفتراضي' in title:
                    #when default insert as first
                    urlTab.insert(0, params)
                else:
                    urlTab.append(params)
        
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("DarshowCom.getVideoLinks [%s]" % videoUrl)
        m1 = '?s=http'
        if m1 in videoUrl:
            videoUrl = videoUrl[videoUrl.find(m1)+3:]
        
        if 'dardarkom.com' in videoUrl:
            sts, data = self.cm.getPage(videoUrl)
            if not sts: return []
            url = ''
            urlTmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe ', '</iframe>', False, True)
            printDBG(urlTmpTab)
            for urlTmp in urlTmpTab:
                url = self.cm.ph.getSearchGroups(urlTmp, '''location\.href=['"]([^"^']+?)['"]''', 1, True)[0]
                if 'javascript' in url: 
                    url = ''
            if url == '': url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
            url = self._getFullUrl( url )
            videoUrl = url
        
        urlTab = []
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("DarshowCom.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL
        cItem['post_data'] = {'do':'search', 'subaction':'search', 'story':searchPattern}
        if cItem.get('page', 1) > 1:
            cItem['post_data']['search_start'] = cItem['page']
        self.listItems(cItem)

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % self.currItem )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu({'url':self.MAIN_URL, 'icon':self.DEFAULT_ICON}, 'categories', 'list_items')
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_items')
        elif category == 'list_items':
                self.listItems(self.currItem)
    #EXPLORE ITEM
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_videos')
        elif category == 'list_videos':
                self.listItems(self.currItem, 'video')
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
        CHostBase.__init__(self, DarshowCom(), True, favouriteTypes=[]) #, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('darshowcomlogo.png')])
    
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
