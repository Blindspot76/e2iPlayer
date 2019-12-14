# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re,urllib



def getinfo():
	info_={}
	info_['name']='Animekom.Com'
	info_['version']='2.0 22/11/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='202'
	info_['desc']='جميع الإنميات مترجمة عربي، والأفلام والأوفات'
	info_['icon']='https://i.ibb.co/QmjbP6z/logo.png'
	info_['recherche_all']='0'
	info_['update']='New Site'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'animekom.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://animekom.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage


	def showmenu0(self,cItem):
		hst='host2'
		Animekom_TAB = [
							{'category':hst,      'title':'جميع الأنميات'     , 'mode':'30', 'url':self.MAIN_URL+'/'},
							{'category':hst,      'title':'جميع الافلام'       , 'mode':'30', 'url':self.MAIN_URL+'/movies/'},
							{'category':hst,      'title':'جديد الأنمي'       , 'mode':'21', 'sub_mode':2},
							{'category':hst,      'title':'جديد الأفلام'       , 'mode':'21', 'sub_mode':0},
							{'category':hst,      'title':'جديد الأوفات'      , 'mode':'21', 'sub_mode':1},	
							{'category':hst,      'title': tscolor('\c0000??00')+'أنواع الأنمي'      , 'mode':'22'},
							{'category':hst,      'title':'قريبا'            , 'mode':'23'},										
							{'category':'search', 'title':_('Search')  ,'search_item':True,'page':1,'hst':'tshost'},
							]
		self.listsTab(Animekom_TAB, {'icon':cItem['icon'],'import':cItem['import']})						
	
	def showmenu_21(self,cItem):
		gnr=cItem['sub_mode']
		Url=self.MAIN_URL
		if   gnr==0: pat = '<span>جديد الأفلام</span>(.*?)<div class="title">'
		elif gnr==1: pat = '<span>جديد الأوفات</span>(.*?)<div class="title">'
		elif gnr==2: pat = '"title">جديد الأنمي</p>(.*?)<div class="title'
		sts, data = self.getPage(Url)
		if sts:
			_data = re.findall(pat,data, re.S)		
			if _data:
				_data = re.findall('class="poster">.*?src="(.*?)".*?>(.*?)href="(.*?)".*?name_film">(.*?)</p>(.*?)</div>',_data[0], re.S)
				for (image,desc,url,titre,desc1) in _data:
					desc=self.cleanHtmlStr(desc+'>')
					if not image.startswith('http'): image = self.MAIN_URL+image
					if desc.strip()!='':
						titre = self.cleanHtmlStr(titre)+' ('+tscolor('\c0000????')+desc+tscolor('\c00??????')+')'
					else: titre = self.cleanHtmlStr(titre)
					if desc1.strip()!='': desc1= tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+self.cleanHtmlStr(desc1)
					self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc1,'icon':image,'hst':'tshost','mode':'31'} )	
		
	def showmenu_23(self,cItem):
		Url=self.MAIN_URL
		sts, data = self.getPage(Url)
		if sts:
			_data = re.findall('<h3>قريبا</h3>(.*?)class="menu">',data, re.S)		
			if _data:
				_data = re.findall('class="poster">.*?src="(.*?)".*?href="(.*?)".*?name_film">(.*?)</p>(.*?)</div>',_data[0], re.S)
				for (image,url,titre,desc) in _data:
					if not image.startswith('http'): image = self.MAIN_URL+image					
					titre = self.cleanHtmlStr(titre)
					if desc.strip()!='': desc= tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+self.cleanHtmlStr(desc)
					self.addMarker({'title':titre,'desc':desc,'icon':image} )	
		

	def showmenu_22(self,cItem):
		Url=self.MAIN_URL
		sts, data = self.getPage(Url)
		if sts:
			Cat_data = re.findall('class="cat-list">(.*?)</ul',data, re.S)
			if Cat_data:
				list_cat=re.findall('href="(.*?)">(.*?)<', Cat_data[0], re.S)
				for (url,titre) in list_cat:
					if '18' not in titre:
						self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':titre,'icon':cItem['icon'],'mode':'30'})

	def showitms(self,cItem):
		Url=cItem['url']
		page=cItem.get('page',1)
		sUrl=Url+'page/'+str(page)+'/'
		sts, data = self.getPage(sUrl)
		if sts: 
			Liste_films_data = re.findall('</h1>(.*?)class="title">', data, re.S)
			if Liste_films_data:
				_data = re.findall('class="poster">.*?src="(.*?)".*?>(.*?)href="(.*?)".*?name_film">(.*?)</p>(.*?)</div>',Liste_films_data[0], re.S)
				for (image,desc,url,titre,desc1) in _data:
					#desc= tscolor('\c00????00')+'Type: '+tscolor('\c00??????')+desc
					desc=self.cleanHtmlStr(desc+'>')
					if not image.startswith('http'): image = self.MAIN_URL+image
					if desc.strip()!='':
						titre = self.cleanHtmlStr(titre)+' ('+tscolor('\c0000????')+desc+tscolor('\c00??????')+')'
					else: titre = self.cleanHtmlStr(titre)
					if desc1.strip()!='': desc1= tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+self.cleanHtmlStr(desc1)
					self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc1,'icon':image,'hst':'tshost','mode':'31'} )	
			self.addDir({'import':cItem['import'],'category' : 'host2','url': cItem['url'],'title':tscolor('\c0090??20')+_('Next page'),'page':page+1,'icon':cItem['icon'],'mode':'30'} )

	def showelems(self,cItem):
		Url=cItem['url'].replace('://','rgysoft')
		Url=urllib.quote(Url).replace('rgysoft','://')
		sts, sHtmlContent = self.getPage(Url)
		srv=[]
		if sts:
			desc = self.get_info(sHtmlContent)
			Liste_Episodes_data = re.findall('(youtube.com.*?)"', sHtmlContent, re.S)
			if Liste_Episodes_data:			
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','title':'Trailer','desc':desc,'icon':cItem['icon'],'hst':'none','url':'https://www.'+Liste_Episodes_data[0]} )	
			
			Liste_Episodes_data = re.findall('<div id="accordian">(.*?)</div>', sHtmlContent, re.S)
			if Liste_Episodes_data:
				for (Lst_Episodes_data) in Liste_Episodes_data:	
					srv=[]
					Name_Episodes_data = re.findall('data-link="(.*?)".*?">(.*?)</li>', Lst_Episodes_data, re.S)
					titre='!'
					for (elm,hst) in Name_Episodes_data:
						if elm.startswith('*'): titre = 'Episode: '+elm.split('*')[1].replace('الحلقة','')
						elif elm.strip()!='': srv.append((elm,self.cleanHtmlStr(hst)))				
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','title':titre,'desc':desc,'icon':cItem['icon'],'hst':'tshost','url':srv} )	
			else:
				Liste_Episodes_data = re.findall('role="tablist">(.*?)</div>', sHtmlContent, re.S)
				if Liste_Episodes_data:
					srv=[]
					Name_Episodes_data = re.findall('data-link="(.*?)".*?">(.*?)</li>', Liste_Episodes_data[0], re.S)					
					for (elm,hst) in Name_Episodes_data:
						if elm.strip()!='': srv.append((elm,self.cleanHtmlStr(hst)))							
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','title':cItem['title'],'desc':desc,'icon':cItem['icon'],'hst':'tshost','url':srv} )	
			
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/index.php?do=search'
		post_data = {'do':'search','subaction':'search','search_start':page,'full_search':0,'result_from':((page-1)*20)+1,'story':str_ch}
		sts, data = self.getPage(url_, post_data=post_data)
		if sts:
			printDBG('data sc='+data)
			Liste_films_data = re.findall('</h1>(.*?)class="title">', data, re.S)
			if Liste_films_data:
				_data = re.findall('class="poster">.*?src="(.*?)".*?>(.*?)href="(.*?)".*?name_film">(.*?)</p>(.*?)</div>',Liste_films_data[0], re.S)
				for (image,desc,url,titre,desc1) in _data:
					desc=self.cleanHtmlStr(desc+'>')
					if not image.startswith('http'): image = self.MAIN_URL+image
					if desc.strip()!='':
						titre = self.cleanHtmlStr(titre)+' ('+tscolor('\c0000????')+desc+tscolor('\c00??????')+')'
					else: titre = self.cleanHtmlStr(titre)
					if desc1.strip()!='': desc1= tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+self.cleanHtmlStr(desc1)
					self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc1,'icon':image,'hst':'tshost','mode':'31'})
			
	def get_links(self,cItem): 	
		urlTab = []
		data=cItem['url']
		printDBG('srv='+str(data))
		for (srv,hst) in data:
			urlTab.append({'name':hst, 'url':srv, 'need_resolve':1})	 
		return urlTab				

	def getArticle(self, cItem):
		printDBG("Animekom.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc = cItem['desc']
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('class="details">(.*?)</ul>', data, re.S)
			for (xx) in lst_dat:
				lst_dat0=re.findall('<li>(.*?):(.*?)</li>',xx, re.S)
				for (x1,x2) in lst_dat0:
					if 'حلقات' in x1: otherInfo1['episodes'] = ph.clean_html(x2.replace('الحلقة',''))
					if 'لمدة' in x1: otherInfo1['duration'] = ph.clean_html(x2)
					if 'صاحب' in x1: otherInfo1['station'] = ph.clean_html(x2)			
					if 'لإسم العر' in x1: otherInfo1['alternate_title'] = ph.clean_html(x2)

			lst_dat=re.findall('class="genres">(.*?)</div>', data, re.S)
			if lst_dat: otherInfo1['genres'] = ph.clean_html(lst_dat[0])
					
			lst_dat=re.findall('class="txt">(.*?)<br />', data, re.S)
			if lst_dat: desc = ph.clean_html(lst_dat[0])
				
		icon = cItem.get('icon')
		title = cItem['title']			
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]
		 
	def get_info(self,data):
		inf = ''
		lst_dat=re.findall('class="details">(.*?)</ul>', data, re.S)
		for (xx) in lst_dat:
			lst_dat0=re.findall('<li>(.*?):(.*?)</li>',xx, re.S)
			for (x1,x2) in lst_dat0:
				if 'حلقات' in x1: inf=inf +tscolor('\c00????00')+ 'Episodes: '+tscolor('\c00??????')+ph.clean_html(x2.replace('الحلقة',''))+' | '
				if 'لمدة' in x1: inf=inf +tscolor('\c00????00')+ 'Duration: '+tscolor('\c00??????')+ph.clean_html(x2)+' | '		

		lst_dat=re.findall('class="genres">(.*?)</div>', data, re.S)
		if lst_dat: inf = inf+'\n'+tscolor('\c00????00')+'Genre: '+tscolor('\c00??????')+ph.clean_html(lst_dat[0])
				
		lst_dat=re.findall('class="txt">(.*?)<br />', data, re.S)
		if lst_dat: inf = inf+'\n'+tscolor('\c00????00')+'Story: '+tscolor('\c0000????')+ph.clean_html(lst_dat[0])
		return inf	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='21':
			self.showmenu_21(cItem)
		if mode=='22':
			self.showmenu_22(cItem)
		if mode=='23':
			self.showmenu_23(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelems(cItem)	
