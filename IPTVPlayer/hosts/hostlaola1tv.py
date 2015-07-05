# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify, CSelOneLink
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta
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
config.plugins.iptvplayer.laola1tv_defquality  = ConfigSelection(default = "1000000", choices = [("0", _("The worst")), ("500000", _("Low")), ("1000000", _("Mid")), ("1500000", _("High")), ("9000000", _("The best"))]) 
config.plugins.iptvplayer.laola1tv_onelink     = ConfigYesNo(default = False)
config.plugins.iptvplayer.laola1tv_portal      = ConfigSelection(default = "int", choices = [("at", "AT"), ("de", "DE"), ("int", "INT")]) 
config.plugins.iptvplayer.laola1tv_language    = ConfigSelection(default = "en", choices = [("en", _("English")), ("de", _("Deutsch"))]) 
config.plugins.iptvplayer.laola1tv_myip1       = ConfigText(default = "146.0.32.8", fixed_size = False)
config.plugins.iptvplayer.laola1tv_myip2       = ConfigText(default = "85.128.142.29", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Video default quality:"), config.plugins.iptvplayer.laola1tv_defquality))
    optionList.append(getConfigListEntry(_("Use default quality:"), config.plugins.iptvplayer.laola1tv_onelink))
    optionList.append(getConfigListEntry(_("Portal:"), config.plugins.iptvplayer.laola1tv_portal))
    optionList.append(getConfigListEntry(_("Language:"), config.plugins.iptvplayer.laola1tv_language))
    optionList.append(getConfigListEntry(_("Alternative geolocation IP 1:"), config.plugins.iptvplayer.laola1tv_myip1))
    optionList.append(getConfigListEntry(_("Alternative geolocation IP 2:"), config.plugins.iptvplayer.laola1tv_myip2))
    return optionList
###################################################


def gettytul():
    return 'laola1.tv'

class Laola1TV(CBaseHostClass):
    HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'}
    MAIN_URL    = 'http://laola1.tv/'
    
    #'http://www.laola1.tv/img/laola1_logo.png'
    #MAIN_CAT_TAB = [{'category':'search',             'title': _('Search'), 'search_item':True},
    #                {'category':'search_history',     'title': _('Search history')} ]
    MAIN_CAT_TAB = []
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Laola1TV', 'cookie':'Laola1TV.cookie'})
        self.mainCache = {}
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        
        if self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def getPage(self, url, params={}, post_data=None):
        return self.cm.getPage(url, params, post_data)
        
    def getMainUrl(self):
        return (self.MAIN_URL + '{language}-{portal}/').format(language=config.plugins.iptvplayer.laola1tv_language.value, portal=config.plugins.iptvplayer.laola1tv_portal.value)

    def listsTab(self, tab, cItem, type=''):
        printDBG("Laola1TV.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == '':
                type = item['category']
            if type == 'video':
                self.addVideo(params)
            else: 
                self.addDir(params)
            
    def listMainMenu(self):
        sts, data = self.getPage( self.getMainUrl() + 'home/0.html' )
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul>', '<li class="heading">More</li>', False)[1]
        data = data.split('<li class="heading">')
        if len(data): del data[0]
        
        # remove first one because it is user sub
        if len(data): del data[0]
        self.mainCache = {}
        
        for cat in data:
            m1 = '</li>'
            idx = cat.find(m1)
            if idx < 0: continue
            catTitle = self.cleanHtmlStr( cat[:idx] )
            
            tmpTab = []
            if '<li class=" has_sub">' not in cat:
                cat = cat[idx+len(m1):]
                cat = cat.split('</li>')
                if len(cat): del cat[-1]
                for item in cat:
                    url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
                    icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
                    title  = self.cleanHtmlStr(item)
                    category = ''
                    if '/ehftv/' in url: continue
                    if '/video/' in url:
                        category = 'video'
                    elif '/home/' in url:
                        category = 'videos_list'
                    elif '/calendar/' in url:
                        category = 'calendar'
                    elif '"noparent"' in item:
                        category = 'videos_list'
                    else:
                        category = 'sub_category'
                    if '' != title and '' != url:
                        tmpTab.append({'title':title, 'icon':icon, 'url':self._getFullUrl(url), 'category':category})
            else:
                subCat = cat.split('<li class=" has_sub">')
                if len(subCat): del subCat[0]
                for sub in subCat:
                    m1 = '</a>'
                    idx = sub.find(m1)
                    if idx < 0: continue
                    subCatTitle = self.cleanHtmlStr( sub[:idx] )
                    subCatIcon  = self.cm.ph.getSearchGroups(sub[:idx], 'src="([^"]+?)"')[0] 
                    subItems = sub[idx+len(m1):]
                    subItems = sub.split('</li>')
                    if len(subItems): del subItems[-1]
                    printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> subCatTitle[%s]' % subCatTitle)
                    tmpTab2 = []
                    for item in subItems:
                        url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
                        icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
                        title  = self.cleanHtmlStr(item)
                        if '' != title and '' != url:
                            tmpTab2.append({'title':title, 'icon':icon, 'url':self._getFullUrl(url), 'category':'videos_list'})
                    if len(tmpTab2):
                        self.mainCache[catTitle + '_' + subCatTitle] = tmpTab2
                        tmpTab.append({'title':subCatTitle, 'cat_id':catTitle + '_' + subCatTitle, 'url':'', 'category':'main'}) #, 'icon':subCatIcon
            if len(tmpTab):
                self.mainCache[catTitle] = tmpTab
                self.addDir({'title':catTitle, 'cat_id':catTitle, 'category':'main'})

            printDBG(catTitle)
            
    def listFromCache(self, cItem):
        printDBG("Laola1TV.listFromCache")
        data = self.mainCache.get(cItem['cat_id'], [])
        mainItem = dict(cItem)
        self.listsTab(data, cItem)
        
    def listCalendary(self, cItem):
        printDBG("Laola1TV.listCalendary")
        sts, data = self.getPage(cItem['url'])
        if not sts: return 
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="liveprogramm_full"', '<div class="crane_footer has_rightbar inline_footer">', False)[1]
        
        data = data.split('<div class="stream ')
        if len(data): del data[0]
        nextPage = False
        for item in data:
            idx   = item.find('>')
            if idx < 0: continue 
            item  = item[idx+1:]
            tmp   = item.split('<div class="streamdesc ')
            title = self.cleanHtmlStr( tmp[0] )
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(tmp[0], 'src="([^"]+?)"')[0] )
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(tmp[0], 'href="([^"]+?)"')[0] )
            
            desc = ''
            if len(tmp) > 1:
                idx   = tmp[1].find('>')
                if idx > -1:
                    desc = self.cleanHtmlStr( tmp[1][idx+1:] )
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'desc':desc, 'icon':icon})
            nextPage = True
            self.addVideo(params)

    def listVideos(self, cItem):
        printDBG("Laola1TV.listVideos")
        paramsKeys = ['stageid', 'call', 'page', 'filterpage', 'startvids', 'htag']
        vidParams = {}
        if 'page' not in cItem:
            sts, data = self.getPage(cItem['url'])
            if not sts: return 
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="stage_frame active"', '>', False)[1]
            try:
                for key in paramsKeys:
                    vidParams[key] = self.cm.ph.getSearchGroups(data, 'data-%s[ ]*?=[ ]*?"([^"]+?)"' % key)[0]
                vidParams['page'] = int(vidParams['page'])
            except:
                printExc()
                return
            cItem = dict( cItem )
            cItem.update( vidParams )
        else:
            try:
                for key in paramsKeys:
                    vidParams[key] = cItem[key]
            except:
                printExc()
                return
        
        url = 'http://www.laola1.tv/nourish.php?stageid={0}&newpage={1}&filterpage={2}&startvids={3}&anzahlblock=12&filter1=0&filter2=0&filter3=0&customdata=&lang={4}&geo={5}'.format(vidParams['stageid'], vidParams['page'], vidParams['filterpage'], vidParams['startvids'], config.plugins.iptvplayer.laola1tv_language.value, config.plugins.iptvplayer.laola1tv_portal.value) 
        sts, data = self.getPage(url)
        if not sts: return 
        
        data = data.split('<div class="teaser">')
        if len(data): del data[0]
        nextPage = False
        for item in data:
            cat   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span class="category">', '<', False)[1] )
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2>', '</h2>', False)[1] )
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            date = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span class="date">', '<', False)[1] )
            mediatype = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span class="mediatype">', '<', False)[1] )
            
            desc = ', '.join([cat, date, mediatype])
            params = dict(cItem)
            params.update({'title':title, 'url':url, 'desc':desc, 'icon':icon})
            nextPage = True
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':vidParams['page']+1})
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Laola1TV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        if searchType == 'live':
            pass
        else:
            params = dict(cItem)
            params['url'] = self.SRCH_MOVIES_URL + urllib.quote_plus(searchPattern)
            self.listMovies(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("Laola1TV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return urlTab
        error = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(data, '<div class="notready">', '<div', False)[1] )
        if '' != error: SetIPTVPlayerLastHostError(error)
        
        data = self.cm.ph.getSearchGroups(data, 'class="main_tv_player"[^>]+?src="([^"]+?)"')[0]
        vidUrl = self._getFullUrl( data )
        
        sts, data = self.getPage(vidUrl)
        if not sts: return urlTab
        
        label        = self.cm.ph.getSearchGroups(data, 'var label = "([^"]+?)";')[0]
        vidUrl       = self.cm.ph.getSearchGroups(data, 'url: "([^"]+?)" \+ label \+ "([^"]+?)"', 2)
        vidUrl       = self._getFullUrl( vidUrl[0] + label + vidUrl[1] )
        playeSource  = self.cm.ph.getSearchGroups(data, "playeSource =[^;]*?'([^']+?)'[^;]*?;")[0]
        
        for myip in ['', config.plugins.iptvplayer.laola1tv_myip1.value, config.plugins.iptvplayer.laola1tv_myip2.value]:
            if '' != myip: header = {'X-Forwarded-For':myip}
            else: header = {}

            sts, data = self.getPage(vidUrl, {'header':header})
            if not sts: return urlTab
            data = self.cm.ph.getDataBeetwenMarkers(data, '<data>', '</data>', False)[1]
            printDBG(data)
            comment = self.cm.ph.getSearchGroups(data, 'comment="([^"]+?)"')[0]
            auth = self.cm.ph.getSearchGroups(data, 'auth="([^"]+?)"')[0]
            if auth == 'restricted': continue
            url  = self.cm.ph.getSearchGroups(data, 'url="([^"]+?)"')[0]
            url = url + playeSource + auth
            
            tmp = getDirectM3U8Playlist(url, checkExt=False)
            for item in tmp:
                item['need_resolve'] = 0
                urlTab.append(item)
            break
            
        if 0 < len(urlTab):
            max_bitrate = int(config.plugins.iptvplayer.laola1tv_defquality.value)
            def __getLinkQuality( itemLink ):
                try:
                    value = itemLink['bitrate']
                    return int(value)
                except:
                    printExc()
                    return 0
            urlTab = CSelOneLink(urlTab, __getLinkQuality, max_bitrate).getSortedLinks()
            if config.plugins.iptvplayer.laola1tv_onelink.value:
                urlTab = [urlTab[0]] 
        else:
            SetIPTVPlayerLastHostError(comment)
                
        return urlTab
    
    def getVideoLinks(self, baseUrl):
        printDBG("Movie4kTO.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        if '' != baseUrl: 
            videoUrl = baseUrl
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listMainMenu()
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'}, 'dir')
        elif category == 'main':
            self.listFromCache(self.currItem)
        elif category == 'videos_list':
            self.listVideos(self.currItem)
        elif category == 'calendar':    
            self.listCalendary(self.currItem)
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
        CHostBase.__init__(self, Laola1TV(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('laola1tvlogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item["need_resolve"]))

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
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Live-streams"), "live"))
        searchTypesOptions.append((_("Videos"), "videos"))
    
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
