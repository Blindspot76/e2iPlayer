# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

import re



def getinfo():
	info_={}
	info_['name']='Animekom.Com'
	info_['version']='1.1 07/07/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='202'
	info_['desc']='جميع الإنميات مترجمة عربي، والأفلام والأوفات'
	info_['icon']='https://i.ibb.co/nbJGfT9/cssswe6b.png'
	info_['recherche_all']='0'
	info_['update']='Bugs Fix'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'animekom.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'http://www.animekom.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage


	def showmenu0(self,cItem):
		hst='host2'
		Animekom_TAB = [
							{'category':hst,      'title':'Animes'     , 'mode':'20'},
							{'category':hst,      'title':'Films'      , 'mode':'21'},							
							{'category':'search', 'title':_('Search')  ,'search_item':True,'page':1,'hst':'tshost'},
							]
		self.listsTab(Animekom_TAB, {'icon':cItem['icon'],'import':cItem['import']})						

	def showmenu1(self,cItem):
		Anim_CAT_TAB = [{'title': 'Animes',          'mode':'30','Url':'http://www.animekom.com/animes/','page':1},
						{'title': 'Animes Par Genre','mode':'22'},]		
		self.listsTab(Anim_CAT_TAB, {'import':cItem['import'],'category':'host2','icon':cItem['icon'],'sub_mode':'Anim'})			
		
	def showmenu2(self,cItem):
		Film_CAT_TAB = [{'title': 'Films',         'mode':'30'  ,'Url':'http://www.animekom.com/movies/','page':1},
						{'title': 'Films Par Genre','mode':'22'},]		
		self.listsTab(Film_CAT_TAB, {'import':cItem['import'],'category':'host2','icon':cItem['icon'],'sub_mode':'Film'})		

	def showmenu3(self,cItem):
		gnr=cItem['sub_mode']
		Url='http://www.animekom.com/'
		Spatern1='<ul class="cat-list"(.*?)</ul>'
		Spatern2='<li><a href="(.*?)".*?</i>(.*?)<'
		sts, data = self.getPage(Url)
		if sts:
			Cat_data = re.findall(Spatern1,data, re.S)
			if Cat_data:
				if gnr=='Anim':
					list_cat=re.findall(Spatern2, Cat_data[0], re.S)
				else:
					list_cat=re.findall(Spatern2, Cat_data[1], re.S)
				for (url,titre) in list_cat:
					if '18' not in titre:
						self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','Url': url,'title':titre,'desc':titre,'page':1,'icon':cItem['icon'],'sub_mode':'anim','mode':'30'})


	def showitms(self,cItem):
		Url=cItem['Url']
		page=cItem['page']
		sUrl=Url+'page/'+str(page)+'/'
		sts, data = self.getPage(sUrl)
		if sts: 
			Liste_films_data = re.findall('div id="content">(.*?)<style>#dle-content{width:650px;}</style>', data, re.S)
			if Liste_films_data:
				Liste_films = re.findall('alt="(.*?)".*?img src="(.*?)".*?href="(.*?)">(.*?)&.*?desc">(.*?)<', Liste_films_data[0], re.S)
				for (name_eng,image,url,name_ar,desc) in Liste_films:
					if image.startswith('/'):
						image='https://www.animekom.com'+image
					self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','Url': url,'title':name_ar+' ('+name_eng+')','desc':desc,'icon':image,'hst':'tshost','mode':'31'} )	
			self.addDir({'import':cItem['import'],'category' : 'host2','Url': Url,'title':'Page Suivante','page':page+1,'desc':'Page Suivante','icon':cItem['icon'],'mode':'30'} )

	def showelems(self,cItem):
		Url=cItem['Url']
		sts, sHtmlContent = self.getPage(Url)
		if sts:
			Liste_Episodes_data = re.findall('class="treiler">.*?iframe.*?src="(.*?)"', sHtmlContent, re.S)
			if Liste_Episodes_data:			
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','title':'Trailer','desc':cItem['desc'],'icon':cItem['icon'],'hst':'none','url':Liste_Episodes_data[0]} )	
			
			Liste_Episodes_data = re.findall('<div id="sirt9awad">(.*?)</div>', sHtmlContent, re.S)
			if Liste_Episodes_data:
				for (Lst_Episodes_data) in Liste_Episodes_data:	
					Name_Episodes_data = re.findall('</i>(.*?)<', Lst_Episodes_data, re.S)
					Name_Episode=Name_Episodes_data[0]					
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','title':Name_Episode,'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost','url':Lst_Episodes_data} )	
			else:
				Liste_Episodes_data = re.findall('role="tablist">(.*?)</div>', sHtmlContent, re.S)
				if Liste_Episodes_data:				
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost','url':Liste_Episodes_data[0]} )	
			
	def SearchResult(self,str_ch,page,extra):
		url_='https://www.animekom.com/index.php?do=search'
		post_data = {'do':'search','subaction':'search','search_start':page,'full_search':0,'result_from':((page-1)*20)+1,'story':str_ch}
		sts, data = self.getPage(url_, post_data=post_data)
		if sts:
			Liste_films_data = re.findall('<div class="search-result">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?title">.*?">(.*?)<.*?desc">(.*?)<', data, re.S)
			for (url,image,name_eng,name_ar,desc) in Liste_films_data:
				if image.startswith('/'):
					image='https://www.animekom.com'+image
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','Url': url,'title':name_ar,'desc':desc,'icon':image,'hst':'tshost','mode':'31'})
			
	def get_links(self,cItem): 	
		urlTab = []
		data=cItem['url']
		lst_hoste_data = re.findall('<a data-link="(.*?)".*?>(.*?)<', data, re.S)				
		for (url,host) in lst_hoste_data:
			if host.strip()!='':
				urlTab.append({'name':host, 'url':url, 'need_resolve':1})	 
		return urlTab				

	def getArticle(self, cItem):
		printDBG("Animekom.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc = cItem['desc']
		sts, data = self.getPage(cItem['Url'])
		if sts:
			lst_dat=re.findall('slide-top">(.*?)</ul>', data, re.S)
			for (xx) in lst_dat:
				lst_dat0=re.findall("<li.*?</b>(.*?)<.*?>(.*?)</li>", xx+'</li>', re.S)
				for (x1,x2) in lst_dat0:
					if 'حلقات' in x1: otherInfo1['episodes'] = ph.clean_html(x2.replace('الحلقة',''))
					if 'لمدة' in x1: otherInfo1['duration'] = ph.clean_html(x2)
					if 'صاحب' in x1: otherInfo1['station'] = ph.clean_html(x2)			
					if 'لإسم العر' in x1: otherInfo1['alternate_title'] = ph.clean_html(x2)
					if 'لنوع' in x1: otherInfo1['genres'] = ph.clean_html(x2)
					

				
			lst_dat0=re.findall('<div class="slide-desc">(.*?)<a', data, re.S)
			if lst_dat0: desc = ph.clean_html(lst_dat0[0])
			else: desc = cItem['desc']
			
			lst_dat0=re.findall('slide-info">.*?</i>(.*?)</b>', data, re.S)
			if lst_dat0: otherInfo1['views'] = lst_dat0[0]	
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
		if mode=='22':
			self.showmenu3(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelems(cItem)	
