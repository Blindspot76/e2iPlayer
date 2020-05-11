# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.urlparser import urlparser as ts_urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Components.config import config
class URLResolver():
	def __init__(self,sHosterUrl):
		sHosterUrl = sHosterUrl.replace('\r','').replace('\n','')
		self.sHosterUrl = sHosterUrl
	def getLinks(self):
		urlTab=[]
		if config.plugins.iptvplayer.tsi_resolver.value=='tsiplayer':
			ts_parse = ts_urlparser()
			e2_parse = urlparser()
		else:
			ts_parse = urlparser()
			e2_parse = ts_urlparser()
			
		if ts_parse.checkHostSupport(self.sHosterUrl)==1:
			urlTab = ts_parse.getVideoLinkExt(self.sHosterUrl)
		else:
			urlTab = e2_parse.getVideoLinkExt(self.sHosterUrl)			
		return urlTab