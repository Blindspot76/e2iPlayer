# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify, GetCookieDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
try: import json
except Exception: import simplejson as json
from os import path as os_path
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.wagasworld_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.wagasworld_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry('wagasworld.com ' + _("email") + ':', config.plugins.iptvplayer.wagasworld_login))
    optionList.append(getConfigListEntry('wagasworld.com ' + _("password") + ':', config.plugins.iptvplayer.wagasworld_password))
    return optionList
    
###################################################


class WagasWorldApi:

    def __init__(self):
        self.cm = common()
        self.up = urlparser()
        self.sessionEx = MainSessionWrapper()
        self.MAIN_URL      = 'http://www.wagasworld.com/'
        self.HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': self.MAIN_URL }
    
        self.COOKIE_FILE = GetCookieDir('wagasworld.cookie')
        self.http_params = {'header': dict(self.HTTP_HEADER), 'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        
        if self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url.replace('&amp;', '&')
        
    def getMainCategories(self, cItem):
        printDBG("WagasWorldApi.getMainCategories")
        list = []
        list.append({'type':'waga_cat', 'waga_cat':'groups', 'title':_('Channel'), 'url':self.MAIN_URL + 'channel'})
        list.append({'type':'waga_cat', 'waga_cat':'groups', 'title':_('LiveTv'),  'url':self.MAIN_URL + 'LiveTv' })
        return list
        
    def getGroups(self, cItem):
        printDBG("WagasWorldApi.getGroups")
        list = []
        sts, data = self.cm.getPage(cItem['url'], self.http_params)
        if not sts: return list
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="form-item">', '<select', True)[1]
        data = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(data)
        for item in data:
            list.append({'type':'waga_cat', 'waga_cat':'items', 'title':item[1], 'url':self._getFullUrl(item[0])})
        return list
        
    def getItems(self, cItem):
        printDBG("WagasWorldApi.getItems")
        list = []
        page = cItem.get('page', 0)
        url  = cItem['url']
        if page > 0:
            if '?' in url: url += '&'
            else: url += '?'
            url += 'page={0}'.format(page)
        sts, data = self.cm.getPage(url, self.http_params)
        if not sts: return list
        
        nextPage = False
        if '&amp;page={0}"'.format(page+1) in data:
            nextPage = True
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="view-content">', '</section>', True)[1]
        data = data.split('</span>')
        if len(data): del data[-1]
        for item in data:
            title = self.cm.ph.getSearchGroups(item, '>([^<]+?)</a>')[0]
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            if '' != url and '' != title:
                list.append( {'type':'video', 'title':title, 'icon':icon, 'url':url} )
        if nextPage:
            list.append({'type':'waga_cat', 'waga_cat':'items', 'title':_('Next page'), 'url':cItem['url'], 'page':page+1})
        return list
        
    def getChannelsList(self, cItem):
        printDBG("WagasWorldApi.getChannelsList waga_cat[%s]" % cItem.get('waga_cat',  '') )
        list = []
        waga_cat = cItem.get('waga_cat',  '')
        if '' == waga_cat:
            login    = config.plugins.iptvplayer.wagasworld_login.value
            password = config.plugins.iptvplayer.wagasworld_password.value
            if login != '' and password != '':        
                if self.doLogin(login, password):
                    self.loggedIn = True
                    self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
                else:
                    self.sessionEx.open(MessageBox, _('"%s" login failed! Please check your login and password.') % login, type = MessageBox.TYPE_INFO, timeout = 10 )
        
            list = self.getGroups({'url':self.MAIN_URL + 'channel'})
            #list = self.getMainCategories(cItem)
        elif 'groups' == waga_cat:
            list = self.getGroups(cItem)
        elif 'items' == waga_cat:
            list = self.getItems(cItem)
        return list

    
    def getVideoLink(self, baseUrl):
        printDBG("WagasWorldApi.getVideoLink url[%s]" % baseUrl)
        def _url_path_join(a, b):
            from urlparse import urljoin
            return urljoin(a, b)
        
        sts,data = self.cm.getPage(baseUrl, self.http_params)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="videoWrapper">', ' </section>', False)[1]
        return self.up.getAutoDetectedStreamLink(baseUrl, data)
        
    def doLogin(self, login, password):
        logged = False
        loginUrl = self.MAIN_URL + '?q=user'
        
        params = dict(self.http_params)
        params['load_cookie'] = False
        sts, data = self.cm.getPage(loginUrl, params)
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>', False, False)[1]
        action = self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0]
        if action.startswith('/'):
            action = self.MAIN_URL + action[1:]
        
        printDBG(data)
        post_data = dict(re.findall(r'<(?:input|button)[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        post_data.update({'name':login, 'pass':password})
        
        HTTP_HEADER= dict(self.HTTP_HEADER)
        HTTP_HEADER.update( {'Referer':loginUrl} )
        
        params    = {'header' : HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True, 'load_cookie' : True}
        sts, data = self.cm.getPage( loginUrl, params, post_data)
        if sts:
            if os_path.isfile(self.COOKIE_FILE):
                if 'user/logout' in data:
                    printDBG('WagasWorldApi.doLogin login as [%s]' % login)
                    logged = True
                else:
                    printDBG('WagasWorldApi.doLogin login failed - wrong user or password?')
            else:
                printDBG('WagasWorldApi.doLogin there is no cookie file after login')
        return logged
