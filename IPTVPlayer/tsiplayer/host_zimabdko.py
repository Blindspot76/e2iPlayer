# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor

import re

def getinfo():
	info_={}
	info_['name']='Zimabdko.Com'
	info_['version']='1.1 20/10/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='202'
	info_['desc']='انمي + دراما اسياوية'
	info_['icon']='https://www.zimabdko.com/wp-content/themes/zimabdk/images/logo.png'
	info_['recherche_all']='0'
	info_['update']='Bugs Fix'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'zimabdko.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.zimabdko.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']
		cat_TAB = [
					{'category':hst,'title': 'أفلام الأنيمي'    ,'mode':'30','url':'http://www.zimabdko.com/anime/'},
					{'category':hst,'title': 'الأنميات'        ,'mode':'30','url':'http://www.zimabdko.com/series/'},
					{'category':hst,'title': 'آخر الحلقات'    ,'mode':'30','url':'http://www.zimabdko.com/episodes/'},					
					{'category':hst,'title': 'الدراما الأسيوية','mode':'30','url':'http://www.zimabdko.com/asian-movies/'},					
					{'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
					]
		self.listsTab(cat_TAB, {'import':cItem['import'],'icon':img_})						
		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		if page>0:
			sts, data = self.getPage(url1+'page/'+str(page)+'/')
		else:
			sts, data = self.getPage(url1)
		if sts:
			if 'class="movies-servers' not in data:
				films_list = re.findall('class="one-poster.*?href="(.*?)".*?src="(.*?)".*?<h2>(.*?)</h2>.*?hover-poster.*?>(.*?)</div>', data, re.S)		
				i=0
				for (url,image,titre,desc_) in films_list:
					desc=''
					i=i+1
					inf_list = re.findall('<span.*?>(.*?)</span>', desc_, re.S)		
					for elm in inf_list:
						if ph.clean_html(elm) !='':
							if 'fa-star' in elm:
								desc=desc+'Rating: '+tscolor('\c00????00')+ph.clean_html(elm)+tscolor('\c00??????')+'\\n'
							elif 'fa-eye' in elm:
								desc=desc+'View: '+tscolor('\c00????00')+ph.clean_html(elm)+tscolor('\c00??????')+'\\n'
							else:
								desc=desc+tscolor('\c00????00')+ph.clean_html(elm)+tscolor('\c00??????')+'\\n'			
					self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':ph.clean_html(titre),'desc':desc,'icon':image,'hst':'tshost','mode':'30','page':-1,'EPG':True})	
				if (i>17) and (page >0):
					self.addDir({'import':cItem['import'],'title':'Next Page','page':page+1,'category' : 'host2','url':url1,'icon':cItem['icon'],'mode':'30'} )									
			else:
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url1,'title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'})	
					
	
	def SearchResult(self,str_ch,page,extra):
		url_='http://www.zimabdko.com/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('class="one-poster.*?href="(.*?)".*?src="(.*?)".*?<h2>(.*?)</h2>.*?hover-poster">(.*?)</div>', data, re.S)		
			for (url,image,titre,desc_) in films_list:
				desc=''
				inf_list = re.findall('<span.*?>(.*?)</span>', desc_, re.S)		
				for elm in inf_list:
					if 'fa-star' in elm:
						desc=desc+'Rating: '+tscolor('\c00????00')+ph.clean_html(elm)+tscolor('\c00??????')+'\\n'
					elif 'fa-eye' in elm:
						desc=desc+'View: '+tscolor('\c00????00')+ph.clean_html(elm)+tscolor('\c00??????')+'\\n'
					else:
						desc=desc+tscolor('\c00????00')+ph.clean_html(elm)+tscolor('\c00??????')+'\\n'			
				self.addDir({'import':extra,'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'hst':'tshost','EPG':True})	

		
	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			Liste_els = re.findall('class="movies-servers.*?<ul(.*?)</ul>', data, re.S)
			if Liste_els:		
				Liste_els_2 =  re.findall('<li.*?data-serv="(.*?)".*?post="(.*?)">(.*?)</li>', Liste_els[0], re.S)
				for (code1,code2,srv) in Liste_els_2:
					url='https://www.zimabdko.com/wp-admin/admin-ajax.php?action=codecanal_ajax_request&post='+code2+'&serv='+code1
					sts, data = self.getPage(url)
					Liste_els = re.findall('src.*?["\'](.*?)["\']', data, re.S)
					if Liste_els:
						urlTab.append({'name':'|Server: '+ph.clean_html(srv)+'| '+gethostname(Liste_els[0]), 'url':Liste_els[0], 'need_resolve':1})						
		return urlTab

		
	def getArticle(self, cItem):
		printDBG("cima4u.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc= cItem['desc']	
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('class="head-s-meta-first(.*?)</div>', data, re.S)
			if lst_dat:
				lst_dat2=re.findall('<span>(.*?)<span>(.*?)</span>', lst_dat[0], re.S)
				for (x1,x2) in lst_dat2:
					if 'تقييم'  in x1: otherInfo1['imdb_rating'] = ph.clean_html(x2)
					if 'الدولة'  in x1: otherInfo1['country'] = ph.clean_html(x2)			
					if 'حالة'  in x1: otherInfo1['status'] = ph.clean_html(x2)					
					if 'اللغة'  in x1: otherInfo1['language'] = ph.clean_html(x2)
					if 'سنة' in x1: otherInfo1['year'] = ph.clean_html(x2)					
					if 'مدة'  in x1: otherInfo1['duration'] = ph.clean_html(x2)				


			lst_dat=re.findall('class="head-s-meta-last(.*?)</div>', data, re.S)
			if lst_dat:
				lst_dat2=re.findall('<span(.*?)<a.*?>(.*?)</span>', lst_dat[0], re.S)
				for (x1,x2) in lst_dat2:
					if 'الجودة'  in x1: otherInfo1['quality'] = ph.clean_html(x2)
					if 'الفئة' in x1: otherInfo1['age_limit'] = ph.clean_html(x2)			
					if 'السنة'  in x1: otherInfo1['year'] = ph.clean_html(x2)					
				
					
			lst_dat=re.findall('class="head-s-meta-ctas.*?>(.*?)</div>', data, re.S)
			if lst_dat:		
				otherInfo1['genres'] = ph.clean_html(lst_dat[0])				
										
			lst_dat=re.findall('class="head-s-story.*?>(.*?)</div>', data, re.S)
			if lst_dat:		
				desc=ph.clean_html(lst_dat[0])

		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='30':
			self.showitms(cItem)			
			
