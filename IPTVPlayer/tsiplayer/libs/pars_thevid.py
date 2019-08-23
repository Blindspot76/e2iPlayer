# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass 
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, VIDUPME_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.packer import cPacker
import re

class resolve_(CBaseHostClass):
	def __init__(self):
		CBaseHostClass.__init__(self,{'cookie':'thevid.cookie'})
			
	def parser_(self, baseUrl):
		printDBG("parser baseUrl[%s]" % baseUrl)
		videoTab = []
		HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
		defaultParams = {'header': HTTP_HEADER}
		sts, data = self.cm.getPage(baseUrl.replace('/v/','/e/'), defaultParams)
		if not sts: return []
		Liste_els = re.findall('(eval.*?)</script>', data, re.S)
		tmp = cPacker().unpack(Liste_els[1].strip())
		printDBG('data='+tmp)
		Liste_els = re.findall('vldAb="(.*?)"', tmp, re.S)
		if Liste_els:
			URL=Liste_els[0]
			if URL.startswith('//'): URL='https:'+URL
			videoTab.append({'url':URL , 'name': 'Thevid'})    
		return videoTab
                       
def get_video_url(url):
	host=resolve_()
	return host.parser_(url)
 
