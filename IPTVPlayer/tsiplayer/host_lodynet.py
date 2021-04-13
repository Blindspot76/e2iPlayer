# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re
import base64,urllib

def getinfo():
    info_={}
    info_['name']='Lodynet'
    info_['version']='1.0 12/07/2020'
    info_['dev']='RGYSoft'
    info_['cat_id']='21'
    info_['desc']='افلام و مسلسلات كرتون'
    info_['icon']='https://www.lodynet.co/wp-content/uploads/2015/12/logo-1.png'
    info_['recherche_all']='0'
    return info_


class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{})
        self.MAIN_URL = 'https://ww.lodynet.cam'
        
    def showmenu(self,cItem):
        TAB = [('مسلسلات','','10',0),('افلام','','10',1),('برامج و حفلات','/category/برامج-و-حفلات-tv/','20','')]
        self.add_menu(cItem,'','','','','',TAB=TAB,search=True)

    def showmenu1(self,cItem):
        gnr = cItem.get('sub_mode','')
        if gnr == 0 : TAB = [('مسلسلات هندية','/category/مسلسلات-هنديه/','20',''),('مسلسلات هندية مدبلجة','/category/1dubbed-indian-series/','20',''),('مسلسلات هندية مترجمة','/المسلسلات-هندية-مترجمة/','20',''),
                            ('مسلسلات تركية','/category/مشاهدة-مسلسلات-تركية/','20',''),('مسلسلات تركية مدبلجة','/category/مشاهدة-مسلسلات-تركية-مدبلجة/','20',''),('مسلسلات كورية','/category/مشاهدة-مسلسلات-كورية/','20',''),
                            ('مسلسلات تركية','/category/مشاهدة-مسلسلات-تركية/','20',''),('مسلسلات تركية مدبلجة','/category/مشاهدة-مسلسلات-تركية-مدبلجة/','20',''),('مسلسلات كورية','/category/مشاهدة-مسلسلات-كورية/','20',''),
                            ('مسلسلات صينية مترجمة','/category/مسلسلات-صينية-مترجمة/','20',''),('مسلسلات تايلاندية','/category/مسلسلات-تايلاندية/','20',''),('مسلسلات مكسيكية','/category/مسلسلات-مكسيكية/','20','')]
        elif gnr == 1 : TAB = [('افلام هندية','/category/افلام-هندية-مترجمة/','20',''),('أفلام هندية مدبلجة','/category/أفلام-هندية-مدبلجة/','20',''),('افلام تركية مترجم','/category/افلام-تركية-مترجم/','20',''),
                            ('افلام اسيوية','/category/افلام-اسيوية/','20',''),('افلام اجنبي','/category/افلام-اجنبية-مترجمة/','20',''),('انيمي','/category/انيمي/','20','')]
        self.add_menu(cItem,'','','','','',TAB=TAB)

    def showitms(self,cItem):
        desc = [('Info','Ribbon">(.*?)</div>','',''),('Time','<time>(.*?)</time>','','')]
        next = ['class="next page.*?href="(.*?)"','20']
        self.add_menu(cItem,'','class="LodyBlock.*?href="(.*?)".*?>(.*?)<img.*?src="(.*?)".*?<h2>(.*?)</h2>(.*?)</li>','','21',ord=[0,3,2,1,4],Desc=desc,Next=next,u_titre=True,EPG=True)		

    def showelms(self,cItem):
        desc = [('Episode','NumberLayer">(.*?)</div>','',''),('Time','<time>(.*?)</time>','','')]
        next = ['class="next page-numbers.*?href="(.*?)"','21']
        self.add_menu(cItem,'CategorySubLinks">(.*?)class="pagination">','class="LodyBlock.*?href="(.*?)".*?<img.*?src="(.*?)"(.*?)<h2>(.*?)</h2>(.*?)</li>','','video',ord=[0,3,1,2,4],Next=next,Desc=desc,u_titre=True,EPG=True)		
            
    def SearchResult(self,str_ch,page,extra):
        url = self.MAIN_URL+'/search/'+str_ch+'/page/'+str(page)
        desc = [('Info','Ribbon">(.*?)</div>','',''),('Time','<time>(.*?)</time>','','')]
        self.add_menu({'import':extra,'url':url},'','class="LodyBlock.*?href="(.*?)".*?>(.*?)<img.*?src="(.*?)".*?<h2>(.*?)</h2>(.*?)</li>','','21',ord=[0,3,2,1,4],Desc=desc,u_titre=True)

    def getArticle(self,cItem):
        Desc = [('Date','PublishDate">(.*?)</div>','',''),('Story','BoxContentInner">(.*?)</div>','\n','')]
        desc = self.add_menu(cItem,'','DetailsBox">(.*?)<ul','','desc',Desc=Desc)	
        if desc =='': desc = cItem.get('desc','')
        return [{'title':cItem['title'], 'text': desc, 'images':[{'title':'', 'url':cItem.get('icon','')}], 'other_info':{}}]

    def get_links(self,cItem): 		
        local = [('vidlo.us','LoDyTo','0'),]
        result = self.add_menu(cItem,'ServersList">(.*?)</ul','<li.*?data-embed="(.*?)".*?>(.*?)</li>','','serv',local=local)						
        return result[1]	
        
