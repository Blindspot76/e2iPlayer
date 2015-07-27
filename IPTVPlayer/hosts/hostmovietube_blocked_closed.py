# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import base64
try:    import json
except: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.movieshdco_sortby = ConfigSelection(default = "date", choices = [("date", _("Lastest")), ("views", _("Most viewed")), ("duree", _("Longest")), ("rate", _("Top rated")), ("random", _("Tandom"))]) 

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'MovieTube'

class MovieTube(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URLS    = {'movie': 'http://www.movietube.ph/', 'tv_serie': 'http://www.tvstreaming.cc/', 'anime': 'http://www.anime1.tv/'}
    
    MAIN_CAT_TAB = [{'category':'filters',         'mode':'movie',    'title': _('Movies'),    'url':'search.php',    'icon':''},
                    {'category':'filters',         'mode':'tv_serie', 'title': _('TV Series'), 'url':'search.php', 'icon':''},
                    {'category':'filters',         'mode':'anime',    'title': _('Anime'),     'url':'search.php',     'icon':''},
                    {'category':'search',          'title': _('Search'), 'search_item':True},
                    {'category':'search_history',  'title': _('Search history')} ]
    
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'MovieTube', 'cookie':'movieshdco.cookie'})
        self.cacheFilters = []
        
    def _getFullUrl(self, url, mode):
        if url.startswith('//'):
            url = 'http:' + url
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URLS[mode] + url
        
        if self.MAIN_URLS[mode].startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def _getKeyWord(self, url):
        marker = 'watch.php?v='
        if marker not in url: return ''
        return url.split(marker)[1]
        
    def _padArg(self, arg):
        if 1 == len(arg):
            try:
                num = int(arg)
                if num < 10:
                    arg = '0%d' % num
            except: pass
        return arg
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("MovieTube.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillCacheFilters(self, url):
        printDBG("MovieTube.fillCacheFilters url[%s]" % url)
        self.cacheFilters = []
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="type_item">', '</ul>', False)
        reObj = re.compile('<a[^>]+?data="([^"]*?)"[^>]*?>([^<]+?)<')
        for item in data:
            item = item.split('<li class="current">')
            if 2 != len(item): continue
            name = self.cm.ph.getSearchGroups(item[0], 'id="([^"]+?)"')[0]
            values = reObj.findall(item[1])
            tmp = []
            for val in values:
                tmp.append({'name':name, 'value': val[0], 'title':val[1]})
            if 0 == len(tmp): continue
            self.cacheFilters.append(tmp)
            
    def getFilters(self, cItem, nextCategory):
        printDBG("MovieTube.getFilters")
        filters = cItem.get('filters', {})
        if 0 == len(filters): 
            self.fillCacheFilters( self._getFullUrl( cItem['url'], cItem['mode'] ))
            if 0 == len(self.cacheFilters):
                printExc('>>>>>>>>>>>>>>>> 0 == len(filters)')
                return
        
        filterIdx = len(filters)
        totalFilters = len(self.cacheFilters)
        if filterIdx >= totalFilters:
            printExc('>>>>>>>>>>>>>>>> filterIdx[%d] totalFilters[%d]' % (filterIdx, totalFilters))
            return 
        
        for item in self.cacheFilters[filterIdx]:
            params = dict(cItem)
            params['title'] = item['title']
            params['filters'] = dict(filters)
            params['filters'][item['name']] = item['value']
            
            if (filterIdx + 1) == totalFilters:
                params['category'] = nextCategory
                
            self.addDir(params)

    def mapItem(self, item, hNum='1'):
        printDBG("MovieTube.maMovieItem")
        url    = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
        icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
        dat    = self.cm.ph.getSearchGroups(item, 'data="([^"]+?)"')[0]
        idx    = item.find('</h%s>' % hNum)
        if idx < 0: return None
        
        title  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item[:idx], '<h%s[^>]*?>(.+?)</a>' % hNum)[0] )
        desc   = self.cleanHtmlStr(item[idx:])
        
        return {'title':title, 'url':url, 'icon':icon, 'desc':desc, 'data':dat}
    
    def listItems(self, cItem, category, keyWord=None):
        printDBG("MovieTube.listItems")
        
        page = cItem.get('page', 1)
        nextToken = cItem.get('next_token', '')
        p = dict(cItem.get('filters', {}))
        p.update({"Page":"%d" % page,"NextToken":nextToken})
        if keyWord != None:
            p["KeyWord"] = keyWord
            c = 'result'
        else:
            c = 'song' 
        
        p = json.dumps(p, sort_keys=False, separators=(',', ':'))
        post_data = {'c':c, 'a':'retrieve', 'p':p}
        
        sts, data = self.cm.getPage(self._getFullUrl('/index.php', cItem['mode']), {'header':self.AJAX_HEADER}, post_data=post_data)
        if not sts: return 
        
        idx = data.find('|')
        if idx < 0: return
        
        nextToken = data[:idx]
        data = data[idx+1:]
        
        data = data.split('</tr>')
        if len(data): del data[-1]
        
        catMap = {'movie':'video'}
        for item in data:
            tmp = self.mapItem(item)
            category = catMap.get(cItem['mode'], category)
            
            if None == tmp: continue
            params = dict(cItem)
            params.update(tmp)
            params['category'] = category
            if category == 'video':
                self.addVideo(params)
            else:
                self.addDir(params)
        
        if len(nextToken):
            params = dict(cItem)
            params.update({'title': _('Next page'), 'page':page+1, 'next_token':nextToken})
            self.addDir(params)
        
    def listSeasons(self, cItem, category):
        printDBG("MovieTube.listSeasons")
        KeyWord = self._getKeyWord(cItem['url'])
        
        p = {"KeyWord":KeyWord}
        p = json.dumps(p, sort_keys=False, separators=(',', ':'))
        post_data = {'c':'result', 'a':'getmovieallseason', 'p':p}
        
        tmpList = []
        sts, data = self.cm.getPage(self._getFullUrl('/index.php', cItem['mode']), {'header':self.AJAX_HEADER}, post_data=post_data)
        if sts:
            data = data.split('</li>')
            if len(data): del data[-1]
            for item in data:
                params = self.mapItem(item, '3')
                if None == params: continue
                params['category'] = category
                tmpList.append( params )
        
        if 1 >= len(tmpList):
            params = dict(cItem)
            #params.update( tmpList[0] )
            self.listEpisodes(params)
        else:
            params = dict(cItem)
            params['category'] = category
            self.listsTab(tmpList, params)
            
    
    def listEpisodes(self, cItem):
        printDBG("MovieTube.listEpisodes")

        KeyWord = self._getKeyWord(cItem['url'])
        Episode = self._padArg( cItem.get('episode', '1') )
        Part    = self._padArg( cItem.get('part', '1') )
        
        p = {"KeyWord":KeyWord, "Episode":Episode, "Part":Part}
        
        p = json.dumps(p, sort_keys=False, separators=(',', ':'))
        post_data = {'c':'result', 'a':'getplaylistinfo', 'p':p}
        
        sts, data = self.cm.getPage(self._getFullUrl('/index.php', cItem['mode']), {'header':self.AJAX_HEADER}, post_data=post_data)
        if not sts: return 
        
        idx = data.find('<a ')
        if idx < 0: return
        
        data = data[idx:]
        data = data.split('</a>')
        if len(data): del data[-1]
        
        baseTitle = self.cm.ph.getSearchGroups(cItem['title'], '^(.+?) EP[0-9]+?$')[0]
        if '' == baseTitle: baseTitle = self.cm.ph.getSearchGroups(cItem['title'], '^(.+?) Full$')[0]
        if '' == baseTitle: baseTitle = cItem['title']
        
        for item in data:
            title  = self.cleanHtmlStr( item )
            episode =  self._padArg( self.cm.ph.getSearchGroups(item, 'data="([^"]+?)"')[0] )
            updateuntil =  self.cm.ph.getSearchGroups(item, 'updateuntil="([^"]+?)"')[0]
            
            params = dict(cItem)
            params.update( {'title': baseTitle + ' ' + title, 'episode':episode, 'updateuntil':updateuntil} )
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("MovieTube.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        params = dict(cItem)
        params['mode'] = searchType
        self.listItems(params, 'list_seasons', searchPattern)
    
    '''
    def getArticleContent(self, cItem):
        printDBG("MovieTube.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return retTab
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<table id="imdbinfo">', '</table>', False)
        if not sts: return retTab
        
        tmp = data.split('</tr>')
        if len(tmp) < 2: return retTab
        
        title = self.cleanHtmlStr(tmp[0])
        if '' == title: icon = self.cm.ph.getSearchGroups(tmp[1], 'alt="([^"]+?)"')[0]
        icon  = self.cm.ph.getSearchGroups(tmp[1], 'src="([^"]+?)"')[0]
        desc  = self.cm.ph.getDataBeetwenMarkers(tmp[1], '<b>Plot:</b>', '</td>', False)[1]
        
        otherInfo = {}
        tmpTab = [{'mark':'<b>Rating:</b>',   'key':'rating'},
                  {'mark':'<b>Director:</b>', 'key':'director'},
                  {'mark':'<b>Writer:</b>',   'key':'writer'},
                  {'mark':'<b>Stars:</b>',    'key':'stars'},
                  {'mark':'<b>Runtime:</b>',  'key':'duration'},
                  {'mark':'<b>Rated:</b>',    'key':'rated'},
                  {'mark':'<b>Genre:</b>',    'key':'genre'},
                  {'mark':'<b>Released:</b>', 'key':'released'},
        ]
        for item in tmpTab:
            val = self.cm.ph.getDataBeetwenMarkers(tmp[1], item['mark'], '</td>', False)[1]
            if '' != val: otherInfo[item['key']] =  self.cleanHtmlStr(val)
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':otherInfo}]
    '''
    
    def getLinksForVideo(self, cItem):
        printDBG("MovieTube.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        KeyWord = self._getKeyWord(cItem['url'])
        p = {"KeyWord":KeyWord}
        
        if cItem['mode'] == 'movie':
            a = 'getmoviealternative'
        else:
            a = 'getpartlistinfo'
            p["Episode"] = self._padArg( cItem.get('episode', '1') )
            p["Part"]    = self._padArg( cItem.get('part', '1') )
        
        strP = json.dumps(p, sort_keys=False, separators=(',', ':'))
        post_data = {'c':'result', 'a':a, 'p':strP}
        
        sts, data = self.cm.getPage(self._getFullUrl('/index.php', cItem['mode']), {'header':self.AJAX_HEADER}, post_data=post_data)
        if not sts: return urlTab
        
        idx = data.find('<a ')
        if idx < 0: return urlTab
        data = data[idx:]
        data = data.split('</a>')
        if len(data): del data[-1]
        
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            newP  = dict(p)
            KeyWord = self._getKeyWord(url)
            if '' != KeyWord: newP['KeyWord'] = KeyWord 
            part  = self.cm.ph.getSearchGroups(item, 'data="([^"]+?)"')[0]
            if '' != part: newP['part'] = self._padArg( part )
            newP = json.dumps(newP, sort_keys=False, separators=(',', ':'))
            urlData = '|'.join([url, cItem['mode'], newP])
            name  = self.cm.ph.getSearchGroups(item, 'src="[^"]+?/([^./]+?)\.png"')[0]
            if name == '0000000008400000': name = 'google'
            name += ' ' + self.cleanHtmlStr( item )
            urlTab.append({'name':name, 'url':urlData, 'need_resolve':1})
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("MovieTube.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        urlData = baseUrl.split('|')
        if 3 != len(urlData): return urlTab
        url  = urlData[0]
        mode = urlData[1]
        p    = urlData[2]
        
        post_data = {'c':'result', 'a':'getplayerinfo', 'p':p}
        sts, data = self.cm.getPage(self._getFullUrl('/index.php', mode), {'header':self.AJAX_HEADER}, post_data=post_data)
        if not sts: return urlTab
        
        # google doc
        tmp = re.compile('<source ([^>]*?)>').findall(data)
        for item in tmp:
            type = self.cm.ph.getSearchGroups(item, 'type="([^"]+?)"')[0]
            if 'video' not in type: continue 
            url  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            name = type + ' ' + self.cm.ph.getSearchGroups(item, 'data-res="([^"]+?)"')[0]
            urlTab.append({'name':name, 'url':url})
        if len(urlTab): return urlTab
        tmp = None
        
        videoUrl  = self.cm.ph.getSearchGroups(data, '<iframe [^>]*?src="([^"]+?)"')[0]
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        #return json.dumps(cItem['url'])
        params = {}
        params['url']     = cItem['url']
        params['mode']    = cItem['mode']
        params['episode'] = cItem.get('episode', '')
        params['part']    = cItem.get('part', '')
        return  json.dumps( params )
        
    def getLinksForFavourite(self, fav_data):
        try:
            params = byteify( json.loads(fav_data) )
            return self.getLinksForVideo(params)
        except:
            printExc()
        return []

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        filters  = self.currItem.get("filters", {})
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'filters':
            self.getFilters(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_seasons')
        elif category == 'list_seasons':
            self.listSeasons(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
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
        CHostBase.__init__(self, MovieTube(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('movietubelogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)

    '''
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
        return RetHost(RetHost.OK, value = retlist)
    '''
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Movies"),    "movie"))
        searchTypesOptions.append((_("TV Series"), "tv_serie"))
        searchTypesOptions.append((_("Anime"),     "anime"))
        
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None

        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
        elif 'more' == cItem['type']:
            type = CDisplayListItem.TYPE_MORE
        elif 'audio' == cItem['type']:
            type = CDisplayListItem.TYPE_AUDIO
            
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO]:
            url = cItem.get('url', '')
            if '' != url:
                hostLinks.append(CUrlItem("Link", url, 1))
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
