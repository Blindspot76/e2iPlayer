# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir, GetTmpDir, byteify, rm, CSelOneLink
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
config.plugins.iptvplayer.rtbfbe_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.rtbfbe_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    #optionList.append(getConfigListEntry(_("login")+":", config.plugins.iptvplayer.rtbfbe_login))
    #optionList.append(getConfigListEntry(_("password")+":", config.plugins.iptvplayer.rtbfbe_password))
    return optionList
###################################################

def gettytul():
    return 'https://www.rtbf.be/'

class RTBFBE(CBaseHostClass):
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'rtbf.be', 'cookie':'rtbf.be.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = 'https://www.rtbf.be/'
        self.DEFAULT_ICON_URL = 'https://www.mediaspecs.be/wp-content/uploads/RTBF_Auvio.png'
        self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.AJAX_HEADER = dict(self.HTTP_HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.login = ''
        self.password = ''
        self.loggedIn = None
        self.loginMessage = ''
        self.userGeoLoc = ''
        
        self.cacheChannels = []
        
    def setMainUrl(self, url):
        if self.cm.isValidUrl(url):
            self.MAIN_URL = self.cm.getBaseUrl(url)
        
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        baseUrl = self.cm.iriToUri(baseUrl)
        return self.cm.getPage(baseUrl, addParams, post_data)
        
    def listMainMenu(self, cItem, nextCategory):
        printDBG("RTBFBE.listMainMenu")
        
        CAT_TAB = [{'category':'sections',       'title': _('Main'),       'url':self.getFullUrl('/auvio/')},
                   #{'category':'live',           'title': 'En Direct',     'url':self.getFullUrl('/auvio/direct#/')},
                   #{'category':'channels',       'title': 'Chaînes',       'url':self.getFullUrl('/auvio/')},
                   {'category':'sections',       'title': 'Émissions',     'url':self.getFullUrl('/auvio/emissions')},
                   {'category':'categories',     'title': 'Catégories',    'url':self.getFullUrl('/news/api/menu?site=media')},
                   {'category':'search',         'title': _('Search'),          'search_item':True}, 
                   {'category':'search_history', 'title': _('Search history')},]
        
        params = dict(cItem)
        params['desc'] = self.loginMessage
        self.listsTab(CAT_TAB, params)
        
    def listCategories(self, cItem, nextCategory):
        printDBG("RTBFBE.listCategories")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        cUrl = data.meta['url']
        self.setMainUrl(cUrl)
        
        try:
            data = byteify(json.loads(data))['item']
            for item in data:
                if item['@attributes']['id'] == 'category':
                    for it in item['item']:
                        it = it['@attributes']
                        if it['url'].startswith('.'): continue
                        url = self.getFullUrl(it['url'])
                        title = self.cleanHtmlStr(it['name'])
                        params = dict(cItem)
                        params.update({'good_for_fav':False, 'url':url, 'title':title, 'category':nextCategory})
                        self.addDir(params)
                    break
        except Exception:
            printExc()
        
    def serParams(self, obj, data=''):
        newData = ''
        if isinstance(obj, list):
            for idx in range(len(obj)):
                newData += self.serParams(obj[idx], data + urllib.quote('[%d]' % idx))
        elif isinstance(obj, dict):
            for key in obj:
                newData += self.serParams(obj[key], data + urllib.quote('[%s]' % key))
        elif obj == True:
            newData += data + '=true&'
        elif obj == False:
            newData += data + '=false&'
        else:
            newData += data + '=%s&' % urllib.quote(str(obj))
        return newData
        
    def listSections(self, cItem, nextCategory1, nextCategory2):
        printDBG("RTBFBE.listSections")
        page = cItem.get('page', 0)
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        
        cItem = dict(cItem)
        defaultMediaType = cItem.pop('default_media_type', 'video')
        
        cUrl = data.meta['url']
        self.setMainUrl(cUrl)
        
        nextPage = self.cm.ph.getSearchGroups(data, '''(<a[^>]+?pagination__link[^>]+?Next[^>]+?>)''')[0]
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(nextPage, '''href=['"]([^'^"]+?)['"]''')[0], cUrl)
        
        sections = self.cm.ph.getAllItemsBeetwenNodes(data, ('<section', '>'), ('</section', '>'), False)
        if page == 0: sections.append(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'autocomplete--medias'), ('</section', '>'))[1])
        
        reObj = re.compile('\sdata\-([^=]+?)="([^"]+?)"')
        query = []
        uuids = []
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<b', '>', 'data-uuid'), ('</b', '>'))
        for item in data:
            item = reObj.findall(item)
            obj = {}
            for it in item:
                if it[0] == 'devices': continue
                if it[0] == 'uuid': uuids.append(it[1])
                try: obj[it[0]] = byteify(json.loads(self.cleanHtmlStr(it[1])))
                except Exception: obj[it[0]] = it[1]
            query.append(obj)
        
        if len(query):
            query = self.serParams(query, 'data')
            url = self.getFullUrl('/news/api/block?' + query)
            sts, data = self.getPage(url)
            if not sts: return
            
            try:
                data = byteify(json.loads(data))['blocks']
                for uuid in uuids:
                    if uuid not in data: continue
                    sections.append(data[uuid])
            except Exception:
                printExc()
        
        for sectionItem in sections:
            sectionItem = sectionItem.split('<section', 1)[-1]
            sTitle = self.cm.ph.getDataBeetwenNodes(sectionItem, ('<h', '>', 'www-title'), ('</h', '>'))[1]
            sUrl = self.getFullUrl(self.cm.ph.getSearchGroups(sTitle, '''href=['"]([^'^"]+?)['"]''')[0])
            if sUrl == '' and '<article' not in sectionItem: 
                sUrl = self.getFullUrl(self.cm.ph.getSearchGroups(sectionItem, '''<a[^>]+?href=['"]([^'^"]+?)['"]''')[0])
            sTitle = self.cleanHtmlStr(sTitle)
            if sTitle == '': continue
            sItems = []
            sectionItem = self.cm.ph.getAllItemsBeetwenMarkers(sectionItem, '<article', '</article>')
            for item in sectionItem:
                icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''data\-srcset=['"]([^'^"^\s]+?)[\s'"]''')[0])
                header = self.cm.ph.getDataBeetwenMarkers(item, '<header', '</header>')[1]
                url = self.cm.ph.getSearchGroups(header, '''href=['"]([^'^"]+?)['"]''')[0]
                if url == '' or url[0] in ['{', '[']: continue
                url = self.getFullUrl(url)
                title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(header, ('<h', '>', '__title'), ('</h', '>'))[1])
                subTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(header, ('<h', '>', '__subtitle'), ('</h', '>'))[1])
                duration = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(item, ('<span', '>', 'duration'), ('</span', '>'))[1])
                desc = []
                if subTitle != '':
                    if subTitle.decode('utf-8').lower() not in title.decode('utf-8').lower():
                        title = '%s - %s' % (title, subTitle)
                    else: 
                        desc.append(subTitle)
                if duration != '': desc.append(duration)
                desc.append(self.cleanHtmlStr(item.split('</header>', 1)[-1]))
                params = {'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'desc':'[/br]'.join(desc)}
                if 'ico-volume' in item: params['type'] = 'audio'
                elif 'ico-play' in item: params['type'] = 'video'
                elif '/emissions/' in url: params['type'] = 'video'
                else: params['type'] = defaultMediaType
                sItems.append(params)
                
            if len(sItems): icon = sItems[0]['icon']
            else: icon = ''
            
            if sUrl != '' and sUrl != cItem['url']:
                if 0 == len(sItems): title = sTitle
                else: title = _('More') 
                params = dict(cItem)
                params.update({'good_for_fav':False, 'url':sUrl, 'title':title, 'category':nextCategory2, 'icon':icon})
                sItems.append(params)
            
            if len(sItems) > 1:
                params = dict(cItem)
                params.update({'good_for_fav':False, 'title':sTitle, 'category':nextCategory1, 'sub_items':sItems, 'icon':icon})
                self.addDir(params)
            elif len(sItems) == 1:
                self.currList.append(sItems[0])
                
        if 1 == len(self.currList) and 'sub_items' in self.currList[0]:
            self.currList = self.currList[0]['sub_items']
                
        if nextPage != '' and len(self.currList):
            params = dict(cItem)
            params.update({'good_for_fav':False, 'default_media_type':defaultMediaType, 'category':nextCategory2, 'url':nextPage,  'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listSubItems(self, cItem):
        printDBG("RTBFBE.listSubItems")
        self.currList = cItem['sub_items']
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("RTBFBE.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        params = {'name':'category', 'type':'category', 'default_media_type':searchType, 'url':self.getFullUrl('/auvio/recherche?q=%s&type=%s') % (urllib.quote_plus(searchPattern), searchType)}
        self.listSections(params, 'list_sub_items', 'sections')
        
    def getUserGeoLoc(self):
        if 0 == len(self.userGeoLoc):
            sts, data = self.getPage(self.getFullUrl('/api/geoloc'))
            try:
                byteify(json.loads(data), '', True)
                self.userGeoLoc = data['country']
            except Exception:
                printExc()
        return self.userGeoLoc
        
    def getLinksForVideo(self, cItem):
        printDBG("RTBFBE.getLinksForVideo [%s]" % cItem)
        self.tryTologin()
        
        retTab = []
        mp4Tab = []
        hlsTab = []
        dashTab = []
        subsTab = []
        cacheKey = cItem['url']
        cacheTab = self.cacheLinks.get(cacheKey, [])
        if len(cacheTab): return cacheTab
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return []
        
        cUrl = data.meta['url']
        self.setMainUrl(cUrl)
        
        url = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
        urlParams = dict(self.defaultParams)
        urlParams['header'] = dict(urlParams['header'])
        urlParams['header']['Referer'] = cUrl
        
        sts, data = self.getPage(url, urlParams)
        if not sts: return []
        
        geoLocRestriction = ''
        data = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, 'data-media="', '"', False)[1])
        try:
            data = byteify(json.loads(data), '', True)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            geoLocRestriction = data.get('geoLocRestriction', '')
            
            # HLS LINKS
            hslUrls = [data.get('streamUrlHls', '')]
            hslUrls.append(data.get('urlHls', ''))
            for hslUrl in hslUrls:
                if not self.cm.isValidUrl(hslUrl): continue
                hlsTab = getDirectM3U8Playlist(hslUrl, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999)
            
            # DASH LINKS
            dashUrl = data.get('urlDash', '')
            if self.cm.isValidUrl(dashUrl):
                dashTab = getMPDLinksWithMeta(dashUrl, checkExt=False, sortWithMaxBandwidth=999999999)
            
            # MP4 LINKS
            if 'sources' in data:
                try:
                    tmp = []
                    for type in ['url', 'high', 'mobile', 'web']:
                        url = data['sources'][type]
                        if url in tmp: continue
                        tmp.append(url)
                        name = self.cm.ph.getSearchGroups(url, '''[\-_]([0-9]+?)p\.mp4''')[0]
                        if name == '': name = type
                        if self.cm.isValidUrl(url): mp4Tab.append({'name':'[mp4] %sp'% name, 'url':url, 'quality':name})
                    mp4Tab = CSelOneLink(mp4Tab, lambda item: int(item['quality']), 999999999).getSortedLinks()
                except Exception:
                    printExc()
                    
            # SUBTITLES
            for item in data['tracks']:
                if isinstance(item, basestring): item = data['tracks'][item]
                subtitleUrl = item['url']
                if not self.cm.isValidUrl(subtitleUrl): continue
                subsTab.append({'title':item['label'], 'url':subtitleUrl, 'lang':item['lang'], 'format':item['format']})
                
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(subsTab)
        except Exception:
            printExc()
        
        if len(hlsTab) or len(dashTab) or geoLocRestriction == 'open' or \
           geoLocRestriction == self.getUserGeoLoc():
            retTab.extend(mp4Tab)
        retTab.extend(hlsTab)
        retTab.extend(dashTab)
        
        for idx in range(len(retTab)):
            retTab[idx]['url'] = strwithmeta(retTab[idx]['url'], {'external_sub_tracks':subsTab})
            retTab[idx]['need_resolve'] = 1
        
        if 0 == len(retTab) and geoLocRestriction != 'open':
            errorMessage = self.cleanHtmlStr('Media geo-blocked.')
            SetIPTVPlayerLastHostError(errorMessage)
        
        if len(retTab):
            self.cacheLinks[cacheKey] = retTab
        return retTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("RTBFBE.getVideoLinks [%s]" % videoUrl)
        self.tryTologin()
        
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
        
        return [{'name':'direct', 'url':videoUrl}]
        
    def getArticleContent(self, cItem):
        printDBG("RTBFBE.getArticleContent [%s]" % cItem)
        self.tryTologin()
        retTab = []
        
        url = cItem.get('url', '')
        if ',odcinek' in url: type = 'episode'
        elif 'serial,' in url: type = 'series'
        elif 'film,' in url: type = 'movie'  
        else: return []
        
        sts, data = self.getPage(url)
        if not sts: return []
        
        otherInfo = {}
        retTab = []
        desc = []
        
        desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<p', '</p>')[1])
        icon = self.cm.ph.getDataBeetwenNodes(data, ('<meta', '>', 'image'), ('<', '>'))[1]
        icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(icon, '''content=['"]([^'^"]+?)['"]''')[0])
        
        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'prawo-kontener'), ('</div', '>'), False)[1].replace('&laquo;', '').replace('&raquo;', ''))
        if type == 'episode':
            sTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'movieinfo'), ('</h', '>'), False)[1])
            title = '%s - %s' % (sTitle, title)
        
        if title == '': title = cItem['title']
        if desc == '':  desc = cItem.get('desc', '')
        if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullIconUrl(icon)}], 'other_info':otherInfo}]
        
    def tryTologin(self):
        printDBG('RTBFBE.tryTologin start')
        
        if self.login == config.plugins.iptvplayer.rtbfbe_login.value and \
           self.password == config.plugins.iptvplayer.rtbfbe_password.value:
           return 
        
        self.login = config.plugins.iptvplayer.rtbfbe_login.value
        self.password = config.plugins.iptvplayer.rtbfbe_password.value
        
        rm(self.COOKIE_FILE)
        self.loggedIn = False
        
        if '' == self.login.strip() or '' == self.password.strip():
            return False
        
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return False
        
        nick = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', 'nick'), ('</a', '>'))[1])
        loginMarker = 'logout.html'
        if loginMarker not in data or nick != self.login:
            self.cm.clearCookie(self.COOKIE_FILE, ['__cfduid', 'cf_clearance'])
            sts, data = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'user'), ('</form', '>'))
            if not sts: return False
            
            actionUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0])
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>')
            post_data = {}
            for item in data:
                name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''')[0]
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''')[0]
                post_data[name] = value
            
            post_data.update({'ga10':self.login, 'gb10':self.password, 'gautolog':'t'})
            
            httpParams = dict(self.defaultParams)
            httpParams['header'] = dict(httpParams['header'])
            httpParams['header']['Referer'] = self.getMainUrl()
            sts, data = self.cm.getPage(actionUrl, httpParams, post_data)
        if sts and loginMarker in data:
            self.loggedIn = True
            data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'po-zalogowaniu'), ('<a', '>', 'logout.html'))[1]
            data = data.split('</a>')
            self.loginMessage =  []
            for t in data:
                t = self.cleanHtmlStr(t)
                if t not in ['', '>']: self.loginMessage.append(t)
            self.loginMessage = '[/br]'.join(self.loginMessage)
        else:
            message = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'warn'), ('</div', '>'))[1])
            self.sessionEx.open(MessageBox, _('Login failed.') + '\n' + message, type = MessageBox.TYPE_ERROR, timeout = 10)
            printDBG('tryTologin failed')
        return self.loggedIn
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        self.tryTologin()
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        self.informAboutGeoBlockingIfNeeded('BE')

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||| name[%s], category[%s] " % (name, category) )
        self.cacheLinks = {}
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu({'name':'category'}, 'sub_menu')
    #CATEGORIES
        elif category == 'categories':
            self.listCategories(self.currItem, 'sections')
    #SECTIONS
        elif category == 'sections':
            self.listSections(self.currItem, 'list_sub_items', 'sections')
        elif category == 'list_sub_items':
            self.listSubItems(self.currItem)
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
        CHostBase.__init__(self, RTBFBE(), True, [])
        
    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append((_("Video"), "video"))
        searchTypesOptions.append((_("Audio"), "audio"))
        return searchTypesOptions
        
    #def withArticleContent(self, cItem):
    #    url = cItem.get('url', '')
    #    if 'serial,' in url or ',odcinek' in url or 'film,' in url:
    #        return True
    #    return False