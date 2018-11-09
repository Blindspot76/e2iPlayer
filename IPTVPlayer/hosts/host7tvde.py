# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, MergeDicts
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
###################################################

###################################################
# FOREIGN import
###################################################
import urllib
from hashlib import sha1, sha256
from datetime import timedelta
###################################################

def gettytul():
    return 'https://7tv.de/'

class C7tvDe(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'7tv.de', 'cookie':'7tv.de.cookie'})

        self.HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        self.defaultParams = {'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

        self.MAIN_URL    = 'https://www.7tv.de/'
        self.DEFAULT_ICON_URL = 'https://s.p7s1.io/xfiles/7tv/android-icon-192x192.png'

        self.cacheLinks = {}
        self.cacheChannels = []
        self.cacheABC = []

    def getPage(self, baseUrl, addParams={}, post_data=None):
        if addParams == {}: addParams = dict(self.defaultParams)
        return self.cm.getPage(baseUrl, addParams, post_data)

    def listMain(self, cItem, nextCategory):
        printDBG("C7tvDe.listMain")
        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])

        MAIN_CAT_TAB = [{'category':'explore_item',   'title': 'Home',            'url':self.getMainUrl()},
                        {'category':'channels',       'title': 'Mediathek',       'url':self.getFullUrl('/mediathek')},
                        {'category':'search',         'title': _('Search'),       'search_item':True       },
                        {'category':'search_history', 'title': _('Search history'),                        }]
        self.listsTab(MAIN_CAT_TAB, cItem)

    def listChannels(self, cItem, nextCategory):
        printDBG("listChannels")
        if not self.cacheChannels or not self.cacheABC:
            sts, data = self.getPage(cItem['url'])
            if not sts: return

            tmp = ph.find(data, ('<div', '>', 'filterAZ'), ('<div', '>', 'filter-search'), flags=0)[1]
            tmp = ph.findall(tmp, ('<a', '>'), '</a>', flags=0)
            for item in tmp:
                item = ph.clean_html(item)
                self.cacheABC.append({'title':item, 'f_letter':item})

            tmp = ph.find(data, ('<div', '>', 'filterCategorie'), ('<button', '>', 'next'), flags=0)[1]
            tmp = ph.find(tmp, ('<a', '>', 'selected'), ('<a', '>', 'selected'))[1]
            tmp = ph.findall(tmp, ('<a', '>'), '</a>', flags=0)
            for item in tmp:
                item = ph.clean_html(item)
                self.cacheChannels.append({'title':item, 'f_channel':item})

        self.listsTab(self.cacheChannels, MergeDicts(cItem, {'category':nextCategory}))

    def listABC(self, cItem, nextCategory):
        printDBG("listABC")
        self.listsTab(self.cacheABC, MergeDicts(cItem, {'category':nextCategory}))

    def getAPIUrl(self, baseUrl, query):
        url = 'https://magellan-api.7tv.de/' + baseUrl
        url += query
        url += '&queryhash=' + sha256(query).hexdigest()
        return url + '&initialcv=browser-0b546aff762ba75475aa-1'

    def listItems(self, cItem, nextCategory):
        printDBG("listItems")
        cursor = cItem.get('f_cursor')
        cursor = '%22' + cursor + '%22' if cursor else 'null'
        query = 'operationName=&query=%20query%20QueryItems(%24domain%3A%20String!%2C%20%24elementId%3A%20String!%2C%20%24channelContext%3A%20String%2C%20%24groupId%3A%20String%2C%20%24cursor%3A%20String%2C%20%24filter%3A%20FilterStateInputType%2C%20%24limit%3A%20Int%2C%20%24debug%3A%20Boolean!%2C%20%24authentication%3A%20AuthenticationInput)%20%7B%20site(domain%3A%20%24domain%2C%20authentication%3A%20%24authentication)%20%7B%20items(element%3A%20%24elementId%2C%20channelContext%3A%20%24channelContext%2C%20group%3A%20%24groupId%2C%20cursor%3A%20%24cursor%2C%20filter%3A%20%24filter%2C%20limit%3A%20%24limit)%20%7B%20id%20title%20total%20cursor%20items%20%7B%20...fContentElementItem%20%7D%20debug%20%40include(if%3A%20%24debug)%20%7B%20...fContentDebugInfo%20%7D%20%7D%20%7D%20%7D%20%0Afragment%20fContentElementItem%20on%20ContentElementItem%20%7B%20id%20url%20info%20branding%20%7B%20...fBrand%20%7D%20body%20config%20headline%20contentType%20channel%20%7B%20...fChannelInfo%20%7D%20site%20image%20videoType%20orientation%20date%20duration%20flags%20genres%20valid%20%7B%20from%20to%20%7D%20epg%20%7B%20episode%20%7B%20...fEpisode%20%7D%20season%20%7B%20...fSeason%20%7D%20duration%20nextEpgInfo%20%7B%20...fEpgInfo%20%7D%20%7D%20debug%20%40include(if%3A%20%24debug)%20%7B%20...fContentDebugInfo%20%7D%20%7D%20%0Afragment%20fBrand%20on%20Brand%20%7B%20id%2C%20name%20%7D%20%0Afragment%20fChannelInfo%20on%20ChannelInfo%20%7B%20title%20shortName%20cssId%20cmsId%20%7D%20%0Afragment%20fEpisode%20on%20Episode%20%7B%20number%20%7D%20%0Afragment%20fSeason%20on%20Season%20%7B%20number%20%7D%20%0Afragment%20fEpgInfo%20on%20EpgInfo%20%7B%20time%20endTime%20primetime%20%7D%20%0Afragment%20fContentDebugInfo%20on%20ContentDebugInfo%20%7B%20source%20transformations%20%7B%20description%20%7D%20%7D%20&variables=%7B%22channelContext%22%3Anull%2C%22cursor%22%3A'
        query+= cursor + '%2C%22debug%22%3Afalse%2C%22domain%22%3A%227tv.de%22%2C%22elementId%22%3A%22mediathek%3Apage%22%2C%22filter%22%3A%7B%22categories%22%3A%5B%7B%22name%22%3A%22brand%22%2C%22value%22%3A%22'
        query+= urllib.quote(cItem['f_channel']) + '%22%7D%5D%2C%22search%22%3Anull%2C%22term%22%3A%22'
        query+= urllib.quote(cItem['f_letter']) + '%22%7D%2C%22groupId%22%3Anull%2C%22limit%22%3A18%7D'

        url = self.getAPIUrl('pagination/7tv.de/mediathek:page/graphql?', query)
        sts, data = self.getPage(url)
        if not sts: return
        try:
            data = json_loads(data)['data']['site']['items']
            cursor = data.get('cursor')
            self.doListItems(cItem, nextCategory, data['items'], cursor)
        except Exception:
            printExc()

    def doListItems(self, cItem, nextCategory, data, cursor):
        for item in data:
            params = self.mapItem(cItem, nextCategory, item)
            if not params:
                continue
            if params['f_type'] == 'video':
                self.addVideo(params)
            else:
                params.update({'category':nextCategory})
                self.addDir(params)

        if cursor:
            self.addDir(MergeDicts(cItem, {'good_for_fav':False, 'title':_('Next page'), 'f_cursor':cursor}))

    def mapItem(self, cItem, nextCategory, item):
        type = item['contentType']
        url = self.getFullUrl(item['url'])
        title = ph.clean_html(item['headline'])

        icon = item.get('image')
        icon = self.getFullIconUrl(icon + '/profile:mag-300x170') if icon else ''
        if type == None: 
            printDBG("ITEM TYPE IS NONE: %s" % item)
            return None

        desc = [type]
        try: desc.append( '' + item['branding']['name'] )
        except Exception: pass

        try: desc.append( '' + item['channel']['title'] )
        except Exception: pass

        tmp = item.get('videoType')
        if tmp: desc.append(ph.clean_html(tmp))

        tmp = item.get('orientation')
        if tmp: desc.append(ph.clean_html(tmp))

        desc = [' | '.join(desc)]

        tmp = item.get('info')
        if tmp: desc.append(ph.clean_html(tmp))

        return MergeDicts(cItem, {'good_for_fav':True, 'title':title, 'url':url, 'icon':icon, 'f_type':type, 'desc':'[/br]'.join(desc)})

    def exploreItem(self, cItem, nextCategory):
        printDBG("C7tvDe.exploreItem")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])
        
        data = ph.find(data, ('<script', '>', 'state'), '</script>', flags=0)[1]
        try: 
            data = json_loads(data)['views']['default']['content']['areas'][0]['containers']
            for cData in data:
                cData = cData['elements'][0]
                gTitle = cData['title']
                if not cData['groups']: continue
                for sSection in cData['groups']:
                    sTitle = sSection['title']
                    if not sTitle: sTitle = gTitle
                    if sTitle: sTitle = '%s (%s)' % (sTitle, sSection['total'])
                    subItems = []
                    for item in sSection['items']:
                        params = self.mapItem(cItem, nextCategory, item)
                        if not params: continue
                        if params['f_type'] == 'video': params['type'] = 'video'
                        else: params['category'] = nextCategory
                        subItems.append(params)
                    if len(subItems):
                        if sTitle:
                            self.addDir(MergeDicts(cItem, {'good_for_fav':False, 'category':'sub_items', 'sub_items':subItems, 'title':sTitle}))
                        else:
                            self.currList.extend(subItems)
        except Exception:
            printExc()

    def listSearchResult(self, cItem, searchPattern, searchType):
        if searchType == 'videos':
            cItem = MergeDicts(cItem, {'category':'search_next', 'f_pattern':searchPattern})
            self.listSearchResultNext(cItem, 'explore_item')
        else:
            cItem = MergeDicts(cItem, {'category':'list_items', 'f_letter':searchPattern, 'f_channel':'Alle'})
            self.listItems(cItem, 'explore_item')

    def listSearchResultNext(self, cItem, nextCategory):
        cursor = cItem.get('f_cursor')
        cursor = '%22' + cursor + '%22' if cursor else 'null'
        query = 'operationName=&query=%20query%20SearchQuery(%24domain%3A%20String!%2C%20%24filter%3A%20String%2C%20%24query%3A%20String%2C%20%24limit%3A%20Int%2C%20%24cursor%3A%20String)%20%7B%20site(domain%3A%20%24domain)%20%7B%20search(query%3A%20%24query%2C%20filter%3A%20%24filter%2C%20limit%3A%20%24limit%2C%20cursor%3A%20%24cursor)%20%7B%20total%20filter%20filtersHits%20%7B%20name%20hits%20%7D%20offset%20cursor%20results%20%7B%20...fTeaserItem%20%7D%20%7D%20%7D%20%7D%0Afragment%20fTeaserItem%20on%20TeaserItem%20%7B%20id%20url%20info%20headline%20contentType%20channel%20%7B%20...fChannelInfo%20%7D%20branding%20%7B%20...fBrand%20%7D%20site%20image%20videoType%20orientation%20date%20flags%20valid%20%7B%20from%20to%20%7D%20epg%20%7B%20episode%20%7B%20...fEpisode%20%7D%20season%20%7B%20...fSeason%20%7D%20duration%20nextEpgInfo%20%7B%20...fEpgInfo%20%7D%20%7D%20%7D%20%0Afragment%20fChannelInfo%20on%20ChannelInfo%20%7B%20title%20shortName%20cssId%20cmsId%20%7D%20%0Afragment%20fBrand%20on%20Brand%20%7B%20id%2C%20name%20%7D%20%0Afragment%20fEpisode%20on%20Episode%20%7B%20number%20%7D%20%0Afragment%20fSeason%20on%20Season%20%7B%20number%20%7D%20%0Afragment%20fEpgInfo%20on%20EpgInfo%20%7B%20time%20endTime%20primetime%20%7D%20&variables=%7B%22cursor%22%3A'
        query+= cursor + '%2C%22domain%22%3A%227tv.de%22%2C%22filter%22%3Anull%2C%22limit%22%3A33%2C%22query%22%3A%22'
        query+= urllib.quote(cItem['f_pattern']) + '%22%7D'

        url = self.getAPIUrl('graphql?', query)
        sts, data = self.getPage(url)
        if not sts: return
        try:
            data = json_loads(data)['data']['site']['search']
            cursor = data.get('cursor')
            self.doListItems(cItem, nextCategory, data['results'], cursor)
        except Exception:
            printExc()

    def getLinksForVideo(self, cItem, source_id=None):
        linksTab = []

        sts, data = self.getPage(cItem['url'])
        if not sts: return
        client_location = self.cm.meta['url']
        data = ph.find(data, ('<script', '>', 'state'), '</script>', flags=0)[1]
        try: 
            data = json_loads(json_loads(data)['views']['default']['page']['contentResource'])[0]
        except Exception:
            printExc()

        try:
            drm = data.get('drm')
            if drm:
                SetIPTVPlayerLastHostError(_('Link protected with DRM.'))
            video_id = data['id']
        except Exception:
            printExc()
            return []

        #dashLinks = self.doGetLinks(video_id, client_location, 'application/dash+xml')
        try:
            for it in  (False, True):
                hlsLinks  = self.doGetLinks(video_id, client_location, 'application/x-mpegURL', it)
                if hlsLinks:
                    linksTab.extend( getDirectM3U8Playlist(hlsLinks[0]['url'], checkExt=True, checkContent=True, sortWithMaxBitrate=999999999) )
                    break

            for it in  (True, False):
                mp4Links  = self.doGetLinks(video_id, client_location, 'video/mp4', it)
                for item in mp4Links:
                    if item['mimetype'] == 'video/mp4':
                        linksTab.append({'name':'[MP4] bitrate: %s' % item['bitrate'], 'url':item['url'], 'bitrate':item['bitrate']})
                if mp4Links:
                    break
            if not mp4Links and drm:
                return []
            linksTab.sort(reverse=True, key=lambda k: int(k['bitrate']))
        except Exception:
            printExc()
            
        return linksTab

    def doGetLinks(self, video_id, client_location, mimetype, web=False):
        linksTab = []
        try:
            if web:
                access_token = 'h''b''b''t''v'  
                salt = '0''1''r''e''e''6''e''L''e''i''w''i''u''m''i''e''7''i''e''V''8''p''a''h''g''e''i''T''u''i''3''B'
                client_name='h''b''b''t''v'
            else:
              access_token = 'seventv-web'  
              salt = '01!8d8F_)r9]4s[qeuXfP%'
              client_name = ''

            json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s?access_token=%s&client_location=%s&client_name=%s' % (video_id, access_token, client_location, client_name)
            sts, json_data = self.getPage(json_url)
            if not sts: return []
            printDBG(json_data)
            printDBG("++++++++++++++++++++")
            json_data = json_loads(json_data) 

            source_id = -1
            for stream in json_data['sources']:
                if  stream['mimetype'] == mimetype and int(source_id) <  int(stream['id']):
                    source_id = stream['id']

            if source_id < 0:
                return []

            client_id_1 = salt[:2] + sha1(''.join([str(video_id), salt, access_token, client_location, salt, client_name]).encode('utf-8')).hexdigest()

            json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s/sources?access_token=%s&client_location=%s&client_name=%s&client_id=%s' % (video_id, access_token, client_location, client_name, client_id_1)            
            sts, json_data = self.getPage(json_url)
            if not sts: return []
            printDBG(json_data)
            printDBG("++++++++++++++++++++")
            json_data = json_loads(json_data) 
            server_id = json_data['server_id']
            
            #client_name = 'kolibri-1.2.5'
            client_id = salt[:2] + sha1(''.join([salt, video_id, access_token, server_id,client_location, str(source_id), salt, client_name]).encode('utf-8')).hexdigest()
            url_api_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s/sources/url?%s' % (video_id, urllib.urlencode({
                'access_token': access_token,
                'client_id': client_id,
                'client_location': client_location,
                'client_name': client_name,
                'server_id': server_id,
                'source_ids': str(source_id),
            }))

            tries = 0
            while tries < 2:
                tries += 1
                if tries == 2:
                    url = 'http://savansec.de/browse.php?u={0}&b=0&f=norefer'.format(urllib.quote(url_api_url))
                    params = dict(self.defaultParams)
                    params['header'] = dict(params['header'])
                    params['header']['Referer'] = url
                else:
                    params = self.defaultParams
                    url = url_api_url

                sts, json_data = self.getPage(url, params)
                if not sts: return []

                printDBG(json_data)
                printDBG("++++++++++++++++++++")
                printDBG(json_data)
                json_data = json_loads(json_data) 
                if json_data.get("status_code") != 12:
                    break

            return json_data["sources"]
        except Exception:
            printExc()
        return linksTab

    def getVideoLinks(self, videoUrl):
        printDBG("C7tvDe.getVideoLinks [%s]" % videoUrl)
        # mark requested link as used one
        if len(self.cacheLinks.keys()):
            for key in self.cacheLinks:
                for idx in range(len(self.cacheLinks[key])):
                    if videoUrl in self.cacheLinks[key][idx]['url']:
                        if not self.cacheLinks[key][idx]['name'].startswith('*'):
                            self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']

        return [{'name':'direct', 'url':videoUrl}]

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: ||| name[%s], category[%s] " % (name, category) )
        self.currList = []

    #MAIN MENU
        if name == None:
            self.listMain({'name':'category', 'type':'category'}, 'list_items')

        elif category == 'channels':
            self.listChannels(self.currItem, 'abc')

        elif category == 'abc':
            self.listABC(self.currItem, 'list_items')
            
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')

        elif category == 'sub_items':
            self.listSubItems(self.currItem)

        elif category == 'explore_item':
            self.exploreItem(self.currItem, 'explore_item')

    #SEARCH
        elif category == 'search':
            self.listSearchResult(MergeDicts(self.currItem, {'search_item':False, 'name':'category'}), searchPattern, searchType)
        elif category == 'search_next':
            self.listSearchResultNext(self.currItem, 'explore_item')
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()

        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):
    def __init__(self):
        CHostBase.__init__(self, C7tvDe(), True, [])

    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append(("Sendungen",    "format"))
        searchTypesOptions.append((_("Videos"),    "videos"))
        return searchTypesOptions
