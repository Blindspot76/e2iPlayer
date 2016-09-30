# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, remove_html_markup, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import random
import string
try:    import json
except: import simplejson as json
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.iklubnet_categorization  = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_('Categorization') + ": ", config.plugins.iptvplayer.iklubnet_categorization))
    return optionList
    
###################################################

class IKlubNetApi(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self)
        self.MAIN_URL    = 'http://iklub.net/'
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        self.COOKIE_FILE = GetCookieDir('iklubnet.cookie')
        
        self.cm = common()
        self.up = urlparser()
        self.http_params = {}
        self.http_params.update({'save_cookie': True, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        self.cacheList = {}
        
    def getListOfChannels(self, cItem):
        printDBG("IKlubNetApi.getListOfChannels")
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        retList = []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="entry-content">', '</div>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            icon = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            title = self.cm.ph.getSearchGroups(item, '''alt=['"]([^'^"]+?)['"]''')[0].replace('Telewizja online - ', '')
            if url == '': continue
            params = dict(cItem)
            params.update({'type':'video', 'url':self.getFullUrl(url), 'title':title, 'icon':self.getFullUrl(icon)})
            retList.append(params)
        return retList
        
    def getList(self, cItem):
        printDBG("IKlubNetApi.getChannelsList")
        channelsTab = []
        initList = cItem.get('init_list', True)
        if initList:
            if config.plugins.iptvplayer.iklubnet_categorization.value:
                sts, data = self.cm.getPage(self.getFullUrl(self.MAIN_URL))
                if not sts: return []
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="menu">', '</ul>')[1]
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
                for item in data:
                    url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                    title = self.cleanHtmlStr(item)
                    if url != '': continue
                    params = dict(cItem)
                    params.update({'init_list':False, 'url':self.getFullUrl(url), 'title':title})
                    retList.append(params)
                channelsTab = retList
            else:
                cItem = dict(cItem)
                cItem['url'] = self.getFullUrl('all/')
                channelsTab = self.getListOfChannels(cItem)
        else:
            channelsTab = self.getListOfChannels(cItem)
        return channelsTab
        
    def getVideoLink(self, cItem):
        printDBG("IKlubNetApi.getVideoLink")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        urlNext = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', 1, True)[0]
        if urlNext.startswith('http://') or urlNext.startswith('https://'):
            sts, data = self.cm.getPage(urlNext)
            if not sts: return []
            
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'eval(', ');', False)
        try:
            ddata = ''
            for idx in range(len(data)):
                tmp = data[idx].split('+')
                for item in tmp:
                    item = item.strip()
                    if item.startswith("'") or item.startswith('"'):
                        ddata += self.cm.ph.getSearchGroups(item, '''['"]([^'^"]+?)['"]''')[0]
                    else:
                        tmp2 = re.compile('''unescape\(['"]([^"^']+?)['"]''').findall(item)
                        for item2 in tmp2:
                            ddata += urllib.unquote(item2)
            
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(ddata)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++")
            
            funName = self.cm.ph.getSearchGroups(ddata, '''function\s*([^\(]+?)''')[0].strip()
            sp      = self.cm.ph.getSearchGroups(ddata, '''split\(\s*['"]([^'^"]+?)['"]''')[0]
            modStr  = self.cm.ph.getSearchGroups(ddata, '''\+\s*['"]([^'^"]+?)['"]''')[0] 
            modInt  = int( self.cm.ph.getSearchGroups(ddata, '''\+\s*(-?[0-9]+?)[^0-9]''')[0] )
            
            ddata =  self.cm.ph.getSearchGroups(ddata, '''document\.write[^'^"]+?['"]([^'^"]+?)['"]''')[0]
            data  = ''
            tmp   = ddata.split(sp)
            ddata = urllib.unquote(tmp[0])
            k = urllib.unquote(tmp[1] + modStr)
            for idx in range(len(ddata)):
                data += chr((int(k[idx % len(k)]) ^ ord(ddata[idx])) + modInt)
                
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++")
            
            if 'rtmp://' in data:
                rtmpUrl = self.cm.ph.getDataBeetwenMarkers(data, '&source=', '&', False)[1]
                return [{'name':'rtmp', 'url':rtmpUrl + ' live=1 '}]
            elif 'content.jwplatform.com' in data:
                vidUrl = self.getFullUrl( self.cm.ph.getSearchGroups(data, '''['"]([^'^"]+?content.jwplatform.com[^'^"]+?)['"]''')[0] )
                
                sts, data = self.cm.getPage(vidUrl)
                if not sts: return []
                
                if '/players/' not in vidUrl:
                    vidUrl = self.cm.ph.getSearchGroups(data, '''['"](https?[^'^"]+?/players/[^'^"]+?\.js)['"]''')[0]
                    HEADER = dict( self.HEADER )
                    HEADER['Referer'] = vidUrl
                    sts, data = self.cm.getPage(vidUrl, {'header':HEADER})
                    if not sts: return []
                
                data = self.cm.ph.getDataBeetwenMarkers(data, '"sources":', ']', False)[1]
                file = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?\s*:\s*['"]([^"^']+)['"],''')[0]
                printDBG(">>>>>>>>>>>>>>>>>>>>>>>> FILE[%s]" % file)
                if file.startswith('http') and file.split('?')[-1].endswith('.m3u8'):
                    return getDirectM3U8Playlist(file)
                elif file.startswith('rtmp'):
                    return [{'name':'rtmp', 'url':file + ' live=1 '}]
        except:
            printExc()
            return []
            
        return []
        
        url = self.MAIN_URL + 'set_cookie.php'
        sts, data = self.cm.getPage(url, http_params, {'url':vid_url})
        if not sts: return []
        
        url = self.MAIN_URL + 'get_channel_url.php'
        sts, data = self.cm.getPage(url, http_params, {'cid':cItem['cid']})
        if not sts: return []
        
        try:
            vid_url = byteify(json.loads(data))
            vid_url = vid_url['url']
        except:
            vid_url = data
        
        urlsTab = []
        vid_url = vid_url.strip()
        if vid_url.startswith('http://') and 'm3u8' in vid_url:
            try:
                sessid = self.cm.getCookieItem(self.COOKIE_FILE, 'sessid')
                msec   = self.cm.getCookieItem(self.COOKIE_FILE, 'msec')
                statid = self.cm.getCookieItem(self.COOKIE_FILE, 'statid')
                url = strwithmeta(vid_url, {'Cookie':'sessid=%s; msec=%s; statid=%s;' % (sessid, msec, statid)})
                urlsTab = getDirectM3U8Playlist(url)
            except:
                SetIPTVPlayerLastHostError("Problem z dostępem do pliku \"%\".\nSprawdź, czy masz wolne miejsce na pliki cookies." % self.COOKIE_FILE)
        return urlsTab