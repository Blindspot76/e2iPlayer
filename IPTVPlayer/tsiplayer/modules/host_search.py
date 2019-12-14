# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,TsThread
from Plugins.Extensions.IPTVPlayer.components.e2ivkselector import GetVirtualKeyboard

from Components.config import config
import re,os

def getinfo():
	info_={}
	info_['name']=tscolor('\c0000????')+'>> Search ALL <<'
	info_['version']='1.0 28/11/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='904'
	info_['desc']='Search in ALL Hosts'
	info_['icon']='https://i.ibb.co/rfPB0v5/database-icon-4.png'	
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'tsiplayer.cookie'})
		
	def showmenu0(self,cItem):
		type_  = cItem.get('gnr','')
		cat_id_filtre=[]
		if type_=='ar': cat_id_filtre=['201']
		if type_=='fr': cat_id_filtre=['301']
		if type_=='en': cat_id_filtre=['401']
		self.list=[]
		if config.plugins.iptvplayer.xtream_active.value=='Yes': cat_id_filtre.append('101')
		str_ch = cItem.get('str_ch','NoneNone')
		page   = cItem.get('page',1)
		if str_ch=='NoneNone':
			ret = self.sessionEx.waitForFinishOpen(GetVirtualKeyboard(), title=_('Set file name'))
			if isinstance(ret[0], basestring): str_ch=ret[0]
			else:
				self.addMarker({'title':'String Search Not Valid !!'})
				return
		folder  = '/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/tsiplayer'
		import_ = 'Plugins.Extensions.IPTVPlayer.tsiplayer.'
		lst     = []
		lst     = os.listdir(folder)
		lst.sort()
		threads = []
		for (file_) in lst:
			if (file_.endswith('.py'))and(file_.startswith('host_')):
				path_       = folder+'/'+file_
				file_ = file_.replace('.py','')
				import_str  = import_+file_
				_temp       = __import__(import_str, globals(), locals(), ['getinfo'], -1)
				info        = _temp.getinfo()
				search      = info.get('recherche_all', '0')	
				cat_id      = info.get('cat_id', '0')
				name        = info['name']
				if 	(cat_id in cat_id_filtre)and(search!='0'):	
					printDBG('--------------> Recherche '+name+'<----------------')
					threads.append(TsThread(self.get_results,import_str,str_ch,page,name,file_))
		printDBG('1110')
		[i.start() for i in threads]
		[i.join(timeout=2)  for i in threads]	
		printDBG('1111')
		for elm in self.list:
			if elm.get('category' ,'')=='video':
				self.addVideo(elm)
			elif elm.get('category' ,'')=='mark':
				self.addMarker(elm)
			else:
				self.addDir(elm)
		printDBG('1112')	
		self.addDir({'category' : 'host2','title':tscolor('\c0000??00')+'Next','str_ch':str_ch,'desc':'','icon':cItem['icon'],'mode':'00','import':cItem['import'],'gnr':type_})			
		
	def get_results(self,import_str,str_ch,page,name,file_):
		printDBG('0001')
		_temp = __import__(import_str, globals(), locals(), ['TSIPHost'], -1)
		host_ = _temp.TSIPHost()
		host_.currList=[]
		host_.SearchResult(str_ch,page,extra='')
		lst = host_.currList
		printDBG('0002')
		import_str = 'from '+import_str+' import '
		lst.insert(0,{'title':tscolor('\c00????00')+' ----> '+name+' <----','category' : 'mark'})
		printDBG('0003')
		for elm in lst:
			elm['import']=import_str
			#elm['title']=name+'|'+elm['title']
			self.list.append(elm)
		printDBG('0004')	
			
			
	def start(self,cItem):
		list_=[]
		mode=cItem.get('mode', None)
		if mode=='00':
			list_ = self.showmenu0(cItem)	
		return True
