# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVNotify
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, GetTmpDir, GetDefaultLang, WriteTextFile, ReadTextFile
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
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
from datetime import datetime
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
config.plugins.iptvplayer.maxtvgo_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.maxtvgo_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("login")+":",    config.plugins.iptvplayer.maxtvgo_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.maxtvgo_password))
    return optionList
###################################################
def gettytul():
    return 'https://maxtvgo.com/'

class MaxtvGO(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'maxtvgo.com', 'cookie':'maxtvgo.com.cookie', 'cookie_type':'MozillaCookieJar', 'min_py_ver':(2,7,9)})
        self.DEFAULT_ICON_URL = 'https://maxtvgo.com/images/logo_37.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'https://maxtvgo.com/'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.MAIN_CAT_TAB = [{'category':'list_items',        'title': 'MaxTVGo',             'url':self.getFullUrl('/index.php')},
                             {'category':'list_yt_channel',   'title': 'Max Kolonko - MaxTV', 'url':'https://www.youtube.com/user/Media2000Corp/videos' },
                             {'category':'list_yt_channel',   'title': 'MaxTVNews',           'url':'https://www.youtube.com/user/MaxTVTUBE/videos'},
                            ]
        self.ytp = YouTubeParser()
        self.loggedIn = None
        self.login    = ''
        self.password = ''
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        origBaseUrl = baseUrl
        baseUrl = self.cm.iriToUri(baseUrl)
        def _getFullUrl(url):
            if self.cm.isValidUrl(url): return url
            else: return urlparse.urljoin(baseUrl, url)
        addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT, 'full_url_handle':_getFullUrl}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        
    def listMainMenu(self, cItem, nextCategory):
        printDBG("MaxtvGO.listMainMenu")
        self.listsTab(self.MAIN_CAT_TAB, cItem)
        
    def listItems(self, cItem, nextCategory):
        printDBG("MaxtvGO.listItems [%s]" % cItem)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'slajder_film'), ('<div', '>', 'chat_round'))[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url   = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0])
            # 'category':nextCategory,
            params = dict(cItem)
            params.update({'good_for_fav':True, 'title':title, 'url':url, 'icon':icon})
            self.addVideo(params)
            
        if self.loggedIn != True and 0 == len(self.currList):
            msg = _('The host %s requires registration. \nPlease fill your login and password in the host configuration. Available under blue button.' % self.getMainUrl())
            GetIPTVNotify().push(msg, 'error', 10)
            SetIPTVPlayerLastHostError(msg)
            
    def listYTChannel(self, cItem):
        printDBG('MaxtvGO.getVideos cItem[%s]' % (cItem))
        
        category = cItem.get("category", '')
        url      = cItem.get("url", '')
        page     = cItem.get("page", '1')
        if -1 == url.find('browse_ajax'):
            if url.endswith('/videos'): 
                url = url + '?flow=list&view=0&sort=dd'
            else:
                url = url + '/videos?flow=list&view=0&sort=dd'
        params = dict(cItem)
        self.currList = self.ytp.getVideosFromChannelList(url, category, page, params)
        for idx in range(len(self.currList)):
            if self.currList[idx].get('type', '') == 'video':
                self.currList[idx]['good_for_fav'] = True
        
    def getLinksForVideo(self, cItem):
        printDBG("MaxtvGO.getLinksForVideo [%s]" % cItem)
        
        if 1 == self.up.checkHostSupport(cItem.get('url', '')):
            videoUrl = cItem['url'].replace('youtu.be/', 'youtube.com/watch?v=')
            return self.up.getVideoLinkExt(videoUrl)
        
        self.tryTologin()
        
        retTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>')
        for item in data:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            if not self.cm.isValidUrl(url): continue
            type = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0]).lower()
            if 'mp4' in type:
                retTab.append({'name':'direct', 'url':self.getFullUrl(url), 'need_resolve':0})
            else:
                printDBG("Unknown source: [%s]" % item)
        
        return retTab
    
    def tryTologin(self):
        printDBG('tryTologin start')
        
        if None == self.loggedIn or self.login != config.plugins.iptvplayer.maxtvgo_login.value or\
            self.password != config.plugins.iptvplayer.maxtvgo_password.value:
        
            self.login = config.plugins.iptvplayer.maxtvgo_login.value
            self.password = config.plugins.iptvplayer.maxtvgo_password.value
            
            rm(self.COOKIE_FILE)
            
            self.loggedIn = False
            
            if '' == self.login.strip() or '' == self.password.strip():
                return False
            
            sts, data = self.getPage(self.getFullUrl('/login.php'))
            if not sts: return False
            
            sts, data = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'login'), ('</form', '>'))
            if not sts: return False
            actionUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0])
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>')
            post_data = {}
            for item in data:
                name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                post_data[name] = value
            
            post_data.update({'email':self.login, 'pass':self.password})
            
            httpParams = dict(self.defaultParams)
            httpParams['header'] = dict(httpParams['header'])
            httpParams['header']['Referer'] = self.getFullUrl('/index.php')
            sts, data = self.cm.getPage(actionUrl, httpParams, post_data)
            if sts and 'logout.php' in data:
                printDBG('tryTologin OK')
                self.loggedIn = True
            else:
                self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_ERROR, timeout = 10)
                printDBG('tryTologin failed')
        return self.loggedIn
        
    def getArticleContent(self, cItem, data=None):
        printDBG("MaxtvGO.getArticleContent [%s]" % cItem)
        self.tryTologin()
        
        
        if self.up.getDomain(cItem['url']) not in self.up.getDomain(self.getMainUrl()):
            return []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        otherInfo = {}
        retTab = []
        desc = []
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'chat_round'), ('<div', '>', 'modal-dialog'))[1]
        icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(data, '''poster=['"]([^'^"]+?)['"]''')[0])
        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'chat-video-title'), ('</div', '>'), False)[1])
        released = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'chat-video-date'), ('</div', '>'), False)[1])
        if released != '': otherInfo['released'] = released
        
        data = re.compile('<div[^>]+?odswiezchat[^>]+?>').split(data, 1)[-1]
        data = re.compile('<div[^>]+?chat-comment-block[^>]+?>').split(data)
        if len(data): del data[0]
        for item in data:
            author = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'chat-comment-author'), ('</div', '>'), False)[1])
            date   = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'chat-comment-content-data'), ('</div', '>'), False)[1])
            text   = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>', 'chat-comment-content"'), ('</div', '>'), False)[1])
            desc.append('%s[/br]%s[/br]%s[/br]' % (author, date, text))
            printDBG("============================================================================")
            printDBG('%s\n%s\n%s\n' % (author, date, text))
        
        desc = '------------------------------------------------------------------------------[/br]'.join(desc)
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        self.tryTologin()
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'}, 'list_genres')
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'list_yt_channel':
            self.listYTChannel(self.currItem)
        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'list_episodes')
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
        CHostBase.__init__(self, MaxtvGO(), True, [])
        
    def withArticleContent(self, cItem):
        return 'maxtvgo.com' in cItem.get('url', '')
    
    
    