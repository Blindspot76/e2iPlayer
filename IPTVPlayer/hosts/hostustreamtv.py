# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from os import stat
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetLogoDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.e2ijs import js_execute
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta

###################################################

###################################################
# FOREIGN import
###################################################
import copy
import re
import urllib
try:    import json
except Exception: import simplejson as json
###################################################


import requests

def gettytul():
    return 'http://ustream.to/'

class UstreamTV(CBaseHostClass):
    def __init__(self):
        CBaseHostClass.__init__(self)

        self.MAIN_URL    = 'https://www.ustream.to/'
        self.SRCH_URL    = self.MAIN_URL + 'search?q='
        self.DEFAULT_ICON_URL = 'http://occopwatch-com.secure40.ezhostingserver.com/wp-content/uploads/2013/10/ustream-logo.jpg'

        self.MAIN_CAT_TAB = [
            {'category': 'listItems',          'title': _("Main"), 'url': self.MAIN_URL},
            {'category': 'listItems',          'title': _("Sports"), 'url': self.MAIN_URL + '/sports'},
            {'category': 'listCountries',      'title': _("Countries"), 'url': self.MAIN_URL},
            ]
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}

        self.session = requests.Session()
        self.session.headers.update(self.HEADER)

    def listItems(self, cItem, nextCategory):
        printDBG("UstreamTV.listItems cItem: %s" % cItem)

        url = cItem['url']
        resp = self.session.get(url)
        if not resp:
            return
        data = resp.content

        items = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a class="ch_numz">', '</span>')
        for item in items:
            status =  self.cm.ph.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''<span class="status_.*?">(.*?)</span>''')[0])
            title = self.cm.ph.getSearchGroups(item, '''target="_blank">([^>]+?)<span''')[0]
            id = self.cm.ph.getSearchGroups(item, '''id=(.*?)&''')[0]

            #printDBG("UstreamTV.listItems title: %s" % title)
            #printDBG("UstreamTV.listItems id: %s" % id)
            itemLink = self.MAIN_URL + "stream_original.php?id=" + id

            color = ""
            if "status_idle" in item:
                color = "\c00????00"
            elif "status_unknown" in item:
                color = "\c00??2525"
            elif "status_live" in item:
                color = "\c0000??00"
            title = color + title

            params = dict(cItem)
            params.update({'good_for_fav': False, 'category': nextCategory, 'title': title , 'url': itemLink, 'desc':status})
            self.addDir(params)

    def listCountries(self, cItem, nextCategory):
        printDBG("UstreamTV.listCountries cItem: %s" % cItem)
        url = cItem['url']
        resp = self.session.get(url)
        if not resp:
            return
        data = resp.content
        CountriesMenu = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li class="dropdown-header"', 'class="divider"></li>')[0]
        CountryList = self.cm.ph.getAllItemsBeetwenMarkers(CountriesMenu, ('<a', 'href='), '</a>')
        for country in CountryList:
            link = self.getFullUrl(self.cm.ph.getSearchGroups(country, '''href="([^"]+?)"''')[0])
            title = self.cm.ph.getSearchGroups(country, '''>([^>]+?)<''')[0]
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category': nextCategory, 'title': title , 'url': link})
            self.addDir(params)

    def exploreItem(self, cItem):
        printDBG("UstreamTV.exploreItem cItem: %s" % cItem)

        url = cItem['url']

        resp = self.session.get(url)
        if not resp:
            return
        data = resp.content

        funcs = self.cm.ph.getAllItemsBeetwenMarkers(data, 'eval(function(p,a,c,k,e,d)', '</script>')
        videolink = None
        for func in funcs:
            func = func.replace('</script>', '')
            func = func.replace('eval', 'console.log')

            ret = js_execute(func)
            data = ret['data']

            if 'jdtk=' in data:
                #printDBG("UstreamTV.exploreItem data: %s" % data)
                filename = self.cm.ph.getSearchGroups(data, '''file_name="([^"]+?)"''')[0]
                token = self.cm.ph.getSearchGroups(data, '''jdtk="([^"]+?)"''')[0]
                host = self.cm.ph.getSearchGroups(data, '''host_tmg="([^"]+?)"''')[0]
                adresa = self.cm.ph.getSearchGroups(data, '''adresa="([^"]+?)"''')[0]
                videolink = 'http://' + host + "/" +  filename + "?token=" + token

                import math
                import time

                mytimez = math.floor(int(time.time() * 1000) / 1000)

                l1= "https://cdn.ustream.to/ts_count/%s-tmg.txt?%s" % (adresa, str(mytimez))
                resp = self.session.get(l1)
                if not resp:
                    return
                ts_count = resp.content
                #printDBG("UstreamTV.exploreItem ts_count: %s" % ts_count)

                l2 ="https://cdn.ustream.to/ts_count/%s-sequence.txt?%s" % (adresa, str(mytimez))
                resp = self.session.get(l2)
                if not resp:
                    return
                sequence = resp.content
                #printDBG("UstreamTV.exploreItem sequence: %s" % sequence)

                videolink += "&sequence=" + sequence

                params = dict(cItem)
                params.update({'url': strwithmeta(videolink, {'Referer':cItem['url']})})
                self.addVideo(params)
                break

        #printDBG("UstreamTV.exploreItem videolink: %s" % videolink)

    def getLinksForVideo(self, cItem):
        printDBG("Tele5.getLinksForVideo [%s]" % cItem)
        linksTab = []
        link = cItem['url']

        linksTab.extend(getDirectM3U8Playlist(link, checkExt=True, checkContent=True, sortWithMaxBitrate=999999999))

        return linksTab

    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['q']  = urllib.quote_plus(searchPattern)
        cItem['filters'] = {}
        self.listFilters(cItem, 'category', 'filter_type')

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
        if name is None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'listItems':
            self.listItems(self.currItem, 'exploreItem')
        elif category == 'listCountries':
            self.listCountries(self.currItem, 'listItems')
    # FILTERS
        elif category == 'exploreItem':
            self.exploreItem(self.currItem)

    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORY SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()

        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, UstreamTV(), True)


if __name__=='__main__':
    host = UstreamTV()
    cItem = host.MAIN_CAT_TAB[0]
    print(cItem)