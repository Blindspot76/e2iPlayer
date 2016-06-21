# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CDisplayListItem, RetHost
from Plugins.Extensions.IPTVPlayer.components.isubprovider import CSubProviderBase, CBaseSubProviderClass

from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetDefaultLang, GetCookieDir, byteify, \
                                                          RemoveDisallowedFilenameChars, GetSubtitlesDir, GetTmpDir, rm, \
                                                          MapUcharEncoding, GetPolishSubEncoding
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

class Napisy24plProvider(CBaseSubProviderClass): 
    
    def __init__(self, params={}):
        self.MAIN_URL      = 'http://napisy24.pl/'
        self.USER_AGENT    = 'DMnapi 13.1.30'
        self.HTTP_HEADER   = {'User-Agent':self.USER_AGENT, 'Referer':self.MAIN_URL, 'Accept':'gzip'}#, 'Accept-Language':'pl'}

        params['cookie'] = 'napisy24pl.cookie'
        CBaseSubProviderClass.__init__(self, params)
        
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.dInfo = params['discover_info']
        
        self.cacheSeasons = {}
        
    def sortSubtitlesByDurationMatch(self):
        # we need duration to sort
        movieDurationSec = self.params.get('duration_sec', 0)
        if movieDurationSec <= 0: return 
    
        # get only subtitles items from current list
        hasDuration = False
        subList = []
        for item in self.currList:
            if 'subtitle' == item.get('type', ''):
                subList.append(item)
                if 'duration_sec' in item: hasDuration = True

        # if there is no subtitle with duration available 
        # we will skip sort
        if not hasDuration: return
        subList.sort(key=lambda item: abs(item.get('duration_sec', 0) - movieDurationSec))
        
        for idx in range(len(self.currList)):
            if 'subtitle' == self.currList[idx].get('type', ''):
                self.currList[idx] = subList.pop(0)
        
    def getMoviesList(self, cItem, nextCategoryMovie):
        printDBG("Napisy24plProvider.getMoviesList")
        page = cItem.get('page', 1)
        title = urllib.quote_plus( self.params['confirmed_title'] )
        url = self.getFullUrl('szukaj?page={0}&lang=0&search={1}&typ=0'.format(page, title))
        
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        if 'title="Next"' in data:
            nextPage = True
        else: nextPage = False
        
        # series items
        if page == 1:
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, 'Znalezione Seriale:', '</section>')
            if sts:
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<div class="tbl">', '<div class="clear">')
                for item in tmp:
                    imdbid = self.cm.ph.getSearchGroups(item, 'data-imdb="(tt[0-9]+?)"')[0]
                    url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
                    title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h2>')[1] )
                    if title == '': title = self.cleanHtmlStr( urllib.unquote_plus( url.split('/')[-1] ).title() )
                    desc   = item.split('</h2>')[-1]
                    
                    params = dict(cItem)
                    params.update({'sub_item_type':'series', 'category':nextCategoryMovie, 'title':title, 'url': self.getFullUrl(url), 'imdbid':imdbid, 'desc':self.cleanHtmlStr(desc)})
                    self.addDir(params)
        
        #subtitles items
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="tbl" data-napis-id', '<div class="footertext">')
        for item in data:
            imdbid = self.cm.ph.getSearchGroups(item, 'data-imdb="(tt[0-9]+?)"')[0]
            subId  = self.cm.ph.getSearchGroups(item, 'napisId=([0-9]+?)[^0-9]')[0]
            title  = self.cm.ph.getDataBeetwenMarkers(item, '<h2', '</h3>')[1]
            lang   =self.cm.ph.getSearchGroups(item, 'flags/(..)\.png')[0]
            
            descTab = []
            columnsTitles = self.cm.ph.getDataBeetwenMarkers(item, '<div class="infoColumn1">', '</div>', False)[1].split('<br>')
            columnsValues = self.cm.ph.getDataBeetwenMarkers(item, '<div class="infoColumn2">', '</div>', False)[1].split('<br>')
            if len(columnsTitles) > 0 and len(columnsTitles) == len(columnsValues):
                for idx in range(len(columnsTitles)):
                    descTab.append("%s: %s" % (columnsTitles[idx], columnsValues[idx]))
            desc = '[/br]'.join(descTab)
            params = dict(cItem)
            params.update({'title':self.cleanHtmlStr(title), 'sub_id':subId, 'lang':lang, 'imdbid':imdbid, 'desc':self.cleanHtmlStr(desc)})
            self.addSubtitle(params)
                
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Next page'), 'page':page+1})
            self.addDir(params)
            
    def getSeasons(self, cItem, nextCategory):
        printDBG("Napisy24plProvider.getEpisodes")
        url = cItem['url']
        self.cacheSeasons = {}
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        titleN24 = self.cm.ph.getSearchGroups(data, 'titleN24="([^"]+?)"')[0]
        imdbid = self.cm.ph.getSearchGroups(data, 'imdbN24="([^"]+?)"')[0]
        
        tab = []
        promItem = None
        promSeason = str(self.dInfo.get('season'))
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'class="table-layout sezon', '</table>')
        for item in data:
            season = self.cm.ph.getSearchGroups(item, 'sezon([0-9]+?)[^0-9]')[0]
            tmp = self.cm.ph.getDataBeetwenMarkers(item, '<tbody>', '</tbody>', False)[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<tr ', '</tr>')
            eTab = []
            
            promEpisode = str(self.dInfo.get('episode'))
            promEpisodeItem = None
            for tmpItem in tmp:
                dId = self.cm.ph.getSearchGroups(tmpItem, 'id="([^"]+?)"')[0]
                dNid = self.cm.ph.getSearchGroups(tmpItem, 'nid="([^"]+?)"')[0]
                dSeazon = self.cm.ph.getSearchGroups(tmpItem, 'data-sezon="([0-9]+?)"')[0]
                dEpizod = self.cm.ph.getSearchGroups(tmpItem, 'data-epizod="([0-9]+?)"')[0]
                if dNid == '': continue
                if dSeazon not in self.cacheSeasons:
                    self.cacheSeasons[season] = []
                title = self.cleanHtmlStr(tmpItem)
                eParams = {'title':title, 'd_id':dId, 'd_nid':dNid, 'd_seazon':dSeazon, 'd_episode':dEpizod}
                if promEpisode != dEpizod:
                    self.cacheSeasons[season].append(eParams)
                else:
                    promEpisodeItem = eParams
            if None != promEpisodeItem:
                self.cacheSeasons[season].insert(0, promEpisodeItem)
            
            params = {'season':season, 'serie_title':titleN24, 'imdbid':imdbid}
            if promSeason == season:
                promItem = params
            else:
                tab.append(params)
        
        if None != promItem:
            tab.insert(0, promItem)
        
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params.update({'category':nextCategory, 'title':_('Season %s') % item['season']})
            self.addDir(params)
    
    def getEpisodes(self, cItem, nextCategory):
        printDBG("Napisy24plProvider.getEpisodes")
        season = cItem['season']
        episodesTab = self.cacheSeasons.get(str(season), [])
        for item in episodesTab:
            params = dict(cItem)
            params.update(item)
            params.update({'category':nextCategory})
            self.addDir(params)
            
    def getSubtitles(self, cItem):
        printDBG("Napisy24plProvider.getSubtitles")
        post_data = {'serial':cItem['serie_title'], 'sezon':cItem['d_seazon'], 'epizod':cItem['d_episode'], 'nid':cItem['d_nid']}
        
        url = self.getFullUrl('run/pages/serial_napis.php')
        sts, data = self.cm.getPage(url, self.defaultParams, post_data)
        if not sts: return
        
        try:
            data = byteify(json.loads(data))
            for item in data:
                subId  = str(item['napisid'])
                title  = self.cm.ph.getDataBeetwenMarkers(item['table'], '<h6', '</h6>')[1]
                lang   = 'pl'
                
                descTab = []
                columnsTitles = self.cm.ph.getDataBeetwenMarkers(item['table'], '<div class="infoColumn1tab">', '</div>', False)[1].split('<br>')
                columnsValues = self.cm.ph.getDataBeetwenMarkers(item['table'], '<div class="infoColumn2tab">', '</div>', False)[1].split('<br>')
                if len(columnsTitles) > 0 and len(columnsTitles) == len(columnsValues):
                    for idx in range(len(columnsTitles)):
                        descTab.append("%s: %s" % (columnsTitles[idx], columnsValues[idx]))
                desc = '[/br]'.join(descTab)
                durationSecTab = self.cm.ph.getSearchGroups(desc, '[^0-9]([0-9]{2}):([0-9]{2}):([0-9]{2})[^0-9]', 3)
                if '' not in durationSecTab:
                    durationSec = int(durationSecTab[0]) * 3600 + int(durationSecTab[1]) * 60 + int(durationSecTab[2])
                else: durationSec = 0
                printDBG("DUTATION >>>>>>>>>>>>>>>>>>>>>>> [%s]s" % durationSec)
                params = dict(cItem)
                params.update({'title':self.cleanHtmlStr(title), 'duration_sec':durationSec, 'sub_id':subId, 'lang':lang, 'desc':self.cleanHtmlStr(desc)})
                self.addSubtitle(params)
        except Exception:
            printExc()
        self.sortSubtitlesByDurationMatch()
            
    def _getFileName(self, title, lang, subId, imdbid):
        title = RemoveDisallowedFilenameChars(title).replace('_', '.')
        match = re.search(r'[^.]', title)
        if match: title = title[match.start():]

        fileName = "{0}_{1}_0_{2}_{3}".format(title, lang, subId, imdbid)
        fileName = fileName + '.srt'
        return fileName
            
    def downloadSubtitleFile(self, cItem):
        printDBG("Napisy24plProvider.downloadSubtitleFile")
        retData = {}
        title    = cItem['title']
        lang     = cItem['lang']
        subId    = cItem['sub_id']
        imdbid   = cItem['imdbid']
        fileName = self._getFileName(title, lang, subId, imdbid)
        fileName = GetSubtitlesDir(fileName)
        
        url = 'http://napisy24.pl/run/pages/download.php?napisId={0}&typ=sru'.format(subId)
        tmpFile = GetTmpDir( self.TMP_FILE_NAME )
        tmpFileZip = tmpFile + '.zip'
        
        urlParams = dict(self.defaultParams)
        urlParams['return_data'] = False
        
        try:
            fileSize = self.getMaxFileSize()
            sts, response = self.cm.getPage(url, urlParams)
            data = response.read(fileSize)
            response.close()
        except Exception:
            printExc()
            sts = False
                    
        if not sts:
            SetIPTVPlayerLastHostError(_('Failed to download subtitle.'))
            return retData
        
        try:
            with open(tmpFileZip, 'w') as f:
                f.write(data)
        except Exception:
            printExc()
            SetIPTVPlayerLastHostError(_('Failed to write file "%s".') % tmpFileZip)
            return retData
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(tmpFile)
        printDBG(tmpFileZip)
        printDBG(fileName)
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        def __cleanFiles(all=False):
            if all: rm(fileName)
            rm(tmpFile)
            rm(tmpFileZip)
        
        cmd = "unzip -po '{0}' -x Napisy24.pl.url > '{1}' 2>/dev/null".format(tmpFileZip, tmpFile)
        ret = self.iptv_execute(cmd)
        if not ret['sts'] or 0 != ret['code']:
            __cleanFiles()
            message = _('Unzip error code[%s].') % ret['code']
            if str(ret['code']) == str(127):
                message += '\n' + _('It seems that unzip utility is not installed.')
            elif str(ret['code']) == str(9):
                message += '\n' + _('Wrong format of zip archive.')
            SetIPTVPlayerLastHostError(message)
            return retData
            
        # detect encoding
        cmd = '%s "%s"' % (config.plugins.iptvplayer.uchardetpath.value, tmpFile)
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
            with open(tmpFile) as f:
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
                SetIPTVPlayerLastHostError(_('Failed to convert the file "%s" to UTF-8.') % tmpFile)
        except Exception: 
            printExc()
            SetIPTVPlayerLastHostError(_('Failed to open the file "%s".') % tmpFile)
        
        __cleanFiles()
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
            self.getMoviesList({'name':'category', 'category':'get_movies_list'}, 'get_seasons')
        elif category == 'get_movies_list':
            self.getMoviesList(self.currItem, 'get_seasons')
        elif category == 'get_seasons':
            # take actions depending on the type
            self.getSeasons(self.currItem, 'get_episodes')
        elif category == 'get_episodes':
            self.getEpisodes(self.currItem, 'get_subtitles')
        elif category == 'get_subtitles':
            self.getSubtitles(self.currItem)
        
        CBaseSubProviderClass.endHandleService(self, index, refresh)

class IPTVSubProvider(CSubProviderBase):

    def __init__(self, params={}):
        CSubProviderBase.__init__(self, Napisy24plProvider(params))
    
