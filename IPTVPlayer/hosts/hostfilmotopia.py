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
    return 'http://filmotopia.com/'

class Filmotopia(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'filmotopia.com', 'cookie':'filmotopiacom.cookie', 'cookie_type':'MozillaCookieJar'})
        self.DEFAULT_ICON_URL = 'http://www.sajtovi.mk/tmp/img-13.jpg'
        self.USER_AGENT = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.M_MAIN_URL = 'http://filmotopia.com/'
        self.S_MAIN_URL = 'http://serijal.com/' 
        self.serviceType = 'movie'
        
        self.cacheLinks    = {}
        self.cacheEpisodes = {}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_CAT_TAB = [{'category':'list_movies_cats',   'title': _('Movies'),                     },
                             {'category':'list_series_cats',   'title': _('Series'),                     },
                             {'category':'search',            'title': _('Search'), 'search_item':True,  },
                             {'category':'search_history',    'title': _('Search history'),              } 
                            ]
                            
        self.MOVIES_CAT_TAB = [{'category':'list_items',   'title': _('News'),    'url':self.M_MAIN_URL              },
                               {'category':'list_items',   'title': _('Popular'), 'url':self.getFullUrl('popularno/')},
                              ]
        
        self.SERIES_CAT_TAB = [{'category':'list_items',   'title': _('News'),         'url':self.S_MAIN_URL                       },
                               {'category':'list_items',   'title': _('New episodes'), 'url':self.getFullUrl('nove-epizode/', True)},
                               {'category':'list_items',   'title': _('Popular'),      'url':self.getFullUrl('popularno/',    True)},
                              ]
        
    def getMainUrl(self):
        if 'movies' == self.serviceType: return self.M_MAIN_URL
        else: return self.S_MAIN_URL
        
    def getFullUrl(self, url, series=False):
        if series: self.serviceType = 'series'
        else: self.serviceType = 'movies'
        return CBaseHostClass.getFullUrl(self, url)
        
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
        
    def listItems(self, cItem, nextCategory=None):
        printDBG("Filmotopia.listItems")
        url = cItem['url']
        page = cItem.get('page', 1)
        
        if self.up.getDomain(url) == self.up.getDomain(self.M_MAIN_URL):
            type = 'movie'
        else:
            type = 'serie'
        
        if page > 1:
            url += '/page/%s' % page
        
        sts, data = self.getPage(url)
        if not sts: return
        
        nextPage = self.cm.ph.getDataBeetwenMarkers(data, '<div class="nav-previous', '</div>', False)[1]
        if ('page/%s"' % (page+1)) in nextPage: 
            nextPage = True
        else: 
            nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="movies"', '<!-- #content -->')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            if 'post-' not in item: continue
            url  = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if not self.cm.isValidUrl(url): continue
            icon = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title = self.cleanHtmlStr( item )

            params = {'good_for_fav': True, 'title':title, 'url':url, 'icon':icon}
            if type == 'movie':
                self.addVideo(params)
            else:
                params['category'] = nextCategory
                self.addDir(params)
        
        if nextPage and len(self.currList) > 0:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
            
    def listSeasons(self, cItem, nextCategory='list_episodes'):
        printDBG("Filmotopia.listSeasons")
        self.cacheEpisodes = {}
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="seasons">', '<script')[1]
        data = data.split('<dt>')
        if len(data): del data[0]
        
        for seasonItem in data:
            seasonTitle  = self.cleanHtmlStr(seasonItem.split('</dt>')[0])
            sNum = self.cm.ph.getSearchGroups(seasonTitle+'|', '''[^0-9]([0-9]+?)[^0-9]''')[0]
            episodesData = self.cm.ph.getAllItemsBeetwenMarkers(seasonItem, '<dd', '</dd>')
            episodesTab  = []
            for item in episodesData:
                eNum   = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="number"', '</div>')[1])
                eTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="title"',  '</div>')[1])
                eTitle = re.sub('Epizoda\s*[0-9]+?\s*\:', '', eTitle).strip()
                data_path = self.cm.ph.getSearchGroups(item, '''data-path=['"]([^'^"]+?)['"]''')[0]
                data_open = self.cm.ph.getSearchGroups(item, '''data-open=['"]([^'^"]+?)['"]''')[0]
                
                title = '%s: s%se%s %s' % (cItem['title'], sNum.zfill(2), eNum.zfill(2), eTitle)
                params = {'title':title, 'data_path':data_path, 'data_open':data_open}
                episodesTab.append(params)
            
            if len(episodesTab):
                self.cacheEpisodes[seasonTitle] = episodesTab
                params = dict(params)
                params.update({'good_for_fav': False, 'category':nextCategory, 'title':seasonTitle, 'cache_key':seasonTitle})
                self.addDir(params)
    
    def listEpisodes(self, cItem):
        printDBG("Filmotopia.listEpisodes")
        cacheKey = cItem.get('cache_key', '')
        tab = self.cacheEpisodes.get(cacheKey, [])
        self.listsTab(tab, cItem, 'video')

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Filmotopia.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        if searchType == 'movie':
            url = self.getFullUrl('?s=', False)
        elif searchType == 'serie':
            url = self.getFullUrl('?s=', True)
        else:
            printDBG("Filmotopia.listSearchResul - wrong search type")
            return
        
        cItem = dict(cItem)
        cItem['url'] = url + urllib.quote_plus(searchPattern)
        self.listItems(cItem, 'list_seasons')
        
    def getLinksForVideo(self, cItem):
        printDBG("Filmotopia.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if 'data_open' in cItem:
            videoUrl = 'https://openload.co/embed/' + cItem['data_open']
        else:
            sts, data = self.getPage(cItem['url'])
            if not sts: return urlTab
            videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
        
        urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
    
    def getFavouriteData(self, cItem):
        printDBG('Filmotopia.getFavouriteData')
        return json.dumps(cItem) 
        
    def getLinksForFavourite(self, fav_data):
        printDBG('Filmotopia.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception: printExc()
        return links
        
    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('Filmotopia.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception: 
            params = {}
            printExc()
        self.addDir(params)
        return True
        
    def getArticleContent(self, cItem):
        printDBG("Filmotopia.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.getPage(cItem.get('url', ''))
        if not sts: return retTab
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="description"', '</div>')[1])
        tmp  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="header">', '</div>')[1]
        title = self.cleanHtmlStr(tmp)
        icon  = self.getFullUrl( self.cm.ph.getSearchGroups(data, '<img[^>]+?src="(https?://[^"]+?)"')[0] )
        
        if title == '': title = cItem['title']
        if desc == '':  title = cItem['desc']
        if icon == '':  title = cItem['icon']
        
        otherInfo = {}
        rating = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div id="post-ratings', '</div>')[1])
        if rating != '': otherInfo['rating'] = rating
        
        year = self.cm.ph.getSearchGroups(tmp, '<span>\s*([0-9]{4})\s*</span>')[0]
        if year != '': otherInfo['year'] = year
        
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
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_movies_cats':
            self.listsTab(self.MOVIES_CAT_TAB, self.currItem)
        elif category == 'list_series_cats':
            self.listsTab(self.SERIES_CAT_TAB, self.currItem)
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_seasons')
        elif category == 'list_seasons':
            self.listSeasons(self.currItem)
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
        CHostBase.__init__(self, Filmotopia(), True, [])
        
    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append((_("Movies"), "movie"))
        searchTypesOptions.append((_("Series"), "serie"))
        return searchTypesOptions
        
    def withArticleContent(self, cItem):
        if cItem['type'] != 'video' and cItem['category'] != 'list_seasons':
            return False
        return True
    
    