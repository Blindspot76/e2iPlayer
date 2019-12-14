# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Components.config import config

import re


def getinfo():
	info_={}
	info_['name']='Cimaclub.Com'
	info_['version']='1.6 20/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام, مسلسلات و انمي عربية و اجنبية'
	info_['icon']='https://i.pinimg.com/originals/f2/67/05/f267052cb0ba96d70dd21e41a20a522e.jpg'
	info_['recherche_all']='1'
	info_['update']='Fix Hosts Links'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'cimaclub.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://m.cimaclub.com'
		self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.AJAX_HEADER = dict(self.HTTP_HEADER)
		self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
		self.defaultParams = {'header':self.HTTP_HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

	def getPage(self, baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
		
	def cimaclub_plus_extract(self,code,id):	
		URL=self.MAIN_URL+'/wp-content/themes/Cimaclub/servers/server.php?q='+code+'&i='+id
		URL_=''
		sts, data = self.getPage(URL)
		if sts:
			printDBG('dddddaaaaattttaaaaa'+data)
			_data2 = re.findall('iframe.*?src=(.*?) ',data, re.IGNORECASE)
			if _data2:
				URL_=_data2[0]
				URL_=URL_.replace('"','')
				URL_=URL_.replace("'",'')
				if URL_.startswith('//'):
					URL_='http:'+URL_
		return URL_

		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']
		Cimaclub_TAB=[{'category':hst,'title': 'Films'    ,'mode':'20'  ,'sub_mode':'film'},
					  {'category':hst,'title': 'Series'   ,'mode':'20'  ,'sub_mode':'serie'},
					  {'category':hst,'title': 'Other'    ,'mode':'20'  ,'sub_mode':'other'},
					  {'category':hst,'title': 'Filter'   ,'mode':'20' ,'sub_mode':'filter'},						  
					  {'category':'search'  ,'title': _('Search'),'search_item':True,'page':1,'hst':'tshost'},
					]
		self.listsTab(Cimaclub_TAB, {'icon':img_,'import':cItem['import']})

	def showmenu1(self,cItem):
		gnr2=cItem['sub_mode']			 
		url=self.MAIN_URL
		img=cItem['icon']
	
		if gnr2=='filter':
			Cimaclub_filter=[{'category':'host2', 'title': 'الاحدث'       , 'url':self.MAIN_URL+'/wp-content/themes/Cimaclub/filter/recent.php', 'desc':'', 'icon':img, 'mode':'30', 'page':1},
							 {'category':'host2', 'title': 'المثبت'      , 'url':self.MAIN_URL+'/wp-content/themes/Cimaclub/filter/pin.php'   , 'desc':'', 'icon':img, 'mode':'30', 'page':0},						  
							 {'category':'host2', 'title': 'الاكثر مشاهدة', 'url':self.MAIN_URL+'/most-views/'                                 , 'desc':'', 'icon':img, 'mode':'30', 'page':1},						  
							 {'category':'host2', 'title': 'الأعلى تقييماً', 'url':self.MAIN_URL+'/top-imdb/'                                   , 'desc':'', 'icon':img, 'mode':'30', 'page':1},	 
							]
			self.listsTab(Cimaclub_filter, {'name':'categories','import':cItem['import']})
		else:
			sts, data = self.getPage(url)
			if sts:
				lst_data = re.findall('<ul class="sub-menu">(.*?)</ul>',data, re.S)
				if lst_data:
					if gnr2=='film':
						data1= lst_data[0]
					elif gnr2=='serie':
						self.addDir({'category' :'host2', 'url':self.MAIN_URL+'/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%b9%d8%b1%d8%a8%d9%8a/%d8%b1%d9%85%d8%b6%d8%a7%d9%86-2019/', 'title':'رمضان 2019', 'desc':'رمضان 2019', 'icon':img, 'mode':'30','page':1,'import':cItem['import']})					
						data1= lst_data[1]		
					elif gnr2=='other':
						data1= lst_data[2]
					lst_data1 = re.findall('<li.*?href="(.*?)">(.*?)<',data1, re.S)
					for (url1,titre1) in lst_data1:
						self.addDir({'import':cItem['import'],'category' :'host2', 'url':url1, 'title':titre1, 'desc':titre1, 'icon':img, 'mode':'30', 'page':1})
					if gnr2=='film':
						lst_data0 = re.findall('FooterMenu">(.*?)</ul>',data, re.S)
						if lst_data0:
							lst_data01 = re.findall('<li.*?href="(.*?)">(.*?)<',lst_data0[0], re.S)
							for (url11,titre11) in lst_data01:
								if ('الرئيسية' not in titre11) and ('الطلبات' not in titre11) and ('سلاسل' not in titre11):
									self.addDir({'import':cItem['import'],'category' :'host2', 'url':url11, 'title':titre11, 'desc':titre11, 'icon':img, 'mode':'30', 'page':1})
								
						self.addMarker({'title':tscolor('\c0000??00')+'Films by genre','icon':'','desc':''})				
						lst_data2 = re.findall('<h2>نوع العرض</h2>(.*?)</ul',data, re.S)
						if lst_data2:
							lst_data3 = re.findall('<li.*?href="(.*?)">(.*?)</li>',lst_data2[0], re.S)
							for (url3,titre3) in lst_data3:
								if url3=='#':url3=self.MAIN_URL					
								self.addDir({'import':cItem['import'],'category' :'host2', 'url':url3, 'title':ph.clean_html(titre3), 'desc':ph.clean_html(titre3), 'icon':img, 'mode':'30','page':1})					
		
	def showitms(self,cItem):
		page=cItem.get('page',1)
		url0=cItem['url']
		url=url0
		if page!=0:
			if (url0.endswith('.php')or url0==self.MAIN_URL): 
				url=url0+'/?page='+str(page)+'/'
			elif '?' in url0:
				x1,x2 = url0.split('?')
				url=x1+'page/'+str(page)+'/?'+x2
			else:
				url=url0+'page/'+str(page)+'/'
		#sts, data = self.cm.getPage(url)	
		sts, data = self.getPage(url)	
		if sts:		
			lst_data=re.findall('<div class="Block">.*?href="(.*?)".*?src="(.*?)".*?TitleDesc">(.*?)</ul>.*?<h2>(.*?)<.*?DescPost">(.*?)</a>.*?BlockDets">(.*?)</ul>', data, re.S)
			for (url1,image,desc0,name_eng,desc,desc1) in lst_data:
				name_eng=name_eng.replace(' اون لاين','')
				name_eng=name_eng.replace('مسلسل ','')
				name_eng=name_eng.replace('فيلم ','')
				desc=self.get_desc(desc0,desc1)
				self.addDir({'import':cItem['import'],'good_for_fav':True,'category':'host2', 'url':url1, 'title':ph.clean_html(name_eng), 'desc':desc, 'icon':image, 'mode':'31','EPG':True,'hst':'tshost'} )							
			if page!=0:
				self.addDir({'import':cItem['import'],'category':'host2', 'url':url0, 'title':tscolor('\c0000??00')+'Page Suivante', 'page':page+1, 'desc':'Page Suivante', 'icon':cItem['icon'], 'mode':'30'})	

	def get_desc(self,desc0,desc1):
		desc = ''

			
		elm_list = re.findall('<li.*?<em>(.*?)</em>(.*?)</li>', desc1, re.S)
		for (href,titre) in elm_list:
			if 'المشاهدات' in href: desc=desc+tscolor('\c00??????')+'Views: '+tscolor('\c00????00')+ph.clean_html(titre)+'\n'				
			if 'سنة' in href: desc=desc+tscolor('\c00??????')+'Year: '+tscolor('\c00????00')+ph.clean_html(titre)+'\n'				
			if 'النوع' in href: desc=desc+tscolor('\c00??????')+'Genre: '+tscolor('\c00????00')+ph.clean_html(titre)+'\n'			


		elm_list = re.findall('href="(.*?)">(.*?)<', desc0, re.S)
		for (href,titre) in elm_list:
			if 'category' in href: desc=desc+tscolor('\c00??????')+'Category: '+tscolor('\c00????00')+ph.clean_html(titre)+'\n'				
			if 'quality' in href: desc=desc+tscolor('\c00??????')+'Quality: '+tscolor('\c00????00')+ph.clean_html(titre)+'\n'	
			

			
		return desc




	def showelems(self,cItem):
		url0=cItem['url']	
		titre=cItem['title']			
		lst=[]
		tab=[] 
		#sts, data = self.cm.getPage(url0)	
		sts, data = self.getPage(url0)
		if sts:
			cat_data=re.findall('<div data-season="(.*?)".*?href="(.*?)">(.*?)<', data, re.S)		
			if cat_data:
				cat_data2=re.findall('<div class="season" data-filter="(.*?)">(.*?)<', data, re.S)
				for (dat_,name_) in cat_data2:
					elem={'code':dat_.strip(),'name' : name_.strip(),'len':len(dat_.strip())}
					lst.append(elem)
				for (data,url,titre) in cat_data:
					data=data.strip()
					fnd=0
					for elm in lst:
						if str(elm['code'])==str(data):
							data=elm['name']
							fnd=1
							break
					if fnd==1:
						try:
							nb=int(titre.strip())
						except:
							nb=0
						tab.append((data,nb,url))
				tab=sorted(tab, key = lambda x: (x[0], x[1]))		
				for(data_,titre_,url_) in tab:
					data_=data_.replace('موسم ','Saison ') 
					Ep=str(titre_)
					if len(Ep)==1: 
						Ep='0'+Ep
					Ep=data_+' - E'+Ep
					params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url_,'title':Ep,'desc':'','icon':cItem['icon'],'hst':'tshost'} 
					self.addVideo(params)					
			else:
				'''cat_data=re.findall('<div class="moviesBlocks">(.*?)<div class="moviesBlocks">', data, re.S)
				if cat_data:
					data2=cat_data[0]'''
				params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url0,'title':titre,'desc':'','icon':cItem['icon'],'desc':cItem['desc'],'hst':'tshost'} 
				self.addVideo(params)						
				self.addMarker({'title':tscolor('\c0000??00')+'نرشح لكم','icon':'','desc':''})	
				cat_data=re.findall('<div class="Block">.*?href="(.*?)".*?src="(.*?)".*?<h2>(.*?)<.*?DescPost">(.*?)</a>', data, re.S)
				if cat_data:
					for (url,image,name_eng,desc) in cat_data:
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng,'desc':ph.clean_html(desc),'icon':image,'hst':'tshost'} 
						self.addVideo(params)	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			cat_data=re.findall('<div class="Block">.*?href="(.*?)".*?src="(.*?)".*?<h2>(.*?)<.*?DescPost">(.*?)</a>', data, re.S)
			for (url1,image,name_eng,desc) in cat_data:
				params = {'import':extra,'good_for_fav':True,'category' : 'host2','url': url1,'title':ph.clean_html(name_eng),'desc':ph.clean_html(desc),'icon':image,'mode':'31','EPG':True,'hst':'tshost'} 
				self.addDir(params)		
		
	def get_links(self,cItem): 	
		urlTab = []	
		URL=cItem['url']#+'?view=1'
		post_data={'view':'1'}				
		sts, data = self.getPage(URL, post_data=post_data)
		if sts:
			code_data = re.findall("data: 'q=(.*?)&", data, re.S)
			if code_data:
				code=code_data[0]
				server_data = re.findall('data-server="(.*?)">(.*?)</li>', data, re.S)	
				for (id,name) in server_data:
					if config.plugins.iptvplayer.ts_dsn.value:
						URL_=self.cimaclub_plus_extract(code,id)
						if URL_!='':
							urlTab.append({'name':self.up.getDomain(URL_), 'url':URL_, 'need_resolve':1})
					else:
						urlTab.append({'name':ph.clean_html(name), 'url':'hst#tshost#'+code+'|'+id, 'need_resolve':1})
				if urlTab == []:
					for i in range(1,14):
						URL_=self.cimaclub_plus_extract(code,str(i))
						if URL_!='':
							urlTab.append({'name':self.up.getDomain(URL_), 'url':URL_, 'need_resolve':1})				
		return urlTab
		 
	def getVideos(self,videoUrl):
		urlTab = []	
		code,id=videoUrl.split('|')
		urlTab.append((self.cimaclub_plus_extract(code,id),'1'))
		return urlTab
				
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc = cItem.get('desc','')
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('StoryContentExtend">(.*?)</div>', data, re.S)
			if lst_dat: 
				if ph.clean_html(lst_dat[0])!='':
					desc = tscolor('\c00????00')+'Story: '+tscolor('\c00??????')+ph.clean_html(lst_dat[0])
		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

	
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
