# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Components.config import config
import re
import base64,urllib

def getinfo():
	info_={}
	info_['name']='CimaNow'
	info_['version']='1.0 04/03/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='افلام و مسلسلات'
	info_['icon']='https://i.ibb.co/5LnpQrZ/cimanow.png'
	info_['recherche_all']='0'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'cimanow.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://cima-now.com'
		self.MAIN_URL = 'https://new.cima-now.com'		
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.cacheLinks = {}
		self.getPage = self.cm.getPage
		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'الرئيسية','icon':'https://i.ibb.co/CHgkb4c/Home.png','mode':'10','sub_mode':-1,'url':self.MAIN_URL+'/category/%d8%a7%d9%84%d8%a7%d9%81%d9%84%d8%a7%d9%85/'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'أفلام','icon':'https://i.ibb.co/pr0KVFL/Films.png','mode':'10','sub_mode':0,'url':self.MAIN_URL+'/category/%d8%a7%d9%84%d8%a7%d9%81%d9%84%d8%a7%d9%85/'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'مسلسلات','icon':'https://i.ibb.co/cCxKTnt/series.png','mode':'10','sub_mode':1,'url':self.MAIN_URL+'/category/%d8%a7%d9%84%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa/'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'رمضان','icon':'https://i.ibb.co/mCsssTr/ramadan.png','mode':'10','sub_mode':2,'url':self.MAIN_URL+'/category/%d8%b1%d9%85%d8%b6%d8%a7%d9%86/'})		
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'برامج تليفزيونية','url':self.MAIN_URL+'/category/%d8%a7%d9%84%d8%a8%d8%b1%d8%a7%d9%85%d8%ac-%d8%a7%d9%84%d8%aa%d9%84%d9%81%d8%b2%d9%8a%d9%88%d9%86%d9%8a%d8%a9/','icon':'https://i.ibb.co/3kXyKqh/prog.png','mode':'20'})		
		self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':'https://i.ibb.co/sqkBMBP/search.png'})

	def showmenu1(self,cItem):
		ind=cItem.get('sub_mode',0)
		if ind>-1:
			URL=cItem.get('url','')
			pat = '<ul class="sub-menu">(.*?)</ul>'
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'الكل','url':URL,'icon':cItem['icon'],'mode':'20'})
			sts, data = self.getPage(self.MAIN_URL)
			if sts:
				Liste_els = re.findall(pat, data, re.S)		
				if Liste_els:
					if len(Liste_els)>ind:
						data1=Liste_els[ind]
						Listes_els = re.findall('<li.*?href="(.*?)".*?>(.*?)<', data1, re.S)	
						for (url,titre) in Listes_els:
							self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'icon':cItem['icon'],'mode':'20'})
		else:
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'احدث المواضيع','url':self.MAIN_URL+'/?','icon':cItem['icon'],'mode':'20'})		
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'المواضيع المثبتة','url':'pin','icon':cItem['icon'],'mode':'20','sub_mode':0})
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'الاكثر مشاهدة' ,'url':'views','icon':cItem['icon'],'mode':'20','sub_mode':0})
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'الاكثر اعجابا' ,'url':'likes','icon':cItem['icon'],'mode':'20','sub_mode':0})
			
	def showitms(self,cItem):
		printDBG('citem='+str(cItem))
		ind=cItem.get('sub_mode',-1)
		page=cItem.get('page',1)
		pat = 'class="block".*?href="(.*?)"(.*?)image:url\((.*?)\).*?class="title.*?>(.*?)<.*?class="content.*?>(.*?)<.*?detail(.*?)</a>'
		if page!=1:
			if '?' in cItem['url']:
				url=cItem['url']+'page='+str(page)+'/'
			else:
				url=cItem['url']+'page/'+str(page)+'/'
		else:
			url=cItem['url']
		if ind==0:
			post_data = {'key':url}
			url = self.MAIN_URL+'/wp-content/themes/CimaNow/Interface/filter.php'
			sts, data = self.getPage(url,post_data=post_data)
		else: sts, data = self.getPage(url)
		if sts:
			i=0	
			Liste_els = re.findall(pat, data, re.S)
			for (url,inf1,image,titre,inf2,inf3) in Liste_els:
				titre = self.cleanHtmlStr(titre)
				inf0,titre = self.uniform_titre(titre,year_op=1)
				desc = inf0
				inf_1=''
				inf_2=''
				Lst_inf = re.findall('ribbon">(.*?)<',inf1, re.S)
				if Lst_inf: inf_1 = Lst_inf[0]
				Lst_inf = re.findall('ribbon1">(.*?)<',inf1, re.S)
				if Lst_inf: inf_2 = ' / ' + Lst_inf[0]				
				desc = desc+tscolor('\c00????00')+'Info: '+tscolor('\c00??????') + inf_1 + inf_2+' | '
				Lst_inf = re.findall('<li.*?>(.*?)</li>',inf3, re.S)
				for elm in Lst_inf:
					if   'fa-play'     in elm: desc = desc+tscolor('\c00????00')+'Qual: '+tscolor('\c00??????') + self.cleanHtmlStr(elm)+' | '
					elif 'fa-calendar' in elm: desc = desc+tscolor('\c00????00')+'Year: '+tscolor('\c00??????') + self.cleanHtmlStr(elm)+' | '
					elif 'fa-film'     in elm: desc = desc+tscolor('\c00????00')+'Cat: ' +tscolor('\c00??????') + self.cleanHtmlStr(elm)+' | '
					elif 'fa-eye'      in elm: desc = desc+tscolor('\c00????00')+'View: ' +tscolor('\c00??????') + self.cleanHtmlStr(elm)+' | '	
				desc = desc+tscolor('\c00????00')+'\nDesc: '+tscolor('\c00??????') + self.cleanHtmlStr(inf2) +'\n'
				self.addDir({'import':cItem['import'],'category' : 'host2','title':self.cleanHtmlStr(titre),'url':url ,'desc':desc,'icon':image,'mode':'20','good_for_fav':True,'EPG':True,'hst':'tshost'})
				i=i+1
			if (i>13) and (ind<0): self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':cItem['url'],'page':page+1,'mode':'20'})
			if i==0: self.addVideo({'import':cItem['import'],'category' : 'host2','title':cItem['title'],'url':cItem['url'] ,'desc':cItem['desc'],'icon':cItem['icon'],'good_for_fav':True,'hst':'tshost'})			

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			pat = 'class="block".*?href="(.*?)"(.*?)image:url\((.*?)\).*?class="title.*?>(.*?)<.*?class="content.*?>(.*?)<.*?detail(.*?)</a>'
			Liste_els = re.findall(pat, data, re.S)
			for (url,inf1,image,titre,inf2,inf3) in Liste_els:
				titre = self.cleanHtmlStr(titre)
				inf0,titre = self.uniform_titre(titre,year_op=1)
				desc = inf0
				inf_1=''
				inf_2=''
				Lst_inf = re.findall('ribbon">(.*?)<',inf1, re.S)
				if Lst_inf: inf_1 = Lst_inf[0]
				Lst_inf = re.findall('ribbon1">(.*?)<',inf1, re.S)
				if Lst_inf: inf_2 = ' / ' + Lst_inf[0]				
				desc = desc+tscolor('\c00????00')+'Info: '+tscolor('\c00??????') + inf_1 + inf_2+' | '
				Lst_inf = re.findall('<li.*?>(.*?)</li>',inf3, re.S)
				for elm in Lst_inf:
					if   'fa-play'     in elm: desc = desc+tscolor('\c00????00')+'Qual: '+tscolor('\c00??????') + self.cleanHtmlStr(elm)+' | '
					elif 'fa-calendar' in elm: desc = desc+tscolor('\c00????00')+'Year: '+tscolor('\c00??????') + self.cleanHtmlStr(elm)+' | '
					elif 'fa-film'     in elm: desc = desc+tscolor('\c00????00')+'Cat: ' +tscolor('\c00??????') + self.cleanHtmlStr(elm)+' | '
					elif 'fa-eye'      in elm: desc = desc+tscolor('\c00????00')+'View: ' +tscolor('\c00??????') + self.cleanHtmlStr(elm)+' | '	
				desc = desc+tscolor('\c00????00')+'\nDesc: '+tscolor('\c00??????') + self.cleanHtmlStr(inf2) +'\n'
				self.addDir({'import':extra,'category' : 'host2','title':self.cleanHtmlStr(titre),'url':url ,'desc':desc,'icon':image,'mode':'20','good_for_fav':True,'EPG':True,'hst':'tshost'})


	def getArticle(self,cItem):
		printDBG("mycima.getVideoLinks [%s]" % cItem) 
		otherInfo1 = {}
		title = cItem['title']
		icon = cItem.get('icon','')
		desc = cItem.get('desc','')
		sts, data = self.getPage(cItem['url'])
		if sts:
			data1 = ''
			lst_dat=re.findall('detailsPoster">(.*?)</ul>', data, re.S)
			if lst_dat: data1 = data1+lst_dat[0]
			lst_dat=re.findall('detailsContentSide">(.*?)</ul>', data, re.S)
			if lst_dat: data1 = data1+lst_dat[0]			
			lst_dat=re.findall('titleShape">(.*?)</ul>', data, re.S)
			if lst_dat: data1 = data1+lst_dat[0]			
			
			lst_dat=re.findall('<li(.*?)</span>(.*?)</li>', data1, re.S)
			for (x1,x2) in lst_dat:
				if 'إخراج'  in x1: otherInfo1['director'] = self.cleanHtmlStr(x2)
				if 'تأليف'  in x1: otherInfo1['writer'] = self.cleanHtmlStr(x2)			
				if 'المدة'  in x1: otherInfo1['duration'] = self.cleanHtmlStr(x2)					
				if 'النوع'  in x1: otherInfo1['genres'] = self.cleanHtmlStr(x2)
				if 'الجودة'  in x1: otherInfo1['quality'] = self.cleanHtmlStr(x2)
				if 'سنة'    in x1: otherInfo1['year'] = self.cleanHtmlStr(x2)
				if 'االتصنيف' in x1: otherInfo1['category'] = self.cleanHtmlStr(x2)
				if 'الممثلين'  in x1: otherInfo1['actors'] = self.cleanHtmlStr(x2)

			lst_dat=re.findall('storyFilm">(.*?)<div class', data, re.S)
			if lst_dat: desc = self.cleanHtmlStr(lst_dat[0])
			else: desc = cItem['desc']
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

	def get_links(self,cItem): 	
		url=str(cItem['url'])
		printDBG('url='+url)
		urlTab = self.cacheLinks.get(url, [])
		printDBG('Cache='+str(urlTab))
		if urlTab == []:
			sts, data = self.getPage(url)
			if sts:
				Liste_els = re.findall('serversUl">(.*?)</ul>', data, re.S)
				if 	Liste_els:
					data0 = Liste_els[0]
					id_tab = re.findall("'id':(.*?),", data0, re.S)
					if id_tab:
						id_ = id_tab[0].strip()
						Liste_els = re.findall('<li.*?data-server="(.*?)".*?>(.*?)</li>', data0, re.S)
						for (url,titre) in Liste_els:
							local_=''
							if 'cn server'   in titre.lower(): titre='fembed'
							elif 'vidbob'    in titre.lower(): titre='jawcloud'
							elif 'Cima Now'  in titre: local_='local'
							titre = self.cleanHtmlStr(titre).strip()
							if ('Server' in titre) and (config.plugins.iptvplayer.ts_dsn.value):
								urlTab0=self.getVideos(url+'|'+id_)
								for elm in urlTab0:
									printDBG('elm='+str(elm))
									url_ = elm[0]
									urlTab.append({'name':'|Watch Server*| '+self.up.getDomain(url_), 'url':url_, 'need_resolve':1})
							else:
								urlTab.append({'name':'|Watch Server| '+titre, 'url':'hst#tshost#'+url+'|'+id_, 'need_resolve':1,'type':local_})
				Liste_els = re.findall('class="download">(.*?)</ul>', data, re.S)
				for elm in Liste_els:
					Tag    = '|Download Server| '
					local_ = 'non'
					if 'الجودات' in elm:
						local_ = 'local'
						L_els = re.findall('<li.*?href="(.*?)".*?>(.*?)</li>', elm, re.S)
						for (url,titre) in L_els:
							if ('Server' in titre) and (config.plugins.iptvplayer.ts_dsn.value):
								urlTab0=self.getVideos(url+'|'+'DOWN')
								for elm in urlTab0:
									printDBG('elm='+str(elm))
									url_ = elm[0]
									urlTab.append({'name':'|Download Server| '+self.up.getDomain(url_), 'url':url_, 'need_resolve':1})
							else:
								urlTab.append({'name':Tag+self.cleanHtmlStr(titre), 'url':'hst#tshost#'+url+'|'+'DOWN', 'need_resolve':1,'type':local_})		
			self.cacheLinks[str(cItem['url'])] = urlTab
			printDBG('Cache='+str(self.cacheLinks[str(cItem['url'])]))
		return urlTab	
			
	def getVideos(self,videoUrl):
		urlTab = []	
		code,id_ = videoUrl.split('|',1)
		if id_ == 'DOWN':
			sts, data = self.getPage(code,self.defaultParams)
			printDBG('data='+data)
			Liste_els = re.findall('id="downloadbtn".*?href="(.*?)"', data, re.S|re.IGNORECASE)			
			if Liste_els:
				url_ = Liste_els[0]
				if url_.endswith('mp4'):
					host = url_.split('.net/',1)[0]+'.net'
					URL_= strwithmeta('MP4|'+url_, {'Referer':host})
					urlTab.append((URL_,'4'))	
				else:
					urlTab.append((url_,'1'))
		else:	
			url = self.MAIN_URL+'/wp-content/themes/CimaNow/Interface/server.php'
			post_data = {'id':id_, 'server':code}
			sts, data = self.getPage(url,post_data=post_data)
			if sts:
				Liste_els_3 = re.findall('src="(.+?)"', data, re.S|re.IGNORECASE)	
				if Liste_els_3:
					URL = Liste_els_3[0]
					if URL.startswith('//'): URL='http:'+URL
					if 'cimanow.net/' in URL:
						host = URL.split('.net/',1)[0]+'.net'
						printDBG('host='+host)
						sts, data = self.getPage(URL,self.defaultParams)
						if sts:
							printDBG('data='+data)
							Liste_els = re.findall('source.*?src="(.*?)".*?size="(.*?)"', data, re.S|re.IGNORECASE)
							for elm in Liste_els:
								url_ = elm[0]
								if not(url_.startswith('http')): url_ = host + urllib.quote(url_)
								URL_= strwithmeta(elm[1]+'|'+url_, {'Referer':host})
								urlTab.append((URL_,'4'))
					else:
						urlTab.append((URL,'1'))
		return urlTab			
				
	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		elif mode=='10':
			self.showmenu1(cItem)	
		elif mode=='11':
			self.showmenu2(cItem)
		elif mode=='12':
			self.showmenu3(cItem)		
		elif mode=='20':
			self.showitms(cItem)
		elif mode=='21':
			self.showelms(cItem)		
		return True
