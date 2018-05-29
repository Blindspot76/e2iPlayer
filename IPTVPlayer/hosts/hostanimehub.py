# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, RetHost, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify, rm, GetPluginDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.components.asynccall import iptv_js_execute
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import time
import re
import urllib
import string
import random
import base64
from urlparse import urlparse, urljoin
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
config.plugins.iptvplayer.animehub_proxy = ConfigSelection(default = "None", choices = [("None",     _("None")),
                                                                                        ("proxy_1",  _("Alternative proxy server (1)")),
                                                                                        ("proxy_2",  _("Alternative proxy server (2)"))])
config.plugins.iptvplayer.animehub_alt_domain = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Use proxy server:"), config.plugins.iptvplayer.animehub_proxy))
    if config.plugins.iptvplayer.animehub_proxy.value == 'None':
        optionList.append(getConfigListEntry(_("Alternative domain:"), config.plugins.iptvplayer.animehub_alt_domain))
    return optionList
###################################################

def gettytul():
    return 'https://animehub.to/'

class AnimehubTo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'yesmovies.to', 'cookie':'yesmovies.to.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        
        self.DEFAULT_ICON_URL = 'https://www.animehub.to/assets/images/logo2@2x.png'
        self.HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0', 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = None
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.defaultParams = {'with_metadata':True, 'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
            
        proxy = config.plugins.iptvplayer.animehub_proxy.value
        if proxy != 'None':
            if proxy == 'proxy_1':
                proxy = config.plugins.iptvplayer.alternative_proxy1.value
            else:
                proxy = config.plugins.iptvplayer.alternative_proxy2.value
            addParams = dict(addParams)
            addParams.update({'http_proxy':proxy})
        
        return self.cm.getPage(url, addParams, post_data)
        
    def setMainUrl(self, url):
        if self.cm.isValidUrl(url):
            self.MAIN_URL = self.cm.getBaseUrl(url)
        
    def getFullIconUrl(self, url):
        url = url.split('url=')[-1]
        url = self.getFullUrl(url)
        proxy = config.plugins.iptvplayer.animehub_proxy.value
        if proxy != 'None':
            if proxy == 'proxy_1':
                proxy = config.plugins.iptvplayer.alternative_proxy1.value
            else:
                proxy = config.plugins.iptvplayer.alternative_proxy2.value
            url = strwithmeta(url, {'iptv_http_proxy':proxy})
        return url
        
    def selectDomain(self):
        domains = ['https://www.animehub.to/']
        domain = config.plugins.iptvplayer.animehub_alt_domain.value.strip()
        if self.cm.isValidUrl(domain):
            if domain[-1] != '/': domain += '/'
            domains.insert(0, domain)
        
        for domain in domains:
            sts, data = self.getPage(domain)
            if sts and '/movies' in data:
                self.MAIN_URL = self.cm.getBaseUrl(data.meta['url'])
                break
            
            if self.MAIN_URL != None:
                break
                
        if self.MAIN_URL == None:
            self.MAIN_URL = domains[0]
    
    def listMainMenu(self, cItem, nextCategory1, nextCategory2, nextCategory3):
        if self.MAIN_URL == None: return
        
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'top-menu'), ('<div', '>', 'main'))[1]
        data = re.compile('(<li[^>]*?>|</li>|<ul[^>]*?>|</ul>)').split(data)
        if len(data) > 1:
            try:
                cTree = self.listToDir(data[1:-1], 0)[0]
                params = dict(cItem)
                params['c_tree'] = cTree['list'][0]
                params['category'] = nextCategory1
                self.listCategories(params, nextCategory2, nextCategory3)
            except Exception:
                printExc()
        
        MAIN_CAT_TAB = [#{'category':'list_filters',    'title': _('Filters'),      'url':self.getFullUrl('/filter')},
                        {'category':'search',          'title': _('Search'),       'search_item':True,      },
                        {'category':'search_history',  'title': _('Search history'),                        } 
                       ]
        self.listsTab(MAIN_CAT_TAB, cItem)
        
    def listCategories(self, cItem, nextCategory1, nextCategory2):
        printDBG("AnimehubTo.listCategories")
        try:
            cTree = cItem['c_tree']
            for item in cTree['list']:
                title = self.cleanHtmlStr(item['dat'])
                url   = self.getFullUrl(self.cm.ph.getSearchGroups(item['dat'], '''href=['"]([^'^"]+?)['"]''')[0])
                if 'list' not in item:
                    if self.cm.isValidUrl(url) and title != '':
                        if '/az-list' in url: cat = nextCategory1
                        else: cat = nextCategory2
                        params = dict(cItem)
                        params.update({'good_for_fav':False, 'category':cat, 'title':title, 'url':url})
                        self.addDir(params)
                        
                        if cat == nextCategory1:
                            break
                elif len(item['list']) == 1 and title != '':
                    params = dict(cItem)
                    params.update({'good_for_fav':False, 'c_tree':item['list'][0], 'title':title, 'url':url})
                    self.addDir(params)
        except Exception:
            printExc()
            
    def listAZ(self, cItem, nextCategory):
        printDBG("AnimehubTo.listAZ")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'az-list'), ('</ul', '>'), False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            title = self.cleanHtmlStr(item)
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            params = {'good_for_fav':False, 'name':'category', 'category':nextCategory, 'title':title, 'url':url}
            self.addDir(params)
        
    def fillCacheFilters(self, cItem):
        printDBG("AnimehubTo.fillCacheFilters")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        def addFilter(data, marker, baseKey, allTitle='', titleFormat=''):
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
                    allTitle = ''
                elif titleFormat != '':
                    title = titleFormat.format(title)
                self.cacheFilters[key].append({'title':title.title(), key:value})
                
            if len(self.cacheFilters[key]):
                if allTitle != '': self.cacheFilters[key].insert(0, {'title':allTitle})
                self.cacheFiltersKeys.append(key)
        
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'filter dropdown'), ('</ul', '>'))
        for tmp in data:
            if 'type[]' in tmp: continue
            titleFormat = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(tmp, ('<button', '>'), ('<', '>'), False)[1]) + ': {0}'
            key = self.cm.ph.getSearchGroups(tmp, '''name="([^"]+?)"''')[0]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
            addFilter(tmp, 'value', key, _('All'), titleFormat)
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("AnimehubTo.listFilters")
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
        printDBG("AnimehubTo.listItems")
        page = cItem.get('page', 1)
        url = cItem['url']
        
        if url.endswith('/filter'):
            query = {}
            keys = list(self.cacheFiltersKeys)
            keys.extend(['f_type[]', 'f_keyword'])
            for key in keys:
                baseKey = key[2:] # "f_"
                if key in cItem: query[baseKey] = cItem[key]
                
            if query != {}:
                if 'f_keyword' in cItem: url = self.getFullUrl('/search')
                else: url = self.getFullUrl('/filter')
            else:
                url = cItem['url']
            
            if page > 1: query['page'] = page
            query = urllib.urlencode(query)
            if '?' in url: url += '&' + query
            else: url += '?' + query
        
        sts, data = self.getPage(url)
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        nextPage = self.cm.ph.getSearchGroups(data, '''(<a\s+?[^>]*?rel=['"]next['"][^>]*?>)''')[0]
        nextPage = self.getFullUrl( self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^"^']+?)['"]''')[0] )
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', '-item'), ('</ul', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            if not self.cm.isValidUrl(url): continue
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(item, ('<', '>', 'item-title'), ('</', '>'))[1])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            if title == '': title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0])

            desc = []
            tmp = self.cm.ph.getAllItemsBeetwenNodes(item, ('<div', '>', 'gr-'), ('</div', '>'))
            tmp.append(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'item-eps'), ('</div', '>'))[1])
            for t in tmp:
                t = self.cleanHtmlStr(t)
                if t != '': desc.append(t)
            desc = ' | '.join(desc) 
            desc += '[/br]' + self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'desc'), ('<', '>', 'div'), False)[1])
            
            params = dict(cItem)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            params['category'] = nextCategory
            self.addDir(params)
        
        if nextPage != '':
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':_("Next page"), 'page':page+1, 'url':nextPage})
            self.addDir(params)
    
    def exploreItem(self, cItem):
        printDBG("AnimehubTo.exploreItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        dataId = self.cm.ph.getSearchGroups(data, '''data\-id=['"]([^'^"]+?)['"]''')[0]
        
        url = self.getFullUrl('/ajax/movie/episodes/') + dataId
        sts, data = self.getPage(url)
        if not sts: return
        cUrl = data.meta['url'].split('?', 1)[0]
        
        titlesTab = []
        self.cacheLinks  = {}
        try:
            data = byteify(json.loads(data))['html']
            tmpData = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'tablist'), ('</ul', '>'), False)[1]
            tmpData = self.cm.ph.getAllItemsBeetwenMarkers(tmpData, '<li', '</li>')
            for tmp in tmpData:
                serverName = self.cleanHtmlStr(tmp)
                serverId   = self.cm.ph.getSearchGroups(tmp, '''href=['"]\#([^'^"]+?)['"]''')[0]
                tmp = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', serverId), ('</ul', '>'), False)[1]
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
                for item in tmp:
                    title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<a', '</a>')[1])
                    id    = self.cm.ph.getSearchGroups(item, '''data-id=['"]([^'^"]+?)['"]''')[0]
                    url   = cUrl + '?e=' + id
                    if title not in titlesTab:
                        titlesTab.append(title)
                        self.cacheLinks[title] = []
                    url = strwithmeta(url, {'id':id, 'server_id':serverId})
                    self.cacheLinks[title].append({'name':serverName, 'url':url, 'need_resolve':1})
        except Exception:
            printExc()
        
        for item in titlesTab:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':'%s : %s' % (cItem['title'], item), 'links_key':item})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnimehubTo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('/search/') + urllib.quote_plus(searchPattern)
        cItem['category'] = 'list_items'
        self.listItems(cItem, 'explore_item')
    
    def getLinksForVideo(self, cItem):
        printDBG("AnimehubTo.getLinksForVideo [%s]" % cItem)
        key = cItem.get('links_key', '')
        return self.cacheLinks.get(key, [])
        
    def getVideoLinks(self, videoUrl):
        printDBG("AnimehubTo.getVideoLinks [%s]" % videoUrl)
        baseUrl = videoUrl
        videoUrl = strwithmeta(videoUrl)
        referer = str(baseUrl)
        
        urlTab = []
        subTracks = []
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
        
        params = dict(self.defaultParams)
        params['header'] = dict(self.AJAX_HEADER)
        params['header']['Referer'] = referer
        
        url = self.getFullUrl('/ajax/movie/get_sources/') + videoUrl.meta.get('id', '')
        sts, data = self.getPage(url, params)
        if not sts: return []
        
        try:
            tmp = byteify(json.loads(data))
            printDBG("----\n%s+++++\n" % tmp)
            if 'src' in tmp and tmp.get('embed', False):
                url = strwithmeta(tmp['src'], {'Referer':referer, 'User-Agent':params['header']['User-Agent']})
                urlTab = self.up.getVideoLinkExt(url)
            
            if isinstance(tmp['playlist'][0]['sources'], dict): tmp['playlist'][0]['sources'] = [tmp['playlist'][0]['sources']]
            for item in tmp['playlist'][0]['sources']:
                if "mp4" == item['type']:
                    urlTab.append({'name':str(item.get('label', 'default')), 'url':item['file']})
                elif "m3u8" == item['type']:
                    url = strwithmeta(item['file'], {'Referer':referer, 'User-Agent':params['header']['User-Agent']})
                    urlTab.extend(getDirectM3U8Playlist(url, checkContent=True))
            if isinstance(tmp['playlist'][0]['tracks'], dict): tmp['playlist'][0]['tracks'] = [tmp['playlist'][0]['tracks']]
            for item in tmp['playlist'][0]['tracks']:
                format = item['file'][-3:]
                if format in ['srt', 'vtt'] and "captions" == item['kind']:
                    subTracks.append({'title':str(item['label']), 'url':self.getFullIconUrl(item['file']), 'lang':item['label'], 'format':format})
        except Exception:
            printExc()
        
        printDBG(subTracks)
        urlParams = {'Referer':referer, 'User-Agent':params['header']['User-Agent']}
        if len(subTracks):
            urlParams.update({'external_sub_tracks':subTracks})
        
        for idx in range(len(urlTab)):
            urlTab[idx]['url'] = strwithmeta(urlTab[idx]['url'], urlParams)
        
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("SolarMovie.getArticleContent [%s]" % cItem)
        retTab = []
        
        params = dict(self.defaultParams)
        params['header'] = dict(self.AJAX_HEADER)
        params['header']['Referer'] = str(cItem['url'])
        
        sts, data = self.getPage(cItem['url'], params)
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'detail-anime'), ('<div', '>', 'goblock-bottom'), False)[1]
        
        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<h', '>', 'title'), ('</h', '>'), False)[1])
        icon  = self.getFullUrl( self.cm.ph.getSearchGroups(data, '''<img[^>]+?src=['"]([^'^"]+?)['"]''')[0] )
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'desc'), ('</div', '>'), False)[1])
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem['desc']
        if icon == '':  icon = cItem['icon']
        
        otherInfo = {}
        descData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<b>', '</div>')
        descTabMap = {"views":     "views",
                      "quality":   "quality",
                      "status":    "status",
                      "released":  "released",
                      "type":      "type",
                      "genre":     "genre"}
        
        otherInfo = {}
        for item in descData:
            item = item.split('</b>')
            if len(item) < 2: continue
            key = self.cleanHtmlStr( item[0] ).replace(':', '').strip().lower()
            val = self.cleanHtmlStr( item[1] ).replace(' , ', ', ')
            if key in descTabMap:
                try: otherInfo[descTabMap[key]] = val
                except Exception: continue
        
        tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'rating'), ('</div', '>'), False)[1].split('</strong> ', 1)[-1])
        if tmp != '': otherInfo['rating'] = tmp
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        if self.MAIN_URL == None:
            #rm(self.COOKIE_FILE)
            self.selectDomain()

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'}, 'list_categories', 'list_az', 'list_items')
        elif category == 'list_categories':
            self.listCategories(self.currItem, 'list_az', 'list_items')
        elif category == 'list_az':
            self.listAZ(self.currItem, 'list_items')
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
        CHostBase.__init__(self, AnimehubTo(), True, [])
    
    def withArticleContent(self, cItem):
        if cItem.get('type', 'video') != 'video' and cItem.get('category', 'unk') != 'explore_item':
            return False
        return True
    