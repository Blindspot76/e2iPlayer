# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVNotify
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, GetTmpDir, GetDefaultLang, CSelOneLink
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getMPDLinksWithMeta
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

def GetConfigList():
    optionList = []
    return optionList
###################################################
def gettytul():
    return 'http://questtv.co.uk/'

class QuesttvCoUK(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'questtv.co.uk', 'cookie':'questtv.co.uk.cookie', 'cookie_type':'MozillaCookieJar'})
        self.DEFAULT_ICON_URL = 'http://www.questtv.co.uk/wp-content/themes/dni_wp_theme_quest_uk/img/quest_logo.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'http://www.questtv.co.uk/'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        
        self.MAIN_CAT_TAB = [{'category':'list_playlists',    'title': _('On Demand'),       'url':self.getFullUrl('/video/')},
                             {'category':'list_abc',          'title': _('Shows A-Z'),       'url':self.getFullUrl('/shows/')},
                             {'category':'search',            'title': _('Search'),          'search_item':True}, 
                             {'category':'search_history',    'title': _('Search history')},
                            ]
                            
        
        self.cacheLinks    = {}
        self.cachePlaylist = {}
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urlparse.urljoin(baseUrl, url)
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def listPlaylists(self, cItem, nextCategory):
        printDBG("QuesttvCoUK.listPlaylists")
        
        self.cachePlaylist = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<section', '>', 'other_playlists'), ('</section', '>'))[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
        sections = {}
        for item in tmp:
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if url != '#': continue
            title = self.cleanHtmlStr(item)
            id = self.cm.ph.getSearchGroups(item, '''data=['"]([^'^"]+?)['"]''')[0]
            sections[id] = title
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'class="playlist'), ('<script', '>', 'javascript'))[1]
        data = re.compile('''(<div[^>]+?class="playlist[^>]+?>)''').split(data)
        for idx in range(1,len(data),2):
            id = self.cm.ph.getSearchGroups(data[idx], '''data=['"]([^'^"]+?)['"]''')[0]
            printDBG('>> id: %s' % id)
            if id not in sections: continue
            itemsTab = []
            items = self.cm.ph.getAllItemsBeetwenNodes(data[idx+1], ('<div', '>', 'video-playlist-thumb-box'), ('</a', '>'))
            for item in items:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''data\-url=['"]([^'^"]+?)['"]''')[0])
                if not self.cm.isValidUrl(url): continue
                title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h3', '</h3>')[1])
                desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p', '</p>')[1])
                icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                params = {'type':'video', 'title':title, 'url':url, 'desc':desc, 'icon':icon}
                itemsTab.append(params)
            
            if len(itemsTab):
                self.cachePlaylist[id] = itemsTab
                params = dict(cItem)
                params.update({'title':sections[id], 'id':id, 'category':nextCategory})
                self.addDir(params)
        
    def listPlaylist(self, cItem):
        printDBG("QuesttvCoUK.listPlaylist")
        self.listsTab(self.cachePlaylist[cItem['id']], {'name':'category', 'good_for_fav':True})
        
    def listABC(self, cItem, nextCategory):
        printDBG("QuesttvCoUK.listABC")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        ajaxUrl = self.cm.ph.getSearchGroups(data, '''var\s+?ajaxurl\s+?=\s+?['"]([^'^"]+?)['"]''')[0].replace('\\/', '/')
        postId = self.cm.ph.getSearchGroups(data, '''(<input[^>]+?post_id[^>]+?>)''')[0]
        postId = self.cm.ph.getSearchGroups(postId, '''value=['"]([^'^"]+?)['"]''')[0]
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'slides'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            title = self.cleanHtmlStr(item)
            id = self.cm.ph.getSearchGroups(item, '''#id=([^=^'^"^&]+?)[='"&]''')[0]
            if id == '': continue
            letter = self.cm.ph.getSearchGroups(item, '''letter=([^=^'^"^&]+?)[='"&]''')[0]
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':ajaxUrl, 'id':id, 'letter':letter, 'post_id':postId})
            self.addDir(params)
            
    def listShows(self, cItem, nextCategory):
        printDBG("QuesttvCoUK.listShows")
        page = cItem.get('page', 1)
        url = cItem['url'] + ('?action=dni_listing_items_filter&letter=%s&page=%s&id=%s&post_id=%s&view_type=grid' % (cItem['letter'], page, cItem['id'], cItem['post_id']))
        nextPage = False
        sts, data = self.getPage(url)
        if not sts: return
        try:
            data = byteify(json.loads(data))
            if data['total_pages'] > page:
                nextPage = True
            data = self.cm.ph.getAllItemsBeetwenMarkers(data['html'], '<a', '</a>')
            for item in data:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                if not self.cm.isValidUrl(url): continue
                title = self.cleanHtmlStr(item)
                icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                params = dict(cItem)
                params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon})
                self.addDir(params)
        except Exception:
            printExc()
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listEpisodes(self, cItem):
        printDBG("QuesttvCoUK.listEpisodes")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        episodesUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''href=['"]([^'^"]+?\-episodes/)['"]''')[0])
        
        if self.cm.isValidUrl(episodesUrl): 
            sts, tmp = self.getPage(episodesUrl)
            if sts: data += tmp
        
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<section', '>', 'pagetype-video'), ('</section', '>'))
        for tmp in data:
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
            for item in tmp:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                if not self.cm.isValidUrl(url): continue
                title = self.cleanHtmlStr(item)
                if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0]).replace('(DNI)', '').strip()
                icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                params = dict(cItem)
                params.update({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon})
                self.addVideo(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("QuesttvCoUK.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        url = '/search/?q=' + urllib.quote_plus(searchPattern)
        page = cItem.get('page', 1)
        if page > 1: url += '&pg=%s' % page
        
        sts, data = self.getPage(self.getFullUrl(url))
        if not sts: return
        
        if '>Next</a>' in data: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ol', '>', 'search-results'), ('</ol', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            if url == self.up.getDomain(url, False): continue
            if not self.cm.isValidUrl(url): continue
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<h4', '</h4>')[1]).split(' | ', 1)[0].strip()
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p', '</p>')[1])
            icon = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'desc':desc, 'icon':icon})
            if '/find-us/' in url:
                continue
            elif '/video/' in url:
                self.addVideo(params)
            else:
                params['category'] = 'list_episodes'
                self.addDir(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("QuesttvCoUK.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        videoId = self.cm.ph.getSearchGroups(data, '''data\-videoid=['"]([^'^"]+?)['"]''')[0]
        if videoId == '': return ''
        
        getParams = {}
        data = self.cm.ph.getDataBeetwenMarkers(data, '<object', '</object>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<param', '>')
        for item in data:
            name = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
            if name not in ['playerID', '@videoPlayer', 'playerKey']: continue
            value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
            getParams[name] = value
        
        mp4Tab = []
        url = 'http://c.brightcove.com/services/viewer/htmlFederated?' + urllib.urlencode(getParams)
        sts, data = self.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '"renditions":', ']', False)[1]
            try:
                printDBG(data)
                data = byteify(json.loads(data+']'), '', True)
                for item in data:
                    if item['videoCodec'] != 'H264': continue
                    url = item['defaultURL']
                    if not self.cm.isValidUrl(url): continue
                    name = '[mp4] bitrate: %s, %sx%s' % (item['encodingRate'], item['frameWidth'], item['frameHeight'])
                    mp4Tab.append({'name':name, 'url':url, 'bitrate':item['encodingRate']})
                    
                    def __getLinkQuality( itemLink ):
                        try: return int(itemLink['bitrate'])
                        except Exception: return 0
                    mp4Tab = CSelOneLink(mp4Tab, __getLinkQuality, 999999999).getSortedLinks()
            except Exception:
                printExc()
        
        hlsUrl = 'http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId=' + videoId
        hlsTab = getDirectM3U8Playlist(hlsUrl, checkContent=True, sortWithMaxBitrate=999999999)
        for idx in range(len(hlsTab)):
            hlsTab[idx]['name'] = '[hls] ' + hlsTab[idx]['name'].replace('None', '').strip()
        
        urlTab.extend(mp4Tab)
        urlTab.extend(hlsTab)
        return urlTab
       
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
        elif category == 'list_playlists':
            self.listPlaylists(self.currItem, 'list_playlist')
        elif category == 'list_playlist':
            self.listPlaylist(self.currItem)
        elif category == 'list_abc':
            self.listABC(self.currItem, 'list_shows')
        elif category == 'list_shows':
            self.listShows(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, QuesttvCoUK(), True, [])
    