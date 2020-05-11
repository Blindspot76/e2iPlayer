# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,cryptoJS_AES_decrypt,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################


import re
import base64
import hashlib

def getinfo():
	info_={}
	info_['name']='Vumoo.To'
	info_['version']='1.2 08/03/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'#'401'
	info_['desc']='Films & Series'
	info_['icon']='http://vumoo.to/images/logo.png'
	info_['recherche_all']='1'
	info_['update']='Fix Links'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'vumoo.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'http://vumoo.to'
		self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'with_metadata':True,'no_redirection':False,'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.password = 'iso10126'


	def getPage(self, url, addParams={}, post_data=None):
		if addParams == {}:
			addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file': self.COOKIE_FILE, 'User-Agent': self.HTTP_HEADER['User-Agent']}
		return self.cm.getPageCFProtection(url, addParams, post_data)


		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'Movies', 'mode':'30','url':self.MAIN_URL+'/movies'},
					{'category':hst,'title': 'Tv Series', 'mode':'30','url':self.MAIN_URL+'/tv-series'},			
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})	
				
		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		url1=url1+'/page/'+str(page)
		sts, data = self.getPage(url1)
		if sts:
			data_list = re.findall('class="intro">.*?href="(.*?)".*?src="(.*?)".*?<h3.*?>(.*?)<', data, re.S)
			i=0
			for (url,image,titre) in data_list:
				i=i+1
				if not url.startswith('http'):
					url=self.MAIN_URL+url
				self.addDir({'import':cItem['import'],'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':'','icon':image,'hst':'tshost','good_for_fav':True,'mode':'31'})	
			if i>23:
				self.addDir({'import':cItem['import'],'title':tscolor('\c0000????')+'Next Page','page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	
	
	def showelms(self,cItem):	
		urlTab = []
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			data_list = re.findall('class="tab-pane.*?id="(.*?)".*?<ul(.*?)</ul', data, re.S)
			for (server,data1) in data_list:
				server=server.replace('server-','Server ')
				self.addMarker({'title':tscolor('\c00????00')+server,'icon':cItem['icon']} )
				data_list = re.findall('embedUrl="(.*?)">(.*?)<', data1, re.S)
				for (Url,titre) in data_list:
					data_h={'name':titre, 'url':'hst#tshost#'+Url+'|'+URL, 'need_resolve':1}
					self.addVideo({'import':cItem['import'],'category' : 'host2','url': Url,'title':titre,'desc':'','icon':cItem['icon'],'hst':'tshost','good_for_fav':True,'data_h':data_h})	
	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/search?t=2018BC65S4359XSMloz2HpQU2bXW4T_cTmTZFKx_zfeb1NAvH2OpqEK-aJloawZL-xo426IMAVLtpWZ3SK1d==&q='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			data = json_loads(data)
			for elm in data['suggestions']:
				titre    = elm['value']
				url      = elm['data']['href']
				image    = elm['data']['image']		
				typ_     = elm['data']['type']
				titre=titre+' '+tscolor('\c0000????')+'('+typ_+')'
				if not url.startswith('http'):
					url=self.MAIN_URL+url			
				self.addDir({'import':extra,'category' : 'host2','url': url,'title':titre,'desc':'','icon':image,'hst':'tshost','EPG':True,'good_for_fav':True,'mode':'31'})	
		

	def get_links(self,cItem):
		urlTab = []
		data_h=cItem['data_h']
		urlTab.append(data_h)
		return urlTab	


	def getVideos(self,videoUrl):
		urlTab = []	
		videoUrl,referer = videoUrl.split('|')
		# New methode
		if 'meomeo' in videoUrl:
			self.defaultParams['header']['Referer']=referer
			sts, data = self.getPage(videoUrl)
			if sts:			
				printDBG('data='+data)
				Liste_els_5 = re.findall('"playlist":.*?"file":"(.*?)"', data, re.S)
				if Liste_els_5:
					url_1=Liste_els_5[0]
					if url_1.startswith('//'): url_1 = 'https:'+url_1
					urlTab.append((url_1,'3'))				
		# Old methode
			Liste_els_3 = re.findall('embedVal="(.+?)"', data, re.S)	
			if Liste_els_3:
				encrypted = base64.b64decode(Liste_els_3[0])
				salt = encrypted[8:16]
				decrypted = cryptoJS_AES_decrypt(encrypted[16:], self.password, salt)
				Liste_els_4 = re.findall('url":"(.*?)"', decrypted, re.S)
				if Liste_els_4:
					url_=Liste_els_4[0]	
					if self.up.checkHostSupport(url_)==1:
						urlTab.append((url_,'1'))
					else:	
						sts, data = self.getPage(url_)
						if sts:
							Liste_els_5 = re.findall('media="(.*?)"', data, re.S)
							if Liste_els_5:
								url_1=Liste_els_5[0]				
								urlTab.append((url_1,'3'))
		return urlTab

			
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc=''
		
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			lst_dat2=re.findall('<strong>Genres(.*?)</div>', data, re.S)
			if lst_dat2: otherInfo1['genres'] = ph.clean_html(lst_dat2[0])
			lst_dat2=re.findall('<strong>Directors(.*?)</div>', data, re.S)
			if lst_dat2: otherInfo1['directors'] = ph.clean_html(lst_dat2[0])			
			lst_dat2=re.findall('<strong>Writers(.*?)</div>', data, re.S)
			if lst_dat2: otherInfo1['writers'] = ph.clean_html(lst_dat2[0])				
			lst_dat2=re.findall('<strong>Release(.*?)</div>', data, re.S)
			if lst_dat2: otherInfo1['released'] = ph.clean_html(lst_dat2[0])				
			lst_dat2=re.findall('<strong>Actors(.*?)</div>', data, re.S)
			if lst_dat2: otherInfo1['actors'] = ph.clean_html(lst_dat2[0])	
			lst_dat2=re.findall('<strong>IMDb(.*?)</div>', data, re.S)
			if lst_dat2: otherInfo1['imdb_rating'] = ph.clean_html(lst_dat2[0])				
			lst_dat2=re.findall('<strong>Countries(.*?)</div>', data, re.S)
			if lst_dat2: otherInfo1['country'] = ph.clean_html(lst_dat2[0])
			lst_dat2=re.findall('<strong>Runtime(.*?)</div>', data, re.S)
			if lst_dat2: otherInfo1['duration'] = ph.clean_html(lst_dat2[0])				
					
			lst_dat2=re.findall('</h1><span>(.*?)</span>', data, re.S)
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
		if mode=='31':
			self.showelms(cItem)						
