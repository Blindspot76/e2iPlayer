# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Components.config import config
###################################################


import re
import base64

def getinfo():
	info_={}
	info_['name']='Dardarkom.Tv'
	info_['version']='1.0 01/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='102'
	info_['desc']='أفلام و مسلسلات عربية و اجنبية'
	info_['icon']='https://i.ibb.co/1rp9DNF/logo.png'
	info_['recherche_all']='1'
	info_['update']='New Host'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'dardarkom.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.dardarkom.tv'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.HEADER1 = {'User-Agent': self.USER_AGENT,'Accept':'*/*', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.defaultParams1 = {'header':self.HEADER1, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'أفلام',  'mode':'20','sub_mode':0},
					{'category':hst,'title': 'مسلسلات', 'mode':'20','sub_mode':1},					
					{'category':hst,'title': 'مصارعة', 'mode':'30','url':self.MAIN_URL+'/wwe/'},			
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})	
		
	def showmenu1(self,cItem):
		gnr=cItem['sub_mode']
		if gnr==0:
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/aflamonline/','title':'جميع الأفلام','desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
			self.addMarker({'title':tscolor('\c0000??00')+'أنواع الافلام','desc':'','icon':cItem['icon']})
			sts, data = self.getPage(self.MAIN_URL)
			if sts:
				films_list = re.findall('class="hm-col">(.*?)</ul', data, re.S)		
				for data1 in films_list:
					films_list1 = re.findall('<li>.*?href="(.*?)".*?title.*?">(.*?)<', data1, re.S)
					for (url,titre) in films_list1:
						self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
			self.addMarker({'title':tscolor('\c0000??00')+'تصنيفات الافلام','desc':'','icon':cItem['icon']})
			sts, data = self.getPage(self.MAIN_URL, {'header':{'User-Agent': 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16', 'Accept': 'text/html'}})
			if sts:
				films_list = re.findall('class="collection">(.*?)</ul', data, re.S)	
				if films_list:
					films_list1 = re.findall('class="collection">(.*?)</ul', data, re.S)
					if films_list1:
						films_list2 = re.findall('<li.*?href="(.*?)".*?title.*?">(.*?)<', films_list1[1], re.S)
						for (url,titre) in films_list2:
							self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
		if gnr==1:
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/series-online/latest-series/','title':'اخر المسلسلات','desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
			self.addMarker({'title':tscolor('\c0000??00')+'حسب التصنيف','desc':'','icon':cItem['icon']})
			sts, data = self.getPage(self.MAIN_URL)
			if sts:
				films_list = re.findall('class="ft-col">(.*?)</ul', data, re.S)		
				if films_list:
					films_list1 = re.findall('<li>.*?href="(.*?)".*?title.*?">(.*?)<', films_list[1], re.S)
					for (url,titre) in films_list1:
						self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	

			

	def showitms(self,cItem):
		url1=cItem['url']
		
		page=cItem.get('page',1)
		url1=url1+'page/'+str(page)+'/'
		sts, data = self.getPage(url1)
		if sts:
			data0  = re.findall('<head>(.*?)class="randseries"', data, re.S)	
			if data0: data=data0[0]
			films_list = re.findall('<div class="short">.*?href="(.*?)".*?src="(.*?)".*?title">(.*?)<', data, re.S)		
			for (url,image,titre) in films_list:
				titre=titre.replace('مشاهدة فيلم','')
				image=self.MAIN_URL+image
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':ph.clean_html(titre),'desc':'','icon':image,'hst':'tshost','mode':'31'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	def showelms(self,cItem):
		urlo=cItem['url']
		img_=cItem['icon']
		sts, data = self.getPage(urlo)
		if sts:
			films_list0 = re.findall('(youtube.com/embed/.*?)["\']', data, re.S)
			if films_list0:
				self.addVideo({'import':cItem['import'],'category' : 'host2','url': 'https://www.'+films_list0[0],'title':'إعلان ولقطات من الفيلم','desc':cItem['desc'],'icon':img_,'hst':'none'} )				
			films_list = re.findall('class="fmain aboveposbut.*?href="(.*?)"', data, re.S)
			if films_list:
				url2=films_list[0]
				sts, data2 = self.getPage(url2)
				if sts:
					films_list2 = re.findall('class="insidelinks">(.*?)</ul>', data2, re.S)				
					if films_list2:
						films_list3 = re.findall('<a.*?href="(.*?)".*?">(.*?)</a>', films_list2[0], re.S)
						for (url1,titre1) in films_list3:
							self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url1,'title':ph.clean_html(titre1),'desc':cItem['desc'],'icon':img_,'hst':'tshost'} )				
			else:
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': urlo,'title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'} )
			
	
	def SearchResult(self,str_ch,page,extra):
		url_='https://www.dardarkom.tv/index.php?do=search'
		post_data = {'do':'search','subaction':'search','search_start':page,'full_search':0,'result_from':((page-1)*20)+1,'story':str_ch}
		sts, data = self.getPage(url_, post_data=post_data)
		if sts:
			films_list = re.findall('sres-wrap clearfix".*?href="(.*?)".*?src="(.*?)".*?title="(.*?)".*?sres-desc">(.*?)<', data, re.S)
			for (url,image,titre,desc) in films_list:
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'hst':'tshost','mode':'31'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			Tab_els = re.findall('<iframe.*?src="(.*?)"', data, re.S)
			i=0
			for url in Tab_els:
				if url.startswith('//'): url='http:'+url
				if ('youtube' not in url) and ('/templates/' not in url):
					i=i+1
					if 'darkom.video' in url:
						if not config.plugins.iptvplayer.ts_dsn.value:
							urlTab.append({'name':'Server: '+str(i), 'url':'hst#tshost#'+url, 'need_resolve':1})
						else:
							url=self.extract_link(url)
							if url!='': urlTab.append({'name':gethostname(url), 'url':url, 'need_resolve':1})							
					else:
						urlTab.append({'name':gethostname(url), 'url':url, 'need_resolve':1})
						
			films_list2 = re.findall('class="insidelinks">(.*?)</ul>', data, re.S)				
			if films_list2:
				films_list3 = re.findall('<a.*?href="(.*?)".*?">(.*?)</a>', films_list2[0], re.S)
				for (url1,titre1) in films_list3:
					titre1=titre1.replace('شاهد على المشغل','Server: ')
					if 'darkom.video' in url1:
						if not config.plugins.iptvplayer.ts_dsn.value:
							urlTab.append({'name':ph.clean_html(titre1), 'url':'hst#tshost#'+url1, 'need_resolve':1})
						else:
							url1=self.extract_link(url1)
							if url1!='': urlTab.append({'name':gethostname(url1), 'url':url1, 'need_resolve':1})
					else:
						urlTab.append({'name':ph.clean_html(titre1), 'url':url1, 'need_resolve':1})
		return urlTab
	def extract_link(self,videoUrl):
		url=''
		sts, data = self.getPage(videoUrl)
		if sts:
			Liste_els = re.findall('<iframe.*?src=["\'](.*?)["\']', data, re.S)
			if 	Liste_els:
				url = Liste_els[0]
				if 'piclame' in url:
					sts, data = self.getPage(url)
					if sts:
						Liste_els = re.findall('name="description.*?content=["\'](.*?)["\']', data, re.S)		
						if Liste_els:
							url = Liste_els[0]
			else:
				Liste_els = re.findall('window.open\(["\'](.*?)["\']', data, re.S)
				if 	Liste_els:
					url = Liste_els[0]															
		return url
		
		
		
	def getVideos(self,videoUrl):
		urlTab = []	
		url=self.extract_link(videoUrl)
		urlTab.append((url,'1'))
		return urlTab	
			
		
	def getArticle(self, cItem):
		printDBG("DardarkomCom.getVideoLinks [%s]" % cItem)
		retTab = []
		itemsList = []

		if 'prev_url' in cItem: url = cItem['prev_url']
		else: url = cItem['url']

		sts, data = self.cm.getPage(url)
		if not sts: return

		data = self.cm.ph.getDataBeetwenMarkers(data, '<article', '</article>', False)[1]
		icon = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'fposter'), ('</div', '>'), False)[1]
		icon = self.getFullUrl( self.cm.ph.getSearchGroups(icon, '''<img[^>]+?src=['"]([^'^"]+?)['"]''')[0] )
		title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(data, ('<h', '>', 's-title'), ('</h', '>'), False)[1] )
		desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'desc'), ('</div', '>'), False)[1] )

		tmpTab = self.cm.ph.getAllItemsBeetwenNodes(data, ('<ul', '>', 'flist-col'), ('</ul', '>'), False)
		for tmp in tmpTab:
			tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<li', '</li>')
			for item in tmp:
				if 'data-label' in item:
					item = [self.cm.ph.getSearchGroups(item, '''data\-label=['"]([^'^"]+?)['"]''')[0], item]
				else:
					item = item.split('</span>', 1)
					if len(item) < 2: continue
				key = self.cleanHtmlStr(item[0])
				val = self.cleanHtmlStr(item[1])
				if key == '' or val == '': continue
				itemsList.append((key, val))

		return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':{'custom_items_list':itemsList}}]

		 

	
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
			
