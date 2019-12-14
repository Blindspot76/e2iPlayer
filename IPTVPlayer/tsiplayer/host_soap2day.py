# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re
import base64

def getinfo():
	info_={}
	info_['name']='Soap2day.com'
	info_['version']='1.0 28/07/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'
	info_['desc']='Films & Series'
	info_['icon']='https://soap2day.com/title.png'
	info_['recherche_all']='1'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'soap2day.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://soap2day.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Films','icon':cItem['icon'],'mode':'10','sub_mode':'1'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'TV Series','icon':cItem['icon'],'mode':'10','sub_mode':'2'})
		self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})

	def showmenu1(self,cItem):
		gnr=cItem.get('sub_mode','1')
		if gnr=='1':
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'All'  ,'url':self.MAIN_URL+'/movielist'    ,'icon':cItem['icon'],'mode':'20'})
			self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c0000????')+'By Filtre','icon':cItem['icon'],'mode':'11','sub_mode':0})
		else:
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'All' ,'url':self.MAIN_URL+'/tvlist' ,'icon':cItem['icon'],'mode':'20'})
			self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c0000????')+'By Filtre','icon':cItem['icon'],'mode':'11','sub_mode':1})

	def showmenu2(self,cItem):
		count = cItem.get('count',0)
		if count==0:
			gnr   = cItem.get('sub_mode',0)
			url_  = ['/movielist/','/tvlist/']
			url   = self.MAIN_URL+url_[gnr]			
			sts, data = self.getPage(url)
			if sts:
				Liste_els = re.findall('Sort :(.*?)</h5>', data, re.S)
				if Liste_els:
					Liste_ = re.findall('href="(.*?)".*?>(.*?)<', Liste_els[0], re.S)
					i=0
					for (url,titre) in Liste_:
						titre = titre.strip()
						url = self.MAIN_URL+url
						if not((titre=='Popular')and(i==0)):
							self.addDir({'import':cItem['import'],'desc':url,'url':url,'category' : 'host2','title':titre,'icon':cItem['icon'],'mode':'11','count':1})
							i=i+1
		else:
			url   = cItem.get('url','')
			sts, data = self.getPage(url)
			if sts:
				Liste_els = re.findall('dropdown-menu">(.*?)</ul', data, re.S)
				if Liste_els:
					Liste_ = re.findall('<li>.*?href="(.*?)".*?>(.*?)<', Liste_els[count], re.S)
					for (url,titre) in Liste_:
						titre = titre.strip()
						url = self.MAIN_URL+url
						if count==2:mode_='20'
						else: mode_='11'
						self.addDir({'import':cItem['import'],'desc':url,'url':url,'category' : 'host2','title':titre,'icon':cItem['icon'],'mode':mode_,'count':count+1})
											
	def showitms(self,cItem):
		page=cItem.get('page',1)
		url_or=cItem['url']	
		if '?' in url_or:
			url=url_or+'&page='+str(page)
		else:	
			url=url_or+'?page='+str(page)
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('img-group">.*?href=\'(.*?)\'.*?src="(.*?)".*?>(.*?)<h5>(.*?)</h5>', data, re.S)
			i=0	
			for (url,image,desc,titre) in Liste_els:
				Desc = tscolor('\c00????00')+ 'Info: '+tscolor('\c00??????')+self.cleanHtmlStr(desc)
				url = self.MAIN_URL+url
				image = self.MAIN_URL+image
				titre = self.cleanHtmlStr(titre)
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','title':titre  ,'url':url ,'desc':Desc,'icon':image,'mode':'21','hst':'tshost'})
				i=i+1
			if i>28:
				self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c0090??20')+_('Next page'),'url':url_or,'page':page+1,'mode':'20'})

	def showelms(self,cItem):
		url1=cItem['url']
		img=cItem['icon']
		sts, data = self.getPage(url1)
		if sts:
			inf = self.getArticle(cItem,data)
			Desc = ''
			Desc = Desc +tscolor('\c00????00')+ 'Rating: '+tscolor('\c00??????')+inf[0].get('other_info',{}).get('rating','')+' | '
			Desc = Desc +tscolor('\c00????00')+ 'Release: '+tscolor('\c00??????')+inf[0].get('other_info',{}).get('year','')+'\n'
			Desc = Desc +tscolor('\c00????00')+ 'Genre: '+tscolor('\c00??????')+inf[0].get('other_info',{}).get('genres','')+'\n'
			Desc = Desc +tscolor('\c00????00')+ 'Story: '+tscolor('\c0000????')+inf[0].get('text','')
						
			Liste_els = re.findall('alert-info-ex.*?<h4>(.*?)</h4>(.*?)</div></div>', data, re.S)		
			if Liste_els:
				for(s,data0) in Liste_els:
					self.addMarker({'title':tscolor('\c00????00')+s})
					Liste_ = re.findall('href="(.*?)">(.*?)<', data0, re.S)	
					for( url,titre) in Liste_:
						url = self.MAIN_URL+url
						self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':titre,'desc':Desc,'icon':img,'hst':'tshost','gnr':'E'})		
			else:
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url1,'title':cItem['title'],'desc':Desc,'icon':img,'hst':'tshost','gnr':'M'})		
	

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/search/keyword/'+str_ch
		sts, data = self.getPage(url_)
		if sts:
			Liste_els = re.findall('img-group">.*?href=\'(.*?)\'.*?src="(.*?)".*?>(.*?)<h5>(.*?)</h5>', data, re.S)
			for (url,image,desc,titre) in Liste_els:
				Desc = tscolor('\c00????00')+ 'Info: '+tscolor('\c00??????')+self.cleanHtmlStr(desc)
				url = self.MAIN_URL+url
				image = self.MAIN_URL+image
				titre = self.cleanHtmlStr(titre)
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','title':titre ,'url':url ,'desc':Desc,'icon':image,'mode':'21','hst':'tshost'})
		
	def getArticle(self, cItem,data='none'):
		otherInfo1 = {}
		icon = cItem.get('icon')
		title = cItem['title']
		desc = cItem['desc']	
		if data=='none':
			sts, data = self.getPage(cItem['url'])
		lst_dat0=re.findall("<p><h4>(.*?)</h4>.*?</p>(.*?)</p>", data, re.S)
		for (x1,x2) in lst_dat0:
			if 'Release' in x1: otherInfo1['year'] = self.cleanHtmlStr(x2)
			if 'Genre' in x1: otherInfo1['genres'] = self.cleanHtmlStr(x2)			
			if 'Stars' in x1: otherInfo1['actors'] = self.cleanHtmlStr(x2)
			if 'Rating' in x1: otherInfo1['rating'] = self.cleanHtmlStr(x2)
			if 'Director' in x1: otherInfo1['director'] = self.cleanHtmlStr(x2)			
			if 'Story' in x1: desc = self.cleanHtmlStr(x2)	

		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]


	def get_links(self,cItem): 	
		urlTab = []
		url=cItem['url']	
		gnr=cItem['gnr']
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('id="hId.*?value="(.*?)"', data, re.S)
			if 	Liste_els:
				pass_ = Liste_els[0]
				post_data={'pass':pass_}
				if gnr == 'M': URL = self.MAIN_URL+'/home/index/GetMInfoAjax'
				else : URL = self.MAIN_URL+'/home/index/GetEInfoAjax'
				self.defaultParams['header']['Referer'] = url

				sts, data = self.getPage(URL,self.defaultParams,post_data=post_data)
				if sts:
					printDBG(data)
					Liste_els = re.findall('val".*?"(.*?)"', data, re.S)
					if Liste_els:
						link = Liste_els[0].replace('\\/', '/')
						urlTab.append({'name':'Main Server', 'url':link, 'need_resolve':0})	

		return urlTab	

			
	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		elif mode=='10':
			self.showmenu1(cItem)	
		elif mode=='11':
			self.showmenu2(cItem)
		elif mode=='12':
			self.showmenu3(cItem)		
		elif mode=='20':
			self.showitms(cItem)
		elif mode=='21':
			self.showelms(cItem)		
		return True
