# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

import re



def getinfo():
	info_={}
	info_['name']='Yalla-Shoot.Com (Only replay)'
	info_['version']='1.0 24/04/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='110'
	info_['desc']='مشاهدة ملخصات و مباريات كاملة'
	info_['icon']='http://www.yalla-shoot.com/img/logo.png'
	info_['recherche_all']='0'
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'yalla.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.4.2; SAMSUNG-SM-N900A Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Safari/537.36'
		self.MAIN_URL = 'http://www.yalla-shoot.com'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		
		
	def showmenu(self,cItem):
		page = cItem.get('page',1)	
		url = 'http://www.yalla-shoot.com/live/video.php?page='+str(page)
		sts, data = self.cm.getPage(url)
		Liste_els = re.findall('<div class="col-md-3 col-sm-6 goals-item">.*?href="(.*?)".*?src="(.*?)".*?title="(.*?)">(.*?)<.*?</i>(.*?)<.*?</i>(.*?)<', data, re.S)
		for (URL,pic,desc,titre,date_,desc2) in Liste_els:
			self.addVideo({'import':cItem['import'],'url':URL,'title': titre,'desc':desc,'icon':pic,'hst':'tshost','good_for_fav':True} )
		self.addDir({'import':cItem['import'],'title':'Page '+str(page+1),'page':page+1,'category' : 'yallashoot','icon':cItem['icon'],'mode':'20'}) 
		

	def get_links(self,cItem):	
		urlTab = []	
		url='http://www.yalla-shoot.com/live/'+cItem['url']	 
		URL_=''
		sts, data = self.cm.getPage(url)
		Liste_els = re.findall('<iframe.*?src="(.*?)"', data, re.S)
		if Liste_els:
			URL2=Liste_els[0]
			if 'ok.php?id=' in	URL2:
				Link = re.findall('php\?id=(.*?)(\?| |<)', data, re.S)
				if Link:
					URL_='http://ok.ru/videoembed/'+Link[0][0]
			elif 'youtube.php?ytid=' in	URL2:
				Link = re.findall('php\?ytid=(.*?)(\?| |<)', data, re.S)
				if Link:
					URL_='https://www.youtube.com/embed/'+Link[0][0]
			elif 'videostreamlet.net' in URL2:
				Link = re.findall('.*/(.*?)\?', URL2, re.S)
				if Link:
					URL_='http://player.videostreamlet.net/embed/'+Link[0]			
					sts, data2 = self.cm.getPage(URL_)
					Liste_els2 = re.findall('hls:"(.*?)"', data2, re.S)	
					if Liste_els2:
						url_=Liste_els2[0]
						if url_.startswith('//'):
							url_='http:'+url_
						urlTab = getDirectM3U8Playlist(url_, False, checkContent=True, sortWithMaxBitrate=999999999)
						return urlTab
			else:
				URL_=URL2
		if URL_!='':
			if URL_.startswith('//'):
				URL_='http:'+URL_
			name=URL_
			Link = re.findall(':(.*?)/', URL_, re.S)
			if Link:
				name=Link[0]				
			urlTab.append({'name':name, 'url':URL_, 'need_resolve':1})	
		return urlTab
	
	def start(self,cItem):
		list_=[]
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)	
		elif mode=='20':
			self.showmenu(cItem)
		return True
