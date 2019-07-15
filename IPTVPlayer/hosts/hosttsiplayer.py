# -*- coding: utf-8 -*-
###################################################
# LOCAL import 
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetTmpDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.tstools import *
from Plugins.Extensions.IPTVPlayer.tsiplayer.pars_openload import get_video_url as pars_openload
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist

###################################################
# FOREIGN import
###################################################
import re
import urllib
from Screens.MessageBox import MessageBox
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.config import config, ConfigText, getConfigListEntry,ConfigYesNo,ConfigSelection
from os import remove as os_remove, path as os_path, system as os_system
from datetime import datetime
import sys
import os
try:
	sys.path.insert(0,'/usr/lib/enigma2/python/Plugins/Extensions/TSmedia/scripts/script.module.main/lib')
	sys.path.insert(0,'/usr/lib/enigma2/python/Plugins/Extensions/TSmedia/scripts/script.module.urlresolver/lib')
	sys.path.insert(0,'/usr/lib/enigma2/python/Plugins/Extensions/TSmedia/scripts/script.module.urlresolver/lib/urlresolver')
except: pass

###################################################

config.plugins.iptvplayer.ts_xtream_user   = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_xtream_pass   = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_xtream_host   = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_xtream_ua     = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_egybest_email = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_egybest_pass  = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_star7live_user  = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_star7live_pass  = ConfigText(default = '', fixed_size = False)



config.plugins.iptvplayer.ts_dsn           = ConfigYesNo(default = True)
config.plugins.iptvplayer.ud_methode = ConfigSelection(default = "tar", choices = [("tar", "TAR"), ("zip", "ZIP")])
config.plugins.iptvplayer.ol_resolver = ConfigSelection(default = "e2iplayer", choices = [("e2iplayer", "E2IPlayer"), ("tsiplayer", "TSIPlayer")])
config.plugins.iptvplayer.ts_resolver = ConfigSelection(default = "tsmedia", choices = [("tsmedia", "TSMedia"), ("tsiplayer", "TSIPlayer")])
config.plugins.iptvplayer.dev_mod     = ConfigYesNo(default = False)
config.plugins.iptvplayer.imsakiya_tn = ConfigSelection(default = '', choices = tunisia_gouv)
config.plugins.iptvplayer.xtream_active = ConfigSelection(default = "Yes", choices = [("Yes", "Yes"), ("", "No")])

def GetConfigList():
	optionList = []

	optionList.append( getConfigListEntry(_("Decrypt Server Name:"), config.plugins.iptvplayer.ts_dsn) )
	optionList.append( getConfigListEntry(_("Update Archive Type:"), config.plugins.iptvplayer.ud_methode) )
	optionList.append( getConfigListEntry(_("Developer mode:"), config.plugins.iptvplayer.dev_mod) )
	optionList.append( getConfigListEntry(_("TSMedia group Resolver:"), config.plugins.iptvplayer.ts_resolver) )	
	optionList.append( getConfigListEntry(_("Openload Resolver:"), config.plugins.iptvplayer.ol_resolver) )	
	optionList.append( getConfigListEntry(_("Display Xtream:"), config.plugins.iptvplayer.xtream_active) )
	optionList.append( getConfigListEntry(_("Xtream User:"), config.plugins.iptvplayer.ts_xtream_user) )
	optionList.append( getConfigListEntry(_("Xtream Pass:"), config.plugins.iptvplayer.ts_xtream_pass) )
	optionList.append( getConfigListEntry(_("Xtream Host:"), config.plugins.iptvplayer.ts_xtream_host) )	
	optionList.append( getConfigListEntry(_("Xtream User Agent:"), config.plugins.iptvplayer.ts_xtream_ua) )	
	optionList.append( getConfigListEntry(_("Imsakiya:"), config.plugins.iptvplayer.imsakiya_tn) )
	optionList.append( getConfigListEntry(_("EgyBest Email:"), config.plugins.iptvplayer.ts_egybest_email) )
	optionList.append( getConfigListEntry(_("EgyBest Pass:"), config.plugins.iptvplayer.ts_egybest_pass) )
	optionList.append( getConfigListEntry(_("Star7 Live User:"), config.plugins.iptvplayer.ts_star7live_user) )
	optionList.append( getConfigListEntry(_("Star7 Live Pass:"), config.plugins.iptvplayer.ts_star7live_pass) )				
	return optionList



def gettytul():
	return 'TS IPlayer'

class TSIPlayer(CBaseHostClass):

	tsiplayerversion = "2019.07.08.2"  
	tsiplayerremote  = "0.0.0.0"
	
	def __init__(self):
		CBaseHostClass.__init__(self, {'cookie':'TSIPlayer.cookie1'})
		self.USER_AGENT = self.cm.getDefaultHeader()['User-Agent']	
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':'', 'Origin':''}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.DEFAULT_ICON_URL = 'https://i.ibb.co/Q8ZRP0X/yaq9y3ab.png'
		self.import_str	=''				
							
#RICH_DESC_PARAMS = ["alternate_title", "original_title", "station", "price", "age_limit", "views", "status", "type", "first_air_date", "last_air_date", "seasons", "episodes", "country", "language", "duration", "quality", "subtitles", "year", "imdb_rating", "tmdb_rating","released", "broadcast", "remaining", "rating", "rated", "genre", "genres", "category", "categories", "production", "director", "directors", "writer", "writers", "creator", "creators", "cast", "actors", "stars", "awards", "budget", "translation",]

