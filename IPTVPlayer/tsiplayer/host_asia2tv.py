# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
try:
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
except:
	pass 

import re,urllib,cookielib,time



def getinfo():
	info_={}
	info_['name']='Asia2tv'
	info_['version']='1.3 07/11/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات آسياوية'
	info_['icon']='https://i.ibb.co/MpXLVK8/x2p8y3u4.png'
	info_['recherche_all']='1'
	info_['update']='Fix cover' 
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'asia2tv.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
		self.MAIN_URL = 'https://astv.co'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		#self.getPage = self.cm.getPage


	def getPage(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams) 
		addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
		return sts, data


	def showmenu0(self,cItem):
		hst='host2'
		img=cItem['icon']
		asia_TAB=[ 			
					{'category':hst,'title': 'افلام آسيوية',    'mode':'30' ,'icon':img ,'url':self.MAIN_URL+'/category/asia-movies/'},						
					{'category':hst,'title': 'الدراما',        'mode':'30' ,'icon':img ,'url':self.MAIN_URL+'/category/list-drama/'},						
					{'category':hst,'title': 'الحلقات الجديدة','mode':'30' ,'icon':img ,'url':self.MAIN_URL+'/n-episodes/'},
					{'category':hst,'title': tscolor('\c0000????') + 'حسب النوع',    'mode':'20' ,'icon':img ,'sub_mode':0},
					{'category':hst,'title': tscolor('\c0000????') + 'حسب الحالة',      'mode':'20' ,'icon':img ,'sub_mode':1},
					{'category':hst,'title': tscolor('\c0000????') + 'حسب التصنيف' ,       'mode':'20' ,'icon':img ,'sub_mode':2},
					{'category':'search'  ,'title':tscolor('\c00????30') + _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':img},
					]
		self.listsTab(asia_TAB, {'import':cItem['import'],'name':hst})
		
	def showmenu1(self,cItem):		
		gnr2=cItem['sub_mode']
		sts, data = self.getPage(self.MAIN_URL+'/category/list-drama/')
		if (gnr2<2):
			pat='class="dropdown-toggle">(.*?)</ul>'
			ind_=gnr2
		else:	
			pat='class="col-md-11">(.*?)</ul>'
			ind_=0				
		if sts:
			Liste_films_data = re.findall(pat, data, re.S)
			if Liste_films_data:
				Liste_films_data0 = re.findall('<li.*?href="(.*?)">(.*?)<', Liste_films_data[ind_], re.S)
				for (url,titre) in Liste_films_data0:
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :'host2', 'url':url, 'title':self.cleanHtmlStr( titre), 'desc':'', 'icon':cItem['icon'], 'mode':'30'})						
		
		
	def showitms(self,cItem):		
		url=cItem['url']
		page = cItem.get('page', 1)
		if 'n-episodes/' in url:
			URL=self.MAIN_URL+'/n-episodes/?action=load_more_new_episode&more='+str(page)
		else:
			URL=url+'page/'+str(page)+'/'
			
		sts, data = self.getPage(URL)
		if sts:
			i=0			
			Liste_films_data = re.findall('class="postmoveie">.*?post-date">(.*?)<.*?href="(.*?)".*?thumb-bg">(.*?)</div>.*?<h4.*?">(.*?)<', data, re.S)
			cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
			for (desc,url1,image,name_eng) in Liste_films_data:
				i=i+1
				img_data = re.findall('data-lazy-src="(.*?)"', image, re.S)
				if not img_data: img_data = re.findall('src="(.*?)"', image, re.S)
				if img_data:
					image=img_data[0]
				else:
					image=''
				if image.startswith('//'): image='http:'+image
				image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
				desc0,name_eng = self.uniform_titre(name_eng.strip())
				if desc.strip()!='':
					desc = tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+desc
				desc=desc0+desc
				
				self.addDir({'import':cItem['import'],'good_for_fav':True, 'EPG':True, 'category':'host2', 'url':url1, 'title':name_eng, 'desc':desc, 'icon':image, 'mode':'31','hst':'tshost'} )
			if i>24:
				self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':'Page Suivante','page':page+1,'desc':'Page Suivante','icon':cItem['icon'],'mode':'30'} )
		
	def showelems(self,cItem):
		url=cItem['url']
		title_=cItem['title']
		sts, data = self.getPage(url)
		if sts:
			Liste_films_data = re.findall('class="episode_box_tabs_container">(.*?)<div class="row">', data, re.S)
			if Liste_films_data:
				Liste_films_data0 = re.findall('href="(.*?)".*?titlepisode">(.*?)<.*?numepisode">(.*?)<', Liste_films_data[0], re.S)
				for (url1,titre,num) in Liste_films_data0:
					if 'الحلقة Movie' in titre:
						titre=title_
					else:
						titre=titre+' - '+num
					self.addVideo({'import':cItem['import'],'good_for_fav':True, 'name':'categories', 'category':'video', 'url':url1, 'title':titre, 'desc':'', 'icon':cItem['icon'], 'hst':'tshost'} )
		
		
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
			Liste_films_data = re.findall('class="postmoveie">.*?post-date">(.*?)<.*?href="(.*?)".*?src="(.*?)".*?<h4.*?">(.*?)<', data, re.S)
			for (desc,url1,image,name_eng) in Liste_films_data:
				image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
				desc0,name_eng = self.uniform_titre(name_eng.strip())
				if desc.strip()!='':
					desc = tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+desc
				desc=desc0+desc
				self.addDir({'import':extra,'good_for_fav':True, 'EPG':True, 'name':'categories', 'category':'host2', 'url':url1, 'title':name_eng, 'desc':desc, 'icon':image, 'mode':'31','hst':'tshost'} )

			
	def getArticle(self, cItem):
		printDBG("Asia2tv.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc = ''
		sts, data = self.cm.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('info-detail-single">(.*?)</ul>(.*?)</div>(.*?)</div>', data, re.S)
			if lst_dat:
				lst_dat0=re.findall('sdhdfhd">(.*?)</div>', lst_dat[0][0], re.S)
				if lst_dat0: otherInfo1['quality'] = ph.clean_html(lst_dat0[0])
				lst_dat0=re.findall('post_imdb">(.*?)</div>', lst_dat[0][0], re.S)
				if lst_dat0: otherInfo1['imdb_rating'] = ph.clean_html(lst_dat0[0])		
				lst_dat0=re.findall('box-date">(.*?)</div>', lst_dat[0][0], re.S)
				if lst_dat0: otherInfo1['age_limit'] = ph.clean_html(lst_dat0[0])				
				lst_dat0=re.findall('<li>(.*?)</span>(.*?)</', lst_dat[0][0], re.S)
				for (x1,x2) in lst_dat0:
					if 'اسم المسلسل'  in x1: otherInfo1['original_title'] = x2
					if 'الاسم بالعربي' in x1: otherInfo1['alternate_title'] = x2
					if 'الحلقات'      in x1: otherInfo1['episodes'] = x2
					if 'البلد'        in x1: otherInfo1['country'] = x2
					if 'موعد البث'    in x1: otherInfo1['first_air_date'] = x2
				otherInfo1['genre'] = ph.clean_html(lst_dat[0][1])	
				desc = ph.clean_html(lst_dat[0][2])	
		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

	def get_links(self,cItem): 	
		urlTab = []
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			Liste_els = re.findall('getplay.*?titlea="(.*?)".*?hrefa=.*?\?url=(.*?)"', data, re.S)
			for (host_,Url) in Liste_els:
				Url = Url.replace('%3A',':')
				Url = Url.replace('%2F','/')
				Url = Url.replace('%3F','?')
				Url = Url.replace('%3D','=')

				if Url.startswith('//'):
					Url='http:'+Url
				if ('userpro' not in Url) and('بتغير' not in host_):
					urlTab.append({'name':host_, 'url':Url, 'need_resolve':1})						
		return urlTab
		 

			
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelems(cItem)
