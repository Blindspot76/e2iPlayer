# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost
from Components.config import config
import base64,urllib
import re

def getinfo():
	info_={}
	name = 'Faselhd.Co'
	hst = tshost(name)	
	if hst=='': hst = 'https://www.faselhd.live'
	info_['host']= hst
	info_['name']=name
	info_['version']='1.2.01 05/07/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات اسياوية و اجنبية'
	info_['icon']='https://i.ibb.co/XDQ5v3G/facel.png'
	info_['recherche_all']='1'
	#info_['update']='Add Local M3u8 and T7meel servers '	
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'faselhd.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = getinfo()['host']
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):		
		Fasel_TAB=[ {'category':'host2' ,'mode':'30' ,'url':self.MAIN_URL+'/most_recent','title': 'الأحدث'},			
					{'category':'host2' ,'mode':'20'               ,'title': 'الأفلام' },
					{'category':'host2' ,'mode':'20' ,'sub_mode':1 ,'title': 'المسلسلات' },
					{'category':'host2' ,'mode':'20' ,'sub_mode':2 ,'title': 'البرامج التلفزيونية' },	
					{'category':'host2' ,'mode':'20' ,'sub_mode':3 ,'title': 'القسم الاسيوي' },						
					{'category':'host2' ,'mode':'20' ,'sub_mode':4 ,'title': 'الأنمي' },	
					{'category':'search'  ,'title': _('Search'),'search_item':True,'page':1,'hst':'tshost'},
					]
		self.listsTab(Fasel_TAB, {'import':cItem['import'],'name':'host2','icon':cItem['icon']})			


	def showmenu1(self,cItem):
		gnr=cItem.get('sub_mode',0)
		sts, data = self.getPage(self.MAIN_URL)
		if sts:
			lst_data = re.findall('role="menu">(.*?)</div',data, re.S)
			if lst_data:
				data = lst_data[gnr]
				lst_data = re.findall('href="(.*?)".*?>(.*?)<',data, re.S)
				for (url,titre) in lst_data:
					self.addDir({'import':cItem['import'],'category' :'host2', 'url':url, 'title':titre, 'desc':'', 'icon':cItem['icon'], 'mode':'30'})

	def showitms(self,cItem):
		url=cItem['url']
		page=cItem.get('page',1)
		url=url+'/page/'+str(page)+'/'	
		sts, data = self.getPage(url)
		if sts:
			lst_data=re.findall('postDiv">.*?href="(.*?)".*?-src="(.*?)"(.*?)h1">(.*?)<', data, re.S)			
			for (url1,image,desc1,titre) in lst_data:
				desc0,titre = self.uniform_titre(titre)
				desc = desc0
				mode = '31'
				if 'movies_collections' in url1: mode = '30'
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':titre, 'desc':desc, 'icon':image, 'mode':mode} )	
			self.addDir({'import':cItem['import'],'category':'host2', 'url':cItem['url'], 'title':tscolor('\c0000??00')+'Page Suivante', 'page':page+1, 'desc':'Page Suivante', 'icon':cItem['icon'], 'mode':'30'})					



	def showelms(self,cItem):
		url=cItem['url']
		if not url.startswith('http'): 
			post_data = {'seasonID':url}
			url = self.MAIN_URL+'/series-ajax/?_action=get_season_list&_post_id='+url
			sts, data = self.getPage(url,post_data = post_data)
			#printDBG('data='+data)
		else:
			sts, data = self.getPage(url)
		if sts:
			lst_data=re.findall('class="seasonDiv.*?href="(.*?)".*?-src="(.*?)"(.*?)title">(.*?)<', data, re.S)			
			if lst_data:
				for (url1,image,desc,titre) in lst_data:
					self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':titre, 'desc':'', 'icon':image, 'mode':'31'} )	
			else:
				lst_data=re.findall('class="epAll"(.*?)</div', data, re.S)	
				if lst_data:
					lst_data = re.findall('href="(.*?)".*?>(.*?)<',lst_data[0], re.S)
					for (url1,titre) in lst_data:
						self.addVideo({'import':cItem['import'], 'hst':'tshost', 'url':url1, 'title':titre.strip(), 'desc':cItem['desc'], 'icon':cItem['icon']})
				else:
					self.addVideo({'import':cItem['import'], 'hst':'tshost', 'url':cItem['url'], 'title':cItem['title'], 'desc':cItem['desc'], 'icon':cItem['icon']})
		
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			lst_data=re.findall('postDiv">.*?href="(.*?)".*?-src="(.*?)"(.*?)h1">(.*?)<', data, re.S)			
			for (url1,image,desc1,name_eng) in lst_data:
				desc=''
				name_eng=name_eng.replace('&#8211;','-')				
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':str(name_eng), 'desc':desc, 'icon':image, 'mode':'32'} )	

	def MediaBoxResult(self,str_ch,year_,extra):
		urltab=[]
		str_ch_o = str_ch
		str_ch = urllib.quote(str_ch_o+' '+year_)
		url_=self.MAIN_URL+'/page/1/?s='+str_ch
		sts, data = self.cm.getPage(url_)
		if sts:
			lst_data=re.findall('class="movie-wrap">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?<span>(.*?)</span>(.*?)<h1>', data, re.S)			
			for (url1,image,name_eng,desc1,desc2) in lst_data:
				desc=''
				if self.cleanHtmlStr(desc1)!='':
					desc='Rate:'+self.cleanHtmlStr(desc1)+'\n'
				desc=''
				
				name_eng=str(name_eng).replace('&#8211;','-')
				
				x1,titre0=self.uniform_titre(name_eng,year_op=1)
				desc=x1+desc				
				
				if str_ch_o.lower().replace(' ','') == titre0.replace('-',' ').replace(':',' ').lower().replace(' ',''):
					trouver = True
				else:
					trouver = False
				name_eng='|'+tscolor('\c0060??60')+'FaselHD'+tscolor('\c00??????')+'| '+titre0				
				if trouver:
					urltab.insert(0,{'titre':titre0,'import':extra,'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':name_eng, 'desc':desc, 'icon':image, 'mode':'32'} )					
				else:
					urltab.append({'titre':titre0,'import':extra,'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':name_eng, 'desc':desc, 'icon':image, 'mode':'32'} )	
		return urltab	
		
	def get_links(self,cItem): 	
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			Liste_els = re.findall('class="signleWatch(.*?)div', data, re.S)
			if Liste_els:
				Liste_els = re.findall('<li.*?href.*?["\'](.*?)["\'].*?>(.*?)</li', Liste_els[0], re.S)
				for (url,titre) in Liste_els:
					titre = self.cleanHtmlStr(titre)
					local = ''
					if ('سيرفر #01' in titre) or ('سيرفر الجودة الأصلية' in titre):
						titre = '|Server 01| FaselHD'
						local = 'local'
					elif 'سيرفر #07' in titre: titre = '|Server 07| Vidfast.Co'	
					if url.startswith('http'):
						urlTab.append({'name':titre, 'url':'hst#tshost#'+url, 'need_resolve':1,'type':local})	
		return urlTab
		 
	def getVideos(self,videoUrl):
		urlTab = []	
		sts, data = self.cm.getPage(videoUrl)
		if sts:			
			if 'adilbo_HTML_encoder' in data:
				printDBG('ttttttttttttttttttttttttttt'+data)
				t_script = re.findall('<script.*?;.*?\'(.*?);', data, re.S)	
				t_int = re.findall('/g.....(.*?)\)', data, re.S)	
				if t_script and t_int:
					script = t_script[0].replace("'",'')
					script = script.replace("+",'')
					script = script.replace("\n",'')
					sc = script.split('.')
					page = ''
					for elm in sc:
						#printDBG('decode'+elm)
						c_elm = base64.b64decode(elm+'==')
						t_ch = re.findall('\d+', c_elm, re.S)
						if t_ch:
							nb = int(t_ch[0])+int(t_int[0])
							page = page + chr(nb)
					t_url = re.findall('file":"(.*?)"', page, re.S)	
					if t_url:	
						urlTab.append((t_url[0].replace('\\',''),'3'))
			else:
				Liste_els_3 = re.findall('<iframe.*?src="(.*?)"', data, re.S)	
				if Liste_els_3:
					urlTab.append((Liste_els_3[0],'1'))
				else:
					Liste_els_3 = re.findall('file: "(.*?)"', data, re.S)	
					if Liste_els_3:			
						meta = {'iptv_proto':'m3u8','Referer':videoUrl}
						url_=strwithmeta(Liste_els_3[0], meta)
						urlTab.append((url_,'3'))
		return urlTab
		
	def getArticle(self, cItem):
		printDBG("FaselhdCOM.getArticleContent [%s]" % cItem)
		retTab = []
		otherInfo = {}
		title = ''
		desc = ''
		icon = ''
		sts, data = self.cm.getPage(cItem['url'])
		if sts:
			url = self.cm.ph.getDataBeetwenNodes(data, ('<meta', '>', 'refresh'), ('<', '>'))[1]
			url = self.getFullUrl(self.cm.ph.getSearchGroups(url, '''url=['"]([^'^"]+?)['"]''', 1, True)[0])

			if self.cm.isValidUrl(url):
				sts, tmp = self.getPage(url)
				if sts: data = tmp

			data = self.cm.ph.getDataBeetwenNodes(data, ('<header', '>'), ('<style', '>'))[1]
			desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<p', '</p>')[1])
			title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<h1', '</h1>')[1])
			icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(data, '''\ssrc=['"]([^'^"]+?)['"]''')[0])

			keysMap = {'دولة المسلسل':   'country',
					   'حالة المسلسل':   'status',
					   'اللغة':          'language',
					   'توقيت الحلقات':  'duration',
					   'الموسم':         'seasons',
					   'الحلقات':        'episodes',

					   'تصنيف الفيلم':   'genres',
					   'مستوى المشاهدة': 'age_limit',
					   'سنة الإنتاج':     'year',
					   'مدة الفيلم':     'duration',
					   'تقييم IMDB':     'imdb_rating',
					   'بطولة':          'actors',
					   'جودة الفيلم':    'quality'}
			data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<i', '>', 'fa-'), ('</span', '>'))
			for item in data:
				tmp = self.cleanHtmlStr(item).split(':')
				marker = tmp[0].strip()
				value  = tmp[-1].strip().replace(' , ', ', ')
				
				printDBG(">>>>>>>>>>>>>>>>>> marker[%s] -> value[%s]" % (marker, value))
				
				#marker = self.cm.ph.getSearchGroups(item, '''(\sfa\-[^'^"]+?)['"]''')[0].split('fa-')[-1]
				#printDBG(">>>>>>>>>>>>>>>>>> " + marker)
				if marker not in keysMap: continue
				if value == '': continue
				otherInfo[keysMap[marker]] = value

		if title == '': title = cItem['title']
		if desc == '':  desc = cItem.get('desc', '')
		if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)

		return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]

	
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
		if mode=='32':
			self.showitms3(cItem)
