# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass 
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, VIDUPME_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.tools.e2ijs import js_execute
import re

class resolve_(CBaseHostClass):
	def __init__(self):
		CBaseHostClass.__init__(self,{'cookie':'samaup.cookie'})
			
	def parser_(self, baseUrl):
		printDBG("parser baseUrl[%s]" % baseUrl)
		videoTab = []
		HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
		defaultParams = {'header': HTTP_HEADER}
		sts, data = self.cm.getPage(baseUrl, defaultParams)
		if not sts: return []
		Liste_els = re.findall('(eval.*?)</script>', data, re.S)
		
		################Methode1##############
		#data = unpackJSPlayerParams(Liste_els[0].strip(), VIDUPME_decryptPlayerParams,1)
		####################################
		
		################Methode2################
		jscode = ['window=this; function jwplayer() {return {setup:function(){print(JSON.stringify(arguments[0]))}}}']
		jscode.append(Liste_els[0].strip())
		ret = js_execute( '\n'.join(jscode) )
		data = ret['data']
		####################################
		
		Liste_els = re.findall('file.*?:"(.*?)"', data, re.S)
		if Liste_els:
			videoTab.append({'url': Liste_els[0], 'name': 'Samaup'})
		return videoTab
                       
def get_video_url(url):
	host=resolve_()
	return host.parser_(url)
 
