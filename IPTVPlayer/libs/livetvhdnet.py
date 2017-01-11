# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import random
import string
try:    import json
except Exception: import simplejson as json
############################################

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

class LivetvhdNetApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL    = 'https://livetvhd.net/'
        self.HEADER = {'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.COOKIE_FILE = GetCookieDir('livetvhdnet.cookie')
        
        self.http_params = {}
        self.http_params.update({'header':self.HEADER, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        
        self.cacheList = {}
    
    def getList(self, cItem):
        printDBG("LivetvhdNetApi.getChannelsList")
        channelsTab = []
        sts, data = self.cm.getPage('https://livetvhd.net/api/videos')
        if not sts: return []
        
        try:
            data = byteify(json.loads(data))
            for item in data['videos']:
                url   = item['url']
                icon  = item['thumbnail']
                title = self.cleanHtmlStr(item['title'])
                params = dict(cItem)
                params.update({'type':'video', 'title':title, 'url':url, 'icon':icon})
                channelsTab.append(params)
        except Exception:
            printExc()
        return channelsTab
        
    def _getAttrVal(self, data, attr):
        return self.cm.ph.getSearchGroups(data, '''['"]?%s['"]?\s*:\s*['"]([^'^"]+?)['"]''' % attr)[0]
        
    def getVideoLink(self, cItem):
        printDBG("LivetvhdNetApi.getVideoLink")
        urlsTab = []
        if len(cItem['url']) < 3:
            return []
        
        sts, data = self.cm.getPage('https://livetvhd.net/api/videos', self.http_params)
        if not sts: return []
        token = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('"token"\s*:\s*"'), re.compile('"'), False)[1]
        
        videoUrl = cItem['url'] + '?token=' + token 
        
        videoUrl = strwithmeta(videoUrl, {'Referer':self.MAIN_URL, 'User-Agent':self.HEADER['User-Agent']})
        urlsTab  = getDirectM3U8Playlist(videoUrl, checkContent=True)
        return urlsTab