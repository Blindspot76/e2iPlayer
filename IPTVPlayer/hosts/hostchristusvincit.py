# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, MergeDicts, rm, formatBytes
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
###################################################

###################################################
# FOREIGN import
###################################################
import re
import time
from datetime import  timedelta
###################################################

def gettytul():
    return 'http://christusvincit-tv.pl/'

class Christusvincit(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'christusvincit-tv.pl', 'cookie':'christusvincit-tv.pl.cookie'})

        self.HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        self.defaultParams = {'header':self.HTTP_HEADER}

        self.MAIN_URL   = 'http://christusvincit-tv.pl/'
        self.DEFAULT_ICON_URL = 'http://christusvincit-tv.pl/images/christusbg.jpg'
        self.reImgObj = re.compile(r'''<img[^>]+?src=(['"])([^>]*?\.(?:jpe?g|png|gif)(?:\?[^\1]*?)?)(?:\1)''', re.I)

    def listMain(self, cItem, nextCategory):
        printDBG("Christusvincit.listMain")

        sts, data = self.getPage(self.getMainUrl())
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])

        data = re.sub("<!--[\s\S]*?-->", "", data)
        sections = ph.rfindall(data, '</table>', ('<td', '>', 'capmain-left'), flags=0)
        for section in sections:
            self.handleSection(cItem, nextCategory, section)

    def handleSection(self, cItem, nextCategory, section):
        printDBG("Christusvincit.handleSection")

        tmp = section.split('</table>', 1)
        sTitle = self.cleanHtmlStr(tmp[0])
        if sTitle.lower() in ('linki',): #'kategorie'
            return
        sIcon = self.getFullUrl( ph.search(section, ph.IMAGE_SRC_URI_RE)[1] )
        iframe = ph.search(section, ph.IFRAME_SRC_URI_RE)[1]
        subItems = []
        if iframe: subItems.append(MergeDicts(cItem, {'category':nextCategory, 'title':sTitle, 'url':iframe}))
        section = ph.findall(section, ('<a', '>', 'articles.php'), '</a>')
        for item in section:
            url = self.getFullUrl( ph.search(item, ph.A_HREF_URI_RE)[1] )
            icon = self.getFullUrl( ph.search(item, self.reImgObj)[1] )
            title = icon.rsplit('/', 1)[-1].rsplit('.', 1)[0].upper()
            subItems.append(MergeDicts(cItem, {'good_for_fav':True:, 'category':nextCategory, 'title':title, 'url':url, 'icon':icon}))

        if len(subItems) > 1:
            self.addDir(MergeDicts(cItem, {'category':'sub_items', 'title':sTitle, 'icon':sIcon, 'sub_items':subItems}))
        elif len(subItems) == 1:
            params = subItems[0]
            params.update({'title':sTitle})
            self.addDir(params)

    def getPage(self, baseUrl, addParams={}, post_data=None):
        if addParams == {}: addParams = dict(self.defaultParams)
        return self.cm.getPage(baseUrl, addParams, post_data)

    def listSubItems(self, cItem):
        printDBG("Christusvincit.listSubItems")
        self.currList = cItem['sub_items']

    def exploreItem(self, cItem):
        printDBG("Christusvincit.exploreItem")
        playerConfig = None

        sts, data = self.getPage(cItem['url'])
        if not sts: return
        self.setMainUrl(self.cm.meta['url'])

        if 'articles.php' in cItem['url']:
            iframe = ph.search(data, ph.IFRAME_SRC_URI_RE)[1]
            if not iframe: 
                iframe = ph.find(data, ('<script', '>', 'embedIframeJs'))[1]
                iframe = ph.getattr(iframe, 'src')

            if iframe and '?' in iframe:
                sts, tmp = self.getPage(self.getFullUrl(iframe.replace('?', '?iframeembed=true&')))
                if not sts: return
                playerConfig = ph.find(tmp, '{"playerConfig"', '};')[1][:-1]
            else:
                sections = ph.find(data, '<noscript', 'scapmain-left')[1]
                sections = ph.rfindall(sections, '</table>', ('<td', '>', 'capmain-left'), flags=0)
                for section in sections:
                    self.handleSection(cItem, cItem['category'], section)
        else:
            playerConfig = ph.find(data, '{"playerConfig"', '};')[1][:-1]
        
        if playerConfig:
            try:
                playerConfig = json_loads(playerConfig)
                playlistResult = playerConfig.get('playlistResult', {})
                if not playlistResult: playlistResult['0'] = {'items':[playerConfig['entryResult']['meta']]}
                for key, section in playlistResult.iteritems():
                    for item in section['items']:
                        icon = self.getFullUrl(item['thumbnailUrl'])
                        title = item['name']
                        desc = '%s | %s' % (str(timedelta(seconds=item['duration'])), item['description'])
                        params = {'title':title, 'icon':icon, 'desc':desc, 'f_id':item['id']}
                        if item.get('hlsStreamUrl'): params['url'] = item['hlsStreamUrl']
                        self.addVideo(params)
            except Exception:
                printExc()

    def getLinksForVideo(self, cItem):
        urlsTab = []

        if 'url' in cItem:
            return getDirectM3U8Playlist(cItem['url'])

        url = 'http://mediaserwer3.christusvincit-tv.pl/api_v3/index.php?service=multirequest&apiVersion=3.1&expiry=86400&clientTag=kwidget%3Av2.41&format=1&ignoreNull=1&action=null&1:service=session&1:action=startWidgetSession&1:widgetId=_100&2:ks=%7B1%3Aresult%3Aks%7D&2:service=baseentry&2:action=list&2:filter:objectType=KalturaBaseEntryFilter&2:filter:redirectFromEntryId='
        url += cItem['f_id']
        url += '&3:ks=%7B1%3Aresult%3Aks%7D&3:contextDataParams:referrer=http%3A%2F%2Fmediaserwer3.christusvincit-tv.pl&3:contextDataParams:objectType=KalturaEntryContextDataParams&3:contextDataParams:flavorTags=all&3:contextDataParams:streamerType=auto&3:service=baseentry&3:entryId=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&3:action=getContextData&4:ks=%7B1%3Aresult%3Aks%7D&4:service=metadata_metadata&4:action=list&4:version=-1&4:filter:metadataObjectTypeEqual=1&4:filter:orderBy=%2BcreatedAt&4:filter:objectIdEqual=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&4:pager:pageSize=1&5:ks=%7B1%3Aresult%3Aks%7D&5:service=cuepoint_cuepoint&5:action=list&5:filter:objectType=KalturaCuePointFilter&5:filter:orderBy=%2BstartTime&5:filter:statusEqual=1&5:filter:entryIdEqual=%7B2%3Aresult%3Aobjects%3A0%3Aid%7D&kalsig=404d9c08e114ce91328cd739e5151b80'
        sts, data = self.getPage(url)
        if not sts: return []

        try:
            data = json_loads(data)
            baseUrl = data[1]['objects'][0]['dataUrl']
            for item in data[2]['flavorAssets']:
                if item['fileExt'] != 'mp4' or not item['isWeb']: continue
                name = '%sx%s %s' % (item['width'], item['height'], formatBytes(item['size']*1024))
                url = baseUrl.replace('/format/', '/flavorId/%s/format/' % item['id'])
                urlsTab.append({'name':name, 'url':url, 'need_resolve':0, 'bitrate':item['bitrate'], 'original':item['isOriginal']})
            urlsTab.sort(key=lambda x: x['bitrate'], reverse=True)
        except Exception:
            printExc()
        return urlsTab

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: ||| name[%s], category[%s] " % (name, category) )
        self.currList = []

    #MAIN MENU
        if name == None:
            self.listMain({'name':'category', 'type':'category'}, 'explore_item')

        elif category == 'explore_item':
            self.exploreItem(self.currItem)

        elif category == 'sub_items':
            self.listSubItems(self.currItem)

        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Christusvincit(), False, [])

