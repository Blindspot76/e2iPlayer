# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re

def getinfo():
	info_={}
	info_['name']='Shahid4u'
	info_['version']='1.3 28/10/2019'
	info_['dev']='Opesboy'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات عربية و اجنبية'
	info_['icon']='https://ww.shahid4u.net/themes/Shahid4u/img/logo.png'
	info_['recherche_all']='1'
	info_['update']='change to ww.shahid4u.net'	

	return info_
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'shahid4u.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://ww.shahid4u.net'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		hst='host2'
		self.Arablionz_TAB = [
							{'category':hst,               'title': tscolor('\c00????00')+'By Filter', 'mode':'20','count':1,'data':'none','code':self.MAIN_URL+'/getposts?'},
							{'category':hst, 'sub_mode':'film', 'title': 'Films',                  'mode':'21'},
							{'category':hst, 'sub_mode':'serie','title': 'Series',                 'mode':'21'},
							#{'category':hst, 'sub_mode':'music','title': 'اغاني وكليبات',          'mode':'21'},							
							#{'category':hst, 'sub_mode':'other','title': 'برامج تليفزيونية',       'mode':'30','url':self.MAIN_URL+'/category/%D8%A8%D8%B1%D8%A7%D9%85%D8%AC-%D8%AA%D9%84%D9%8A%D9%81%D8%B2%D9%8A%D9%88%D9%86%D9%8A%D8%A9/','page':1},
							#{'category':hst, 'sub_mode':'other','title': 'رياضة و مصارعه',         'mode':'30','url':self.MAIN_URL+'/category/%D8%B9%D8%B1%D9%88%D8%B6-%D8%A7%D9%84%D9%85%D8%B5%D8%A7%D8%B1%D8%B9%D8%A9/','page':1},
							{'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
							]		
		self.listsTab(self.Arablionz_TAB, {'import':cItem['import'],'icon':cItem['icon']})	

	def showmenu1(self,cItem):
		count=cItem['count']
		data1=cItem['data']	
		codeold=cItem['code']	
		if count==1:
			sts, data = self.getPage(self.MAIN_URL)
			if sts:
				data1=re.findall('dropdown select-menu">.*?<ul(.*?)</ul>', data, re.S)
			else:
				data1='' 
		if count==4:
			mode_='30' 
		else:
			mode_='20'
		lst_data1 = re.findall('<li.*?data-tax="(.*?)".*?data-cat="(.*?)".*?bold">(.*?)<',data1[count-1], re.S)	
		for (x1,x2,x3) in lst_data1:
			code=codeold+x1+'='+x2+'&'
			self.addDir({'import':cItem['import'],'category' :'host2', 'url':code, 'title':x3, 'desc':x1, 'icon':cItem['icon'], 'mode':mode_,'count':count+1,'data':data1,'code':code, 'sub_mode':'item_filter','page':-1})					

	def showmenu2(self,cItem):		
		gnr=cItem['sub_mode']
		img_=cItem['icon']
		if gnr=='film': 
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/cat/%D8%A7%D9%81%D9%84%D8%A7%D9%85','title':'أفلام','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A','title':'افلام اجنبي','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%B9%D8%B1%D8%A8%D9%8A','title':'أفلام عربية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%87%D9%86%D8%AF%D9%8A','title':'افلام هندي','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
					
		elif gnr=='serie':
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/cat/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA','title':'مسلسلات','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'} )		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A','title':'مسلسلات اجنبية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%B9%D8%B1%D8%A8%D9%8A','title':'مسلسلات عربية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%AA%D8%B1%D9%83%D9%8A%D8%A9','title':'مسلسلات تركية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D9%87%D9%86%D8%AF%D9%8A%D8%A9','title':'مسلسلات هندية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		


		
	def showitms(self,cItem):
		gnr=cItem['sub_mode']
		url=cItem['url']
		titre=cItem['title']
		img_=cItem['icon']
		if gnr=='items':
			sts, data = self.getPage(url)
			if sts:
				desc=''
				desc_data=re.findall('<p>(.*?)</p>', data, re.S)
				if desc_data:
					desc='#'+desc_data[0].replace('&quot;','')+'#'
				info_data=re.findall('info-item\">.*?<span>(.*?)</span>.*?\">(.*?)<', data, re.S)
				itm_=''
				for (itm_n,itm_d) in info_data:
					itm_=itm_+' | ' + itm_n+itm_d		
				desc='#'+itm_+'#'+'\n'+'|'+'\n'+desc 
				cat_data=re.findall('<div class="row gutter-small">(.*?)</div>', data, re.S)		
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':titre,'desc':desc,'icon':img_,'hst':'tshost'} )
				if cat_data:
					data1=cat_data[0]
					cat_data=re.findall('<a href="(.*?)".*?<span>(.*?)</span></h3>', data1, re.S)
					if cat_data:
						self.addMarker({'title':tscolor('\c00????00')+'حلقات اخرة','desc':''})
					for(url_,titre_) in cat_data:
						titre_=titre_.replace('\n',' ')	
						if titre_=='':
							titre_data=re.findall('الحلقة-(.*?)-', url_, re.S)
							if titre_data:
								titre_=titre_data[0]+' ?'
							else:
								titre_data=re.findall('الحلقة-(.*)', url_, re.S)
								if titre_data:
									titre_=titre_data[0]+' !'								
						if '/season/' not in url_:
							self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url_,'title':'E'+titre_,'desc':url_,'icon':img_,'hst':'tshost'})	
		elif gnr=='item_filter':
			sts, data = self.getPage(url)	
			if sts:	 
				cat_data=re.findall('content-box">.*?href="(.*?)".*?data-src="(.*?)".*?<h3>(.*?)<', data, re.S)
				for (url1,image,name_eng) in cat_data:
					self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url1,'title':name_eng,'desc':'','icon':image,'sub_mode':'items','mode':'30'})			
		else: 
			page=cItem['page']
			sUrl=url+'?page='+str(page)
			sts, data = self.getPage(sUrl)
			if sts:		 
				cat_data=re.findall('<div class="row">(.*?)class="pagination">', data, re.S)
				if cat_data:
					data=cat_data[0]
					cat_data=re.findall('src="(.*?)".*?href="(.*?)".*?">(.*?)<.*?<h3>(.*?)<', data, re.S)
					for (image,url1,desc,name_eng) in cat_data:
						self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':False,'hst':'tshost','category' : 'host2','url': url1,'title':name_eng,'desc':desc,'icon':image,'sub_mode':'items','mode':'30'})			
					self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':'Next Page','page':page+1,'desc':'Next Page','icon':img_,'sub_mode':gnr,'mode':'30'} )	
	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/search?s='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:		
			cat_data=re.findall('<div class="row">(.*?)("pagination">|main-footer">)', data, re.S)
			if cat_data:
				data=cat_data[0][0]
				cat_data=re.findall('content-box">.*?href="(.*?)".*?data-src="(.*?)".*?<h3>(.*?)<', data, re.S)
				for (url1,image,name_eng) in cat_data:
					self.addDir({'import':extra,'good_for_fav':True,'EPG':False,'hst':'tshost','category' : 'host2','url': url1,'title':name_eng,'desc':'','icon':image,'sub_mode':'items','mode':'30'})							
		
		
	def get_links(self,cItem): 	
		urlTab = []	
		url_origin=cItem['url']
		URL=url_origin.replace('/episode/','/watch/')
		URL=URL.replace('/film/','/watch/')
		URL=URL.replace('/post/','/watch/')
		sts, data = self.getPage(URL)
		if sts:
			server_data = re.findall('<ul class="servers-list">(.*?)</ul>', data, re.S)
			if server_data:
				code_data = re.findall('<li.*?data-order="(.*?)" data-embedd="(.*?)".*?server_image">(.*?)<', server_data[0], re.S)
				id_data = re.findall("attr\('data-embedd'\).*?url: \"(.*?)\"", data, re.S)
				if (id_data and code_data):
					for (x1,code_,titre_) in code_data:
						url=id_data[0]+'&serverid='+code_
						urlTab.append({'name':titre_.strip(), 'url':'hst#tshost#'+url, 'need_resolve':1})
				else:
					server_data = re.findall('<li.*?data-embedd="(.*?)"', server_data[0], re.S)
					if server_data:
						for (url) in server_data:
							hostUrl=url.replace("www.", "")				
							raw1 =  re.findall('//(.*?)/', hostUrl, re.S)				
							hostUrl=raw1[0]
							urlTab.append({'name':hostUrl, 'url':url, 'need_resolve':1})



		URL=url_origin.replace('/episode/','/download/')
		URL=URL.replace('/film/','/download/')
		URL=URL.replace('/post/','/download/')
		sts, data = self.getPage(URL)
		if sts:
			server_data = re.findall('postId:"(.*?)"', data, re.S)
			if server_data:
				url_=self.MAIN_URL+'/ajaxCenter?_action=getdownloadlinks&postId='+server_data[0]
				HTTP_HEADER= {'X-Requested-With':'XMLHttpRequest','Referer':url_origin}
				sts, data_ = self.getPage(url_,{'header':HTTP_HEADER})
				server_data = re.findall('<a href="(.*?)"', data_, re.S)
				for (url_1) in server_data:
					hostUrl=url_1.replace("www.", "")				
					raw1 =  re.findall('//(.*?)/', hostUrl, re.S)
					if raw1:				
						hostUrl=raw1[0]
					if ('openload' in hostUrl.lower())or('uptobox' in hostUrl.lower()):
						urlTab.append({'name':hostUrl+' - سرفر تحميل', 'url':url_1, 'need_resolve':1})
			else:
				#code_data = re.findall('class="" data-order="(.*?)" data-embedd="(.*?)">.*?alt="(.*?)"', data, re.S)
				code_data = re.findall('data-embedd="(.*?)".*?alt="(.*?)"', data, re.S)
				
				id_data = re.findall("attr\('data-embedd'\).*?url: \"(.*?)\"", data, re.S)
				if id_data:
					for (code_,titre_) in code_data:
						url=id_data[0]+'&serverid='+code_
						urlTab.append({'name':titre_, 'url':'hst#tshost#'+url, 'need_resolve':1})		
		return urlTab
		 
	def getVideos(self,videoUrl):
		urlTab = []	
		HTTP_HEADER= { 'X-Requested-With':'XMLHttpRequest' }
		sts, data = self.getPage(videoUrl,{'header':HTTP_HEADER})
		if sts:
			_data2 = re.findall('<iframe.*?(src|SRC)=(.*?) ',data, re.S) 
			if _data2:
				URL_=_data2[0][1]
				URL_=URL_.replace('"','')
				URL_=URL_.replace("'",'')
				if URL_.startswith('//'):
					URL_='http:'+URL_ 
				urlTab.append((URL_,'1'))
			else:
				data=data.strip()
				if data.startswith('http'):
					urlTab.append((data,'1'))					
		return urlTab
		
	def getArticle(self, cItem):
		printDBG("Arablionz.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc = cItem['desc']
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('<div class="info-bar">(.*?)class="btns col-12 col-m-4 col-l-3">', data, re.S)
			elm=lst_dat[0].split('<div class="info-bar">')
			for (xx) in elm:
				lst_dat0=re.findall("<span>(.*?)</span>(.*?)</div>", xx.replace('</a></div>','</a>'), re.S)
				for (x1,x2) in lst_dat0:
					if 'الجودة' in x1: otherInfo1['quality'] = ph.clean_html(x2)
					if 'السنة' in x1: otherInfo1['year'] = ph.clean_html(x2)
					if 'النوع' in x1: otherInfo1['genres'] = ph.clean_html(x2)			
					if 'ممثلين' in x1: otherInfo1['actors'] = ph.clean_html(x2)
					if 'القسم' in x1: otherInfo1['category'] = ph.clean_html(x2)
					if 'مخرج' in x1: otherInfo1['director'] = ph.clean_html(x2)			
					if 'لمؤلف' in x1: otherInfo1['writer'] = ph.clean_html(x2)

					

				
			lst_dat0=re.findall('class="row no-gutter">.*?<p>(.*?)</p>', data, re.S)
			if lst_dat0: desc = ph.clean_html(lst_dat0[0])
			else: desc = cItem['desc']
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
			self.showitms(cItem)			


