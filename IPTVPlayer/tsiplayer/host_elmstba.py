# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass
from tsiplayer.libs.packer import cPacker
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit       import SetIPTVPlayerLastHostError

import re
import base64

def getinfo():
	info_={}
	info_['name']='Elmstba'
	info_['version']='1.0 08/10/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='افلام و مسلسلات'
	info_['icon']='https://www.elmstba.tv/uploads/custom-logo.png'
	info_['recherche_all']='0'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'katkoute.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.elmstba.tv'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		
	def showmenu(self,cItem):
		url = self.MAIN_URL+ '/category.php'
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('li-category">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)"', data, re.S)
			for (cat,img,titre) in Liste_els:
				if ('يعرض' not in titre) and ('قنوات' not in titre) and('للكبار' not in titre):
					self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'icon':img,'mode':'31','url':cat})
		self.addDir({'import':cItem['import'],'name':'host2','category':'search',      'title': _('Search'), 'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})

					
	def showitms(self,cItem):
		page=cItem.get('page',1)
		url_or=cItem['url']	
		if '?' in url_or:
			url=url_or+'&page='+str(page)
		else:	
			url=url_or+'?page='+str(page)
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('col-md-3">.*?<a href="(.*?)".*?title="(.*?)".*?data-echo="(.*?)"', data, re.S)
			i=0	
			for (url,titre,image) in Liste_els:
				#titre=titre.replace('مشاهدة فيلم ','').replace(' كامل HD اون لاين','').replace(' مترجم HD اون لاين','')
				desc0,titre = self.uniform_titre(titre)
				self.addDir({'import':cItem['import'],'category' : 'host2','title':titre  ,'url':url ,'desc':desc0,'icon':image,'mode':'32'})
				i=i+1
			if i>22:
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'\c00????00Next','url':url_or,'page':page+1,'mode':'31'})

	def showelms(self,cItem):
		
		self.addVideo({'import':cItem['import'],'category' : 'host2','title':cItem['title'].replace('>> \c0000??00Elmstba - \c00??????','')  ,'url':cItem['url'] ,'desc':cItem['desc'],'icon':cItem['icon'],'good_for_fav':True,'hst':'tshost'})
		url=cItem['url']	
		sts, data = self.getPage(url)
		if sts:
			if 'Epslist">' in data:
				self.addMarker({'title':'\c0000??00Episodes:','icon':cItem['icon']})
				Liste_els = re.findall('Epslist">(.*?)</div>', data, re.S)
				if Liste_els:
					Liste_els = re.findall('href="(.*?)">(.*?)<', Liste_els[0], re.S)
					for (url1,titre) in Liste_els:
						self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1 ,'desc':cItem['desc'],'icon':cItem['icon'],'good_for_fav':True,'hst':'tshost'})


	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/search.php?keywords='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:
			Liste_els = re.findall('col-md-3">.*?<a href="(.*?)".*?title="(.*?)".*?data-echo="(.*?)"', data, re.S)
			for (url,titre,image) in Liste_els:
				desc0,titre = self.uniform_titre(titre)
				self.addDir({'import':extra,'category' : 'host2','title':titre  ,'url':url ,'desc':desc0,'icon':image,'mode':'32'})

		


	def get_links(self,cItem): 	
		urlTab = []
		url=cItem['url']	
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('<iframe src="(.*?)"', data.replace('\\',''), re.IGNORECASE)	
			url_elm=[]
			for (url) in Liste_els:
				if url not in url_elm:
					url_elm.append(url)
					if ('liivideo' in url ) or ('holavid' in url ) :
						urlTab.append({'name':self.up.getDomain(url).replace('www.','').title(), 'url':'hst#tshost#'+url, 'need_resolve':1,'type':'local'})
					else:
						urlTab.append({'name':self.up.getDomain(url).replace('www.','').title(), 'url':url, 'need_resolve':1})	

		return urlTab	

	def getVideos(self,videoUrl):
		urlTab = []
		printDBG('videoUrl'+videoUrl)
		sts, data = self.getPage(videoUrl)
		if sts:
			printDBG('data'+data)
			Liste_els = re.findall('sources.*?"(.*?)"', data, re.S)
			if not Liste_els:
				L_els = re.findall('(eval.*?)</script>', data, re.S)
				if 	L_els:
					printDBG('p,a,c,k,e,d Trouver')
					data = cPacker().unpack(L_els[0].strip())
					printDBG(data)
					Liste_els = re.findall('sources.*?"(.*?)"', data, re.S)	
			if 	Liste_els:
				URL=Liste_els[0]				
				if ('m3u8' in URL):
					urlTab.append((URL,'3'))
				else:
					urlTab.append((URL,'0'))
			else:
				if 'File is no longer available' in data:
					SetIPTVPlayerLastHostError('File is no longer available')
		return urlTab	
			
	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		elif mode=='31':
			self.showitms(cItem)
		elif mode=='32':
			self.showelms(cItem)		
		return True
