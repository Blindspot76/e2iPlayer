# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import urllib
###################################################

def gettytul():
    return 'http://szene-streamz.com/'

class Kkiste(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'szenestreamz.com', 'cookie':'szenestreamz.com.cookie'})
        self.DEFAULT_ICON_URL = 'http://www.szene-streamz.com/Original_Header.png'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'http://szene-streamz.com/'
        self.cacheLinks   = {}
        self.cacheFilters  = {}
        self.cacheFiltersKeys = []
        self.MOVIES_GENRE_CAT = []
        self.SERIES_GENRE_CAT = []
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.MAIN_CAT_TAB = [{'category':'list_items',         'title': _('Movies'),        'url':self.getFullUrl('publ/')                                },
                             {'category':'list_cats',          'title': _('Genre selection')+': '+_('Movies'), 'url':self.getFullUrl('publ/')             },
                             {'category':'list_items',         'title': _('Series'),            'url':self.getFullUrl('load/')                            },
                             {'category':'list_cats',          'title': _('Genre selection')+': '+_('Series'), 'url':self.getFullUrl('load/')             },
                             {'category':'search',             'title': _('Search'), 'search_item':True,},
                             {'category':'search_history',     'title': _('Search history'),            } 
                            ]
        

    def getPage(self, url, addParams = {}, post_data = None):
        if addParams == {}:
            addParams = dict(self.defaultParams)
        
        return self.cm.getPage(url, addParams, post_data)
        
    def listsCats(self, cItem, nextCat):
        printDBG("hostszenestreamz.listsCats |%s|" % cItem)
        
        url  = cItem['url']

        if '/publ/' in url: cats = self.MOVIES_GENRE_CAT
        else: cats = self.SERIES_GENRE_CAT

        if cats == []:
            sts, data = self.getPage(url)
            if not sts: return
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a class="CatInf"', '</a>')
            for item in data:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
                title = self.cm.ph.getSearchGroups(item, '''class="CatNameInf">([^<]+)<''')[0]
                if title.startswith('S-'): title = title.replace('S-','')
                cats.append({'category':'list_items', 'title':title, 'url':url})

        self.listsTab(cats, nextCat)
        
    def listItems(self, cItem, nextCategory, post_data = None):
        printDBG("hostszenestreamz.listItems |%s|" % cItem)
        
        url  = cItem['url']
        page = cItem.get('page', 1)
        
        sts, data = self.getPage(url, {}, post_data)

        if not sts: return

        pagedata = self.cm.ph.getAllItemsBeetwenMarkers(data, '<span class="pagesBlockuz1">', '<span class="numShown73">')
        
        if pagedata == []: 
            nextPage = False
        else: 
            nextPage = True
        
        urls = []
        titles = []
        genres = []
        ldata = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a class="newstitl entryLink"', '</a>')
        for item in ldata:
            url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0])
            urls.append(url)
            title = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''href=['"][^'^"]+['"]>(.+)</''')[0])
            titles.append(title)

        gdata = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="MesWrapBlogDet"', '</a>')
        for item in gdata:
            if '<script>' in item: continue
            genre = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, '''href=['"][^'^"]+['"]>([^<]+)</''')[0])
            genre = genre.replace('Genre: ','')
            if genre.startswith('S-'): genre = genre.replace('S-','')
            genres.append(genre)

        index = 0
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="ImgWrapNews">', '</div>')
        for item in data:
            icon = self.getFullIconUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
            url = urls[index]
            title = titles[index]
            genre = genres[index]
            desc = ''
            if genre != '':
                desc = genre
            params = dict(cItem)
            params.update({'good_for_fav':True, 'category':nextCategory, 'title':title, 'url':url, 'desc':desc, 'icon':icon})
            self.addDir(params)
            index += 1
        
        if nextPage:
            for item in pagedata:
                thispage = self.cm.ph.getAllItemsBeetwenMarkers(item, 'class="swchItem', '</span>')
                current_page = False
                url = ''
                for pitem in thispage:
                    if 'swchItemA' in pitem:
                        current_page = True
                    elif current_page:
                        url = self.getFullUrl(self.cm.ph.getSearchGroups(pitem, '''href=['"]([^'^"]+?)['"]''')[0])
                        break

                if url != '':
                    url = url.replace('&amp;','&')
                    params = dict(cItem)
                    params.update({'good_for_fav':False, 'title':_('Next page'), 'page':page+1, 'url':url})
                    self.addDir(params)
        
    def exploreItem(self, cItem):
        printDBG("hostszenestreamz.exploreItem")
        
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        if '<div class="noEntry"' in data:
            return

        title = cItem.get('title','')

        trailerurl = ''
        trailerdata =  self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe src=', '</iframe>')
        for item in trailerdata:
            if 'youtube' in item:
                trailerurl = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0])
                if trailerurl.endswith('/embed/'): trailerurl = ''
                break

        plot = ''
        plotdata = self.cm.ph.getAllItemsBeetwenMarkers(data, '<p><b>', '</b></p>', withMarkers=False)
        for item in plotdata:
            item = item.replace('\n','')
            item = item.replace('\r','')
            plot = item

        desc = cItem.get('desc','')
        url = cItem.get('url','')
        icon = cItem.get('icon','')

        if plot != '':
            if desc != '':
                desc = desc + '[/br]'
            desc = desc + plot

        if trailerurl != '':
            trailerurl = self.getFullUrl(trailerurl)
            trailerurl = strwithmeta(trailerurl, {'Referer':url})
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title':'%s %s' % (title, '[Trailer]'), 'url':trailerurl, 'desc':desc})
            self.addVideo(params)

        if '/publ/' in url:
            links = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="inner', '</fieldset>')

            self.cacheLinks  = {}
            linksKey = cItem['url']
            self.cacheLinks[linksKey] = []
            params = dict(cItem)
            url = ''
            for item in links:
                item = item.replace('\n','')
                item = item.replace('\r','')
                url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                name = self.cm.ph.getSearchGroups(url, '''//([^/]+)/''')[0]
                nameparts = name.split('.')
                if len(nameparts) != 2:
                    name = nameparts[-2] + '.' + nameparts[-1]
                url = self.getFullUrl(url)
                url = strwithmeta(url, {'Referer':linksKey})
                self.cacheLinks[linksKey].append({'name':name, 'url':url, 'need_resolve':1})

            if self.cacheLinks != {}:
                params = dict(cItem)
                params.update({'good_for_fav': False, 'links_key':linksKey})
                params.update({'good_for_fav': False, 'title':'%s' % title, 'url':linksKey, 'desc':desc})
                self.addVideo(params)
        else:
            seasons = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="spoiler', '</fieldset>')
            sKey = 0
            self.cacheSeasons = {}
            onlyEpisodes = False
            episodesList = []
            eNum = 1
            for item in seasons:
                item = item.replace('\n','')
                item = item.replace('\r','')
                season = self.cm.ph.getSearchGroups(item, '''STAFFEL ([^<]+)<''')[0]
                if len(season):
                    if season.startswith('0'): season = season.replace('0','')
                    episodesList = []
                    links = self.cm.ph.getAllItemsBeetwenMarkers(item, '<a href="', '</a>')
                    eNum = 1
                    for litem in links:
                        url = self.cm.ph.getSearchGroups(litem, '''href=['"]([^'^"]+?)['"]''')[0]
                        url = strwithmeta(url, {'Referer':cItem['url']})
                        episode = str(eNum)
                        etitle = '%s s%se%s' % (cItem['title'], season.zfill(2), episode.zfill(2))
                        params = {'title':etitle, 'url':url, 'prev_url':cItem['url']}
                        episodesList.append(params)
                        eNum += 1

                    if len(episodesList):
                        self.cacheSeasons[sKey] = episodesList

                    params = dict(cItem)
                    params.update({'good_for_fav':True, 'category':'list_episodes', 'title':title + ' ' + _('Season %s') % season, 'url':url, 'desc':desc, 'icon':icon, 's_key':sKey})
                    self.addDir(params)
                    sKey += 1
                else:
                    onlyEpisodes = True
                    season = '1'
                    url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                    url = strwithmeta(url, {'Referer':cItem['url']})
                    episode = str(eNum)
                    etitle = '%s s%se%s' % (cItem['title'], season.zfill(2), episode.zfill(2))
                    params = {'title':etitle, 'url':url, 'prev_url':cItem['url']}
                    episodesList.append(params)
                    eNum += 1

            if onlyEpisodes:
                if len(episodesList):
                    self.cacheSeasons[sKey] = episodesList

                params = dict(cItem)
                params.update({'good_for_fav':True, 'category':'list_episodes', 'title':title + ' ' + _('Season %s') % season, 'url':url, 'desc':desc, 'icon':icon, 's_key':sKey})
                self.addDir(params)

    def listEpisodes(self, cItem):
        printDBG("hostszenestreamz.listEpisodes")
        
        sKey = cItem.get('s_key', -1)
        episodesList = self.cacheSeasons.get(sKey, [])
        
        for item in episodesList:
            params = dict(cItem)
            params.update(item)
            params.update({'good_for_fav': False})
            self.addVideo(params)

    def getVideoLinks(self, videoUrl):
        printDBG("hostszenestreamz.getVideoLinks [%s]" % videoUrl)
        videoUrl = strwithmeta(videoUrl)
        urlTab = []
        
        # mark requested link as used one
        if len(self.cacheLinks):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
                        break
                        
        sts, data = self.getPage(videoUrl)
        if not sts: return []
        
        if self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        
        return urlTab
        
    def getLinksForVideo(self, cItem):
        printDBG("szenestreamz.getLinksForVideo [%s]" % cItem)
        url = cItem.get('url', '')
        if 1 == self.up.checkHostSupport(url):
            return self.up.getVideoLinkExt(url)
        
        key = cItem.get('links_key', '')
        return self.cacheLinks.get(key, [])
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("hostszenestreamz.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        post_data = { 'query':urllib.unquote(searchPattern), 'sfSbm':'', 'a':'2' }
        cItem = dict(cItem)
        cItem['url'] = self.getFullUrl('/publ/')
        self.listItems(cItem, 'explore_item', post_data)
        
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('hostszenestreamz.handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'list_cats':
            self.listsCats(self.currItem, {'name':'category'})
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
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
        CHostBase.__init__(self, Kkiste(), True, [])

