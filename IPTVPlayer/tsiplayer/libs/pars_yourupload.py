# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass 
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
import re

class resolve_(CBaseHostClass):
	def __init__(self):
		CBaseHostClass.__init__(self,{'cookie':'yourupload.cookie'})
			
	def parser_(self, baseUrl):
		printDBG("parser baseUrl[%s]" % baseUrl)
		videoTab = []
		HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
		defaultParams = {'header': HTTP_HEADER,'with_metadata':True,'no_redirection':True}
		sts, data = self.cm.getPage(baseUrl, defaultParams)
		if not sts: return []
		Liste_els = re.findall("file\s*:\s*'(.+?)'", data, re.S)
		if Liste_els:
			paramsUrl = dict(defaultParams)
			paramsUrl['header']['Referer'] = baseUrl
			sts, data = self.cm.getPage(Liste_els[0], paramsUrl)
			URL = strwithmeta(data.meta['location'], {'Referer':Liste_els[0]})	
			videoTab.append({'url': URL, 'name': 'Yourupload'})    
		return videoTab
                       
def get_video_url(url):
	host=resolve_()
	return host.parser_(url)
 
