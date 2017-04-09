# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CDisplayListItem, RetHost
from Plugins.Extensions.IPTVPlayer.components.isubprovider import CSubProviderBase, CBaseSubProviderClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetDefaultLang, GetCookieDir, byteify, \
                                                          RemoveDisallowedFilenameChars, GetSubtitlesDir, GetTmpDir, rm, \
                                                          MapUcharEncoding, GetPolishSubEncoding, rmtree, mkdirs
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
import time
import re
import urllib
import unicodedata
import base64
try:    from urlparse import urlsplit, urlunsplit
except Exception: printExc()
from os import listdir as os_listdir, path as os_path
try:    import json
except Exception: import simplejson as json
try:
    try: from cStringIO import StringIO
    except Exception: from StringIO import StringIO 
    import gzip
except Exception: pass
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################

class OpenSubtitles(CBaseSubProviderClass): 
    
    def __init__(self, params={}):
        self.MAIN_URL      = 'https://www.opensubtitles.org/'
        self.USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0'
        self.HTTP_HEADER   = {'User-Agent':self.USER_AGENT, 'Referer':self.MAIN_URL, 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding':'gzip, deflate'}
        
        params['cookie'] = 'opensubtitlesorg2.cookie'
        CBaseSubProviderClass.__init__(self, params)
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.languages = []
        
        self.dInfo = params['discover_info']
        self.searchTypes = [{'title':_('Search Movies and TV Series')}, {'title':_('Search only in Movies'), 'search_only_movies':'on'}, {'title':_('Search only in TV Series'), 'search_only_tv_series':'on'} ]
        self.episodesCache = {}
        self.logedIn = None
        
    def getPage(self, url, params={}, post_data=None):
        if params == {}:
            params = dict(self.defaultParams)
        sts, data = self.cm.getPage(url, params, post_data)
        return sts, data
        
    def initSubProvider(self, cItem):
        printDBG("OpenSubtitles.initSubProvider")
        self.logedIn = False
        
        rm(self.COOKIE_FILE)
        
        # select site language 
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="lang-selector"', '</ul>')[1]
        printDBG(tmp)
        lang = GetDefaultLang()
        url  = self.getFullUrl(self.cm.ph.getSearchGroups(tmp, 'href="([^"]+?setlang\-%s[^"]*?)"' % lang)[0])
        if self.cm.isValidUrl(url):
            sts, data = self.getPage(url)
            if not sts: return
            
        # fill language cache
        self.languages = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<select name="SubLanguageID"', '</select>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<option', '</option>')
        for item in tmp:
            title = self.cleanHtmlStr(item)
            subLanguageID = self.cm.ph.getSearchGroups(item, 'value="([^"]+?)"')[0]
            self.languages.append({'title':title, 'sub_language_id':subLanguageID})
        
        # login user 
        login  = config.plugins.iptvplayer.opensuborg_login.value
        passwd = config.plugins.iptvplayer.opensuborg_password.value
        if login != '' and passwd != '':
            errMsg = _('Failed to connect to server "%s".') % self.getMainUrl()
            
            url  = self.getFullUrl(self.cm.ph.getSearchGroups(data, '<form[^>]+?name="loginform"[^>]+?action="([^"]+?)"')[0])
            sts, data = self.getPage(url)
            if not sts:
                self.sessionEx.open(MessageBox, errMsg, type = MessageBox.TYPE_INFO, timeout = 5)
                return
            
            data = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>')[1]
            loginUrl = self.getFullUrl(self.cm.ph.getSearchGroups(data, 'action="([^"]+?)"')[0])
            data = re.compile('<input[^>]+?name="([^"]+?)"[^>]+?value="([^"]+?)"').findall(data)
            post_data = {}
            for item in data:
                post_data[item[0]] = item[1]
            post_data.update({'user':login, 'password':passwd, 'remember':'on'})
            
            sts, data = self.getPage(loginUrl, post_data=post_data)
            if not sts:
                self.sessionEx.open(MessageBox, errMsg, type = MessageBox.TYPE_INFO, timeout = 5)
            elif 'logout' not in data:
                self.sessionEx.open(MessageBox, _('Failed to log in user "%s". Please check your login and password.') % login, type = MessageBox.TYPE_INFO, timeout = 5)
                self.logedIn = False
            else:
                self.logedIn = True
        
    def listLanguages(self, cItem, nextCategory):
        printDBG("OpenSubtitles.listLanguages")
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.languages, cItem)
    
    def listSearchTypes(self, cItem, nextCategory):
        printDBG("OpenSubtitles.listLanguages")
        cItem = dict(cItem)
        cItem['category'] = nextCategory
        self.listsTab(self.searchTypes, cItem)
        
    def searchSubtitles(self, cItem, nextCategory):
        printDBG("OpenSubtitles.searchSubtitles")
        url = cItem.get('url', '')
        if url == '':
            query = {'id':8, 'action':'search', 'SubSumCD':'', 'Genre':'', 'MovieByteSize':'', 'MovieLanguage':'', 'MovieImdbRatingSign':'1', 'MovieImdbRating':'', 'MovieCountry':'', 'MovieYearSign':'1', 'MovieYear':'', 'MovieFPS':'', 'SubFormat':'', 'SubAddDate':'', 'Uploader':'', 'IDUser':'', 'Translator':'', 'IMDBID':'', 'MovieHash':'', 'IDMovie':''}
            keywords = urllib.quote_plus(self.params['confirmed_title'])
            subLanguageID = cItem.get('sub_language_id', '')
            searchOnlyTVSeries = cItem.get('search_only_tv_series', '')
            searchOnlyMovies   = cItem.get('search_only_movies', '')
            
            if 'on' == searchOnlyTVSeries:
                season  = self.dInfo.get('season', None)
                episode = self.dInfo.get('episode', None)
            else:
                season   = None
                episode  = None
            
            if season == None: season = '' 
            if episode == None: episode = '' 
            
            query['MovieName']     = keywords
            query['SubLanguageID'] = subLanguageID
            if 'on' == searchOnlyTVSeries: query['SearchOnlyTVSeries'] = searchOnlyTVSeries
            if 'on' == searchOnlyMovies:   query['SearchOnlyMovies']   = searchOnlyMovies
            query['Season']  = season
            query['Episode'] = episode
            
            url = self.getFullUrl('/search2') + '?' + urllib.urlencode(query)
        else:
            url = cItem['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<table id="search_results"', '</tbody>')[1]
        m1  = '<tr id="name'
        m2  = '<tr onclick'
        m3  = '<span id="season'
        
        cItem = dict(cItem)
        cItem['url'] = url
        
        if m1 in tmp:
            self.listSearchItems(cItem, cItem['category'], data)
        elif m2 in tmp:
            self.listDownloadItems(cItem, nextCategory, data)
        elif m3 in tmp:
            self.listSeasonsItems(cItem, 'list_episodes', data)
            
    def listSearchItems(self, cItem, nextCategory, data=None):
        printDBG("OpenSubtitles.listSearchItems")
        if data == None:
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return
        page = cItem.get('page', 1)
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(data, '<link[^>]+?rel="next"[^>]+?href="([^"]+?)"')[0])
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tr id="name', '</tbody>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr id="name', '</tr>')
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<td', '</a>')[1])
            imdbid = self.cm.ph.getSearchGroups(item, '''/tt([0-9]+?)[^0-9]''')[0]
            
            descTab  = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<td', '</td>') 
            for t in tmp:
                t = t.split('<a rel="nofollow"')[0]
                t = self.cleanHtmlStr(t)
                if t != '': descTab.append(t)
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'imdbid':imdbid, 'url':self.getFullUrl(url), 'desc':' | '.join(descTab)})
            self.addDir(params)
        
        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listDownloadItems(self, cItem, nextCategory, data=None):
        printDBG("OpenSubtitles.listDownloadItems")
        if data == None:
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return
        page = cItem.get('page', 1)
        nextPage = self.getFullUrl(self.cm.ph.getSearchGroups(data, '<link[^>]+?rel="next"[^>]+?href="([^"]+?)"')[0])
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tr onclick', '</tbody>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr onclick', '</tr>')
        for item in data:
            url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?/sub/[^"]+?)"')[0]
            title  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<td', '</td>')[1].split('<a rel="nofollow"')[0])
            imdbid = self.cm.ph.getSearchGroups(item, '''/tt([0-9]+?)[^0-9]''')[0]
            lang   = self.cm.ph.getSearchGroups(item, '''class="flag\s*([^"]+?)"''')[0]
            
            descTab  = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(item, '<td', '</td>') 
            if len(tmp) > 3: fps = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(tmp[3], '<span', '</span>')[1])
            else: fps = '0'
            if len(tmp) > 4: format = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(tmp[4], '<span', '</span>')[1])
            else: format = '0'
            
            for t in tmp:
                t = t.split('<a rel="nofollow"')[0]
                t = self.cleanHtmlStr(t)
                if t != '': descTab.append(t)
            params = dict(cItem)
            params.update({'category':nextCategory, 'lang':lang, 'fps':fps, 'format':format, 'title':'[%s | %s] %s' % (lang, format, title), 'imdbid':imdbid, 'url':self.getFullUrl(url), 'desc':' | '.join(descTab)})
            self.addDir(params)
        
        if self.cm.isValidUrl(nextPage):
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
        
    def listSeasonsItems(self, cItem, nextCategory, data=None):
        printDBG("OpenSubtitles.listSeasonsItems")
        self.episodesCache = {}
        
        if data == None:
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<table id="search_results"', '</tbody>')[1]
        data = data.split('<span id="season')
        if len(data): del data[0]
        for seasonItem in data:
            seasonTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(seasonItem, '<b', '</b>')[1])
            episodesTab = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(seasonItem, '<tr itemprop="episode"', '</tr>')
            for item in tmp:
                td = self.cm.ph.getAllItemsBeetwenMarkers(item, '<td', '</td>')
                title  = self.cleanHtmlStr(td[0])
                desc   = self.cleanHtmlStr(item)
                url    = self.cm.ph.getSearchGroups(td[0], 'href="([^"]+?)"')[0]
                if url == '': continue
                imdbid = self.cm.ph.getSearchGroups(item, '''/tt([0-9]+?)[^0-9]''')[0]
                params = {'title':title, 'imdbid':imdbid, 'url':self.getFullUrl(url), 'desc':desc}
                
                numOfSubs = self.cleanHtmlStr(td[1])
                if numOfSubs == '1': params['category'] = 'list_subtitles'
                episodesTab.append(params)
            
            if len(episodesTab):
                self.episodesCache[seasonTitle] = episodesTab
                params = dict(cItem)
                params.update({'category':nextCategory, 'title':seasonTitle, 'season_key':seasonTitle})
                self.addDir(params)
            
    def listEpisodesItems(self, cItem, nextCategory):
        printDBG("OpenSubtitles.listSeasonsItems")
        
        params = dict(cItem)
        params['category'] = nextCategory
        seasonKey = cItem.get('season_key', '')
        tab = self.episodesCache.get(seasonKey, [])
        self.listsTab(tab, params)
        
    def getSubtitlesList(self, cItem, nextCategory):
        printDBG("OpenSubtitles.getSubtitlesList")
        
        url = cItem['url']
        
        if '/subtitleserve/sub/' not in url:
            sts, data = self.getPage(url)
            if not sts: return
            url = self.getFullUrl(self.cm.ph.getSearchGroups(data, 'href="([^"]*?/subtitleserve/sub/[^"]+?)"')[0])
        
        if not self.cm.isValidUrl(url): return 
        
        imdbid = cItem.get('imdbid', '')
        subId  = url.split('/')[-2]
        fps    = cItem.get('fps', 0)
        
        if not self.logedIn:
            sts, data = self.getPage(url)
            if not sts: return
            url = self.cm.ph.getSearchGroups(data, '''URL=(https?://[^"^'^\s]+?)["'\s]''')[0]
        
        if not self.cm.isValidUrl(url): return 
        
        urlParams = dict(self.defaultParams)
        tmpDIR = self.downloadAndUnpack(url, urlParams)
        if None == tmpDIR: return
        
        cItem = dict(cItem)
        cItem.update({'category':'', 'path':tmpDIR, 'fps':fps, 'imdbid':imdbid, 'sub_id':subId})
        self.listSupportedFilesFromPath(cItem, self.getSupportedFormats(all=True))
    
    def listSubsInPackedFile(self, cItem, nextCategory):
        printDBG("OpenSubtitles.listSubsInPackedFile")
        tmpFile = cItem['file_path']
        tmpDIR  = tmpFile[:-4]
        
        if not self.unpackArchive(tmpFile, tmpDIR):
            return
        
        cItem = dict(cItem)
        cItem.update({'category':nextCategory, 'path':tmpDIR})
        self.listSupportedFilesFromPath(cItem, self.getSupportedFormats(all=True))
            
    def _getFileName(self, title, lang, subId, imdbid, fps, ext):
        title = RemoveDisallowedFilenameChars(title).replace('_', '.')
        match = re.search(r'[^.]', title)
        if match: title = title[match.start():]

        fileName = "{0}_{1}_0_{2}_{3}".format(title, lang, subId, imdbid)
        if fps > 0:
            fileName += '_fps{0}'.format(fps)
        fileName = fileName + '.' + ext
        return fileName
            
    def downloadSubtitleFile(self, cItem):
        printDBG("SubsceneComProvider.downloadSubtitleFile")
        retData = {}
        title    = cItem['title']
        lang     = cItem.get('lang', '')
        subId    = cItem['sub_id']
        imdbid   = cItem['imdbid']
        inFilePath = cItem['file_path']
        ext      = cItem.get('ext', 'srt')
        fps      = cItem.get('fps', 0)
        
        outFileName = self._getFileName(title, lang, subId, imdbid, fps, ext)
        outFileName = GetSubtitlesDir(outFileName)
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(inFilePath)
        printDBG(outFileName)
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        
        if self.converFileToUtf8(inFilePath, outFileName, lang):
            retData = {'title':title, 'path':outFileName, 'lang':lang, 'imdbid':imdbid, 'sub_id':subId, 'fps':fps}
        
        return retData
    
    def handleService(self, index, refresh = 0):
        printDBG('handleService start')
        
        CBaseSubProviderClass.handleService(self, index, refresh)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.initSubProvider(self.currItem)
            self.listSearchTypes(self.currItem, 'list_languages')
        elif category == 'list_languages':
            self.listLanguages(self.currItem, 'search_subtitles')
        elif category == 'search_subtitles':
            self.searchSubtitles(self.currItem, 'list_subtitles')
        elif category == 'list_episodes':
            self.listEpisodesItems(self.currItem, 'list_download_items')
        elif category == 'list_download_items':
            self.listDownloadItems(self.currItem, 'list_subtitles')
        elif category == 'list_subtitles':
            self.getSubtitlesList(self.currItem, 'list_sub_in_packed_file')
        elif category == 'list_sub_in_packed_file':
            self.listSubsInPackedFile(self.currItem, 'list_sub_in_packed_file')
        
        CBaseSubProviderClass.endHandleService(self, index, refresh)

class IPTVSubProvider(CSubProviderBase):

    def __init__(self, params={}):
        CSubProviderBase.__init__(self, OpenSubtitles(params))
    
