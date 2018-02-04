# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError, GetIPTVNotify
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, byteify, rm, NextDay, PrevDay, GetDefaultLang
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
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
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper, iptv_js_execute
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.eurosportplayer_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.eurosportplayer_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("e-mail")+":",    config.plugins.iptvplayer.eurosportplayer_login))
    optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.eurosportplayer_password))
    return optionList
###################################################
def gettytul():
    return 'https://www.eurosportplayer.com/'

class EuroSportPlayer(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'eurosportplayer.com', 'cookie':'eurosportplayer.com.cookie', 'cookie_type':'MozillaCookieJar'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
        self.MAIN_URL = 'https://www.eurosportplayer.com/'
        self.DEFAULT_ICON_URL = 'https://superrepo.org/static/images/icons/original/xplugin.video.eurosportplayer.png.pagespeed.ic.xB5vsEn8I9.png'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/vnd.media-service+json; version=1', 'Origin':self.getMainUrl()[:-1]} )
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        
        self.loggedIn = None
        self.login    = ''
        self.password = ''
        self.serverApiData = {}
        self.tokenData = {}
        self.langsMap = {}
        self.OFFSET = None
        self.ABBREVIATED_MONTH_NAME_TAB = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        return self.cm.getPage(baseUrl, addParams, post_data)
        
    def getJSPage(self, baseUrl, addParams = {}, post_data = None):
        try:
            if self.tokenData['timeout'] <= time.time():
                self.getToken('refresh')
        
            getParams = dict(self.defaultParams)
            getParams.update(addParams)
            getParams['header'] = dict(self.AJAX_HEADER)
            getParams['header'].update(addParams.get('header', {}))
            getParams['header']['Authorization']  = self.tokenData['access_token']
            
            sts, data = self.cm.getPage(baseUrl, getParams, post_data)
        except Exception:
            printExc()
        return sts, data
    
    def listMainMenu(self, cItem):
        printDBG("EuroSportPlayer.listMainMenu")
        
        MAIN_CAT_TAB = [{'category':'on_air',         'title': _('On Air'),     }, 
                        {'category':'search',         'title': _('Search'),          'search_item':True}, 
                        {'category':'search_history', 'title': _('Search history')},]
        
        self.listsTab(MAIN_CAT_TAB, cItem)
        
    def _str2date(self, txt):
        return datetime.strptime(txt, '%Y-%m-%dT%H:%M:%SZ')
        
    def _gmt2local(self, txt):
        if self.OFFSET == None: self.OFFSET = datetime.now() - datetime.utcnow()
        utc_date = self._str2date(txt)
        utc_date = utc_date + self.OFFSET
        if utc_date.time().second == 59:
            utc_date = utc_date + timedelta(0,1)
        return utc_date
        
    def _getLanguageDisplayName(self, key):
        langName = key
        if self.langsMap == {}:
            try:
                for item in self.serverApiData['locale']['languageMenuModel']['list']:
                    self.langsMap[item['locale']] = item['displayName']
            except Exception:
                printExc()
        return self.langsMap.get(key, str(key))
        
    def _getCatsDisplay(self, cats):
        tab = []
        for item in cats:
            val = self.serverApiData['i18n_dictionary'].get('sport_' + item)
            if val != '': tab.append(val)
        return ', '.join(tab)
        
    def fillServerApiData(self):
        printDBG('EuroSportPlayer.fillServerApiData')
        if self.serverApiData != {}:
            return
        
        serverApiData = {}
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return False
        
        jscode = ['var window={};function getStartupDeviceTypeString(){return "desktop";}\nwindow.requirejs_data={};requirejs=function(){if (2 == arguments.length) {window.requirejs_data.siteScripts=arguments[0];arguments[1]()} else {window.requirejs_data.scripts=arguments[0];}};requirejs.config=function(){window.requirejs_data.config=arguments[0];};']
        markers = ['window.server_path','window.i18n_dictionary','window.locale','window.SPORTS_BY_ID','window.bamTrackingConfig','window.specialEvents','requirejs']
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in data:
            for m in markers:
                if m in item:
                    jscode.append(item)
                    break
        jscode.append('\nprint(JSON.stringify(window));')
        ret = iptv_js_execute( '\n'.join(jscode) )
        if ret['sts'] and 0 == ret['code']:
            data = ret['data'].strip()
            try:
                serverApiData = byteify(json.loads(data))
                clientId = serverApiData['server_path']['sdk']['clientId']
                env = serverApiData['server_path']['sdk']['environment']
                url = 'https://bam-sdk-configs.mlbam.net/v0.1/%s/browser/v2.1/windows/chrome/%s.json' % (clientId, env)
                sts, data = self.getPage(url)
                if not sts: return False
                serverApiData['prod'] =  byteify(json.loads(data))
            except Exception:
                printExc()
                return
        
        self.serverApiData = serverApiData
        
    def getToken(self, grantType):
        printDBG('EuroSportPlayer.getToken start')
        bRet = False
        try:
            getParams = dict(self.defaultParams)
            getParams['header'] = dict(self.AJAX_HEADER)
        
            clientData = self.serverApiData['prod']['authorization']['client']
            
            url = clientData['links'][0]['href']
            getParams['header'].update(clientData['links'][0]['headers'])
            getParams['header']['Authorization'] = getParams['header']['Authorization'].replace('{encodedApiToken}', self.serverApiData['server_path']['sdk']['clientApiKey'])
            post_data = None
            if grantType == 'init':
                import uuid
                post_data = {'grant_type':'client_credentials', 'latitude':0, 'longitude':0, 'platform':clientData['platformId'], 'token':str(uuid.uuid4())}
            elif grantType == 'refresh':
                post_data = {'grant_type':'refresh_token', 'latitude':0, 'longitude':0, 'platform':clientData['platformId'], 'token':self.tokenData['refresh_token']}
            elif grantType == 'code':
                post_data = {'grant_type':'urn:mlbam:params:oauth:grant_type:token', 'latitude':0, 'longitude':0, 'platform':clientData['platformId'], 'token':self.tokenData['access_code']}
            sts, data = self.getPage(url, getParams, post_data)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            self.tokenData.update(byteify(json.loads(data)))
            self.tokenData['timeout'] = time.time() + self.tokenData['expires_in'] # expires_in - in seconds
            bRet = True
        except Exception:
            printExc()
        printDBG('EuroSportPlayer.getToken end bRet[%s]' % bRet)
        return bRet
        
    def listOnAir(self, cItem, nextCategory):
        printDBG("EuroSportPlayer.listOnAir [%s]" % cItem)
        try:
            variables = {"uiLang":self.serverApiData['locale']['language'],"mediaRights":["GeoMediaRight"],"preferredLanguages":self.serverApiData['locale']['languageOrder']}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/eurosport/web/Airings/onAir?variables=' + urllib.quote(json.dumps(variables, separators=(',', ':')))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            data = byteify(json.loads(data))
            for item in data['data']['Airings']:
                title = self.cleanHtmlStr(item['titles'][0]['title'])
                try: icon  = item['photos'][0]['uri']
                except Exception: icon = ''
                duration =  self.cleanHtmlStr(item['runTime'])
                startDate = self._gmt2local(item['startDate'])
                endDate = self._gmt2local(item['endDate'])
                language = self._getLanguageDisplayName(item['titles'][0]['language'])
                categories = self._getCatsDisplay(item['genres'])
                episodeName = self.cleanHtmlStr(item['titles'][0]['episodeName'])
                
                desc = []
                desc.insert(0, categories)
                desc.insert(0, language)
                desc.insert(0, episodeName)
                desc.insert(0, '%s - %s' % (startDate.strftime('%H:%M'), endDate.strftime('%H:%M')))
                
                desc = ' | '.join(desc) + '[/br]' + self.cleanHtmlStr(item['titles'][0]['descriptionLong'])
                
                if item['liveBroadcast']:
                    title = '[%s] %s' % (self.serverApiData['i18n_dictionary']['Live'], title)
                
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'icon':icon, 'desc':desc, 'priv_item':item})
                self.addDir(params)
                
        except Exception:
            printExc()
            
    def listSearchItems(self, cItem, nextCategory):
        printDBG("EuroSportPlayer.listSearchItems [%s]" % cItem)
        try:
            NOW = datetime.now()
            page = cItem.get('page', 1)
            variables = {"index":"eurosport_global","preferredLanguages":["pl","en"],"uiLang":"pl","mediaRights":["GeoMediaRight"],"page":page,"pageSize":20,"q":cItem['f_query'],"type":["Video","Airing","EventPage"],"include_images":True}
            url = self.serverApiData['server_path']['search'] + '/persisted/query/core/sitesearch?variables=' + urllib.quote(json.dumps(variables, separators=(',', ':')))
            
            sts, data = self.getJSPage(url)
            if not sts: return
            
            data = byteify(json.loads(data))['data']['sitesearch']
            for item in data['hits']:
                item = item['hit']
                title = self.cleanHtmlStr(item['titles'][0]['title'])
                try: icon  = item['photos'][0]['uri']
                except Exception: icon = ''
                duration =  self.cleanHtmlStr(item['runTime'])
                startDate = self._gmt2local(item['startDate'])
                endDate = self._gmt2local(item['endDate'])
                language = self._getLanguageDisplayName(item['titles'][0]['language'])
                categories = self._getCatsDisplay(item['genres'])
                episodeName = self.cleanHtmlStr(item['titles'][0]['episodeName'])
                desc = []
                desc.insert(0, categories)
                desc.insert(0, language)
                desc.insert(0, episodeName)
                
                if NOW < startDate: 
                    prefix = self.serverApiData['i18n_dictionary']['Header_Upcoming']
                elif item['liveBroadcast'] and \
                    startDate.day == NOW.day and \
                    startDate.month == NOW.month and \
                    startDate.year == NOW.year: 
                    prefix = self.serverApiData['i18n_dictionary']['Live']
                else: 
                    prefix = item['mediaConfig']['type']
                title = '[%s] %s' % (prefix, title)
                
                if prefix.lower() == 'video': dateStr = str(item['runTime'])
                else: dateStr = '%s - %s' % (startDate.strftime('%H:%M'), endDate.strftime('%H:%M'))
                
                month = self.ABBREVIATED_MONTH_NAME_TAB[startDate.month-1]
                if startDate.year == NOW.year: dateStr += ' | %s %s' % (startDate.day, self.serverApiData['i18n_dictionary'].get(month, month))
                else: dateStr += ' | %s %s %s' % (startDate.day, self.serverApiData['i18n_dictionary'].get(month, month), startDate.year)
                    
                desc.insert(0, dateStr)
                desc = ' | '.join(desc) + '[/br]' + self.cleanHtmlStr(item['titles'][0]['descriptionLong'])
                
                params = dict(cItem)
                params.update({'good_for_fav':False, 'category':nextCategory, 'title':title, 'icon':icon, 'desc':desc, 'priv_item':item})
                self.addDir(params)
            
            if page*20 < data['meta']['hits']:
                params = dict(cItem)
                params.pop('priv_item', None)
                params.update({'good_for_fav':False, 'title':_('Next page'), 'page':page+1})
                self.addDir(params)
                
                self.ABBREVIATED_MONTH_NAME_TAB = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
        except Exception:
            printExc()
            
    def listLinksTypeItems(self, cItem):
        printDBG("EuroSportPlayer.listLinksTypeItems [%s]" % cItem)
        try:
            privItem = cItem['priv_item']
            title = self.cleanHtmlStr(privItem['titles'][0]['title'])
            for item in privItem['playbackUrls']:
                rel = item['rel']
                url = item['href']
                params = dict(cItem)
                params.pop('priv_item', None)
                params.update({'good_for_fav':False, 'title':title, 'url':url, 'desc':rel})
                self.addVideo(params)
        except Exception:
            printExc()
    
    def tryTologin(self):
        printDBG('EuroSportPlayer.tryTologin start')
        errorMsg = 'Error communicating with the server.'
        
        if None == self.loggedIn or self.login != config.plugins.iptvplayer.eurosportplayer_login.value or\
            self.password != config.plugins.iptvplayer.eurosportplayer_password.value:
        
            self.login = config.plugins.iptvplayer.eurosportplayer_login.value
            self.password = config.plugins.iptvplayer.eurosportplayer_password.value
            
            rm(self.COOKIE_FILE)
            
            self.loggedIn = False
            self.loginMessage = ''
            
            if '' == self.login.strip() or '' == self.password.strip():
                msg = _('The host %s requires subscription.\nPlease fill your login and password in the host configuration - available under blue button.' % self.getMainUrl())
                GetIPTVNotify().push(msg, 'info', 10)
                return False
            
            if not self.getToken('init'):
                msg = _(errorMsg + '\nError[1].')
                GetIPTVNotify().push(msg, 'error', 10)
                return False
            
            try:
                baseUrl = self.serverApiData['server_path']['server'] + '/'
                url = self.getFullUrl('/login', baseUrl)
                
                sts, data = self.getPage(url)
                if not sts: return False
                
                getParams = dict(self.defaultParams)
                getParams['raw_post_data'] = True
                getParams['header'] = dict(self.AJAX_HEADER)
            
                clientData = self.serverApiData['prod']['authentication']['client']
                
                url = clientData['links'][0]['href']
                getParams['header'].update(clientData['links'][0]['headers'])
                getParams['header']['Authorization'] = getParams['header']['Authorization'].replace('{encodedUserToken}', self.tokenData['access_token'])
                post_data = '{"type":"email-password","email":{"address":"%s"},"password":{"value":"%s"}}' % (self.login, self.password)
                
                sts, data = self.getPage(url, getParams, post_data)
                if '401' in str(data):
                    msg =  _('Login failed. Invalid email or password.')
                    GetIPTVNotify().push(msg, 'error', 10)
                    return False
                else:
                    data = byteify(json.loads(data))
                    printDBG(data)
                    self.tokenData['access_code'] = data['code']
                    self.tokenData['access_timeout'] = time.time() + (data['exp'] - data['iat']) / 1000.0
                    
                    if not self.getToken('code'):
                        msg = _(errorMsg + '\nError[2].')
                        GetIPTVNotify().push(msg, 'error', 10)
                        return False
                    self.loggedIn = True
            except Exception:
                printExc()
            
            printDBG('EuroSportPlayer.tryTologin end loggedIn[%s]' % self.loggedIn)
            return self.loggedIn
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("EuroSportPlayer.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        params = dict(cItem)
        params.update({'category':'list_search_items', 'f_query':searchPattern})
        self.listSearchItems(params, 'list_links_types')
        
    def getLinksForVideo(self, cItem):
        printDBG("EuroSportPlayer.getLinksForVideo [%s]" % cItem)
        self.fillServerApiData()
        self.tryTologin()
        
        linksTab = []
        try:
            url = cItem['url'].replace('{scenario}', 'browser~unlimited')
            sts, data = self.getJSPage(url)
            data = byteify(json.loads(data))['stream']
            printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            for item in [('slide', 'slide'), ('complete', 'complete')]:
                if item[0] not in data: continue
                linksTab.append({'url':data[item[0]], 'name':item[1], 'need_resolve':1})
        except Exception:
            printExc()
        
        return linksTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("EuroSportPlayer.getVideoLinks [%s]" % baseUrl)
        self.getToken('refresh')
        
        videoUrl = strwithmeta(baseUrl)
        linksTab = []
        
        try:
            getParams = dict(self.defaultParams)
            getParams['header'] = dict(self.HTTP_HEADER)
            getParams['header']['Authorization']  = self.tokenData['access_token']
            linksTab = getDirectM3U8Playlist(baseUrl, cookieParams=getParams, checkContent=False, sortWithMaxBitrate=999999999)
            token = self.tokenData['access_token']
            referer = self.serverApiData['server_path']['server'] + '/'
            for idx in range(len(linksTab)):
                linksTab[idx]['url'] = strwithmeta(linksTab[idx]['url'], {'Authorization':token, 'User-Agent':getParams['header']['User-Agent'], 'Referer':referer, 'Origin':referer[:-1]})
        except Exception:
            printExc()
        
        return linksTab
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        self.fillServerApiData()
        self.tryTologin()
        
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
        elif category == 'on_air':
            self.listOnAir(self.currItem, 'list_links_types')
        elif category == 'list_links_types':
            self.listLinksTypeItems(self.currItem)
        elif category == 'list_search_items':
            self.listSearchItems(self.currItem, 'list_links_types')
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
        CHostBase.__init__(self, EuroSportPlayer(), True, [])
        
    #def getSearchTypes(self):
    #    searchTypesOptions = []
    #    return searchTypesOptions
    