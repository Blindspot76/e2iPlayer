# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.libs import ph
import re,urllib,base64

def getinfo():
	info_={}
	info_['name']='3sk.Co'
	info_['version']='1.4 20/02/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات تركية'
	info_['icon']='https://i.ibb.co/XxF6hB3/culcaqfk.png'
	info_['recherche_all']='0'
	#info_['update']='Fix Links extractor'	

	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'_3sk.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://3sk.co'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'اخر الحلقات'  ,'icon':cItem['icon'],'mode':'30','sub_mode':'0'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'افلام'         ,'icon':cItem['icon'],'mode':'30','sub_mode':'2'})			
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'جميع المسلسلات','icon':cItem['icon'],'mode':'30','sub_mode':'1'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'ارشيف المسلسلات المترجمة' ,'icon':cItem['icon'],'mode':'30','sub_mode':'3'})		
		self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})


	def showitms(self,cItem):
		sub_mode=cItem.get('sub_mode', '0')	
		page = cItem.get('page', 1)
		
		
		if (sub_mode=='0')or(sub_mode=='2') :
			if sub_mode=='0': url0='https://3sk.co/p'+str(page)+'.html'
			else: url0='https://3sk.co/pdep42-p'+str(page)+'.html'
			sts, data = self.getPage(url0)
			if sts:
				lst_data=re.findall('<div class="article">.*?href=\'(.*?)\'>(.*?)<.*?src=\'(.*?)\'.*?details">(.*?)</div>', data, re.S)
				for (url1,name_eng,image,desc) in lst_data:
					if not image.startswith('http'): image='https://3sk.co/'+image	
					if not url1.startswith('http'):	 url1='https://3sk.co/'+url1
					self.addVideo({'import':cItem['import'],'category' : 'host2','title':ph.clean_html(name_eng.strip()),'url':url1,'desc':ph.clean_html(desc.strip()),'icon':image,'hst':'tshost','good_for_fav':True})	
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':'','page':page+1,'mode':'30','sub_mode':sub_mode})
					
		elif (sub_mode=='1') :
			url0='https://3sk.co/vb/'
			sts, data = self.getPage(url0)
			if sts:
				lst_data=re.findall('<div class="col-xs-12 catTitle">(.*?)/h2>(.*?)<div class="row">', data, re.S)
				for (name_cat,data2) in lst_data:		
					self.addMarker({'title':tscolor('\c00????00')+ph.clean_html(name_cat),'icon':cItem['icon']})
					lst_data2=re.findall('"itemIMG">.*?href="(.*?)".*?src="(.*?)".*?<h3>(.*?)</h3>', data2, re.S)
					for (url1,image,name_eng) in lst_data2:	
						if not image.startswith('http'): image='https://3sk.co/'+image	
						if not url1.startswith('http'):	 url1='https://3sk.co/'+url1			
						self.addDir({'import':cItem['import'],'category' : 'host2','title':ph.clean_html(name_eng.strip()),'url':url1,'icon':image,'mode':'20','good_for_fav':True})

		elif (sub_mode=='3') :
			url0='https://3sk.co/vb/forumdisplay.php?f=8'
			sts, data = self.getPage(url0)
			if sts:
				lst_data=re.findall('<h3>.*?href="(.*?)">(.*?)<', data, re.S)
				for (url_,name_) in lst_data:		
					if not url_.startswith('http'):	 url_='https://3sk.co/vb/'+url_	
					self.addDir({'import':cItem['import'],'category' : 'host2','title':name_,'url':url_.replace('&amp;','&'),'icon':cItem['icon'],'mode':'20','good_for_fav':True})


	def showmenu1(self,cItem):
		url=cItem.get('url', '')
		sts, data = self.getPage(url)
		if sts:
			lst_data = re.findall('container-fluid">.*?href="(.*?)".*?_title.*?>(.*?)<',data, re.S)
			for (url1,name_eng) in lst_data:
				if not url1.startswith('http'):	url1='https://3sk.co/vb/'+url1
				self.addVideo({'import':cItem['import'],'category' : 'host2','title':name_eng,'url':url1.replace('&amp;','&'),'icon':cItem['icon'],'hst':'tshost','good_for_fav':True})	


	def SearchResult(self,str_ch,page,extra):
		KEYV3 = 'AIzaSyDn2w07I3D8xNQ9D-QcY5t3n0JZ7RW8J8c'
		if page>1:
			url="https://www.googleapis.com/customsearch/v1?key=%s&cx=002583796122408301021:jbaiasxjs2k&q=%s&start=%s"%(KEYV3,str_ch,str((int(page)*10)+1))
		else:    
			url="https://www.googleapis.com/customsearch/v1?key=%s&cx=002583796122408301021:jbaiasxjs2k&q=%s"%(KEYV3,str_ch)
		sts, data = self.getPage(url)
		if sts:
			jdata = json_loads(data)
			items=jdata['items']
			icon = 'https://i.ibb.co/XxF6hB3/culcaqfk.png'
			for item in items:
				title=item['title'].encode("utf-8")
				link=item['link']
				snippet=item['snippet']
				if 'showthread' in link:
					mode_='91'
				else:
					mode_='20'
				if not ".php" in link:
					continue
				if mode_=='91':
					self.addVideo({'import':extra,'category' : 'video','title':title,'url':link,'hst':'tshost','good_for_fav':True})		
				else:
					self.addDir({'import':extra,'category' : 'host2','title':title,'url':link,'icon':icon,'mode':'20','good_for_fav':True})
		
		
	def get_links(self,cItem): 	
		urlTab = []
		baseUrl=cItem['url']
		sts, data = self.getPage(baseUrl)
		if sts:	
			_data = re.findall('class="postat-hyper">(.*?)class="top-adv"',data, re.S)
			if _data:
				data2 = re.findall('<a href=["\'](.*?)["\']',_data[0], re.S)
				i=0
				for href in data2:
					i=i+1
					if href.startswith('//'):
						href='http:'+href
					if 'post.php?url=' in href:
						x1,href = href.split('post.php?url=')
						href = base64.b64decode( urllib.unquote(href) )
					if self.up.checkHostSupport(href)==1: 
						urlTab.append({'url':href, 'name':'|'+str(i)+'| '+self.cm.getBaseUrl(href, True).replace('www.',''), 'need_resolve':1})
					elif '/vid/' in href:
						sts, data3 = self.getPage(href)
						if sts:
							data4 = re.findall('<iframe.*?src.*?["\'](.*?)["\']',data3, re.S)
							for url in data4:
								if url.startswith('//'):
									url='http:'+url
								if self.up.checkHostSupport(url)==1:
									urlTab.append({'url':url, 'name':'|'+str(i)+'| '+self.cm.getBaseUrl(url, True).replace('www.',''), 'need_resolve':1})
							data4 = re.findall('target=.*?href.*?["\'](.*?)["\']',data3, re.S)
							for url in data4:
								if url.startswith('//'):
									url='http:'+url
								if self.up.checkHostSupport(url)==1:
									if ('youtube.com/user/' not in url) and ('facebook' not in url):
										urlTab.append({'url':url, 'name':'|'+str(i)+'| '+self.cm.getBaseUrl(url, True).replace('www.',''), 'need_resolve':1})
							data4 = re.findall('<script.*?src=["\'](.*?)["\']',data3, re.S)
							for url in data4:
								if url.startswith('//'):
									url='http:'+url
								if self.up.checkHostSupport(url)==1:
									urlTab.append({'url':url, 'name':'|'+str(i)+'| '+self.cm.getBaseUrl(url, True).replace('www.',''), 'need_resolve':1})
				
		return urlTab	
		 

			
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='30':
			self.showitms(cItem)			

