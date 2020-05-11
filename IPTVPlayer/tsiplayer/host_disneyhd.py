# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
import base64,re

def getinfo():
	info_={}
	info_['name']='DisneyHD'
	info_['version']='1.0 28/07/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='104'
	info_['desc']='Films & Series Disney HD'
	info_['icon']='https://i.ibb.co/09jnM7Z/dhd.png'
	info_['recherche_all']='0'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'disneyhd.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://disneyhd.cf'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Liste des films et séries','icon':cItem['icon'],'mode':'10','url':self.MAIN_URL+'/?page=liste.php'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Visionnés en ce moment','icon':cItem['icon'],'mode':'10','sub_mode':8})				
		self.addDir({'import':cItem['import'],'category' :'search','title':tscolor('\c0000????')+ _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})		
		self.addMarker({'category' : 'host2','title':tscolor('\c00????00')+' >>> Films <<<'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Derniers ajouts','icon':cItem['icon'],'mode':'10','sub_mode':3})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Les dernières sorties','icon':cItem['icon'],'mode':'10','sub_mode':4})		
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Les plus populaires','icon':cItem['icon'],'mode':'10','sub_mode':5})			
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Courts métrages','icon':cItem['icon'],'mode':'10','sub_mode':6})			
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Studios','icon':cItem['icon'],'mode':'10','sub_mode':7})		
		self.addMarker({'category' : 'host2','title':tscolor('\c00????00')+' >>> Series <<<'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Derniers ajouts','icon':cItem['icon'],'mode':'10','sub_mode':0})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Dernières sorties','icon':cItem['icon'],'mode':'10','sub_mode':1})		
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Les plus populaires','icon':cItem['icon'],'mode':'10','sub_mode':2})				
					
	def showitms(self,cItem):
		gnr=cItem.get('sub_mode',-1)
		mode = '21'
		if gnr > -1:
			url = self.MAIN_URL
			patern = '<section class.*?<h2>.*?</h2>(.*?)</section>'
			patern2 = '<a href="(.*?)".*?<img src="(.*?)".*?filmspan">(.*?)<br/>(.*?)</a>'
			if gnr == 7:
				patern2 = '<a href="(.*?)".*?<img src="(.*?)".*?alt="(.*?)"(.*?)'
				mode    = '10'
		else:
			url = cItem['url']
			patern  = '<section.*?<h1>.*?<div id(.*?)</section>'
			patern2 = '<a href="(.*?)".*?<img.*?src="(.*?)".*?</picture>(.*?)</a>(.*?)'	
			if 'studios.php' in url: patern2 = '<a href="(.*?)".*?<img src="(.*?)".*?filmspan">(.*?)<br/>(.*?)</a>'	
			gnr = 0
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall(patern, data, re.S)
			if Liste_els:
				data = Liste_els[gnr]
				Liste_els = re.findall(patern2, data, re.S)
				for (url,image,titre,desc) in Liste_els:
					titre = self.cleanHtmlStr(titre)
					desc = self.cleanHtmlStr(desc)
					image = image.replace('/small/','/')
					self.addDir({'import':cItem['import'],'category' : 'host2','title':titre  ,'url':self.MAIN_URL+url ,'desc':desc,'icon':self.MAIN_URL+'/'+image,'mode':mode,'good_for_fav':True,'EPG':True,'hst':'tshost'})					

	def showelms(self,cItem):
		url = cItem['url']
		printDBG('get url='+url)
		sts, data = self.getPage(url)
		if sts:
			printDBG('1')
			printDBG('2')
			Liste_els = re.findall('data-ws="([^"]+)">(.*?)</span>', data, re.S)
			if not Liste_els:
				Liste_els = re.findall('data-qualurl="([^"]+)">(.*?)</span>', data, re.S)
			for (url,qual) in Liste_els:
				if 'playlist/' in url:
					self.addMarker({'title':tscolor('\c0000????')+qual,'icon':cItem['icon']})
					url_list = self.MAIN_URL+'/'+url
					sts, data_ep = self.getPage(url_list)
					if sts:
						data_ep = data_ep.replace('\r','|||').replace('\n','|||').replace('||||||','|||').replace('|||','###|||')+'###'
						printDBG('data_ep='+data_ep)
						Liste_eps = re.findall('\|\|\|(.*?),(.*?)###', data_ep, re.S)
						for (url1,name1) in Liste_eps:
							self.addVideo({'import':cItem['import'],'category' : 'host2','title':name1,'url':url1 ,'desc':cItem['desc'],'icon':cItem['icon'],'good_for_fav':True,'hst':'direct'})	
				else:
					printDBG('3')
					titre = cItem['title'] + ' - '+qual
					self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url ,'desc':cItem['desc'],'icon':cItem['icon'],'good_for_fav':True,'hst':'direct'})
	
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc = cItem.get('desc','')
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('filminfos">(.*?)</p>', data, re.S)
			if lst_dat: 
				if self.cleanHtmlStr(lst_dat[0])!='':
					desc = tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+self.cleanHtmlStr(lst_dat[0])			
			lst_dat=re.findall('synopsis">(.*?)</p>', data, re.S)
			if lst_dat: 
				if self.cleanHtmlStr(lst_dat[0])!='':
					desc = desc + '\n' + tscolor('\c00????00')+'Story: '+tscolor('\c00??????')+self.cleanHtmlStr(lst_dat[0])
		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/movies_list.php'
		sts, data = self.getPage(url_)
		if sts:
			Liste_els = re.findall('<a class="item" href="([^"]+)" title="([^"]+)"> *<img src="([^"]+)">', data, re.S)
			for (url,titre,image) in Liste_els:
				image = image.replace('/small/','/')
				if str_ch.lower() in titre: 
					self.addDir({'import':extra,'category' : 'host2','title':titre,'url':self.MAIN_URL+url ,'desc':'','icon':self.MAIN_URL+'/'+image,'mode':'21','good_for_fav':True,'EPG':True,'hst':'tshost'})					

	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		elif mode=='10':
			self.showitms(cItem)
		elif mode=='21':
			self.showelms(cItem)		
		return True
