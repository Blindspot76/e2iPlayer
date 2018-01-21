# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, NextDay, PrevDay, GetDefaultLang
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.m3uparser import ParseM3u
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
from datetime import datetime, timedelta
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
    return 'http://radiostacja.pl/'

class RadiostacjaPl(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'radiostacja.pl', 'cookie':'radiostacja.pl.cookie', 'cookie_type':'MozillaCookieJar'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'http://www.radiostacja.pl/'
        self.DEFAULT_ICON_URL = 'http://is3.mzstatic.com/image/thumb/Purple122/v4/82/c4/6f/82c46f38-3532-e414-530e-33e5d0be2614/source/392x696bb.jpg'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'*/*', 'Origin':self.getMainUrl()[:-1]} )
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cache = {}
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        return self.cm.getPage(baseUrl, addParams, post_data)
    
    def listMainMenu(self, cItem):
        printDBG("RadiostacjaPl.listMainMenu")
        
        MAIN_CAT_TAB = [{'category':'live',           'title': _('Stacje Radiowe'),  'f_cache':'live',     'url':self.getFullUrl('/data/mobile/live.json')}, 
                        {'category':'channels',       'title': _('Kanały Muzyczne'), 'f_cache':'muzyczne', 'url':self.getFullUrl('/data/mobile/muzyczne_android.json')}, 
                        {'category':'djsety',         'title': _('Sety Muzyczne'),   'f_cache':'podcasty', 'url':self.getFullUrl('/data/mobile/podcasty_android.json'), 'f_key':'djsety'}, 
                       ]
        
        self.listsTab(MAIN_CAT_TAB, cItem)
        
    def listLive(self, cItem, nextCategory):
        printDBG("RadiostacjaPl.listGenres [%s]" % cItem)
        
        CAT_TAB = [{'good_for_fav':True, 'title': _('Radia ZET'),      'f_key':'eurozet'},
                   {'good_for_fav':True, 'title': _('Radia Lokalne'),  'f_key':'lokalne'}]
        
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(CAT_TAB, cItem)
        
    def _fillCache(self, cItem):
        if cItem['f_cache'] not in self.cache:
            sts, data = self.getPage(cItem['url'])
            if not sts: return
            
            try:
                data = byteify(json.loads(data))
                self.cache[cItem['f_cache']] = data
            except Exception:
                printExc()
        
    def listItemsFromCache(self, cItem):
        printDBG("RadiostacjaPl.listItems [%s]" % cItem)
        self._fillCache(cItem)
        
        try:
            cacheKey = cItem['f_cache']
            tabKey = cItem['f_key']
            data = self.cache[cacheKey][tabKey]
            self.listItems(cItem, data)
        except Exception:
            printExc()
        
    def listItems(self, cItem, data):
        printDBG("RadiostacjaPl.listItems [%s]" % cItem)
        for item in data:
            title = self.cleanHtmlStr(item['name'])
            icon  = self.cleanHtmlStr(item['image'])
            url   = self.cleanHtmlStr(item['stream'])
            params = {'title':title, 'url':url, 'icon':icon}
            self.addAudio(params)
            
    def listChannels(self, cItem):
        printDBG("RadiostacjaPl.listGenres [%s]" % cItem)
        self._fillCache(cItem)
        
        CAT_TAB = [{'good_for_fav':True, 'category':'list_items',  'title': _('Wszystkie'), 'f_key':'muzyczne'},
                   {'good_for_fav':True, 'category':'list_genres', 'title': _('Nastroje'),  'f_key':'kategorie'}]
        
        cItem = dict(cItem)
        cItem.pop('category', None)
        self.listsTab(CAT_TAB, cItem)
            
    def listGenres(self, cItem, nextCategory):
        printDBG("RadiostacjaPl.listGenres [%s]" % cItem)
        self._fillCache(cItem)
        
        try:
            cacheKey = cItem['f_cache']
            tabKey = cItem['f_key']
            
            for idx in range(len(self.cache[cacheKey][tabKey])):
                channel = self.cache[cacheKey][tabKey][idx]
                title = self.cleanHtmlStr(channel['name'])
                icon  = self.cleanHtmlStr(channel['logo'])
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'icon':icon, 'f_idx':idx})
                self.addDir(params)
        except Exception:
            printExc()
            
    def listChannel(self, cItem):
        printDBG("RadiostacjaPl.listChannelsItems [%s]" % cItem)
        try:
            cacheKey = cItem['f_cache']
            tabKey = cItem['f_key']
            idx    = cItem['f_idx']
            data = self.cache[cacheKey][tabKey][idx]['channels']
            self.listItems(cItem, data)
        except Exception:
            printExc()
            
    def listDJSety(self, cItem, nextCategory):
        printDBG("RadiostacjaPl.listDJSety [%s]" % cItem)
        self._fillCache(cItem)
        
        try:
            cacheKey = cItem['f_cache']
            tabKey = cItem['f_key']
            for idx in range(len(self.cache[cacheKey][tabKey])):
                content = self.cache[cacheKey][tabKey][idx]['content']
                title = self.cleanHtmlStr(content['name'])
                icon  = self.cleanHtmlStr(content['logo'])
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'icon':icon, 'f_idx':idx})
                self.addDir(params)
        except Exception:
            printExc()
            
    def listDJ(self, cItem):
        printDBG("RadiostacjaPl.listDJ [%s]" % cItem)
        try:
            cacheKey = cItem['f_cache']
            tabKey = cItem['f_key']
            idx    = cItem['f_idx']
            data = self.cache[cacheKey][tabKey][idx]['content']['data']
            for item in data:
                title = self.cleanHtmlStr(item['name'])
                url   = self.cleanHtmlStr(item['file'])
                params = {'title':title, 'url':url, 'icon':cItem.get('icon', '')}
                self.addAudio(params)
        except Exception:
            printExc()
        
    def getLinksForVideo(self, cItem):
        printDBG("RadiostacjaPl.getLinksForVideo [%s]" % cItem)
        return [{'name':'stream', 'url':cItem['url'], 'need_resolve':0}]
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||| name[%s], category[%s] " % (name, category) )
        self.cacheLinks = {}
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'})
    # LIVE
        elif category == 'live':
            self.listLive(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItemsFromCache(self.currItem)
    # CHANNELS
        elif category == 'channels':
            self.listChannels(self.currItem)
        elif category == 'list_genres':
            self.listGenres(self.currItem, 'list_channel')
        elif category == 'list_channel':
            self.listChannel(self.currItem)
    # DJSETY
        elif category == 'djsety':
            self.listDJSety(self.currItem, 'list_dj')
        elif category == 'list_dj':
            self.listDJ(self.currItem)
        
        
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, RadiostacjaPl(), True, [])
    