# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################
from Plugins.Extensions.IPTVPlayer.p2p3.UrlParse import urljoin, urlparse
from Plugins.Extensions.IPTVPlayer.p2p3.UrlLib import urllib_quote_plus, urllib_unquote
###################################################
# FOREIGN import
###################################################
import re
###################################################

def GetConfigList():
    optionList = []
    return optionList


def gettytul():
    return 'http://watchwrestling.la/'


class WatchwrestlingUNO(CBaseHostClass):
    def __init__(self):
        CBaseHostClass.__init__(self, {'history': 'watchwrestling.la', 'cookie': 'watchwrestling.uno.cookie'})
        self.MAIN_URL = 'http://watchwrestling.la/'
        self.SRCH_URL = self.getFullUrl('index.php?s=')
        self.DEFAULT_ICON_URL = 'http://i.imgur.com/UsYsZ.png'

        self.MAIN_CAT_TAB = [{'category': 'categories', 'title': _('Categories'), 'url': self.getMainUrl(), 'm1': 'Categories</h3>'},
                             {'category': 'categories', 'title': _('WWE'), 'url': self.getFullUrl('category/wwe/'), 'm1': '>WWE</a>'},
                             {'category': 'live', 'title': _('LIVE 24/7'), 'url': self.getFullUrl('watch-wwe-network-247-live-free/')},
                             {'category': 'list_filters', 'title': _('Replay Shows'), 'url': self.getFullUrl('category/wwe-network/')},
                             {'category': 'list_filters', 'title': _('iMPACT Wrestling'), 'url': self.getFullUrl('category/tna/')},
                             {'category': 'list_filters', 'title': _('RAW'), 'url': self.getFullUrl('category/wwe/raw/')},
                             {'category': 'list_filters', 'title': _('Smackdown'), 'url': self.getFullUrl('category/wwe/smackdown/')},
                             {'category': 'list_filters', 'title': _('Total Divas'), 'url': self.getFullUrl('category/wwe-total-divas/')},
                             {'category': 'list_filters', 'title': _('NXT'), 'url': self.getFullUrl('category/wwe/nxt/')},
                             {'category': 'list_filters', 'title': _('Main Event'), 'url': self.getFullUrl('category/wwe/main-event/')},
                             {'category': 'list_filters', 'title': _('UFC'), 'url': self.getFullUrl('category/ufc/')},
                             {'category': 'categories', 'title': _('Indy'), 'url': self.getFullUrl('category/indy/'), 'm1': '>Indy</a>'},
                             {'category': 'list_filters', 'title': _('NJPW'), 'url': self.getFullUrl('category/njpw/')},
                             {'category': 'list_filters', 'title': _('Others'), 'url': self.getFullUrl('category/wrestling-archives/')},

                             {'category': 'search', 'title': _('Search'), 'search_item': True},
                             {'category': 'search_history', 'title': _('Search history')}
                            ]

        self.SORT_TAB = [{'sort': 'date', 'title': _('DATE')},
                         {'sort': 'views', 'title': _('VIEWS')},
                         {'sort': 'likes', 'title': _('LIKES')},
                         {'sort': 'comments', 'title': _('COMMENTS')}
                        ]
        self.serversCache = []

    def listCategories(self, cItem, nexCategory):
        printDBG("WatchwrestlingUNO.listCategories")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts:
            return

        data = self.cm.ph.getDataBeetwenMarkers(data, cItem['m1'], '</ul>', False)[1]

        if '"sub-menu"' in data:
            params = dict(cItem)
            params.update({'title': _('--All--'), 'category': nexCategory})
            self.addDir(params)

        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)["']''')[0]
            if url == '':
                continue
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'title': title, 'url': self.getFullUrl(url), 'category': nexCategory})
            self.addDir(params)

    def listFilters(self, cItem, category):
        printDBG("WatchwrestlingUNO.listFilters")
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(self.SORT_TAB, cItem)

    def listMovies(self, cItem, nextCategory):
        printDBG("WatchwrestlingUNO.listMovies")
        url = cItem['url']
        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%d/' % page
        if '?' in url:
            url += '&'
        else:
            url += '?'
        url += 'orderby=%s' % cItem['sort']

        sts, data = self.cm.getPage(url)
        if not sts:
            return

        if ('/page/%d/' % (page + 1)) in data:
            nextPage = True
        else:
            nextPage = False

        posts = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div id="post-', '</div>')
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="data"', '</div>')
        for idx in range(len(posts)):
            item = posts[idx]
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title = self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0]
            if title == '':
                title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]

            if len(data) < len(posts):
                printDBG("FIX ME: data_len[%d] posts_len[%d]" % (len(data), len(posts)))
                desc = ''
            else:
                desc = []
                tmp = [self.cm.ph.getDataBeetwenMarkers(data[idx], '<time', '</time>')[1]]
                tmp.extend(self.cm.ph.getAllItemsBeetwenMarkers(data[idx], '<i', '</span>'))
                for item in tmp:
                    item = self.cleanHtmlStr(item)
                    if item != '':
                        desc.append(item)
                desc = ' | '.join(desc)
            params = dict(cItem)
            params.update({'good_for_fav': True, 'category': nextCategory, 'title': self.cleanHtmlStr(title), 'url': self.getFullUrl(url), 'desc': desc, 'icon': self.getFullIconUrl(icon)})
            if '/category/' not in url:
                params['category'] = nextCategory
            self.addDir(params)

        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title': _('Next page'), 'page': page + 1})
            self.addDir(params)

    def listServers(self, cItem, nextCategory):
        printDBG("WatchwrestlingUNO.listServers [%s]" % cItem)
        sts, data = self.cm.getPage(cItem['url'])
        if not sts:
            return

        baseUrl = self.cm.ph.getSearchGroups(data, '''<base[^>]+?href=["'](https?://[^"^']+?)['"]''')[0]

        self.serversCache = []
        matchObj = re.compile('href="([^"]+?)"[^>]*?>([^>]+?)</a>')
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="entry-content rich-content">', '<p class="no-break">', False)[1]
        if not tmp:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="entry-content rich-content">', '<div id="extras">', False)[1]
        data = tmp
        sp = '<span style="font-size:'
        if sp in data:
            data = data.split(sp)
            sp = '</span>'
        else:
            data = data.split('color:')
            sp = '</p>'

        if len(data):
            del data[0]
        printDBG(data)
        for item in data:
            sts, serverName = self.cm.ph.getDataBeetwenMarkers(item, '>', sp, False)
            if not sts:
                continue
            parts = matchObj.findall(item)
            partsTab = []
            for part in parts:
                url = urljoin(baseUrl, part[0])
                title = cItem['title'] + '[%s]' % part[1]
                partsTab.append({'title': title, 'url': strwithmeta(url, {'live': True, 'Referer': cItem['url']})})
            if len(partsTab):
                params = dict(cItem)
                params.update({'good_for_fav': False, 'category': nextCategory, 'title': serverName, 'part_idx': len(self.serversCache)})
                self.addDir(params)
                self.serversCache.append(partsTab)

    def listParts(self, cItem):
        printDBG("WatchwrestlingUNO.listParts [%s]" % cItem)
        partIdx = cItem['part_idx']
        self.listsTab(self.serversCache[partIdx], cItem, 'video')

    def listLiveStreams(self, cItem):
        printDBG("WatchwrestlingUNO.listLiveStreams [%s]" % cItem)
        sts, data = self.cm.getPage(cItem['url'])
        if not sts:
            return

        baseUrl = self.cm.ph.getSearchGroups(data, '''<base[^>]+?href=["'](https?://[^"^']+?)['"]''')[0]
        sp = '<div style="text-align: center;">'
        data = self.cm.ph.getDataBeetwenMarkers(data, '<p style="text-align: center;"><a', '</p>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>', True)
        for item in data:
            title = self.cleanHtmlStr(item)
            url = urljoin(baseUrl, self.cm.ph.getSearchGroups(item, '''href=["']([^"^']+?)['"]''')[0])
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title': title, 'url': strwithmeta(url, {'live': True, 'Referer': cItem['url']}), 'live': True})
            self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib_quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = self.SRCH_URL + searchPattern
        cItem['sort'] = searchType
        self.listMovies(cItem, 'list_server')

    def _clearData(self, data):
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        return data

    def getLinksForVideo(self, cItem):
        printDBG("WatchwrestlingUNO.getLinksForVideo [%s]" % cItem)
        urlTab = []
        live = cItem.get('live', False)
        if live:
            return [{'name': cItem['title'], 'url':cItem['url'], 'need_resolve':1}]

        url = strwithmeta(cItem['url'])
        referer = url.meta.get('Referer', '')
        if 1 != self.up.checkHostSupport(url):
            tries = 0
            while tries < 3:
                sts, data = self.cm.getPage(url, {'header': {'Referer': referer, 'User-Agent': 'Mozilla/5.0'}})
                if not sts:
                    return urlTab
                data = data.replace('// -->', '')
                data = self._clearData(data)
                #printDBG(data)
                if 'eval(unescape' in data:
                    data = urllib_unquote(self.cm.ph.getSearchGroups(data, '''eval\(unescape\(['"]([^"^']+?)['"]''')[0])
                url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=['"]([^"^']+?)['"]''', 1, True)[0]
                if '/cgi-bin/' in url:
                    referer = cItem['url']
                else:
                    break
                tries += 1
        url = strwithmeta(url)
        url.meta['Referer'] = referer
        url.meta['live'] = cItem.get('live', False)

        urlTab.append({'name': cItem['title'], 'url': url, 'need_resolve': 1})
        return urlTab

    def getVideoLinks(self, baseUrl):
        printDBG("WatchwrestlingUNO.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        url = strwithmeta(baseUrl)
        if url.meta.get('live'):
            urlTab = self.up.getAutoDetectedStreamLink(url)
        else:
            urlTab = self.up.getVideoLinkExt(url)
        return urlTab

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('handleService start')

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG("handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category))
        self.currList = []

    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name': 'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_filters')
        elif category == 'list_filters':
            self.listFilters(self.currItem, 'list_movies')
    #MOVIES
        elif category == 'list_movies':
            self.listMovies(self.currItem, 'list_server')
        elif category == 'list_server':
            self.listServers(self.currItem, 'list_parts')
        elif category == 'list_parts':
            self.listParts(self.currItem)
    #LIVE
        elif category == 'live':
            self.listLiveStreams(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item': False, 'name': 'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name': 'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()

        CBaseHostClass.endHandleService(self, index, refresh)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, WatchwrestlingUNO(), True, [])

    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append((_("DATE"), "date"))
        searchTypesOptions.append((_("VIEWS"), "views"))
        searchTypesOptions.append((_("LIKES"), "likes"))
        searchTypesOptions.append((_("COMMENTS"), "comments"))
        return searchTypesOptions
