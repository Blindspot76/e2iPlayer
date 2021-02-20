# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re
import base64,urllib

def getinfo():
	info_={}
	info_['name']='Aflamy'
	info_['version']='1.0 14/07/2020'
	info_['dev']='RGYSoft' + tscolor('\c00????30') + ' >> Thx to TSmedia <<'
	info_['cat_id']='201'
	info_['desc']='افلام و مسلسلات كرتون'
	info_['icon']='https://i.ibb.co/TmtpsxH/logo.png'
	info_['recherche_all']='0'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{})
		self.MAIN_URL = 'http://aflamy.ps'
		
	def showmenu(self,cItem):
		TAB = [('أفلام','','10',0),('مسلسلات','','10',1),('أنمي','','10',2),('إسلامي','/Sections.aspx?SECID=85&Page=1','20',''),('رياضة','/Sections.aspx?SECID=64&Page=1','20','')]
		self.add_menu(cItem,'','','','','',TAB=TAB,search=True)
		#self.add_menu(cItem,'<ul class="list-unstyled(.*?)</u','<li>.*?href="(.*?)".*?>(.*?)<','','20',del_=['طلبات'],search=True)		

	def showmenu1(self,cItem):
		gnr = cItem.get('sub_mode','')
		if   gnr == 2 : TAB = [('مسلسلات كرتونية','/Sections.aspx?SECID=87&Category_ID=88&Page=1','20',''),('أفلام كرتونية','/Sections.aspx?SECID=87&Category_ID=89&Page=1','20','')]	
		elif gnr == 1 : TAB = [('مسلسلات عربية','/Sections.aspx?SECID=62&Category_ID=71&Page=1','20',''),('مسلسلات رمضانية','/Sections.aspx?SECID=62&Category_ID=97&Page=1','20',''),
		                       ('مسلسلات أجنبية','/Sections.aspx?SECID=62&Category_ID=72&Page=1','20',''),('مسلسلات تركية','/Sections.aspx?SECID=62&Category_ID=74&Page=1','20',''),
							   ('مسلسلات هندية','/Sections.aspx?SECID=62&Category_ID=90&Page=1','20',''),('مسلسلات كورية','/Sections.aspx?SECID=62&Category_ID=91&Page=1','20',''),
							   ('البرامج','/Sections.aspx?SECID=62&Category_ID=63&Page=1','20','')]
		elif gnr == 0 : TAB = [('أفلام عربية','/Sections.aspx?SECID=57&Category_ID=58&Page=1','20',''),('أفلام أجنبية','/Sections.aspx?SECID=57&Category_ID=59&Page=1','20',''),
		                       ('أفلام هندية','/Sections.aspx?SECID=57&Category_ID=60&Page=1','20',''),('أفلام آسيوية','/Sections.aspx?SECID=57&Category_ID=98&Page=1','20',''),
							   ('أفلام تركية','/Sections.aspx?SECID=57&Category_ID=99&Page=1','20',''),('أفلام وثائقية','/Sections.aspx?SECID=57&Category_ID=61&Page=1','20','')]	
		self.add_menu(cItem,'','','','','',TAB=TAB)

	def showitms(self,cItem):
		desc = [('Rate','class="starR">(.*?)</span>','',''),('Category','class="category">(.*?)</span>','','')]
		next = ['id="ContentPlaceHolder1_next.*?href="(.*?)"','20']
		url = cItem['url'].replace('&amp;','&')
		sts, data = self.getPage(cItem['url'].replace('&amp;','&'))
		if sts:
			self.add_menu(cItem,'','class="movieBlock.*?href="(.*?)".*?src=\'(.*?)\'(.*?)moive-title.*?>(.*?)<(.*?)</a>',data,'21',ord=[0,3,1,2,4],Desc=desc,Next=next,EPG=True)

	def showelms(self,cItem):
		if '/movies/' in cItem['url']:
			sts, data = self.getPage(cItem['url'].replace('&amp;','&'))
			if sts:
				lst_ = re.findall('sources:.*?file.*?[\'"](.*?)[\'"]', data, re.S)
				if lst_:
					self.addVideo({'category':'host2', 'title': cItem['title'],'url':lst_[0], 'desc':cItem['desc'],'import':cItem['import'],'icon':cItem['icon'],'hst':'direct'})	
		else:
			data1=re.findall('id=(.*?)&', cItem['url'], re.S)
			if data1:	
				id = data1[0]
				url = self.MAIN_URL+'/api/Series.aspx?ID='+id
				sts, data = self.getPage(url)
				if sts:
					lst_ = re.findall('Name":"(.*?)".*?Link":"(.*?)"', data, re.S)
					for (name,link) in lst_:
						URL = self.MAIN_URL+'/api/Series.aspx?ID='+link
						link = link.replace('/DLNASDELL','DLNASDELL')
						link ='http://dl3.aflamy.ps:1935/TEST/_definst_/mp4:'+link+'/playlist.m3u8'						
						#printDBG('LINKKKK='+link+'#'+name)
						self.addVideo({'category':'host2', 'title': name,'url':link, 'desc':cItem['desc'],'import':cItem['import'],'icon':cItem['icon'],'hst':'direct'})	
			
	def SearchResult(self,str_ch,page,extra):
		url = self.MAIN_URL+'/Search.aspx?Key='+str_ch
		desc = [('Rate','class="starR">(.*?)</span>','',''),('Category','class="category">(.*?)</span>','','')]
		self.add_menu({'import':extra,'url':url},'','class="movieBlock.*?href="(.*?)".*?src=\'(.*?)\'(.*?)moive-title.*?>(.*?)<(.*?)</a>','','21',ord=[0,3,1,2,4],Desc=desc,EPG=True)

	def getArticle(self,cItem):
		Desc = [('Year','class="year.*?>(.*?)<','',''),('Category','class="category.*?>(.*?)<','',''),('Rate','stars">.*?title=\'(.*?)\'','',''),('Story','Description">(.*?)</div>','\n','')]
		desc = ''
		sts, data = self.getPage(cItem['url'].replace('&amp;','&'))
		if sts:
			desc = self.add_menu(cItem,'','InfoDetails">(.*?)class="clearfix',data,'desc',Desc=Desc)	
		if desc =='': desc = cItem.get('desc','')
		return [{'title':cItem['title'], 'text': desc, 'images':[{'title':'', 'url':cItem.get('icon','')}], 'other_info':{}}]

		
