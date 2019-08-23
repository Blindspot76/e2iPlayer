# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,unifurl

import re

def getinfo():
	info_={}
	info_['name']='Arabseed.Com'
	info_['version']='1.3 30/06/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'#'201'
	info_['desc']='أفلام و مسلسلات عربية و اجنبية'
	info_['icon']='https://arabseed.com/themes/arabseed/img/logo-c.png'
	info_['recherche_all']='1'
	info_['update']='Bugs Fix'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'arabseed.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://arabseed.net'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		
	def getPage2(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
		return sts, data


	def getPage3(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		sts, data = self.cm.getPage(baseUrl, addParams, post_data)
		printDBG(str(sts))
		if "'jschl-answer'" in data:
			#try:
			import cookielib
			import time
			from Plugins.Extensions.IPTVPlayer.tsiplayer.libs import cfscrape		
			scraper = cfscrape.create_scraper()
			data = scraper.get(baseUrl).content
			tokens, user_agent=cfscrape.get_tokens(self.MAIN_URL)
			sts = True
			cj = self.cm.getCookie(self.COOKIE_FILE)
			
			cook_dat=re.findall("'(.*?)'.*?'(.*?)'", str(tokens), re.S)			
			for (cookieKey,cookieValue) in cook_dat:
				cookieItem = cookielib.Cookie(version=0, name=cookieKey, value=cookieValue, port=None, port_specified=False, domain='.'+self.cm.getBaseUrl(baseUrl, True), domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=time.time()+3600*48, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
				cj.set_cookie(cookieItem)		
			printDBG( 'save cookies=')
			cj.save(self.COOKIE_FILE, ignore_discard = True)
			printDBG( 'saveed')
			'''except Exception as e:
				printDBG( 'Erreur='+str(e) )	
				addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
				sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)'''
		return sts, data

		 
	def showmenu0(self,cItem):
		hst='host2'
		self.Arablionz_TAB = [
							{'category':hst, 'sub_mode':0, 'title': 'افلام',       'mode':'20'},
							{'category':hst, 'sub_mode':1, 'title': 'مسلسلات',     'mode':'20'},
							#{'category':hst, 'sub_mode':2, 'title':'رمضان 2019',  'mode':'20'},
							{'category':hst, 'sub_mode':3, 'title': 'اقسام اخري', 'mode':'20'},
							{'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
							]		
		self.listsTab(self.Arablionz_TAB, {'import':cItem['import'],'icon':cItem['icon']})	

	def showmenu1(self,cItem):
		hst='host2'
		gnr=cItem['sub_mode']
		if gnr<2:
			sts, data = self.getPage(self.MAIN_URL)
			if sts:
				cat_film_data=re.findall('<ul class="sub-menu">(.*?)</ul>', data, re.S) 
				if cat_film_data:
					data2=re.findall('<li.*?href="(.*?)">(.*?)<', cat_film_data[gnr], re.S)
					for (url,titre) in data2:
						url=self.MAIN_URL+url
						self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
		elif gnr==2:	
			self.Arablionz_TAB = [
								{'category':hst,'title': 'مسلسلات رمضان 2019',    'mode':'30', 'url':self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%B1%D9%85%D8%B6%D8%A7%D9%86-2019'},
								{'category':hst,'title': 'برامج رمضان 2019',     'mode':'30', 'url':self.MAIN_URL+'/category/%D8%A8%D8%B1%D8%A7%D9%85%D8%AC-%D8%B1%D9%85%D8%B6%D8%A7%D9%86-2019'},
								]		
			self.listsTab(self.Arablionz_TAB, {'import':cItem['import'],'icon':cItem['icon']})	
			
		elif gnr==3:			
			self.Arablionz_TAB = [
								{'category':hst,'title': 'مصارعه',          'mode':'30', 'url':self.MAIN_URL+'/category/%D9%85%D8%B5%D8%A7%D8%B1%D8%B9%D9%87'},
								{'category':hst,'title': 'برامج تلفزيونية', 'mode':'30', 'url':self.MAIN_URL+'/category/%D8%A8%D8%B1%D8%A7%D9%85%D8%AC-%D8%AA%D9%84%D9%81%D8%B2%D9%8A%D9%88%D9%86%D9%8A%D8%A9'},
								{'category':hst,'title': 'مسرحيات عربية',   'mode':'30', 'url':self.MAIN_URL+'/category/%D9%85%D8%B3%D8%B1%D8%AD%D9%8A%D8%A7%D8%AA-%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9'},
								{'category':hst,'title': 'رياضه',           'mode':'30', 'url':self.MAIN_URL+'/category/%D8%B1%D9%8A%D8%A7%D8%B6%D9%87'},
								]		
			self.listsTab(self.Arablionz_TAB, {'import':cItem['import'],'icon':cItem['icon']})	

		
	def showitms(self,cItem):
		page=cItem.get('page',1)
		urlorg=cItem['url']
		titre=cItem['title']
		img=cItem['icon']
		url1=urlorg+'?page='+str(page)
		sts, data = self.getPage(url1)
		if sts:
			data1=re.findall('class="media-block.*?href="(.*?)".*?data-src="(.*?)".*?class="details">(.*?)</div>.*?class="info">.*?<h3>(.*?)</h3>(.*?)</div>', data, re.S)		
			i=0
			for (url,image,inf,titre,desc) in data1:
				inf_data=re.findall('class="ti.*?">(.*?)<', inf, re.S)		
				if inf_data:
					desc1='Rate: \c0000??00'+inf_data[0]+'\c00?????? \\n'
					try: desc1=desc1+'View: \c0000??00'+inf_data[1]+'\c00??????\\n'
					except: pass
					desc=desc1+ph.clean_html(desc)
				else:
					desc=ph.clean_html(desc)				
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'mode':'31','hst':'tshost'})			
				i=i+1
			if i>47:
				self.addDir({'import':cItem['import'],'name':'categories', 'category':'host2', 'url':urlorg, 'title':'Page Suivante', 'page':page+1, 'desc':'Page Suivante', 'icon':img, 'mode':'30'})	

	def showelms(self,cItem):
		url1=cItem['url']
		img=cItem['icon']
		self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url1,'title':cItem['title'],'desc':'','icon':img,'hst':'tshost'})		
		sts, data = self.getPage(url1)
		if sts:
			data1=re.findall('class="episodesSection">(.*?)</table>', data, re.S)		
			if data1:
				data2=re.findall('<tr>.*?<td>(.*?)<.*?href="(.*?)"', data1[0], re.S)
				for (titre,url) in data2:
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':'E'+titre,'desc':'','icon':img,'hst':'tshost'})	
	
	def SearchResult(self,str_ch,page,extra):	
		url_=self.MAIN_URL+'/search?s='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:		
			data1=re.findall('class="media-block.*?href="(.*?)".*?data-src="(.*?)".*?class="details">(.*?)</div>.*?class="info">.*?<h3>(.*?)</h3>(.*?)</div>', data, re.S)		
			i=0
			for (url,image,inf,titre,desc) in data1:
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'mode':'31','hst':'tshost'})			

		
	def get_links(self,cItem): 	
		urlTab = []	
		url=cItem['url']
		sts, data = self.getPage(url)
		if sts:
			data1 = re.findall('main-info">.*?href="(.*?)"', data, re.S)
			if data1:
				URL=data1[0].replace('download','watch')
				sts, data = self.getPage(URL)
				if sts:
					server_data = re.findall('servers-list">(.*?)</ul>', data, re.S)
					if server_data:
						server_data1 = re.findall('<li.*?(src|SRC)=&quot;(.*?)&quot;.*?">(.*?)<', server_data[0], re.S)
						for (x1,url,titre) in server_data1:
							url=unifurl(url)
							host=gethostname(url)
							titre = titre.replace('سيرفر','Server')
							titre=titre+'  \c0000??00( ' +host+' )'
							if not '/arabseed.' in url:
								urlTab.append({'name':titre, 'url':url, 'need_resolve':1})
							else:
								urlTab.append({'name':titre, 'url':'hst#tshost#'+url, 'need_resolve':1})

						if len(urlTab)==0:
							server_data2 = re.findall('<li.*?"(.*?)">(.*?)<', server_data[0], re.S)
							for (url,titre) in server_data2:
								url=unifurl(url)
								host=gethostname(url)
								titre = titre.replace('سيرفر','Server')
								titre=titre+'  \c0000??00( ' +host+' )'
								if not 'arabseed' in url:
									urlTab.append({'name':titre, 'url':url, 'need_resolve':1})
								else:
									urlTab.append({'name':titre, 'url':'hst#tshost#'+url, 'need_resolve':1})
			
			return urlTab
			
	def getVideos(self,videoUrl):
		urlTab = []	
		sts, data = self.getPage(videoUrl)
		if sts:
			Liste_els_3 = re.findall('<video.*?src="(.+?)"', data, re.S)	
			if Liste_els_3:
				urlTab.append((Liste_els_3[0],'0'))
		return urlTab
		
	def getArticle(self, cItem):
		printDBG("Arablionz.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc = cItem['desc']
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('<div class="content">(.*?)<ul>(.*?)</ul>', data, re.S)
			if lst_dat:
				desc = ph.clean_html(lst_dat[0][0])
				lst_dat0=re.findall("<li>(.*?):(.*?)</li>", lst_dat[0][1], re.S)
				for (x1,x2) in lst_dat0:
					if 'الجودة'     in x1: otherInfo1['quality'] = ph.clean_html(x2)
					if 'تأليف'      in x1: otherInfo1['writer'] = ph.clean_html(x2)				
					if 'إخراج'      in x1: otherInfo1['director'] = ph.clean_html(x2)	
					if 'النوع'      in x1: otherInfo1['genres'] = ph.clean_html(x2)				
					if 'المشاهدات'  in x1: otherInfo1['views'] = ph.clean_html(x2)
					if 'طاقم العمل' in x1: otherInfo1['actors'] = ph.clean_html(x2)
					if 'البلد'      in x1: otherInfo1['country'] = ph.clean_html(x2)	
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
		if mode=='31':
			self.showelms(cItem)

