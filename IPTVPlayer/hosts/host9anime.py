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
            
    def exploreItem(self, cItem):
        printDBG("AnimeTo.exploreItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        serverNamesMap = {}
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'servers'), ('</div', '>'))[1]
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<span', '>', 'data-name'), ('</span', '>'))
        for item in tmp:
            serverName = self.cleanHtmlStr(item)
            serverKey  = self.cm.ph.getSearchGroups(item, '''\sdata\-name=['"]([^'^"]+?)['"]''')[0]
            serverNamesMap[serverKey] = serverName
        
        titlesTab = []
        self.cacheLinks  = {}
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'data-name'), ('</ul', '>'))
        for tmp in data:
            if 'episodes' not in tmp: continue
            serverKey  = self.cm.ph.getSearchGroups(tmp, '''\sdata\-name=['"]([^'^"]+?)['"]''')[0]
            serverName = serverNamesMap.get(serverKey, serverKey)
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
            for item in tmp:
                title = self.cleanHtmlStr(item)
                id    = self.cm.ph.getSearchGroups(item, '''data-id=['"]([^'^"]+?)['"]''')[0]
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                if id == '' or url == '': continue 
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
            
        
    def _updateParams(self, params, params2=True,params3=True):
        if self._myFun == None:
            try:
                if True:
                    tmp = 'd4dc09ccf50eec3e8ff154e9aaae91d7929c817981b33e845bd0b59ba69cdee3c2d131462159801b5c5f8ca1593cf4340528e8cfd3f924c7bab5ae87f601e1c8f6218fc0901c805980b855bea9f665f31ff0396dadbcd5df601371897d5c156a06dc05b1f50736014a1eda203861858d500b67feca80d937f4108e0a961d399a9668084db2e0bd80af141f2f7b09d390324a25325af7eea4886dd17270e90a73dbec576074ddab2137dc3023607fbc86f549892c4d662c4122dc3b5bac1be0d739e6d2354bbeb8a4110654edb862630424c81d9b37b48be32ce174d90f1a52603af40e2a2bba1c26fc6cf660bed8ecac30e5fc4d479f2978036b9289a762d33f463881537d815d95fffd8d38b8a2f2d5a5ddf7270310eae29b48ac82a6a0c34b244f4c98864c10edcf65af2b9e550356f338fae937c1f502fa301f0c36e7837e9256a6b4e0bda84ecd8d5923a2c8feaa8a197195e93ac52688451b6b95252e26d70b4e79ac22b8445b72d98f796e65e674dcd7309a4f7ee2504856fc06f1c25af2d883a6c20bc3469767a46485b0bd6d1378e68216e1a10df259486fbde7b957165a3b06b70d13ffda13a61b2f2ddb919e302db25efbf7de2b0c1313e6db973707f957e9d624f8c941e4e9032abba3ae964b6b7a386b4ed09d59f2fadbcbaccb47513847b71cd42d6ffb1777d8813e65bd2bb59fb774635015618a0e345e33273d6f49213c90111c9e0a5a235aaa13679df3f38d6bb259e7a17cd3edd942b353cbd1034a69768489332e3719b55e64804c78e9986fa9535f0ee4ccb3521a734dd5695dcc5b9d9bfaa905cbfd952acd1a7f868ef35c1ccd4bff97cf49c0d12b92126e228f51eaf1fb2820698b965cb0466e930c4885712264447bbe4d9059c19f0fce59d61953afa7d7a3663bad90bd605f8cf63a2e41c2e56332966bb74c830e1721eafa02e9ec74beb3ab2219cc7e9d1e77703770370a647bf110aeecf244537ff60c016c49e8eea9ec103337c80bf11a9ea5a1992bfa9c3e116b419ae9f4ea69a764083c265edccfdcb97e20e1c27b03474da65e55ada8274126f5d5e86360446f24189e9cc9b482fbc70ee0522665decc717214bd7f632f2d788a3a85eba8f662ac2c934ffbd794cbc79e295fd8dc75a644972b6cdeb48bd28dddf05c6123e399c9f4891429a21b495b05ae1a7e9b8e2e1a51a2963583e26ed86d769e60ae454133b6a4129e2189cda0a0fdec9b0e96990c709ae888495a42bd2b5d3a88821a7006fbfc387d0ca7436e0dfbab0afce0d3af8c1350410e3017ad889a750c67ab36c153ffbc9a77b9ef707617cb03b0e66c5f354ce3eb04c39624294b23e4cff0eb43f153e5b8aac13e0388cbb689c84aa4c8009a1af593f5ef12d14ba142c886ab8eb56e8210172a1069effc58087d55c8076594359354d1a088c6c261c21dec49ae6f8e8bc2331674a73a37f600d498f08db9dbe781299520f70ae0e19992ee411a0d216b84e050c8372d463073b3f39bef6fda2b776edcbba79573acad6cad1b4ed605ff65fd5ad69bccf78b417b31c8e161a09d32de58662e44a351b4cfbd87d161a0a8037e07487a10107cf92deb61a16726a619d3ce90ff4e08ad31c307abafdf959674e95af39a03a02076a933ed5b435a127385aa2be398e173666204c6cc2b90d336acc08e8f62ed51da2ee458d1ce59f17d6658185839288d9d4d0524e7b03d2109d65085b58f7929f8e3d0db72859df4dfbcd65e05a7dd82ce77d5423d53c072d4b274fa1dc55816c0b8abfd9904120ca5ff8cf3254f606588d3b485fc7c1b56e60c38381c286741dbca0886b3e2225b64ab27421feec5434dadc1254f07786960f600d2a9fd0cede1dc8728202ce1738c9a2ea225a8397f0a3fd84bb42f724dbfafc1cc089c7744e7e85b1765daa153dd65db97c446d7001216218f93a6e40d1cb7f4d335006ba7f232beafc3a416755fdb59c81aea0b8ff0e35b8d03aa4c2efb526e8cf55f83683de213d8666f733a42032217e453981d65b12f58a09abfbb47ac8d3f6f55a66cc35143c03c29b841894807820c502b3a14ba06d4dea9fdeb203b7a74862c4af30c00d42082c8c02f4824f02cec35cefa9814e2ebd93eec3da2beccdc3b644f73768189dbea272146d3f749abf9a4e56e0bbf07c90c0c7be65ca4f9b02e428f598ed44e0ba97d149113fd68325114eb0791c6b868750a07d01af4fc8b9413338577d9cc5c2516009da3c84e8564c449e0a2418edaad147c854b3c3a901427f00e527874ea0fec3ce9b0d7f58724c9c4886cf08723a4da0af7418dfc6462c2b3b7e8dd079f23fd5483f19a029c39fd502118690a428abb4657b00102a36ccf461caffad0de94521a6abce56664b7805b32c77aa58421061c32a569c0f74da69f491865aaaa3e1ce4f1551edf99bb06cced0bc12787da5989497d2566ea8c1a0ab76e32885101b9f2c8f26f0e5fa45acaa042011802146eafe335cf1d0d51f6df18a5b9782f7146829dc9fb2107f977d6f497b92327958e6b666a6ce8636ca2b01c1eb00e896394982903ef0a7725ba5c54b8d90f8ee4e73a7d4c548dd38d3db7f2b8ff4b2c8097d140969d64a064e0566fe298094b143dc14afa6b6425a4224a63b51dfada8a6ad4571dabb91a6f5aa0878a623fed3f861d00172ac9ee9deb3b50a7cd9446bf00aabdc0ed88f9cbd18c764df9c43e8390430e4704c91dd497408c48af7d5117c71a1422fe9712a9b928cf973d1ce47f5f18e934248b4b19095ea82d9facdabd1c6097ed52abbd41c970c48fbb601c37256286719249bda0d009f945b2a0792bd5a70dae6f9a011a26057a4374'
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
        elif category == 'list_letters':
            self.listLetters(self.currItem, 'list_items')
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
    
    