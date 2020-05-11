# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads

try:
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
except:
	pass 

import re
import urllib

import cookielib
import time

def getinfo():
	info_={}
	info_['name']='Jetanimes.Com'
	info_['version']='1.0 05/10/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='104'
	info_['desc']='Animes et Mangas'
	info_['update']='New Host'		
	info_['icon']='https://i.ibb.co/zJh34S1/web-horizontal.png'

	info_['recherche_all']='0'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'jetanimes.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
		self.cookieHeader=''
		self.MAIN_URL = 'https://www.jetanimes.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.HEADER1 = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded'}
		self.defaultParams1 = {'header':self.HEADER1, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': 'dpstream.cookie'}



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
		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'En Cours'  ,'url':self.MAIN_URL+'/episodes/'    ,'icon':cItem['icon'],'mode':'31','sub_mode':2})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'FILMS Animes'  ,'url':self.MAIN_URL+'/films/'    ,'icon':cItem['icon'],'mode':'31'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'ANIMES VF/Vostfr'  ,'url':self.MAIN_URL+'/serie/'    ,'icon':cItem['icon'],'mode':'31'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c0000????')+'Par Genres|Années' ,'icon':cItem['icon'],'mode':'21'})
		self.addDir({'import':cItem['import'],'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})


	def showmenu1(self,cItem):
		url   = self.MAIN_URL
		sts, data = self.getPage(url)
		if sts:
			self.addMarker({'title':tscolor('\c0000????')+'Par Genres'  ,'icon':cItem['icon']})
			Liste_els = re.findall('<ul class="genres(.*?)</ul', data, re.S)
			if 	Liste_els:
				Liste_els = re.findall('<li.*?href="(.*?)">(.*?)<', Liste_els[0], re.S)
				for (url,titre) in Liste_els:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':ph.clean_html(titre)  ,'url':url    ,'icon':cItem['icon'],'mode':'31'})

			self.addMarker({'title':tscolor('\c0000????')+'Par Années'  ,'icon':cItem['icon']})	
			Liste_els = re.findall('<ul class="releases(.*?)</ul', data, re.S)
			if 	Liste_els:
				Liste_els = re.findall('<li.*?href="(.*?)">(.*?)<', Liste_els[0], re.S)
				for (url,titre) in Liste_els:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':ph.clean_html(titre)  ,'url':url    ,'icon':cItem['icon'],'mode':'31'})
					

	def showitms(self,cItem):
		gnr=cItem.get('sub_mode',9)
		url_or=cItem['url']	
		if gnr==9:
			page=cItem.get('page',1)
			url=url_or+'page/'+str(page)+'/'
			sts, data = self.getPage(url)
			if sts:
				cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
				Liste_els = re.findall('<article id="post-(.*?)".*?src="(.*?)".*?alt="(.*?)".*?"rating">(.*?)</div>.*?("featu">|"mepo">)(.*?)</div>.*?href="(.*?)">(.*?)</article>', data, re.S)
				i=0	
				for (x1,image,titre,rate,x2,qual,url,desc1) in Liste_els:
					if 'featured' not in x1:
						image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
						titre = ph.clean_html(titre) + ' '+tscolor('\c00????00')+ph.clean_html(qual)
						desc ='IMDB: '+ tscolor('\c00????00')+ph.clean_html(rate)
						self.addDir({'import':cItem['import'],'category' : 'host2','title':ph.clean_html(titre)  ,'url':url ,'EPG':True,'good_for_fav':True,'hst':'tshost','desc':desc,'icon':image,'mode':'32'})
						i=i+1
				if i>28:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':url_or,'page':page+1,'mode':'31'})
		if gnr==2:
			page=cItem.get('page',1)
			url=url_or+'page/'+str(page)+'/'
			sts, data = self.getPage(url)
			if sts:
				cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
				Liste_els = re.findall('class="item.*?src="(.*?)".*?alt="(.*?)".*?href="(.*?)".*?"b">(.*?)<.*?"c">(.*?)<.*?</div>(.*?)<span class="serie">(.*?)<.*?<h3>(.*?)</h3>(.*?)</article>', data, re.S)
				i=0	
				for (image,titre,url,x1,x2,qual,x3,x4,date_) in Liste_els:
					image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
					titre = ph.clean_html(titre) + ' '+tscolor('\c00????00')+'('+ph.clean_html(x4)+')'
					desc =tscolor('\c00????00')+ph.clean_html(qual)+' '+tscolor('\c00??????')+'| '+tscolor('\c0000????')+ph.clean_html(date_)
					self.addDir({'import':cItem['import'],'category' : 'host2','title':ph.clean_html(titre)  ,'url':url ,'EPG':True,'good_for_fav':True,'hst':'tshost','desc':desc,'icon':image,'mode':'32'})
					i=i+1
				if i>28:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':url_or,'page':page+1,'mode':'31','sub_mode':2})
	def showelms(self,cItem):
		urlo=cItem['url']	
		sts, data = self.getPage(urlo)
		if sts:
			if 'playeroptionsul' in data:
				self.addVideo({'import':cItem['import'],'category' : 'host2','title':cItem['title']  ,'url':cItem['url'] ,'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'})
			else:
				cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
				Liste_els = re.findall("class='imagen.*?src='(.*?)'.*?numerando'>(.*?)<.*?href='(.*?)'>(.*?)<.*?date'>(.*?)<", data, re.S)
				for (image,titre,url,x1,desc) in Liste_els:
					image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
					titre = ph.clean_html(titre) + ' '+tscolor('\c00????00')+ph.clean_html(x1)
					desc =tscolor('\c00????00')+ph.clean_html(desc)
					self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre  ,'url':url ,'desc':desc,'icon':image,'EPG':True,'good_for_fav':True,'hst':'tshost'})
					
	def SearchResult(self,str_ch,page,extra):

		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			cookieHeader = self.cm.getCookieHeader(self.COOKIE_FILE)
			Liste_els = re.findall('class="result.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?">(.*?)<.*?class="meta">(.*?)</div>.*?contenido">(.*?)</div>', data, re.S)
			for (url,image,titre,type_,meta_,desc) in Liste_els:
				image=strwithmeta(image,{'Cookie':cookieHeader, 'User-Agent':self.USER_AGENT})
				desc= ph.clean_html(meta_.replace('</span><span',' |<'))+'\\n'+ph.clean_html(desc)
				titre = ph.clean_html(titre)+ ' '+tscolor('\c00????00')+'('+type_+')'
				self.addDir({'import':extra,'category' : 'host2','title':titre,'desc':desc,'url':url,'icon':image,'hst':'tshost','good_for_fav':True,'EPG':True,'mode':'32'})


	def getArticle(self, cItem):
		printDBG("cima4u.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc= cItem['desc']	
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall("<span class='date'>(.*?)<", data, re.S)
			if lst_dat: otherInfo1['year'] = ph.clean_html(lst_dat[0])
			lst_dat=re.findall("class='country'>(.*?)<", data, re.S)
			if lst_dat: otherInfo1['country'] = ph.clean_html(lst_dat[0])				
			lst_dat=re.findall("class='runtime'>(.*?)<", data, re.S)
			if lst_dat: otherInfo1['duration'] = ph.clean_html(lst_dat[0])				
			lst_dat=re.findall("CR rated'>(.*?)<", data, re.S)
			if lst_dat: otherInfo1['age_limit'] = ph.clean_html(lst_dat[0])						
			lst_dat=re.findall("ratingValue\">(.*?)<", data, re.S)
			if lst_dat: otherInfo1['rating'] = ph.clean_html(lst_dat[0])				
			lst_dat=re.findall("sgeneros\">(.*?)</div>", data, re.S)
			if lst_dat: otherInfo1['genres'] = ph.clean_html(lst_dat[0])				
			lst_dat=re.findall("wp-content\">(.*?)</p>", data, re.S)
			if lst_dat: desc = ph.clean_html(lst_dat[0])			
			

		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]



	def get_links(self,cItem): 	
		urlTab = []
		url=cItem['url']	
		sts, data = self.getPage(url)
		if sts:
			Liste_els = re.findall('playeroptionsul\'>(.*?)</ul>', data, re.S)
			if 	Liste_els:
				Liste_els = re.findall("<li.*?data-post='(.*?)'.*?data-nume='(.*?)'.*?title'>(.*?)<.*?class='server'>(.*?)<", Liste_els[0], re.S)	
				for (post_,num_,titre,srv) in 	Liste_els:
					if 'cine.co' not in srv:	
						local=''	
						if 'paradise' in srv.lower(): local='local'
						urlTab.append({'name':'|'+titre.strip()+'| '+ srv, 'url':'hst#tshost#'+post_+'|'+num_, 'need_resolve':1,'type':local})	

		return urlTab	

	def getVideos(self,videoUrl):
		urlTab = []
		url=self.MAIN_URL+'/wp-admin/admin-ajax.php'
		post_,nume_=videoUrl.split('|')
		post_data = {'action':'doo_player_ajax','post':post_,'nume':nume_,'type':'movie'}	
	
		sts, data = self.getPage(url,post_data=post_data)
		if sts:
			Liste_els = re.findall('src=["\'](.*?)["\']', data, re.S)
			if 	Liste_els:
				URL_= Liste_els[0]
				if 'down-paradise' in URL_:
					post_data = {'r':'','d':'down-paradise.com'}						

					URL_=URL_.replace('/v/','/api/source/')
					sts, data = self.getPage(URL_, post_data=post_data)
					data = json_loads(data)
					elmdata = data['data']
					for elm0 in elmdata:
						urlTab.append((elm0['label']+'|'+elm0['file'],'4'))
						
				elif 'jetanimes.com' in URL_:						
					#sts, data,z1 = self.getPage(URL_)
					printDBG('jetanimes.com')	
						
						
						
				else:
					urlTab.append((URL_,'1'))	
		return urlTab	
			
	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		elif mode=='21':
			self.showmenu1(cItem)	
		elif mode=='31':
			self.showitms(cItem)
		elif mode=='32':
			self.showelms(cItem)		
		return True
