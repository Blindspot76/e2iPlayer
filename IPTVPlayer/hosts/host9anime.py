# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, rm, GetPluginDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import DecodeGzipped, EncodeGzipped
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

try: from cStringIO import StringIO
except Exception: from StringIO import StringIO 
import gzip

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
        self.MAIN_URL = 'https://www6.9anime.is/'
        self.cacheEpisodes = {}
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.defaultParams = {'header':self.HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
        self.MAIN_CAT_TAB = [{'category':'list_filters',    'title': _('Home'),        'url':self.getFullUrl('/filter')      },
                             {'category':'list_items',      'title': _('Newest'),      'url':self.getFullUrl('/newest')      },
                             {'category':'list_items',      'title': _('Last update'), 'url':self.getFullUrl('/updated')     },
                             {'category':'list_items',      'title': _('Most watched'),'url':self.getFullUrl('/most-watched')},
                             {'category':'list_letters',    'title': _('A-Z List'),    'url':self.getFullUrl('/az-list')     },
                             
                             {'category':'search',            'title': _('Search'), 'search_item':True,},
                             {'category':'search_history',    'title': _('Search history'),            } 
                            ]
        self.scriptCache = {}
    
    def setMainUrl(self, url):
        if self.cm.isValidUrl(url):
            self.MAIN_URL = self.cm.getBaseUrl(url)
    
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
        self.setMainUrl(data.meta['url'])

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
        self.setMainUrl(data.meta['url'])
        
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
        self.setMainUrl(data.meta['url'])
        
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
        self.setMainUrl(data.meta['url'])
        
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
    
    def _getUrl(self, jsCode, url='', data='', timestamp=''):
        printDBG("AnimeTo._getUrl url[%s], data[%s], timestamp[%s]" % (url, data, timestamp))
        try:
            if False:
                tmp = EncodeGzipped('code')
                tmp = self._cryptoJS_AES(tmp, ''.join(GetPluginDir().split('/')[-5:]), False)
                tmp = hexlify(tmp)
                printDBG("$$$: " + tmp)
            else:
                tmp = '98ab1f3c676b9a8fb7b3a5595b0380e0bcbfa30415c262ebb0340b646ad6ab07f7ead7e8fec96b6f4dc251b97c9834a6c8c185eb9ad1f512a0f860d7448e2ebc711c0aa8fb19e7b979b264be904dd11cec89f98b5027c9d0b74d78cf7f63a5c7d48a73a136655bb6a5087210ec8ba1cb1e06fa933e3699124f6f9a23bfb320aa6300070a342b8a6f29189225e889fff2f322ae3e0277f189c28e0f88382d0c85144c28bdcd482c0b953b0cba88da4266e7d0a384b39b5c33cecf389f56d9fe27963acc417422d90cd3caee835d252156118576124024d8af4fd4bb230253013ea24bf19b59d4938b2a7ddd6a4aed5f9fb2806a36e5903869633e4834679bcfc7b892dad8b4f031a99be6389efc68c11a9de723dec354fc8b37a5989e787e20c16f928c5354958bd49cadf0f4f7deb9981f4b4e13587ecd6667d8dfbbd53e49848bbf1acfd45e304f03ea86fe9a3b2c482327b1672f3616e1a9a3ce443b471ce4524e5083f3eb22a9bf774770672d6fdc9d65f95cd78cac48562ca2b4574948d2924938569b7bf5be821be01331f545cd629f76fbd7e923569336a4cac2e2e0470f85dd9f41489fbff05c1ef37c4dc3779625136481ef4672b8b4aeb59116c203bd44a92484c71084fdb64b5d21ad3a758ddbff649aee9e9716223803b7aadb511c3bd34073d014a77533890aa02a764875b97934c4fd6a98199bc2d05de9232e9a1d4777667110e582feab7e4cf87a5a550225a5a7d8f61727f1fe1f03b5a90a8e5d2050e99abb8aa359ee6f6b5cfe1e204cace50ebe0c63f9e0216aab56f46359000cbb1e7cdd3f9223067f0075b1ccf1a8b1e93a82566966c5dfa1f9d0d4e29c8064b0a0f812f76d8628fd6af3fd00f9077006d17c076f23def58ad081971bf580963b06027602cb23d6e2217738c3efe3b51a057a5ff3234ee6c953334ca7a13fa89899e228f6587f2b749f1d51b7c664567451bdb23db6b265ce83414f42'
                tmp = self._cryptoJS_AES(unhexlify(tmp), ''.join(GetPluginDir().split('/')[-5:]))
                tmp = DecodeGzipped(tmp)
        except Exception:
            printExc()

        retUrl = ''
        jscode = ['iptv_ts=%s;' % timestamp, tmp, jsCode, 'iptv_arg = {url:"%s", "data":"%s"}; iptv_call(iptv_arg); print(JSON.stringify(iptv_arg));' % (url, data)]
        ret = iptv_js_execute('\n'.join(jscode), {'timeout_sec':15})
        if ret['sts'] and 0 == ret['code']:
            data = ret['data'].strip()
            try:
                data = byteify(json.loads(data))
                retUrl = data['url'] + '&' + data['data']
            except Exception:
                printExc()
        return retUrl
        
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
        
        cUrl = data.meta['url']
        allJsScripts = []
        jsCode = ''
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>', 'all.js'), ('</script', '>'))
        for item in tmp:
            jsUrl = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?all\.js(?:\?[^'^"]*?)?)['"]''')[0] )
            if jsUrl in self.scriptCache:
                jsCode = self.scriptCache[jsUrl]
                break
            allJsScripts.append(jsUrl)
        
        if jsCode == '':
            for item in allJsScripts:
                sts, tmp = self.getPage(item, params)
                if not sts: continue
                if '(window)' in tmp:
                    jsCode = tmp
                    self.scriptCache[jsCode] = jsCode
                    break

        if False:
            getParams = {'id':videoUrl.meta.get('id', ''), 'Q':'1'}
            url = self.getFullUrl('/ajax/film/update-views')
            url = self._getUrl(jsCode, url, urllib.urlencode(getParams), timestamp)
            sts, data = self.getPage(url, params)
            if not sts: return []
        
        getParams = {'id':videoUrl.meta.get('id', ''), 'random':'0'}
        url = self.getFullUrl('/ajax/episode/info')
        url = self._getUrl(jsCode, url, urllib.urlencode(getParams), timestamp)
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        domain = self.up.getDomain(baseUrl)
        printDBG(">> domain: " + domain)
        videoUrl = ''
        subTrack = ''
        try:
            data = byteify(json.loads(data))
            printDBG(data)
            subTrack = data.get('subtitle', '')
            if data['type'] == 'iframe':
                videoUrl = data['target']
                if domain in videoUrl:
                    videoUrl = self._getUrl(jsCode, videoUrl, "", timestamp)
                if videoUrl.startswith('//'): videoUrl = 'http:' + videoUrl
            elif data['type'] == 'direct':
                printDBG("----------------------------------------------")
                printDBG(data)
                printDBG("----------------------------------------------")
                if domain in data['grabber']:
                    url = self._getUrl(jsCode, data['grabber'], urllib.urlencode(dict(data['params'])), timestamp) + '&mobile=0'
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
        #getParams = self._updateParams(getParams)
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
    
    