# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
try:
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
	from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
except:
	pass 
	
import re
import time,urllib,cookielib


def getinfo():
	info_={}
	info_['name']='Cima4u.Tv'
	info_['version']='1.5 02/09/2019' 
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام, مسلسلات و انمي عربية و اجنبية'
	info_['icon']='https://apkplz.net/storage/images/aflam/egybest/film/aflam.egybest.film_1.png'
	info_['recherche_all']='1'
	info_['update']='change to w.cima4u.tv'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'cima4u.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'http://w.cima4u.tv'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
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
		Cima4u_TAB = [
					{'category':hst,'title': 'Films', 'mode':'20'},
					{'category':hst,'title': 'Series','mode':'21'},
					{'category':hst,'title': 'WWE','link':self.MAIN_URL+'/category/%d9%85%d8%b5%d8%a7%d8%b1%d8%b9%d8%a9-%d8%ad%d8%b1%d8%a9-wwe/','mode':'30','page':1},
					{'category':hst,'title': 'برامج تلفزيونية','link':'http://live.cima4u.tv/24.%D8%A8%D8%B1%D8%A7%D9%85%D8%AC+%D8%AA%D9%84%D9%81%D8%B2%D9%8A%D9%88%D9%86%D9%8A%D8%A9.html','mode':'31','page':1},							
					{'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
					]
		self.listsTab(Cima4u_TAB, {'import':cItem['import'],'icon':img_})						

	def showmenu1(self,cItem):
		hst='host2'
		img_=cItem['icon']
		Cima4u_films_Cat = [{'title': 'افلام عربي',  'link':self.MAIN_URL+'/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%b9%d8%b1%d8%a8%d9%8a-arabic-movies/'},
							{'title': 'افلام اجنبي', 'link':self.MAIN_URL+'/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a-movies-english/'},
							{'title': 'افلام كرتون', 'link':self.MAIN_URL+'/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d9%83%d8%b1%d8%aa%d9%88%d9%86-movies-anime-cartoon/'},
							{'title': 'افلام هندي',  'link':self.MAIN_URL+'/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d9%87%d9%86%d8%af%d9%8a-indian-movies/'},
							]
		self.listsTab(Cima4u_films_Cat, {'import':cItem['import'],'category':hst,'page':1, 'mode':'30','icon':img_})									

	def showmenu2(self,cItem):
		hst='host2'
		img_=cItem['icon']
		Cima4u_series_Cat = [  #{'title': 'مسلسلات وبرامج رمضان 2019','link':'http://live.cima4u.tv/35.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D9%88%D8%A8%D8%B1%D8%A7%D9%85%D8%AC+%D8%B1%D9%85%D8%B6%D8%A7%D9%86+2019.html'},
							   {'title': 'مسلسلات وبرامج رمضان 2018','link':'http://live.cima4u.tv/34.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D9%88%D8%A8%D8%B1%D8%A7%D9%85%D8%AC+%D8%B1%D9%85%D8%B6%D8%A7%D9%86+2018.html'},
							   {'title': 'مسلسلات وبرامج رمضان 2017','link':'http://live.cima4u.tv/29.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D9%88%D8%A8%D8%B1%D8%A7%D9%85%D8%AC+%D8%B1%D9%85%D8%B6%D8%A7%D9%86+2017.html'},
							   {'title': 'مسلسلات رمضان 2016',       'link':'http://live.cima4u.tv/28.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%B1%D9%85%D8%B6%D8%A7%D9%86+2016.html'},
							   {'title': 'مسلسلات اجنبى',            'link':'http://live.cima4u.tv/25.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%A7%D8%AC%D9%86%D8%A8%D9%89.html'},
							   {'title': 'مسلسلات مصريه',            'link':'http://live.cima4u.tv/10.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D9%85%D8%B5%D8%B1%D9%8A%D9%87.html'},
							   {'title': 'مسلسلات خليجيه',           'link':'http://live.cima4u.tv/11.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%AE%D9%84%D9%8A%D8%AC%D9%8A%D9%87.html'},
							   {'title': 'مسلسلات مدبلجة',           'link':'http://live.cima4u.tv/33.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D8%A9.html'},
							   {'title': 'مسلسلات تركيه مترجمه',     'link':'http://live.cima4u.tv/13.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%AA%D8%B1%D9%83%D9%8A%D9%87+%D9%85%D8%AA%D8%B1%D8%AC%D9%85%D9%87.html'},
							   {'title': 'مسلسلات تركيه مدبلجه',     'link':'http://live.cima4u.tv/14.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%AA%D8%B1%D9%83%D9%8A%D9%87+%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D9%87.html'},
							   {'title': 'مسلسلات اسيوية مترجمة',    'link':'http://live.cima4u.tv/19.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%A7%D8%B3%D9%8A%D9%88%D9%8A%D8%A9+%D9%85%D8%AA%D8%B1%D8%AC%D9%85%D8%A9.html'},
							   {'title': 'مسلسلات اسيوية مدبلجة',    'link':'http://live.cima4u.tv/20.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%A7%D8%B3%D9%8A%D9%88%D9%8A%D8%A9+%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D8%A9.html'},
							   {'title': 'مسلسلات هندية مترجمة',     'link':'http://live.cima4u.tv/23.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D9%87%D9%86%D8%AF%D9%8A%D8%A9+%D9%85%D8%AA%D8%B1%D8%AC%D9%85%D8%A9.html'},
							   {'title': 'مسلسلات هندية مدبلجة',     'link':'http://live.cima4u.tv/22.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D9%87%D9%86%D8%AF%D9%8A%D8%A9+%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D8%A9.html'},
							   {'title': 'مسلسلات انيمي مترجمة',     'link':'http://live.cima4u.tv/17.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%A7%D9%86%D9%8A%D9%85%D9%8A+%D9%85%D8%AA%D8%B1%D8%AC%D9%85%D8%A9.html'},
							   {'title': 'مسلسلات انيمي مدبلجة',     'link':'http://live.cima4u.tv/16.%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%A7%D9%86%D9%8A%D9%85%D9%8A+%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D8%A9.html'},
							]	
		self.listsTab(Cima4u_series_Cat, {'import':cItem['import'],'category':hst,'page':1,'icon':img_,'mode':'31'})
		
	def showitms_films(self,cItem):
		url1=cItem['link']
		page=cItem['page']
		sts, data = self.getPage(url1+'page/'+str(page)+'/')
		if sts:
			Liste_els = re.findall('</h2>(.*?)(class="pagination"|<footer>)', data, re.S)
			
			if Liste_els:
				films_list = re.findall('class="block">.*?<a href="(.*?)".*?background-image:url\((.*?)\).*?"boxtitle">(.*?)<.*?"boxdetil">(.*?)<\/div>', Liste_els[0][0], re.S)		
				for (url,image,titre,desc) in films_list:
					titre=titre.replace('مشاهدة فيلم ','')
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':titre,'desc':desc,'icon':image,'hst':'tshost','EPG':True})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','link':url1,'icon':image,'mode':'30'} )									

	def showitms_series(self,cItem):
		url1=cItem['link']
		page=cItem['page']
		sts, data = self.getPage(url1+'?PageID='+str(page))
		if sts:
			Liste_els = re.findall('</h2>(.*?)(class="pagination"|<footer>)', data, re.S)
			if Liste_els:
				films_list = re.findall('class="block">.*?<a href="(.*?)".*?background-image:url\((.*?)\).*?"boxtitle">(.*?)<', Liste_els[0][0], re.S)		
				for (url,image,titre) in films_list:
					titre=titre.replace('مشاهدة مسلسل ','')
					titre=titre.replace('مشاهدة برنامج ','')
					titre=titre.replace('مشاهدة','')
					self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':'','icon':image,'mode':'32'} )
				self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','link':url1,'icon':cItem['icon'],'mode':'31'})				

	def showepisodes(self,cItem):
		URL=cItem['url']  
		titre=cItem['title'] 	
		sts, data = self.getPage(URL)
		if sts:
			Liste_els = re.findall('حلقات المسلسل(.*?)<footer>', data, re.S)
			if Liste_els:	
				Liste_els_2 =  re.findall('<a href="(.*?)".*?</span>(.*?)<', Liste_els[0], re.S)
				for (url,titre) in Liste_els_2:
					titre=titre.replace('(','').replace(')','')
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':titre,'desc':url,'icon':cItem['icon'],'hst':'tshost','EPG':True} )
			
	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('class="block">.*?<a href="(.*?)".*?background-image:url\((.*?)\).*?"boxtitle">(.*?)<.*?"boxdetil">(.*?)<\/div>', data, re.S)		
			for (url,image,titre,desc) in films_list:
				titre=titre.replace('مشاهدة فيلم ','')
				titre=titre.replace('مشاهدة مسلسل ','')
				self.addVideo({'import':extra,'good_for_fav':True,'category' : 'video','url': url,'title':titre,'desc':desc,'icon':image,'hst':'tshost'} )
		
		
	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			Trailer_els = re.findall('class="modalTrailer".*?<iframe.*?src="(.*?)"', data, re.S)
			if Trailer_els:
				urlTab.append({'name':'TRAILER', 'url':Trailer_els[0], 'need_resolve':1})	
			Liste_els = re.findall('"embedURL" content="(.*?)"', data, re.S)		
			if Liste_els:
				sts, data = self.getPage(Liste_els[0])
			Liste_els = re.findall('"serversList">.*?<h2>(.*?)(<h2>|<footer>)', data, re.S)
			if Liste_els:		
				Liste_els_2 =  re.findall('data-link="(.*?)".*?/>(.*?)<', Liste_els[0][0], re.S)
				for (code,host_) in Liste_els_2:
					host_ = host_.replace(' ','')
					if 'thevids' in host_.lower(): host_= 'thevideobee'
					urlTab.append({'name':host_, 'url':'hst#tshost#'+code, 'need_resolve':1})						
		return urlTab
		
		 
	def getVideos(self,videoUrl):
		urlTab = []	
		sUrl = 'http://live.cima4u.tv/structure/server.php?id='+videoUrl
		post_data = {'id':videoUrl}
		sts, data = self.getPage(sUrl, post_data=post_data)
		if sts:
			Liste_els_3 = re.findall('src="(.*?)"', data, re.S)	
			if Liste_els_3:
				urlTab.append((Liste_els_3[0].replace('\r',''),'1'))
		return urlTab
		
	def getArticle(self, cItem):
		printDBG("cima4u.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc= cItem['desc']
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('class="tags">(.*?)</div>', data, re.S)
			if lst_dat:
				lst_dat2=re.findall('<span>(.*?)</span>(.*?)</p>', lst_dat[0], re.S)
				for (x1,x2) in lst_dat2:
					if 'النوع'  in x1: otherInfo1['genres'] = ph.clean_html(x2)
					if 'القسم'  in x1: otherInfo1['categories'] = ph.clean_html(x2)			
					if 'الجودة'  in x1: otherInfo1['quality'] = ph.clean_html(x2)					
					if 'السنة'  in x1: otherInfo1['year'] = ph.clean_html(x2)					
			lst_dat=re.findall('storyContent">(.*?)</div>', data, re.S)
			if lst_dat:		
				desc=ph.clean_html(lst_dat[0])
				
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
			self.showitms_films(cItem)			
		if mode=='31':
			self.showitms_series(cItem)
		if mode=='32':
			self.showepisodes(cItem)
			
