# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

def getinfo():
    info_={}
    info_['name']='Alwan Film'
    info_['version']='1.0 27/12/2020'
    info_['dev']='RGYSoft'
    info_['cat_id']='21'
    info_['desc']='افلام و مسلسلات كرتون'
    info_['icon']='https://i.ibb.co/Bj4mLP1/Sans-titre.png'
    info_['recherche_all']='0'
    return info_

class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'none.cookie'})
        self.MAIN_URL   = 'https://alwanfilm.com'
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        self.HEADER     = {'User-Agent': self.USER_AGENT,'x-requested-with':'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': False}
                
    def showmenu(self,cItem):
        TAB = [('أفلام','/','20',0),('مسرحيات','/genre/مسرحيات-ملونة/','20',1)]
        self.add_menu(cItem,'','','','','',TAB=TAB,search=True)
       
    def showitms(self,cItem):
        desc = [('Date','</h3>(.*?)</span>','',''),('Rating','rating">(.*?)</div>','',''),('Quality','quality">(.*?)</div>','','')]
        self.add_menu(cItem,'','class="item .*?alt="(.*?)".*?src="(.*?)"(.*?)href="(.*?)"(.*?)</article>','','video',ord=[3,0,1,2,4],Desc=desc)

    def SearchResult(self,str_ch,page,extra):
        url = self.MAIN_URL+'/?s='+str_ch
        desc = [('Date','year">(.*?)</span>','',''),('Rating','rating">(.*?)</span>','',''),('Story','contenido">(.*?)</div>','\n','')]        
        self.add_menu({'import':extra,'url':url},'','item">.*?href="(.*?)".*?data-src="(.*?)".*?title">(.*?)</div>(.*?)</article>','','video',ord=[0,2,1,3],Desc=desc)
    
    def get_links(self,cItem): 		
        result = self.add_menu(cItem,'',"<li id='player.*?data-type='(.*?)'.*?data-post='(.*?)'.*?data-nume='(.*?)'.*?title'>(.*?)<",'','param_servers',ord=[3,0,1,2])						
        return result[1]	

    def getVideos(self,videoUrl):   
        URL = self.MAIN_URL+'/wp-admin/admin-ajax.php'
        params=videoUrl.split('%%')
        data_post = {'action':'doo_player_ajax','post':int(params[1]),'nume':int(params[2]),'type':params[0].strip()}
        result = self.add_menu({'url':URL},'','(embed_url)":"(.*?)"','','link1',ord=[1,0],post_data=data_post)	
        return result[1]	
        
