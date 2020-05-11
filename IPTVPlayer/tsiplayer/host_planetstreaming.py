# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler

try:
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
except:
	pass 
	
import re
import urllib,cookielib,time

def getinfo():
	info_={}
	info_['name']='Planet-Streaming.Net'
	info_['version']='1.3 22/03/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='301'
	info_['desc']='Films en VF & VOSTFR'
	info_['icon']='https://i.ibb.co/VvvSHFT/logo.png'
	info_['recherche_all']='1'
	info_['update']='New Host'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'planetstreaming.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'
		self.MAIN_URL = 'https://www.streaming-planet.net'
		self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1','Connection':'close','Cache-Control': 'no-cache','Pragma': 'no-cache', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'en-US,en;q=0.5', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'with_metadata':True,'no_redirection':False,'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}



	def getPage_old(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams) 
		addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
		return sts, data
				
	def getPage(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams) 
		sts, data = self.cm.getPage(baseUrl,addParams,post_data)
		if not data: data=''
		if '!![]+!![]' in data:
			try:
				printDBG('Start CLoudflare  Vstream methode')
				oRequestHandler = cRequestHandler(baseUrl)
				if post_data:
					post_data_vstream = ''
					for key in post_data:
						if post_data_vstream=='':
							post_data_vstream=key+'='+post_data[key]
						else:
							post_data_vstream=post_data_vstream+'&'+key+'='+post_data[key]					
					oRequestHandler.setRequestType(cRequestHandler.REQUEST_TYPE_POST)
					oRequestHandler.addParametersLine(post_data_vstream)					
				data = oRequestHandler.request()
				sts = True
				printDBG('cook_vstream_file='+self.up.getDomain(baseUrl).replace('.','_'))
				cook = GestionCookie().Readcookie(self.up.getDomain(baseUrl).replace('.','_'))
				printDBG('cook_vstream='+cook)
				if ';' in cook: cook_tab = cook.split(';')
				else: cook_tab = cook
				cj = self.cm.getCookie(self.COOKIE_FILE)
				for item in cook_tab:
					if '=' in item:	
						printDBG('item='+item)		
						cookieKey, cookieValue = item.split('=')
						cookieItem = cookielib.Cookie(version=0, name=cookieKey, value=cookieValue, port=None, port_specified=False, domain='.'+self.cm.getBaseUrl(baseUrl, True), domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=time.time()+3600*48, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
						cj.set_cookie(cookieItem)
				cj.save(self.COOKIE_FILE, ignore_discard = True)
			except Exception, e:
				printDBG('ERREUR:'+str(e))
				printDBG('Start CLoudflare  E2iplayer methode')
				addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
				sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)	
		return sts, data		

				 
	def showmenu0(self,cItem):
		hst='host2'
		Planet_TAB = [
							{'category':hst,      'title':'Films'                , 'mode':'30','url':'/regarder-film/'},
							{'category':hst,      'title':'Top Films Exclus'     , 'mode':'30','url':'/exclu/'},							
							{'category':hst,      'title':'Box Office'           , 'mode':'30','url':'/box-office/'},																		
							{'category':hst,      'title':'Genres'               , 'mode':'20'},							
							{'category':'search', 'title':_('Search')  ,'search_item':True,'page':1,'hst':'tshost'},
							]
		self.listsTab(Planet_TAB, {'import':cItem['import'],'icon':cItem['icon']})
			
	def showmenu1(self,cItem):	
		sts, data = self.getPage(self.MAIN_URL)
		if sts:
			data1 = re.findall('grid-column grid-column2.*?<ul>(.*?)</ul>',data, re.S)
			for data2 in data1:
				data3 = re.findall('<li>.*?href="(.*?)">(.*?)<',data2, re.S)
				for (url,titre) in data3:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'icon':cItem['icon'],'mode':'30'})
		
	def showitms(self,cItem):
		url0=cItem['url']
		page=cItem.get('page',1)
		surl=self.MAIN_URL+url0+'page/'+str(page)+'/'
		sts, data = self.getPage(surl)
		if sts:
			i=0
			data1 = re.findall('fullstream fullstreaming.*?src="(.*?)".*?quality-container">(.*?)</div>.*?href="(.*?)">(.*?)<.*?<FONT.*?>(.*?)fullinfo">',data, re.S)		
			for (image,qual,url,titre,desc) in data1:
				i=i+1
				desc=desc.replace('<strong><span','<stgrong><span')
				desc=desc.replace('<strong>Qualit','Qualit')			
				desc=desc.replace('<b>','\\n')
				desc=desc.replace('<strong>','\\n')
				desc=ph.clean_html(desc+'>').strip()		
				self.addVideo({'import':cItem['import'],'title':titre+' '+tscolor('\c0000??00')+'('+ph.clean_html(qual)+')','url':url,'desc':desc,'icon':image,'good_for_fav':True,'EPG':True,'hst':'tshost'})
			if i>14:
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':url0,'page':page+1,'mode':'30'})
		else:
			self.addMarker({'title':tscolor('\c00????00')+'----> Erreur <----','icon':'','desc':'Cloudflare problem'})

	def get_links(self,cItem): 	
		sts, data = self.getPage(cItem['url'])
		if not sts: return []
		linksTab = []
		data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', '-tab'), ('<script', '>'))[1]
		data = self.cm.ph.rgetAllItemsBeetwenNodes(data, ('</div', '>'), ('<div', '>', '-tab'))
		for langItem in data:
			langTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(langItem, '<div', '</div>')[1])
			langItem = self.cm.ph.getAllItemsBeetwenMarkers(langItem, '<a', '</a>')
			for item in langItem:
				url = self.getFullUrl( self.cm.ph.getSearchGroups(item, '''\shref=['"]([^'^"]+?)['"]''')[0] )
				if url == '': continue
				title = self.cleanHtmlStr(item)
				title = self.up.getDomain(url)
				title= '|'+langTitle.upper()+'| '+ title
				
				linksTab.append({'name':title, 'url':url, 'need_resolve':1})
		return linksTab

	def getArticle(self,cItem):
		otherInfo1 = {}
		desc = cItem['desc']
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('details">(.*?)</ul>', data, re.S)
			if lst_dat: 
				lst_dat2=re.findall('<strong><span(.*?)</strong>(.*?)<hr', lst_dat[0], re.S)
				for (x1,x2) in lst_dat2:
					if 'Date de sortie' in x1: otherInfo1['first_air_date'] = ph.clean_html(x2)
					if 'Réalisateur' in x1: otherInfo1['director'] = ph.clean_html(x2)				
					if 'Avec' in x1: otherInfo1['actors'] = ph.clean_html(x2)				
					if 'Catégorie' in x1: otherInfo1['genres'] = ph.clean_html(x2)
					if 'Langue' in x1: otherInfo1['language'] = ph.clean_html(x2)					
					if 'Film en Version' in x1: otherInfo1['quality'] = ph.clean_html(x2)						
					if 'Origine' in x1: otherInfo1['country'] = ph.clean_html(x2)
					
				lst_dat2=re.findall('Synopsis(.*?)</ul>', lst_dat[0]+'</ul>', re.S)
				if lst_dat2: desc = 'Resumé'+ph.clean_html(lst_dat2[0])
		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

	def SearchResult(self, str_ch,page,extra):
		post_data  = {'do':'search', 'subaction':'search', 'search_start':page, 'full_search':'0', 'result_from':1+(page-1)*12, 'story':str_ch} 
		url = self.MAIN_URL+'/index.php?do=search'
		sts, data = self.getPage(url, post_data=post_data)  
		if sts: 
			data1 = re.findall('fullstream fullstreaming.*?src="(.*?)".*?href="(.*?)">(.*?)<.*?"short-insider">(.*?)fullinfo">',data, re.S)		
			for (image,url,titre,desc) in data1:
				desc=desc.replace('<strong><span','<stgrong><span')
				desc =desc.replace('<strong> <b>','<b>')
				desc=desc.replace('<strong>Version','Version')
				desc=desc.replace('<b><strong></strong>','')			
				desc=desc.replace('<b>','\\n')
				desc=desc.replace('<strong>','\\n')
				desc=ph.clean_html(desc+'>').strip()		
				self.addVideo({'import':extra,'category' : 'video','title':titre,'url':url,'desc':desc,'icon':image,'good_for_fav':True,'EPG':True,'hst':'tshost'})
	   

			
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='30':
			self.showitms(cItem)			


