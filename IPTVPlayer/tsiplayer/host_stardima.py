# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

import re
import base64

def getinfo():
	info_={}
	info_['name']='Stardima.Com'
	info_['version']='1.0 19/04/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='203'
	info_['desc']='افلام و مسلسلات كرتون'
	info_['icon']='https://www.stardima.com/watch/uploads/custom-logo.jpg'
	info_['recherche_all']='0'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'stardima.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.stardima.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'المشاهدة',                                                          'icon':cItem['icon'],'mode':'50'})		
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'الاكثر مشاهده','url':'https://www.stardima.com/watch/topvideos.html','icon':cItem['icon'],'mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'الجديد','url':'https://www.stardima.com/watch/newvideos.html',      'icon':cItem['icon'],'mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'By Category',                                                       'icon':cItem['icon'],'mode':'60'})	
		self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})

		
	def showmenu1(self,cItem):
		abc = ['\xd8\xa3', '\xd8\xa8', '\xd8\xaa', '\xd8\xab', '\xd8\xac', '\xd8\xad', '\xd8\xae', '\xd8\xaf', '\xd8\xb0', '\xd8\xb1', '\xd8\xb2', '\xd8\xb3', '\xd8\xb4', '\xd8\xb5', '\xd8\xb6', '\xd8\xb7', '\xd8\xb8', '\xd8\xb9', '\xd8\xba', '\xd9\x81', '\xd9\x82', '\xd9\x83', '\xd9\x84', '\xd9\x85', '\xd9\x86', '\xd9\x87\xd9\x80', '\xd9\x88', '\xd9\x8a']
		i=0
		for letter in abc:
			i=i+1
			href='https://www.stardima.com/watch/browse-%s-videos-1-date.html' %str(i) 
			self.addDir({'import':cItem['import'],'category' : 'host2','title':letter,'url':href,'mode':'40'})			

	def showmenu2(self,cItem):
		sts, data = self.getPage(cItem['url'])
		if sts:
			Liste_els = re.findall('<li><a href="(.*?)">(.*?)</a></li>', data, re.S)	
			for href,title in Liste_els:
				try:href=href.split('.html')[0]+'.html'
				except:continue
				if not "videos-1-date.html" in href:
					continue
				self.addDir({'import':cItem['import'],'category' : 'host2','title':title,'url':href,'mode':'20','good_for_fav':True})			       

		
	def showmenu3(self,cItem):
		sts, data = self.getPage('https://www.stardima.com/ads.php')
		if sts:
			Liste_els = re.findall('<li>.*?title="(.*?)".*?href="(.*?)".*?src="(.*?)"', data, re.S)	
			for (titre,url,image) in Liste_els:
				if '?cat=' in url:
					x1,name_=url.split('?cat=')
					url='https://www.stardima.com/watch/browse-'+name_+'-videos-1-date.html'
				if titre.strip()!='':
					self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'icon':image,'mode':'20','good_for_fav':True})			       

		
	def showmenu4(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'أ-ي',                                                                                                                         'mode':'30'})
		self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'مسلسلات أنمي وكرتون مدبلجة','url':'https://www.stardima.com/watch/browse-cartoon_anime_dub_arabic-videos-1-date.html',         'mode':'40'})
		self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'مسلسلات أنمي وكرتون مترجمة','url':'https://www.stardima.com/watch/browse-cartoon_anime_sub_arabic-videos-1-date.html',         'mode':'40'})
		self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'نمي وكرتون مدبلجة عربي','url':'https://www.stardima.com/watch/browse-movie_anime_cartoon_dub_arabic-videos-1-date.html',      'mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'أفلام أنمي وكرتون مترجمة عربي','url':'https://www.stardima.com/watch/browse-movie_anime_cartoon_sub_arabic-videos-1-date.html','mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'أفلام أنمي وكرتون صامتة','url':'https://www.stardima.com/watch/browse-cartoon-anime-Silent-videos-1-date.html',                'mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'افلام عائلية','url':'https://www.stardima.com/watch/browse-movies-family-arabic-videos-1-date.html',                           'mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'Pixar Short Movies','url':'https://www.stardima.com/watch/browse-Pixar-Short-Movies-videos-1-date.html',                      'mode':'20'})
	
	def showanim(self,cItem):
		page=cItem.get('page',1)
		url_or=cItem['url']	
		if '-1-date.html' in url_or:
			url=url_or.replace('1-date.html',str(page)+'-date.html')
		else:
			url=url_or+'?page='+str(page)
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('class="thumbnail">.*?echo="(.*?)".*?<a href="(.*?)".*?title="(.*?)"', data, re.S)
			i=0	
			for (image,url,titre) in Liste_els:
				self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'icon':image,'hst':'tshost','good_for_fav':True})
				i=i+1
			if i>10:
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':url_or,'page':page+1,'mode':'20'})


	def SearchResult(self,str_ch,page,extra):
		url_='https://www.stardima.com/watch/search.php?keywords='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:
			Liste_els = re.findall('class="thumbnail">.*?echo="(.*?)".*?<a href="(.*?)".*?title="(.*?)"', data, re.S)
			for (image,url,titre) in Liste_els:
				self.addVideo({'import':extra,'category' : 'host2','title':titre,'url':url,'icon':image,'hst':'tshost','good_for_fav':True})


		


	def get_links(self,cItem): 	
		urlTab = []
		url=cItem['url']	
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('contentURL" content="(.*?)"', data, re.S)
			if 	Liste_els:
				urlTab.append({'name':'|Watch Server| Main Server', 'url':Liste_els[0], 'need_resolve':0,'type':'local'})	
			
			Liste_els = re.findall('<input rel="nofollow".*?.open\(\'(.*?)\'.*?value=\'(.*?)\'', data, re.S)	
			for (url,titre) in 	Liste_els:
				titre = titre.replace('إضغط هنا لتحميل الجودة ✔','Download Server')
				titre = titre.replace('إضغط هنا تحميل جودة ✔','Download Server')
				if '|' in titre:
					titre = '|'+titre.split('|')[-1].strip()+'| '+titre.split('|')[0].strip()+'p'
				urlTab.append({'name':titre, 'url':'hst#tshost#'+url, 'need_resolve':1,'type':'local'})	

		return urlTab	

	def getVideos(self,videoUrl):
		urlTab = []
		url='https://www.stardima.com/watch/'+videoUrl	
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('videoUrl.*? value="(.*?)"', data, re.S)
			if 	Liste_els:
				URL_part=Liste_els[0].split('O0k0O', 1)
				new=''
				i=0
				for letter in URL_part[0]:
					if (i % 2)==0:
						new=new+letter
					i=i+1	
				URL_b64=new+URL_part[1].replace('O0k0O','=')
				URL_=base64.b64decode(URL_b64)
				urlTab.append((URL_,'0'))	
		return urlTab	
			
	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)	
		elif mode=='20':
			self.showanim(cItem)		
		elif mode=='30':
			self.showmenu1(cItem)	
		elif mode=='40':
			self.showmenu2(cItem)
		elif mode=='50':
			self.showmenu3(cItem)	
		elif mode=='60':
			self.showmenu4(cItem)
		return True
