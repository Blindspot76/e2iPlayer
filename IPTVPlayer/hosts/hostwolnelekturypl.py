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

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'wolnelektury.pl'

class WolnelekturyPL(CBaseHostClass):
    ITEMS_PER_PAGE = 50
    HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    MAIN_URL = 'http://wolnelektury.pl/'
    DEFAULT_ICON = 'http://m.img.brothersoft.com/android/598/1352446551_icon.png'
    MAIN_CAT_TAB = [{'category':'categories',  'key':'author', 'title':'Autorzy',  'icon':DEFAULT_ICON},
                    {'category':'categories',  'key':'epoch',  'title':'Epoki',    'icon':DEFAULT_ICON},
                    {'category':'categories',  'key':'genre',  'title':'Gatunki',  'icon':DEFAULT_ICON},
                    {'category':'categories',  'key':'kind',   'title':'Rodzaje',  'icon':DEFAULT_ICON}]
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'wolnelektury.pl', 'cookie':'WolnelekturyPL.cookie'})
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.cache = []
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("WolnelekturyPL.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillCache(self):
        printDBG("WolnelekturyPL.fillCache")
        self.cache = []
        sts, data = self.cm.getPage('http://iptvplayer.pl/resources/wolnelektury3.db')
        if not sts: return
        try:
            self.cache = byteify(json.loads(data))
        except:
            printExc()
    
    def listCategories(self, cItem, category):
        printDBG("WolnelekturyPL.listCategories")
        try:
            key = cItem['key']
            categories = set()
            for item in self.cache:
                tmp = item[key].split(',')
                for cat in tmp:
                    categories.add(cat.strip())
            categories = sorted(list(categories))
        except:
            printExc()
        
        for item in categories:
            params = dict(cItem)
            params.update({'title':item, 'cat':item, 'category':category})
            self.addDir(params)
    
    def listItems(self, cItem):
        printDBG("WolnelekturyPL.listItems")
        
        try:
            key = cItem['key']
            cat = cItem['cat']
            max = len(self.cache)
            idx = cItem.get('idx', 0)
            items = 0
            while idx < max and items < self.ITEMS_PER_PAGE:
                if cat in self.cache[idx][key]:
                    params = dict(cItem)
                    title = self.cache[idx]['title']
                    icon  = self.cache[idx]['cover']
                    url   = self.cache[idx]['href']
                    
                    desc = []
                    for dKey in ['kind', 'author', 'epoch', 'genre']:
                        desc.append(self.cache[idx][dKey])
                    params.update({'title':title, 'icon':icon, 'url':url, 'desc':'[/br]'.join(desc)}) 
                    self.addAudio(params)
                    items += 1
                idx += 1
            
            if idx < max:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'idx':idx})
                self.addDir(params)
        except:
            printExc()
    
    def getLinksForVideo(self, cItem):
        printDBG("WolnelekturyPL.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        try:
            data = byteify(json.loads(data))
            for item in data['media']:
                if item['type'] not in ['mp3', 'ogg']: continue
                urlTab.append({'name': '{0} | {1}, {2}'.format(item['type'], item['artist'], item['director']), 'url':item['url'], 'need_resolve':0})
        except:
            printExc()
        
        return urlTab
        
    def getArticleContent(self, cItem):
        printDBG("WolnelekturyPL.getArticleContent [%s]" % cItem)
        retTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        try:
            data = byteify(json.loads(data))
            url = data['txt']
            sts, desc = self.cm.getPage(url)
            if not sts: desc = ''
            otherInfo = {}
            return [{'title':self.cleanHtmlStr( data['title'] ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':data['cover']}], 'other_info':otherInfo}]
        except:
            printExc()
        
        return []
        
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
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.fillCache()
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem)
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, WolnelekturyPL(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('wolnelekturypllogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        cItem = self.host.currList[Index]
        if cItem['type'] != 'audio':
            return RetHost(retCode, value=retlist)
        
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