###################################################
# MAIN CATEGORY
###################################################	
	def MainCat(self):
		self.addDir({'name':'cat','category' : 'FilmsSeriesAr','title':'Arabic section','desc':'Arabic section','icon':'https://i.ibb.co/Fgk8Yq4/tsiplayer-films.png'} )	
		self.addDir({'name':'cat','category' : 'FilmsSeriesFr','title':'French section','desc':'Films, Series et Animes en Vf et Vostfr','icon':'https://i.ibb.co/Fgk8Yq4/tsiplayer-films.png'} )	
		self.addDir({'name':'cat','category' : 'FilmsSeriesEn','title':'English section','desc':'Films, Series & Animes (Eng)','icon':'https://i.ibb.co/Fgk8Yq4/tsiplayer-films.png'} )	

		self.addDir({'name':'cat','category' : 'Live','title':'Live Tv & Replay','desc':'Live Tv & Replay','icon':'https://1.bp.blogspot.com/-PHYAba3vvI0/WDroJDScJdI/AAAAAAAABuY/SfwAZRpThoIF-IFAaijBZNWThAn0KXU9QCLcB/s320/Ligtvkafe%2B%25C4%25B0le%2BKumanda%2BSende.jpg'} )

#		self.addDir({'category' : 'Ramadan','title':'Ramadan 2019','desc':'Ramadan','icon':'https://freedesignfile.com/upload/2018/07/Ramadan-kareem-purple-background-vector-01.jpg'} )
#		self.addDir({'category' : 'Kids','title':'Kids','desc':'Kids','icon':'https://store-images.s-microsoft.com/image/apps.29938.9007199266637533.0c6bdecb-3600-484c-8f25-f2bfff75f499.5a2f599e-d619-41d4-a9b9-493f591bd3e0'} )
		if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/TSmedia/addons'):
			desc=''
			version='/usr/lib/enigma2/python/Plugins/Extensions/TSmedia/version'
			pic='file:///usr/lib/enigma2/python/Plugins/Extensions/TSmedia/interface/images/team.png' #'https://i.imgur.com/ddCxCbQ.png'
			with open(version) as f:
				content = f.readlines()	
			for x in content:
				if ':' in x:
					x1,x2=x.strip().split(':',1)
					desc=desc+'\c00????00'+x1+':\c00?????? '+x2+'\\n'
			desc=desc+'\c00????00Developpeur:\c00?????? mfaraj57\\n'		
			self.addDir({'name':'cat','category' : 'tsmedia','title':'TSMedia','desc':desc,'icon':pic,'gnr':'start'} )
		if config.plugins.iptvplayer.dev_mod.value:
			self.addDir({'name':'cat','category' : 'Devmod','title':'Development','desc':'','icon':'http://www.mezganisaid.com/z-include/images/code-dev.png'} )
		self.GetVersions()
		if (self.tsiplayerversion == self.tsiplayerremote):
			color='\c00??????'
			titre_='INFO'
			img_='https://i.ibb.co/Q8ZRP0X/yaq9y3ab.png'
		else:
			color='\c0000????'
			titre_=' ---> UPDATE <--- '
			img_='https://i.ibb.co/fVR0HL6/tsiplayer-update.png'
		params = {'name':'cat','category' : 'update','title':color+titre_,'desc':'تحديث البرنامج','icon':img_} 
		self.addDir(params)	

#1:Ar,2:Live,3:Kids,4:Ramadan,6:Ar+In,10:dev,101:EN,102:FR,
#Live: 100
#All:  101  
#Dev:  102
#Dev Touls :103
#not work: 104
#Arabic: 201:Films 202:Anim 203:kids 204:Islamic
#French: 301,302,303
#Eng:    401,402,403
#
	def FilmCatFr(self):
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Films & Series |★●-----','desc':'Films, Series & Animes en VF et VOSTFR'})	
		self.tsiplayer_host({'cat_id':'101'})	
		self.tsiplayer_host({'cat_id':'301'})
		self.addDir({'name':'search','category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'ALLFR','icon':''})
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Animes & Dessins animés |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'302'})
		self.tsiplayer_host({'cat_id':'303'})

	def FilmCatEn(self):
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Films & Series |★●-----','desc':'Films, Series & Animes'})	
		self.tsiplayer_host({'cat_id':'101'})	
		self.tsiplayer_host({'cat_id':'401'})
