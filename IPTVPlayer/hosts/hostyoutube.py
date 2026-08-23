# -*- coding: utf-8 -*-
# Blindspot - 2026-07-15
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, IsExecutable, printExc, byteify, GetSearchHistoryDir
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tools.iptvfilehost import IPTVFileHost
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################
from Plugins.Extensions.IPTVPlayer.p2p3.UrlLib import urllib_quote_plus
###################################################
# FOREIGN import
###################################################
try:
    import json
except Exception:
    import simplejson as json
import re
import urllib
import os
import codecs
from Components.config import config, ConfigDirectory, getConfigListEntry
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.Sciezkaurllist = ConfigDirectory(default="/hdd/")


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Sort by:"), config.plugins.iptvplayer.ytSortBy))
    optionList.append(getConfigListEntry(_("Path to ytlist.txt, urllist.txt"), config.plugins.iptvplayer.Sciezkaurllist))
    optionList.append(getConfigListEntry(_("Video format:"), config.plugins.iptvplayer.ytformat))
    optionList.append(getConfigListEntry(_("Default video quality:"), config.plugins.iptvplayer.ytDefaultformat))
    optionList.append(getConfigListEntry(_("Use default video quality:"), config.plugins.iptvplayer.ytUseDF))
    optionList.append(getConfigListEntry(_("Age-gate bypass:"), config.plugins.iptvplayer.ytAgeGate))
    # temporary, the ffmpeg must be in right version to be able to merge file without transcoding
    # checking should be moved to setup
    if IsExecutable('ffmpeg'):
        optionList.append(getConfigListEntry(_("Allow dash format:"), config.plugins.iptvplayer.ytShowDash))
        if config.plugins.iptvplayer.ytShowDash.value != 'false':
            optionList.append(getConfigListEntry(_("Allow VP9 codec:"), config.plugins.iptvplayer.ytVP9))
    return optionList
###################################################
###################################################


def gettytul():
    return 'https://youtube.com/'


