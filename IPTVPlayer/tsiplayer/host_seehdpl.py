# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.packer import cPacker

try:
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
except:
	pass 
###################################################


import re
import base64
import urllib,cookielib,time

def getinfo():
	info_={}
	info_['name']='Seehd.pl'
	info_['version']='1.1 22/02/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'
	info_['desc']='Movies & TV shows'
	info_['icon']='https://i.ibb.co/mJymy06/seehd.png'
	info_['recherche_all']='1'
	info_['update']='Fix cloudFlare'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'seehdpl.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
		self.MAIN_URL = 'http://www.seehd.pl'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		#self.getPage = self.cm.getPage


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
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'MOVIES',       'url': self.MAIN_URL+'/category/movies/', 'mode':'30'},
					{'category':hst,'title': 'TV SHOWS',     'url': self.MAIN_URL+'/category/tv-shows/', 'mode':'30'},
					{'category':hst,'title': 'Hd',           'url': self.MAIN_URL+'/category/hd/', 'mode':'30'},
					{'category':hst,'title': 'Featured',     'url': self.MAIN_URL+'/category/featured-movies-and-tv-shows/', 'mode':'30'},																					
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_,'desc':''})				

	
	def showitms(self,cItem):
		url=cItem['url']
		page=cItem.get('page',1)
		url_=url+'page/'+str(page)+'/'
		sts, data = self.getPage(url_)
		if sts:
			cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
			films_list = re.findall('movie big">(.*?)<h2.*?title">(.*?)<.*?href="(.*?)">.*?src="(.*?)"', data, re.S)		
			for (desc1,titre,url,image) in films_list:
				image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
				desc = ph.clean_html(desc1)
				titre = titre.replace('Watch Online','')
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url':url,'title':ph.clean_html(titre),'desc':desc,'icon':image,'hst':'tshost'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('movie big">(.*?)<h2.*?title">(.*?)<.*?href="(.*?)">.*?src="(.*?)"', data, re.S)		
			for (desc1,titre,url,image) in films_list:
				desc = ph.clean_html(desc1)
				titre = titre.replace('Watch Online','')
				self.addVideo({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'video','url':url,'title':ph.clean_html(titre),'desc':desc,'icon':image,'hst':'tshost'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			Tab_els = re.findall('tabtitle">(.*?)<(.*?)</center>', data, re.S)
			for (titre0,data0) in Tab_els:		
				local=''
				Tab_els0 = re.findall('<iframe.*?src="(.*?)"', data0, re.S|re.IGNORECASE)		
				if Tab_els0:
					URL=Tab_els0[0]
					if '24hd' in URL:
						local='local'
						urlTab.append({'name':gethostname(URL), 'url':'hst#tshost#'+URL+'|XXSEE', 'need_resolve':1,'type':local})
					else:
						urlTab.append({'name':gethostname(URL), 'url':URL, 'need_resolve':1})
						
		return urlTab
		
		
	def getVideos(self,videoUrl):
		urlTab = []	
		videoUrl,x1=videoUrl.split('|')
		if '24hd' in videoUrl:
			url_post=videoUrl.replace('/v/','/api/source/')
			data_post = {'r':'','d':'24hd.be'}
			sts, data = self.getPage(url_post,post_data=data_post)
			if sts:
				printDBG('ffffffffffff'+data)
				Tab_els0 = re.findall('"file":"(.*?)".*?label":"(.*?)".*?type":"(.*?)"', data, re.S)
				for (url,label,type_) in Tab_els0:
					name = type_+' ['+label+']'
					urlTab.append((name+'|'+url.replace('\\',''),'4'))
						
		return urlTab		
	
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc= cItem.get('desc','')	
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('<div class="quads.*?<p><strong>(.*?)<a', data, re.S)
			if lst_dat:
				desc=lst_dat[0].replace('<strong>','\\n'+tscolor('\c00????00'))
				desc=desc.replace('</strong>',tscolor('\c00??????'))
				desc=ph.clean_html(desc)
			else:
				desc= cItem['desc']				
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
			
