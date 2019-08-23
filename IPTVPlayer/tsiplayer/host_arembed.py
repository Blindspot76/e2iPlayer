# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
#from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,resolve_liveFlash
from Plugins.Extensions.IPTVPlayer.libs import ph
import re

def getinfo():
	info_={}
	info_['name']='Arembed.Com'
	info_['version']='1.0 17/06/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='100'#2
	info_['desc']='Live Bein Sports'
	info_['icon']='http://c247.se/embed_logo/Bein%20Sports%201%20to%204.png'
	info_['recherche_all']='0'
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'coolkora.cookie'})
		self.MAIN_URL = 'http://ar.coolkora.com'
		self.USER_AGENT = 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage

	
		
	def showmenu(self,cItem):
		sts,data=self.getPage('http://c247.se/')
		image='http://c247.se/embed_logo/Bein%20Sports%201%20to%204.png'
		if sts:
			printDBG('dddddddd'+data)		
			films_list = re.findall('<div id="Bein.*?ch=\'(.*?)\'.*?href ="(.*?)"', data, re.S)
			for (titre,url) in films_list:
				self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre.replace('_',' '),'url':url,'desc':'','icon':image,'hst':'tshost'})	

	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		urlTab.append({'name':'Bein', 'url':'hst#tshost#'+URL, 'need_resolve':1})	

		
		return urlTab
		

	def getVideos(self,videoUrl):
		urlTab = []	
		sts, data = self.getPage(videoUrl)
		url_data = re.findall("channel='(.*?)'.*?src='(.*?\..*?)/", data, re.S)
		if url_data:
			hst=url_data[0][1]
			link=hst+'/embedplayer/'+url_data[0][0]+'/1/700/400'
			urlTab.append((resolve_liveFlash(link,videoUrl),'0'))

		return urlTab

		
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