class Youtube(CBaseHostClass):

    def __init__(self):
        printDBG("Youtube.__init__")
        CBaseHostClass.__init__(self, {'history': 'ytlist', 'cookie': 'youtube.cookie'})
        self.UTLIST_FILE = 'ytlist.txt'
        self.DEFAULT_ICON_URL = 'https://www.mm229.com/images/youtube-button-psd-450203.png'
        self.yeah = self.lenhistory()
        self.MAIN_GROUPED_TAB = [{'category': 'from_file',
          'title': _('User links'),
          'desc': _('User links stored in the ytlist.txt file.')},
         {'category': 'search',
          'title': _('Search'),
          'desc': _('Search youtube materials '),
          'search_item': True},
         {'category': 'feeds',
          'title': _('Explore'),
          'desc': _('Popular trending videos')},
         {'category': 'search_history',
          'title': _('Search history'),
          'desc': _('History of searched phrases.')},
          {'category': 'delete_history',
          'title': _('Delete search history'),
          'desc': self.yeah}]         
          
        self.SEARCH_TYPES = [(_("Video"), "video"),
                               (_("Channel"), "channel"),
                               (_("Playlist"), "playlist"),
                              #(_("Movie"),    "movie"   ),
                               (_("Live"), "live")]
                              #("Program",            "show"    ),
                              #("traylist",           "traylist"),
        self.ytp = YouTubeParser()
        self.currFileHost = None

    def getJsonObject(self, text, marker):
       start = text.find(marker)
       if start < 0:
           return None
       start = text.find('{', start)
       if start < 0:
           return None
       level = 0
       in_string = False
       escape = False
       for i in range(start, len(text)):
           c = text[i]
           if escape:
               escape = False
               continue
           if c == '\\':
               escape = True
               continue
           if c == '"':
               in_string = not in_string
               continue
           if in_string:
               continue
           if c == '{':
               level += 1
           elif c == '}':
               level -= 1
               if level == 0:
                   try:
                       return json.loads(text[start:i+1])
                   except Exception as e:
                       printDBG("JSON ERROR: %s" % e)
                       return None
       return None
       
    def _getCategory(self, url):
        printDBG("Youtube._getCategory")
        if '/playlist?list=' in url:
            category = 'playlist'
        elif url.split('?')[0].endswith('/playlists'):
            category = 'playlists'
        elif None != re.search('/watch\?v=[^\&]+?\&list=', url):
            category = 'traylist'
        elif 'user/' in url or (('channel/' in url or '/c/' in url or '/@' in url) and not url.endswith('/live')):
            category = 'channel'
        else:
            category = 'video'
        return category

    def listMainMenu(self):
        printDBG("Youtube.listsMainMenu")
        for item in self.MAIN_GROUPED_TAB:
            params = {'name': 'category'}
            params.update(item)
            self.addDir(params)

    def listCategory(self, cItem, searchMode=False):
        printDBG("Youtube.listCategory cItem[%s]" % cItem)

        sortList = True
        filespath = config.plugins.iptvplayer.Sciezkaurllist.value
        groupList = True
        if 'sub_file_category' not in cItem:
            self.currFileHost = IPTVFileHost()
            self.currFileHost.addFile(filespath + self.UTLIST_FILE, encoding='utf-8')
            tmpList = self.currFileHost.getGroups(sortList)
            if 0 < len(tmpList):
                params = dict(cItem)
                params.update({'sub_file_category': 'all', 'group': 'all', 'title': _("--All--")})
                self.addDir(params)
            for item in tmpList:
                if '' == item:
                    title = _("--Other--")
                else:
                    title = item
                params = dict(cItem)
                params.update({'sub_file_category': 'group', 'title': title, 'group': item})
                self.addDir(params)
        else:
            if 'all' == cItem['sub_file_category']:
                tmpList = self.currFileHost.getAllItems(sortList)
                for item in tmpList:
                    params = dict(cItem)
                    category = self._getCategory(item['url'])
                    params.update({'good_for_fav': True, 'title': item['full_title'], 'url': item['url'], 'desc': item['url'], 'category': category})
                    if 'video' == category:
                        self.addVideo(params)
                    elif 'more' == category:
                        self.addMore(params)
                    else:
                        self.addDir(params)
            elif 'group' == cItem['sub_file_category']:
                tmpList = self.currFileHost.getItemsInGroup(cItem['group'], sortList)
                for item in tmpList:
                    if '' == item['title_in_group']:
                        title = item['full_title']
                    else:
                        title = item['title_in_group']
                    params = dict(cItem)
                    category = self._getCategory(item['url'])
                    params.update({'good_for_fav': True, 'title': title, 'url': item['url'], 'desc': item['url'], 'category': category})
                    if 'video' == category:
                        self.addVideo(params)
                    elif 'more' == category:
                        self.addMore(params)
                    else:
                        self.addDir(params)

    def listItems(self, cItem):
        printDBG('Youtube.listItems cItem[%s]' % (cItem))
        category = cItem.get("category", '')
        url = cItem.get("url", '')
        page = cItem.get("page", '1')
        if "playlists" == category:
            self.currList = self.ytp.getListPlaylistsItems(url, category, page, cItem)

        for idx in range(len(self.currList)):
            if self.currList[idx]['category'] in ["channel", "playlist", "movie", "traylist"]:
                self.currList[idx]['good_for_fav'] = True
    
    def listFeeds(self, cItem):
        printDBG('Youtube.listFeeds cItem[%s]' % cItem)
        if cItem.get('category') == "feeds_video":
            if 'page_data' in cItem:
                sts = True
                data = cItem['page_data']
            else:
                sts, data = self.cm.getPage(cItem['url'])
            tokens = re.findall(r'"token":"([^"]+)"', data)
            itcts = re.findall(r'"clickTrackingParams":"([^"]+)"', data)
            nextToken = tokens[-1] if tokens else ""
            itct = itcts[-1] if itcts else ""
            printDBG("NEXT TOKEN[%s]" % nextToken)
            printDBG("NEXT ITCT[%s]" % itct)
            if nextToken:
                pos = data.find(nextToken)
                printDBG("TOKEN FOUND AT[%d]" % pos)
                printDBG(data[max(0, pos-500):pos+800])
            grid = self.cm.ph.getDataBeetwenMarkers(data, '"richGridRenderer":{', 'PageType,a.ytCommand', False)[1]
            if not grid:
                grid = self.cm.ph.getDataBeetwenMarkers(data, '"richGridRenderer":{', 'continuationItemRenderer', False)[1]
            printDBG("GRID LEN[%s]" % len(grid))
            items = grid.split('richItemRenderer')
            if len(items) > 1:
                del items[0]
            printDBG("ITEM COUNT[%s]" % len(items))
            for item in items:
                videoId = self.cm.ph.getSearchGroups(item, '''videoId":["]([^"^']+)['"]''', 1, True)[0]
                if not videoId:
                    continue
                url = "https://www.youtube.com/watch?v=" + videoId
                icon = self.cm.ph.getSearchGroups(item, '''url":["]([^"^']+)['"],"width":336''', 1, True)[0]
                title = self.cm.ph.getSearchGroups(item, '''"lockupMetadataViewModel":{"title":{"content":"([^"]+)''', 1, True)[0]
                if not title:
                    title = self.cm.ph.getSearchGroups(item, '''label":["]([^"^']+)['"]''', 1, True)[0]
                if len(title) <= 3:
                    title = self.cm.ph.getSearchGroups(item, '''content":"((?:\\\\.|[^"])*)''', 1, True)[0]
                title = title.replace('&quot;', '"')
                title = title.replace('\\u0026', '&')
                printDBG("ADD VIDEO id[%s] title[%s]" % (videoId, title))
                params = {'title': title, 'url': url, 'icon': icon, 'desc': ''}
                self.addVideo(params)
            if nextToken:
                params = {'type': 'more', 'category': 'feeds_next_page', 'title': 'Next Page', 'url': cItem['url'], 'continuation': nextToken, 'itct': itct}
                printDBG("CREATE NEXT PAGE[%s]" % params)
                self.addDir(params)
        
        elif cItem.get('category') == "feeds_next_page":
            printDBG("NEXT PAGE CLICK cItem[%s]" % cItem)
            continuation = cItem.get('continuation', '')
            itct = cItem.get('itct', '')
            if not continuation:
                printDBG("ERROR NO CONTINUATION")
                return
            post_data = {"continuation": continuation, "context": {"client": {"clientName": "WEB", "clientVersion": "2.20250331.00.00", "hl": "en", "gl": "US"}, "clickTracking": {"clickTrackingParams": itct}}}
            post_data = json.dumps(post_data)
            url = "https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
            params = {"header": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Content-Type": "application/json"}, "raw_post_data": True}
            printDBG("NEXT REQUEST URL[%s]" % url)
            printDBG("NEXT POST LEN[%s]" % len(post_data))
            sts, data = self.cm.getPage(url, params, post_data)
            printDBG("NEXT RESPONSE sts[%s] len[%s]" % (sts, len(data)))
            if not sts:
                printDBG("NEXT REQUEST FAILED")
                return
            printDBG("NEXT richItemRenderer[%s]" % ("YES" if "richItemRenderer" in data else "NO"))
            printDBG("NEXT videoRenderer[%s]" % ("YES" if "videoRenderer" in data else "NO"))
            printDBG("NEXT gridVideoRenderer[%s]" % ("YES" if "gridVideoRenderer" in data else "NO"))
            printDBG("NEXT continuationItems[%s]" % ("YES" if "continuationItems" in data else "NO"))
            self.listFeeds({'category': 'feeds_video', 'url': cItem.get('url', ''), 'page_data': data})

        else:
          title = "YouTube videos test"
          url = "https://www.youtube.com/channel/UCBR8-60-B28hp2BmDPdntcQ/videos"
          params = {'category':'feeds_video','title':title, 'url': url}
          self.addDir(params)
          title = "Music"
          url = "https://www.youtube.com/@YouTubeMusic/videos"
          params = {'category':'feeds_video','title':title, 'url': url}
          self.addDir(params)
          title = "Gaming"
          url = "https://www.youtube.com/@YouTubeGaming/videos"
          params = {'category':'feeds_video','title':title, 'url': url}
          self.addDir(params)
          title = _("Podcasts")
          url = "https://www.youtube.com/podcasts"
          params = {'category': 'feeds_video', 'title': title, 'url': url}
          self.addDir(params)

    def listSubItems(self, cItem):
        printDBG("Youtube.listSubItems")
        self.currList = cItem['sub_items']

    def getVideos(self, cItem):
        printDBG('Youtube.getVideos cItem[%s]' % (cItem))

        category = cItem.get("category", '')
        url = strwithmeta(cItem.get("url", ''))
        page = cItem.get("page", '1')

        if "channel" == category:
            if not ('browse' in url) and (not 'ctoken' in url):
                if url.endswith('/videos'):
                    url = url + '?flow=list&view=0&sort=dd'
                else:
                    url = url + '/videos?flow=list&view=0&sort=dd'
                tmp = self.ytp.getVideosFromChannelList(url, category, page, cItem)
                if len(tmp) > 0:
                    params = {'good_for_fav': False, 'category': 'sub_items', 'title': _('Videos'), 'sub_items': tmp}
                    self.addDir(params)
                url = url.replace('videos', 'streams')
                tmp = self.ytp.getVideosFromChannelList(url, category, page, cItem)
                if len(tmp) > 0:
                    params = {'good_for_fav': False, 'category': 'sub_items', 'title': _('Live streams'), 'sub_items': tmp}
                    self.addDir(params)
            else:
                self.currList = self.ytp.getVideosFromChannelList(url, category, page, cItem)

        elif "playlist" == category:
            self.currList = self.ytp.getVideosApiPlaylist(url, category, page, cItem)

        elif "traylist" == category:
            self.currList = self.ytp.getVideosFromTraylist(url, category, page, cItem)
        else:
            printDBG('YTlist.getVideos Error unknown category[%s]' % category)

    def listSearchResult(self, cItem, pattern, searchType):
        page = cItem.get("page", '1')
        url = cItem.get("url", "")

        if url:
            printDBG("URL ricerca -----------> %s" % url)
            tmpList = self.ytp.getSearchResult(urllib.quote_plus(pattern), searchType, page, 'search', config.plugins.iptvplayer.ytSortBy.value, url)
        else:
            tmpList = self.ytp.getSearchResult(urllib.quote_plus(pattern), searchType, page, 'search', config.plugins.iptvplayer.ytSortBy.value)

        for item in tmpList:
            item.update({'name': 'category'})
            if 'video' == item['type']:
                self.addVideo(item)
            elif 'more' == item['type']:
                self.addMore(item)
            else:
                if item['category'] in ["channel", "playlist", "movie", "traylist"]:
                    item['good_for_fav'] = True
                self.addDir(item)

    def getLinksForVideo(self, cItem):
        printDBG("Youtube.getLinksForVideo cItem[%s]" % cItem)
        urlTab = self.up.getVideoLinkExt(cItem['url'])
        if config.plugins.iptvplayer.ytUseDF.value and 0 < len(urlTab):
            return [urlTab[0]]
        return urlTab

    def getFavouriteData(self, cItem):
        printDBG('Youtube.getFavouriteData')
        return json.dumps(cItem)

    def getLinksForFavourite(self, fav_data):
        printDBG('Youtube.getLinksForFavourite')
        links = []
        try:
            cItem = byteify(json.loads(fav_data))
            links = self.getLinksForVideo(cItem)
        except Exception:
            printExc()
            return self.getLinksForVideo({'url': fav_data})
        return links

    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('Youtube.setInitListFromFavouriteItem')
        try:
            params = byteify(json.loads(fav_data))
        except Exception:
            params = {}
            printExc()
        self.addDir(params)
        return True

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Youtube.handleService start')

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG("Youtube.handleService: ---------> name[%s], category[%s] " % (name, category))
        self.currList = []

        if None == name:
            self.listMainMenu()
        elif 'from_file' == category:
            self.listCategory(self.currItem)
        elif category in ["channel", "playlist", "movie", "traylist"]:
            self.getVideos(self.currItem)
        elif category.startswith("feeds"):
            self.listFeeds(self.currItem)
        elif category == 'playlists':
            self.listItems(self.currItem)
        elif category == 'sub_items':
            self.listSubItems(self.currItem)
        #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item': False, 'name': 'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
        #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name': 'history', 'category': 'search'}, 'desc', _("Type: "))
        elif category == "delete_history":
            self.delhistory()
        else:
            printExc()
        self.yeah = self.lenhistory()

        CBaseHostClass.endHandleService(self, index, refresh)

    def delhistory(self):
        printDBG('Youtube.delhistory')
        msg = 'Are you sure you want to delete search history?'
        ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
        if ret[0]:
            self.doit()

    def doit(self):
        try:
           os.remove(GetSearchHistoryDir("ytlist.txt"))
           msg = 'Search History successfully deleted.'
           ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_INFO)
        except:
           msg = 'Unable to comply. Search History is empty.'
           ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_INFO)
    
    def lenhistory(self):
        num = 0
        
        try:
            file = codecs.open(GetSearchHistoryDir("ytlist.txt"), 'r', 'utf-8', 'ignore')
            for line in file:
                num = num+1
            file.close()
        except:
            return("Search History is empty.")
        return("Number of items in search history: " + str(num))
    
    def getSuggestionsProvider(self, index):
        printDBG('Youtube.getSuggestionsProvider')
        from Plugins.Extensions.IPTVPlayer.suggestions.google import SuggestionsProvider
        return SuggestionsProvider(True)


class IPTVHost(CHostBase):

    def getSearchTypes(self):
        return self.host.SEARCH_TYPES

    def __init__(self):
        CHostBase.__init__(self, Youtube(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
