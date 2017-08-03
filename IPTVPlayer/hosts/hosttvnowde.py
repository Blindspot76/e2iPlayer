# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
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
from datetime import date, timedelta
from copy import deepcopy
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
config.plugins.iptvplayer.tvnowde_show_paid_items = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Show paid items (it may be illegal)"), config.plugins.iptvplayer.tvnowde_show_paid_items))
    return optionList
###################################################

def gettytul():
    return 'https://www.tvnow.de/'

class TVNowDE(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'movs4u.com', 'cookie':'movs4u.com.cookie', 'cookie_type':'MozillaCookieJar'})
        self.DEFAULT_ICON_URL = 'https://www.tvnow.de/styles/modules/header/tvnow.png'
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding':'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://api.tvnow.de/v3/'
        self.cacheLinks = {}
        self.cacheAZ = {'list':[], 'cache':{}}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
        self.MAIN_CAT_TAB = [{'category':'list_az',         'title': _('A-Z')},
                             {'category':'list_cats',       'title': _('Categories')},
                            ]
        
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
        
    def getStr(self, item, key):
        value = item.get(key, None)
        if value == None: value = ''
        return str(value)
        
    def listCats(self, cItem, nextCategory):
        printDBG("TVNowDE.listCats")
        
        genres = ["Soap", "Action", "Crime", "Ratgeber", "Comedy", "Show", "Docutainment", "Drama", "Tiere", "News", "Mags", "Romantik", "Horror", "Familie", "Kochen", "Auto", "Sport", "Reportage und Dokumentationen", "Sitcom", "Mystery", "Lifestyle", "Musik", "Spielfilm", "Anime"]
        for item in genres:
            params = dict(cItem)
            params = {'good_for_fav': True, 'title':item, 'f_genre':item.lower()}
            params['category'] = nextCategory
            self.addDir(params)
            
    def listAZ(self, cItem, nextCategory):
        printDBG("TVNowDE.listAZ")
        
        if 0 == len(self.cacheAZ.get('list', [])): 
            self.cacheAZ = {'list':[], 'cache':{}}
        
            page = cItem.get('page', 1)
            url = self.getFullUrl('/formats?fields=id,title,station,title,titleGroup,seoUrl,icon,hasFreeEpisodes,hasPayEpisodes,categoryId,searchAliasName,genres&filter=%7B%22Id%22:%7B%22containsNotIn%22:%5B%221896%22%5D%7D,%22Disabled%22:0%7D&maxPerPage=500&page=1&page={0}'.format(page))
            
            sts, data = self.getPage(url)
            if not sts: return 
            try:
                data = byteify(json.loads(data))
                for item in data['items']:  
                    if not config.plugins.iptvplayer.tvnowde_show_paid_items.value and not item.get('hasFreeEpisodes', False): 
                        continue
                    letter = self.getStr(item, 'titleGroup')
                    title    = self.getStr(item, 'title')
                    station  = self.getStr(item, 'station')
                    name     = self.cleanHtmlStr(self.getStr(item, 'seoUrl'))
                    desc     = item.get('genres', [])
                    if isinstance(desc, list):
                        desc = ' | '.join(desc)
                    else: desc  = ''
                    
                    params = {'f_station':station, 'f_name':name, 'title':title, 'desc':desc}
                    if not letter in self.cacheAZ['list']:
                        self.cacheAZ['list'].append(letter)
                        self.cacheAZ['cache'][letter] = []
                    self.cacheAZ['cache'][letter].append(params)
                    
                    categoryId = self.getStr(item, 'categoryId')
                    if categoryId not in ['serie', 'film', 'news']:
                        printDBG("Unknown categoryId [%s]" % categoryId)
                        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        printDBG(item)
            except Exception:
                printExc()
        
        self.cacheAZ['list'].sort()
        for letter in self.cacheAZ['list']:
            params = dict(cItem)
            params = {'name':'category', 'category':nextCategory, 'f_letter':letter, 'title':letter}
            self.addDir(params)
                
    def listItemsByLetter(self, cItem, nextCategory):
        printDBG("TVNowDE.listItemsByLetter")
        letter = cItem.get('f_letter', '')
        tab = self.cacheAZ['cache'].get(letter, [])
        for item in tab:
            params = dict(item)
            params.update({'name':'category', 'category':nextCategory})
            self.addDir(params)
            
    def listCatsItems(self, cItem, nextCategory):
        printDBG("TVNowDE.listCatsItems")
        page = cItem.get('page', 1)
        genre = cItem.get('f_genre', '')
        
        url = self.getFullUrl('/formats/genre/{0}?fields=*&filter=%7B%22station%22:%22none%22%7D&maxPerPage=500&order=NameLong+asc&page={1}'.format(genre, page))
        
        sts, data = self.getPage(url)
        if not sts: return 
        try:
            data = byteify(json.loads(data))
            for item in data['items']:  
                if not config.plugins.iptvplayer.tvnowde_show_paid_items.value and not item.get('hasFreeEpisodes', False): 
                    continue
                icon = self.getStr(item, 'defaultDvdImage')
                if icon == '': icon = self.getStr(item, 'defaultDvdImage')
                title    = self.getStr(item, 'title')
                station  = self.getStr(item, 'station')
                name     = self.cleanHtmlStr(self.getStr(item, 'seoUrl'))
                desc     = self.cleanHtmlStr(self.getStr(item, 'metaDescription'))
                
                params = {'name':'category', 'category':nextCategory, 'f_station':station, 'f_name':name, 'title':title, 'icon':icon, 'desc':desc}
                self.addDir(params)

                categoryId = self.getStr(item, 'categoryId')
                if not categoryId in ['serie', 'film', 'news']:
                    printDBG("Unknown categoryId [%s]" % categoryId)
                    printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    printDBG(item)
        except Exception:
            printExc()
            
    def listNavigation(self, cItem):
        printDBG("TVNowDE.listNavigation")
        name = cItem.get('f_name', '')
        station = cItem.get('f_station', '')
        
        url = self.getFullUrl('/formats/seo?fields=*,.*,formatTabs.*,formatTabs.formatTabPages.*,formatTabs.formatTabPages.container.*,annualNavigation.*&name={0}.php&station={1}'.format(name, station))
        
        sts, data = self.getPage(url)
        if not sts: return 
        try:
            data = byteify(json.loads(data))
            if data.get('tabSeason', False):
                for item in data['formatTabs']['items']:
                    if not item.get('visible', False): continue
                    try:
                        title = self.getStr(item, 'headline')
                        containers = []
                        for tabItem in item['formatTabPages']['items']:
                            containers.append( tabItem['container']['id'])
                        
                        if 0 == len(containers): continue
                        params = {'name':'category', 'category':'list_tab_items', 'f_containers_items':containers, 'title':title, 'icon':cItem.get('icon', ''), 'desc':cItem.get('desc', '')}
                        self.addDir(params)
                    except Exception:
                        printExc()
            else:
                id = data['id']
                for item in data['annualNavigation']['items']:
                    year = int(self.getStr(item, 'year'))
                    months = item['months']
                    for m in range(1, 13, 1):
                        m1 = (m + 1)
                        if m1 > 12: m1 = m1 % 12
                        days = (date(year +(m+1)/12, m1, 1)  - date(year, m, 1)).days
                        m = str(m)
                        if not m in months: continue
                        title = '%s/%s' % (year, m.zfill(2))
                        url = self.getFullUrl('/movies?fields=*,format,paymentPaytypes,pictures,trailers,packages&filter=%7B%22BroadcastStartDate%22:%7B%22between%22:%7B%22start%22:%22{0}-{1}-{2}+00:00:00%22,%22end%22:+%22{3}-{4}-{5}+23:59:59%22%7D%7D,+%22FormatId%22+:+{6}%7D&maxPerPage=300&order=BroadcastStartDate+desc'.format(year, m.zfill(2), '01', year, m.zfill(2), str(days).zfill(2), id))
                        params = {'name':'category', 'category':'list_video_items', 'url' :url, 'title':title, 'icon':cItem.get('icon', ''), 'desc':cItem.get('desc', '')}
                        self.addDir(params)
                self.currList.reverse()
                    
        except Exception:
            printExc()
            
    def listTabItems(self, cItem):
        printDBG("TVNowDE.listTabItems")
        containers = cItem.get('f_containers_items', [])
        
        try:
            for item in containers:
                url = self.getFullUrl('/containers/{0}/movies?fields=*,format.*,paymentPaytypes.*,livestreamEvent.*,pictures,trailers,packages,annualNavigation&maxPerPage=300&order=OrderWeight+asc,+BroadcastStartDate+desc'.format(item))
                params = dict(cItem)
                cItem['url'] = url
                self.listVideoItems(cItem)
        except Exception:
            printExc()
        
    def listVideoItems(self, cItem):
        printDBG("TVNowDE.listVideoItems [%s]" % cItem)
        page = cItem.get('page', 1)
        url  = cItem['url'] + '&page=%s' % page 
        
        sts, data = self.getPage(url)
        if not sts: return 
        try:
            data = byteify(json.loads(data))
            for item in data['items']:
                try:
                    if not config.plugins.iptvplayer.tvnowde_show_paid_items.value and not item.get('free', False): 
                        continue
                    
                    urlDashClear = item['manifest']['dashclear']
                    if not self.cm.isValidUrl(urlDashClear): continue
                    id = self.getStr(item, 'id')
                    icon = 'https://ais.tvnow.de/tvnow/movie/{0}/600x716/title.jpg'.format(id)
                    title    = self.getStr(item, 'title')
                    desc     = self.cleanHtmlStr(self.getStr(item, 'articleLong'))
                    seoUrlItem = self.getStr(item, 'seoUrl')
                    seoUrlFormat = self.getStr(item['format'], 'seoUrl')
                    station = self.getStr(item['format'], 'station')
                    url = '/%s/%s' % (seoUrlFormat, seoUrlItem)
                    params = {'dashclear':urlDashClear, 'f_seo_url_format':seoUrlFormat, 'f_seo_url_item':seoUrlItem, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
                    self.addVideo(params)
                except Exception:
                    printExc()
        except Exception:
            printExc()


    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("TVNowDE.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('/?s=' + urllib.quote_plus(searchPattern))
        self.listItems(cItem, 'explore_item')
        
    def getLinksForVideo(self, cItem):
        printDBG("TVNowDE.getLinksForVideo [%s]" % cItem)
        retTab = []
        
        cacheTab = self.cacheLinks.get(cItem['url'], [])
        if len(cacheTab):
            return cacheTab
        
        url = cItem.get('dashclear', '')
        if self.cm.isValidUrl(url):
            retTab = getMPDLinksWithMeta(url, False)
        
        if len(retTab):
            self.cacheLinks[cItem['url']] = retTab
        
        return retTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("TVNowDE.getVideoLinks [%s]" % videoUrl)
        videoUrl = strwithmeta(videoUrl)
        urlTab = []
        orginUrl = str(videoUrl)
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
        
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('TVNowDE.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('TVNowDE.getLinksForFavourite')
        if self.MAIN_URL == None:
            self.selectDomain()
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('TVNowDE.setInitListFromFavouriteItem')
        if self.MAIN_URL == None:
            self.selectDomain()
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
    
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
        elif category == 'list_az':
            self.listAZ(self.currItem, 'list_items_by_letter')
        elif category == 'list_items_by_letter':
            self.listItemsByLetter(self.currItem, 'list_navigation')
        elif category == 'list_cats':
            self.listCats(self.currItem, 'list_cats_items')
        elif category == 'list_cats_items':
            self.listCatsItems(self.currItem, 'list_navigation')
        elif category == 'list_navigation':
            self.listNavigation(self.currItem)
        elif category == 'list_tab_items':
            self.listTabItems(self.currItem)
        elif category == 'list_video_items':
            self.listVideoItems(self.currItem)
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
        CHostBase.__init__(self, TVNowDE(), True, [])

    
    