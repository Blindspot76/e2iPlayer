# -*- coding: utf-8 -*-
# Blindspot - 2021.08.21
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, getConfigListEntry
try:
    import json
except Exception:
    import simplejson as json
############################################

###################################################
# E2 GUI COMMPONENTS
###################################################
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.skylinewebcams_lang = ConfigSelection(default="en", choices=[("en", "en"), ("it", "it"), ("es", "es"), ("de", "de"), ("fr", "fr"),
                                                                                           ("el", "el"), ("hr", "hr"), ("sl", "sl"), ("zh", "zh")])


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Language:"), config.plugins.iptvplayer.skylinewebcams_lang))
    return optionList

###################################################


class WkylinewebcamsComApi:
    MAIN_URL = 'https://www.skylinewebcams.com/'

    def __init__(self):
        self.COOKIE_FILE = GetCookieDir('skylinewebcamscom.cookie')
        self.cm = common()
        self.up = urlparser()
        self.http_params = {}
        self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        self.cacheList = {}
        self.mainMenuCache = {}
        self.lang = config.plugins.iptvplayer.skylinewebcams_lang.value
    
    def getMainMenu(self, cItem):
        printDBG("WkylinewebcamsCom.getMainMenu")
        STATIC_TAB = [{'title': _('NEW'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/new-livecams.html', 'cat': 'list_cams'},
                      {'title': _('City Views'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/city-cams.html', 'cat': 'list_cams'},
                      {'title': _('Top Live Cams'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/top-live-cams.html', 'cat': 'list_cams'},
                      {'title': _('Beaches'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/beach-cams.html', 'cat': 'list_cams'},
                      {'title': _('Landscapes'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/nature-mountain-cams.html', 'cat': 'list_cams'},
                      {'title': _('Landscapes'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/nature-mountain-cams.html', 'cat': 'list_cams'},
                      {'title': _('Marinas'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/seaport-cams.html', 'cat': 'list_cams'},
                      {'title': _('UNESCO'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/unesco-cams.html', 'cat': 'list_cams'},
                      {'title': _('Ski slopes'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/ski-cams.html', 'cat': 'list_cams'},
                      {'title': _('Animals'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/animals-cams.html', 'cat': 'list_cams'},
                      {'title': _('Volcanoes'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/volcanoes-cams.html', 'cat': 'list_cams'},
                      {'title': _('Lakes'), 'url': "https://www.skylinewebcams.com/" + self.lang + '/live-cams-category/lake-cams.html', 'cat': 'list_cams'}
                      ]

        list = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts:
            return list
        data = self.cm.ph.getDataBeetwenMarkers(data, 'id="main-menu', ' lang')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li class="dropdown">', '</ul>')
        for idx in range(2):
            if idx >= len(data):
                continue
            catData = data[idx]
            catData = catData.split('<ul ')
            if len(catData) < 2:
                continue
            catTitle = self.cleanHtmlStr(catData[0])
            catUrl = self.cm.ph.getSearchGroups(catData[0], '''<a[^>]*?href="([^"]+?)"''', 1, True)[0]
            catData = self.cm.ph.getAllItemsBeetwenMarkers(catData[-1], '<a ', '</a>')
            tab = []
            for item in catData:
                url = self.cm.ph.getSearchGroups(item, '''href="([^"]+?)"''', 1, True)[0]
                title = self.cleanHtmlStr(item)
                if url != '' and title != '':
                    tab.append({'url': self.getFullUrl(url), 'title': title, 'cat': 'list_cams'}) #explore_item
            if len(tab):
                tab.insert(0, {'url': self.getFullUrl(catUrl), 'title': _('All'), 'cat': 'list_cams'})
                self.mainMenuCache[idx] = tab
                params = dict(cItem)
                params.update({'title': catTitle, 'cat': 'list_main_category', 'idx': idx})
                list.append(params)

        for item in STATIC_TAB:
                params = dict(cItem)
                params.update(item)
                list.insert(0, params)
        return list
    
    def listCams(self, cItem):
        printDBG("WkylinewebcamsCom.listCams")
        list = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts:
            return list
        cam = self.cm.ph.getDataBeetwenMarkers(data, '/h1><hr></div><a href="', '</div></div></div><div class="footer"') [1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(cam, '><a href="', '</p></div></a>')
        for item in data:
            url = "https://www.skylinewebcams.com/" + self.cm.ph.getDataBeetwenMarkers(item, '><a href="', '"', False) [1]
            icon = self.cm.ph.getDataBeetwenMarkers(item, '<img src="', '"', False) [1]
            title = self.cm.ph.getDataBeetwenMarkers(item, 'alt="', '"', False) [1]
            desc = self.cm.ph.getDataBeetwenMarkers(item, 'class="subt">', '</p>', False) [1]
            params = dict(cItem)
            params.update({'title': title, 'url': url, 'icon': icon, 'desc': desc, 'type': 'video'})
            list.append(params)
        return list

    def getChannelsList(self, cItem):
        printDBG("WkylinewebcamsCom.getChannelsList")
        list = []
        cat = cItem.get('cat', None)
        lang = config.plugins.iptvplayer.skylinewebcams_lang.value
        self.lang = lang
        if None == cat:
            cItem = dict(cItem)
            cItem['url'] = self.MAIN_URL + lang + '.html'
            return self.getMainMenu(cItem)
        elif 'list_main_category' == cat:
            tab = self.mainMenuCache.get(cItem['idx'], [])
            for item in tab:
                params = dict(cItem)
                params.update(item)
                list.append(params)
        elif 'list_cams' == cat:
            return self.listCams(cItem)

        return list

    def getVideoLink(self, cItem):
        printDBG("WkylinewebcamsCom.getVideoLink")
        urlsTab = []
        sts, data = self.cm.getPage(cItem['url'])
        if not sts:
            return urlsTab
        id = self.cm.ph.getDataBeetwenMarkers(data, "source:'livee.m3u8?a=", "',", False) [1]
        url = "https://hd-auth.skylinewebcams.com/live.m3u8?a=" + id
        urlsTab.append({'name': cItem['title'], 'url': url})
        return urlsTab
