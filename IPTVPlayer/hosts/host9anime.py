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
    return 'https://9anime.to/'

class AnimeTo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'9anime.to', 'cookie':'9animeto.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.DEFAULT_ICON_URL = 'http://redeneobux.com/wp-content/uploads/2017/01/2-4.png'
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://9anime.to/'
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
        self.MAIN_CAT_TAB = [{'category':'list_filters',    'title': _('Home'),        'url':self.getFullUrl('filter')        },
                             {'category':'list_items',      'title': _('Newest'),      'url':self.getFullUrl('newest')        },
                             {'category':'list_items',      'title': _('Last update'), 'url':self.getFullUrl('updated')       },
                             {'category':'list_items',      'title': _('Most watched'),'url':self.getFullUrl('most-watched')  },
                             #{'category':'list_items2',     'title': _('Upcoming'),   'url':self.getFullUrl('upcoming') },
                             
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
    
    def fillCacheFilters(self, cItem):
        printDBG("AnimeTo.listCategories")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(cItem['url'])
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
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="filter dropdown">', '</ul>')
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
            if key in cItem: query[baseKey] = urllib.quote(cItem[key])
        
        query = urllib.urlencode(query)
        if '?' in url: url += '&' + query
        else: url += '?' + query
        
        sts, data = self.getPage(url)
        if not sts: return
        
        if  '>Next<' in data: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="item">', '</div>')
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            tip = self.getFullUrl( self.cm.ph.getSearchGroups(item, 'data-tip="([^"]+?)"')[0] )
            if not self.cm.isValidUrl(url): continue
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            title = self.cleanHtmlStr( item )
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])

            params = dict(cItem)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'tip_url':tip, 'icon':icon}
            params['category'] = nextCategory
            self.addDir(params)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
            
    def exploreItem(self, cItem):
        printDBG("AnimeTo.exploreItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        titlesTab = []
        self.cacheLinks  = {}
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="servers">', '<div class="widget')[1]
        data = data.split('<div class="server row"')
        for tmp in data:
            serverName = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(tmp, '<label', '</label>')[1])
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
            for item in tmp:
                title = self.cleanHtmlStr(item)
                id    = self.cm.ph.getSearchGroups(item, '''data-id=['"]([^'^"]+?)['"]''')[0]
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                if title not in titlesTab:
                    titlesTab.append(title)
                    self.cacheLinks[title] = []
                url = strwithmeta(url, {'id':id})
                self.cacheLinks[title].append({'name':serverName, 'url':url, 'need_resolve':1})
        
        for item in titlesTab:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':'%s : %s' % (cItem['title'], item), 'links_key':item})
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
            
        
    def _updateParams(self, params):
        if self._myFun == None:
            try:
                tmp = 'd4dc09ccf50eec3e8ff154e9aaae91d70fd5cb194964f86c2f2b4dda892d816ca7515b17a77760b52b0fa8ada0f4404a51c9485e13b96e508e6630b076d3af9b4915c3fba4c93ea7bf07839938a08243ec03e518960cad35077cdb5060dd677be8f1def1b057dfc86887a4a7f52350fcf9dddbe96b59a2c6e22ec6accb515c95a1d306c5b8bfb6213d553433ed87c8355f1e5cc057d3d79b004b0338d645a20ec0712a5396bde975ffbe5c90a67a1c52cc275f62dd9600d5d482fb74c8e2dbfd9f1e1f27f17aaca3650d1cd025b52eb810bd438f9ea2ababccdf861eefeb932f81370c7a5eb3bbe8679aeb9a96ae923becdde1b010bb16796473feb3750407bc9f794703fda58501ba1a4f20a964dfa2a30f607736342a3fa47e8a0efa3440e33c8ae36b6f9f9740826b52b8a103f176dfe121d49c740a14436294dc5a957ac3057d33693763c3a85535536ac83e1c6faa1251200f324555a6f8c2080f90b2d557e1e08690489bd6e6b684f01eaa39a8aa9e5eb4c587ef4341a5940d4213c0814437cd34c48e6454e6e0cf9307ceb8c439e36f483eee4465eb451e1a83b330158dc55a8aaac8c7955d5c05542de31f8a44164365caf92de8a321dad1b07a5807e75fef0156b503a873b781f4f94886595cb3fadef717b2d0c789c3cf153a206188a2ee844c265c8fa8245cdc91b688b602d3ec514649b6a24709885920a11a065f1a63e4e1d8e69935e3edf8fda397ec4929f05d08c47ea107a2d9b5e556dd3b6f96391c1cfd3e09e7abc0b269a6c6ccb73e960c06f196590677a3c2eb0b79bee0f00983e79cea0f60b18b20f3b2d76044c5582955d27f60a75f12fd90257bd820797a01390ab6e3b0af8745b82eaaa64fabff78fb36f4923d312c7dbe84166dc8fe473fee9c1b03206e648917991497b2b56a427b39a5bf6c37ef76147fc65665932018a6381c960097805c31bc05a35a6d33eaf62cc88ee060669d30684afd0832533fcbf33939a5340b508884fa2fd973a15968b4ba57cec1fffea3584ec6'
                tmp = self._cryptoJS_AES(unhexlify(tmp), ''.join(GetPluginDir().split('/')[-5:]))
                tmp = base64.b64decode(tmp.split('\r')[0]).replace('\r', '')
                
                _myFun = compile(tmp, '', 'exec')
                vGlobals = {"__builtins__": None, 'len': len, 'dict':dict, 'list': list, 'ord':ord, 'range':range, 'str':str, 'max':max, 'hex':hex}
                vLocals = { 'zaraza': '' }
                exec _myFun in vGlobals, vLocals
                self._myFun = vLocals['zaraza']
            except Exception:
                printExc()
        try: params = self._myFun(params)
        except Exception: printExc()
        return params
        
    def getVideoLinks(self, videoUrl):
        printDBG("AnimeTo.getVideoLinks [%s]" % videoUrl)
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
                        
        sts, data = self.getPage(self.getFullUrl('token'))
        if not sts: return []
        cookieItem = self.uncensored(data)
        
        id = videoUrl.meta.get('id', '')
        params = dict(self.defaultParams)
        params['header'] = dict(self.AJAX_HEADER)
        params['header']['Referer'] = str(videoUrl)
        params['cookie_items'] = cookieItem
        
        #sts, data = self.getPage('https://9anime.to/ajax/episode/info?id=%s&update=0' % id, params)
        #if not sts: return []
        
        sts, data = self.getPage(videoUrl, params)
        if not sts: return []
        
        timestamp = self.cm.ph.getSearchGroups(data, '''data-ts=['"]([0-9]+?)['"]''')[0]

        getParams = {'ts':timestamp, 'id':videoUrl.meta.get('id', ''), 'Q':'1'}
        getParams = self._updateParams(getParams)
        url = self.getFullUrl('/ajax/film/update-views?' + urllib.urlencode(getParams))
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        m = "++++++++++++++++++++++++++++++++"
        printDBG('%s\n%s\n%s' % (m, data, m))
        
        getParams = {'ts':timestamp, 'id':videoUrl.meta.get('id', ''), 'update':'0'}
        getParams = self._updateParams(getParams)
        
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
                videoUrl = data['target']
                if videoUrl.startswith('//'): videoUrl = 'http:' + videoUrl
            elif data['type'] == 'direct':
                query = dict(data['params'])
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
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
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
        
        id = self.cm.ph.getSearchGroups(data, '''<([^>]+?class="watchpage"[^>]*?)>''')[0]
        id = self.cm.ph.getSearchGroups(id, '''data-id=['"]([^'^"]+?)['"]''')[0]
        
        timestamp = self.cm.ph.getSearchGroups(data, '''data-ts=['"]([0-9]+?)['"]''')[0]

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
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
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
        CHostBase.__init__(self, AnimeTo(), True, [])
        
    def withArticleContent(self, cItem):
        if cItem['type'] != 'video' and cItem['category'] != 'explore_item':
            return False
        return True
    
    