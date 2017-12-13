# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, GetTmpDir, CSelOneLink
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import time
import re
import urllib
import string
import random
import base64
from datetime import datetime
from hashlib import md5
from copy import deepcopy
try:    import json
except Exception: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.iplaDefaultformat = ConfigSelection(default = "1900", choices = [("200", "bitrate: 200"),("400", "bitrate: 400"),("900", "bitrate: 900"),("1900", "bitrate: 1900")])
config.plugins.iptvplayer.iplaUseDF         = ConfigYesNo(default = True)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Domyślny format video:"), config.plugins.iptvplayer.iplaDefaultformat))
    optionList.append(getConfigListEntry(_("Używaj domyślnego format video:"), config.plugins.iptvplayer.iplaUseDF))
    return optionList
###################################################
def gettytul():
    return 'https://ipla.tv/'

class IplaTV(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'ipla', 'cookie':'ipla.tv.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.DEFAULT_ICON_URL = 'http://www.conowego.pl/uploads/pics/ipla-logo.jpg'
        self.USER_AGENT = 'mipla/23'
        self.MAIN_URL = 'https://www.ipla.tv/'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.cacheEpisodes = {}
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_CAT_TAB = [
                             #{'category':'search',         'title': _('Search'),          'search_item':True}, 
                             #{'category':'search_history', 'title': _('Search history')},
                            ]
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urlparse.urljoin(baseUrl, url)
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
    
    def listMainMenu(self, cItem, nextCategory):
        printDBG("IplaTV.listMainMenu")
        
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', '"mainmenu"'), ('<li', '>', '"separate"'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
            
    def listCategories(self, cItem, nextCategory):
        printDBG("IplaTV.listCategories")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', '"side_menu"'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
            
    def exploreCategory(self, cItem, nextCategory):
        printDBG("IplaTV.exploreCategory")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        # check for seasons
        if 'f_season' not in cItem:
            tmp = self.cm.ph.getDataBeetwenNodes(data, ('<span', '>', 'itemprop="title"'), ('</ul', '>'))[1]
            if '-Sezon-' in tmp:
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
                for item in tmp:
                    url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                    title = self.cleanHtmlStr(item)
                    params = dict(cItem)
                    params.pop('f_sort', None)
                    params.update({'good_for_fav':True, 'title':title, 'url':url, 'f_season':True})
                    self.addDir(params)
                
        # check for sort
        if 'f_sort' not in cItem and 0 == len(self.currList):
            url = cItem['url']
            if not url.endswith('/'): url += '/'
            tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'sort_select'), ('</select', '>'))[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<option', '</option>')
            for item in tmp:
                val = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                title = self.cleanHtmlStr(item)
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'url':url + val, 'f_sort':val})
                self.addDir(params)
        
        if 0 == len(self.currList):
            self.listItems(cItem, cItem['category'], data)
        
    def listItems(self, cItem, nextCategory, data=None):
        printDBG("IplaTV.listItems [%s]" % cItem)
        page = cItem.get('page', 1)
        
        if data == None:
            sts, data = self.getPage(cItem['url'])
            if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', 'class="next_page"'), ('</a', '>'))[1]
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^'^"]+?)['"]''')[0])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', '"box_items"'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''[\s\-]src=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<p', '>', 'title'), ('</p', '>'), False)[1])
            desc  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<p', '>', 'description'), ('</p', '>'), False)[1])
            
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'desc':desc})
            
            if '/vod-' in url:
                item = self.cm.ph.getDataBeetwenNodes(item, ('<i', '>', '"free'), ('</i', '>'))[1]
                if 'no_show' in item: continue
                self.addVideo(params)
            else:
                params['category'] = nextCategory
                self.addDir(params)
        
        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'good_for_fav':False, 'title':_("Next page"), 'url':nextPage, 'page':page+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("IplaTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        if 0 == cItem.get('page', 0):
            cItem['f_search_query'] = searchPattern
            cItem['url'] = self.getFullUrl('/search/')
        self.listItems(cItem, 'explore_category')
        
    def getLinksForVideo(self, cItem):
        printDBG("IplaTV.getLinksForVideo [%s]" % cItem)
        retTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'start-watch-wrapper'), ('</div', '>'))[1]
        videoId = self.cm.ph.getSearchGroups(data, '''href=['"](ipla://[^'^"]+?)['"]''')[0].split('|', 1)[-1]
        videoUrl = 'http://getmedia.redefine.pl/vods/get_vod/?cpid=1&ua=mipla/23&media_id=%s' % videoId
        
        sts, data = self.getPage(videoUrl)
        if not sts: return []
        
        try:
            data = byteify(json.loads(data), '', True)
            protectedByDRM = False
            for item in data['vod']['copies']:
                if item['drmtype'] != '0': 
                    protectedByDRM = True
                    continue
                url = item['url']
                bitrate = item['bitrate']
                quality = item['quality_p']
                retTab.append({'name':'%s\t%s' % (quality, bitrate), 'url':url, 'bitrate':bitrate})
            if protectedByDRM and 0 == len(retTab):
                SetIPTVPlayerLastHostError(_('Video protected by DRM.'))
        except Exception:
            printExc()
            
        def __getLinkQuality( itemLink ):
            try:
                return int(itemLink['bitrate'])
            except Exception:
                printExc()
                return 0
        if len(retTab):
            maxBitrate = int(int(config.plugins.iptvplayer.iplaDefaultformat.value)*1.1)
            retTab = CSelOneLink(retTab, __getLinkQuality, int(maxBitrate)).getSortedLinks()
            if config.plugins.iptvplayer.iplaUseDF.value:
                retTab = [retTab[0]]
        
        return retTab
        
    def getArticleContent(self, cItem, data=None):
        printDBG("IplaTV.getArticleContent [%s]" % cItem)
        
        retTab = []
        
        otherInfo = {}
        
        if data == None:
            sts, data = self.getPage(cItem.get('prev_url', cItem['url']))
            if not sts: return []
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'plot'), ('</div', '>'), False)[1])
        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<h1', '>', 'big-title'), ('</h1', '>'), False)[1])
        icon  = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'avatar-container'), ('</div', '>'), False)[1]
        icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(icon, '''\ssrc=['"]([^'^"]+?)['"]''')[0])
        
        otherInfo['rating']   = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'item-vote'), ('</div', '>'), False)[1].split('</span>', 1)[-1])
        otherInfo['released'] = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<strong', '</strong>', 'Fecha'), ('</div', '>'), False)[1])
        otherInfo['duration'] = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<strong', '</strong>', 'Duración'), ('</div', '>'), False)[1])
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<strong', '</strong>', 'Género'), ('</ul', '>'), False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
        tmpTab = []
        for t in tmp:
            t = self.cleanHtmlStr(t)
            if t != '': tmpTab.append(t)
        otherInfo['genres'] = ', '.join(tmpTab)
        
        objRe = re.compile('<div[^>]+?text\-sub[^>]+?>')
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<li', '>', 'star-container'), ('</li', '>'), False)
        stars = []
        directors = []
        for t in tmp:
            t = objRe.split(t, 1)
            t[0] = self.cleanHtmlStr(t[0])
            if t[0] == '': continue
            if 2 == len(t):
                t[1] = self.cleanHtmlStr(t[1])
                if t[1] == 'Director':
                    directors.append(t[0])
                    continue
            stars.append(t[0])
        if len(directors): otherInfo['director'] = ', '.join(directors)
        if len(stars): otherInfo['stars'] = ', '.join(stars)
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
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
            self.listMainMenu({'name':'category'}, 'list_categories')
        elif category == 'list_categories':
            self.listCategories(self.currItem, 'explore_category')
        elif category == 'explore_category':
            self.exploreCategory(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_category')
        elif category == 'list_lists':
            self.listLists(self.currItem, 'list_items')
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, IplaTV(), True, [])
        
    #def withArticleContent(self, cItem):
    #    return cItem.get('good_for_fav', False)
    
    
    