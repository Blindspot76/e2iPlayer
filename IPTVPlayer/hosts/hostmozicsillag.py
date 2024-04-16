# -*- coding: utf-8 -*-
###################################################
# 2024-04-15 by Blindspot
###################################################
HOST_VERSION = "2.5"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, rm, GetTmpDir, MergeDicts
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
try:
    import urllib.parse
except:
   import urllib
import random
import base64
import os
from Components.config import config, ConfigText, ConfigYesNo, getConfigListEntry
###################################################
def gettytul():
    return 'https://mozicsillag1.me/'

class MoziCsillag(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'mozicsillag', 'cookie':'mozicsillag.cookie'})
        self.MAIN_URL = 'https://mozicsillag1.me/'
        self.DEFAULT_ICON_URL =  'https://mozicsillag1.me/img/logo.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
    
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
    
    def _uriIsValid(self, url):
        return '://' in url
    
    def listMainMenu(self, cItem):
        MAIN_CAT_TAB = [
                        {'category':'list_filters', 'title': _('Filmek'), 'url':'https://mozicsillag1.me/filmek-online/legfrissebb'},
                        {'category':'list_filters', 'title': _('Sorozatok'), 'url':'https://mozicsillag1.me/sorozatok-online'},
                        {'category':'search', 'title': _('Keresés'), 'search_item':True},
                        {'category':'search_history', 'title': _('Keresési előzmények')} 
                          ]
        self.listsTab(MAIN_CAT_TAB, {'name':'category'})
    
    def listFilters(self, cItem):
        printDBG("MoziCsillag.listFilters")
        sts, data = self.getPage(cItem['url'])
        if "filmek" in cItem['url']:
            cat = self.cm.ph.getDataBeetwenMarkers(data, '</i> Filmek</a>', '<li class="has-dropdown not-click">', False)[1]
            cats = self.cm.ph.getAllItemsBeetwenMarkers(cat, '<a href', '</a>', False)
            for i in cats:
                url = self.cm.ph.getDataBeetwenMarkers(i, '="', '"', False)[1]
                title = self.cm.ph.getDataBeetwenMarkers(i, '<strong>', '</strong>', False)[1]
                title = self.cleanHtmlStr(title)
                params = {'category':'list_items','title':title, 'icon': None, 'url': url}
                self.addDir(params)
                if cats.index(i) == 0:
                    url = 'https://mozicsillag1.me/filmek-online/legnezettebb'
                    title = "Legnézettebb"
                    params = {'category':'list_items','title':title, 'icon': None, 'url': url}
                    self.addDir(params)
                    url = 'https://mozicsillag1.me/filmek-online/legjobbra-ertekelt'
                    title = "Legjobbra értékelt"
                    params = {'category':'list_items','title':title, 'icon': None, 'url': url}
                    self.addDir(params)
        if "sorozatok" in cItem['url']:
            cat = self.cm.ph.getDataBeetwenMarkers(data, '</i> Sorozatok</a>', 'Sztárok', False)[1]
            cats = self.cm.ph.getAllItemsBeetwenMarkers(cat, '<a href', '</a>', False)
            for i in cats:
                url = self.cm.ph.getDataBeetwenMarkers(i, '="', '"', False)[1]
                title = self.cm.ph.getDataBeetwenMarkers(i, '<strong>', '</strong>', False)[1]
                title = self.cleanHtmlStr(title)
                params = {'category':'list_items','title':title, 'icon': None, 'url': url}
                self.addDir(params)
                if cats.index(i) == 0:
                    url = 'https://mozicsillag1.me/sorozatok-online/legnezettebb'
                    title = "Legnézettebb"
                    params = {'category':'list_items','title':title, 'icon': None, 'url': url}
                    self.addDir(params)
                    url = 'https://mozicsillag1.me/sorozatok-online/legjobbra-ertekelt'
                    title = "Legjobbra értékelt"
                    params = {'category':'list_items','title':title, 'icon': None, 'url': url}
                    self.addDir(params)
    
    def listItems(self, cItem):
        printDBG("MoziCsillag.listItems")
        sts, data = self.getPage(cItem['url'])
        next = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagination">', '</ul>', False)[1]
        film = self.cm.ph.getDataBeetwenMarkers(data, '<div class="row" id="listing-top-holder">', '<div class="row" id="listing-bottom-holder">', False)[1]
        if not film:
            film = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="small-block-grid-2 medium-block-grid-4 large-block-grid-5 enable-hover-link">', '<div class="pagination-centered">', False)[1]
        filmek = self.cm.ph.getAllItemsBeetwenMarkers(film, '<a href', '</div></a>', False)
        for i in filmek:
            url = self.cm.ph.getDataBeetwenMarkers(i, '="', '"', False)[1]
            title = self.cm.ph.getDataBeetwenMarkers(i, '<strong>', '</strong>', False)[1]
            title = self.cleanHtmlStr(title)
            icon = "https://mozicsillag1.me" + self.cm.ph.getDataBeetwenMarkers(i, 'data-original="', '"', False)[1]
            desc = self.cm.ph.getDataBeetwenMarkers(i, '</p>', '<div', False)[1]
            desc = desc.replace("<br>", "")
            desc = desc.replace("   ", "")
            desc = desc.replace("\n", "")
            desc = desc.replace("Hossz", " Hossz").replace("IMDB", " IMDB").replace("Feltöltve", " Feltöltve")
            params = {'category':'explore_items','title':title, 'icon': icon , 'url': url, 'desc': desc}
            self.addDir(params)
        if "</li><li class='arrow unavailable'>" not in next:
            next = self.cm.ph.getAllItemsBeetwenMarkers(next, "<a href='", "'", False)
            next = next[-1]
            params = {'category':'list_items','title':"Következő oldal", 'icon': None, 'url': next}
            self.addDir(params)
    
    def exploreItems(self, cItem):
        printDBG("MoziCsillag.exploreItems")
        sts, data = self.getPage(cItem['url'])
        desc = self.cm.ph.getDataBeetwenMarkers(data, '<p>', '</p>', False)[1]
        desc = self.cleanHtmlStr(desc)
        urls = data.split('<div class="panel">')
        if len(urls): 
           del urls[0]
        #printDBG('Lekért linkek: '+str(urls))
        if len(urls) == 1:
            urls = self.cm.ph.getDataBeetwenMarkers(data, '<div class="panel">', 'Lejátszás</a>', False)[1]
            printDBG('Lekért URLS: '+str(urls))
            host = self.cm.ph.getSearchGroups(urls, '''title=["]([^"^']+?)["]>.+/span''', 1, True)[0]
            printDBG('Lekért HOST: '+str(host))
            url = self.cm.ph.getSearchGroups(urls, '''href=['"]([^"^']+?)['"].target''', 1, True)[0]
            printDBG('Lekért URL: '+str(url))
            title = cItem['title'] + " - " + host
            printDBG('Lekért TITLE: '+str(title))
            params = {'title':title, 'icon': cItem['icon'] , 'url': url, 'desc': desc}
            self.addVideo(params)
        else:
           for i in urls:
               host = self.cm.ph.getSearchGroups(i, '''title=["]([^"^']+?)["]>.+/span''', 1, True)[0]
               printDBG('ELSE HOST: '+str(host))
               url = self.cm.ph.getSearchGroups(i, '''href=['"]([^"^']+?)['"].target''', 1, True)[0]
               printDBG('ELSE url: '+str(url))
               title = cItem['title'] + " - " + host
               printDBG('ELSE Title: '+str(title))
               params = {'title':title, 'icon': cItem['icon'] , 'url': url, 'desc': desc}
               self.addVideo(params)
    
    def exploreEpisodes(self, cItem):
        printDBG("MoziCsillag.exploreEpisodes")
        sts, data = self.getPage(cItem['url'])
        desc = self.cm.ph.getSearchGroups(data, '''Tag.+\s\s.+\s.+\s.+\s.+<p[>]([^"^']+?)[<]/p>''', 1, True)[0].strip()
        desc = self.cleanHtmlStr(desc)
        episodes = re.findall('''href="#.+strong[>]([^"^']+?)[<]/strong''', data)
        for i in episodes:
            printDBG(i)
            num = str(episodes.index(i)+1)
            title = num + ".rész"
            params = {'category': 'explore_episodes', 'title': title, 'url': cItem['url'], 'icon': cItem['icon'], 'num': num, 'desc': desc}
            self.addDir(params)
    
    def exploreLinks(self, cItem):
        sts, data = self.getPage(cItem['url'])
        episode = self.cm.ph.getDataBeetwenMarkers(data, "<strong>Epizód %s</strong>" % cItem['num'], '</dd>', False)[1]
        urls = re.findall('''href=['"]([^"^']+?)['"] t''', episode)
        titles = re.findall('''title="([^"^']+?)">.+</span>''', episode)
        for i in urls:
            params = {'title': titles[urls.index(i)], 'url': i, 'icon': cItem['icon'], 'desc': cItem['desc']}
            self.addVideo(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("MoziCsillag.getLinksForVideo")
        videoUrls = []
        sts, data = self.cm.getPage(cItem['url'])
        printDBG('GetLinksforVideo DATA: '+data)
        url = self.cm.meta['url']
        printDBG('GetLinksforVideo URL: '+str(url))
        if "waaw" in cItem['title']:
            sts, data = self.getPage(url)
            printDBG( 'Videolinkek oldala: ' + data )
            id = self.cm.ph.getDataBeetwenMarkers(data, "'MTQ5-", "')", False)[1]
            url = 'https://waaw.to/watch_video.php?v=' + id
        if 'voe' in cItem['title'] or 'Voe' in cItem['title']:
            videoUrls = []
            sts, data = self.getPage(url)
            printDBG( 'Film oldala: ' + data )
            url = self.cm.ph.getDataBeetwenMarkers(data, "'hls': '", "'", False)[1]
            if not url:
                url = self.cm.ph.getDataBeetwenMarkers(data, "'mp4': '", "'", False)[1]
            videoUrls.append({'name':'direct link', 'url':url})
            return videoUrls
        uri = urlparser.decorateParamsFromUrl(url)
        protocol = uri.meta.get('iptv_proto', '')
        
        printDBG("PROTOCOL [%s] " % protocol)
        
        urlSupport = self.up.checkHostSupport( uri )
        if 1 == urlSupport:
            retTab = self.up.getVideoLinkExt( uri )
            videoUrls.extend(retTab)
        elif 0 == urlSupport and self._uriIsValid(uri):
            if protocol == 'm3u8':
                retTab = getDirectM3U8Playlist(uri, checkExt=False, checkContent=True)
                videoUrls.extend(retTab)
            elif protocol == 'f4m':
                retTab = getF4MLinksWithMeta(uri)
                videoUrls.extend(retTab)
            elif protocol == 'mpd':
                retTab = getMPDLinksWithMeta(uri, False)
                videoUrls.extend(retTab)
            else:
                videoUrls.append({'name':'direct link', 'url':uri})
        return videoUrls
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG("MoziCsillag.handleService start")
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        url    = self.currItem.get("url", '')
        self.currList = []
        if name == None:
            self.listMainMenu( {'name':'category'} )        
        elif category == 'list_filters':
            self.listFilters(self.currItem)
        elif category == 'list_items':
            self.listItems(self.currItem)
        elif category == 'explore_items' and 'film' in url:
            self.exploreItems(self.currItem)
        elif category == 'explore_items' and 'sorozat' in url:
            self.exploreEpisodes(self.currItem)
        elif category == 'explore_episodes':
            self.exploreLinks(self.currItem)
        elif category == "search":
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        CBaseHostClass.endHandleService(self, index, refresh)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("MoziCsillag.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        try:
            searchPattern = urllib.parse.quote_plus(searchPattern)
        except:
            searchPattern = urllib.quote_plus(searchPattern)
        url = 'search_term=' + searchPattern +'&search_type=0&search_where=0&search_rating_start=1&search_rating_end=10&search_year_from=1900&search_year_to=2022'
        url = url.encode('ascii')
        url = base64.b64encode(url)
        url = url.decode("ascii")
        url = 'https://mozicsillag1.me/kereses/' + url
        cItem['url'] = url
        self.listItems(cItem) 

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, MoziCsillag(), True, [])
    