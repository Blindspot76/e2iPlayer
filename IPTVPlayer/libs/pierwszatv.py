# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify, GetPyScriptCmd
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
import base64
try:    import json
except: import simplejson as json

from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from binascii import hexlify, unhexlify, a2b_hex
from hashlib import md5
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
config.plugins.iptvplayer.pierwszatv_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.pierwszatv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry('pierwsza.tv ' + _("email") + ':', config.plugins.iptvplayer.pierwszatv_login))
    optionList.append(getConfigListEntry('pierwsza.tv ' + _("password") + ':', config.plugins.iptvplayer.pierwszatv_password))
    return optionList
    
###################################################

class PierwszaTVApi:
    MAIN_URL   = 'http://pierwsza.tv/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAIN_URL }
    
    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('pierwszatv.cookie')
        self.sessionEx = MainSessionWrapper()
        self.cm = common()
        self.up = urlparser()
        self.http_params = {}
        self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        self.cacheList = {}
        
    def cryptoJS_AES_decrypt(self, encrypted, password, salt):
        def derive_key_and_iv(password, salt, key_length, iv_length):
            d = d_i = ''
            while len(d) < key_length + iv_length:
                d_i = md5(d_i + password + salt).digest()
                d += d_i
            return d[:key_length], d[key_length:key_length+iv_length]
        bs = 16
        key, iv = derive_key_and_iv(password, salt, 32, 16)
        cipher = AES_CBC(key=key, keySize=32)
        return cipher.decrypt(encrypted, iv)
        
    def getFullUrl(self, url):
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return self.MAIN_URL + url[1:]
        return url
        
    def cleanHtmlStr(self, str):
        return CBaseHostClass.cleanHtmlStr(str)
        
    def getChannelsList(self, cItem):
        printDBG("TelewizjadaNetApi.getChannelsList")
        
        login    = config.plugins.iptvplayer.pierwszatv_login.value
        password = config.plugins.iptvplayer.pierwszatv_password.value
        if login != '' and password != '':        
            if self.doLogin(login, password):
                self.loggedIn = True
                self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
            else:
                self.sessionEx.open(MessageBox, _('Problem z zalogowanie użytkownika "%s. Sprawdź dane do logowania w konfiguracji hosta."') % login, type = MessageBox.TYPE_INFO, timeout = 10 )
        
        channelsTab = []
        sts, data = self.cm.getPage(self.MAIN_URL + 'player/watch?show=active')
        if not sts: return []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a class="source', '</a>')
        for item in data:
            url   = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''', 1, True)[0] )
            icon  = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''src="([^"]+?)"''', 1, True)[0] )
            #icon = ''
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="name">', '</div>', False)[1] )
            desc  = self.cleanHtmlStr( item.split('<div class="author">')[-1] )
            if not url.startswith('http'): continue
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'icon':icon, 'desc':desc})
            channelsTab.append(params)
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("TelewizjadaNetApi.getVideoLink")
        params    = {'header' : self.HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True}
        sts, data = self.cm.getPage(cItem['url'], params)
        if not sts: return []
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'connectToLive(', ')', False)[1]
        tmp = self.cm.ph.getSearchGroups(tmp, '''['"]([^'^"]+?)['"][^'^"]+?['"]([^'^"]+?)['"]''', 2, True)[0]
        
        varData = self.cm.ph.getDataBeetwenMarkers(data, 'window.', 'var items')[1]
        window = {'streamUrl':'', 'sourceType':'', 'sourcePlayer':'', 'streamId':'', 'streamToken':'', 'serverId':''} 
        for key in window:
            val = self.cm.ph.getSearchGroups(varData, '''window\.%s[^'^"]*?=([^;]+?);''' % key, 1, True)[0].strip()
            if val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            window[key] = val
            
        window['urls'] = {}
        for keyUrl in ['playRecord', 'player', 'sync', 'multiLogin', 'reportError', 'reportOk', 'bumpToken']:
            window['urls'][keyUrl] = self.cm.ph.getSearchGroups(varData, '''window\.urls\['[^']+?\@%s'\][\s]*?=[\s]*?['"]([^'^"]+?)['"]''' % keyUrl, 1, True)[0].strip()
        
        urlsTab = []
        try:
            printDBG(window)
            streamUrl = byteify(json.loads(window['streamUrl']))
            ciphertext = base64.b64decode(streamUrl['ct'])
            iv         = a2b_hex(streamUrl['iv'])
            salt       = a2b_hex(streamUrl['s'])
            
            url = self.cryptoJS_AES_decrypt(ciphertext, 'number-one', salt)
            baseUrl = byteify(json.loads(url))
            url = baseUrl + "/stream/get?id=" + window['streamId'] + "&token=" + window['streamToken']
            
            sts, data = self.cm.getPage(url, params)
            data = byteify(json.loads(data))
            if data['error'] != None:
                SetIPTVPlayerLastHostError(str(data['error']))
            url = baseUrl + "/" + data['url'] + "?token=" + window['streamToken']
            tmpUrlsTab = getDirectM3U8Playlist(url)
            
            refreshUrl1 = baseUrl + "/stream/bump?id=" + window['streamId'] + "&token=" + window['streamToken']
            refreshUrl2 = window['urls']['bumpToken'] + "?pid=" + window['serverId'] + "&token=" + window['streamToken']
            reportOkUrl = window['urls']['reportOk']
            
            HTTP_HEADER= dict(PierwszaTVApi.HTTP_HEADER)
            HTTP_HEADER.update( {'Referer':cItem['url']} )
            
            params    = {'header' : HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True, 'load_cookie' : True}
            self.cm.getPage(reportOkUrl, params)
            
            pyCmd = GetPyScriptCmd('pierwszatv') + ' "%s" "%s" "%s" "%s" ' % (HTTP_HEADER['User-Agent'], cItem['url'], refreshUrl1, refreshUrl2)
            for item in tmpUrlsTab:
                item['url'] = strwithmeta(item['url'], {'iptv_refresh_cmd':pyCmd, 'Referer':cItem['url'], 'User-Agent':HTTP_HEADER['User-Agent']})
                urlsTab.append(item)
                
            self.cm.getPage(refreshUrl1, params)
            self.cm.getPage(refreshUrl2, params)
            
            printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(pyCmd)
            printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            
        except:
            printExc()
            return []
        
        return urlsTab
        
    def doLogin(self, login, password):
        logged = False
        loginUrl = self.MAIN_URL + 'account/login'
        
        params = dict(self.http_params)
        params['load_cookie'] = False
        sts, data = self.cm.getPage(loginUrl, params)
        if not sts: return False
        
        _token = self.cm.ph.getSearchGroups(data, '''_token"[\s]*?value="([^"]+?)"''', 1, True)[0]
        
        HTTP_HEADER= dict(PierwszaTVApi.HTTP_HEADER)
        HTTP_HEADER.update( {'Referer':loginUrl} )
        
        post_data = {'email' : login, 'password' : password, '_token' : _token, 'remember_me' : 'on' }
        params    = {'header' : HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True, 'load_cookie' : True}
        sts, data = self.cm.getPage( loginUrl, params, post_data)
        if sts:
            if os_path.isfile(self.COOKIE_FILE):
                if 'dashboard/logout' in data:
                    printDBG('PierwszaTVApi.doLogin login as [%s]' % login)
                    logged = True
                else:
                    printDBG('PierwszaTVApi.doLogin login failed - wrong user or password?')
            else:
                printDBG('PierwszaTVApi.doLogin there is no cookie file after login')
        return logged
