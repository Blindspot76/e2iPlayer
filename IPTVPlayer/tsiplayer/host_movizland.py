# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.packer import cPacker
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
import re

def getinfo():
    info_={}
    name = 'Movizland.Com'
    hst = tshost(name)	
    if hst=='': hst = 'https://movizland.top'
    info_['host']= hst
    info_['name']=name
    info_['version']='1.2.01 05/07/2020'
    info_['dev']='RGYSoft'
    info_['cat_id']='21'
    info_['desc']='أفلام, مسلسلات و انمي بالعربية'
    info_['icon']='https://i.ibb.co/ZS8tq3z/movizl.png'
    info_['recherche_all']='1'
    #info_['update']='New Template'	
    return info_
    
    
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'movizland.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL        = getinfo()['host']
        self.MAIN_URL_MOBILE = 'https://app.movizland.online'
        self.defaut_mobile = False
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.getPage = self.cm.getPage
                         
    def showmenu0(self,cItem):
        hst='host2'
        img_=cItem['icon']								
        Cat_TAB = [
                    {'category':hst,'title': 'الأفلام',                  'mode':'20','sub_mode':0},
                    {'category':hst,'title': 'المسلسلات',               'mode':'20','sub_mode':1},
                    {'category':hst,'title': 'تصنيف آخر ',             'mode':'20','sub_mode':2},												
                    {'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
                    {'category':hst,'title': tscolor('\c00????00')+'Mobile Version',  'mode':'40'},			
                    ]
        self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})				
        
    def showmenu10(self,cItem):
        self.defaut_mobile = True
        sts, data = self.getPage(self.MAIN_URL_MOBILE)
        if sts:
            Liste_films_data = re.findall('id="tabs-ui">(.*?)</ul>', data, re.S)
            if Liste_films_data:
                Liste_films_data0 = re.findall('<li>.*?href="(.*?)".*?title="(.*?)"', Liste_films_data[0], re.S)
                for (url,titre) in Liste_films_data0:
                    self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'icon':cItem['icon'],'mode':'50','sub_mode':'3'})
            self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})

    def showmenu1(self,cItem):
        self.defaut_mobile = False
        sts, data = self.getPage(self.MAIN_URL)
        if sts:
            gnr=cItem.get('sub_mode', 0)
            if gnr==1:
                self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c0000????') + 'Ramadan 2021','url':self.MAIN_URL+'/category/series/arab-series/?release-year=2021','icon':cItem['icon'],'mode':'30'})
            Liste_films_data = re.findall('DropdownFilter">(.*?)</ul', data, re.S)
            if Liste_films_data:			
                Liste_films_data0 = re.findall('<li>.*?href="(.*?)".*?">(.*?)</li>', Liste_films_data[gnr], re.S)
                for (url,titre) in Liste_films_data0:
                    if 'javascript' in url:
                        if gnr==0: url = self.MAIN_URL+'/category/movies/'
                        if gnr==1: url = self.MAIN_URL+'/category/series/'
                        if gnr==2: url = self.MAIN_URL+'/'
                    self.addDir({'import':cItem['import'],'category' : 'host2','title':ph.clean_html(titre),'url':url,'icon':cItem['icon'],'mode':'30'})
                if gnr <3:
                    self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c00????00')+'By Filter','icon':cItem['icon'],'mode':'21','sub_mode':gnr})

    def showfilter(self,cItem):
        count=cItem.get('count',0)
        data=cItem.get('data',[])
        gnr=cItem.get('sub_mode', 0)
        filter_=cItem.get('filter_','')
        if count==0:
            sts, data1 = self.getPage(self.MAIN_URL+'/homepage6/')
            if sts:
                Liste_films_data = re.findall('DropdownFilter">(.*?)</ul', data1, re.S)
                if Liste_films_data:
                    self.addMarker({'title':tscolor('\c0000??00')+'التصنيف','desc':'','icon':cItem['icon']})
                    data = Liste_films_data
                    elm_list = re.findall('<li>.*?data-term="(.*?)".*?">(.*?)</li>', data[gnr], re.S)
                    for (term,titre) in elm_list:
                        self.addDir({'import':cItem['import'],'count':1,'data':data,'category' : 'host2','url': '','filter_':term,'title':ph.clean_html(titre),'desc':ph.clean_html(titre),'icon':cItem['icon'],'hst':'tshost','mode':'21'})	
                
        elif count==1:			
            self.addMarker({'title':tscolor('\c0000??00')+'النوع','desc':'','icon':cItem['icon']})
            self.addDir({'import':cItem['import'],'count':2,'data':data,'category' : 'host2','url': '','filter_':filter_+'|'+'undefined','title':'الكل','desc':cItem['desc']+'|'+'كل الانواع','icon':cItem['icon'],'hst':'tshost','mode':'21'})	
            elm_list = re.findall('<li>.*?data-term="(.*?)".*?">(.*?)</li>', data[3], re.S)
            for (term,titre) in elm_list:
                self.addDir({'import':cItem['import'],'count':2,'data':data,'category' : 'host2','url': '','filter_':filter_+'|'+term,'title':ph.clean_html(titre),'desc':cItem['desc']+'|'+ph.clean_html(titre),'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

        elif count==2:			
            self.addMarker({'title':tscolor('\c0000??00')+'سنة الإصدار','desc':'','icon':cItem['icon']})
            self.addDir({'import':cItem['import'],'count':3,'data':data,'category' : 'host2','url': '','filter_':filter_+'|'+'undefined','title':'الكل','desc':cItem['desc']+'|'+'كل السنوات','icon':cItem['icon'],'hst':'tshost','mode':'21'})		
            elm_list = re.findall('<li>.*?data-term="(.*?)".*?">(.*?)</li>', data[4], re.S)
            for (term,titre) in elm_list:
                self.addDir({'import':cItem['import'],'count':3,'data':data,'category' : 'host2','url': '','filter_':filter_+'|'+term,'title':ph.clean_html(titre),'desc':cItem['desc']+'|'+ph.clean_html(titre),'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

        elif count==3:			
            self.addMarker({'title':tscolor('\c0000??00')+'الجودة','desc':'','icon':cItem['icon']})	
            self.addDir({'import':cItem['import'],'category' : 'host2','url': '','filter_':filter_+'|'+'undefined','title':'الكل','desc':cItem['desc']+'|'+'كل الجودات','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
            elm_list = re.findall('<li>.*?data-term="(.*?)".*?">(.*?)</li>', data[5], re.S)
            for (term,titre) in elm_list:
                self.addDir({'import':cItem['import'],'category' : 'host2','url': '','filter_':filter_+'|'+term,'title':ph.clean_html(titre),'desc':cItem['desc']+'|'+ph.clean_html(titre),'icon':cItem['icon'],'hst':'tshost','mode':'30'})	


    def showitms(self,cItem):
        urlo=cItem.get('url', '')
        page = cItem.get('page', 1)	
        filter_ = cItem.get('filter_', '')
        if 	(urlo=='') and (filter_!=''):
            x1,x2,x3,x4 = filter_.split('|')
            post_data={'category':x1,'genre':x2,'year':x3,'quality':x4}
            url = self.MAIN_URL+'/wp-content/themes/Movizland2019/Filtering.php'
            sts, data = self.getPage(url,post_data=post_data)
            
            #if sts: _data = re.findall('pageurl =.*?\'(.*?)\'', data, re.S)
                #if _data: urlo=_data[0]				
        else:
            if urlo.endswith('/'):	
                url = urlo+'?page='+str(page)+'/'
            else:
                url = urlo+'/?page='+str(page)+'/'
            if url.startswith('/'): url = self.MAIN_URL + url
            sts, data = self.getPage(url)
        if sts:
            Liste_films_data = re.findall('BlockItem">.*?href="(.*?)".*?<img.*?src="(.*?)"(.*?)RestInformation">(.*?)</ul.*?InfoEndBlock">(.*?)</ul.*?Title">(.*?)<', data, re.S)
            for (url1,image,desc0,desc1,desc2,name_eng) in Liste_films_data:
                name_eng=self.cleanHtmlStr(name_eng.strip())
                desc3,titre = self.uniform_titre(name_eng,-1)
                desc = desc3 + self.get_desc(desc0,desc1,desc2)
                image=self.std_url(image)
                self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'icon':image,'desc':desc,'mode':'31','good_for_fav':True,'EPG':True,'hst':'tshost'})					
            if (filter_==''):
                self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c0000??00')+'Page Suivante','url':urlo,'page':page+1,'mode':'30'})


    def showitms_mobile(self,cItem):
        urlo=cItem.get('url', '')	
        page = cItem.get('page', 1)
        url=cItem['url']+'page/'+str(page)+'/'		
        sts, data = self.getPage(url)
        if sts:
            Liste_films_data = re.findall('<li class="grid-item(.*?)src="(.*?)".*?Title">(.*?)<', data, re.S)
            for (url1,image,name_eng) in Liste_films_data:
                Liste_url = re.findall('href="(.*?)"', url1, re.S)
                if Liste_url:
                    URL = Liste_url[-1]
                    desc,titre = self.uniform_titre(name_eng.strip(),-1)
                    image=self.std_url(image)
                    self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':URL,'icon':image,'desc':desc,'good_for_fav':True,'hst':'tshost'})					
            self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c0000??00')+'Page Suivante','url':urlo,'page':page+1,'mode':'50'})



    def showelms(self,cItem):
        url=cItem['url']
        title_=cItem['title']
        sts, data = self.getPage(url)
        if sts:
            Liste_films_data = re.findall('id="EmbedScmain"', data, re.S)
            if Liste_films_data:
                self.addVideo({'import':cItem['import'],'category' : 'host2','title':title_,'url':url,'desc':'','icon':cItem['icon'],'hst':'tshost','good_for_fav':True})	
            else:
                Liste_films_data = re.findall('BlockItem">.*?href="(.*?)".*?<img.*?src="(.*?)"(.*?)RestInformation">(.*?)</ul.*?InfoEndBlock">(.*?)</ul.*?Title">(.*?)<', data, re.S)
                for (url1,image,desc0,desc1,desc2,name_eng) in Liste_films_data:
                    name_eng=self.cleanHtmlStr(name_eng.strip())
                    desc = self.get_desc(desc0,desc1,desc2)
                    desc3,titre = self.uniform_titre(name_eng,-1)
                    desc = desc3 + desc
                    image=self.std_url(image)
                    if 'الموسم' in name_eng: 
                        self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'icon':image,'desc':desc,'mode':'31','good_for_fav':True,'EPG':True,'hst':'tshost'})					
                    else:
                        self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'icon':image,'desc':desc,'good_for_fav':True,'EPG':True,'hst':'tshost'})						

    def SearchResult(self,str_ch,page,extra):
        if self.defaut_mobile:
            url_=self.MAIN_URL_MOBILE+'/?s='+str_ch+'&page='+str(page)
            url_=self.std_url(url_)			
            sts, data = self.getPage(url_)
            if sts:
                Liste_films_data = re.findall('<li class="grid-item.*?href="(.*?)".*?src="(.*?)".*?Title">(.*?)<', data, re.S)
                for (url1,image,name_eng) in Liste_films_data:
                    image=self.std_url(image)
                    desc,titre = self.uniform_titre(name_eng.strip(),-1)
                    self.addVideo({'import':extra,'category' : 'video','title':titre,'url':url1,'icon':image,'desc':desc,'good_for_fav':True,'hst':'tshost'})					
        else:
            url_=self.MAIN_URL+'/search/'+str_ch+'/page/'+str(page)+'/'
            url_=self.std_url(url_)				
            sts, data = self.getPage(url_)
            if sts:
                Liste_films_data = re.findall('BlockItem">.*?href="(.*?)".*?<img.*?src="(.*?)"(.*?)RestInformation">(.*?)</ul.*?InfoEndBlock">(.*?)</ul.*?Title">(.*?)<', data, re.S)
                for (url1,image,desc0,desc1,desc2,name_eng) in Liste_films_data:
                    image=self.std_url(image)
                    name_eng=self.cleanHtmlStr(name_eng.strip())
                    desc3,titre = self.uniform_titre(name_eng,-1)
                    desc = desc3+self.get_desc(desc0,desc1,desc2)
                    self.addDir({'import':extra,'category' : 'host2','title':titre,'url':url1,'icon':image,'desc':desc,'mode':'31','good_for_fav':True,'EPG':True,'hst':'tshost'})					

        
    def get_links(self,cItem): 	
        urlTab = []
        Url=cItem['url']
        printDBG('getdata from:'+Url)
        post_data = {'watch':'1'}
        sts, data = self.getPage(Url,post_data=post_data)
        if sts:
            printDBG('data::'+data)
            #Local server
            iframe = re.findall('EmbedCode">.*?<IFRAME.*?SRC="(.*?)"',data,re.S|re.IGNORECASE)			
            if iframe:
                urlTab.append({'name':'Moshahda', 'url':iframe[0]+'|Referer='+Url, 'need_resolve':1,'type':'local'})
            # other servers		
            iframe = re.findall('<li data.*?">(.*?)<.*?srcout="(.*?)"',data,re.S|re.IGNORECASE)			
            for (server,href) in iframe:
                urlTab.append({'name':server, 'url':href, 'need_resolve':1})
            # mobile version
            iframe = re.findall('rgba\(203, 0, 44, 0.36\).*?href="(.*?)".*?ViewMovieNow">(.*?)<',data,re.S|re.IGNORECASE)			
            for (url_,titre_) in iframe:
                if 'منخفضة' in titre_: titre_='|Low| Movizland'
                if 'sd' in titre_.lower(): titre_='|SD| Movizland'
                if 'hd' in titre_.lower(): titre_='|HD| Movizland'
                if 'و حمل' in titre_: titre_='|HLS| Movizland'
                if 'تحميل' in titre_: titre_='|Download Server| Movizland'
                if '|HLS|' in titre_:
                    if False:
                        post_data = {'watch':'1'}
                        sts, data = self.getPage(url_,post_data=post_data)
                        if sts:
                            printDBG('data00='+data)	
                            iframe = re.findall('EmbedCode">.*?<IFRAME.*?SRC="(.*?)"',data,re.S|re.IGNORECASE)			
                            if iframe:
                                sts, data0 = self.getPage(iframe[0])
                                if sts:
                                    packed_ = re.findall('(eval\(.*?)</script>',data0,re.S)
                                    if packed_: 
                                        #try:
                                        packed = packed_[0].strip()
                                        printDBG('packed='+packed)
                                        unpacked = cPacker().unpack(packed)
                                        printDBG('unpacked='+unpacked)
                                        data0 = data0.replace(packed,unpacked)
                                        #except:
                                        #	printDBG('erreur: packer')			
                                    iframe = re.findall('{.{0,3}file:"(.*?)"(.*?)}',data0,re.S)
                                    for (url,label) in iframe:								
                                        if 'm3u8' in url:
                                            urlTab.append({'name':titre_, 'url':'hst#tshost#'+url, 'need_resolve':1,'type':'local'})					
                else:
                    link = strwithmeta(url_,{'Referer' : Url})	
                    urlTab.append({'name':titre_, 'url':link, 'need_resolve':0,'type':'local'})		
        return urlTab	


    def getVideos(self,videoUrl):
        urlTab = []	
        urlTab.append((videoUrl,'3'))	
        return urlTab


    def getArticle(self,cItem):
            printDBG("movizland.getVideoLinks [%s]" % cItem) 
            otherInfo1 = {}
            desc = cItem.get('desc','')
            sts, data = self.getPage(cItem['url'])
            if sts:
                lst_dat=re.findall('StoryContent">(.*?)</div>', data, re.S)
                if lst_dat: desc = tscolor('\c00????00')+'Story: '+tscolor('\c00??????')+ph.clean_html(lst_dat[0])
            icon = cItem.get('icon')
            title = cItem['title']		
            return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]


    def get_desc(self,desc0,desc1,desc2):
        desc = ''
        elm_list = re.findall('StarsIMDB">(.*?)</div>', desc0, re.S)
        if elm_list:
            if 'n/A' not in elm_list[0]:
                desc=desc+tscolor('\c00????00')+'IMDB: '+tscolor('\c00??????')+ph.clean_html(elm_list[0])+'\n'				
        
        elm_list = re.findall('fa-film">(.*?)</li>', desc1, re.S)
        if elm_list: 
            if 'n/A' not in elm_list[0]:
                desc=desc+tscolor('\c00????00')+'Genre: '+tscolor('\c00??????')+ph.clean_html(elm_list[0].replace('</span>','|'))+'\n'	
        elm_list = re.findall('desktop">(.*?)</li>', desc1, re.S)
        if elm_list: desc=desc+tscolor('\c00????00')+'Quality: '+tscolor('\c00??????')+ph.clean_html(elm_list[0])+'\n'
        elm_list = re.findall('<li>.*?<span>(.*?)</span>(.*?)</li>', desc2, re.S)
        for (tt,vv) in elm_list:
            if 'سنة' in tt: desc=desc+tscolor('\c00????00')+'Year: '+tscolor('\c00??????')+ph.clean_html(vv)+'\n'
            if 'الإشراف' in tt: desc=desc+tscolor('\c00????00')+'Type: '+tscolor('\c00??????')+ph.clean_html(vv)+'\n'
            if 'دولة' in tt: desc=desc+tscolor('\c00????00')+'Country: '+tscolor('\c00??????')+ph.clean_html(vv)+'\n'
        return desc

            
    def start(self,cItem):      
        mode=cItem.get('mode', None)
        if mode=='00':
            self.showmenu0(cItem)
        if mode=='20':
            self.showmenu1(cItem)
        if mode=='21':
            self.showfilter(cItem)
        if mode=='30':
            self.showitms(cItem)
        if mode=='31':
            self.showelms(cItem)
        if mode=='40':
            self.showmenu10(cItem)	
        if mode=='50':
            self.showitms_mobile(cItem)				
        return True

