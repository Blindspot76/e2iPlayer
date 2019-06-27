# -*- coding: utf-8 -*-
###################################################
# 2019-06-11 by Alec - modified Mozicsillag
###################################################
HOST_VERSION = "1.1"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify, GetIPTVPlayerVerstion
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import re
import urllib
import random
import os
import datetime
import time
import zlib
import cookielib
import base64
import traceback
try:
    import json
except Exception:
    import simplejson as json
from Components.config import config, ConfigText, ConfigYesNo, getConfigListEntry
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS
from datetime import datetime
from hashlib import sha1
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.mozicsillag_id = ConfigYesNo(default = False)
config.plugins.iptvplayer.boxtipus = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.boxrendszer = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("id:", config.plugins.iptvplayer.mozicsillag_id))
    return optionList
###################################################

def gettytul():
    return 'https://mozicsillag.me/'

class MuziCsillangCC(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'mozicsillag.cc', 'cookie':'mozicsillag.cc.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://mozicsillag.me/'
        self.DEFAULT_ICON_URL =  strwithmeta('https://mozicsillag.me/img/logo.png', {'Referer':self.getMainUrl()})
        self.vivn = GetIPTVPlayerVerstion()
        self.porv = self.gits()
        self.pbtp = '-'
        self.btps = config.plugins.iptvplayer.boxtipus.value
        self.brdr = config.plugins.iptvplayer.boxrendszer.value
        self.aid = config.plugins.iptvplayer.mozicsillag_id.value
        self.aid_ki = ''
        self.ilk = False
        self.cacheLinks    = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.cacheSortOrder = []
        self.defaultParams = {'header':self.HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
                            
    def getFullIconUrl(self, url):
        if url == '': return url
        url = url.replace('&amp;', '&')
        url = CBaseHostClass.getFullIconUrl(self, url)
        return strwithmeta(url, {'Referer':self.getMainUrl()})
        
    def setMainUrl(self, url):
        if self.cm.isValidUrl(url):
            self.MAIN_URL = self.cm.getBaseUrl(url)
        
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
        
    def listMainMenu(self, cItem):
        try:
            self.cacheLinks = {}
            if not self.ebbtit(): return
            if self.btps != '' and self.brdr != '': self.pbtp = self.btps.strip() + ' - ' + self.brdr.strip()
            tab_catalog = 'mozicsillag_catalog'
            desc_catalog = self.getdvdsz(tab_catalog, 'Főoldali felvételek megjelenítése...')
            tab_movies = 'mozicsillag_movies'
            desc_movies = self.getdvdsz(tab_movies, 'Filmek megjelenítése...')
            tab_series = 'mozicsillag_series'
            desc_series = self.getdvdsz(tab_series, 'Sorozatok megjelenítése...')
            tab_search = 'mozicsillag_search'
            desc_search = self.getdvdsz(tab_search, 'Keresés...')
            tab_search_hist = 'mozicsillag_search_hist'
            desc_search_hist = self.getdvdsz(tab_search_hist, 'Keresés az előzmények között...')
            MAIN_CAT_TAB = [{'category':'list_filters', 'title': _('Home'), 'url':self.getMainUrl(), 'use_query':True, 'tab_id':tab_catalog, 'desc':desc_catalog },
                            {'category':'list_movies', 'title': _('Movies'), 'url':self.getMainUrl(), 'tab_id':tab_movies, 'desc':desc_movies },
                            {'category':'list_series', 'title': _('Series'), 'url':self.getMainUrl(), 'tab_id':tab_series, 'desc':desc_series },
                            {'category':'search', 'title': _('Search'), 'search_item':True, 'tab_id':tab_search, 'desc':desc_search },
                            {'category':'search_history', 'title': _('Search history'), 'tab_id':tab_search_hist, 'desc':desc_search_hist }
                           ]
            self.listsTab(MAIN_CAT_TAB, {'name':'category'})
            self.ilk = True
        except Exception:
            printExc()
    
    def fillCacheFilters(self, cItem):
        printDBG("MuziCsillangCC.listCategories")
        self.cacheFilters = {}
        self.cacheFiltersKeys = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(data.meta['url'])
        
        def addFilter(data, marker, baseKey, allTitle='', titleBase=''):
            key = 'f_' + baseKey
            self.cacheFilters[key] = []
            for item in data:
                type  = self.cm.ph.getSearchGroups(item, '''type="([^"]+?)"''')[0]
                value = self.cm.ph.getSearchGroups(item, marker + '''="([^"]+?)"''')[0]
                if value == '': continue
                title = self.cleanHtmlStr(item)
                if title in ['Összes']:
                    allTitle = ''
                self.cacheFilters[key].append({'title':title.title(), key:value, ('%s_type' % key):type })
                
            if len(self.cacheFilters[key]):
                if allTitle != '': self.cacheFilters[key].insert(0, {'title':allTitle})
                self.cacheFiltersKeys.append(key)
                
        # search_type
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input id="search_type', '</label>')
        if len(tmp): addFilter(tmp, 'value', 'search_type')
        
        # search_sync_
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input id="search_sync_', '</label>')
        if len(tmp): addFilter(tmp, 'value', 'search_sync_', _('Any'))
        
        # search_rating_start
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<select id="search_rating_start"', '</select>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<option', '</option>')[::-1]
        if len(tmp): addFilter(tmp, 'value', 'search_rating_start', _('Any'))
        
        # year
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<select id="search_year_from"', '</select>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<option', '</option>')[::-1]
        if len(tmp): addFilter(tmp, 'value', 'year', _('Any'), 'IMDB pont')
        
        # search_categ_
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input id="search_categ_', '</label>')
        if len(tmp) > 1: tmp = tmp[2:]
        if len(tmp): addFilter(tmp, 'value', 'search_categ_', _('Any'))
        
        # search_qual_
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input id="search_qual_', '</label>')
        if len(tmp): addFilter(tmp, 'value', 'search_qual_', _('Any'))
        
        # search_share_
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input id="search_share_', '</label>')
        if len(tmp): addFilter(tmp, 'value', 'search_share_', _('Any'))
        
        printDBG(self.cacheFilters)
        
    def listFilters(self, cItem, nextCategory):
        printDBG("MuziCsillangCC.listFilters")
        if self.ilk:
            self.susn('2', '5', 'mozicsillag_catalog')
            self.ilk = False
        cItem = dict(cItem)
        cItem['desc'] = ''
        
        f_idx = cItem.get('f_idx', 0)
        if f_idx == 0: self.fillCacheFilters(cItem)
        
        if 0 == len(self.cacheFiltersKeys): return
        
        filter = self.cacheFiltersKeys[f_idx]
        f_idx += 1
        cItem['f_idx'] = f_idx
        if f_idx  == len(self.cacheFiltersKeys):
            cItem['category'] = nextCategory
        self.listsTab(self.cacheFilters.get(filter, []), cItem)
        
    def listItems(self, cItem, nextCategory):
        printDBG("MuziCsillangCC.listItems")
        
        url = cItem['url']
        page = cItem.get('page', 1)
        sort = cItem.get('f_sort', '')
        
        query = ''
        if cItem.get('use_query', False):
            url = self.getFullUrl('/kereses/')
            query += 'search_type=%s&' % cItem.get('f_search_type', '0')
            query += 'search_where=%s&' % cItem.get('f_search_where', '0')
            query += 'search_rating_start=%s&search_rating_end=10&' % cItem.get('f_search_rating_start', '1')
            query += 'search_year_from=%s&search_year_to=%s&' % (cItem.get('f_year', '1900'), cItem.get('f_year', '2090'))
            if 'f_search_sync_' in cItem: query += 'search_sync_%s=%s&' % (cItem['f_search_sync_'], cItem['f_search_sync_'])
            if 'f_search_categ_' in cItem: query += 'search_categ_%s=%s&' % (cItem['f_search_categ_'], cItem['f_search_categ_'])
            if 'f_search_qual_' in cItem: query += 'search_qual_%s=%s&' % (cItem['f_search_qual_'], cItem['f_search_qual_'])
            if 'f_search_share_' in cItem: query += 'search_share_%s=%s&' % (cItem['f_search_share_'], cItem['f_search_share_'])
            if query.endswith('&'): query = query[:-1]
            printDBG('>>> query[%s]' % query)
        
        if not url.endswith('/'): url += '/'
        if sort != '': url += sort + '/'
        if query != '': url += base64.b64encode(query)
        if page > 1: url += '?page=%s' % page
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, 'pagination', '</ul>')[1]
        if  '' != self.cm.ph.getSearchGroups(nextPage, 'page=(%s)[^0-9]' % (page+1))[0]: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="small-block-grid', '</ul>')[1]        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        reFlagObj = re.compile('''<img[^>]+?src=['"][^"^']+?/([^/]+?)\.png['"]''')
        for item in data:
            url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0] )
            if not self.cm.isValidUrl(url): continue
            
            icon = self.getFullIconUrl( self.cm.ph.getSearchGroups(item, '''data-original=['"]([^"^']+?\.jpe?g)''')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<strong', '</strong>')[1] )
            if title == '': title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1] )
            
            # desc start
            descTab = []
            tmp = self.cm.ph.getDataBeetwenMarkers(item, '</strong>', '</div>')[1]
            flags = reFlagObj.findall(tmp)
            if len(flags): descTab.append(' | '.join(flags))
            tmp = tmp.split('<br>')
            for t in tmp:
                t = self.cleanHtmlStr(t)
                if t == '': continue
                descTab.append(t)
            ######
            
            params = dict(cItem)
            params = {'good_for_fav': True, 'title':title, 'url':url, 'desc':'[/br]'.join(descTab), 'icon':icon}
            params['category'] = nextCategory
            self.addDir(params)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
            
    def _listCategories(self, cItem, nextCategory, m1, m2):
        printDBG("MuziCsillangCC._listCategories")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params['desc'] = ''
            params.update({'category':nextCategory, 'title':title, 'url':url})
            self.addDir(params)
        
    def listMovies(self, cItem, nextCategory):
        printDBG("MuziCsillangCC.listMovies")
        tabID = cItem['tab_id']
        if tabID != '':
            self.susn('2', '5', tabID)
        self._listCategories(cItem, nextCategory, 'Filmek</a>', 'has-dropdown not-click')
        
    def listSeries(self, cItem, nextCategory):
        printDBG("MuziCsillangCC.listSeries")
        tabID = cItem['tab_id']
        if tabID != '':
            self.susn('2', '5', tabID)
        self._listCategories(cItem, nextCategory, 'Sorozatok</a>', '/sztarok"')
        
    def listSort(self, cItem, nextCategory):
        printDBG("MuziCsillangCC.listSeries")
        cItem['desc'] = ''
        if 0 == len(self.cacheSortOrder):
            sts, data = self.getPage(self.getFullUrl('/filmek-online')) # sort order is same for movies and series
            if not sts: return
            data = self.cm.ph.getDataBeetwenMarkers(data, '<dl ', '</dl>')[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
            for item in data:
                sort  = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0].split('/')[-1]
                if sort == '': continue
                title = self.cleanHtmlStr(item)
                self.cacheSortOrder.append({'title':title, 'f_sort':sort})
        
        for item in self.cacheSortOrder:
            params = dict(cItem)
            params.update({'category':nextCategory})
            params.update(item)
            self.addDir(params)
        
    def exploreItem(self, cItem):
        printDBG("MuziCsillangCC.exploreItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        lastUrl = data.meta['url']
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<p>', '</p>')[1])
        desc = re.sub(r'^(.{1000}).*$', '\g<1>...', desc)
        
        # trailer 
        tmp = self.cm.ph.rgetAllItemsBeetwenMarkers(data, '</iframe>', '<h2')
        for idx in xrange(len(tmp)):
            url = self.getFullUrl(self.cm.ph.getSearchGroups(tmp[idx], '''src=['"]([^'^"]+?)['"]''')[0])
            if url.endswith('/thanks'): continue
            title = self.cleanHtmlStr(tmp[idx])
            if title.endswith(':'): title = title[:-1]
            if title == '': title = '%s - %s' %(cItem['title'], _('trailer'))
            if 1 == self.up.checkHostSupport(url):
                params = dict(cItem)
                params.update({'good_for_fav': False, 'title':'%s. %s' % (idx+1, title), 'prev_title':cItem['title'], 'url':url, 'prev_url':cItem['url'], 'prev_desc':cItem.get('desc', ''), 'desc':desc})
                self.addVideo(params)
        
        sourcesLink = self.cm.ph.rgetDataBeetwenMarkers2(data, 'Beküldött linkek megtekintése', '<a', caseSensitive=False)[1]
        sourcesLink = self.cm.ph.getSearchGroups(sourcesLink, '''href=['"](https?://[^'^"]+?)['"]''')[0]
        if not self.cm.isValidUrl(sourcesLink):
            printDBG("MuziCsillangCC.exploreItem - missing link for sources")
            return
        
        if sourcesLink != '':
            sts, data = self.getPage(sourcesLink)
            if not sts: return
            lastUrl = data.meta['url']
        
        sourcesLink = self.cm.ph.getSearchGroups(data, '''<a[^>]+?href=['"](https?://[^'^"]+?)['"][^>]*?>Lejatszas''')[0]
        if sourcesLink != '':
            sts, data = self.getPage(sourcesLink)
            if not sts: return
            lastUrl = data.meta['url']
        
        self.cacheLinks  = {}
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="links_holder', '<script type="text/javascript">', False)[1]
        data = data.split('accordion-episodes')
        episodesTab = []
        for tmp in data:
            episodeName = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(tmp, '<h3', '</h3>')[1])
            
            tmp = tmp.split('panel')
            for item in tmp:
                printDBG(">>>>>>>>>>>> [%s]" % item)
                url = self.cm.ph.getSearchGroups(item, '''<a[^>]+?href=['"]([^'^"]*?watch[^'^"]*?)['"]''')[0]
                
                if url != '': url = self.getFullUrl(url, lastUrl)
                if not self.cm.isValidUrl(url): continue
                serverName = []
                item = self.cm.ph.getAllItemsBeetwenMarkers(item, '<div', '</div>')
                for t in item:
                    if 'link_flag' in t:
                        t = self.cm.ph.getSearchGroups(t, '''<img[^>]+?src=['"][^"^']+?/([^/]+?)\.png['"]''')[0]
                    t = self.cleanHtmlStr(t)
                    if t != '': serverName.append(t)
                serverName = ' | '.join(serverName)
                
                if episodeName not in episodesTab:
                    episodesTab.append(episodeName)
                    self.cacheLinks[episodeName] = []
                self.cacheLinks[episodeName].append({'name':serverName, 'url':url, 'need_resolve':1})
        
        for item in episodesTab:
            params = dict(cItem)
            title = cItem['title']
            if item != '': title += ' : ' + item
            params.update({'good_for_fav': False, 'title':title, 'links_key':item, 'prev_desc':cItem.get('desc', ''), 'desc':desc})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("MuziCsillangCC.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))        
        cItem = dict(cItem)
        query = base64.b64encode('search_term=%s&search_type=0&search_where=0&search_rating_start=1&search_rating_end=10&search_year_from=1900&search_year_to=2100' % urllib.quote_plus(searchPattern) ) 
        cItem['url'] = self.getFullUrl('kereses/' + query)
        self.listItems(cItem, 'explore_item')
        
    def getLinksForVideo(self, cItem):
        printDBG("MuziCsillangCC.getLinksForVideo [%s]" % cItem)
        retTab = []
        if 1 == self.up.checkHostSupport(cItem.get('url', '')):
            videoUrl = cItem['url'].replace('youtu.be/', 'youtube.com/watch?v=')
            return self.up.getVideoLinkExt(videoUrl)
        key = cItem.get('links_key', '')
        return self.cacheLinks.get(key, [])
        
    def getVideoLinks(self, videoUrl):
        printDBG("MuziCsillangCC.getVideoLinks [%s]" % videoUrl)
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

        sts, data = self.cm.getPage(videoUrl, self.defaultParams)
        videoUrl = self.cm.meta.get('url', videoUrl)
        
        if 1 != self.up.checkHostSupport(videoUrl):
            if not sts: return []
            
            printDBG(data)
            tmp = re.compile('''<iframe[^>]+?src=['"]([^"^']+?)['"]''', re.IGNORECASE).findall(data)
            for url in tmp:
                if 1 == self.up.checkHostSupport(url):
                    videoUrl = url
                    break
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('MuziCsillangCC.getFavouriteData')
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem['desc'], 'icon':cItem['icon']}
        return json.dumps(params) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('MuziCsillangCC.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('MuziCsillangCC.setInitListFromFavouriteItem')
        if self.MAIN_URL == None:
            self.selectDomain()
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def getArticleContent(self, cItem):
        printDBG("MuziCsillangCC.getArticleContent [%s]" % cItem)
        retTab = []
        
        otherInfo = {}
        
        url = cItem.get('prev_url', '')
        if url == '': url = cItem.get('url', '')
        
        sts, data = self.getPage(url)
        if not sts: return retTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="row" id="content-tab">', '<div id="zone')[1]
        
        title = '' #self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="f_t_b">', '</div>')[1])
        icon  = self.getFullIconUrl( self.cm.ph.getSearchGroups(data, '''<img[^>]+?src=['"]([^"^']+?\.jpe?g[^"^']*?)["']''')[0] )
        desc  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<p>', '</p>', False)[1])
        
        for item in [('Rendező(k):', 'directors'),
                     ('Színészek:',     'actors'),
                     ('Kategoria:',      'genre')]:
            tmpTab = []
            tmp = self.cm.ph.getDataBeetwenMarkers(data, item[0], '</li>', False)[1].split('<br>')
            for t in tmp:
                t = self.cleanHtmlStr(t).replace(' , ',  ', ')
                if t != '': tmpTab.append(t)
            if len(tmpTab): otherInfo[item[1]] = ', '.join(tmpTab)
        
        for item in [('Játékidő:',     'duration'),
                     ('IMDB Pont:', 'imdb_rating'),
                     ('Nézettség:',       'views')]:
            tmp = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, item[0], '</li>', False)[1])
            if tmp != '': otherInfo[item[1]] = tmp
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def getdvdsz(self, pu='', psz=''):
        bv = ''
        if pu != '' and psz != '':
            n_atnav = self.malvadst('1', '5', pu)
            if n_atnav != '' and self.aid:
                if pu == 'mozicsillag_catalog':
                    self.aid_ki = 'ID: ' + n_atnav + '  |  Mozicsillag  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = 'ID: ' + n_atnav + '\n'
            else:
                if pu == 'mozicsillag_catalog':
                    self.aid_ki = 'Mozicsillag  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = ''
            bv = self.aid_ki + psz
        return bv
        
    def malvadst(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu}
        t_s = ''
        temp_vn = ''
        temp_vni = ''
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a_div', '</div>')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '/>')
                if len(data) == 0: return t_s
                for item in data:
                    t_i = self.cm.ph.getSearchGroups(item, 'id=[\'"]([^"^\']+?)[\'"]')[0]
                    if t_i == 'vn':
                        temp_vn = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                    elif t_i == 'vni':
                        temp_vni = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                if temp_vn != '':
                    t_s = temp_vn
            return t_s
        except Exception:
            return t_s
            
    def susn(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu, 'hv':self.vivn, 'orv':self.porv, 'bts':self.pbtp}
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
    
    def ebbtit(self):
        try:
            if '' == self.btps.strip() or '' == self.brdr.strip():
                msg = 'A Set-top-Box típusát és a használt rendszer (image) nevét egyszer meg kell adni!\n\nA kompatibilitás és a megfelelő használat miatt kellenek ezek az adatok a programnak.\nKérlek, a helyes működéshez a valóságnak megfelelően írd be azokat.\n\nA "HU Telepítő" keretrendszerben tudod ezt megtenni.\n\nKilépek és megyek azt beállítani?'
                ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
                return False
            else:
                return True
        except Exception:
            return False
    
    def gits(self):
        bv = '-'
        tt = []
        try:
            if fileExists(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE'))):
                fr = open(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE')),'r')
                for ln in fr:
                    ln = ln.rstrip('\n')
                    if ln != '':
                        tt.append(ln)
                fr.close()
                if len(tt) == 1:
                    bv = tt[0].strip()[:-6].capitalize()
                if len(tt) == 2:
                    bv = tt[1].strip()[:-6].capitalize()
            return bv
        except:
            return '-'
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        self.currList = []
        if name == None:
            self.listMainMenu( {'name':'category'} )
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_sort')
        elif category == 'list_movies':
            self.listMovies(self.currItem, 'list_sort')
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_sort')
        elif category == 'list_sort':
            self.listSort(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
        elif category in ["search", "search_next_page"]:
            if self.currItem['tab_id'] == 'mozicsillag_search':
                self.susn('2', '5', 'mozicsillag_search')
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == "search_history":
            if self.currItem['tab_id'] == 'mozicsillag_search_hist':
                self.susn('2', '5', 'mozicsillag_search_hist')
            self.listsHistory({'name':'history', 'category': 'search', 'tab_id':''}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, MuziCsillangCC(), True, [])
        
    def withArticleContent(self, cItem):
        if (cItem['type'] != 'video' and cItem['category'] != 'explore_item'):
            return False
        return True
    
    