# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.tstools import TSCBaseHostClass

import re

def getinfo():
	info_={}
	info_['name']='m.Movizland.Online'
	info_['version']='1.1 06/07/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام, مسلسلات و انمي بالعربية'
	info_['icon']='https://i.ibb.co/Jz35Xbn/2p12b1o6.png'
	info_['recherche_all']='1'
	info_['update']='Bugs Fix'	
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'movizland.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		#self.MAIN_URL = 'http://movizland.online'
		self.MAIN_URL = 'http://m.movizland.online'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
					 	 
	def showmenu0(self,cItem):
		sts, data = self.getPage(self.MAIN_URL)
		if sts:
			Liste_films_data = re.findall('id="tabs-ui">(.*?)</ul>', data, re.S)
			if Liste_films_data:
				Liste_films_data0 = re.findall('<li>.*?href="(.*?)".*?title="(.*?)"', Liste_films_data[0], re.S)
				for (url,titre) in Liste_films_data0:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'icon':cItem['icon'],'mode':'30','sub_mode':'3'})
				
			self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})

	def showitms(self,cItem):
		urlo=cItem.get('url', '')	
		page = cItem.get('page', 1)
		url=cItem['url']+'page/'+str(page)+'/'		
		sts, data = self.getPage(url)
		if sts:
			Liste_films_data = re.findall('<li class="grid-item.*?href="(.*?)".*?src="(.*?)".*?Title">(.*?)<', data, re.S)
			for (url1,image,name_eng) in Liste_films_data:
				self.addVideo({'import':cItem['import'],'category' : 'host2','title':name_eng.strip(),'url':url1,'icon':image,'desc':'','good_for_fav':True,'hst':'tshost'})					
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':urlo,'page':page+1,'mode':'30'})

		

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/?s='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:
			Liste_films_data = re.findall('<li class="grid-item.*?href="(.*?)".*?src="(.*?)".*?Title">(.*?)<', data, re.S)
			for (url1,image,name_eng) in Liste_films_data:
				self.addVideo({'import':extra,'category' : 'host2','title':name_eng.strip(),'url':url1,'icon':image,'desc':'','good_for_fav':True,'hst':'tshost'})					
		
		
	def get_links(self,cItem): 	
		urlTab = []
		Url=cItem['url']
		sts, data = self.getPage(Url.replace('//movizland.online/','//m.movizland.online/'))
		if sts:
			Liste_els = re.findall('rgba\(203, 0, 44, 0.36\).*?href="(.*?)".*?ViewMovieNow">(.*?)<', data, re.S)
			for (url_,titre_) in Liste_els:
				if 'و حمل' not in titre_:
					if 'تحميل' in titre_: titre_='سرفر التحميل'
					urlTab.append({'name':titre_, 'url':url_, 'need_resolve':0})							
		return urlTab	

			
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='30':
			self.showitms(cItem)				
		return True

