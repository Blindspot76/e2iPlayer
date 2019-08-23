# -*- coding: utf8 -*-
import os
import re
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG


myHosts      = ['openload','samaup','yourupload','thevid','vidbom']
vStreamHosts = ['mystream']




class URLResolver():
	def __init__(self,sHosterUrl):
		if not '://' in sHosterUrl: sHostName = sHosterUrl
		else: sHostName = sHosterUrl.split('/')[2]
		self.sHostName  = sHostName
		self.sHosterUrl = sHosterUrl
		tmp_=sHostName.replace('embed.','').replace('www.','')
		if '.' in tmp_: tmp_=tmp_.split('.')[0]
		self.sHosterFileName = tmp_.lower()	
		if   any(self.sHosterFileName in s for s in myHosts      ): self.sHostType = 0		
		elif any(self.sHosterFileName in s for s in vStreamHosts ): self.sHostType = 1	
		else: self.sHostType = 3
		printDBG('resolv url:'+self.sHosterUrl)
		printDBG('resolv sHosterFileName:'+self.sHosterFileName)
		printDBG('resolv type:'+str(self.sHostType))

	def getLinks(self):
		urlTab=[]

		if self.sHostType == 0:
			func_='pars_'+self.sHosterFileName
			exec('from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.'+func_+' import get_video_url as '+func_)
			exec('urlTab = '+func_+'(self.sHosterUrl)')
		elif self.sHostType == 1:	
			exec "from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.hosters." + self.sHosterFileName + " import cHoster"
			oHoster = cHoster()
			oHoster.setUrl(self.sHosterUrl)
			aLink = oHoster.getMediaLink()
			if (aLink[0] == True):
				URL = aLink[1]
				if '|User-Agent=' in URL:
					URL,UA=aLink[1].split('|User-Agent=',1)
				URL = strwithmeta(URL, {'User-Agent':UA})
				urlTab.append({'url':URL , 'name': self.sHosterFileName})
		else:
			urlTab = urlparser().getVideoLinkExt(self.sHosterUrl)
				
		return urlTab
