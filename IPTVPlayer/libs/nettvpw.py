# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
############################################


class NettvPw:
    MAINURL      = 'http://www.nettv.pw/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()

    def getChannelsList(self, url=''):
        printDBG("NettvPw.getChannelsList url[%s]" % url )
        channelsList = []

        sts,data = self.cm.getPage(NettvPw.MAINURL + 'program.html')
        if not sts: return channelsList
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="programs-list">', '<div id="footer">', False)[1]
        data = re.sub('<!--[^!]+?-->', '', data)
        data = data.split('</li>')
        if len(data): del data[-1]
        for item in data:            
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon  = self.cm.ph.getSearchGroups(item, 'src="(http[^"]+?)"')[0]
            title = url.split('/')[-1].replace('.html', '').capitalize()
            if '' == url: continue
            if not url.startswith('http'): url = NettvPw.MAINURL + url
            channelsList.append({'title':title, 'url':url, 'icon':icon})
        return channelsList
    
    def getVideoLink(self, baseUrl):
        printDBG("NettvPw.getVideoLink url[%s]" % baseUrl)
        def _url_path_join(a, b):
            from urlparse import urljoin
            return urljoin(a, b)
        
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player">', '</div>', False)[1]
        url  = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
        if not url.startswith('http'): url = _url_path_join(baseUrl, url)
        sts,data = self.cm.getPage(url)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<body>', '</body>', False)[1]
        
        if "yukons.net" in data:
            channel = self.cm.ph.getDataBeetwenMarkers(data, 'channel="', '"', False)[1]
            videoUrl = strwithmeta('http://yukons.net/watch/'+channel, {'Referer':url})
            return self.up.getVideoLinkExt(videoUrl)
        elif "privatestream.tv" in data:
            videoUrl = self.cm.ph.getSearchGroups(data, '"(http://privatestream.tv/[^"]+?)"')[0]
            videoUrl = strwithmeta(videoUrl, {'Referer':url})
            return self.up.getVideoLinkExt(videoUrl)
        elif "ustream.tv" in data:
            videoUrl = self.cm.ph.getSearchGroups(data, 'src="([^"]+?ustream.tv[^"]+?)"')[0]
            if videoUrl.startswith('//'):
                videoUrl = 'http:' + videoUrl
            videoUrl = strwithmeta(videoUrl, {'Referer':url})
            return self.up.getVideoLinkExt(videoUrl)
        elif 'rtmp://' in data:
            tmp = self.cm.ph.getSearchGroups(data, """(rtmp://[^'^"]+?)['"]""")[0]
            tmp = tmp.split('&amp;')
            r = tmp[0]
            if 1 < len(tmp)and tmp[1].startswith('c='):
                playpath = tmp[1][2:]
            else:
                playpath = self.cm.ph.getSearchGroups(data, """['"]*url['"]*[ ]*?:[ ]*?['"]([^'^"]+?)['"]""")[0]
            if '' != playpath:
                r += ' playpath=%s' % playpath.strip()
            swfUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?swf)['"]""")[0]
            r += ' swfUrl=%s pageUrl=%s' % (swfUrl, url)
            return [{'name':'team-cast', 'url':r}]
        elif 'abcast.biz' in data:
            file = self.cm.ph.getSearchGroups(data, "file='([^']+?)'")[0]
            if '' != file:
                videoUrl = 'http://abcast.biz/embed.php?file='+file+'&width=640&height=480'
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.up.getVideoLinkExt(videoUrl)
        elif 'shidurlive.com' in data:
            videoUrl = self.cm.ph.getSearchGroups(data, """src=['"](http[^'^"]+?shidurlive.com[^'^"]+?)['"]""")[0]
            if '' != videoUrl:
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.up.getVideoLinkExt(videoUrl)
        elif 'sawlive.tv' in data:
            videoUrl = self.cm.ph.getSearchGroups(data, """src=['"](http[^'^"]+?sawlive.tv[^'^"]+?)['"]""")[0]
            if '' != videoUrl:
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.up.getVideoLinkExt(videoUrl)
        elif "castalba.tv" in data:
            id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"];""")[0]
            if '' != id:
                videoUrl = 'http://castalba.tv/embed.php?cid='+id+'&wh=640&ht=400&r=team-cast.pl.cp-21.webhostbox.net'
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.up.getVideoLinkExt(videoUrl)
        elif "fxstream.biz" in data:
            file = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
            if '' != file:
                videoUrl = 'http://fxstream.biz/embed.php?file='+file+'&width=640&height=400'
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.up.getVideoLinkExt(videoUrl)
        else:
            file = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?\.m3u8[^'^"]*?)['"]""")[0]
            if '' != file: return getDirectM3U8Playlist(file, checkExt=False)
            printDBG("=======================================================================")
            printDBG(data)
            printDBG("=======================================================================")
        return []