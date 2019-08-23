# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.components.ihost import CBaseHostClass 
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, VIDUPME_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.tools.e2ijs import js_execute
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.aadecode import AADecoder
import re

class resolve_(CBaseHostClass):
	def __init__(self):
		CBaseHostClass.__init__(self,{'cookie':'vidbom.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.HEADER = {'User-Agent': self.USER_AGENT}
			
	def parser_(self, baseUrl):
		printDBG("parser baseUrl[%s]" % baseUrl)
		videoTab = []
		headers = self.HEADER
		defaultParams = {'header':headers}
		sts, html = self.cm.getPage(baseUrl, defaultParams)
		if not sts: return []
		file_id = re.search("file_id',\s*'([^']+)",html)
		if file_id:
			headers.update({'cookie': 'lang=1; file_id={}'.format(file_id.group(1))})
			defaultParams = {'header':headers}
			sts, html = self.cm.getPage(baseUrl, defaultParams)
		else:
			html = None
        
		if html:
			html = html.encode('utf-8')
			aa_text = re.search("""(ﾟωﾟﾉ\s*=\s*/｀ｍ´\s*）\s*ﾉ.+?;)\svar""", html, re.I)
			if aa_text:
				printDBG('text brut='+str(aa_text.group(1)))
				aa_decoded = AADecoder(aa_text.group(1)).decode()
				printDBG('text aadecoded='+str(aa_decoded))
				data2=re.findall('file:"(.*?)"', aa_decoded, re.S)
				if data2:
					videoTab.append({'url': data2[0], 'name': 'Vidbom'})
		return videoTab
                       
def get_video_url(url):
	host=resolve_()
	return host.parser_(url)
 
