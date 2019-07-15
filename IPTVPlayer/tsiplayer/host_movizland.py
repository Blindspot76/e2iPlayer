# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.tstools import TSCBaseHostClass

import re

def getinfo():
	info_={}
	info_['name']='Movizland.Online'
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
		self.MAIN_URL = 'http://movizland.online'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
					 	 
	def showmenu0(self,cItem):
		self.addDir({'import':cItem['import'],'category' :'host2','title':'بوكس اوفيس' ,'icon':cItem['icon'],'mode':'30','sub_mode':'0'})
		self.addDir({'import':cItem['import'],'category' :'host2','title':'أحدث الأفلام','icon':cItem['icon'],'mode':'30','sub_mode':'1'})
		self.addDir({'import':cItem['import'],'category' :'host2','title':'تليفزيون موفيز لاند','icon':cItem['icon'],'mode':'30','sub_mode':'2'})
		self.addDir({'import':cItem['import'],'category' :'host2','title':'By Category','icon':cItem['icon'],'mode':'20'})
		self.addDir({'import':cItem['import'],'category' :'host2','title':'\c00????00'+'By Filter','url':'http://movizland.online/?s=','icon':cItem['icon'],'mode':'21'})	
			
		self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})

	def showmenu1(self,cItem):
		sts, data = self.getPage('http://movizland.online/')
		if sts:
			Liste_films_data = re.findall('menu-bar-cat">(.*?)</div>', data, re.S)
			if Liste_films_data:
				Liste_films_data0 = re.findall('<li>.*?href="(.*?)".*?title="(.*?)"', Liste_films_data[0], re.S)
				for (url,titre) in Liste_films_data0:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'icon':cItem['icon'],'mode':'30','sub_mode':'3'})


	def showmenu2(self,cItem):
		count=cItem.get('count','')
		if count=='':
			count=1	
		codeold=cItem['url']
		sts, data = self.getPage('http://movizland.online/')	
		if sts:		
			if count==1:
				data1=re.findall('<select name="mcat">(.*?)</select>', data, re.S)
				codeold=codeold+'&mcat='
			elif count==2:	
				data1=re.findall('<select name="tagm">(.*?)</select>', data, re.S) 
				codeold=codeold+'&tagm='				
			elif count==3:					
				data1=re.findall('<select name="quality">(.*?)</select>', data, re.S) 				
				codeold=codeold+'&quality='				
			if count==3:
				gnr='30'
			else:
				gnr='21'
				
			lst_data1 = re.findall('option value="(.*?)".*?>(.*?)<',data1[0], re.S)
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'ALL','url':codeold,'icon':cItem['icon'],'mode':gnr,'sub_mode':'4','count':count+1})	
			for (x1,x2) in lst_data1:
				if x1!='':
					code=codeold+x1
					self.addDir({'import':cItem['import'],'category' : 'host2','title':x2,'url':code,'icon':cItem['icon'],'mode':gnr,'sub_mode':'4','count':count+1})
	def showitms(self,cItem):
		gnr2=cItem.get('sub_mode', '0')	
		urlo=cItem.get('url', '')	
		page = cItem.get('page', 1)
		if int(gnr2)<3:
			url='http://movizland.online/?page='+str(page)
		elif gnr2=='3':	
			url=cItem['url']+'page/'+str(page)+'/'
		elif gnr2=='4':
			url=cItem['url']+'&page='+str(page)

			
		sts, data = self.getPage(url)
		if sts:
			if gnr2=='0': pat='<h1 class(.*?)<h1 class'
			if gnr2=='1': pat='أحدث الأفلام</h1>(.*?)<h1 class'				
			if gnr2=='2': pat='تليفزيون موفيز لاند</h1>(.*?)<style>'	
			if int(gnr2)>2: pat='class="movies-blocks">(.*?)class="footer">'					
			Liste_films = re.findall(pat, data, re.S)
			if Liste_films:
				Liste_films_data = re.findall('class="block.*?title="(.*?)".*?href="(.*?)".*?src="(.*?)".*?class="details">(.*?)</div>', Liste_films[0], re.S)
				for (name_eng,url1,image,desc) in Liste_films_data:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':name_eng.strip(),'url':url1,'icon':image,'desc':ph.clean_html(desc),'mode':'31','good_for_fav':True,'EPG':True,'hst':'tshost'})					
			if int(gnr2)>0:
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':urlo,'page':page+1,'mode':'30','sub_mode':gnr2})


	def showelms(self,cItem):
		url=cItem['url']
		title_=cItem['title']

		self.addVideo({'import':cItem['import'],'category' : 'host2','title':title_,'url':url,'desc':'','icon':cItem['icon'],'hst':'tshost','good_for_fav':True})	
			
		sts, data = self.getPage(url)
		if sts:
			Liste_films_data = re.findall('containerEpisodes">(.*?)</div>', data, re.S)
			if Liste_films_data:
				Liste_films_data0 = re.findall('<a.*?href="(.*?)".*?<em>(.*?)<', Liste_films_data[0], re.S)
				i=0
				for (url1,num) in Liste_films_data0:
					i=i+1
					if i==1: self.addMarker({'title':'\c00????00'+'----> Episodes <----','icon':cItem['icon']})
					titre='EPISODE '+num
					self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'desc':'','icon':cItem['icon'],'hst':'tshost','good_for_fav':True})	
		

	def SearchResult(self,str_ch,page,extra):
		url_='http://movizland.online/?s='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:
			Liste_films_data = re.findall('class="block.*?title="(.*?)".*?href="(.*?)".*?src="(.*?)".*?class="details">(.*?)</div>', data, re.S)
			for (name_eng,url1,image,desc) in Liste_films_data:
		
				self.addDir({'import':extra,'category' : 'host2','title':name_eng,'url':url1,'icon':image,'desc':ph.clean_html(desc),'mode':'31','good_for_fav':True,'EPG':True,'hst':'tshost'})					
		
		
	def get_links(self,cItem): 	
		urlTab = []
		Url=cItem['url']
		sts, data = self.getPage(Url.replace('//movizland.online/','//m.movizland.com/'))
		if sts:
			Liste_els = re.findall('rgba\(203, 0, 44, 0.36\).*?href="(.*?)".*?ViewMovieNow">(.*?)<', data, re.S)
			for (url_,titre_) in Liste_els:
				if 'و حمل' not in titre_:
					if 'تحميل' in titre_: titre_='سرفر التحميل'
					urlTab.append({'name':titre_, 'url':url_, 'need_resolve':0})							
		return urlTab	

		
	def getArticle(self,cItem):
			printDBG("movizland.getVideoLinks [%s]" % cItem) 
			otherInfo1 = {}
			desc = cItem.get('desc','')
			sts, data = self.getPage(cItem['url'])
			if sts:
				lst_dat=re.findall('<div class="contentMovie">(.*?)</div>', data, re.S)
				if lst_dat: desc = ph.clean_html(lst_dat[0])
				lst_dat=re.findall('class="ratings">(.*?)</span>', data, re.S)
				if lst_dat: otherInfo1['rating'] = ph.clean_html(lst_dat[0])
				lst_dat=re.findall('<btns class="btns.*?<span>(.*?)</span>(.*?)</div>', data, re.S)
				for (x1,x2) in lst_dat:
					if 'نوع الفيلم'  in x1: otherInfo1['genres'] = ph.clean_html(x2)
					if 'قسم الفيلم'  in x1: otherInfo1['categories'] = ph.clean_html(x2)
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
		return True

