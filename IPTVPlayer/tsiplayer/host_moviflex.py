# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
###################################################


import re
import base64

def getinfo():
	info_={}
	info_['name']='Moviflex.Net'
	info_['version']='1.2 17/08/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات اجنبية'
	info_['icon']='https://cdn.moviflex.net/wp-content/uploads/2017/10/zymzJNA_22bcf2779f586340b970a361a8648be9.png'
	info_['recherche_all']='0'
	info_['update']='Bugs Fix'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'moviflex.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.moviflex.net'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.HEADER1 = {'User-Agent': self.USER_AGENT,'Accept':'*/*', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.defaultParams1 = {'header':self.HEADER1, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']
		self.addMarker({'title':tscolor('\c00????00')+'أفلام','category' : 'host2','icon':img_} )									
		Cat_TAB = [
					{'category':hst,'title': 'الكل', 'mode':'30','url':'https://www.moviflex.net/movies/'},
					{'category':hst,'title': 'الأكتر مشاهدة هذا الأسبوع', 'mode':'30','url':'https://www.moviflex.net/trending/?get=movies'},
					{'category':hst,'title': 'تصنيف', 'mode':'20','sub_mode':0},
					{'category':hst,'title':'سنة الإصدار', 'mode':'20','sub_mode':1},

					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})	
		self.addMarker({'title':tscolor('\c00????00')+'مسلسلات','category' : 'host2','icon':img_} )	
		Cat_TAB = [
					{'category':hst,'title': 'الكل', 'mode':'30','url':'https://www.moviflex.net/tvshows/'},
					{'category':hst,'title': 'الأكتر مشاهدة هذا الأسبوع',  'mode':'30','url':'https://www.moviflex.net/trending/?get=tv'},

					{'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})			


	def showmenu1(self,cItem):
		gnr=cItem['sub_mode']
		sts, data = self.getPage(self.MAIN_URL)
		if sts:
			if gnr==0:
				pat='<ul class="sub-menu">(.*?)</ul>'
			else:
				pat='<ul class="releases(.*?)</ul>'
			films_list = re.findall(pat, data, re.S)
			if films_list:
				films_list2 = re.findall('<li.*?href="(.*?)">(.*?)<', films_list[0], re.S)	
				for (url,titre) in films_list2:
					self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
			
		
		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		if '?' in url1:
			x1,x2=url1.split('?',1)
			url1=x1+'page/'+str(page)+'/?'+x2
		else:
			url1=url1+'page/'+str(page)+'/'
		sts, data = self.getPage(url1)
		if sts:
			films_list = re.findall('<article id="post.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?rating">(.*?)</div>.*?data">.*?<span>(.*?)</span>', data, re.S)		
			for (url,image,titre,rate,desc) in films_list:
				desc='Rating: '+tscolor('\c00????00')+ph.clean_html(rate)+tscolor('\c00??????')+'\\nDate: '+tscolor('\c00????00')+ph.clean_html(desc)
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':ph.clean_html(titre),'desc':desc,'icon':image,'hst':'tshost','mode':'31'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':image,'mode':'30'} )									

	def showelms(self,cItem):
		urlo=cItem['url']
		img_=cItem['icon']
		sts, data = self.getPage(urlo)
		if sts:
			films_list = re.findall('class="se-q">.*?title">(.*?)<div.*?<ul(.*?)</ul>', data, re.S)
			if films_list:
				for elm in films_list:
					self.addMarker({'title':tscolor('\c00????00')+ph.clean_html(elm[0]),'category' : 'host2','icon':img_} )
					films_list1 = re.findall('<li>.*?href="(.*?)".*?src="(.*?)".*?numerando">(.*?)<', elm[1], re.S)				
					for (url,image,titre) in films_list1:
						self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':ph.clean_html(titre),'desc':cItem['desc'],'icon':image,'hst':'tshost'} )
			else:
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': urlo,'title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'} )
			
	
	def SearchResult(self,str_ch,page,extra):
		url_='https://www.moviflex.net/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('class="result-item.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)"', data, re.S)		
			for (url,image,titre) in films_list:
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':'','icon':image,'hst':'tshost','mode':'31'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL,self.defaultParams)
		if sts:
			Tab_els = re.findall('src="(https://www.youtube.*?)"', data, re.S)
			if Tab_els:
				urlTab.append({'name':'TRAILER', 'url':Tab_els[0], 'need_resolve':1})
			Tab_els = re.findall('play-box-iframe.*?data-src="(.*?)".*?></iframe>', data, re.S)
			for url in Tab_els:
				try:
					if '//moviflex.net' in url:
						sts, data = self.getPage(url,self.defaultParams)
						url_els = re.findall('<source src="(.*?)"', data, re.S)
						if url_els:
							urlTab.append({'name':'Moviflex', 'url':url_els[0], 'need_resolve':0,'type':'local'})
					elif 'moviflex.ml' in url:
						post_data = {'r':'','d':'moviflex.ml'}
						url=url.replace('/v/','/api/source/')
						sts, data = self.getPage(url,self.defaultParams, post_data)
						data = json_loads(data)
						elmdata = data['data']
						for elm0 in elmdata:
							urlTab.append({'name':'|'+elm0['label']+'| Moviflex' , 'url':elm0['file'], 'need_resolve':0,'type':'local'})				
					elif '.moviflex.pw' in url:
						paramsUrl = dict(self.defaultParams1)
						paramsUrl['header']['Referer'] = URL
						sts, data = self.getPage(url,paramsUrl)
						url_els = re.findall('JuicyCodes.Run\((.*?)\)', data, re.S)
						if url_els:
							b64data=url_els[0]	
							b64data=b64data.replace('"+"','')	.replace('"','')	
							script_data=base64.b64decode(b64data)
							script_ = unpackJSPlayerParams(script_data, SAWLIVETV_decryptPlayerParams, 0)
							url_els = re.findall('file":"(.*?)".*?label":"(.*?)"', script_, re.S)
							for (url_,titre_) in url_els:	
								urlTab.append({'name':'|'+titre_+'| Moviflex' , 'url':strwithmeta(url_, {'Referer':url}), 'need_resolve':0,'type':'local'})				
					else:	
						if len(url)>4:
							url11 = url.split('https://')
							url='https://' + url11[-1]
							urlTab.append({'name':gethostname(url), 'url':url, 'need_resolve':1})
				except:
					a=''						
		return urlTab
		
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc= cItem.get('desc','')	
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat2=re.findall('class="costum_info">(.*?)(valor">|tag">)(.*?)</div>', data, re.S)
			if lst_dat2:
				for (x1,x0,x2) in lst_dat2:
					if 'اشراف' in x1: otherInfo1['age_limit'] = ph.clean_html(x2)
					if 'بلد'  in x1: otherInfo1['country'] = ph.clean_html(x2)
					if 'مدة'  in x1: otherInfo1['duration'] = ph.clean_html(x2)				
					if 'تاريخ' in x1: otherInfo1['year'] = ph.clean_html(x2)						
					if 'sgeneros'  in x1: otherInfo1['genres'] = ph.clean_html(x2)					
			else:
				lst_dat2=re.findall('class="sgeneros">(.*?)<div', data , re.S)
				if lst_dat2:
					otherInfo1['genres'] = ph.clean_html(lst_dat2[0])			
			
			
				
			lst_dat2=re.findall('wp-content">(.*?)<div', data , re.S)
			if lst_dat2:
				desc=ph.clean_html(lst_dat2[0])
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
		if mode=='31':
			self.showelms(cItem)
			
