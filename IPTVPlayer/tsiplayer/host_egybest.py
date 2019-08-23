# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass
from Components.config import config
from Plugins.Extensions.IPTVPlayer.tools.e2ijs import js_execute
import base64
import re



def getinfo():
	info_={}
	info_['name']='Egy.Best'
	info_['version']='1.1 14/05/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='104'
	info_['desc']='أفلام عربية و اجنبية + مسلسلات اجنبية'
	info_['icon']='https://cdn-static.egybest.net/static/img/egybest_logo.png'
	info_['recherche_all']='1'
	info_['update']='Site Out'
		
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'TSIPlayer.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://egy.best/'	
		self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.AJAX_HEADER = dict(self.HTTP_HEADER)
		self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
		self.defaultParams = {'header':self.HTTP_HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.error_login_egy=False
		self.egy_intro()
	def egy_intro(self):
		self.loggedIn = False
		if (config.plugins.iptvplayer.ts_egybest_email.value!='' and config.plugins.iptvplayer.ts_egybest_pass.value !=''):
			try:
				self.login = config.plugins.iptvplayer.ts_egybest_email.value
				self.password = config.plugins.iptvplayer.ts_egybest_pass.value
				sts, data = self.getPage('https://egy.best/?login=check')
				if sts and '/logout' in data and 'تسجيل الدخول' not in data:
					printDBG('Login OK')
					self.loggedIn = True
				else:	
					rm(self.COOKIE_FILE)
					self.tryTologin()
			except:
				pass 

	def getPage(self, baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
		
		
		
	def tryTologin(self):
		printDBG('tryTologin start')
		self.loggedIn = False
		url = 'https://ssl.egexa.com/login/?domain=egy.best&url=ref'
		sts, data = self.getPage(url)
		if sts:
			sts, data = ph.find(data, ('<form', '>', ph.check(ph.any, ('LoginForm', 'login_form'))), '</form>')
			if sts:
				actionUrl, post_data = self.cm.getFormData(data, url)
				post_data.update({'email':self.login, 'password':self.password})
				httpParams = dict(self.defaultParams) 
				httpParams['header'] = dict(httpParams['header'])
				httpParams['header']['Referer'] = url
				sts, data = self.getPage(actionUrl, httpParams, post_data)
				if sts:
					sts, data = self.getPage(self.getFullUrl('/?login=check'))
		if sts and '/logout' in data and 'تسجيل الدخول' not in data:
			printDBG('tryTologin OK')
			self.loggedIn = True
		else:
			if self.error_login_egy:
				self.sessionEx.open(MessageBox, _('Login failed.'), type = MessageBox.TYPE_ERROR, timeout = 10)
				self.error_login_egy=True
			printDBG('tryTologin failed')
		return self.loggedIn


	def showmenu0(self,cItem):
		hst='host2'
		img=cItem['icon']	
		Cimaclub_TAB=[{'category':hst,'title': 'Films'    ,'mode':'20'  ,'icon':img ,'sub_mode':'film'},
					{'category':hst,'title': 'Series'   ,'mode':'20' ,'icon':img ,'sub_mode':'serie'},					  
					{'category':'search'  ,'title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':img},
					]
		self.listsTab(Cimaclub_TAB, {'import':cItem['import'],'name':hst})
	def showmenu1(self,cItem):
		base='https://egy.best'
		gnr2=cItem['sub_mode']
		hst='host2'
		img=cItem['icon']			 
		url='https://egy.best/'
		sts1, data = self.getPage(url)
				
		if gnr2=='film':
			sts, data2 = self.getPage('https://egy.best/movies/')
			if sts:
				lst_data1 = re.findall('<div class="sub_nav">(.*?)<div id="movies',data2, re.S)
				if  lst_data1:
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :'host2', 'url':'', 'title':'\c00????00'+'By Filter', 'desc':'', 'icon':img, 'mode':'21', 'count':1,'data':lst_data1[0],'code':'','type_':'movies'})						
		
			self.addMarker({'title':'\c0000??00Main','icon':'','desc':''})				
			egy_films=[ {'title': 'أفلام جديدة'       , 'url':'https://egy.best/movies/'      , 'mode':'30', 'page':1},						  
						{'title': 'احدث الاضافات'     , 'url':'https://egy.best/movies/latest' , 'mode':'30', 'page':1},						  
						{'title': 'أفضل الافلام', 'url':'https://egy.best/movies/top'  , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر شهرة' , 'url':'https://egy.best/movies/popular' , 'mode':'30', 'page':1},
						]							
			self.listsTab(egy_films, {'import':cItem['import'],'name':'categories', 'category':hst, 'desc':'', 'icon':img})		
			self.addMarker({'title':'\c0000??00Trendinge','icon':'','desc':''})				
			egy_films=[ {'title': 'الاكثر مشاهدة الان'       , 'url':'https://egy.best/trending/'      , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر مشاهدة اليوم'     , 'url':'https://egy.best/trending/today' , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر مشاهدة هذا الاسبوع', 'url':'https://egy.best/trending/week'  , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر مشاهدة هذا الشهر' , 'url':'https://egy.best/trending/month' , 'mode':'30', 'page':1},						  
						]
			self.listsTab(egy_films, {'import':cItem['import'],'name':'categories', 'category':hst, 'desc':'', 'icon':img})
			if sts1:
				self.addMarker({'title':'\c0000??00Genre','icon':'','desc':''})					
				lst_data1 = re.findall('mgb table full">.*?href="(.*?)">(.*?)<.*?td">.*?href="(.*?)">(.*?)<',data, re.S)
				for (url1,titre1,url2,titre2) in lst_data1:
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':base+url1, 'title':titre1, 'desc':titre1, 'icon':img, 'mode':'30', 'page':1})				
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':base+url2, 'title':titre2, 'desc':titre2, 'icon':img, 'mode':'30', 'page':1})

			
 
		if gnr2=='serie':
			sts, data2 = self.getPage('https://egy.best/tv/')
			if sts:
				lst_data1 = re.findall('<div class="sub_nav">(.*?)<div id="movies',data2, re.S)
				if  lst_data1:
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':'', 'title':'\c00????00'+'By Filter', 'desc':'', 'icon':img, 'mode':'21', 'count':1,'data':lst_data1[0],'code':'','type_':'tv'})						
		
			self.addMarker({'title':'\c0000??00Main','icon':'','desc':''})				
			egy_films=[ {'title': 'احدث الحلقات'  , 'url':'https://egy.best/tv/'        , 'mode':'30', 'page':1},						  
						{'title': 'مسلسلات جديدة'  , 'url':'https://egy.best/tv/new'     , 'mode':'30', 'page':1},						  
						{'title': 'أفضل المسلسلات' , 'url':'https://egy.best/tv/top'     , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر شهرة'    , 'url':'https://egy.best/tv/popular' , 'mode':'30', 'page':1},	
						]
			self.listsTab(egy_films, {'import':cItem['import'],'name':'categories', 'category':hst, 'desc':'', 'icon':img})				

	def showmenu2(self,cItem):	
		hst='host2'
		img=cItem['icon']	
		count=cItem['count']
		data=cItem['data']	
		codeold=cItem['code']	
		type_=cItem['type_']			
		lst_data1 = re.findall('class="dropdown">(.*?)</div></div>',data, re.S)	
		if lst_data1:
			data2=lst_data1[count-1]
			if count==7:
				url='https://egy.best/'+type_+'/'+codeold
				self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':url, 'title':'الكل', 'desc':codeold, 'icon':img, 'mode':'30', 'page':1})					
			else:
				self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':'', 'title':'الكل', 'desc':codeold, 'icon':img, 'mode':'21', 'count':count+1,'data':data,'code':codeold,'type_':type_})
			lst_data2 = re.findall('href="/'+type_+'/(.*?)">(.*?)<',data2, re.S)					
			for (code,titre) in lst_data2:
				if codeold!='':
					code = codeold+'-'+code
				if count==7:
					url='https://egy.best/'+type_+'/'+code
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':url, 'title':titre, 'desc':code, 'icon':img, 'mode':'30', 'page':1})					
				else:	
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':'', 'title':titre, 'desc':code, 'icon':img, 'mode':'21', 'count':count+1,'data':data,'code':code,'type_':type_})
		
	def showitms(self,cItem):
		hst='host2'
		img=cItem['icon']	
		base='https://egy.best'
		page=cItem['page']
		url0=cItem['url']
		url=url0+'?page='+str(page)+'&output_format=json&output_mode=movies_list'
		sts, data = self.getPage(url)
		if sts:
			data=data.replace('\\"','"')	
			data=data.replace('\\/','/')				
			lst_data=re.findall('<a href="(.*?)".*?rating">(.*?)</i>.*?src="(.*?)".*?title">(.*?)<.*?ribbon.*?<span>(.*?)<', data, re.S)			
			for (url1,rate,image,name_eng,qual) in lst_data:
				desc='Rating:'+self.cleanHtmlStr(rate)+'  Qual:'+qual
				self.addDir({'import':cItem['import'],'good_for_fav':True, 'name':'categories', 'category':hst, 'url':base+url1, 'title':str(name_eng.decode('unicode_escape')), 'desc':desc,'EPG':True,'hst':'tshost', 'icon':image, 'mode':'31'} )							
			self.addDir({'import':cItem['import'],'name':'categories', 'category':hst, 'url':url0, 'title':'Page Suivante', 'page':page+1, 'desc':'Page Suivante', 'icon':img, 'mode':'30'})	

	def showelems(self,cItem):
		desc=''
		base='https://egy.best'
		img=cItem['icon']
		url0=cItem['url']	
		titre=cItem['title']
		sts, data = self.getPage(url0)
		if sts:
			cat_data0=re.findall('<table class="movieTable full">(.*?)</table>', data, re.S)
			if cat_data0:
				desc1=cat_data0[0].replace('<tr',' | <tr')
				desc=self.cleanHtmlStr(desc1)+'\n'
				
			cat_data0=re.findall('القصة</strong>.*?<div.*?">(.*?)</div>', data, re.S)
			if cat_data0:
				desc1=cat_data0[0]
				desc=desc+self.cleanHtmlStr(desc1)
								
			cat_data2=re.findall('<div id="yt_trailer".*?url="(.*?)".*?src="(.*?)"', data, re.S)
			for (URl,IMg) in cat_data2:					
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'name':'categories','category' : 'video','url': URl,'title':'Trailer','desc':desc,'icon':IMg,'hst':'none'})						
							
			if (('/series/' in url0) or ('/season/' in url0)):			
				cat_data=re.findall('movies_small">(.*?)</div>', data, re.S)	
				if cat_data:
					el_data=re.findall('<a href="(.*?)".*?src="(.*?)".*?">(.*?)<', cat_data[0], re.S)
					for (url1,image,name_eng) in el_data:					
						self.addDir({'import':cItem['import'],'good_for_fav':True, 'name':'categories', 'category':'host2', 'url':base+url1, 'title':name_eng, 'desc':desc, 'icon':img, 'mode':'31'} )							
			else: 
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'name':'categories','category' : 'video','url': url0,'title':titre,'desc':desc,'icon':img,'hst':'tshost'})			
		
		
		
	def SearchResult(self,str_ch,page,extra):
		url_='https://egy.best/explore/?page='+str(page)+'&output_format=json&q='+str_ch+'&output_mode=movies_list'
		sts, data = self.getPage(url_)	
		if sts:
			data=data.replace('\\"','"')	
			data=data.replace('\\/','/')				
			lst_data=re.findall('<a href="(.*?)".*?rating">(.*?)</i>.*?src="(.*?)".*?title">(.*?)<.*?ribbon.*?<span>(.*?)<', data, re.S)			
			for (url1,rate,image,name_eng,qual) in lst_data:
				desc='Rating:'+self.cleanHtmlStr(rate)+'  Qual:'+qual
				url1='https://egy.best/'+url1
				url1=url1.replace('best//','best/')
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True, 'name':'categories', 'category':'host2', 'url':url1, 'title':str(name_eng.decode('unicode_escape')), 'desc':desc, 'icon':image, 'mode':'31','hst':'tshost'} )							
		
		
	def get_links(self,cItem): 	
		urlTab = []
		URL=cItem['url']	
		sts, data1 = self.getPage(URL)
		if sts:
			Liste_els0 = re.findall('<table(.*?)</table>', data1, re.S)
			if Liste_els0:
				printDBG('data='+Liste_els0[-1])
				urlTab.append({'name':'1', 'url':'rr', 'need_resolve':0})
				urlTab.append({'name':'2', 'url':'rr', 'need_resolve':0})
				Liste_els1 = re.findall('<iframe.*?src="(.*?)"', data1, re.S)
				if Liste_els1:
					printDBG('dat1111a='+Liste_els1[0])
					data = self.cm.getCookieItems(self.COOKIE_FILE)
					printDBG('dat1111a22='+str(data))
					sts, data = self.getPage(Liste_els1[0])
					printDBG('dat1111a222='+data)
					sts, data = self.getPage(Liste_els1[0])
					printDBG('dat1111a2223='+data)
					data = self.cm.getCookieItems(self.COOKIE_FILE)
					printDBG('dat1111a22='+str(data))
					urlTab.append({'name':'2', 'url':'rr', 'need_resolve':0}) 
				'''
				Liste_els1 = re.findall('<tr>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?data-url.*?"(.*?)"', Liste_els0[-1], re.S)
				for (x1,type_,x3,src_) in Liste_els1:
					sts, data = self.getPage('https://egy.best'+src_)#,{'header':HTTP_HEADER})	
					if sts:	
						printDBG('dat1111a='+data)
						Liste_els0 = re.findall('assets/style.css.*?javascript">(.*?)</script>', data, re.S)
						jscode = Liste_els0[0]
						jscode = part1 + '\n' + jscode + '\n' + part2
						ret = js_execute( jscode )
						#if ret['sts'] and 0 == ret['code']:
						'''
						
						
						
						

					
					
					
					
					
					
				'''
				printDBG('login url='+Liste_els0[-1])
				stsx, datax = self.getPage(Liste_els0[-1])			
				Liste_els = re.findall('<video.*?type="(.*?)".*?src="(.*?)"', data1, re.S)
				for(type_,src_) in Liste_els:
					sts, data = self.getPage('https://egy.best'+src_)#,{'header':HTTP_HEADER})	
					if sts:	
						Link = re.findall('#EXT-X-STREAM.*?RESOLUTION=(.*?),.*?(htt.*?m3u8)', data, re.S)
						for (_res,_url) in Link:
							urlTab.append({'name':_res, 'url':_url, 'need_resolve':0})
				if self.loggedIn == True:
					Liste_els = re.findall('<tbody>(.*?)</div>', data1, re.S)
					if Liste_els:					
						Liste_els1 = re.findall('<tr>.*?<td>(.*?)<.*?<td>(.*?)<.*?<td>(.*?)<.*?call="(.*?)"', Liste_els[0], re.S)
						for(qual1,qual2,qual3,call_) in Liste_els1:			
							name=qual1+' '+qual2+' ('+qual3+')'
							urlTab.append({'name':name, 'url':'hst#tshost#'+call_+'|'+'ttttt'+'|'+URL, 'need_resolve':1})
'''
		return urlTab

		 
	def getVideos(self,videoUrl):
		urlTab = []	
		url_,code_,refer=videoUrl.split('|')
		HTTP_HEADER= {'X-Requested-With':'XMLHttpRequest','Referer':refer,'Cookie':code_}
		
		params = dict(self.defaultParams)
		params['header'] = dict(self.AJAX_HEADER)
		params['header']['Referer'] = refer
		params['with_metadata'] = True		
		

		sts, data = self.getPage('https://egy.best/api?call='+url_,params)
		if '"action":"start_dl"' in data:
			data=data.replace('\\','')
			_data2 = re.findall('"url":"(.*?)".*?auth_url":"(.*?)"',data, re.S) 
			if _data2:
				URL_1=_data2[0][0]
				URL_2=_data2[0][1]						
				sts, tmp = self.getPage(URL_2,{'header':HTTP_HEADER})
				if sts:
					meta = {'direct':True}
					meta.update({'Referer':refer})
					urlTab.append((strwithmeta(URL_1, meta),'0'))
		elif '"action":"api"' in data:		
			_data2 = re.findall('"api":"(.*?)"',data, re.S) 
			if _data2:
				sts, data1 = self.getPage('https://egy.best/api?call='+_data2[0])	
		
		return urlTab	 							
		
	def getArticle(self, cItem):
		printDBG("EgyBest.getArticleContent [%s]" % cItem)
		desc = ''
		retTab = []
		otherInfo = {}
		sts, data = self.getPage(cItem['url'])
		if sts:
			desc = ph.clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<strong', '</div>', 'القصة'), ('</div', '>'), False)[1])
			tmp  = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'full_movie'), ('</table', '>'), False)[1]
			icon  = self.cm.ph.getDataBeetwenNodes(tmp, ('<div', '>', 'movie_img'), ('</div', '>'), False)[1]
			icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(icon, '''src=['"]([^'^"]+?)['"]''')[0])
			title = ph.clean_html(self.cm.ph.getDataBeetwenNodes(tmp, ('<div', '>', 'movie_title'), ('</div', '>'), False)[1])

			keysMap = {'اللغة • البلد'            :'country',
					   'التصنيف'                  :'type',
					   'النوع'                    :'genres', 
					   'التقييم العالمي'          :'rating',
					   'المدة'                    :'duration',
					   'الجودة'                   :'quality',
					   'الترجمة'                  :'translation'}

			tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<tr>', '</tr>')
			for item in tmp:
				item = item.split('</td>', 1)
				if len(item) != 2: continue
				keyMarker = ph.clean_html(item[0]).replace(':', '').strip()
				printDBG("+++ keyMarker[%s]" % keyMarker)
				value = ph.clean_html(item[1]).replace(' , ', ', ')
				key = keysMap.get(keyMarker, '')
				if key != '' and value != '': otherInfo[key] = value

			# actors
			tTab = []
			tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<div', '>', 'cast_item'), ('</span', '>'))
			for t in tmp:
				t = ph.clean_html(t)
				if t != '': tTab.append(t)
			if len(tTab): otherInfo['actors'] = ', '.join(tTab)

		title = cItem['title']
		if desc == '':  desc = cItem.get('desc', '')
		cItem.get('icon', '')

		return [{'title':ph.clean_html( title ), 'text': ph.clean_html( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]

	
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
			self.showelems(cItem)
