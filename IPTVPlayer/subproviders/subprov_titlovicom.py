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
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import hex_md5
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
from os import listdir as os_listdir, path as os_path
try:    import json
except: import simplejson as json
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

class TitlovicomProvider(CBaseSubProviderClass): 
    
    def __init__(self, params={}):
        params['cookie'] = 'titlovicom.cookie'
        CBaseSubProviderClass.__init__(self, params)
        
        self.LANGUAGE_CACHE = ['rs', 'hr', 'ba' , 'mk', 'si', 'en']
        self.USER_AGENT    = 'Mozilla/5.0'
        self.HTTP_HEADER   = {'User-Agent':self.USER_AGENT, 'Referer':self.getMainUrl(), 'Accept':'gzip'}
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.dInfo = params['discover_info']
        
    def getMainUrl(self):
        lang = GetDefaultLang()
        if lang not in self.LANGUAGE_CACHE:
            lang = 'en'
        if lang == 'rs':
            return 'http://titlovi.com/'
        return 'http://%s.titlovi.com/' % lang
        
    def getMoviesTitles(self, cItem, nextCategory):
        printDBG("TitlovicomProvider.getMoviesTitles")
        sts, tab = self.imdbGetMoviesByTitle(self.params['confirmed_title'])
        if not sts: return
        printDBG(tab)
        for item in tab:
            params = dict(cItem)
            params.update(item) # item = {'title', 'imdbid'}
            params.update({'category':nextCategory})
            self.addDir(params)
                
    def getType(self, cItem):
        printDBG("TitlovicomProvider.getType")
        imdbid = cItem['imdbid']
        title  = cItem['title']
        type = self.getTypeFromThemoviedb(imdbid, title)
        if type == 'series':
            promSeason = self.dInfo.get('season')
            sts, tab = self.imdbGetSeasons(imdbid, promSeason)
            if not sts: return
            for item in tab:
                params = dict(cItem)
                params.update({'category':'get_episodes', 'item_title':cItem['title'], 'season':item, 'title':_('Season %s') % item})
                self.addDir(params)
        elif type == 'movie':
            self.getLanguages(cItem, 'get_search')
            
    def getEpisodes(self, cItem, nextCategory):
        printDBG("TitlovicomProvider.getEpisodes")
        imdbid    = cItem['imdbid']
        itemTitle = cItem['item_title']
        season    = cItem['season']
        
        promEpisode = self.dInfo.get('episode')
        sts, tab = self.imdbGetEpisodesForSeason(imdbid, season, promEpisode)
        if not sts: return
        for item in tab:
            params = dict(cItem)
            params.update(item) # item = "episode_title", "episode", "eimdbid"
            title = 's{0}e{1} {2}'.format(str(season).zfill(2), str(item['episode']).zfill(2), item['episode_title'])
            params.update({'category':nextCategory, 'title':title})
            self.addDir(params)
        
    def getLanguages(self, cItem, nextCategory):
        printDBG("OpenSubOrgProvider.getEpisodes")
        
        url = self.getFullUrl('search.aspx')
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<li class="field-language">', '</select>', False)[1]
        data = re.compile('<option[^>]+?value="([^"]+?)"[^>]*>([^<]+?)</option>').findall(data)
        
        if len(data):
            params = dict(cItem)
            params.update({'title':_('All'), 'search_lang':'null'})
            params.update({'category':nextCategory})
            self.addDir(params)
        
        for item in data:
            params = dict(cItem)
            params.update({'title':item[1], 'search_lang':item[0]})
            params.update({'category':nextCategory})
            self.addDir(params)
        
    def getSearchList(self, cItem, nextCategory):
        printDBG("TitlovicomProvider.getSearchList")
        
        year = cItem.get('year', '')
        if '' == year: year = -1
        
        mt = '-1'
        if 'season' in cItem and 'episode' in cItem:
            mt = '2'
            year = -1
            
        title = self.imdbGetOrginalByTitle(cItem['imdbid'])[1].get('title', cItem['base_title'])
        url = self.getFullUrl('search.aspx?keyword=%s&language=%s&uploader=&mt=%s&season=%s&episode=%s&year=%s&cd=-1' % \
        (urllib.quote_plus(title), cItem['search_lang'], mt, cItem.get('season', -1), cItem.get('episode', -1), year))
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<li class="listing">', '<!-- Content -->', False)[1]
        data = data.split('clearfix">')
        if len(data): del data[0]
        for item in data:
            descTab = []
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            if url == '': continue
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<h4', '</h4>')[1]
            lang   = self.cm.ph.getSearchGroups(item, '"lang ([a-z]{2})"')[0]
            
            # lang name
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<span class="lang', '</span>')[1])
            if desc != '': descTab.append(desc)
            
            # release
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<span class="release">', '</span>')[1])
            if desc != '': descTab.append(desc)
            
            desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '</ul>', '</li>')[1])
            if desc != '': descTab.append(desc)
            
            params = dict(cItem)
            params.update({'category':nextCategory, 'url':url, 'title':self.cleanHtmlStr(title), 'lang':lang, 'desc':'[/br]'.join(descTab)})
            self.addDir(params)
            
    def getSubtitlesList(self, cItem):
        printDBG("TitlovicomProvider.getSubtitlesList")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        imdbid = self.cm.ph.getSearchGroups(data, '/title/(tt[0-9]+?)[^0-9]')[0]
        subId  = self.cm.ph.getSearchGroups(data, 'mediaid=([0-9]+?)[^0-9]')[0]
        url    = self.cm.ph.getSearchGroups(data, 'href="([^"]+?/downloads/[^"]+?mediaid=[^"]+?)"')[0]
        
        try: fps = float(self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<li class="fps">', '</li>')[1].upper().replace('FPS', '')))
        except Exception:
            fps = 0
            printExc()

        urlParams = dict(self.defaultParams)
        tmpDIR = self.downloadAndUnpack(url, urlParams)
        if None == tmpDIR: return
        
        cItem = dict(cItem)
        cItem.update({'category':'', 'path':tmpDIR, 'fps':fps, 'imdbid':imdbid, 'sub_id':subId})
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
        lang     = cItem['lang']
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
            self.getMoviesTitles({'name':'category'}, 'get_type')
        elif category == 'get_type':
            # take actions depending on the type
            self.getType(self.currItem)
        elif category == 'get_episodes':
            self.getEpisodes(self.currItem, 'get_languages')
        elif category == 'get_languages':
            self.getLanguages(self.currItem, 'get_search')
        elif category == 'get_search':
            self.getSearchList(self.currItem, 'get_subtitles')
        elif category == 'get_subtitles':
            self.getSubtitlesList(self.currItem)
        
        CBaseSubProviderClass.endHandleService(self, index, refresh)

class IPTVSubProvider(CSubProviderBase):

    def __init__(self, params={}):
        CSubProviderBase.__init__(self, TitlovicomProvider(params))
    
