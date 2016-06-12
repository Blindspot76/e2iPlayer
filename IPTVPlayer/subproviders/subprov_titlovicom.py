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
        if lang in self.LANGUAGE_CACHE:
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
        ext = 'zip'
        
        urlParams = dict(self.defaultParams)
        urlParams['return_data'] = False
        try:
            fileSize = self.getMaxFileSize()
            sts, response = self.cm.getPage(url, urlParams)
            ext = response.info()['Content-Disposition'].split('.')[-1].lower()
            data = response.read(fileSize)
            response.close()
        except Exception:
            printExc()
            return
        
        if ext not in ['zip', 'rar']:
            SetIPTVPlayerLastHostError(_('Unknown file extension "%s".') % ext)
            return
            
        tmpFile = GetTmpDir( self.TMP_FILE_NAME )
        tmpFileZip = tmpFile + '.' + ext
        tmpDIR = GetTmpDir(self.TMP_DIR_NAME)
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(tmpFile)
        printDBG(tmpFileZip)
        printDBG(tmpDIR)
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        try:
            with open(tmpFileZip, 'w') as f:
                f.write(data)
        except Exception:
            printExc()
            SetIPTVPlayerLastHostError(_('Failed to write file "%s".') % tmpFileZip)
            return
        
        rmtree(tmpDIR, ignore_errors=True)
        if not mkdirs(tmpDIR):
            SetIPTVPlayerLastHostError(_('Failed to create directory "%s".') % tmpDIR)
            return
        if ext == 'zip':
            cmd = "unzip -o '{0}' -d '{1}' 2>/dev/null".format(tmpFileZip, tmpDIR)
            printDBG("cmd[%s]" % cmd)
            ret = self.iptv_execute(cmd)
            if not ret['sts'] or 0 != ret['code']:
                #mkdirs(tmpDIR)
                #rm(tmpFileZip)
                message = _('Unzip error code[%s].') % ret['code']
                if str(ret['code']) == str(127):
                    message += '\n' + _('It seems that unzip utility is not installed.')
                elif str(ret['code']) == str(9):
                    message += '\n' + _('Wrong format of zip archive.')
                SetIPTVPlayerLastHostError(message)
                return
        else:
            cmd = "unrar e -o+ -y '{0}' '{1}' 2>/dev/null".format(tmpFileZip, tmpDIR)
            printDBG("cmd[%s]" % cmd)
            ret = self.iptv_execute(cmd)
            if not ret['sts'] or 0 != ret['code']:
                #mkdirs(tmpDIR)
                #rm(tmpFileZip)
                message = _('Unrar error code[%s].') % ret['code']
                if str(ret['code']) == str(127):
                    message += '\n' + _('It seems that unrar utility is not installed.')
                elif str(ret['code']) == str(9):
                    message += '\n' + _('Wrong format of rar archive.')
                SetIPTVPlayerLastHostError(message)
                return
        
        # list files
        for file in os_listdir(tmpDIR):
            if file.lower().endswith(".srt"):
                path = os_path.join(tmpDIR, file)
                params = dict(cItem)
                params.update({'path':path, 'title':os_path.splitext(file)[0], 'imdbid':imdbid, 'sub_id':subId})
                self.addSubtitle(params)
            
    def _getFileName(self, title, lang, subId, imdbid):
        title = RemoveDisallowedFilenameChars(title).replace('_', '.')
        match = re.search(r'[^.]', title)
        if match: title = title[match.start():]

        fileName = "{0}_{1}_0_{2}_{3}".format(title, lang, subId, imdbid)
        fileName = fileName + '.srt'
        return fileName
            
    def downloadSubtitleFile(self, cItem):
        printDBG("TitlovicomProvider.downloadSubtitleFile")
        retData = {}
        title    = cItem['title']
        lang     = cItem['lang']
        subId    = cItem['sub_id']
        imdbid   = cItem['imdbid']
        path     = cItem['path']
        
        fileName = self._getFileName(title, lang, subId, imdbid)
        fileName = GetSubtitlesDir(fileName)
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(path)
        printDBG(fileName)
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            
        # detect encoding
        cmd = '%s "%s"' % (config.plugins.iptvplayer.uchardetpath.value, path)
        ret = self.iptv_execute(cmd)
        if ret['sts'] and 0 == ret['code']:
            encoding = MapUcharEncoding(ret['data'])
            if 0 != ret['code'] or 'unknown' in encoding:
                encoding = ''
            else: encoding = encoding.strip()
        
        if GetDefaultLang() == 'pl' and encoding == 'iso-8859-2':
            encoding = GetPolishSubEncoding(tmpFile)
        elif '' == encoding:
            encoding = 'utf-8'
            
        # convert file to UTF-8
        try:
            with open(path) as f:
                data = f.read()
            try:
                data = data.decode(encoding).encode('UTF-8')
                try:
                    with open(fileName, 'w') as f:
                        f.write(data)
                    retData = {'title':title, 'path':fileName, 'lang':lang, 'imdbid':imdbid, 'sub_id':subId}
                except Exception:
                    printExc()
                    SetIPTVPlayerLastHostError(_('Failed to write the file "%s".') % fileName)
            except Exception:
                printExc()
                SetIPTVPlayerLastHostError(_('Failed to convert the file "%s" to UTF-8.') % path)
        except Exception:
            printExc()
            SetIPTVPlayerLastHostError(_('Failed to open the file "%s".') % path)
        
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
    
