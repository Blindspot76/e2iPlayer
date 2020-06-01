# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,unifurl,tscolor,tshost
import urllib
import re
from Components.config import config

def getinfo():
	info_={}
	name = 'Arabseed'
	hst = tshost(name)	
	if hst=='': hst = 'https://m2.arabseed.net'
	info_['host']= hst
	info_['name']=name
	info_['version']='1.5.1 07/11/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'#'201'
	info_['desc']='أفلام و مسلسلات عربية و اجنبية'
	info_['icon']='https://m2.arabseed.net/wp-content/themes/ArbSeed/logo-white.png'
	info_['recherche_all']='1'
	info_['update']='Add Filter section'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'arabseed.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = getinfo()['host']
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		#self.getPage = self.cm.getPage
		self.cacheLinks = {}


	def getPage(self, baseUrl, addParams = {}, post_data = None):
		baseUrl=self.std_url(baseUrl)
		if addParams == {}: addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
		
	def showmenu0(self,cItem):
		hst='host2'
		self.Arablionz_TAB = [
							{'category':hst, 'sub_mode':0, 'title': 'افلام',       'mode':'20'},
							{'category':hst, 'sub_mode':1, 'title': 'مسلسلات',     'mode':'20'},
							{'category':hst, 'sub_mode':2, 'title':'رمضان 2020',  'mode':'20'},
							{'category':hst, 'sub_mode':3, 'title': 'اقسام اخري', 'mode':'20'},
							{'category':hst,               'title': tscolor('\c0000????') + 'حسب التصنيف' , 'mode':'21','count':1,'data':'none','code':''},	
							{'category':'search','title':tscolor('\c00????30') + _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
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
						if not url.startswith('http'): url=self.MAIN_URL+url
						self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
		elif gnr==2:	
			self.Arablionz_TAB = [
								{'category':hst,'title': 'مسلسلات رمضان 2020',    'mode':'30', 'url':self.MAIN_URL+'/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%b1%d9%85%d8%b6%d8%a7%d9%86-2020-hd'},
								#{'category':hst,'title': 'برامج رمضان 2019',     'mode':'30', 'url':self.MAIN_URL+'/category/%D8%A8%D8%B1%D8%A7%D9%85%D8%AC-%D8%B1%D9%85%D8%B6%D8%A7%D9%86-2019'},
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

	def showmenu2(self,cItem):
		count=cItem['count']
		data1=cItem['data']	
		codeold=cItem['code']	
		if count==1:
			sts, data = self.getPage(self.MAIN_URL)
			if sts:
				data1=re.findall('class="ListDroped">(.*?)</div>', data, re.S)
			else:
				data1=None
		if count==5:
			mode_='30'
		else:
			mode_='21'
		if data1:
			lst_data1 = re.findall('<li.*?data-tax="(.*?)".*?data-term="(.*?)">(.*?)</li>',data1[count-1], re.S)	
			for (x1,x2,x3) in lst_data1:
				#if  ((('–' not in x2) and ('-' not in x2)) or('Sci-Fi' in x2))and ('null' not in x2)and ('كريستينا' not in x2):
				code=codeold+x1+'='+x2.strip()+'&'
				self.addDir({'import':cItem['import'],'category' :'host2', 'url':code, 'title':ph.clean_html(x3), 'desc':x1, 'icon':cItem['icon'], 'mode':mode_,'count':count+1,'data':data1,'code':code, 'sub_mode':'item_filter','page':-1})					
		
	def showitms(self,cItem):
		#printDBG('citem='+str(cItem))
		page=cItem.get('page',1)
		urlorg=cItem['url']
		if urlorg.startswith('http'):
			titre=cItem['title']
			img=cItem['icon']
			if page!=-1:
				url1=urlorg+'?page='+str(page)
			else:
				url1=urlorg
			sts, data = self.getPage(url1)
		else:
			post_data ={}
			if '&' in urlorg:
				prams = urlorg.split('&')
			else:
				prams = urlorg
			for param in prams:
				if '=' in param:
					pram_x1,param_x2 = param.split('=')
					post_data[pram_x1]=param_x2
				
			urlorg = self.MAIN_URL+'/wp-content/themes/ArbSeed/ajaxCenter/Home/AdvFiltering.php'
			sts, data = self.getPage(urlorg,post_data=post_data)
		if sts:
			data1=re.findall('class="BlockItem.*?href="(.*?)".*?src="(.*?)".*?Title">(.*?)<(.*?)</div>', data, re.S)		
			i=0
			for (url,image,titre,desc) in data1:
				desc = desc .replace ('<li>','rgyrgy')
				desc=ph.clean_html(desc)
				desc = desc .replace ('rgyrgy','\n')
				desc0,titre = self.uniform_titre(titre)
				if desc.strip()!='':
					desc = tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+desc
				desc=desc0+desc								
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'mode':'31','hst':'tshost'})			
				i=i+1
			if i>38:
				if 'AdvFiltering.php' not in urlorg:
					self.addDir({'import':cItem['import'],'name':'categories', 'category':'host2', 'url':urlorg, 'title':'Page Suivante', 'page':page+1, 'desc':'Page Suivante', 'icon':img, 'mode':'30'})	

	def showelms(self,cItem):
		url1=cItem['url']
		img=cItem['icon']
		self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url1,'title':cItem['title'],'desc':'','icon':img,'hst':'tshost'})		
		sts, data = self.getPage(url1)
		if sts:
			data2=re.findall('<div class="episode-block.*?href="(.*?)".*?>(.*?)</div>', data, re.S)
			for (url,titre) in data2:
				titre = ph.clean_html(titre).replace('حلقة رقم','').strip()
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':'E'+titre,'desc':'','icon':img,'hst':'tshost'})	
	
	def SearchResult(self,str_ch,page,extra):	
		url_=self.MAIN_URL+'/?s='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:		
			data1=re.findall('class="BlockItem.*?href="(.*?)".*?src="(.*?)".*?Title">(.*?)<(.*?)</div>', data, re.S)		
			i=0
			for (url,image,titre,desc) in data1:
				desc=ph.clean_html(desc)
				titre=ph.clean_html(titre)
				desc0,titre = self.uniform_titre(titre)
				if desc.strip()!='':
					desc = tscolor('\c00????00')+'Desc: '+tscolor('\c00??????')+desc
				desc=desc0+desc	
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'mode':'31','hst':'tshost'})			


	def MediaBoxResult(self,str_ch,year_,extra):
		urltab=[]
		str_ch_o = str_ch
		str_ch = urllib.quote(str_ch_o+' '+year_)	
		url_=self.MAIN_URL+'/?s='+str_ch+'&page='+str(1)
		sts, data = self.getPage(url_)
		if sts:		
			data1=re.findall('class="BlockItem.*?href="(.*?)".*?src="(.*?)".*?Title">(.*?)<(.*?)</div>', data, re.S)		
			i=0
			for (url,image,titre,desc) in data1:
				desc=ph.clean_html(desc)
				titre=ph.clean_html(titre)
				desc0,titre = self.uniform_titre(titre,year_op=1)
				if desc.strip()!='':
					desc = tscolor('\c00????00')+'Desc: '+tscolor('\c00??????')+desc
				desc=desc0+desc	
				titre0='|'+tscolor('\c0060??60')+'ArabSeeD'+tscolor('\c00??????')+'| '+titre				
				
				urltab.append({'titre':titre,'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre0,'desc':desc,'icon':image,'mode':'31','hst':'tshost'})			
		return urltab



		
	def get_links(self,cItem): 	
		urlTab = []	
		if config.plugins.iptvplayer.ts_dsn.value:
			urlTab = self.cacheLinks.get(str(cItem['url']), [])		
		if urlTab == []:		
			url=cItem['url']+'watch/'
			sts, data = self.getPage(url)
			if sts:
				server_data = re.findall('data-server="(.*?)".*?>(.*?)</li>', data, re.S)
				post_data = re.findall("data: {post:.*?'(.*?)'", data, re.S)
				if post_data:
					for (code1,srv) in server_data:
						code2 = post_data[0]
						srv = ph.clean_html(srv)
						srv = srv.replace('سيرفر','Server').replace('عرب سيد',' ArabSeed')
						local = ''
						if 'ArabSeed' in srv: local = 'local'
						if not config.plugins.iptvplayer.ts_dsn.value:
							urlTab.append({'name':srv, 'url':'hst#tshost#'+code1+'|'+code2, 'need_resolve':1,'type':local})	
						else:
							urlTab0=self.getVideos(code1+'|'+code2)
							for elm in urlTab0:
								#printDBG('elm='+str(elm))
								url_ = elm[0]
								type_ = elm[1]
								if type_ == '1':		
									name_ = gethostname(url_)
									urlTab.append({'name':'|'+srv+'| '+name_, 'url':url_, 'need_resolve':1,'type':local})									
					urlTab = sorted(urlTab, key=lambda x: x['name'], reverse=False)
			if config.plugins.iptvplayer.ts_dsn.value:
				self.cacheLinks[str(cItem['url'])] = urlTab
		return urlTab
			
	def getVideos(self,videoUrl):
		urlTab = []	
		code1,code2=videoUrl.split('|')
		url=self.MAIN_URL+'/wp-content/themes/ArbSeed/Server.php'
		post_data = {'post':code2,'index':code1}
		sts, data = self.getPage(url,post_data=post_data)
		if sts:
			Liste_els = re.findall('src.*?["\'](.*?)["\']', data, re.S|re.IGNORECASE)
			if Liste_els:
				URL_ = Liste_els[0]
				if URL_.startswith('//'): URL_ = 'http:'+URL_
				urlTab.append((URL_,'1'))
		return urlTab	
		
	def getArticle(self, cItem):
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
		if mode=='21':
			self.showmenu2(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelms(cItem)

