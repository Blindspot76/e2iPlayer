# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, rm, GetPluginDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.components.asynccall import iptv_js_execute
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
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
from copy import deepcopy
from binascii import hexlify, unhexlify
from hashlib import md5
try:    import json
except Exception: import simplejson as json
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
    return 'https://9anime.is/'

class AnimeTo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'9anime.to', 'cookie':'9animeto.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.DEFAULT_ICON_URL = 'http://redeneobux.com/wp-content/uploads/2017/01/2-4.png'
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://9anime.is/'
        self.cacheEpisodes = {}
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
        self.MAIN_CAT_TAB = [{'category':'list_filters',    'title': _('Home'),        'url':self.getFullUrl('/filter')      },
                             {'category':'list_items',      'title': _('Newest'),      'url':self.getFullUrl('/newest')      },
                             {'category':'list_items',      'title': _('Last update'), 'url':self.getFullUrl('/updated')     },
                             {'category':'list_items',      'title': _('Most watched'),'url':self.getFullUrl('/most-watched')},
                             {'category':'list_letters',    'title': _('A-Z List'),    'url':self.getFullUrl('/az-list')     },
                             
                             {'category':'search',            'title': _('Search'), 'search_item':True,},
                             {'category':'search_history',    'title': _('Search history'),            } 
                            ]
        self._myFun = None
                            
    def getFullIconUrl(self, url):
        url = url.replace('&amp;', '&')
        return CBaseHostClass.getFullIconUrl(self, url)
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        def _getFullUrl(url):
            if self.cm.isValidUrl(url):
                return url
            else:
                return urlparse.urljoin(baseUrl, url)
            
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
    
    def listLetters(self, cItem, nextCategory):
        printDBG("AnimeTo.listLetters")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'letters'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            title = self.cleanHtmlStr( item )
            params = dict(cItem)
            params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
    
    def fillCacheFilters(self, cItem):
        printDBG("AnimeTo.listCategories")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(self.getFullUrl('ongoing'))
        if not sts: return
        
        def addFilter(data, marker, baseKey, addAll=True, titleBase=''):
            key = 'f_' + baseKey
            self.cacheFilters[key] = []
            for item in data:
                if ('name="%s"' % baseKey) not in item:
                    continue
                value = self.cm.ph.getSearchGroups(item, marker + '''="([^"]+?)"''')[0]
                if value == '':
                    continue
                title = self.cleanHtmlStr(item)
                if title.lower() in ['all', 'default', 'any']:
                    addAll = False
                self.cacheFilters[key].append({'title':title.title(), key:value})
                
            if len(self.cacheFilters[key]):
                if addAll: self.cacheFilters[key].insert(0, {'title':_('All')})
                self.cacheFiltersKeys.append(key)
        
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'filter dropdown'), ('</ul', '>'))
        for tmp in data:
            key = self.cm.ph.getSearchGroups(tmp, '''name="([^"]+?)"''')[0]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
            addFilter(tmp, 'value', key)
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("AnimeTo.listFilters")
        cItem = dict(cItem)
        
        f_idx = cItem.get('f_idx', 0)
        if f_idx == 0: self.fillCacheFilters(cItem)
        
        if f_idx >= len(self.cacheFiltersKeys): return
        
        filter = self.cacheFiltersKeys[f_idx]
        f_idx += 1
        cItem['f_idx'] = f_idx
        if f_idx  == len(self.cacheFiltersKeys):
            cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listItems(self, cItem, nextCategory):
        printDBG("AnimeTo.listItems")
        url = cItem['url']
        page = cItem.get('page', 1)
        
        query = {}
        if page > 1: query['page'] = page
        
        for key in self.cacheFiltersKeys:
            baseKey = key[2:] # "f_"
            if key in cItem: query[baseKey] = cItem[key]
        
        query = urllib.urlencode(query)
        if '?' in url: url += '&' + query
        else: url += '?' + query
        
        sts, data = self.getPage(url)
        if not sts: return
        
        if  '>Next<' in data: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'item'), ('<script', '>'))[1]
        data = self.cm.ph.rgetAllItemsBeetwenNodes(data, ('</div', '>'), ('<div', '>', 'item'))
        if nextPage and len(data): data[-1] = re.compile('<div[^>]+?paging\-wrapper[^>]+?>').split(data[-1], 1)[0]
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            tip = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'data-tip="([^"]+?)"')[0] )
            if not self.cm.isValidUrl(url): continue
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(item, ('<a', '>', 'name'), ('</a', '>'))[1])
            if title == '': title = self.cleanHtmlStr( item )
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])

            desc = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<div', '</div>')
            for t in tmp:
                t = self.cleanHtmlStr(t)
                if t != '': desc.append(t)
            desc = ' | '.join(desc) 
            desc += '[/br]' + self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p', '</p>')[1])
            
            params = dict(cItem)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'tip_url':tip, 'icon':icon, 'desc':desc}
            params['category'] = nextCategory
            self.addDir(params)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem, nextCategory):
        printDBG("AnimeTo.exploreItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'desc'), ('</div', '>'))[1])
        
        serverNamesMap = {}
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'servers'), ('</div', '>'))[1]
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<span', '>', 'data-name'), ('</span', '>'))
        for item in tmp:
            serverName = self.cleanHtmlStr(item)
            serverKey  = self.cm.ph.getSearchGroups(item, '''\sdata\-name=['"]([^'^"]+?)['"]''')[0]
            serverNamesMap[serverKey] = serverName
        
        rangesTab = []
        self.cacheEpisodes = {}
        self.cacheLinks  = {}
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'data-name'), ('<script', '>'))[1]
        data = re.compile('''(<div[^>]+?server[^>]+?>)''').split(data)
        for idx in range(1, len(data), 2):  
            if 'episodes' not in data[idx+1]: continue
            serverKey  = self.cm.ph.getSearchGroups(data[idx], '''\sdata\-name=['"]([^'^"]+?)['"]''')[0]
            serverName = serverNamesMap.get(serverKey, serverKey)
            
            rangeNameMap = {}
            tmp = self.cm.ph.getAllItemsBeetwenNodes(data[idx+1], ('<span', '>', 'data-range-id'), ('</span', '>'))
            for item in tmp:
                rangeName = self.cleanHtmlStr(item)
                rangeKey  = self.cm.ph.getSearchGroups(item, '''\sdata\-range\-id=['"]([^'^"]+?)['"]''')[0]
                rangeNameMap[rangeKey] = rangeName
            
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data[idx+1], '<ul', '</ul>')
            for rangeSection in tmp:
                rangeKey  = self.cm.ph.getSearchGroups(rangeSection, '''\sdata\-range\-id=['"]([^'^"]+?)['"]''')[0]
                rangeName = rangeNameMap.get(rangeKey, rangeKey)
                
                if rangeName not in rangesTab:
                    rangesTab.append(rangeName)
                    self.cacheEpisodes[rangeName] = []
                
                rangeSection = self.cm.ph.getAllItemsBeetwenMarkers(rangeSection, '<li', '</li>')
                for item in rangeSection:
                    title = self.cleanHtmlStr(item)
                    id    = self.cm.ph.getSearchGroups(item, '''data-id=['"]([^'^"]+?)['"]''')[0]
                    url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                    if id == '' or url == '': continue 
                    if title not in self.cacheEpisodes[rangeName]:
                        self.cacheEpisodes[rangeName].append(title)
                        self.cacheLinks[title] = []
                    url = strwithmeta(url, {'id':id})
                    self.cacheLinks[title].append({'name':serverName, 'url':url, 'need_resolve':1})
        
        for item in rangesTab:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category':nextCategory, 'series_title':cItem['title'], 'title':item, 'desc':desc, 'range_key':item})
            if 1 == len(rangesTab):
                self.listEpisodes(params)
                break
            self.addDir(params)
                
    def listEpisodes(self, cItem):
        printDBG("AnimeTo.listEpisodes")
        episodesTab = self.cacheEpisodes[cItem['range_key']]
        for item in episodesTab:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':'%s : %s' % (cItem['series_title'], item), 'links_key':item})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnimeTo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('search?keyword=' + urllib.quote_plus(searchPattern))
        self.listItems(cItem, 'explore_item')
        
    def getLinksForVideo(self, cItem):
        printDBG("AnimeTo.getLinksForVideo [%s]" % cItem)
        key = cItem.get('links_key', '')
        return self.cacheLinks.get(key, [])
        
    def uncensored(self, data):    
        cookieItems = {}
        try:
            jscode = base64.b64decode('''dmFyIGRvY3VtZW50ID0ge307DQp2YXIgd2luZG93ID0gdGhpczsNCnZhciBsb2NhdGlvbiA9ICJodHRwczovLzlhbmltZS50by8iOw0KU3RyaW5nLnByb3RvdHlwZS5pdGFsaWNzPWZ1bmN0aW9uKCl7cmV0dXJuICI8aT48L2k+Ijt9Ow0KU3RyaW5nLnByb3RvdHlwZS5saW5rPWZ1bmN0aW9uKCl7cmV0dXJuICI8YSBocmVmPVwidW5kZWZpbmVkXCI+PC9hPiI7fTsNClN0cmluZy5wcm90b3R5cGUuZm9udGNvbG9yPWZ1bmN0aW9uKCl7cmV0dXJuICI8Zm9udCBjb2xvcj1cInVuZGVmaW5lZFwiPjwvZm9udD4iO307DQpBcnJheS5wcm90b3R5cGUuZmluZD0iZnVuY3Rpb24gZmluZCgpIHsgW25hdGl2ZSBjb2RlXSB9IjsNCkFycmF5LnByb3RvdHlwZS5maWxsPSJmdW5jdGlvbiBmaWxsKCkgeyBbbmF0aXZlIGNvZGVdIH0iOw0KZnVuY3Rpb24gZmlsdGVyKCkNCnsNCiAgICBmdW4gPSBhcmd1bWVudHNbMF07DQogICAgdmFyIGxlbiA9IHRoaXMubGVuZ3RoOw0KICAgIGlmICh0eXBlb2YgZnVuICE9ICJmdW5jdGlvbiIpDQogICAgICAgIHRocm93IG5ldyBUeXBlRXJyb3IoKTsNCiAgICB2YXIgcmVzID0gbmV3IEFycmF5KCk7DQogICAgdmFyIHRoaXNwID0gYXJndW1lbnRzWzFdOw0KICAgIGZvciAodmFyIGkgPSAwOyBpIDwgbGVuOyBpKyspDQogICAgew0KICAgICAgICBpZiAoaSBpbiB0aGlzKQ0KICAgICAgICB7DQogICAgICAgICAgICB2YXIgdmFsID0gdGhpc1tpXTsNCiAgICAgICAgICAgIGlmIChmdW4uY2FsbCh0aGlzcCwgdmFsLCBpLCB0aGlzKSkNCiAgICAgICAgICAgICAgICByZXMucHVzaCh2YWwpOw0KICAgICAgICB9DQogICAgfQ0KICAgIHJldHVybiByZXM7DQp9Ow0KT2JqZWN0LmRlZmluZVByb3BlcnR5KGRvY3VtZW50LCAiY29va2llIiwgew0KICAgIGdldCA6IGZ1bmN0aW9uICgpIHsNCiAgICAgICAgcmV0dXJuIHRoaXMuX2Nvb2tpZTsNCiAgICB9LA0KICAgIHNldCA6IGZ1bmN0aW9uICh2YWwpIHsNCiAgICAgICAgcHJpbnQodmFsKTsNCiAgICAgICAgdGhpcy5fY29va2llID0gdmFsOw0KICAgIH0NCn0pOw0KQXJyYXkucHJvdG90eXBlLmZpbHRlciA9IGZpbHRlcjsNCiVzDQoNCg==''') % (data)                     
            ret = iptv_js_execute( jscode )
            if ret['sts'] and 0 == ret['code']:
                printDBG(ret['data'])
                data = ret['data'].split('\n')
                for line in data:
                    line = line.strip()
                    if not line.endswith('=/'): continue
                    line = line.split(';')[0]
                    line = line.replace(' ', '').split('=')
                    if 2 != len(line): continue
                    cookieItems[line[0]] = line[1].split(';')[0]
        except Exception:
            printExc()
        return cookieItems
        
    def _cryptoJS_AES(self, encrypted, password, decrypt=True):
        def derive_key_and_iv(password, key_length, iv_length):
            d = d_i = ''
            while len(d) < key_length + iv_length:
                d_i = md5(d_i + password).digest()
                d += d_i
            return d[:key_length], d[key_length:key_length+iv_length]
        bs = 16
        key, iv = derive_key_and_iv(password, 32, 16)
        cipher = AES_CBC(key=key, keySize=32)
        if decrypt:
            return cipher.decrypt(encrypted, iv)
        else:
            return cipher.encrypt(encrypted, iv)
            
        
    def _updateParams(self, params, params2=True,params3=True):
        if self._myFun == None:
            try:
                if True:
                    tmp = 'd4dc09ccf50eec3e8ff154e9aaae91d7929c817981b33e845bd0b59ba69cdee3c2d131462159801b5c5f8ca1593cf43406422ee379fc634b29045ebb16c59b296711085334eb391754d0da0059462a8b182e895aaf125160dfbfe09b7397a3f7819d232803b32af8a933a20eafcdf6f2a308fd314479089998bad79964c1d2d3b92480dbc42d5418565fdac3faac40615af34a52d8a6db7fe8851e43a148fae4678f949fe0b70a201807bd8f7d093468ebb63905b54812f6f5a4ff820337e641fb0252b2744123f871c3e76076359b7eea77d6b8207a8af9e360403df67a5f31bb31377f3b3e8cc3a118ce3c35e512313374b16526a28b6e315b587e746c2bf48b118a82a788bd849c852859abc7ab86a13e2d8756c6338749ecc878f6ee0244618bd3e38067879ce449e49b22b6e94d59e64334e28eeb89fcfd05e167f79d8c923b58bb9561aabd8b362fb2278c2bae46f1bebfcd4416580f44102d4def7fcd33e5f6021cde372582f21e75123ff0ea9e4c008cb87c64b225daff9968952a75edc7479d3fb66d886921ae2290a60fd7e13081336040ae44906c25b91e7e72efc37466e13d6d31279536effdbdea310cc9af66224f56244588943867c0b0f2acffc6200c3b4aed323f18a5a247739589749caae7b7bad38e2bc667f1a0f439b58df21bda6f35f54833254af0a35421c3e1a1090f169926f5d630e6e3e4bfe5a641c1a0696390caea942a5b4d46a939e2936c523f5e9532ac9fd5d112bd9c6d5099164edc930b0b307812cf77611d3f31f976c711422ee77aa0603c221bb7042c0d3cb5d7becb58df5a4ee229832a56e7c297f3df8f38155cad424c296e1ff0ff8e88141d6a7dffde1ffae467155c316ca423b95a320efd17ad2a0e44434c1f3d54ab5f31167fcb9764ca795c2d743551727d2eb9b923e4c55f0094d8585d7ea78cf0a75f22d09038b64fa4de7c28e670b2a1b8dc6c032771ae465c1ebaeac76c7c02a98fbe00f985b634d2985b35e298d1fe79db36577dd0194d65945c137fe3c863d50f4573d8db495b1b736debdd8b'
                    tmp = self._cryptoJS_AES(unhexlify(tmp), ''.join(GetPluginDir().split('/')[-5:]))
                    tmp = base64.b64decode(tmp.split('\r')[0]).replace('\r', '')
                _myFun = compile(tmp, '', 'exec')
                vGlobals = {"__builtins__": None, 'len': len, 'dict':dict, 'list': list, 'ord':ord, 'range':range, 'str':str, 'max':max, 'hex':hex, 'b64decode': base64.b64decode, 'True':True, 'False':False}
                vLocals = { 'zaraza': '' }
                exec _myFun in vGlobals, vLocals
                self._myFun = vLocals['zaraza']
            except Exception:
                printExc()
        try: params = self._myFun(params, params2)
        except Exception: printExc()
        return params
        
    def getVideoLinks(self, videoUrl):
        printDBG("AnimeTo.getVideoLinks [%s]" % videoUrl)
        baseUrl  = str(videoUrl)
        videoUrl = strwithmeta(videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
                        
        #sts, data = self.getPage(self.getFullUrl('token'))
        #if not sts: return []
        #cookieItem = self.uncensored(data)
        
        id = videoUrl.meta.get('id', '')
        params = dict(self.defaultParams)
        params['header'] = dict(self.AJAX_HEADER)
        params['header']['Referer'] = str(videoUrl)
        #params['cookie_items'] = cookieItem
        
        #sts, data = self.getPage('https://9anime.to/ajax/episode/info?id=%s&update=0' % id, params)
        #if not sts: return []
        
        sts, data = self.getPage(videoUrl[:videoUrl.rfind('/')], params)
        if sts: timestamp = self.cm.ph.getSearchGroups(data, '''data-ts=['"]([^"^']+?)['"]''')[0]
        else: timestamp = ''
        
        if timestamp == '': 
            sts, data = self.getPage(videoUrl, params)
            if not sts: return []
            timestamp = self.cm.ph.getSearchGroups(data, '''data-ts=['"]([^"^']+?)['"]''')[0]

        getParams = {'ts':timestamp, 'id':videoUrl.meta.get('id', ''), 'Q':'1'}
        getParams = self._updateParams(getParams)
        url = self.getFullUrl('/ajax/film/update-views?' + urllib.urlencode(getParams))
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        m = "++++++++++++++++++++++++++++++++"
        printDBG('%s\n%s\n%s' % (m, data, m))
        
        getParams = {'ts':timestamp, 'id':videoUrl.meta.get('id', ''), 'update':'0'}
        getParams = self._updateParams(getParams)
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> timestamp[%s]" % timestamp)
        url = self.getFullUrl('/ajax/episode/info?' + urllib.urlencode(getParams))
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        videoUrl = ''
        subTrack = ''
        try:
            data = byteify(json.loads(data))
            printDBG(data)
            subTrack = data.get('subtitle', '')
            if data['type'] == 'iframe':
                videoUrl = self._updateParams({'url':data['target']}, False)['url']
                if videoUrl.startswith('//'): videoUrl = 'http:' + videoUrl
            elif data['type'] == 'direct':
                printDBG("----------------------------------------------")
                printDBG(data)
                printDBG("----------------------------------------------")
                query = self._updateParams(dict(data['params']), False)
                query.update({'mobile':'0'})
                url = data['grabber']
                if '?' in url: url += '&'
                else: url += '?'
                url += urllib.urlencode(query)
                sts, data = self.getPage(url, params)
                if not sts: return []
                data = byteify(json.loads(data))
                for item in data['data']:
                    if item['type'] != 'mp4': continue
                    if not self.cm.isValidUrl(item['file']): continue
                    urlTab.append({'name':item['label'], 'url':item['file']})
                urlTab = urlTab[::-1]
            else:
                printDBG('Unknown url type!')
                printDBG(">>>>>>>>>>>>>>>>>>>>>")
                printDBG(data)
                printDBG("<<<<<<<<<<<<<<<<<<<<<")
        except Exception:
            printExc()

        if self.cm.isValidUrl(videoUrl) and 0 == len(urlTab):
            urlTab = self.up.getVideoLinkExt(strwithmeta(videoUrl, {'Referer':baseUrl}))
        
        if self.cm.isValidUrl(subTrack):
            format = subTrack[-3:]
            for idx in range(len(urlTab)):
                urlTab[idx]['url'] = strwithmeta(urlTab[idx]['url'])
                if 'external_sub_tracks' not in urlTab[idx]['url'].meta: urlTab[idx]['url'].meta['external_sub_tracks'] = []
                urlTab[idx]['url'].meta['external_sub_tracks'].append({'title':'', 'url':subTrack, 'lang':'pt', 'format':format})
        
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("SolarMovie.getArticleContent [%s]" % cItem)
        retTab = []
        
        params = dict(self.defaultParams)
        params['header'] = dict(self.AJAX_HEADER)
        params['header']['Referer'] = str(cItem['url'])
        
        sts, data = self.getPage(cItem['url'], params)
        if not sts: return []
        
        id = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'film-report'), ('<', '>'))[1]
        id = self.cm.ph.getSearchGroups(id, '''data-id=['"]([^'^"]+?)['"]''')[0]
        
        timestamp = self.cm.ph.getSearchGroups(data, '''data-ts=['"]([0-9]+?)['"]''')[0]
        
        printDBG("++++++++++++> timestamp[%s], id[%s]" % (timestamp, id))

        getParams = {'ts':timestamp}
        getParams = self._updateParams(getParams)
        url = self.getFullUrl('/ajax/film/tooltip/' + id + '?' + urllib.urlencode(getParams))
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        printDBG(data)
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<p class="desc">', '</p>')[1])
        if desc == '': desc = self.cleanHtmlStr(data.split('<div class="meta">')[-1]) 
        if desc == '': desc = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta property="og:description"[^>]+?content="([^"]+?)"')[0] )
        
        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="title">', '<span>')[1])
        if title == '': title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, '<meta property="og:title"[^>]+?content="([^"]+?)"')[0] )
        
        icon  = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<meta property="og:image"[^>]+?content="([^"]+?)"')[0] )
        
        if title == '': title = cItem.get('title', '')
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', '')
        
        otherInfo = {}
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<span class="duration"', '</span>')[1])
        if tmp != '': otherInfo['duration'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<span class="imdb"', '</span>')[1])
        if tmp != '': otherInfo['imdb_rating'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<[^>]+class="quality"'), re.compile('</span>'))[1])
        if tmp != '': otherInfo['quality'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Country:', '</div>', False)[1])
        if tmp != '': otherInfo['country'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Stars:', '</div>', False)[1])
        if tmp != '': otherInfo['stars'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Other names:', '</div>', False)[1])
        if tmp != '': otherInfo['alternate_title'] = tmp
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'Status:', '</div>', False)[1])
        if tmp != '': otherInfo['status'] = tmp
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'Genre:', '</div>', False)[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
        tmp = ', '.join([self.cleanHtmlStr(item) for item in tmp])
        if tmp != '': otherInfo['genre'] = tmp
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="title">', '</div>', False)[1]
        tmp = self.cm.ph.getSearchGroups(tmp, '''<span[^>]*?>\s*([0-9]+?)\s*<''')[0]
        if tmp != '': otherInfo['year'] = tmp
        
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
            self.cacheLinks = {}
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_items')
        elif category == 'list_letters':
            self.listLetters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
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
        CHostBase.__init__(self, AnimeTo(), True, [])
        
    def withArticleContent(self, cItem):
        if cItem['type'] != 'video' and cItem['category'] != 'explore_item':
            return False
        return True
    
    