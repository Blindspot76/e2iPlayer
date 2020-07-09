# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG,GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost
from Components.config import config
from Plugins.Extensions.IPTVPlayer.tools.e2ijs import js_execute
import base64
import re
import urllib
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper            import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser

def getinfo():
	info_={}
	name = 'Egy.Best'
	hst = tshost(name)	
	if hst=='': hst = 'https://open.egybest.asia'
	info_['host']= hst
	info_['name']=name
	info_['version']='1.2.01 05/07/2020'
	info_['dev']='RGYSoft | Thx to >> @maxbambi & @zadmario <<'
	info_['cat_id']='201'
	info_['desc']='أفلام عربية و اجنبية + مسلسلات اجنبية'
	info_['icon']='https://i.ibb.co/z2SXTd8/souayah-Egy-Best-film.png'
	info_['recherche_all']='1'
	#info_['update']='Fix Vidstream Server'
		
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'egybest01.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Linux; Android 7.0; PLUS Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.98 Mobile Safari/537.36'
		self.MAIN_URL =  getinfo()['host']
		self.VID_URL  = 'https://vidstream.kim'
		self.varconst = 'a0'
		self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.AJAX_HEADER = dict(self.HTTP_HEADER)
		self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
		self.defaultParams = {'header':self.HTTP_HEADER, 'with_metadata':True,'no_redirection':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

	def getPage(self, baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		i=0
		data=''
		while ((len(str(data))<20) and (i<4)):
			sts,data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
			i=i+1
		return sts,data

	def showmenu0(self,cItem):
		hst='host2'
		img=cItem['icon']	
		Cimaclub_TAB=[{'category':hst,'title': 'Films'    ,'mode':'20'  ,'icon':img ,'sub_mode':'film'},
					{'category':hst,'title': 'Series'   ,'mode':'20' ,'icon':img ,'sub_mode':'serie'},					  
					{'category':'search'  ,'title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':img},
					]
		self.listsTab(Cimaclub_TAB, {'import':cItem['import'],'name':hst})
		#self.addDir({'import':cItem['import'], 'name':'categories', 'category':hst, 'url':'https://wilo.egybest.xyz/movie/gemini-man-2019/?ref=movies-p1', 'title':'Test Link', 'desc':'','hst':'tshost', 'icon':'', 'mode':'31'} )							
		
		
	def showmenu1(self,cItem):
		base=self.MAIN_URL
		gnr2=cItem['sub_mode']
		hst='host2'
		img=cItem['icon']			 
		url=self.MAIN_URL+'/'
		sts1, data = self.getPage(url)
				
		if gnr2=='film':
			sts, data2 = self.getPage(self.MAIN_URL+'/movies/')
			if sts:
				lst_data1 = re.findall('<div class="sub_nav">(.*?)<div id="movies',data2, re.S)
				if  lst_data1:
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :'host2', 'url':'', 'title':'\c00????00'+'By Filter', 'desc':'', 'icon':img, 'mode':'21', 'count':1,'data':lst_data1[0],'code':'','type_':'movies'})						
		
			self.addMarker({'title':'\c0000??00Main','icon':'','desc':''})				
			egy_films=[ {'title': 'أفلام جديدة'       , 'url':self.MAIN_URL+'/movies/'      , 'mode':'30', 'page':1},						  
						{'title': 'احدث الاضافات'     , 'url':self.MAIN_URL+'/movies/latest' , 'mode':'30', 'page':1},						  
						{'title': 'أفضل الافلام', 'url':self.MAIN_URL+'/movies/top'  , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر شهرة' , 'url':self.MAIN_URL+'/movies/popular' , 'mode':'30', 'page':1},
						]							
			self.listsTab(egy_films, {'import':cItem['import'],'name':'categories', 'category':hst, 'desc':'', 'icon':img})		
			self.addMarker({'title':'\c0000??00Trendinge','icon':'','desc':''})				
			egy_films=[ {'title': 'الاكثر مشاهدة الان'       , 'url':self.MAIN_URL+'/trending/'      , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر مشاهدة اليوم'     , 'url':self.MAIN_URL+'/trending/today' , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر مشاهدة هذا الاسبوع', 'url':self.MAIN_URL+'/trending/week'  , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر مشاهدة هذا الشهر' , 'url':self.MAIN_URL+'/trending/month' , 'mode':'30', 'page':1},						  
						]
			self.listsTab(egy_films, {'import':cItem['import'],'name':'categories', 'category':hst, 'desc':'', 'icon':img})
			if sts1:
				self.addMarker({'title':'\c0000??00Genre','icon':'','desc':''})					
				lst_data1 = re.findall('mgb table full">.*?href="(.*?)">(.*?)<.*?td">.*?href="(.*?)">(.*?)<',data, re.S)
				i=0
				for (url1,titre1,url2,titre2) in lst_data1:
					if i<10:
						self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':url1, 'title':titre1, 'desc':titre1, 'icon':img, 'mode':'30', 'page':1})				
						self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':url2, 'title':titre2, 'desc':titre2, 'icon':img, 'mode':'30', 'page':1})
						i=i+1
			
 
		if gnr2=='serie':
			sts, data2 = self.getPage(self.MAIN_URL+'/tv/')
			if sts:
				lst_data1 = re.findall('<div class="sub_nav">(.*?)<div id="movies',data2, re.S)
				if  lst_data1:
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':'', 'title':'\c00????00'+'By Filter', 'desc':'', 'icon':img, 'mode':'21', 'count':1,'data':lst_data1[0],'code':'','type_':'tv'})						
		
			self.addMarker({'title':'\c0000??00Main','icon':'','desc':''})				
			egy_films=[ {'title': 'احدث الحلقات'  , 'url':self.MAIN_URL+'/tv/'        , 'mode':'30', 'page':1},						  
						{'title': 'مسلسلات جديدة'  , 'url':self.MAIN_URL+'/tv/new'     , 'mode':'30', 'page':1},						  
						{'title': 'أفضل المسلسلات' , 'url':self.MAIN_URL+'/tv/top'     , 'mode':'30', 'page':1},						  
						{'title': 'الاكثر شهرة'    , 'url':self.MAIN_URL+'/tv/popular' , 'mode':'30', 'page':1},	
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
				url=self.MAIN_URL+'/'+type_+'/'+codeold
				self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':url, 'title':'الكل', 'desc':codeold, 'icon':img, 'mode':'30', 'page':1})					
			else:
				self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':'', 'title':'الكل', 'desc':codeold, 'icon':img, 'mode':'21', 'count':count+1,'data':data,'code':codeold,'type_':type_})
			lst_data2 = re.findall('href=".*?'+type_+'/(.*?)".*?>(.*?)<',data2, re.S)					
			for (code,titre) in lst_data2:
				if codeold!='':
					code = codeold+'-'+code
				if count==7:
					url=self.MAIN_URL+'/'+type_+'/'+code
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':url, 'title':titre, 'desc':code, 'icon':img, 'mode':'30', 'page':1})					
				else:	
					self.addDir({'import':cItem['import'],'name':'categories', 'category' :hst, 'url':'', 'title':titre, 'desc':code, 'icon':img, 'mode':'21', 'count':count+1,'data':data,'code':code,'type_':type_})
		
	def showitms(self,cItem):
		hst='host2'
		img=cItem['icon']	
		base=self.MAIN_URL
		page=cItem['page']
		url0=cItem['url']
		url=url0+'?page='+str(page)+'&output_format=json&output_mode=movies_list'
		sts, data = self.getPage(url)
		if sts:
			data=data.replace('\\"','"')	
			data=data.replace('\\/','/')				
			lst_data=re.findall('<a href="(.*?)".*?rating">(.*?)</i>.*?src="(.*?)".*?title">(.*?)<.*?ribbon.*?<span>(.*?)<', data, re.S)			
			for (url1,rate,image,name_eng,qual) in lst_data:
				desc=tscolor('\c00????00')+'Rating: '+tscolor('\c00??????')+self.cleanHtmlStr(rate)+'/10 | '+tscolor('\c00????00')+'Qual: '+tscolor('\c00??????')+qual
				x1,titre=self.uniform_titre(str(name_eng.decode('unicode_escape')))
				titre=titre.replace('()','')
				self.addDir({'import':cItem['import'],'good_for_fav':True, 'name':'categories', 'category':hst, 'url':base+url1, 'title':titre, 'desc':desc,'EPG':True,'hst':'tshost', 'icon':image, 'mode':'31'} )							
			self.addDir({'import':cItem['import'],'name':'categories', 'category':hst, 'url':url0, 'title':tscolor('\c0090??20')+_('Next page'), 'page':page+1, 'desc':'', 'icon':img, 'mode':'30'})	

	def showelems(self,cItem):
		desc=''
		base=self.MAIN_URL
		
		img=cItem['icon']
		url0=cItem['url']
		if not url0.startswith('http'): url0 = self.MAIN_URL+url0	
		titre=cItem['title']
		titre=titre.replace('|'+tscolor('\c0060??60')+'EgyBest'+tscolor('\c00??????')+'| ','') #for mediabox
		sts, data = self.getPage(url0)
		if sts:
			desc=''
			tmp  = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'full_movie'), ('</table', '>'), False)[1]
			keysMap = {'اللغة • البلد'            :'Country: ',
					   'التصنيف'                  :'Type: ',
					   'النوع'                    :'Genres: ', 
					   'التقييم العالمي'          :'Rating: ',
					   'المدة'                    :'Duration: ',
					   'الجودة'                   :'Quality: ',
					   'الترجمة'                  :'Translation: '}

			tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<tr>', '</tr>')
			for item in tmp:
				item = item.split('</td>', 1)
				if len(item) != 2: continue
				keyMarker = ph.clean_html(item[0]).replace(':', '').strip()
				printDBG("+++ keyMarker[%s]" % keyMarker)
				value = ph.clean_html(item[1]).replace(' , ', ', ')
				key = keysMap.get(keyMarker, '')
				if key != '' and value != '': desc = desc+tscolor('\c00????00')+key+tscolor('\c00??????')+value	+' | '	
			
			
		
				
			cat_data0=re.findall('القصة</strong>.*?<div.*?">(.*?)</div>', data, re.S)
			if cat_data0:
				desc1=cat_data0[0]
				desc=desc+'\n'+tscolor('\c00????00')+'Info: '+tscolor('\c0000????')+self.cleanHtmlStr(desc1)
								
			cat_data2=re.findall('<div id="yt_trailer".*?url="(.*?)".*?src="(.*?)"', data, re.S)
			for (URl,IMg) in cat_data2:					
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'name':'categories','category' : 'video','url': URl,'title':'Trailer','desc':desc,'icon':IMg,'hst':'none'})						
							
			if (('/series/' in url0) or ('/season/' in url0)):			
				cat_data=re.findall('movies_small">(.*?)</div>', data, re.S)	
				if cat_data:
					el_data=re.findall('<a href="(.*?)".*?src="(.*?)".*?title">(.*?)<', cat_data[0], re.S)
					for (url1,image,name_eng) in el_data:					
						self.addDir({'import':cItem['import'],'good_for_fav':True, 'name':'categories', 'category':'host2', 'url':url1, 'title':self.cleanHtmlStr(name_eng.strip()), 'desc':desc, 'icon':img, 'mode':'31'} )							
			else: 
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'name':'categories','category' : 'video','url': url0,'title':titre,'desc':desc,'icon':img,'hst':'tshost'})			
		
		
		
	def SearchResult(self,str_ch,page,extra):
		printDBG('extra='+extra)
		url_=self.MAIN_URL+'/explore/?page='+str(page)+'&output_format=json&q='+str_ch+'&output_mode=movies_list'
		sts, data = self.getPage(url_)	
		if sts:
			data=data.replace('\\"','"')	
			data=data.replace('\\/','/')				
			lst_data=re.findall('<a href="(.*?)".*?rating">(.*?)</i>.*?src="(.*?)".*?title">(.*?)<.*?ribbon.*?<span>(.*?)<', data, re.S)			
			for (url1,rate,image,name_eng,qual) in lst_data:
				#desc='Rating:'+self.cleanHtmlStr(rate)+'  Qual:'+qual
				desc=tscolor('\c00????00')+'Rating: '+tscolor('\c00??????')+self.cleanHtmlStr(rate)+'/10 | '+tscolor('\c00????00')+'Qual: '+tscolor('\c00??????')+qual
				x1,titre=self.uniform_titre(str(name_eng.decode('unicode_escape')))
				titre=titre.replace('()','')				
				if 'series/' in url1: titre=titre+ tscolor('\c00????00')+'(SERIE)'
				url1=self.MAIN_URL+url1
				#url1=url1.replace('best//','best/')
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True, 'name':'categories', 'category':'host2', 'url':url1, 'title':titre, 'desc':desc, 'icon':image, 'mode':'31','hst':'tshost'} )							
	


	def MediaBoxResult(self,str_ch,year_,extra):
		urltab=[]
		str_ch_o = str_ch
		str_ch = urllib.quote(str_ch_o+' '+year_)
		trouver=False
		i=1
		while (not trouver) and (i<3):
			url_=self.MAIN_URL+'/explore/?page='+str(i)+'&output_format=json&q='+str_ch+'&output_mode=movies_list'
			sts, data = self.getPage(url_)	
			if sts:
				data=data.replace('\\"','"')	
				data=data.replace('\\/','/')				
				lst_data=re.findall('<a href="(.*?)".*?rating">(.*?)</i>.*?src="(.*?)".*?title">(.*?)<.*?ribbon.*?<span>(.*?)<', data, re.S)			
				for (url1,rate,image,name_eng,qual) in lst_data:
					desc=tscolor('\c00????00')+'Rating: '+tscolor('\c00??????')+self.cleanHtmlStr(rate)+'/10 | '+tscolor('\c00????00')+'Qual: '+tscolor('\c00??????')+qual
					x1,titre0=self.uniform_titre(str(name_eng.decode('unicode_escape')),year_op=2)
					desc=x1.replace('\n','')+' | '+desc			
					if 'series/' in url1: titre=titre0+ tscolor('\c00????00')+'(SERIE)'
					else: titre=titre0
					url1=self.MAIN_URL+url1
					titre_='|'+tscolor('\c0060??60')+'EgyBest'+tscolor('\c00??????')+'| '+titre
					printDBG('star compart:'+titre+':'+x1+' vs '+year_+':'+str_ch_o)
					if (titre.replace('-',' ').replace(':',' ').replace('.',' ').lower().replace(' ','') == str_ch_o.lower().replace(' ','')) and (x1==year_):
						urltab.insert(0,{'titre':titre0,'import':extra,'good_for_fav':True,'EPG':True, 'name':'categories', 'category':'host2', 'url':url1, 'title':titre_, 'desc':desc, 'icon':image, 'mode':'31','hst':'tshost'} )							
						trouver=True
						break
					else:
						urltab.append({'titre':titre0,'import':extra,'good_for_fav':True,'EPG':True, 'name':'categories', 'category':'host2', 'url':url1, 'title':titre_, 'desc':desc, 'icon':image, 'mode':'31','hst':'tshost'} )							
			i=i+1
		
		return urltab

		
	def get_links(self,cItem): 			
		urlTab = []
		URL=cItem['url']
		printDBG(' ----------> Link='+URL)	
		sts, data = self.getPage(URL)
		if sts:
			Liste_els0 = re.findall('<iframe.*?src="(.*?)"', data, re.S)
			if Liste_els0:			
				urlTab.append({'name':'|HLS| Vidstream', 'url':'hst#tshost#'+Liste_els0[0], 'need_resolve':1,'type':'local'})
			
			#Liste_els0 = re.findall('<table(.*?)</table>', data, re.S)
			#if Liste_els0:
			#	printDBG('data='+Liste_els0[-1])
			#	Liste_els1 = re.findall('<tr>.*?<td>(.*?)<td class.*?url="(.*?)"', Liste_els0[-1], re.S)
			#	for (titre,url) in Liste_els1:
			#		urlTab.append({'name':'|'+ph.clean_html(titre)+'| Vidstream', 'url':'hst#tshost#'+url+'&v=1'+'%%%'+cItem['url'], 'need_resolve':1,'type':'local'})
				
		return urlTab

		 
	def getVideos(self,videoUrl):
		printDBG(' -----------> URL = '+videoUrl)
		urlTab = []	
		referer = self.MAIN_URL
		if '%%%' in videoUrl: videoUrl,referer = videoUrl.split('%%%',1)
		if not videoUrl.startswith('http'): videoUrl=self.MAIN_URL+videoUrl
		if 'watch/?v' in videoUrl:
			try:
				printDBG('try resolve url0: '+videoUrl)
				urlTab = self.parserVIDSTREAM(videoUrl,'egy')
			except Exception, e:
				printDBG('ERREUR:'+str(e))
		else:
			addParams0 = dict(self.defaultParams)
			addParams0['header']['Referer']=referer
			sts, data = self.getPage(videoUrl,addParams0)
			if sts:
				printDBG('referer = '+str(referer))
				printDBG('meta = '+str(data.meta))
				printDBG('data = '+str(data))
				URL = data.meta['location']
				cj = self.cm.getCookie(addParams0['cookiefile'])
				printDBG('cj = '+str(cj))
				if URL == referer:
					printDBG('------------PROBLEM----------')
					sts, data = self.getPage(URL,addParams0)
					if sts:
						printDBG('data = '+str(data))
						# look for javascript
						script =''
						tmp_script = re.findall("<script.*?>(.*?)</script>", data, re.S)
						for s in tmp_script:
							if ('(){ var'in s):
								script = s
								break
						#script = "function InfEQSD(){ var a0a=['wrTMbovoLuoTY1dMnue','OcdZp','EUCKHO','KisU0X','aabmCg','2xUV0MbovoLuoTY7Hsz92','WhSay','aETAmiKOnBspfh','TUdAdLcsZ','xgkTQiduC','vQJU5a','ad720mMSLqvqLALbrl6RS','wLOqbqvqLqmnzDSeE','yXLqLumCLqvjRdR7ZO','LqLumCLqv','3t1VqLqT&authprnB','WABvI','ZtViEkt','YoKyRVCl','hsSBMW','GnefFpSHzm','lh2ffeG','yL95b','ybiVJ2q4AW','MwSxV','mCKWe','HzaEW','mfoTSRD','AOguR','aIMLlNcYr','qCGTPyq7v','#GlobalFrame','ICUzQ2RpdiUyMGNsYXNzJTNEJTIybXNnX2JveCUyMGVycm9yJTIwZnVsbCUyMHRhbSUyMEh4eVlHOFIxNXZoMzd1SyUyMiUzRSUzQ2klMjBjbGFzcyUzRCUyMnNpZ24lMjBpLXdhcm4lMjIlM0UlM0MlMkZpJTNFJTNDaDQlM0UlRDklOEElRDglQUMlRDglQTglMjAlRDglQjklRDklODQlRDklOEElRDklODMlMjAlRDglQUElRDglQjklRDglQjclRDklOEElRDklODQlMjAlM0NzdHJvbmclM0UlRDklODUlRDglQTclRDklODYlRDglQjklMjAlRDglQTclRDklODQlRDglQTclRDglQjklRDklODQlRDglQTclRDklODYlRDglQTclRDglQUElMjAtJTIwQWRCbG9jayUzQyUyRnN0cm9uZyUzRSUyMCVEOCVBNyVEOSU4OCUyMCVEOCVCOSVEOCVBRiVEOSU4NSUyMCVEOCVBNyVEOCVCQSVEOSU4NCVEOCVBNyVEOSU4MiUyMCVEOCVBNyVEOSU4NCVEOCVBNyVEOCVCOSVEOSU4NCVEOCVBNyVEOSU4NiUyMCVEOCVBOCVEOCVCMyVEOCVCMSVEOCVCOSVEOCVBOSUyMCVEOCVBRCVEOCVBQSVEOSU4OSUyMCVEOSU4QSVEOSU4NSVEOSU4MyVEOSU4NiVEOSU4MyUyMCVEOCVBNyVEOSU4NCVEOCVBQSVEOCVBRCVEOSU4NSVEOSU4QSVEOSU4NCUyMCVEOSU4OCUyMCVEOCVBNyVEOSU4NCVEOSU4NSVEOCVCNCVEOCVBNyVEOSU4NyVEOCVBRiVEOCVBOSUyMCVEOSU4NSVEOCVBQyVEOCVBNyVEOSU4NiVEOCVBNyVEOSU4Qi4lM0MlMkZoNCUzRSUyMCUzQ2ltZyUyMHNyYyUzRCUyMmh0dHBzJTNBJTJGJTJGY2RuLXN0YXRpYy5lZ3liZXN0Lm5ldCUyRnN0YXRpYyUyRmltZyUyRmNocm9tZS1ibG9jay1fREVWVF8ucG5nJTNGbSUzRDElMjIlMjBzdHlsZSUzRCUyMm1heC13aWR0aCUzQSUyMDk1JTI1JTNCJTIyJTNFJTIwJTNDJTJGZGl2JTNF','qYa4DmU','aEIg0cet4','nLKaC','DJjL46c','gyhovjDL','YWKsTQOp','2zRky3T','closed','.nop','TCKTZ','fdjjigrHod','function','mIKaLqLAet','VzqvqLqmnz8ZwXugV','ZhiYm9','8HUzHaETAmiKvy2u','sCbbh','BRqmadqr','taQQt','vJfjNR','Apr485f94jxBr4A','dga3JT','lWaKq','eLiCwNHjBM','RPnQLP','2S2f6cFn2','UxhtSVi','href','GZeHvvAnLj','ajax','MuTq8K2S','9vAvAvwMYSKB','45wmMKpAmi82BrZ6J','yimiCsu5CSlKe','sJpfT1sQX','EqLZHqmWja3','qLdjaofUw','GEMGr','WpSD','dWUXhaZ','MDfrVb','dCnfXTJXw','qHNpnIx','wAvEyQPLt','mob','wRXRfKl','T21mIKaLqLh77E2','userAgent','MbovoLuoTY','u3pjtVI6','SzSLxOMX','TWlYnDi','tBkJjC','9WWIcUMd','BQKNE','2H1Sxlvcl','icd4AMbovoLuoTYUi6T0iz','constructor','OQleu','UzRR6','addClass','HTcHf','EaUrsPnigq','mHMww','=0c002','rFDCXnWx','DkEijvzJ','AdovsvdqVA71BNw','HcChumMEU','Hf5d53001KP11c','vkpes','CVmwymEKS1hkez','piqTQc','euHDWI','BTmCW','vAvAv','zdzIYKub','fWJmz','nop','1qqkVzETp5','tKISteA','5J6XFwymEKSuq8U','0awkRzooiiOpVp','open','className','tFapAQaTCq','KLfxe4T','target','wymEKS','PuAqK','uqmEG','V3fqqqLqkUG','GN6EPuqLvLqLmKGjB','POST','NMUpwRL','V3vGq','qLZHqmW','XfNlEi','KyxQQQtCOP','O1K72RkS','return\x20/\x22\x20+\x20this\x20+\x20\x22/','M1oqomalAzohqjdB','length','Vfa477cdbRx8ulTE','B8eCw8KG','aUM0s1','B5Efa477cdbSg1jh','TyeWEx','o95Zf5d53001Ukwt','fLjr3485f94a4T5shk','xCJohmCLvLqLKicHhlB','MZQln2','VBfXTXtjud','SohmCLvLqLKjlF','rISyfN','parents','qwjQPrZMqB','YoKyR','CSLqvocqljjZ','sn9sFLWkbz','oOdrUiA','F5miCsuLZpxVm','location','BqLZHqmWInGG','7z1V6I','IBsSHd','replace','BGLjXmMKpAmiROmK','scyvy','SLqvocq','ovsvdqVAz4x2Y4','JdegPVrUAW','/click.php','HXbmURcdqo','CU61g','vEKcp','120','k1aJ6AJQdv','ZfS05vq','JRItJ5','oLf5P4jn','fqqqLq','lsuRnd','fa477cdb','test','mIKaLqL','lEkIN','HJqWK','TW3cd07ydL','blQMVwZrh','5fC7LPnyiN','^([^\x20]+(\x20+[^\x20]+)+)+[^\x20]}','MlChohmCLvLqLKOvh','khdt98uCl5','5RriOqbLT','spOobixdV','blQMV','anidxr','2sUmzn8','aSvAvAvngGNg','mMKpAmi','5mMKpAmiEptZ','wpGONp','iUrukzI','OxISLQ','5qoKFNJA','7miCsucBrpxD','lYceNj','E3MhovsvdqVAEeBfDy9','PFNpNc','6eVqLqT&authx7LWSEf','D6ypRopyY5','Vafvf','yIQUeJRVa','/api?call=','hyusBG4','gncjTn','21Z9vk8qX','gjyJB','JStmV','lAMVMGJ','apply','FZRY','mfoTSRDXOL','LFgcmz','muqfGtb','RENZoO','fqqqLqLCx1Iaa','mjmfoTSRDMkQ2','NotificationsAsk','485f94','undefined','EPuqLvLqLJnm','gHrW=0c002IcP','click','qrdHwGK','YRN6oHFDxw','bax485f94nkvV','YfRzooiiOf84gKai','enqbfeAlrp','WJi4pX7o','awtnphyJs','QloFt','JBuQzwV','uuEBuCKED','mBKRSdQkid','OQBEm','qvqLqmnz','C0oLqLumCLqvcRG','mXVF','uAZKGQnp','bVZUfqqqLqBsiq','compact','CmIdterrUm','xeJhmMSLqvqLALlMoRK','yAbYWni','l8wymEKS0KsH','mWfwIOv','atob','OHZzvstFWh','1xblQMVH21L','sSUgwPS','SgvAdT','search','Nf9kt44k6','tTXdV','_DEVT_','Ox6Tb','toApnxb','gfIvgvRW','5MGIr5','compile','WsoXyPbr','T0ogKR','PrPmgE','qPMyi','M=0c002BNF','qttcCSP','4X9pRzooiiONHf','MtjxMCtzMr','kh2jPZP6O','4775b','eQNZMw','YoKyR6uj','f5d53001','DwbVHHt','UEGpqvqLqmnzT9EWX','sAXOJnOpp','VqLqT&authF82','wkTmpyTcC','QSTQi','iRIJYN','87F5oqomalAzoh8mwC','sRvje','CuxZYI','miCsu','FPBLqLumCLqvg0Q','top','LYFvowT','mQAZD','qdKxn','g9QENlL','xewJqvJeLu','DOdPngH','ovsvdqVA','jUFJn'];(function(a,b){var c=function(g){while(--g){a['push'](a['shift']());}};var d=function(){var g={'data':{'key':'cookie','value':'timeout'},'setCookie':function(k,l,m,n){n=n||{};var o=l+'='+m;var p=0x0;for(var q=0x0,r=k['length'];q<r;q++){var s=k[q];o+=';\x20'+s;var t=k[s];k['push'](t);r=k['length'];if(t!==!![]){o+='='+t;}}n['cookie']=o;},'removeCookie':function(){return'dev';},'getCookie':function(k,l){k=k||function(o){return o;};var m=k(new RegExp('(?:^|;\x20)'+l['replace'](/([.$?*|{}()[]\/+^])/g,'$1')+'=([^;]*)'));var n=function(o,p){o(++p);};n(c,b);return m?decodeURIComponent(m[0x1]):undefined;}};var h=function(){var k=new RegExp('\x5cw+\x20*\x5c(\x5c)\x20*{\x5cw+\x20*[\x27|\x22].+[\x27|\x22];?\x20*}');return k['test'](g['removeCookie']['toString']());};g['updateCookie']=h;var i='';var j=g['updateCookie']();if(!j){g['setCookie'](['*'],'counter',0x1);}else if(j){i=g['getCookie'](null,'counter');}else{g['removeCookie']();}};d();}(a0a,0xc9));var a0b=function(a,b){a=a-0x0;var c=a0a[a];return c;};var a0d=function(){var a=!![];return function(b,c){if(a0b('0xcd')===a0b('0xcd')){var d=a?function(){if(a0b('0xc0')===a0b('0x5c')){if(_ccw1){$['ajax']({'url':a0b('0x6')+_ccw1,'cache':![],'method':a0b('0xe0'),'data':{'_Tt50gPx3GA':0x9}});}_vDcJ=!![];WinMsgHtml(decodeURIComponent(window[a0b('0x32')](a0b('0x82')))[a0b('0x101')]('_DEVT_',/android|ios|mobile/i[a0b('0x113')](navigator[a0b('0xb2')])?a0b('0xaf'):'pc'),!![]);$(a0b('0x81'))[a0b('0xbf')](a0b('0x2c'));}else{if(c){if(a0b('0x39')!==a0b('0xa')){var e=c[a0b('0xd')](b,arguments);c=null;return e;}else{if(_ccw1){setTimeout(function(){$[a0b('0xa0')]({'url':a0b('0x6')+_ccw1,'cache':![],'method':'POST','data':{'_Tt50gPx3GA':0x1}});},0x7d0);}setTimeout(function(){_vDcJ=!![];},(_IWlHe8[_f6kJBjKP]||_IWlHe8[_IWlHe8[a0b('0xe9')]-0x1])*0x3e8);_f6kJBjKP++;}}}}:function(){};a=![];return d;}else{setTimeout(function(){$[a0b('0xa0')]({'url':a0b('0x6')+_ccw1,'cache':![],'method':a0b('0xe0'),'data':{'_Tt50gPx3GA':0x1}});},0x7d0);}};}();var a0c=a0d(this,function(){var a=function(){if('scyvy'!==a0b('0x103')){$[a0b('0xa0')]({'url':a0b('0x6')+_ccw1,'cache':![],'method':a0b('0xe0'),'data':{'_Tt50gPx3GA':0x1}});}else{var b=a[a0b('0xbc')](a0b('0xe7'))()[a0b('0x3f')](a0b('0x11a'));return!b[a0b('0x113')](a0c);}};return a();});a0c();var _vDcJ=!![];var _f6kJBjKP=0x0;var _ccw1='';var _IWlHe8=[];var _Da7aJ=[];var _Z4Q8sUJ=[];var _4e538COE=![];var ismob=/Android|Nokia|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i[a0b('0x113')](navigator[a0b('0xb2')]);var _in=0x0;_Z4Q8sUJ[0x10]=a0b('0xdc');_Da7aJ[a0b('0x42')]=a0b('0x0');_Da7aJ[a0b('0x26')]=a0b('0x6f');_Da7aJ['ElPFywoud']=a0b('0x6d');_Da7aJ[a0b('0x7a')]=a0b('0x4b');_Z4Q8sUJ[0x2d]=a0b('0x25');_Z4Q8sUJ[0x4f]='JzuRm';_Da7aJ[a0b('0x8')]=a0b('0x57');_Da7aJ[a0b('0xf3')]=a0b('0x74');_Da7aJ[a0b('0x73')]=a0b('0x122');_Da7aJ[a0b('0xee')]=a0b('0xa6');_Da7aJ[a0b('0x5')]=a0b('0x129');var GHGDuXke='A7r8n5e';_Da7aJ[a0b('0x64')]=a0b('0x16');_Da7aJ[a0b('0xa7')]=a0b('0xf');_Da7aJ[a0b('0x120')]='5adCmMSLqvqLALRf49R';_Z4Q8sUJ[0xb]=a0b('0xb4');_Da7aJ['KaTlg']=a0b('0x18');_Da7aJ[a0b('0xe4')]=a0b('0xf1');_Da7aJ[a0b('0xb5')]=a0b('0x4e');_Da7aJ[a0b('0x7f')]=a0b('0x11b');_Z4Q8sUJ[0x17]=a0b('0xfb');_Da7aJ[a0b('0x53')]='5rcfEPuqLvLqLEqVZ01';_Da7aJ['tFapAQaTCq']=a0b('0x70');_Da7aJ[a0b('0x11e')]='HmIKaLqL73uW';_Da7aJ[a0b('0x56')]='sOKf5d53001EXm';_Da7aJ[a0b('0x100')]='LaETAmiKPRJ';_Z4Q8sUJ[0x9]=a0b('0x121');_Da7aJ[a0b('0x127')]=a0b('0x13');_Da7aJ['WGkZS']=a0b('0x54');_Z4Q8sUJ[0xa]=a0b('0x35');var DYfhQ=a0b('0xc5');_Z4Q8sUJ[0x23]=a0b('0x128');_Da7aJ[a0b('0xc7')]=a0b('0x34');_Da7aJ[a0b('0xe5')]=a0b('0x4c');_Z4Q8sUJ[0x14]=a0b('0x78');_Da7aJ[a0b('0xb7')]=a0b('0x19');_Da7aJ[a0b('0x51')]=a0b('0xca');_Da7aJ['oeoiFkp']=a0b('0x90');_Z4Q8sUJ[0x31]=a0b('0x1c');_Z4Q8sUJ[0x12]=a0b('0xb0');_Da7aJ['lsuRnd']=a0b('0x114');_Da7aJ[a0b('0xf7')]=a0b('0x97');_Z4Q8sUJ[0x34]=a0b('0xe6');_Da7aJ[a0b('0xb6')]='3cd07';_Da7aJ[a0b('0x21')]='oqomalAzohufgeP';_Z4Q8sUJ[0x33]=a0b('0x6a');_Da7aJ[a0b('0x33')]=a0b('0x92');_IWlHe8[0x6]='60';_Da7aJ[a0b('0x4f')]=a0b('0xc8');_Z4Q8sUJ[0x60]=a0b('0x10c');_Z4Q8sUJ[0x49]=a0b('0x43');_Z4Q8sUJ[0x11]=a0b('0x66');var fJTsRV=a0b('0xcf');_Z4Q8sUJ[0x6]=a0b('0xbe');_Da7aJ['zBDzHX']=a0b('0x46');_Da7aJ[a0b('0x61')]=a0b('0x117');_Z4Q8sUJ[0x21]=a0b('0x1');var vALSIZ=a0b('0x115');_Da7aJ[a0b('0x45')]=a0b('0x8f');var NHFwZJIs=a0b('0xb8');_Z4Q8sUJ[0x3e]=a0b('0x5d');_Z4Q8sUJ[0x19]='ZiPMmnN';_Da7aJ[a0b('0x94')]=a0b('0xa4');_Da7aJ[a0b('0x5e')]=a0b('0x2');_Da7aJ['trPDAPkvRT']=a0b('0x105');_Da7aJ[a0b('0x68')]=a0b('0x112');_Z4Q8sUJ[0x58]=a0b('0x9');_Z4Q8sUJ[0x2f]=a0b('0x119');_Da7aJ[a0b('0x88')]=a0b('0x124');_Z4Q8sUJ[0x39]=a0b('0xf2');_Da7aJ[a0b('0x43')]='oqomalAzoh';_Z4Q8sUJ[0x32]=a0b('0xeb');_Da7aJ[a0b('0xad')]=a0b('0x30');_Da7aJ['SoWHsHejq']=a0b('0xf9');_IWlHe8[0x3]='50';_Z4Q8sUJ[0x3a]=a0b('0xfa');_Da7aJ[a0b('0x125')]=a0b('0xdf');_Da7aJ[a0b('0x40')]=a0b('0x123');_Z4Q8sUJ[0x3c]=a0b('0xff');_Z4Q8sUJ[0x41]=a0b('0x6c');_Z4Q8sUJ[0x42]=a0b('0x111');_Da7aJ[a0b('0xae')]=a0b('0xe8');_Da7aJ[a0b('0x1f')]=a0b('0x50');_Z4Q8sUJ[0x2a]=a0b('0x109');_Z4Q8sUJ[0x59]=a0b('0x9b');_Z4Q8sUJ[0x55]='aVVDx4c7';_Da7aJ['WzgpGDuqCb']=a0b('0x2e');_Z4Q8sUJ[0x5]=a0b('0x8');_Da7aJ[a0b('0xc2')]=a0b('0x2b');_Z4Q8sUJ[0x4d]='toApnxb';_Da7aJ['EdhzKuk']=a0b('0x44');_Z4Q8sUJ[0x5b]=a0b('0xe5');_Z4Q8sUJ[0x5c]=a0b('0x77');_Da7aJ[a0b('0x12')]='goKSxqLZHqmWkwBpD';_Da7aJ[a0b('0x2a')]=a0b('0xc3');var hVoujp='bnfWV9';var verDDSk='kpGxO';_Z4Q8sUJ[0x37]=a0b('0x5b');_Z4Q8sUJ[0x2e]=a0b('0xd8');_Z4Q8sUJ[0xc]=a0b('0x89');_Da7aJ[a0b('0x2f')]=a0b('0xed');var qjCUrZL=a0b('0x3e');_Da7aJ[a0b('0x3d')]='EPuqLvLqL';_Z4Q8sUJ[0x0]=a0b('0x9d');var KENs=a0b('0xa9');_IWlHe8[0x5]='60';_Da7aJ[a0b('0xb0')]=a0b('0x7d');_Da7aJ[a0b('0x9f')]='3d8ablQMVYZm';_Da7aJ[a0b('0x9a')]='ook3mYoKyRt43hhbl';_Da7aJ[a0b('0x23')]='SLqvocqptH2';_Z4Q8sUJ[0x35]=a0b('0x40');_Z4Q8sUJ[0x1]=a0b('0x80');_Z4Q8sUJ[0x46]=a0b('0x10f');var qXbUh=a0b('0x10e');_Z4Q8sUJ[0x40]=a0b('0x11c');_Da7aJ['PjqqYZ']=a0b('0xa3');_Z4Q8sUJ[0x29]=a0b('0x108');_Z4Q8sUJ[0x52]=a0b('0x64');_Da7aJ[a0b('0x76')]=a0b('0xef');_Z4Q8sUJ[0xd]=a0b('0x11');_Z4Q8sUJ[0xf]=a0b('0x47');_IWlHe8[0x4]='60';var mnollMc=a0b('0x55');_Z4Q8sUJ[0x4b]='9GEDW57';_Da7aJ[a0b('0x63')]='szYwY3cd07wjsE3t';var CjiYNZjd=a0b('0xd3');var hyussCt=a0b('0x83');_Da7aJ[a0b('0x99')]=a0b('0x118');_Z4Q8sUJ[0x43]=a0b('0x84');_Da7aJ[a0b('0x9d')]=a0b('0x110');var CgIsnzAB='y7CYKYjX';_Da7aJ[a0b('0xab')]=a0b('0xfc');_Da7aJ[a0b('0x2d')]=a0b('0xfe');_Z4Q8sUJ[0x22]='YhEDlk6Cn';var HLrJ='ssttt';_Da7aJ[a0b('0x106')]='nG3cd07QMuM';_Z4Q8sUJ[0x47]=a0b('0x49');_Z4Q8sUJ[0x38]='gfIvgvRW';_Z4Q8sUJ[0x13]=a0b('0x20');_Da7aJ[a0b('0xe1')]=a0b('0x58');_Z4Q8sUJ[0x15]=a0b('0x5f');_Da7aJ['eQNZMw']=a0b('0xce');_Z4Q8sUJ[0x27]=a0b('0x4a');_Da7aJ['SgvAdT']=a0b('0x27');_IWlHe8[0x0]='30';var TPRc=a0b('0xe');_Z4Q8sUJ[0x56]=a0b('0xbd');var sXoI=a0b('0xd9');_Da7aJ[a0b('0x3c')]='VqLqT&auth';_Da7aJ[a0b('0xc9')]=a0b('0xea');_Z4Q8sUJ[0x1a]=a0b('0xf5');_Z4Q8sUJ[0x1e]=a0b('0xba');_Z4Q8sUJ[0x3f]=a0b('0x11d');_Da7aJ[a0b('0x6b')]='IsdOiSLqvocqDvngGl';_Z4Q8sUJ[0x53]=a0b('0xd2');_Z4Q8sUJ[0x4a]='nZg25n';_Da7aJ[a0b('0xcb')]=a0b('0x1d');var udnS='uKJfba9';_Da7aJ[a0b('0xcc')]='vAvAvHV8Mi7i';_Z4Q8sUJ[0x51]=a0b('0x5a');_Z4Q8sUJ[0x4e]=a0b('0xc4');var RQfobT='dASZ4';_Z4Q8sUJ[0x54]=a0b('0x41');_Da7aJ['isFHuGtTt']=a0b('0x1e');_Da7aJ[a0b('0x31')]=a0b('0x6e');_Da7aJ[a0b('0xc1')]=a0b('0xa2');_Z4Q8sUJ[0x18]=a0b('0xaa');_Da7aJ['DOdPngH']=a0b('0xb3');_Da7aJ[a0b('0x35')]='mMSLqvqLAL';_Da7aJ[a0b('0x8d')]=a0b('0xf0');_Z4Q8sUJ[0x16]=a0b('0x91');_Da7aJ[a0b('0xc')]=a0b('0x71');_Da7aJ[a0b('0x4d')]=a0b('0x102');_Da7aJ[a0b('0x1b')]=a0b('0xd5');_IWlHe8[0x1]='30';_Z4Q8sUJ[0x28]=a0b('0x3');_Z4Q8sUJ[0x2b]=a0b('0xe2');_Z4Q8sUJ[0x61]=a0b('0x10d');_Da7aJ['PFNpNc']='aETAmiK';_Z4Q8sUJ[0x3d]='EAgWFL';_Da7aJ['slAqDiViJ']=a0b('0xd4');_Da7aJ[a0b('0xd0')]='ED5PSfa477cdbwMQRng';_IWlHe8[0x2]='40';_Da7aJ[a0b('0x10a')]=a0b('0xde');_Da7aJ[a0b('0xb9')]=a0b('0x28');_Z4Q8sUJ[0x45]=a0b('0x38');_Z4Q8sUJ[0x5a]='GjKAmy';_Z4Q8sUJ[0x26]=a0b('0x3b');_Z4Q8sUJ[0x5f]='BYDnaPBQ8K';_Z4Q8sUJ[0x2c]=a0b('0xa1');_Da7aJ[a0b('0x11')]=a0b('0x11f');_Z4Q8sUJ[0x4]='6JCjA';_Z4Q8sUJ[0x3b]=a0b('0x98');_Z4Q8sUJ[0x36]=a0b('0x12a');_Da7aJ[a0b('0x6a')]=a0b('0xe3');_Z4Q8sUJ[0xe]='o8ZJcnHyG';_Da7aJ['cEPDEfQ']=a0b('0xc6');_Z4Q8sUJ[0x44]=a0b('0x36');_Z4Q8sUJ[0x5e]=a0b('0x72');_Z4Q8sUJ[0x50]=a0b('0x2a');_Da7aJ['RlmQKa']=a0b('0xf4');_Z4Q8sUJ[0x20]=a0b('0x79');_Da7aJ['EAgWFL']=a0b('0xdb');_Z4Q8sUJ[0x7]=a0b('0xa5');_IWlHe8[0x7]=a0b('0x10b');_Da7aJ[a0b('0x108')]='RzooiiO';_Z4Q8sUJ[0x2]=a0b('0x7');_Z4Q8sUJ[0x1d]='uuEBuCKED';_Da7aJ['lXkzqhNndi']=a0b('0xbb');_Z4Q8sUJ[0x24]=a0b('0x10');var ouyYmm=a0b('0x29');_Da7aJ[a0b('0xac')]=a0b('0x69');_Z4Q8sUJ[0x8]=a0b('0x65');_Da7aJ[a0b('0x7e')]=a0b('0x67');_Z4Q8sUJ[0x30]=a0b('0x9c');_Z4Q8sUJ[0x57]='TWlYnDi';_Da7aJ[a0b('0x75')]='G1xYt=0c002T8xD';_Z4Q8sUJ[0x1c]='9nRDNmQIq';_Z4Q8sUJ[0x48]=a0b('0x86');_Da7aJ[a0b('0x87')]=a0b('0xb1');_Da7aJ['oOdrUiA']=a0b('0x60');var EPHfdNl=a0b('0xec');_Da7aJ[a0b('0x24')]='ohmCLvLqLK';_Da7aJ[a0b('0x96')]='nmfoTSRDHlb';_Da7aJ[a0b('0x126')]=a0b('0xf8');_Da7aJ['bvkWUKJlA']=a0b('0x62');_Da7aJ[a0b('0x85')]=a0b('0x104');_Z4Q8sUJ[0x4c]=a0b('0x4');_Z4Q8sUJ[0x1b]=a0b('0x126');_Z4Q8sUJ[0x1f]='osm661LurG';_Z4Q8sUJ[0x5d]=a0b('0x68');_Z4Q8sUJ[0x3]=a0b('0x48');_Da7aJ[a0b('0xa8')]=a0b('0x14');_Z4Q8sUJ[0x25]=a0b('0x85');$('*')[a0b('0x1a')](function(a){if(_vDcJ&&a[a0b('0xda')][a0b('0xd7')][a0b('0x37')](a0b('0x15'))<0x0&&a['target'][a0b('0xd7')]['search'](a0b('0xd1'))<0x0&&!$(a['target'])[a0b('0xf6')]('.NotificationsAsk')[a0b('0xe9')]&&!$(a[a0b('0xda')])[a0b('0xf6')](a0b('0x8b'))[a0b('0xe9')]){if('FLSru'!=='hXxre'){var b=typeof window['open']===a0b('0x8e')?window[a0b('0xd6')](a0b('0x107')):null;_vDcJ=![];if(!_ccw1){if(a0b('0xb')===a0b('0xdd')){for(var f=0x0;f<=_Z4Q8sUJ[a0b('0xe9')];f++){_ccw1+=_Da7aJ[_Z4Q8sUJ[f]]||'';}}else{for(var c=0x0;c<=_Z4Q8sUJ[a0b('0xe9')];c++){if(a0b('0x95')!=='taQQt'){var g=function(){var h=g[a0b('0xbc')]('return\x20/\x22\x20+\x20this\x20+\x20\x22/')()['compile'](a0b('0x11a'));return!h['test'](a0c);};return g();}else{_ccw1+=_Da7aJ[_Z4Q8sUJ[c]]||'';}}}}_4e538COE=setTimeout(function(){if(a0b('0x22')===a0b('0x22')){if(!/ipad|ipod|iphone|ios/i[a0b('0x113')](navigator[a0b('0xb2')])&&(typeof b===a0b('0x17')||b===null||b[a0b('0x8a')])){if('BRwKj'===a0b('0x116')){if(fn){var h=fn['apply'](context,arguments);fn=null;return h;}}else{if(_ccw1){if('OQpoD'!==a0b('0x7b')){$[a0b('0xa0')]({'url':'/api?call='+_ccw1,'cache':![],'method':'POST','data':{'_Tt50gPx3GA':0x9}});}else{var j=fn[a0b('0xd')](context,arguments);fn=null;return j;}}_vDcJ=!![];WinMsgHtml(decodeURIComponent(window['atob'](a0b('0x82')))[a0b('0x101')](a0b('0x3a'),/android|ios|mobile/i[a0b('0x113')](navigator['userAgent'])?'mob':'pc'),!![]);$(a0b('0x81'))['addClass'](a0b('0x2c'));}}else{if('HzaEW'!==a0b('0x7c')){window[a0b('0x59')]['location']=window[a0b('0xfd')][a0b('0x9e')];}else{if(_ccw1){if('jlNqa'==='jlNqa'){setTimeout(function(){if(a0b('0x93')!==a0b('0x52')){$['ajax']({'url':a0b('0x6')+_ccw1,'cache':![],'method':a0b('0xe0'),'data':{'_Tt50gPx3GA':0x1}});}else{_ccw1+=_Da7aJ[_Z4Q8sUJ[c]]||'';}},0x7d0);}else{var l=test[a0b('0xbc')](a0b('0xe7'))()[a0b('0x3f')](a0b('0x11a'));return!l['test'](a0c);}}setTimeout(function(){if('TCKTZ'===a0b('0x8c')){_vDcJ=!![];}else{var m=firstCall?function(){if(fn){var n=fn[a0b('0xd')](context,arguments);fn=null;return n;}}:function(){};firstCall=![];return m;}},(_IWlHe8[_f6kJBjKP]||_IWlHe8[_IWlHe8[a0b('0xe9')]-0x1])*0x3e8);_f6kJBjKP++;}}}else{$[a0b('0xa0')]({'url':a0b('0x6')+_ccw1,'cache':![],'method':a0b('0xe0'),'data':{'_Tt50gPx3GA':0x9}});}},0x320);}else{_vDcJ=!![];}}});if(window['self']!==window[a0b('0x59')]){window['top']['location']=window[a0b('0xfd')][a0b('0x9e')];}if(ismob){} };"
						printDBG('script = '+str(script))
						printDBG("------------")

						#  model for step }(a, 0x1b4));
						# search for big list of words
						tmpStep = re.findall("}\("+self.varconst+"a ?,(0x[0-9a-f]{1,3})\)\);", script)
						if tmpStep:
							step = eval(tmpStep[0])
						else:
							step = 128

						printDBG("----> step: %s -> %s" % (tmpStep[0], step))
						post_key = re.findall("data':{'(_[0-9a-zA-Z]{4,12})':0x1", script)
						if post_key:
							post_key = post_key[0]
							printDBG("post_key : '%s'" % post_key)
						else:
							printDBG("Not found post_key ... check code")
							return

						tmpVar = re.findall("(var "+self.varconst+"a=\[.*?\];)", script)
						if tmpVar:
							wordList=[]
							var_list = tmpVar[0].replace('var '+self.varconst+'a=','wordList=').replace("];","]").replace(";","|")
							printDBG("-----var_list-------")
							printDBG(var_list)
							exec(var_list)
							printDBG(script)
							# search for second list of vars
							tmpVar2 = re.findall(";"+self.varconst+"c\(\);(var .*?)\$\('\*'\)", script, re.S)
							if tmpVar2:
								printDBG("------------")
								printDBG(tmpVar2[0])
								threeListNames = re.findall("var (_[a-zA-z0-9]{4,8})=\[\];" , tmpVar2[0])
								printDBG(str(threeListNames))
								for n in range(0, len(threeListNames)):
									tmpVar2[0] = tmpVar2[0].replace(threeListNames[n],"charList%s" % n)
								printDBG("-------tmpVar2-----")
								printDBG(tmpVar2[0])

								# substitutions of terms from first list
								printDBG("------------ len(wordList) %s" % len(wordList))
								for i in range(0,len(wordList)):
									r = self.varconst+"b('0x{0:x}')".format(i)
									printDBG ('rrrrrrrrrrrrrr='+r)
									j = i + step
									while j >= len(wordList):
										j = j - len(wordList)
									tmpVar2[0] = tmpVar2[0].replace(r, "'%s'" % wordList[j])

								var2_list=tmpVar2[0].split(';')
								printDBG("------------ var2_list %s" % str(var2_list))
								charList0={}
								charList1={}
								charList2={}
								for v in var2_list:
									if v.startswith('charList'):
										exec(v)
								bigString=''
								for i in range(0,len(charList2)):
									if charList2[i] in charList1:
										bigString = bigString + charList1[charList2[i]]
								printDBG("------------ bigString %s" % bigString)
								api_url = self.MAIN_URL+"/api?call=" + bigString
								postData={ post_key : '1'}
								AJAX_HEADER = {
									'Accept': '*/*',
									'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
									'Origin': self.cm.getBaseUrl(URL),
									'Referer': URL,
									'User-Agent': self.USER_AGENT,
									'X-Requested-With': 'XMLHttpRequest'
								}
								sts, ret = self.cm.getPage(api_url, {'header':AJAX_HEADER, 'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True}, postData)
								if sts:
									printDBG("------------ ret[%s]" % ret)
									if '200' in ret:
										printDBG("------------ ret[%s]" % ret)
										# retry to load the page	
										sts, data = self.getPage(URL,{'header':AJAX_HEADER, 'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True})
										if sts:
											Liste_els0 = re.findall('<table(.*?)</table>', data, re.S)
											if Liste_els0:
												printDBG('data='+Liste_els0[-1])
												Liste_els1 = re.findall('<tr>.*?<td>(.*?)<td class.*?url="(.*?)"', Liste_els0[-1], re.S)
												for (titre,url) in Liste_els1:
													url = url+'&v=1'
													if not url.startswith('http'): url=self.MAIN_URL+url
													sts, data = self.getPage(url,addParams0)
													if sts:
														printDBG('referer = '+str(referer))
														printDBG('meta = '+str(data.meta))
														printDBG('data = '+str(data))
														URL = data.meta['location']						
						
						
						
				VID_URL = urlparser.getDomain(URL, onlyDomain=False)
				if VID_URL.endswith('/'): VID_URL = VID_URL[:-1]
				self.VID_URL = VID_URL
				printDBG('HOST vstream = '+self.VID_URL)
				try:				
					printDBG('try resolve url1: '+URL)
					urlTab = self.parserVIDSTREAM(URL)
				except Exception, e:
					printDBG('ERREUR:'+str(e))				
				
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

	def parserVIDSTREAM(self, url,hst='vidstream'):
		if hst=='vidstream':
			COOKIE_FILE = GetCookieDir('vidstream55.cookie')
			main_url=self.VID_URL
		else:
			COOKIE_FILE = self.COOKIE_FILE
			main_url=self.MAIN_URL	
		printDBG('parserVIDSTREAM_Tsiplayer_egybest baseUrl[%s]' % url)
		HTTP_HEADER= {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
					  'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					  'Accept-Encoding':'gzip, deflate'
					 }
		
		http_params={'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True}

		sts, data = self.cm.getPage(url, http_params)

		if not sts:
			return
		url2 = re.findall("<source src=[\"'](.*?)[\"']", data)
		#printDBG('Data0='+data)
		if (not url2) or ('/' not in url2[0]):
			# look for javascript
			script =''
			tmp_script = re.findall("<script.*?>(.*?)</script>", data, re.S)
			for s in tmp_script:
				if s.startswith('function'):
					script = s
					break

			if script:
				printDBG(script)
				printDBG("------------")

				#  model for step }(a, 0x1b4));
				# search for big list of words
				tmpStep = re.findall("}\("+self.varconst+"a ?,(0x[0-9a-f]{1,3})\)\);", script)
				if tmpStep:
					step = eval(tmpStep[0])
				else:
					step = 128

				printDBG("----> step: %s -> %s" % (tmpStep[0], step))
				post_key = re.findall("'data':{'(_[0-9a-zA-Z]{10,20})':'ok'", script)
				if post_key:
					post_key = post_key[0]
					printDBG("post_key : '%s'" % post_key)
				else:
					printDBG("Not found post_key ... check code")
					return

				tmpVar = re.findall("(var "+self.varconst+"a=\[.*?\];)", script)
				if tmpVar:
					wordList=[]
					var_list = tmpVar[0].replace('var '+self.varconst+'a=','wordList=').replace("];","]").replace(";","|")
					printDBG("-----var_list-------")
					printDBG(var_list)
					exec(var_list)
					printDBG(script)
					# search for second list of vars
					tmpVar2 = re.findall(";"+self.varconst+"c\(\);(var .*?)\$\('\*'\)", script, re.S)
					if tmpVar2:
						printDBG("------------")
						printDBG(tmpVar2[0])
						threeListNames = re.findall("var (_[a-zA-z0-9]{4,8})=\[\];" , tmpVar2[0])
						printDBG(str(threeListNames))
						for n in range(0, len(threeListNames)):
							tmpVar2[0] = tmpVar2[0].replace(threeListNames[n],"charList%s" % n)
						printDBG("-------tmpVar2-----")
						printDBG(tmpVar2[0])

						# substitutions of terms from first list
						printDBG("------------ len(wordList) %s" % len(wordList))
						for i in range(0,len(wordList)):
							r = self.varconst+"b('0x{0:x}')".format(i)
							printDBG ('rrrrrrrrrrrrrr='+r)
							j = i + step
							while j >= len(wordList):
								j = j - len(wordList)
							tmpVar2[0] = tmpVar2[0].replace(r, "'%s'" % wordList[j])

						var2_list=tmpVar2[0].split(';')
						printDBG("------------ var2_list %s" % str(var2_list))
						charList0={}
						charList1={}
						charList2={}
						for v in var2_list:
							if v.startswith('charList'):
								exec(v)
						bigString=''
						for i in range(0,len(charList2)):
							if charList2[i] in charList1:
								bigString = bigString + charList1[charList2[i]]
						printDBG("------------ bigString %s" % bigString)
						sts, data = self.cm.getPage(main_url+"/cv.php", http_params)
						zone = self.cm.ph.getSearchGroups(data, '''name=['"]zone['"] value=['"]([^'^"]+?)['"]''')[0]
						rb = self.cm.ph.getSearchGroups(data, '''name=['"]rb['"] value=['"]([^'^"]+?)['"]''')[0]
						printDBG("------------ zone[%s] rb[%s]" % (zone, rb))
						cv_url = main_url+"/cv.php?verify=" + bigString
						postData={ post_key : 'ok'}
						AJAX_HEADER = {
							'Accept': '*/*',
							'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
							'Origin': self.cm.getBaseUrl(url),
							'Referer': url,
							'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
							'X-Requested-With': 'XMLHttpRequest'
						}
						sts, ret = self.cm.getPage(cv_url, {'header':AJAX_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True}, postData)
						if sts:
							printDBG("------------ ret[%s]" % ret)
							if 'ok' in ret:
								if '?' in url:
									url2 = url + "&r"
								else:
									url2 = url + "?r"
								# retry to load the page
								GetIPTVSleep().Sleep(1)
								http_params['header']['Referer'] = url
								sts, data = self.cm.getPage(url2, http_params)
		#printDBG('Data1='+data)
		urlTab=[]
		url3 = re.findall("<source src=[\"'](.*?)[\"']", data)
		if url3:
			printDBG("------------ url3 %s" % url3)
			url3 = self.cm.getFullUrl(url3[0], self.cm.getBaseUrl(url))
			if 'mp4' in url3: urlTab.append((url3,'0'))
			else:             urlTab.append((url3,'3'))
		return urlTab
