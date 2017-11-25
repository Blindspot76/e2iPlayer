# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getMPDLinksWithMeta
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

from os import path as os_path
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
config.plugins.iptvplayer.viortv_login              = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.viortv_password           = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.viortv_show_all_channels  = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_('Show all channels') + ": ",    config.plugins.iptvplayer.viortv_show_all_channels))
    optionList.append(getConfigListEntry('vior.tv ' + _("e-mail") + ':',   config.plugins.iptvplayer.viortv_login))
    optionList.append(getConfigListEntry('vior.tv ' + _("password") + ':', config.plugins.iptvplayer.viortv_password))
    return optionList
    
###################################################

class ViorTvApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL         = 'https://vior.tv/'
        self.DEFAULT_ICON_URL = 'https://vior.tv/theme/public/assets/img/logotype.png'
        self.HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        
        self.COOKIE_FILE = GetCookieDir('viortv.cookie')
        
        self.defaultParams = {}
        self.defaultParams.update({'header':self.HTTP_HEADER, 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        self.loggedIn = False
        self.accountInfo = ''
        
    def doLogin(self, login, password):
        logged = False
        premium = False
        loginUrl = self.getFullUrl('/profile/login')
        errMessage = _("Get page \"%s\" error.")
        
        rm(self.COOKIE_FILE)
        sts, data = self.cm.getPage(loginUrl, self.defaultParams)
        if not sts: return False, (errMessage % loginUrl)
        
        sts, data = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'login'), ('</form', '>'))
        if not sts: return False, ""
        
        actionUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0])
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>')
        post_data = {}
        for item in data:
            name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
            value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
            post_data[name] = value
        
        post_data.update({'_username':login, '_password':password, '_remember_me':'on'})
        httpParams = dict(self.defaultParams)
        httpParams['header'] = dict(httpParams['header'])
        httpParams['header']['Referer'] = self.getMainUrl()
        sts, data = self.cm.getPage(actionUrl, httpParams, post_data)
        if sts:
            errMessage = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'loginError'), ('</div', '>'))[1])
            if errMessage != '': 
                return False, errMessage
            elif 'account/logout' in data:
                return True, ''
        else:
            return False, (errMessage % actionUrl)
        
        return False, _("Unknown error.")
    
    def getList(self, cItem):
        printDBG("ViorTvApi.getChannelsList")
        
        login    = config.plugins.iptvplayer.viortv_login.value
        password = config.plugins.iptvplayer.viortv_password.value
        if login != '' and password != '':
            self.accountInfo = ''
            ret, msg = self.doLogin(login, password)
            if ret:
                self.loggedIn = True
                self.accountInfo = msg
            else:
                self.sessionEx.open(MessageBox, '%s\nProblem z zalogowanie użytkownika "%s". Sprawdź dane do logowania w konfiguracji hosta.' % (msg, login), type = MessageBox.TYPE_INFO, timeout = 10 )
                self.loggedIn = False
        else:
            self.sessionEx.open(MessageBox,'Serwis ten wymaga zalogowania. Wprowadź swój login i hasło w konfiguracji hosta dostępnej po naciśnięciu niebieskiego klawisza.', type = MessageBox.TYPE_ERROR, timeout = 10 )
            return []
        
        domain = self.up.getDomain(self.getMainUrl())
        channelsTab = []
        
        sts, data = self.cm.getPage(self.getFullUrl('/channel/list'), self.defaultParams)
        if not sts: return channelsTab
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<section', '>', 'chanelsSection'), ('</section', '>'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            if not config.plugins.iptvplayer.viortv_show_all_channels.value and 'noaccess' in item: continue
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0] )
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0] )
            if not self.cm.isValidUrl(url): continue
            title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0] )
            desc  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(item, ('<span', '>', 'desc'), ('</span', '>'))[1] )
            
            params = {'name':domain, 'type':'video', 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            channelsTab.append(params)
        
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("ViorTvApi.getVideoLink")
        urlsTab = []
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return urlsTab
        
        hlsUrl = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0].replace('.com//', '.com/')
        printDBG("hlsUrl||||||||||||||||| " + hlsUrl)
        if hlsUrl != '':
            hlsUrl = strwithmeta(hlsUrl, {'User-Agent':self.defaultParams['header']['User-Agent'], 'Referer':cItem['url']})
            return getDirectM3U8Playlist(hlsUrl, checkContent=True)
        return urlsTab
