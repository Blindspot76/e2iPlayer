# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re

def getinfo():
	info_={}
	info_['name']='كرتون+ (Android App)'
	info_['version']='1.1 07/07/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='203'
	info_['desc']='افلام و مسلسلات كرتون'
	info_['icon']='https://image.winudf.com/v2/image/Y2FydG9vbnBsdXNwbHVzLmNvbS5jYXJ0b29ucGx1c3BsdXNfc2NyZWVuXzBfMTUyNTIwNzg4NF8wNTc/screen-0.jpg?h=800&fakeurl=1&type=.jpg'
	info_['recherche_all']='0'
	info_['update']='Bugs Fix'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'wiiudown.cookie'})
		self.USER_AGENT = 'Dalvik/2.1.0 (Linux; U; Android 7.1.1; E6633 Build/32.4.A.1.54)'
		self.MAIN_URL = 'https://wiiudown.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
	 

	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'مغامرات',   'icon':cItem['icon'],'mode':'20','sub_mode':'1'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'رياضة',     'icon':cItem['icon'],'mode':'20','sub_mode':'2'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'انمي حديث', 'icon':cItem['icon'],'mode':'20','sub_mode':'3'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'حكيات',     'icon':cItem['icon'],'mode':'20','sub_mode':'4'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'كرتون بنات','icon':cItem['icon'],'mode':'20','sub_mode':'5'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'خيال علمي', 'icon':cItem['icon'],'mode':'20','sub_mode':'6'})	

	def showanim(self,cItem):
		cat_id=cItem.get('sub_mode','1')
		URL='https://wiiudown.com/apps/anime/byCat.php?cid='+cat_id
		sts, data = self.getPage(URL)
		if sts:
			data = json_loads(data)
			for elm in 	data:
				titre    = elm['Title']
				name     = elm['STableName']
				img      = elm['Icon']
				nbSeason = elm['SSeasons']
				nbEp=elm['Total']
				Desc=tscolor('\c00????00')+'Saisons: '+tscolor('\c00??????')+nbSeason+'\\n'
				Desc=Desc+tscolor('\c00????00')+'Episodes: '+tscolor('\c00??????')+nbEp+'\\n'
				if name!='mymoreapps':
					if 	int(nbSeason)>1:
						self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':name,'icon':img,'desc':Desc,'mode':'21','nbSeason':nbSeason,'good_for_fav':True})
					else:	
						self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':name,'icon':img,'desc':Desc,'mode':'30','good_for_fav':True})
						

	def showanim2(self,cItem):
		nbSeason=cItem.get('nbSeason','1')
		for i in range (1,int(nbSeason)+1):
			self.addDir({'import':cItem['import'],'category' : 'host2','title':cItem['title']+' Season '+str(i),'url':cItem['url']+str(i),'icon':cItem['icon'],'desc':cItem['desc'],'mode':'30','good_for_fav':True})

		
	def showep(self,cItem):
		anime=cItem.get('url','')
		URL='https://wiiudown.com/apps/anime/byShow.php?show='+anime
		sts, data = self.getPage(URL)
		if sts:
			data = json_loads(data)
			for elm in 	data:
				titre = elm['Title']
				Views = elm['Views']
				img   = elm['Poster']
				url   = elm['Code']
				
				srv1  = elm.get('Server_1','')
				srv2  = elm.get('Server_2','')
				srv3  = elm.get('Server_3','')
				srv4  = elm.get('Server_4','')
				srv5  = elm.get('Server_5','')
				servers = [srv1,srv2,srv3,srv4,srv5]
				
				Desc=tscolor('\c00????00')+'Views: '+tscolor('\c00??????')+Views+'\\n'
				img='https://wiiudown.com/apps/'+anime+'/Poster/'+img+'.jpg'	
				url_data = re.findall('url=(.*)', url, re.S)
				if url_data:
					URL_=url_data[0]
				else: URL_=url
				if (srv1!='')or(srv2!='')or(srv3!='')or(srv4!='')or(srv5!=''):
					hst='tshost'
					URL_=servers
				elif ('youtube' in URL_) or ('dailymotion' in URL_):
					hst='none'
				else:
					hst='direct'	
				self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':URL_,'icon':img,'hst':hst,'good_for_fav':True})	


	def get_links(self,cItem): 	
		urlTab = []

		servers=cItem['url']
		i=0
		for URL_ in servers:
			if URL_!='':
				i=i+1
				urlTab.append({'name':'Server '+str(i), 'url':'hst#tshost#'+URL_, 'need_resolve':1})
						
		return urlTab	

	def getVideos(self,videoUrl):
		urlTab=[]	
		sts, data = self.getPage(videoUrl)
		if sts:
			url_data = re.findall('file".*?"(.*?)"', data, re.S)
			if not url_data:
				url_data = re.findall("file'.*?'(.*?)'", data, re.S)			
			if url_data:
				if url_data[0].strip()!='':	
					urlTab.append((url_data[0].strip(),'0'))	
		return urlTab	
			
	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)	
		elif mode=='20':
			self.showanim(cItem)	
		elif mode=='21':
			self.showanim2(cItem)	
		elif mode=='30':
			self.showep(cItem)