#		self.addDir({'name':'search','category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'ALLFR','icon':''})


				
	def FilmCatAr(self):
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Films & Series |★●-----','desc':'Films, Series & Animes en VF et VOSTFR'})			
		self.tsiplayer_host({'cat_id':'101'})	
		self.tsiplayer_host({'cat_id':'201'})	
		self.addDir({'name':'search','category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'ALLAR','icon':''})	
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Animes & Dessins animés |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'202'})
		self.tsiplayer_host({'cat_id':'203'})
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Islamic |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'204'})
		
		
					
	def IptvCat(self):
		self.tsiplayer_host({'cat_id':'100'})
						
	def DevCat(self):
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Tools |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'103'})	
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Hosts en développement |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'102'})	
		self.addMarker({'category' :'marker','title':'\c00????00 -----●★| Hosts Out |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'104'})	


###################################################
# HOST tsmedia
###################################################			
	def tsmedia_host(self,cItem):
		img=cItem['icon']
		gnr=cItem['gnr']		
		if gnr=='start':
			folder='/usr/lib/enigma2/python/Plugins/Extensions/TSmedia/addons'
			lst=[]
			lst=os.listdir(folder)
			for (dir_) in lst:
				if ('.py' not in dir_)and('youtube' not in dir_)and('programs' not in dir_):
					folder2=folder+'/'+dir_
					lst2=[]
					lst2=os.listdir(folder2)
					if (len(lst2)>1):			
						self.addDir({'category' : 'tsmedia','title':dir_.upper(),'desc':cItem['desc'],'icon':img,'folder':folder2,'section':dir_,'gnr':'menu1'})			
		if gnr=='menu1':
			folder=cItem['folder']
			lst=[]
			lst=os.listdir(folder)
			for (dir_) in lst:
				if ('.py' not in dir_):
					folder2=folder+'/'+dir_	
					img1='file://'+folder2+'/icon.png'
					version=folder2+'/addon.xml'
					desc=''
					titre=dir_.upper()
					with open(version) as f:
						content = f.read()	
					inf_list = re.findall('id.*?"(.*?)".*?version.*?"(.*?)".*?name.*?"(.*?)".*?name.*?"(.*?)".*?<description>(.*?)</description>', content, re.S)
					if inf_list: 
						desc='\c00????00Version:\c00?????? '+inf_list[0][1]+'\\n'
						desc=desc+'\c00????00ID:\c00?????? '+inf_list[0][0]+'\\n'
						desc=desc+'\c00????00Provider Name:\c00?????? '+inf_list[0][3]+'\\n'
						desc=desc+'\c00????00Description:\c00?????? '+inf_list[0][4].strip()+'\\n'
						titre=inf_list[0][2].strip()
					self.addDir({'category' : 'tsmedia','title':titre,'desc':desc,'icon':img1,'py_file':folder2+'/default.py','section':cItem['section'],'plugin_id':dir_,'gnr':'menu2'})	



		if gnr=='menu2':
			section_=cItem['section']
			plugin_id_=cItem['plugin_id']					
			py_file=cItem['py_file']
			argv2=cItem.get('argv2','{}')
			if argv2=='{}':
				file_=section_ + '___' +plugin_id_
				try:
					_url='http://86.105.212.206/tsiplayer/stat.php?host=host_TSMedia&cat='+file_
					self.cm.getPage(_url)
				except:
					printDBG('erreur')	
			lst=[]	
			sys.argv = [py_file,'1',argv2,'']
			import_ = 'from Plugins.Extensions.TSmedia.addons.' + section_ + '.' + plugin_id_ + '.default import start'
			try:
				exec (import_)
				lst=start()
				printDBG(str(lst))
			except Exception, e:
				lst=None
				self.addMarker({'title':'\c00????00'+'----> Erreur <----','icon':img,'desc':str(e)})
			if lst:
				self.tsmedia_getlist(lst,cItem)
				
	def tsmedia_getlist(self,lst,cItem):
		img=cItem['icon']
		for elm in lst:      #(titre,argv2_,IMG,x4,x5,x6,x7) in lst:
			titre=elm.get('title','')
			if titre=='':
				titre=elm.get('name','')
			img_=elm['image']
			if img_.startswith('/usr/'): img_='file://'+img_
			img_=img_.replace('TSmedia//interface','TSmedia/interface')
			img_=img_.replace('TSmedia//','TSmedia/addons/')
			desc_=elm['desc']
			url_=elm['url']
			mode_=elm['mode']
			printDBG('elm'+str(elm))
			
			if str(mode_)=='103' or str(mode_)=='603' or str(mode_)=='703' or str(mode_)=='803':
				URL=cItem['section']+'|'+cItem['plugin_id']+'|'+cItem['py_file']+'|'+str(elm)
				self.addDir({'category':'search'  ,'title': _('Search'),'search_item':True,'page':-1,'hst':'tsmedia','url':URL,'icon':img})				
			
			elif mode_==0:
				if 'youtube' in url_:
					self.addVideo({'category' : 'video','hst':'none','title':titre,'url':url_,'desc':desc_,'icon':img_})				
				else:
					self.addVideo({'category' : 'video','hst':'direct','title':titre,'url':url_,'desc':desc_,'icon':img_})	
			elif (self.up.checkHostSupport(url_) == 1) and config.plugins.iptvplayer.ts_resolver.value=='tsiplayer':
				URL=url_
				self.addVideo({'category' : 'video','hst':'none','title':titre,'url':URL,'desc':desc_+' mode='+url_,'icon':img_,'py_file':cItem['py_file'],'section':cItem['section'],'plugin_id':cItem['plugin_id'],'argv2':str(elm),'gnr':'menu2',})					
			else:
				self.addDir({'category' : 'tsmedia','argv2':str(elm),'title':titre,'desc':desc_,'icon':img_,'py_file':cItem['py_file'],'section':cItem['section'],'plugin_id':cItem['plugin_id'],'gnr':'menu2',})		

	def tsmedia_getlist_sea(self,lst,section_,plugin_id_,py_file,argv2,str_ch):
		for elm in lst:      #(titre,argv2_,IMG,x4,x5,x6,x7) in lst:
			titre=elm.get('title','')
			if titre=='':
				titre=elm.get('name','')
			img_=elm['image']
			if img_.startswith('/usr/'): img_='file://'+img_
			img_=img_.replace('TSmedia//interface','TSmedia/interface')
			img_=img_.replace('TSmedia//','TSmedia/addons/')
			desc_=elm['desc']
			url_=elm['url']
			mode_=elm['mode']
			printDBG('elm'+str(elm))
			
			if str(mode_)=='103' or str(mode_)=='603' or str(mode_)=='703' or str(mode_)=='803':
				URL=section_+'|'+plugin_id_+'|'+py_file+'|'+str(elm)
				self.addDir({'category':'_next_page','title': '\c0000??00'+'Page Suivante', 'search_item':False,'page':-1,'searchPattern':str_ch,'url':URL,'hst':'tsmedia','icon':img_})				
			elif mode_==0:
				if 'youtube' in url_:
					self.addVideo({'category' : 'video','hst':'none','title':titre,'url':url_,'desc':desc_,'icon':img_})				
				else:
					self.addVideo({'category' : 'video','hst':'direct','title':titre,'url':url_,'desc':desc_,'icon':img_})	
			elif (self.up.checkHostSupport(url_) == 1) and config.plugins.iptvplayer.ts_resolver.value=='tsiplayer':
				URL=url_
				self.addVideo({'category' : 'video','hst':'none','title':titre,'url':URL,'desc':desc_+' mode='+url_,'icon':img_,'py_file':cItem['py_file'],'section':cItem['section'],'plugin_id':cItem['plugin_id'],'argv2':str(elm),'gnr':'menu2',})					
			else:
				self.addDir({'category' : 'tsmedia','argv2':str(elm),'title':titre,'desc':desc_,'icon':img_,'py_file':py_file,'section':section_,'plugin_id':plugin_id_,'gnr':'menu2',})		


	def tsmedia_search(self,str_ch,page,URL):
		section_,plugin_id_,py_file,argv2=URL.split('|')
		input_txt = str(str_ch)
		if not os.path.exists('/tmp/TSmedia'): os.makedirs('/tmp/TSmedia')
		file = open('/tmp/TSmedia/searchSTR', 'w')
		file.write(input_txt)
		file.close()
		file = open('/tmp/TSmedia/searchSTR.txt', 'w')
		file.write(input_txt)
		file.close()			
		lst=[]
		sys.argv = [py_file,'1',argv2,'']
		import_ = 'from Plugins.Extensions.TSmedia.addons.' + section_ + '.' + plugin_id_ + '.default import start'
		try:
			exec (import_)
			lst=start()
		except Exception, e:
			lst=None
			self.addMarker({'title':'\c00????00'+'----> Erreur <----','icon':img,'desc':str(e)})
		if lst:
			self.tsmedia_getlist_sea(lst,section_,plugin_id_,py_file,argv2,str_ch)	
					
	def get_params(self,data):
		params = {}
		item = data.replace('AxNxD', '&').replace('ExQ', '=')
		paramstring = item
		if len(paramstring) >= 2:
			cleanedparams = paramstring.replace('?', '&')
			pairsofparams = cleanedparams.split('&')
			for i in range(len(pairsofparams)):
				splitparams = {}
				splitparams = pairsofparams[i].split('=')
				if len(splitparams) == 2:
					p=splitparams[1]  
					if isinstance(splitparams[1], basestring) :
						p=urllib.unquote_plus(splitparams[1])     
					params[splitparams[0]] = p
		return params  			


###################################################
# HOST tsiplayer
###################################################	





	def tsiplayer_get_remote(self,cItem):
		cat_id=cItem.get('cat_id','')
		devmod=cItem.get('devmod','')
		folder='/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/tsiplayer'
		import_ = 'from Plugins.Extensions.IPTVPlayer.tsiplayer.'
		lst=[]
		lst=os.listdir(folder)
		lst.sort()
		for (file_) in lst:
			if (file_.endswith('.py'))and(file_.startswith('host_')):
				path_=folder+'/'+file_
				import_str=import_+file_.replace('.py',' import ')

				try:
					exec (import_str+'getinfo')
					info=getinfo()
				except Exception, e:
					info={}
					info['warning']=' >>>>>>> Problem in this host <<<<<<<'
					info['desc']=str(e)
					info['name']=file_
					info['icon']=''
					info['version']=''
					info['cat_id']='104'
					info['dev']=''
				
				
				
				
				desc=''
				param_ = 'oui'
				if (info.get('filtre', '')!=''):
					cmd_='param_ = config.plugins.iptvplayer.'+info.get('filtre', '')+'.value'
					try:
						exec(cmd_)
					except:
						param_ = ''
				if param_!='': 
					if cat_id==info['cat_id']:
						if cat_id=='10':
							desc=desc+'\c00????00 -----> !!!!!!!!! Not Working (Dev Mod) !!!!!!!!! <-----\\n'
						if info.get('warning', '')!='':
							desc=desc+'\c00????00 '+info.get('warning', '')+'\\n'
						desc=desc+'\c00????00 Info: \c00??????'+info['desc']+'\\n \c00????00Version: \c00??????'+info['version']+'\\n \c00????00Developpeur: \c00??????'+info['dev']+'\\n'
						if info.get('update', '')!='':
							desc=desc+'\c00????00 Last Update: \c00??????'+info.get('update', '')+'\\n'
						self.addDir({'category' : 'host2','title':info['name'],'desc':desc,'icon':info['icon'],'mode':'00','import':import_str})
		
	def tsiplayer_get_local(self,cItem):
		cat_id=cItem.get('cat_id','')
		devmod=cItem.get('devmod','')
		folder='/usr/lib/enigma2/python/Plugins/tsiplayer'
		import_ = 'from Plugins.tsiplayer.'
		lst=[]
		if os.path.exists(folder):
			lst=os.listdir(folder)
			lst.sort()
			for (file_) in lst:
				if (file_.endswith('.py'))and(file_.startswith('host_')):
					path_=folder+'/'+file_
					import_str=import_+file_.replace('.py',' import ')
					try:
						exec (import_str+'getinfo')
						info=getinfo()
					except Exception, e:
						info={}
						info['warning']=' >>>>>>> Problem in this host <<<<<<<'
						info['desc']=str(e)
						info['name']=file_
						info['icon']=''
						info['version']=''
						info['cat_id']='104'
						info['dev']=''
						
					desc=''
					param_ = 'oui'
					if (info.get('filtre', '')!=''):
						cmd_='param_ = config.plugins.iptvplayer.'+info.get('filtre', '')+'.value'
						try:
							exec(cmd_)
						except:
							param_ = ''
					if param_!='': 
						if cat_id==info['cat_id']:
							if cat_id=='10':
								desc=desc+'\c00????00 -----> !!!!!!!!! Not Working (Dev Mod) !!!!!!!!! <-----\\n'
							if info.get('warning', '')!='':
								desc=desc+'\c00????00 '+info.get('warning', '')+'\\n'
							desc=desc+'\c00????00 Info: \c00??????'+info['desc']+'\\n \c00????00Version: \c00??????'+info['version']+'\\n \c00????00Developpeur: \c00??????'+info['dev']+'\\n'
							if info.get('update', '')!='':
								desc=desc+'\c00????00 Last Update: \c00??????'+info.get('update', '')+'\\n'
							self.addDir({'category' : 'host2','title':'\c0000????'+info['name'],'desc':desc,'icon':info['icon'],'mode':'00','import':import_str})
				
		
	def tsiplayer_host(self,cItem):
		self.tsiplayer_get_local(cItem)			
		self.tsiplayer_get_remote(cItem)
						
	def host2_host(self,cItem):
		mode_=cItem['mode']
		import_str = cItem.get('import',self.import_str)
		if self.import_str!=import_str:
			file_=import_str.replace('from Plugins.Extensions.IPTVPlayer.tsiplayer.','').replace(' import ','')
			try:
				_url='http://86.105.212.206/tsiplayer/stat.php?host='+file_+'&cat=Main_'
				self.cm.getPage(_url)
			except:
				printDBG('erreur')
			exec (import_str+'TSIPHost')
			self.import_str=import_str
			self.host_ = TSIPHost()	
		self.host_.currList=[]
		self.host_.start(cItem)
		self.currList=self.host_.currList
		
###################################################
# UPDATE
###################################################	

	def GetVersions(self):
		printDBG( 'GetVersions begin' )
		_url = 'https://gitlab.com/Rgysoft/iptv-host-e2iplayer/raw/master/IPTVPlayer/hosts/hosttsiplayer.py'	
		query_data = { 'url': _url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
		try:
			data = self.cm.getURLRequestData(query_data)
			r=self.cm.ph.getSearchGroups(data, '''tsiplayerversion = ['"]([^"^']+?)['"]''', 1, True)[0]
			if r:
				printDBG( 'tsiplayerremote = '+r )
				self.tsiplayerremote=r
		except:
			printDBG( 'Host init query error' )
				

		
	def GetCommits(self):
		printDBG( 'GetCommits begin' )
		try:
			data = self.cm.getURLRequestData({ 'url': 'https://gitlab.com/Rgysoft/iptv-host-e2iplayer/commits/master.atom', 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
		except:
			printDBG( 'Host listsItems query error' )
		printDBG( 'Host listsItems data: '+data )
		phCats = re.findall("<entry>.*?<title>(.*?)</title>.*?<updated>(.*?)</updated>.*?<name>(.*?)</name>", data, re.S)
		if phCats:
			for (phTitle, phUpdated, phName ) in phCats:
				phUpdated = phUpdated.replace('T', '   ')
				phUpdated = phUpdated.replace('Z', '   ')
				phUpdated = phUpdated.replace('+01:00', '   ')
				phUpdated = phUpdated.replace('+02:00', '   ')
				printDBG( 'Host listsItems phTitle: '+phTitle )
				printDBG( 'Host listsItems phUpdated: '+phUpdated )
				printDBG( 'Host listsItems phName: '+phName )
				params = {'category' : 'none','title':phUpdated+' '+phName+'  >>  '+phTitle,'desc':phUpdated+' '+phName+'  >>  '+phTitle,'name':'update'} 
				self.addMarker(params)	
		
	def Update(self):
		printDBG( 'Update begin' )
		params = {'category' : 'none','title':'Local version: '+str(self.tsiplayerversion)+'  |  '+'Remote version: '+str(self.tsiplayerremote),'name':'update'} 
		self.addMarker(params)	

		params = {'category' : 'log','title':'ChangeLog','name':'update'} 
		self.addDir(params)	
		params = {'category' : 'contact','title':'Contact Us','name':'contact'} 
		self.addDir(params)	
		if (self.tsiplayerversion != self.tsiplayerremote):
			if config.plugins.iptvplayer.ud_methode.value=='tar':
				cat_='update_now'
				tag='tar'
			else:
				cat_='update_now2'
				tag='zip'				
				
			params = {'category' : cat_,'title':'\c0000????'+' ++++++++++++ UPDATE NOW ('+tag+') ++++++++++++ ','name':'update'} 
			self.addDir(params)	
			params = {'category' : cat_,'title':'\c0000????'+' +++++++ UPDATE NOW & RESTART ('+tag+') +++++++ ','name':'update_restart'} 
			self.addDir(params)	
		params = {'category' : 'thx','title':'Thanks','name':'thx'} 
		self.addDir(params)				 
		printDBG( 'Host getInitList end' )
		
	def contact(self):
		desc = 'For all requests (new hosts, correction & improvement)'
		self.addMarker({'title':'\c0000??00 eMail: \c00?????? rgysoft@mail.ru','desc':desc})	
		self.addMarker({'title':'\c0000??00 Tunisia Sat: \c00?????? https://www.tunisia-sat.com/forums/threads/3951696/','desc':desc})	
		self.addMarker({'title':'\c0000??00 Facebook: \c00?????? https://www.facebook.com/E2TSIPlayer/','desc':desc})	

	def thx(self):
		self.addMarker({'title':'Special thank to \c0000??00 samsamsam \c00?????? the Main developer & all Developer Team','desc':''})	
		self.addMarker({'title':'Special thank to \c0000???? mamrot \c00?????? & \c0000???? mosz_nowy \c00?????? (update script)','desc':''})	
	
	def update_now(self,cItem):
		name_type=cItem['name']
		printDBG('TSIplayer: Start Update' )
		crc=''
		_url = 'https://gitlab.com/Rgysoft/iptv-host-e2iplayer'
		try:
			crc_data = re.findall('/Rgysoft/iptv-host-e2iplayer/commit/([^"^\']+?)[\'"]',self.cm.getPage(_url)[1], re.S)
			if crc_data:
				crc=crc_data[0]
				printDBG('TSIplayer: crc = '+crc)
			else: printDBG('TSIplayer: crc not found') 
		except:
			printDBG('TSIplayer: Get Main URL Error')		
			return ''		
		tmpDir = GetTmpDir() 
		source = os_path.join(tmpDir, 'iptv-host-e2iplayer.tar.gz') 
		dest = os_path.join(tmpDir , '') 
		_url = 'https://gitlab.com/Rgysoft/iptv-host-e2iplayer/repository/archive.tar.gz?ref=master' 
		try:
			output = open(source,'wb')
			output.write(self.cm.getPage(_url)[1])
			output.close() 
			os_system ('sync')
			printDBG('TSIplayer: Download iptv-host-e2iplayer.tar.gz OK' )
		except:
			if os_path.exists(source): os_remove(source)
			printDBG('TSIplayer: Download Error iptv-host-e2iplayer.tar.gz' )	
			return ''
		
		cmd = 'tar -xzf "%s" -C "%s" 2>&1' % ( source, dest )  
		try: 
			os_system (cmd)
			os_system ('sync')
			printDBG('TSIplayer: Unpacking OK' )
		except:
			printDBG( 'TSIplayer: Unpacking Error' )
			os_system ('rm -f %s' % source)
			os_system ('rm -rf %siptv-host-e2iplayer-%s' % (dest, crc))
			return ''

		try:
			od = '%siptv-host-e2iplayer-master-%s/'% (dest, crc)
			do = resolveFilename(SCOPE_PLUGINS, 'Extensions/') 
			cmd = 'cp -rf "%s"/* "%s"/ 2>&1' % (os_path.join(od, 'IPTVPlayer'), os_path.join(do, 'IPTVPlayer'))
			os_system (cmd)
			os_system ('sync')
			printDBG('TSIplayer: Copy OK')			
		except:
			printDBG('TSIplayer: Copy Error')
			os_system ('rm -f %s' % source)
			os_system ('rm -rf %siptv-host-e2iplayer-master-%s' % (dest, crc))
			return ''

		printDBG( 'TSIplayer: Deleting temporary files' )
		os_system ('rm -f %s' % source)
		os_system ('rm -rf %siptv-host-e2iplayer-master-%s' % (dest, crc))

		 
		if (name_type == 'update_restart'):
			try:			
				from enigma import quitMainloop
				quitMainloop(3)
			except Exception as e:
				printDBG( 'TSIplayer: Erreur='+str(e) )				
				pass			
			 
		params = {'category' : 'none','title':'Update End. Please manual restart enigma2','name':'update'} 
		self.addDir(params)				  
		return ''
		
	def update_now2(self,cItem):
		name_type=cItem['name']
		printDBG('TSIplayer: Start Update' )

		tmpDir = GetTmpDir() 
		source = os_path.join(tmpDir, 'archive.zip') 
		dest = os_path.join(tmpDir , '') 
		_url = 'https://gitlab.com/Rgysoft/iptv-host-e2iplayer/repository/archive.zip' 
		try:
			output = open(source,'wb')
			output.write(self.cm.getPage(_url)[1])
			output.close() 
			os_system ('sync')
			printDBG('TSIplayer: Download archive.zip OK' )
		except:
			if os_path.exists(source): os_remove(source)
			printDBG('TSIplayer: Download Error archive.zip' )	
			return ''
		
		cmd = 'unzip -o "%s" -d "%s"'  % ( source, dest )
		try: 
			os_system (cmd)
			os_system ('sync')
			printDBG('TSIplayer(zip): Unpacking OK' )
		except:
			printDBG( 'TSIplayer(zip): Unpacking Error' )
			os_system ('rm -f %s' % source)
			os_system ('rm -rf /tmp/iptv-host-e2iplayer*/IPTVPlayer')
			return ''
			
		try:
			os_system ('cp -rf /tmp/iptv-host-e2iplayer*/IPTVPlayer /usr/lib/enigma2/python/Plugins/Extensions')
			os_system ('sync')
			printDBG('TSIplayer(Zip): Copy OK')			
		except:
			printDBG('TSIplayer(Zip): Copy Error')
			os_system ('rm -f %s' % source)
			os_system ('rm -rf /tmp/iptv-host-e2iplayer*/IPTVPlayer')
			return ''

		printDBG( 'TSIplayer: Deleting temporary files' )
		os_system ('rm -f %s' % source)
		os_system ('rm -rf /tmp/iptv-host-e2iplayer*/IPTVPlayer')

		 
		if (name_type == 'update_restart'):
			try:			
				from enigma import quitMainloop
				quitMainloop(3)
			except Exception as e:
				printDBG( 'TSIplayer: Erreur='+str(e) )				
				pass			
			 
			 
		params = {'category' : 'none','title':'Update End. Please manual restart enigma2','name':'update'} 
		self.addDir(params)				  
		return ''
		
###################################################
# Main
###################################################	
						
	def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
		printDBG('handleService start')
		CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
		name     = self.currItem.get("name", '')
		category = self.currItem.get("category", '')
		printDBG( "handleService: || name[%s], category[%s] " % (name, category) )
		self.currList = []
		self.cacheLinks = {}
		#MAIN MENU
		if name == None:
			self.MainCat()
		# Update	
		elif category == 'update':
			self.Update()
		elif category == 'update_now':
			self.update_now(self.currItem)	
		elif category == 'update_now2':
			self.update_now2(self.currItem)			
		elif category == 'log':
			self.GetCommits()
		elif category == 'thx':
			self.thx()	
		elif category == 'contact':
			self.contact()		
		#CATEGORIES
		elif category == 'FilmsSeriesAr':
			self.FilmCatAr()
		elif category == 'FilmsSeriesFr':
			self.FilmCatFr()
		elif category == 'FilmsSeriesEn':
			self.FilmCatEn()

		elif category == 'Live':
			self.IptvCat()
		elif category == 'Devmod':
			self.DevCat()
		#Search
		elif category == 'search':
			self.listSearchResult(self.currItem,searchPattern, searchType)	
		elif category == '_next_page':
			self.listSearchResult(self.currItem,'', '')	
		#Hosts
		else:
			exec('self.'+category+'_host(self.currItem)')

		CBaseHostClass.endHandleService(self, index, refresh)
		
	def listSearchResult(self, cItem, searchPattern, searchType):		
		hst=cItem['hst']
		cat=cItem['category']
		page=cItem.get('page',1)
		if cat=='_next_page':
			str_ch = cItem['searchPattern']
		else:
			str_ch = searchPattern
		if hst=='tsmedia':
			URL=cItem['url']
			exec('self.'+hst+'_search(str_ch,page,URL)')
			if page>0:
				self.addDir({'category':'_next_page','title': '\c0000??00'+'Page Suivante', 'search_item':False,'page':page+1,'searchPattern':str_ch,'hst':hst})	

		elif hst=='tshost':		
			img = cItem['icon']
			self.host_.currList=[]
			self.host_.SearchResult(str_ch,page,extra=cItem['import'])
			self.currList=self.host_.currList
			if page>0:
				self.addDir({'import':cItem['import'],'category':'_next_page','title': '\c0000??00'+'Page Suivante','icon':img, 'search_item':False,'page':page+1,'searchPattern':str_ch,'hst':hst})	
		
		elif hst.startswith('ALL'):
			folder='/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/tsiplayer'
			import_ = 'from Plugins.Extensions.IPTVPlayer.tsiplayer.'
			lst=[]
			lst=os.listdir(folder)
			lst.sort()
			for (file_) in lst:
				if (file_.endswith('.py'))and(file_.startswith('host_')):
					path_=folder+'/'+file_
					import_str=import_+file_.replace('.py',' import ')
					exec (import_str+'getinfo')
					info=getinfo()
					desc=''
					param_ = 'oui'
					if (info.get('filtre', '')!=''):
						cmd_='param_ = config.plugins.iptvplayer.'+info.get('filtre', '')+'.value'
						try:
							exec(cmd_)
						except:
							param_ = ''
					if param_!='': 
						if (info.get('recherche_all', '0')=='1') and (((info.get('cat_id', '0')=='201') and hst=='ALLAR') or  ((info.get('cat_id', '0')=='301') and hst=='ALLFR') or  (info.get('cat_id', '0')=='101')):
							self.addMarker({'title':'\c00????00 ----> '+info['name']+' <----','desc':info['desc']})
							try:
								exec (import_str+'TSIPHost')
								self.host_ = TSIPHost()
								self.host_.currList=[]
								self.host_.SearchResult(str_ch,page,extra='')
								lst=self.host_.currList
								lst_out=[]
								for elm in lst:
									elm['import']=import_str
									lst_out.append(elm)
								self.currList.extend(lst_out)
								printDBG(str(self.currList))
							except:
								self.addMarker({'title':'\c00??0000 Error','desc':''})
			self.addDir({'category':'_next_page','title': '\c0000??00'+'Page Suivante', 'search_item':False,'page':page+1,'searchPattern':str_ch,'hst':hst})	

		else:
			exec('self.'+hst+'_search(str_ch,page)')
			if page>0:
				self.addDir({'category':'_next_page','title': '\c0000??00'+'Page Suivante', 'search_item':False,'page':page+1,'searchPattern':str_ch,'hst':hst})	
		
	def getVideoLinks(self, videoUrl):
		printDBG("getVideoLinks [%s]" % videoUrl)
		urlTab = []
		if videoUrl.startswith('hst'):
			_data = re.findall('hst#(.*?)#(.*?)#', videoUrl+'#', re.S)	
			hst=_data[0][0]
			videoUrl=_data[0][1]
		else:
			hst='none'
		if hst=='none':
			urlTab = self.TSgetVideoLinkExt(videoUrl)
		elif hst=='host':
			import_str,videoUrl=videoUrl.split('||')
			exec (import_str+'getVideos')
			urlTab1=getVideos(videoUrl)
			for (url_,type_) in urlTab1:
				if 	type_=='1':
					urlTab = self.TSgetVideoLinkExt(url_)
				else:
					urlTab.append({'name':'Direct', 'url':url_})
		elif hst=='tshost':
			urlTab1=self.host_.getVideos(videoUrl)
			for (url_,type_) in urlTab1:
				if 	type_=='1':
					urlTab = self.TSgetVideoLinkExt(url_)
				elif type_=='3':	
					urlTab = getDirectM3U8Playlist(url_, False, checkContent=True, sortWithMaxBitrate=999999999)
				elif type_=='0':
					urlTab.append({'name':'Direct', 'url':url_})
				elif type_=='4':
					urlTab.append({'name':url_.split('|')[0], 'url':url_.split('|')[1]})					
				else:
					urlTab.append({'name':'Direct', 'url':url_})
		else:
			exec('urlTab = self.'+hst+'_videos(videoUrl)')
		return urlTab
		
	def getLinksForVideo(self, cItem):
		printDBG("TVProart.getLinksForVideo [%s]" % cItem)
		name=cItem['title']
		hst=cItem['hst']
		

		
		urlTab = []
		if hst=='direct':	
			urlTab.append({'name':name, 'url':cItem['url'], 'need_resolve':0})		
		elif hst=='none':
			urlTab.append({'name':name, 'url':cItem['url'], 'need_resolve':1})
		elif hst=='tshost':	
			import_str = cItem.get('import',self.import_str)
			if self.import_str!=import_str:
				exec (import_str+'TSIPHost')
				self.import_str=import_str
				self.host_ = TSIPHost()	
			urlTab=self.host_.get_links(cItem)						
		else:
			exec('urlTab = self.'+hst+'_links(cItem[\'url\'])')		
		return urlTab
		
	def getArticleContent(self, cItem):
		printDBG("getArticleContent [%s]" % cItem) 
		retTab = []
		hst=cItem['hst']
		if hst=='direct':			
			data=cItem.get('category', '')
			if data=='host2':
				retTab=self.host_.getArticle(cItem)
		elif hst=='tshost':		
			retTab=self.host_.getArticle(cItem)			
		else:	
			exec ('retTab=self.'+hst+'_getArticleContent(cItem)')
		return retTab

	def openloadResolver(self, URL):
		urlTab = []	
		Live_Cat_data = re.findall('embed/(.*)/',URL, re.S)		
		if Live_Cat_data:
			ol_id=Live_Cat_data[0]
			sts, sHtmlContent = self.cm.getPage('https://api.openload.co/1/file/info?file={'+ol_id+'}')		
			if '"status":404' in sHtmlContent:
				message='File not found'
				self.sessionEx.open(MessageBox,message, type = MessageBox.TYPE_ERROR, timeout = 20)		
			else:
				sts, sHtmlContent = self.cm.getPage('https://api.openload.co/1/streaming/get?file={'+ol_id+'}')
				if 'IP address not authorized' in sHtmlContent:
					message='Please visit https://olpair.com/'
					self.sessionEx.open(MessageBox,'IP address not authorized' + '\n' + message, type = MessageBox.TYPE_ERROR, timeout = 20)
				else:
					Live_Cat_data = re.findall('url":"(.*?)"',sHtmlContent, re.S)
					if Live_Cat_data:
						url_=Live_Cat_data[0].replace('\\','')
						urlTab = [{'url': url_, 'name': 'openload.co'}]	
		else:
			message=URL
			self.sessionEx.open(MessageBox,'Contact RGYSOFT' + '\n' + message, type = MessageBox.TYPE_ERROR, timeout = 20)		
		return urlTab
		 
	def TSgetVideoLinkExt(self,videoUrl):
		urlTab=[]
		if ('openload' in videoUrl) and (config.plugins.iptvplayer.ol_resolver.value=='tsiplayer'):
			urlTab = pars_openload(videoUrl)
			printDBG(str(urlTab))
			
			#urlTab = self.openloadResolver(videoUrl)
		else:
			urlTab = self.up.getVideoLinkExt(videoUrl)	
		return urlTab
	

class IPTVHost(CHostBase): 

	def __init__(self):    
		CHostBase.__init__(self, TSIPlayer(), False, []) 
		
	def withArticleContent(self, cItem):
		if cItem.get('EPG', False):
			return True
		else:
			return False
		
