# -*- coding: utf8 -*-
import os
import re
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.urlparser import urlparser as ts_urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Components.config import config

myHosts      = ['openload','samaup','yourupload','thevid','vidbom']
vStreamHosts = ['mystream']




class URLResolver():
	def __init__(self,sHosterUrl):
		if not '://' in sHosterUrl: sHostName = sHosterUrl
		else: sHostName = sHosterUrl.split('/')[2]
		self.sHostName  = sHostName
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
