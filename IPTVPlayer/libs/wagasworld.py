# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
try: import json
except: import simplejson as json
############################################


class WagasWorldApi:
    MAIN_URL      = 'http://www.wagasworld.com/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAIN_URL }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        
        if self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def getChannelsList(self, url=''):
        printDBG("WagasWorldApi.getChannelsList url[%s]" % url )
        def foo(title, desc, icon, url):
            return dict( locals() )
            
        channelsList = []
        sts,data = self.cm.getPage(url)
        if not sts: return channelsList
        data = self.cm.ph.getDataBeetwenMarkers(data, '<article ', '</section>', True)[1]
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = data.split('</article>')
        if len(data): del data[-1]
        for item in data:
            title = self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', True)[1]
            desc  = self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', True)[1]
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0] )
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)" class="p-link"')[0] )
            if '' != url and '' != title:
                channelsList.append( foo(title, desc, icon, url) )
        return channelsList
    
    def getVideoLink(self, baseUrl):
        printDBG("WagasWorldApi.getVideoLink url[%s]" % baseUrl)
        def _url_path_join(a, b):
            from urlparse import urljoin
            return urljoin(a, b)
        
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '</iframe>', ' <section>', False)[1]
        return self.up.getAutoDetectedStreamLink(baseUrl, data)