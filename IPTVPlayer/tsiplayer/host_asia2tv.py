# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit       import SetIPTVPlayerLastHostError
import re,urllib,time

def getinfo():
    info_={}
    name = 'Asia2tv'
    hst = tshost(name)	
    if hst=='': hst = 'https://asia2tv.cn'
    info_['host']= hst
    info_['name']=name
    info_['version']='1.4 20/02/2020'
    info_['dev']='RGYSoft'
    info_['cat_id']='99'
    info_['desc']='أفلام و مسلسلات آسياوية'
    info_['icon']='https://i.ibb.co/MpXLVK8/x2p8y3u4.png'
    info_['recherche_all']='1'
    info_['update']='Fix cover' 
    return info_
    
    
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'asia2tv_.cookie'})
        #self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
        self.MAIN_URL = getinfo()['host']
        #self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        #self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

    def showmenu0(self,cItem):
        hst='host2'
        img=cItem['icon']
        asia_TAB=[ 			
                    {'category':hst,'title': 'الحلقات الجديدة',   'mode':'30' ,'icon':img ,'url':self.MAIN_URL+'/newepisode'},
                    {'category':hst,'title': 'الدراما المجانية',  'mode':'30' ,'icon':img ,'url':self.MAIN_URL+'/series/free'},	
                    {'category':hst,'title': 'الأفلام المجانية',    'mode':'30' ,'icon':img ,'url':self.MAIN_URL+'/movies/free'},
                    {'category':hst,'title': tscolor('\c0000????') + 'حسب الحالة',      'mode':'20' ,'icon':img ,'sub_mode':1},
                    {'category':'search'  ,'title':tscolor('\c00????30') + _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':img},
                    ]
        self.listsTab(asia_TAB, {'import':cItem['import'],'name':hst})
        
    def showmenu1(self,cItem):		
        gnr2=cItem['sub_mode']
        sts, data = self.getPage(self.MAIN_URL)			
        if sts:
            Liste_films_data = re.findall('<ul>(.*?)</ul>', data, re.S)
            if Liste_films_data:
                Liste_films_data0 = re.findall('<li.*?href="(.*?)".*?>(.*?)<', Liste_films_data[1], re.S)
                for (url,titre) in Liste_films_data0:
                    self.addDir({'import':cItem['import'],'name':'categories', 'category' :'host2', 'url':url, 'title':self.cleanHtmlStr( titre), 'desc':'', 'icon':cItem['icon'], 'mode':'30'})						
        
    def showitms(self,cItem):	
        desc = [('Info','serie-isstatus.*?>(.*?)</span>','',''),('Rating','review_avg">(.*?)</div>','',''),('Date','post-date">(.*?)</div>','','')]
        next = ['<li class="active">.{1,30}<li>.*?href="(.*?)"','30']
        self.add_menu(cItem,'','(?:class="postmovie">|class="recent-movie)(.*?)href="(.*?)".*?src="(.*?)".*?<h4>(.*?)</h4>(.*?)<div>','','31',ord=[1,3,2,0,4],Desc=desc,Next=next,u_titre=True,EPG=True)		

    def showelems(self,cItem):	
        self.add_menu(cItem,'','class="episode_box.*?href="(.*?)".*?titlepisode">(.*?)<','','video',ord=[0,1],EPG=True)		

    def SearchResult(self,str_ch,page,extra):
        url = self.MAIN_URL+'/search?s='+str_ch+'&page='+str(page)
        desc = [('Info','serie-isstatus.*?>(.*?)</span>','',''),('Rating','review_avg">(.*?)</div>','',''),('Date','post-date">(.*?)</div>','','')]
        self.add_menu({'import':extra,'url':url},'','(?:class="postmovie">|class="recent-movie)(.*?)href="(.*?)".*?src="(.*?)".*?<h4>(.*?)</h4>(.*?)<div>','','31',ord=[1,3,2,0,4],Desc=desc,u_titre=True,EPG=True)
            
    def getArticle(self, cItem):
        printDBG("Asia2tv.getVideoLinks [%s]" % cItem) 
        otherInfo1 = {}
        desc = ''
        sts, data = self.cm.getPage(cItem['url'])
        if sts:
            lst_dat=re.findall('info-detail-single">(.*?)</ul>(.*?)</div>(.*?)</p>', data, re.S)
            if lst_dat:
                lst_dat0=re.findall('sdhdfhd">(.*?)</div>', lst_dat[0][0], re.S)
                if lst_dat0: otherInfo1['quality'] = ph.clean_html(lst_dat0[0])
                lst_dat0=re.findall('post_imdb">(.*?)</div>', lst_dat[0][0], re.S)
                if lst_dat0: otherInfo1['imdb_rating'] = ph.clean_html(lst_dat0[0])		
                lst_dat0=re.findall('box-date">(.*?)</div>', lst_dat[0][0], re.S)
                if lst_dat0: otherInfo1['age_limit'] = ph.clean_html(lst_dat0[0])				
                lst_dat0=re.findall('<li>(.*?)</span>(.*?)</', lst_dat[0][0], re.S)
                for (x1,x2) in lst_dat0:
                    if 'اسم المسلسل'  in x1: otherInfo1['original_title'] = x2
                    if 'الاسم بالعربي' in x1: otherInfo1['alternate_title'] = x2
                    if 'الحلقات'      in x1: otherInfo1['episodes'] = x2
                    if 'البلد'        in x1: otherInfo1['country'] = ph.clean_html(x2)
                    if 'موعد البث'    in x1: otherInfo1['first_air_date'] = x2
                otherInfo1['genre'] = ph.clean_html(lst_dat[0][1])	
                desc = ph.clean_html(lst_dat[0][2])	
        icon = cItem.get('icon')
        title = cItem['title']		
        return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

    def get_links(self,cItem): 	
        urlTab = []
        URL=cItem['url']
        sts, data = self.getPage(URL)
        if sts:
            token_ = re.findall('_token.{1,5}value="(.*?)"', data, re.S)
            if token_: token = token_[0]
            else: token = ''
            Liste_els = re.findall('<ul class="server(.*?)</ul>', data, re.S)
            if Liste_els:
                Liste_els = re.findall('<li.*?data-code="(.*?)".*?>(.*?)</li>', Liste_els[0], re.S)
                for (Url,host_) in Liste_els:
                    if host_ != '..':
                        type_=''
                        if 'VIP' not in host_:
                            if 'golden' in host_.lower(): host_='feurl.com'
                            elif 'okru' in host_.lower(): host_='ok.ru'
                            elif 'upto' in host_.lower(): host_='uptobox'
                            elif 'tunepk' in host_.lower(): host_='tunepk'
                            elif 'asia2' in host_.lower():
                                host_='|LOCAL| Asia2Tv'
                                type_='local'
                            else: host_= ph.clean_html(host_)
                            urlTab.append({'name':host_, 'url':'hst#tshost#'+Url+'|'+token, 'need_resolve':1,'type':type_})
                        
        return urlTab


    def getVideos(self,videoUrl):
        urlTab = []	
        videoUrl,token = videoUrl.split('|',1)
        Url = self.MAIN_URL+'/ajaxGetRequest'		
        addParams = dict(self.defaultParams)
        addParams['header']['X-CSRF-TOKEN'] = token
        post_data = {'action':'iframe_server','code':videoUrl}
        sts, data = self.getPage(Url,addParams,post_data=post_data)
        if sts:
            printDBG('dddddaaaaattttaaaaa'+data)
            _data2 = re.findall('src.{1,3}["\'](.*?)["\']',data, re.S|re.IGNORECASE)
            if _data2:
                URL_=_data2[0].replace('\\/','/').replace('\\','')
                printDBG('URL_'+URL_)
                if URL_.startswith('//'): URL_='http:'+URL_
                if 'vip.png' not in URL_:
                    urlTab.append((URL_,'1'))
                else:
                    SetIPTVPlayerLastHostError('Only VIP')
        return urlTab                
            

         
    def getVideos2(self,videoUrl):
        urlTab = []	
        Url = self.MAIN_URL+'/'+videoUrl		
        sts, data = self.getPage(Url)
        if sts:
            printDBG('dddddaaaaattttaaaaa'+data)
            _data2 = re.findall('<iframe.*?src=["\'](.*?)["\']',data, re.S|re.IGNORECASE)
            if _data2:
                printDBG('01')
                URL_=_data2[0]
                if URL_.startswith('//'):
                    URL_='http:'+URL_
                urlTab.append((URL_,'1'))
            else:
                printDBG('02')
                _data2 = re.findall('<body>.*?src=["\'](.*?)["\']',data, re.S|re.IGNORECASE)
                if _data2:
                    printDBG('03')
                    URL_=_data2[0]
                    if URL_.startswith('//'):
                        URL_='http:'+URL_
                    urlTab.append((URL_,'1'))
                else:
                    printDBG('04')
                    if 'https://asiatv.cc/userpro/' in data:
                        SetIPTVPlayerLastHostError('Only premium users!!')
                
        return urlTab

            
    def start(self,cItem):      
        mode=cItem.get('mode', None)
        if mode=='00':
            self.showmenu0(cItem)
        if mode=='20':
            self.showmenu1(cItem)
        if mode=='30':
            self.showitms(cItem)			
        if mode=='31':
            self.showelems(cItem)
