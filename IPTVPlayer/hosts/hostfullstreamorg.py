# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import _unquote
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.components.asynccall import iptv_execute
###################################################

###################################################
# FOREIGN import
###################################################
import time
import datetime
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
config.plugins.iptvplayer.fullstreamorg_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.fullstreamorg_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry( _("Login") + ": ", config.plugins.iptvplayer.fullstreamorg_login))
    optionList.append(getConfigListEntry( _("Password") + ": ", config.plugins.iptvplayer.fullstreamorg_password))
    return optionList
    
def gettytul():
    return 'full-stream.org'

class FullStreamORG(CBaseHostClass):
    HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    MAIN_URL = 'http://full-stream.org/'
    DEFAULT_ICON = 'http://full-stream.org/templates/F-S/images/logo.png'
    MAIN_CAT_TAB = [{'category':'categories',      'title': 'Séries TV',                    'itype':'serie', 'url':MAIN_URL + 'seriestv/', 'icon':DEFAULT_ICON},
                    {'category':'categories',      'title': 'Mangas',                       'itype':'manga', 'url':MAIN_URL + 'mangas/',   'icon':DEFAULT_ICON},
                    {'category':'categories',      'title': 'Film',                         'itype':'movie', 'url':MAIN_URL + 'movie/',    'icon':DEFAULT_ICON},
                    {'category':'search',          'title': _('Search'), 'search_item':True, 'icon':DEFAULT_ICON},
                    {'category':'search_history',  'title': _('Search history'),             'icon':DEFAULT_ICON} ]
    
    SORT_BY_TAB = [{'category':'list_items', 'title': _('Recent'),         'sort_by':'date'     },
                   {'category':'list_items', 'title': 'Les + Notés',       'sort_by':'rating'   },
                   {'category':'list_items', 'title': 'Les + Vus',         'sort_by':'news_read'},
                   {'category':'list_items', 'title': 'Les + Commentés',   'sort_by':'comm_num' },
                   {'category':'list_items', 'title': _('Alphabetically'), 'sort_by':'title'    }]

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'full-stream.org', 'cookie':'FullStreamORG.cookie'})
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.subCache = {}
        self.abcCache = {}
        
    def _getFullUrl(self, url, api=True):
        baseUrl = self.MAIN_URL
        if 0 < len(url):
            if url.startswith('//'):
                url = 'http:' + url
            elif not url.startswith('http'):
                url =  baseUrl + url
        if not baseUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("FullStreamORG.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listCategories(self, cItem):
        printDBG("FullStreamORG.listCategories")
        
        sts, data = self.cm.getPage(self.MAIN_URL, self.defaultParams)
        if not sts: return
        
        type = cItem.get('itype', '')
        
        if type == 'serie':
            m1 = '</i>Séries TV'
            m2 = '</ul>'
        elif type == 'manga':
            m1 = '</i>Mangas'
            m2 = '</ul>'
        elif type == 'movie':
            m1 = '</i>Film'
            m2 = '/forum/'
        else:
            return
            
        params = dict(cItem)
        params.update({'category':'list_sort', 'title':_('--All--')})
        self.addDir(params)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(data)
        for item in data:
            params = dict(cItem)
            params.update({'title':self.cleanHtmlStr(item[1]), 'url':self._getFullUrl(item[0])})
            if 'liste-des' in item[0]:
                params['category'] = 'list_abc' 
            else:
                params['category'] = 'list_sort' 
            self.addDir(params)
            
        if type != 'serie':
            return
        
        self.subCache = {}
        sts, data = self.cm.getPage(self._getFullUrl('10363-zoo-saison-1.html'), self.defaultParams)
        if not sts: return
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, ' seri-list"', '</div>', False)[1]
        tmp = re.compile('<a[^>]+?data-rel="([^"]+?)"[^>]*?>([^<]+?)<').findall(tmp)
        for item in tmp:
            key = item[0]
            categories = []
            catData = self.cm.ph.getDataBeetwenMarkers(data, 'id="%s" class="fullsfeature"' % key, '</ul>', False)[1]
            catData = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(catData)
            for cat in catData:
                categories.append({'category':'list_sort', 'title':self.cleanHtmlStr(cat[1]), 'url':self._getFullUrl(item[0])})
            if len(categories):
                params = dict(cItem)
                params.update({'category':'list_sub', 'title':self.cleanHtmlStr(item[1]), 'key':key})
                self.addDir(params)
                self.subCache[key] = categories
        
    def listSub(self, cItem):
        printDBG("FullStreamORG.listSeriesSub")
        data = self.subCache.get(cItem.get('key', ''), [])
        for item in data:
            params = dict(cItem)
            params.update(item)
            self.addDir(params)
            
    def listABC(self, cItem):
        printDBG("FullStreamORG.listABC")
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        self.abcCache = {}
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="charlist">', '<div id="block-bottom">', False)[1]
        data = data.split('<hr')
        for item in data:
            item = item.split('<br/>')
            if 2 != len(item): continue
            seasons = []
            key = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item[0], 'class="letter-title"[^>]*?>([^<]+?)<')[0])
            item = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)<').findall(item[1])
            for season in item:
                seasons.append({'category':'list_episodes', 'title':self.cleanHtmlStr(season[1]), 'url':self._getFullUrl(season[0])})
            if len(seasons):
                params = dict(cItem)
                params.update({'category':'list_abc_sub', 'title':key, 'key':key})
                self.addDir(params)
                self.abcCache[key] = seasons
                
    def listABCSub(self, cItem):
        printDBG("FullStreamORG.listSeriesSub")
        data = self.abcCache.get(cItem.get('key', ''), [])
        for item in data:
            params = dict(cItem)
            params.update(item)
            self.addDir(params)
    
    def listItems(self, cItem, post_data=None):
        printDBG("FullStreamORG.listItems")
        
        post_data = post_data
        if 'sort_by' in cItem:
            post_data = {'dlenewssortby':cItem['sort_by'], 'dledirection':'desc', 'set_new_sort':'dle_sort_cat', 'set_direction_sort':'dle_direction_cat'}
        
        url  = cItem['url']
        page = cItem.get('page', 1)
        if page > 1:
            if not url.endswith('/'):
                url += '/'
            url += 'page/%s/' % page
         
        sts, data = self.cm.getPage(url, self.defaultParams, post_data)
        if not sts: return
        
        nextPage = self.cm.ph.getSearchGroups(data, '"([^"]*?/page/%s/)"' % (page + 1))[0]
        m1 = '﻿﻿<div class="fullstream fullstreaming">'
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, '<div class="clr">')[1]
        data = data.split(m1)
        if len(data): del data[0]
        for item in data:
            url   = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if 'src=http' in icon:
                icon = icon.split('src=')[-1].split('&w=')[0].split('&h=')[0]
            title = self.cm.ph.getSearchGroups(item, '<a[^<]+?>([^<]+?)</a>')[0]
            desc  = self.cleanHtmlStr(item.replace('<hr/>', '[/br]'))
            
            params = dict(cItem)
            params.update({'category':'list_episodes', 'url':url, 'title':self.cleanHtmlStr(title), 'icon':icon, 'desc':desc})
            
            type = cItem.get('itype', '')
            if type == '':
                     
                if 'saison-' in url or '/manga/' in url or '/serie/' in url or 'Statut ' in item:
                    type = 'serie'
                elif '>Film</a>' in item:
                    type = 'movie'
                else:
                    type = 'manga'
            
            if type != 'movie':
                season = self.cm.ph.getSearchGroups(url+'-', 'aison-([0-9]+?)[^0-9]' )[0]
                params['season'] = season
                params['itype'] = type
                self.addDir(params)
            else:
                self.addVideo(params)
            
        if nextPage != '':
            params = dict(cItem)
            params.update({'title':_("Next page"), 'page':page+1})
            self.addDir(params)
                
    def _getBaseVideoLink(self, data, season, titleSeason, groupByVer=False):
        episodesTab = []
        episodesLinks = {}
        
        error = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div class="block_red">', '<div class="clr">')[1])
        if '' != error:
            SetIPTVPlayerLastHostError(error)
        verData = self.cm.ph.getDataBeetwenMarkers(data, '<div class="clr" style="height:20px">', '<div class="clr" style="height:15px">')[1]
        verData = verData.split('<i class="fa fa-play-circle-o">')
        if len(verData): del verData[0]
        for verItem in verData:
            verItem = verItem.split('<div class="elink">')
            if 2 != len(verItem): continue
            verName = self.cleanHtmlStr(verItem[0])
            episodesData = self.cm.ph.getAllItemsBeetwenMarkers(verItem[1], '<a', '</a>')
            for episodeItem in episodesData:
                url = self.cm.ph.getSearchGroups(episodeItem, '''href=['"]([^'^"]+?)['"]''')[0]
                rel = self.cm.ph.getSearchGroups(episodeItem, '''data-rel=['"]([^'^"]+?)['"]''')[0]
                title = self.cleanHtmlStr(episodeItem)
                playersUrls = []
                if '#' == url:
                    playersData = self.cm.ph.getDataBeetwenMarkers(data, ' id="%s"' % rel, '</ul>')[1]
                    playersData = re.compile('<a[^>]+?href="(http[^"]+?)"[^>]*?>([^<]+?)</a>').findall(playersData)
                    for playerItem in playersData:
                        hotName = self.up.getHostName(playerItem[0])
                        playersUrls.append({'ver_name':verName, 'host_name':hotName, 'title':title, 'name':'%s | %s' % (verName, hotName), 'url':playerItem[0], 'need_resolve':1})
                elif url.startswith('http'):
                    hotName = self.up.getHostName(url)
                    playersUrls.append({'ver_name':verName, 'host_name':hotName, 'title':title, 'name':'%s | %s' % (verName, hotName), 'url':url, 'need_resolve':1})
                
                if len(playersUrls):
                    if groupByVer:
                        fullTitle = verName.strip()
                    else:
                        fullTitle = titleSeason + ' '
                        if season != '':
                            fullTitle += 's%s' % season
                        try:
                            episode = self.cm.ph.getSearchGroups(title + '.', '''pisode ([0-9]+?)[^0-9]''')[0]
                            title = int(episode)
                            fullTitle += 'e%s' % (title) 
                        except:
                            fullTitle += ' %s' % (title)
                    if fullTitle not in episodesTab:
                        episodesTab.append(fullTitle)
                        episodesLinks[fullTitle] = playersUrls
                    else:
                        episodesLinks[fullTitle].extend(playersUrls)
        return episodesTab, episodesLinks
                
    def listEpisodes(self, cItem):
        printDBG("FullStreamORG.listEpisodes")
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        
        #descData  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="filmalti">', '<div class="filmborder">')[1]
        #desc = self.cleanHtmlStr(descData)
        #icon = self.cm.ph.getSearchGroups(descData, '''src=['"]([^'^"]+?)['"]''')[0]
        titleSeason = cItem['title'].split('Saison')[0]
        
        episodesTab, episodesLinks = self._getBaseVideoLink(data, cItem.get('season', ''), titleSeason)
                    
        for title in episodesTab:
            params = dict(cItem)
            params.update({'urls':episodesLinks[title], 'title':title, 'episode':True})#, 'icon':icon, 'desc':desc})
            self.addVideo(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("FullStreamORG.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.MAIN_URL
        post_data = {'do':'search', 'subaction':'search', 'story':searchPattern}
        self.listItems(cItem, post_data)
    
    def getLinksForVideo(self, cItem):
        printDBG("FullStreamORG.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if cItem.get('episode', False):
            return cItem['urls']
        
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return []
        
        episodesTab, episodesLinks = self._getBaseVideoLink(data, '', '', True)
        for title in episodesTab:
            for item in episodesLinks[title]:
                urlTab.append({'name':'%s | %s | %s ' % (item['ver_name'], item['host_name'], item['title']), 'url':item['url'], 'need_resolve':item['need_resolve']})
        
        return urlTab
        
    def getVideoLinks(self, url):
        printDBG("FullStreamORG.getVideoLinks [%s]" % url)
        urlTab = []
        
        if url.startswith('http'):
            return self.up.getVideoLinkExt(url)
        return []
        
    def getArticleContent(self, cItem):
        printDBG("FullStreamORG.getArticleContent [%s]" % cItem)
        retTab = []
        
        if 'resource_uri' not in cItem:
            return []
            
        if 0 == len(self.loginData['api_key']) and 0 == len(self.loginData['username']):
            self.requestLoginData()
        
        url = cItem['resource_uri']
        url += '?api_key=%s&username=%s' % (self.loginData['api_key'], self.loginData['username'])
        url = self._getFullUrl(url, False)
        
        sts, data = self.cm.getPage(url)
        if not sts: return []
        
        title = cItem['title']
        desc  = cItem.get('desc', '')
        icon  = cItem.get('icon', '')
        otherInfo = {}
        try:
            data = byteify(json.loads(data))
            icon = self._viaProxy( self._getFullUrl(data['poster'], False) )
            title = data['title']
            desc = data['overview']
            otherInfo['actors'] = data['actors']
            otherInfo['director'] = data['director']
            genres = []
            for item in data['genre']:
                genres.append(item['name'])
            otherInfo['genre'] = ', '.join(genres)
            otherInfo['rating']= data['imdb_rating']
            otherInfo['year']  = data['year']
            otherInfo['duration'] = str(datetime.timedelta(seconds=data['runtime']))
        except:
            printExc()
        
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo}]
        
    def doLogin(self, login, password):
        logged = False
        HTTP_HEADER= dict(self.HTTP_HEADER)
        HTTP_HEADER.update( {'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With' : 'XMLHttpRequest'} )

        post_data = {'login_name':login, 'login_password':password, 'Submit':'', 'login':'submit'}
        params    = {'header' : HTTP_HEADER, 'cookiefile' : self.COOKIE_FILE, 'save_cookie' : True}
        loginUrl  = self.MAIN_URL
        sts, data = self.cm.getPage( loginUrl, params, post_data)
        if sts and '?action=logout"' in data:
            logged = True
        return logged
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            login  = config.plugins.iptvplayer.fullstreamorg_login.value
            passwd = config.plugins.iptvplayer.fullstreamorg_password .value
            if '' != login.strip() and '' != passwd.strip():
                if not self.doLogin(login, passwd):
                    self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_INFO, timeout = 10 )
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem)
        elif category == 'list_sub':
            self.listSub(self.currItem)
        elif category == 'list_abc':
            self.listABC(self.currItem)
        elif category == 'list_abc_sub':
            self.listABCSub(self.currItem)
        elif category == 'list_sort':
            self.listsTab(self.SORT_BY_TAB, self.currItem)
        elif category == 'list_items':
            self.listItems(self.currItem)
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
        CHostBase.__init__(self, FullStreamORG(), True, [])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('fullstreamorglogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

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
    
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        cItem = self.host.currList[Index]
        
        hList = self.host.getArticleContent(cItem)
        if 0 == len(hList):
            return RetHost(retCode, value=retlist)
        for item in hList:
            title      = item.get('title', '')
            text       = item.get('text', '')
            images     = item.get("images", [])
            othersInfo = item.get('other_info', '')
            retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
        return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        
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
