# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
import re
import urllib
def getinfo():
	info_={}
	info_['name']='Okanime.Com'
	info_['version']='1.2.1 16/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='202'
	info_['desc']='انمي مترجم'
	info_['icon']='https://i.ibb.co/88XFP0D/okanim.jpg'
	info_['recherche_all']='0'
	info_['update']='Add newest_animes'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'okanime.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.okanime.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding':'gzip, deflate, br','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']
		self.addMarker({'title':'أفلام','category' : 'host2','icon':img_} )									

		Cat_TAB = [
					{'category':hst,'title': 'الترتيب حسب أحدث الافلام', 'mode':'30','url':'https://www.okanime.com/movies?direction=desc&sort=published_at'},		
					{'category':hst,'title': 'الترتيب حسب الأبجدية', 'mode':'30','url':'https://www.okanime.com/movies?direction=asc&sort=title'},
					{'category':hst,'title': 'الترتيب حسب تقييم الأعضاء', 'mode':'30','url':'https://www.okanime.com/movies?direction=desc&sort=rating_caches.avg'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})	
		self.addMarker({'title':'قائمة الانميات','category' : 'host2','icon':img_} )	
		Cat_TAB = [
					{'category':hst,'title':'آخر الحلقات المضافة', 'mode':'30','url':'https://www.okanime.com/dashboard/newest_animes?direction=asc','sub_mode':1},
					{'category':hst,'title': 'الترتيب حسب أحدث الانميات', 'mode':'30','url':'https://www.okanime.com/animes?direction=desc&sort=published_at'},
					{'category':hst,'title': 'الترتيب حسب الأبجدية', 'mode':'30','url':'https://www.okanime.com/animes?direction=asc&sort=title'},
					{'category':hst,'title': 'الترتيب حسب تقييم الأعضاء', 'mode':'30','url':'https://www.okanime.com/animes?direction=desc&sort=rating_caches.avg'},
					{'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})			
		
		
	def showitms(self,cItem):
		url1=cItem['url']
		gnr=cItem.get('sub_mode',0)
		page=cItem.get('page',1)
		url_=url1+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:
			if gnr==0:
				films_list = re.findall('class=\'col-md-15.*?title="(.*?)".*?href="(.*?)".*?src="(.*?)".*?class="rating.*?>(.*?)</div>.*?class=\'info-.*?<a(.*?)</div>', data, re.S)		
				for (titre,url,image,rate,desc) in films_list:
					if not url.startswith('http'): url=self.MAIN_URL+url
					if not image.startswith('http'): image=self.MAIN_URL+image
					desc='Rating: '+tscolor('\c00????00')+ph.clean_html(rate)+tscolor('\c00??????')+'\\nGenre: '+tscolor('\c00????00')+ph.clean_html('<a'+desc)
					self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'hst':'tshost','mode':'31'})	
			else:
				films_list0 = re.findall('animes-carousel">(.*?)</ul', data, re.S)	
				if films_list0:
					films_list = re.findall('<li.*?href="(.*?)".*?src="(.*?)".*?class="title.*?>(.*?)</div>', films_list0[0], re.S)		
					for (url,image,titre) in films_list:
						image = self.MAIN_URL+image
						url=self.MAIN_URL+url
						titre=ph.clean_html(titre)
						self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':'','icon':image,'hst':'tshost','mode':'31'})		
			self.addDir({'import':cItem['import'],'title':'Page '+str(page+1),'page':page+1,'category' : 'host2','url':url1,'icon':cItem['icon'],'mode':'30','sub_mode':gnr} )									
				
	def showelms(self,cItem):
		urlo=cItem['url']
		url1=urlo
		sts, data = self.getPage(urlo)
		if sts:
			Liste_els = re.findall('class="btn btn-lg2.*?href="(.*?)"', data, re.S)
			if Liste_els:
				url1=Liste_els[0]
				if not url1.startswith('http'): url1=self.MAIN_URL+url1
				sts, data = self.getPage(url1)
			if sts:
				films_list = re.findall('<ul class=\'episodes-list(.*?)</ul>', data, re.S)
				if films_list:
					films_list1 = re.findall('<a.*?href="(.*?)".*?class=\'episode\'>(.*?)</li>', films_list[0], re.S)				
					for (url,titre) in films_list1:
						if not url.startswith('http'): url=self.MAIN_URL+url
						self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':ph.clean_html(titre),'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'} )
				else:
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url1,'title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'} )
		
	
	def SearchResult(self,str_ch,page,extra):
		url_='https://www.okanime.com/search?utf8=%E2%9C%93&%5Bsearch%5D='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('class=\'col-md-15.*?href="(.*?)".*?src="(.*?)".*?class="rating.*?>(.*?)</div>.*?title\'>(.*?)<', data, re.S)		
			for (url,image,rate,titre) in films_list:
				if not url.startswith('http'): url=self.MAIN_URL+url
				if not image.startswith('http'): image=self.MAIN_URL+image
				desc='Rating: '+tscolor('\c00????00')+ph.clean_html(rate)
				self.addDir({'import':extra,'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'hst':'tshost','mode':'31'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			Tab_els = re.findall('<ul class=\'servers-list(.*?)</ul>', data, re.S)
			if Tab_els:
				Liste_els = re.findall('<li>.*?href="(.*?)">(.*?)<', Tab_els[0], re.S)
				for (code,host_) in Liste_els:
					local=''
					if 'google' in host_.lower(): host_= 'google.com'
					if 'neon' in host_.lower():
						host_ = '|OKAnime| '+host_
						local = 'local'
					urlTab.append({'name':host_, 'url':'hst#tshost#'+code+'|'+URL, 'need_resolve':1,'local':local})						
		return urlTab
		
		 
	def getVideos(self,videoUrl):
		urlTab = []	
		try:
			videoUrl,referer=videoUrl.split('|',1)
			sUrl = self.MAIN_URL+videoUrl
			paramsUrl = dict(self.defaultParams)
			paramsUrl['header']['Referer'] = referer
			sts, data = self.getPage(sUrl,paramsUrl)
			if sts:
				Liste_els_3 = re.findall('url":"(.*?)"', data, re.S)	
				if Liste_els_3:
					URL=Liste_els_3[0].replace('\\n','')
					if URL.startswith('//'): URL='https:'+URL
					if 'www.okanime.com' in URL:			
						sts, data = self.getPage(URL,paramsUrl)
						Liste_els_3 = re.findall('loadVideURL\(.*?src.*?\'(.*?)\'', data, re.S)	
						if Liste_els_3:
							URL1=Liste_els_3[0]	
							if ('vk/index.php?v=' in URL1) or ('vr/index.php?link=' in URL1)or ('yd/index.php?id=' in URL1):
								sts, data = self.getPage(URL1,paramsUrl)
								paramsUrl = dict(self.defaultParams)
								paramsUrl['header']['Referer'] = URL1							
								sts, data = self.getPage(URL1,paramsUrl)
								Liste_els_3 = re.findall('sources:.*?(\[.*?])', data, re.S)								
								if Liste_els_3:
									srvs = json_loads(Liste_els_3[0])
									for elm in srvs:
										urlTab.append((elm['label']+'|'+elm['file'],'4'))
							if 'okgaming' in URL1 :
								urlTab.append(('','1'))
							else:			
								urlTab.append((URL1,'1'))
						else:
							Liste_els_3 = re.findall('sources.*?file":"(.*?)"', data, re.S)	
							if Liste_els_3:
								URL1=Liste_els_3[0]				
								urlTab.append((Liste_els_3[0],'0'))
					else:
						urlTab.append((Liste_els_3[0],'1'))
		except:
			printDBG('erreur')
		return urlTab

	def getArticle(self, cItem):
		printDBG("Animekom.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc = cItem['desc']
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('row description\'>(.*?)</d', data, re.S)
			if lst_dat:
				desc=desc+'\\n'+ph.clean_html(lst_dat[0])

		icon = cItem.get('icon')
		title = cItem['title']			
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]


	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelms(cItem)
			
