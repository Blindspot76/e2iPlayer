## @file  ihost.py
#

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper, iptv_execute
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSearchHistoryHelper, GetCookieDir, printDBG, printExc
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html

from Plugins.Extensions.IPTVPlayer.components.ihost import CDisplayListItem, RetHost

import re
import urllib


class CSubItem:
    def __init__(self, path = "", \
                       name = "", \
                       lang = "", \
                       imdbid = "", \
                       subId = "" ):
        self.path = path
        self.name = name
        self.lang = lang
        self.imdbid = imdbid
        self.subId  = subId
        
## class ISubProvider
# interface base class with method used to
# communicate display layer with host
#
class ISubProvider:

    # return firs available list of item category or video or link
    def getInitList(self):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    
    # return List of item from current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible 
    # server instead of cache 
    def getListForItem(self, Index = 0, refresh = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return prev requested List of item 
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getPrevList(self, refresh = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getCurrentList(self, refresh = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return current List
    # for given Index
    def getMoreForItem(self, Index=0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    
    # return list of CSubItem objects
    # for given Index, 
    def downloadSubtitleFile(self, Index = 0,):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
'''
CSubProviderBase implements some typical methods
          from ISubProvider interface
'''
class CSubProviderBase(ISubProvider):
    def __init__( self, subProvider):
        self.subProvider = subProvider

        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = [] 
        
    def isValidIndex(self, Index, validTypes=None):
        listLen = len(self.subProvider.currList)
        if listLen <= Index or Index < 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return False
        if None != validTypes and self.converItem(self.subProvider.currList[Index]).type not in validTypes:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return False
        return True
    # end getFavouriteItem
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = []
        
        self.subProvider.handleService(self.currIndex)
        convList = self.convertList(self.subProvider.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
    
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        self.listOfprevList.append(self.subProvider.getCurrList())
        self.listOfprevItems.append(self.subProvider.getCurrItem())
        
        self.currIndex = Index
        
        self.subProvider.handleService(Index, refresh)
        convList = self.convertList(self.subProvider.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)

    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            subProviderList = self.listOfprevList.pop()
            subProviderCurrItem = self.listOfprevItems.pop()
            self.subProvider.setCurrList(subProviderList)
            self.subProvider.setCurrItem(subProviderCurrItem)
            
            convList = self.convertList(subProviderList)
            return RetHost(RetHost.OK, value = convList)
        else:
            return RetHost(RetHost.ERROR, value = [])
    
    def getCurrentList(self, refresh = 0):
        if refresh == 1:
            self.subProvider.handleService(self.currIndex, refresh)
        convList = self.convertList(self.subProvider.getCurrList())
        return RetHost(RetHost.OK, value = convList)
        
    def getMoreForItem(self, Index=0):
        self.subProvider.handleService(Index, 2)
        convList = self.convertList(self.subProvider.getCurrList())
        return RetHost(RetHost.OK, value = convList)
        
    def downloadSubtitleFile(self, Index = 0):
        if self.isValidIndex(Index, [CDisplayListItem.TYPE_SUBTITLE]):
            retData = self.subProvider.downloadSubtitleFile(self.subProvider.currList[Index])
            if 'path' in retData and 'title' in retData:
                return RetHost(RetHost.OK, value = [CSubItem(retData['path'], retData['title'], retData.get('lang', ''), retData.get('imdbid', ''), retData.get('sub_id', ''))])
        return RetHost(RetHost.ERROR, value = [])
    
    def convertList(self, cList):
        subProviderList = []
        for cItem in cList:
            subProviderItem = self.converItem(cItem)
            if None != subProviderItem: subProviderList.append(subProviderItem)
        return subProviderList
    # end convertList
    
    def converItem(self, cItem):
        type = CDisplayListItem.TYPE_UNKNOWN

        if 'category' == cItem['type']:
            type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'subtitle':
            type = CDisplayListItem.TYPE_SUBTITLE
        elif 'more' == cItem['type']:
            type = CDisplayListItem.TYPE_MORE
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        
        return CDisplayListItem(name = title,
                                description = description,
                                type = type)
    # end converItem

class CBaseSubProviderClass:
    
    def __init__(self, params={}):
        self.TMP_FILE_NAME = '.iptv_subtitles.org'
        self.sessionEx = MainSessionWrapper(mainThreadIdx=1) 
        
        proxyURL = params.get('proxyURL', '')
        useProxy = params.get('useProxy', False)
        if 'MozillaCookieJar' == params.get('cookie_type', ''):
            self.cm = common(proxyURL, useProxy, True)
        else:
            self.cm = common(proxyURL, useProxy)

        self.currList = []
        self.currItem = {}
        if '' != params.get('cookie', ''):
            self.COOKIE_FILE = GetCookieDir(params['cookie'])
        self.moreMode = False
        self.params = params
        
    def getSupportedFormats(self):
        return ['srt', 'mpl']
        
    def getMaxFileSize(self):
        return 1024 * 1024 * 5 # 5MB, max size of sub file to be download
        
    def listsTab(self, tab, cItem):
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def iptv_execute(self, cmd):
        return iptv_execute(1)(cmd)
        
    @staticmethod 
    def cleanHtmlStr(str):
        str = str.replace('<', ' <')
        str = clean_html(str)
        str = str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return CParsingHelper.removeDoubles(str, ' ').strip()

    @staticmethod 
    def getStr(v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''):  return v
        return default
            
    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        
    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

    def addDir(self, params):
        params['type'] = 'category'
        self.currList.append(params)
        return
        
    def addMore(self, params):
        params['type'] = 'more'
        self.currList.append(params)
        return
  
    def addSubtitle(self, params):
        params['type'] = 'subtitle'
        self.currList.append(params)
        return
        
    def getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif url.startswith('://'):
            url = 'http' + url
        elif url.startswith('/'):
            url = self.MAIN_URL + url[1:]
        elif 0 < len(url) and '://' not in url:
            url =  self.MAIN_URL + url
        return url
    
    def handleService(self, index, refresh=0):
        self.moreMode = False
        if 0 == refresh:
            if len(self.currList) <= index:
                return
            if -1 == index:
                self.currItem = { "name": None }
            else:
                self.currItem = self.currList[index]
        if 2 == refresh: # refresh for more items
            printDBG("CBaseSubProviderClass endHandleService index[%s]" % index)
            # remove item more and store items before and after item more
            self.beforeMoreItemList = self.currList[0:index]
            self.afterMoreItemList = self.currList[index+1:]
            self.moreMode = True
            if -1 == index:
                self.currItem = { "name": None }
            else:
                self.currItem = self.currList[index]
    
    def endHandleService(self, index, refresh):
        if 2 == refresh: # refresh for more items
            currList = self.currList
            self.currList = self.beforeMoreItemList
            for item in currList:
                if 'more' == item['type'] or (item not in self.beforeMoreItemList and item not in self.afterMoreItemList):
                    self.currList.append(item)
            self.currList.extend(self.afterMoreItemList)
            self.beforeMoreItemList = []
            self.afterMoreItemList  = []
        self.moreMode = False
        
    def imdbGetSeasons(self, imdbid, promSeason=None):
        printDBG('CBaseSubProviderClass.imdbGetSeasons imdbid[%s]' % imdbid)
        promotItem = None
        list = []
        # get all seasons
        sts, data = self.cm.getPage("http://www.imdb.com/title/tt%s/episodes" % imdbid)
        if not sts: return False, []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<select id="bySeason"', '</select>', False)[1]
        seasons = re.compile('value="([0-9]+?)"').findall(data)
        for season in seasons:
            if None != promSeason and  season == str(promSeason):
                promotItem = season
            else:
                list.append(season)
            
        if promotItem != None:
            list.insert(0, promotItem)
        
        return True, list
        
    def imdbGetEpisodesForSeason(self, imdbid, season, promEpisode=None):
        printDBG('CBaseSubProviderClass.imdbGetEpisodesForSeason imdbid[%s] season[%s]' % (imdbid, season))
        promotItem = None
        list = []
        
        # get episodes for season
        sts, data = self.cm.getPage("http://www.imdb.com/title/tt%s/episodes/_ajax?season=%s" % (imdbid, season))
        if not sts: return False, []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="list detail eplist">', '<hr>', False)[1]
        data = data.split('<div class="clear">')
        if len(data): del data[-1]
        for item in data:
            episodeTitle = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            eimdbid = self.cm.ph.getSearchGroups(item, 'data-const="tt([0-9]+?)"')[0]
            episode = self.cm.ph.getSearchGroups(item, 'content="([0-9]+?)"')[0]
            params = {"episode_title":episodeTitle, "episode":episode, "eimdbid":eimdbid}
            
            if None != promEpisode and  episode == str(promEpisode):
                promotItem = params
            else:
                list.append(params)
        
        if promotItem != None:
            list.insert(0, promotItem)
        return True, list
        
    def imdbGetMoviesByTitle(self, title):
        printDBG('CBaseSubProviderClass.imdbGetMoviesByTitle title[%s]' % (title))
        
        sts, data = self.cm.getPage("http://www.imdb.com/find?ref_=nv_sr_fn&q=%s&s=tt" % urllib.quote_plus(title))
        if not sts: return False, []
        list = []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<table class="findList">', '</table>', False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            item = item.split('<a ')
            item = '<a ' + item[2]
            if '(Video Game)' in item: continue
            imdbid = self.cm.ph.getSearchGroups(item, '/tt([0-9]+?)/')[0]
            #title = title.split('<br/>')[0]
            title = self.cleanHtmlStr(item)
            if title.endswith('-'): title = title[:-1].strip()
            list.append({'title':title, 'imdbid':imdbid})
        return True, list
        
    def getTypeFromThemoviedb(self, imdbid, title):
        if '(TV Series)' in title:
            return 'series'
        itemType = 'movie'
        try:
            # lazy import
            import base64
            try:    import json
            except Exception: import simplejson as json
            from Plugins.Extensions.IPTVPlayer.tools.iptvtools import byteify
            
            url = "https://api.themoviedb.org/3/find/tt{0}?api_key={1}&external_source=imdb_id".format(imdbid, base64.b64decode('NjMxMWY4MmQ1MjAxNDI2NWQ3NjVkMzk4MDJhYWZhYTc='))
            sts, data = self.cm.getPage(url)
            if not sts: return itemType
            data = byteify(json.loads(data))
            if len(data["tv_results"]):
                itemType = 'series'
        except Exception:
            printExc()
        return itemType
        