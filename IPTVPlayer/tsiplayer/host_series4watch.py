# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

import re

def getinfo():
	info_={}
	info_['name']='Series4watch.Online'
	info_['version']='1.3 21/10/2019'
	info_['dev']='Opesboy'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات عربية و اجنبية'
	info_['icon']='https://i.ibb.co/zVsWkt4/serie4w.png'
	info_['recherche_all']='1'
	info_['update']='New Site Template'	

	return info_
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'series4watch.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://s4w.tv'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		hst='host2'
		self.Arablionz_TAB = [
							{'category':hst, 'sub_mode':'film', 'title': 'أفـــلام',                  'mode':'21'},
							{'category':hst, 'sub_mode':'serie','title': 'مسلســلات',                 'mode':'21'},
							{'category':hst, 'sub_mode':'other','title': 'رياضة و مصارعه',         'mode':'30','url':self.MAIN_URL+'/category/%D8%B9%D8%B1%D9%88%D8%B6-%D9%85%D8%B5%D8%A7%D8%B1%D8%B9%D8%A9/','page':1},
							{'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
							]		
		self.listsTab(self.Arablionz_TAB, {'import':cItem['import'],'icon':cItem['icon']})	

	def showmenu2(self,cItem):		
		gnr=cItem['sub_mode']
		img_=cItem['icon'] 
		if gnr=='film': 				
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a/','title':'افلام اجنبي','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%b9%d8%b1%d8%a8%d9%8a/','title':'أفلام عربية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%87%D9%86%D8%AF%D9%8A','title':'افلام هندي','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%B3%D9%8A%D9%88%D9%8A%D8%A9/','title':'افلام اسيوية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})					
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%AA%D8%B1%D9%83%D9%8A/','title':'افلام تركي','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
					
		elif gnr=='serie':				
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A/','title':'مسلسلات اجنبية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%B9%D8%B1%D8%A8%D9%8A/','title':'مسلسلات عربية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%AA%D8%B1%D9%83%D9%8A/','title':'مسلسلات تركية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D8%A7%D9%86%D9%85%D9%8A/','title':'مسلسلات انمي','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/category/%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA-%D9%83%D9%88%D8%B1%D9%8A%D8%A9/','title':'مسلسلات كورية','desc':'','page':1,'icon':img_,'sub_mode':gnr,'mode':'30'} )		


		
	def showitms(self,cItem):
		page=cItem['page']
		sUrl=cItem['url']+'?page='+str(page)
		sts, data = self.getPage(sUrl)
		if sts:		 
			cat_data=re.findall('"BlockItem">.*?href="(.*?)".*?src="(.*?)".*?IconsList">(.*?)<strong>(.*?)<.*?HoverDescribe2">(.*?)BlockHover">.*?Describe">(.*?)</div>', data, re.S)
			for (url1,image,inf,name_eng,desc,inf2) in cat_data:
				inf = inf .replace('مشاهدة الآن','')
				desc1=ph.clean_html(inf)+'\\n'
				lst_dat=re.findall('GenreLayer">(.*?)</div>', desc, re.S)
				if lst_dat: desc1=desc1+'Genre: '+ ph.clean_html(lst_dat[0]).replace('النوع','') +'\\n'
				desc=desc1+ph.clean_html(inf2)
				titre = ph.clean_html(name_eng)
				titre = titre.replace('اونلاين','').replace('كامل','').replace('فيلم','').replace('اون لاين','').strip()
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'EPG':True,'hst':'tshost','category' : 'host2','url': url1,'title':titre,'desc':ph.clean_html(desc),'icon':image})			
			self.addDir({'import':cItem['import'],'category' : 'host2','url': cItem['url'],'title':'Next Page','page':page+1,'desc':'Next Page','icon':cItem['icon'],'mode':'30'} )	
	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/?s='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:		
			cat_data=re.findall('"BlockItem">.*?href="(.*?)".*?src="(.*?)".*?IconsList">(.*?)<strong>(.*?)<.*?HoverDescribe2">(.*?)BlockHover">.*?Describe">(.*?)</div>', data, re.S)
			for (url1,image,inf,name_eng,desc,inf2) in cat_data:
				inf = inf .replace('مشاهدة الآن','')
				desc1=ph.clean_html(inf)+'\\n'
				lst_dat=re.findall('GenreLayer">(.*?)</div>', desc, re.S)
				if lst_dat: desc1=desc1+'Genre: '+ ph.clean_html(lst_dat[0]).replace('النوع','') +'\\n'
				desc=desc1+ph.clean_html(inf2)
				titre = ph.clean_html(name_eng)
				titre = titre.replace('اونلاين','').replace('كامل','').replace('فيلم','').replace('اون لاين','').strip()
				self.addVideo({'import':extra,'good_for_fav':True,'EPG':True,'hst':'tshost','category' : 'video','url': url1,'title':titre,'desc':ph.clean_html(desc),'icon':image})			

		
	def get_links(self,cItem): 	
		urlTab = []	
		url_=cItem['url']
		sts, data = self.getPage(url_)
		if sts:
			server_data = re.findall("postID\":'(.*?)'", data, re.S)
			if server_data:
				postid = server_data[0]
				post_data = {'action':'WatchArea','postID':postid}
				url_post = self.MAIN_URL+'/wp-admin/admin-ajax.php'
				sts, data = self.getPage(url_post,post_data=post_data)
				if sts:
					server_data = re.findall('<li.*?src="(.*?)".*?<strong>(.*?)<', data,  re.S | re.IGNORECASE)
					for (url,titre) in server_data:
						if url.startswith('//'): url = 'http:'+url
						if 'سيرفر' in titre: titre = self.up.getDomain(url)
						urlTab.append({'name':titre, 'url':url, 'need_resolve':1})
		return urlTab
		
	def getArticle(self, cItem):
		printDBG("Arablionz.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		desc = cItem['desc']
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('StoryInner">(.*?)</div>', data, re.S)
			if lst_dat:
				desc = ph.clean_html(lst_dat[0])
			
		icon = cItem.get('icon')
		title = cItem['title']			
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='21':
			self.showmenu2(cItem)
		if mode=='30':
			self.showitms(cItem)			


