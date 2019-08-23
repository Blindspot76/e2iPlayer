# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph

from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist,unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams

###################################################


import re
import base64
import time
def getinfo():
	info_={}
	info_['name']='Hdo.To'
	info_['version']='1.1 08/07/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='104'#'401'
	info_['desc']='Films & Series'
	info_['icon']='https://i.ibb.co/CvVHrTr/logo-2x.png'
	info_['recherche_all']='1'
	info_['update']='site changed to https://solarmoviehd.ru'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'hdo.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'
		self.MAIN_URL = 'https://hdo.to'
		self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'with_metadata':True,'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}



	def getPage(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		sts, data = self.cm.getPage(baseUrl, addParams, post_data)
		printDBG(str(sts))
		try:
			if "'jschl-answer'" in data:
				try:
					import cookielib
					from Plugins.Extensions.IPTVPlayer.tsiplayer.libs import cfscrape		
					scraper = cfscrape.create_scraper()
					data = scraper.get(baseUrl).content
					tokens, user_agent=cfscrape.get_tokens(self.MAIN_URL)
					sts = True
					cj = self.cm.getCookie(self.COOKIE_FILE)
					
					cook_dat=re.findall("'(.*?)'.*?'(.*?)'", str(tokens), re.S)			
					for (cookieKey,cookieValue) in cook_dat:
						cookieItem = cookielib.Cookie(version=0, name=cookieKey, value=cookieValue, port=None, port_specified=False, domain='.'+self.cm.getBaseUrl(baseUrl, True), domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=time.time()+3600*48, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
						cj.set_cookie(cookieItem)		

					cj.save(self.COOKIE_FILE, ignore_discard = True)
				except:
					addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
					sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
		except:
			printDBG('erreur')
		return sts, data


	def getPage1(self,baseUrl, addParams = {}, post_data = None):
		while True:
			if addParams == {}: addParams = dict(self.defaultParams)
			origBaseUrl = baseUrl
			baseUrl = self.cm.iriToUri(baseUrl)
			addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
			sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
			printDBG(str(sts))
			if sts and 'class="loading"' in data:
				GetIPTVSleep().Sleep(10)
				continue
			break
		return sts, data
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'Movies', 'mode':'30','url':'https://hdo.to/movies'},
					{'category':hst,'title': 'Tv Series', 'mode':'30','url':'https://hdo.to/tv-series'},
					{'category':hst,'title': 'A-Z List', 'mode':'20'},
					{'category':hst,'title': 'By Filter', 'mode':'21'},				
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})	
				
	def showmenu1(self,cItem):
		hst='host2'
		img_=cItem['icon']	
		sts, data = self.getPage(self.MAIN_URL+'/az-list')
		if sts:
			data_list = re.findall('class="ulclear az-list">(.*?)</ul>', data, re.S)
			if data_list:
				data_list2 = re.findall('<li.*?href="(.*?)".*?">(.*?)<', data_list[0], re.S)
				for (url,titre) in data_list2:
					self.addDir({'import':cItem['import'],'category' : hst,'url': url,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
			
		
	def showmenu2(self,cItem):
		hst='host2'
		img_=cItem['icon']	
		count_=cItem.get('count',0)
		data_=cItem.get('data','')
		if count_==0:
			sts, data = self.getPage(self.MAIN_URL+'/movies')
			if sts:
				data_list = re.findall('<div id="filter"(.*?)class="filter-btn">', data, re.S)
				if data_list: data_=data_list[0]
				
		if count_==0:
			self.addMarker({'title':'\c00????00'+'Sort By:','desc':''})
			data_list = re.findall('class="sort.*?data-sort="(.*?)".*?</i>(.*?)<', data_, re.S)
			for (code,titre) in data_list:
				url='https://hdo.to/filter?sort_by='+code
				self.addDir({'import':cItem['import'],'category' : hst,'url': url,'title':titre,'desc':'','icon':cItem['icon'],'mode':'21','count':1,'data':data_})	
		elif count_==1:
			url=cItem['url']
			self.addMarker({'title':'\c00????00'+'Type:','desc':''})
			data_list = re.findall('class="fc-filmtype(.*?)</ul>', data_, re.S)
			if data_list:
				data1=data_list[0]
				data_list = re.findall('<li.*?value="(.*?)".*?">(.*?)<', data1, re.S)
				for (code,titre) in data_list:
					urlf=url+'&type='+code
					self.addDir({'import':cItem['import'],'category' : hst,'url': urlf,'title':titre,'desc':'','icon':cItem['icon'],'mode':'21','count':2,'data':data_})	
		elif count_==2:
			url=cItem['url']
			self.addMarker({'title':'\c00????00'+'Quality:','desc':''})
			data_list = re.findall('class="fc-quality(.*?)</ul>', data_, re.S)
			if data_list:
				data1=data_list[0]
				data_list = re.findall('<li.*?value="(.*?)".*?">(.*?)<', data1, re.S)
				for (code,titre) in data_list:
					urlf=url+'&quality='+code
					self.addDir({'import':cItem['import'],'category' : hst,'url': urlf,'title':titre,'desc':'','icon':cItem['icon'],'mode':'21','count':3,'data':data_})	
			
		
		elif count_==3:
			url=cItem['url']
			self.addMarker({'title':'\c00????00'+'Genre:','desc':''})
			data_list = re.findall('class="fc-genre(.*?)</ul>', data_, re.S)
			if data_list:
				data1=data_list[0]
				self.addDir({'import':cItem['import'],'category' : hst,'url': url+'&genre=all','title':'All','desc':'','icon':cItem['icon'],'mode':'21','count':4,'data':data_})	
				data_list = re.findall('<li.*?value="(.*?)".*?">(.*?)<', data1, re.S)
				for (code,titre) in data_list:
					urlf=url+'&genre='+code
					self.addDir({'import':cItem['import'],'category' : hst,'url': urlf,'title':titre,'desc':'','icon':cItem['icon'],'mode':'21','count':4,'data':data_})	
		
		elif count_==4:
			url=cItem['url']
			self.addMarker({'title':'\c00????00'+'Country:','desc':''})
			data_list = re.findall('class="fc-country(.*?)</ul>', data_, re.S)
			if data_list:
				data1=data_list[0]
				self.addDir({'import':cItem['import'],'category' : hst,'url': url+'&country=all','title':'All','desc':'','icon':cItem['icon'],'mode':'21','count':5,'data':data_})	
				data_list = re.findall('<li.*?value="(.*?)".*?">(.*?)<', data1, re.S)
				for (code,titre) in data_list:
					urlf=url+'&country='+code
					self.addDir({'import':cItem['import'],'category' : hst,'url': urlf,'title':titre,'desc':'','icon':cItem['icon'],'mode':'21','count':5,'data':data_})	
				
		elif count_==5:
			url=cItem['url']
			self.addMarker({'title':'\c00????00'+'Release:','desc':''})
			data_list = re.findall('class="fc-release(.*?)</ul>', data_, re.S)
			if data_list:
				data1=data_list[0]
				data_list = re.findall('<li.*?value="(.*?)".*?">(.*?)<', data1, re.S)
				for (code,titre) in data_list:
					if titre.strip()!='':
						urlf=url+'&year='+code
						self.addDir({'import':cItem['import'],'category' : hst,'url': urlf,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		if '?' in url1:
			x1,x2=url1.split('?',1)
			url1=x1+'/'+str(page)+'?'+x2
		else:
			url1=url1+'/'+str(page)
		sts, data = self.getPage(url1)
		if sts:
			data_list = re.findall('class="movie-item".*?title="(.*?)".*?href="(.*?)".*?class="gr-.*?>(.*?)<.*?src="(.*?)"', data, re.S)
			i=0
			for (titre,url,inf,image) in data_list:
				i=i+1
				titre=titre+' \c0000????('+inf+')'
				self.addVideo({'import':cItem['import'],'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':'','icon':image,'hst':'tshost','good_for_fav':True})	
			if i>19:
				self.addDir({'import':cItem['import'],'title':'\c0000????Page Suivante','page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/search/'+str_ch+'/'+str(page)
		sts, data = self.getPage(url_)
		if sts:
			data_list = re.findall('class="movie-item".*?title="(.*?)".*?href="(.*?)".*?class="gr-.*?>(.*?)<.*?src="(.*?)"', data, re.S)
			i=0
			for (titre,url,inf,image) in data_list:
				i=i+1
				titre=titre+' \c0000????('+inf+')'
				self.addVideo({'import':extra,'category' : 'host2','url': url,'title':titre,'desc':'','icon':image,'hst':'tshost','EPG':True,'good_for_fav':True})	
			

	def get_links(self,cItem):
		urlTab = []
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			data_list = re.findall('this.page.identifier = "(.*?)"', data, re.S)
			if data_list:
				URL1='https://hdo.to/ajax/movie/episodes/'+data_list[0]
				sts, data = self.getPage(URL1)
				#data_list1 = re.findall('<li>.*?data-toggle.*?tab.*?>(.*?)<', data, re.S)
				data_list2 = re.findall('<li class.*?data-server.*?"(.*?)".*?data-id.*?"(.*?)".*?title=.*?">(.*?)<', data, re.S)
				for (server,code_id,titre) in  data_list2:
					server=server.replace('\\','')
					if server==  '14': server='OPENLOAD'
					elif server=='15': server='OPENLOAD 2'
					elif server=='16': server='VidCloud'
					elif server=='1' : server='VIP 1'  
					elif server=='6' : server='VIP 6' 


					titre=titre+' \c00????00('+server+')'
					urlTab.append({'name':titre, 'url':'hst#tshost#'+code_id, 'need_resolve':1})
		return urlTab	


	def getVideos(self,videoUrl):
		urlTab = []	
		sUrl = 'https://hdo.to/ajax/movie/get_embed/'+videoUrl.replace('\\','')

		sts, data = self.getPage(sUrl)
		if sts:
			Liste_els_3 = re.findall('src".*?"(.*?)"', data, re.S)	
			if Liste_els_3:
				urlTab.append((Liste_els_3[0].replace('\\',''),'1'))
		return urlTab





			
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc=''
		
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			data_list = re.findall('this.page.identifier = "(.*?)"', data, re.S)
			if data_list:
				URL1='https://hdo.to/ajax/movie/info/'+data_list[0]
				sts, data = self.getPage(URL1)
				data=data.replace('\\','')
				lst_dat2=re.findall('Country:(.*?)</div>', data, re.S)
				if lst_dat2: otherInfo1['country'] = ph.clean_html(lst_dat2[0])
				lst_dat2=re.findall('Quality(.*?)</div>', data, re.S)
				if lst_dat2: otherInfo1['quality'] = ph.clean_html(lst_dat2[0])	
				lst_dat2=re.findall('Duration(.*?)</div>', data, re.S)
				if lst_dat2: otherInfo1['duration'] = ph.clean_html(lst_dat2[0])				
				lst_dat2=re.findall('Year(.*?)</div>', data, re.S)
				if lst_dat2: otherInfo1['year'] = ph.clean_html(lst_dat2[0])				
				lst_dat2=re.findall('IMDb(.*?)</div>', data, re.S)
				if lst_dat2: otherInfo1['imdb_rating'] = ph.clean_html(lst_dat2[0])				
										
				lst_dat2=re.findall('Genres:(.*?)</div>', data, re.S)
				if lst_dat2: otherInfo1['genres'] = ph.clean_html(lst_dat2[0])				


				lst_dat2=re.findall('Actors:(.*?)</div>', data, re.S)
				if lst_dat2: otherInfo1['actors'] = ph.clean_html(lst_dat2[0])	

									
				lst_dat2=re.findall('class="f-desc.*?>(.*?)</p>', data, re.S)
				if lst_dat2: desc = ph.clean_html(lst_dat2[0])			
			
					
		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

		 

	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='21':
			self.showmenu2(cItem)
		if mode=='30':
			self.showitms(cItem)			
			
