# -*- coding: utf-8 -*-
###################################################
# 2019-12-19 by Alec - modified Filmgo
###################################################
HOST_VERSION = "1.2"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, rm, GetTmpDir, GetIPTVPlayerVerstion, MergeDicts
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs import ph
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import re
import urllib
import random
import os
import datetime
import time
import zlib
import cookielib
import base64
import traceback
from copy import deepcopy
try:
    import json
except Exception:
    import simplejson as json
from Components.config import config, ConfigText, ConfigYesNo, getConfigListEntry
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS
from datetime import datetime
from hashlib import sha1
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.filmgo_id = ConfigYesNo(default = False)
config.plugins.iptvplayer.boxtipus = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.boxrendszer = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("id:", config.plugins.iptvplayer.filmgo_id))
    return optionList
###################################################

def gettytul():
    return 'https://filmgo.cc/'

class Filmgo(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'filmgo', 'cookie':'filmgo.cookie'})
        self.DEFAULT_ICON_URL = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1U/LzMlNz4/PyU/P1yvISwcAfT0RGA=='))
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'
        self.HEADER = self.cm.getDefaultHeader()
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://filmgo.cc/'
        self.vivn = GetIPTVPlayerVerstion()
        self.porv = self.gits()
        self.pbtp = '-'
        self.btps = config.plugins.iptvplayer.boxtipus.value
        self.brdr = config.plugins.iptvplayer.boxrendszer.value
        self.aid = config.plugins.iptvplayer.filmgo_id.value
        self.aid_ki = ''
        self.ilk = False
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}        

    def getFullIconUrl(self, url):
        return CBaseHostClass.getFullIconUrl(self, url.replace('&amp;', '&'))

    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
        
    def listMainMenu(self, cItem):
        try:
            if not self.ebbtit(): return
            if self.btps != '' and self.brdr != '': self.pbtp = self.btps.strip() + ' - ' + self.brdr.strip()
            tab_movies = 'filmgo_filmek'
            desc_movies = self.getdvdsz(tab_movies, 'Filmek megjelenítése...')
            tab_series = 'filmgo_sorozatok'
            desc_series = self.getdvdsz(tab_series, 'Sorozatok megjelenítése...')
            tab_ajanlott = 'filmgo_ajanlott'
            desc_ajanlott = self.getdvdsz(tab_ajanlott, 'Ajánlott, nézett tartalmak megjelenítése...')
            tab_keresett = 'filmgo_keresett_tartalom'
            desc_keresett = self.getdvdsz(tab_keresett, 'Keresett tartalmak megjelenítése...')
            tab_search = 'filmgo_kereses'
            desc_search = self.getdvdsz(tab_search, 'Keresés...')
            tab_search_hist = 'filmgo_kereses_elozmeny'
            desc_search_hist = self.getdvdsz(tab_search_hist, 'Keresés az előzmények között...')
            MAIN_CAT_TAB = [
                            {'category':'list_movies', 'title': _('Movies'), 'url': zlib.decompress(base64.b64decode('eJzLKCkpKLbS10/LzMlNz9dLTtbPz8vJzEvVBQmkZgMAt74Llw==')), 'tps':'1', 'tab_id':tab_movies, 'desc':desc_movies },
                            {'category':'list_series', 'title': _('Series'), 'url': zlib.decompress(base64.b64decode('eJzLKCkpKLbS10/LzMlNz9dLTtbPz8vJzEvVLc4vyq9KLMnPBgDeRA0L')), 'tps':'2', 'tab_id':tab_series, 'desc':desc_series },
                            {'category':'list_main', 'title': 'Ajánlott, nézett tartalmak', 'tab_id':tab_ajanlott, 'desc':desc_ajanlott },
                            {'category':'list_main', 'title': 'Keresett tartalmak', 'tab_id':tab_keresett, 'desc':desc_keresett },
                            {'category':'search', 'title': _('Search'), 'search_item':True, 'tps':'0', 'tab_id':tab_search, 'desc':desc_search },
                            {'category':'search_history', 'title': _('Search history'), 'tps':'0', 'tab_id':tab_search_hist, 'desc':desc_search_hist } 
                           ]
            self.listsTab(MAIN_CAT_TAB, {'name':'category'})
            vtb = self.malvadnav(cItem, '7', '13', '0', '14')
            if len(vtb) > 0:
                for item in vtb:
                    item['category'] = 'list_third'
                    self.addVideo(item)
            self.ilk = True
        except Exception:
            return
            
    def _listCategories(self, cItem, nextCategory, mode):
        try:
            sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
            if not sts: return
            if len(data) == 0: return
            tn = self.cm.ph.getDataBeetwenMarkers(data, "token: '", "'", False)[1]
            if len(tn) == 0: return
            data = self.cm.ph.getDataBeetwenMarkers(data, '<select name="genres"', '</select>')[1]
            if len(data) == 0: return
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<option', '/option>')
            if len(data) == 0: return
            for item in data:
                p_v = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                p_v = p_v.replace('héború','háború')
                if p_v == '':
                    url = zlib.decompress(base64.b64decode('eJwFwUsKgCAQANDbuGysXYF0haD2Mchkkp9BhyDEu/feLcJ1Abh8iC4P1oJ4CVSB0fmEQusp+aFkmu6KqWzoyEyzko/JtLErfNGHI+9SCKPRP7AeHU0=')).format(tn,mode)
                else:
                    url = zlib.decompress(base64.b64decode('eJwFwU0KwyAQBtDbuKw2uwaGXKHQ7EIJg3wxUv/QoRDEu+e9U6S0WevDh+jyw1otXgKaLux8YsGyS/4hUTdDFdQ3O9D0UnIVUH8O5ZAq2valPg3Ff/ZhzR+p4EjmBk8fIhY=')).format(tn,mode,p_v)
                title = self.cm.ph.getDataBeetwenMarkers(item, '>', '</', False)[1]
                title = title.replace('Héború','Háború')
                params = dict(cItem)
                params['desc'] = ''
                params.update({'category':nextCategory, 'title':title, 'url':url, 'md':mode})
                self.addDir(params)
        except Exception:
            return
        
    def listMovies(self, cItem, nextCategory):
        tabID = cItem['tab_id']
        if tabID != '':
            self.susn('2', '13', tabID)
        self._listCategories(cItem, nextCategory, 'movie')
        
    def listSeries(self, cItem, nextCategory):
        tabID = cItem['tab_id']
        if tabID != '':
            self.susn('2', '13', tabID)
        self._listCategories(cItem, nextCategory, 'series')
        
    def listSort(self, cItem, nextCategory):
        url = cItem['url']
        S_CAT_TAB = [{'category':nextCategory, 'title': 'Legfrisebb dátumú', 'url': url + '&order=release_dateDesc', 'desc': ''},
                     {'category':nextCategory, 'title': 'Legnézettebb', 'url': url + '&order=viewsDesc', 'desc': ''},
                     {'category':nextCategory, 'title': 'Legutóbb hozzáadott', 'url': url + '&order=idDesc', 'desc': ''},
                     {'category':nextCategory, 'title': 'Legjobb értékelésű', 'url': url + '&order=tmdb_ratingDesc', 'desc': ''}
                     #{'category':nextCategory, 'title': 'Név sorrend', 'url': url + '&order=titleAsc', 'desc': ''}
                    ]
        self.listsTab(S_CAT_TAB, cItem)
        
    def listItems(self, cItem, nextCategory):
        nextPage = False
        link_tmb = {}
        try:
            tuhe = cItem['url']
            page = cItem.get('page', 1)
            tumd = cItem['md']
            if tuhe != '':
                tuhe = tuhe + '&page=' + str(page)
                sts, data = self.cm.getPage(tuhe)
                if not sts: return
                if len(data) == 0: return
                data = json_loads(data)
                if len(data) > 0:
                    pg = int(data['page'])
                    ppg = int(data['perPage'])
                    titms = data['totalItems']
                    if titms > pg * ppg:
                        nextPage = True
                    dtitms = data.get('items', [])
                    if len(dtitms) > 0:
                        for item in dtitms:
                            id = item['id']
                            if id == '': continue
                            title = item['title']
                            if title == '': continue
                            leiras = item['plot']
                            if leiras != '':
                                leiras_rov = re.sub(r'^(.{400}).*$', '\g<1>...', leiras.replace('\n','').strip())
                            else:
                                leiras_rov = ' '
                            link_nyelv = item['link_nyelv']
                            if link_nyelv == None: link_nyelv = ' '
                            imdb_rating = item['imdb_rating']
                            if imdb_rating == None: imdb_rating = ' '
                            runtime = item['runtime']
                            if runtime == None: runtime = ' '
                            views = item['views']
                            if views == None: views = 1
                            release_date = item['release_date']
                            if release_date == None: release_date = ' '
                            genre = item['genre']
                            if genre == None: genre = ' '
                            icon = item['poster']
                            desc = link_nyelv + '\nMűfaj:  ' + genre + '\nKiadási dátum:  ' + release_date + '  |  Hossz:  ' + runtime + '  |  Nézettség:  ' + str(views) + '  |  IMDB pont:  ' + imdb_rating + '\n\n' + leiras_rov
                            if tumd == 'series':
                                furl = zlib.decompress(base64.b64decode('eJzLKCkpKLbS10/LzMlNz9dLTtbPz8vJzEvVLc4vyq9KLMnP1gcA634NOg==')) + str(id) + '-'
                                params = MergeDicts(cItem, {'category':'list_evad', 'id':id, 'title':title, 'url':furl, 'desc':desc, 'icon':icon, 'leiras':leiras})
                            else:
                                furl = zlib.decompress(base64.b64decode('eJzLKCkpKLbS10/LzMlNz9dLTtbPz8vJzEvVBQmkZusDAMOEC8Y=')) + str(id) + '-'
                                params = MergeDicts(cItem, {'category':nextCategory, 'id':id, 'title':title, 'url':furl, 'desc':desc, 'icon':icon, 'leiras':leiras})
                            self.addDir(params)
                        if nextPage and len(self.currList) > 0:
                            params = dict(cItem)
                            params.update({'title':_("Next page"), 'page':page+1, 'desc':'Nyugi...\nVan még további tartalom, lapozz tovább!!!'})
                            self.addDir(params)
        except Exception:
            return
            
    def exploreItem(self, cItem):
        try:
            if len(cItem) > 0:
                sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
                if not sts: return
                if len(data) == 0: return
                jtmb = self.cm.ph.getDataBeetwenMarkers(data, "vars.title = {", "};", False)[1].strip()
                if len(jtmb) == 0: return
                leiras = cItem['leiras']
                if leiras != '':
                    leiras = re.sub(r'^(.{1000}).*$', '\g<1>...', leiras.replace('\n','').strip())
                params = MergeDicts(cItem, {'good_for_fav': True, 'title':cItem['title'], 'url':cItem['url'], 'desc':leiras, 'icon':cItem['icon']})
                self.addVideo(params)
        except Exception:
            return
            
    def listEvad(self, cItem):
        try:
            if len(cItem) > 0:
                sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
                if not sts: return
                if len(data) == 0: return
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="details-block seasons">', '</div>', False)[1]
                if len(data) == 0: return
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<button onclick=', '</button>')
                if len(data) == 0: return
                for item in data:
                    url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0]
                    if not self.cm.isValidUrl(url): continue
                    tmp_evad = self.cm.ph.getDataBeetwenMarkers(item, '</i>', '</button>', False)[1]
                    m = re.search(r'\d+',tmp_evad)
                    if m is not None:
                        evad = m.group(0)
                    if evad == '':
                        continue
                    else:
                        params = MergeDicts(cItem, {'category':'list_evad_item', 'url': cItem['url'] + '/seasons/' + str(evad), 'eretitle': cItem['title'], 'title':str(evad) + '. évad'})
                        self.addDir(params)
        except Exception:
            return
            
    def listEvadItem(self, cItem):
        try:
            if len(cItem) > 0:
                sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
                if not sts: return
                if len(data) == 0: return
                data = self.cm.ph.getDataBeetwenMarkers(data, '<h2>Online nézhető epizódok</h2>', '<div class="modal fade" id="vid-modal', False)[1]
                if len(data) == 0: return
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a href=', '</a>')
                if len(data) == 0: return
                title = cItem['eretitle'] + ' : ' + cItem['title'] + ' ::  '
                for item in data:
                    url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0]
                    if not self.cm.isValidUrl(url): continue
                    oln = self.cm.ph.getDataBeetwenMarkers(item, '<span class="online-elerheto', '</span>', False)[1]
                    if len(oln) == 0: continue
                    idx1 = url.rfind('/')
                    if -1 < idx1:
                        epzd = url[idx1+1:].strip()
                    else:
                        epzd = '1'
                    ecm = self.cm.ph.getDataBeetwenMarkers(item, '<i>', '</i>', False)[1].replace('(','').replace(')','').strip()
                    if len(ecm) == 0: ecm = ' '
                    ttlrs = self.cm.ph.getDataBeetwenMarkers(item, '<div class="episode-plot">', '</div>', False)[1]
                    if ttlrs != '':
                        leiras = re.sub(r'^(.{600}).*$', '\g<1>...', ttlrs.replace('\n','').strip())
                    else:
                        leiras = ' '
                    desc = 'Epizód címe:  ' + ecm + '\n\n' + leiras
                    params = MergeDicts(cItem, {'good_for_fav': True, 'title':title + epzd + '. epizód', 'url':url, 'desc':desc})
                    self.addVideo(params)
        except Exception:
            return
            
    def getLinksForVideo(self, cItem):
        retTab = []
        md = '1'
        try:
            if 'seasons' in cItem['url']:
                if 'episodes' in cItem['url']:
                    evad = int(self.name_find(cItem['url'],'seasons/','/episodes'))
                    epizod = int(self.name_find(cItem['url'],'episodes/',''))
                    md = '2'
                else:
                    return
            sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
            if not sts: return
            if len(data) == 0: return
            jtmb = self.cm.ph.getDataBeetwenMarkers(data, "vars.title = {", "};", False)[1].strip()
            if len(jtmb) == 0: return
            jtmb = '{' + jtmb + '}'
            data = json_loads(jtmb)
            if len(data) > 0:
                lnktmb = data.get('link',[])
                if len(lnktmb) > 0:
                    url_tmb = []
                    for item in lnktmb:
                        if md == '2':
                            if item['season'] != evad:
                                continue
                            elif item['episode'] != epizod:
                                continue
                        url_name = ''
                        if self.cm.isValidUrl(item['url']):
                            if item['url'] in url_tmb:
                                continue
                            else:
                                url_tmb.append(item['url'])
                            url_name = self.cm.getBaseUrl(item['url'])
                            url_name = self.name_find(url_name,'//','/')
                        else:
                            continue
                        if item['quality'] != '':
                            name = url_name + ' | ' + item['label'] + ' | ' + item['quality']
                        else:
                            name = url_name + ' | ' + item['label']
                        retTab.append({'name':name, 'url':item['url'], 'need_resolve':1})
            if len(retTab) > 0:
                if cItem['category'] != 'list_third':
                    self.susmrgts('2', '13', cItem['tps'], cItem['url'], cItem['title'], cItem['icon'], cItem['desc'], 'mnez')
                return retTab
            else:
                return []
        except Exception:
            return []
            
    def name_find(self, string='', start='', end=''):
        if string != '' and start !='':
            if end != '':
                return string[string.find(start) + len(start):string.rfind(end)]
            else:
                return string[string.find(start) + len(start):]
        else:
            return ''
        
    def getVideoLinks(self, videoUrl=''):
        urlTab = []
        if videoUrl != '' and self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listMainItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'filmgo_ajanlott':
                self.Fzkttm(cItem, tabID)
            elif tabID == 'filmgo_keresett_tartalom':
                self.Vdakstmk({'name':'history', 'category': 'search', 'tab_id':''}, 'desc', _("Type: "), tabID)
            else:
                return
        except Exception:
            return
            
    def Fzkttm(self, cItem, tabID):
        try:
            self.susn('2', '13', tabID)
            tab_ams = 'filmgo_ajnlt_musor'
            desc_ams = self.getdvdsz(tab_ams, 'Ajánlott, nézett tartalmak megjelenítése műsorok szerint...')
            tab_adt = 'filmgo_ajnlt_datum'
            desc_adt = self.getdvdsz(tab_adt, 'Ajánlott, nézett tartalmak megjelenítése dátum szerint...')
            tab_anzt = 'filmgo_ajnlt_nezettseg'
            desc_anzt = self.getdvdsz(tab_anzt, 'Ajánlott, nézett tartalmak megjelenítése nézettség szerint...')
            A_CAT_TAB = [{'category':'list_third', 'title': 'Dátum szerint', 'tab_id':tab_adt, 'desc':desc_adt},
                         {'category':'list_third', 'title': 'Nézettség szerint', 'tab_id':tab_anzt, 'desc':desc_anzt},
                         {'category':'list_third', 'title': 'Műsorok szerint', 'tab_id':tab_ams, 'desc':desc_ams} 
                        ]
            self.listsTab(A_CAT_TAB, cItem)
        except Exception:
            return
        
    def listThirdItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'filmgo_ajnlt_musor':
                self.Vajnltmsr(cItem)
            elif tabID == 'filmgo_ajnlt_datum':
                self.Vajnltdtm(cItem)
            elif tabID == 'filmgo_ajnlt_nezettseg':
                self.Vajnltnztsg(cItem)
            else:
                return
        except Exception:
            return
            
    def Vajnltmsr(self,cItem):
        try:
            self.susn('2', '13', 'filmgo_ajnlt_musor')
            vtb = self.malvadnav(cItem, '3', '13', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return
            
    def Vajnltdtm(self,cItem):
        vtb = []
        try:
            self.susn('2', '13', 'filmgo_ajnlt_datum')
            vtb = self.malvadnav(cItem, '4', '13', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return
            
    def Vajnltnztsg(self,cItem):
        try:
            self.susn('2', '13', 'filmgo_ajnlt_nezettseg')
            vtb = self.malvadnav(cItem, '5', '13', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return

    def listSearchResult(self, cItem, searchPattern, searchType):
        try:
            self.suskrbt('2', '13', searchPattern)
            cItem = dict(cItem)
            tuhe = zlib.decompress(base64.b64decode('eJzLKCkpKLbS10/LzMlNz9dLTtYvqSxITcxITUzRBwCXGApR')) + searchPattern
            sts, data = self.cm.getPage(tuhe)
            if not sts: return
            if len(data) == 0: return
            data = json_loads(data)
            if len(data) > 0:
                for item in data:
                    mode = item['type']
                    id = item['id']
                    title = item['title']
                    icon = item['poster']
                    leiras = item['plot']
                    if leiras != '':
                        leiras = re.sub(r'^(.{1000}).*$', '\g<1>...', leiras.replace('\n','').strip())
                    else:
                        leiras = ' '
                    desc = leiras
                    if mode == 'series':
                        furl = zlib.decompress(base64.b64decode('eJzLKCkpKLbS10/LzMlNz9dLTtbPz8vJzEvVLc4vyq9KLMnP1gcA634NOg==')) + str(id) + '-'
                        params = MergeDicts(cItem, {'category':'list_evad', 'id':id, 'title':title, 'url':furl, 'desc':desc, 'icon':icon, 'leiras':leiras})
                    else:
                        furl = zlib.decompress(base64.b64decode('eJzLKCkpKLbS10/LzMlNz9dLTtbPz8vJzEvVBQmkZusDAMOEC8Y=')) + str(id) + '-'
                        params = MergeDicts(cItem, {'category':'explore_item', 'id':id, 'title':title, 'url':furl, 'desc':desc, 'icon':icon, 'leiras':leiras})
                    self.addDir(params)
        except Exception:
            return

    def getFavouriteData(self, cItem):
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem['desc'], 'icon':cItem['icon']}
        return json_dumps(params) 
  
    def suskrbt(self, i_md='', i_hgk='', i_mpsz=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzwbywERxYklKkl5BRgEAD/4T/Q=='))
        try:
            if i_mpsz != '' and len(i_mpsz) > 1:
                if len(i_mpsz) > 80:
                    i_mpsz = i_mpsz[:78]
                i_mpsz = base64.b64encode(i_mpsz).replace('\n', '').strip()
                if i_hgk != '':
                    i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                    pstd = {'md':i_md, 'hgk':i_hgk, 'mpsz':i_mpsz}
                    if i_md != '' and i_hgk != '' and i_mpsz != '':
                        sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
            
    def susmrgts(self, i_md='', i_hgk='', i_mptip='', i_mpu='', i_mpt='', i_mpi='', i_mpdl='', i_mpnzs=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzy0tSQQTxYklKUl6BRkFABGoFBk='))
        try:
            if i_hgk != '': i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
            if i_mptip != '': i_mptip = base64.b64encode(i_mptip).replace('\n', '').strip()
            if i_mpu != '': i_mpu = base64.b64encode(i_mpu).replace('\n', '').strip()
            if i_mpt != '': i_mpt = base64.b64encode(i_mpt).replace('\n', '').strip()
            if i_mpi == '':
                i_mpi = base64.b64encode('-')
            else:
                i_mpi = base64.b64encode(i_mpi).replace('\n', '').strip()
            if i_mpdl == '':
                i_mpdl = base64.b64encode('-')
            else:
                i_mpdl = base64.b64encode(i_mpdl).replace('\n', '').strip()
            if i_mpnzs != '': i_mpnzs = base64.b64encode(i_mpnzs).replace('\n', '').strip()
            pstd = {'md':i_md, 'hgk':i_hgk, 'mptip':i_mptip, 'mpu':i_mpu, 'mpt':i_mpt, 'mpi':i_mpi, 'mpdl':i_mpdl, 'mpnzs':i_mpnzs}
            if i_md != '' and i_hgk != '' and i_mptip != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
    
    def getdvdsz(self, pu='', psz=''):
        bv = ''
        if pu != '' and psz != '':
            n_atnav = self.malvadst('1', '13', pu)
            if n_atnav != '' and self.aid:
                if pu == 'filmgo_filmek':
                    self.aid_ki = 'ID: ' + n_atnav + '  |  Filmgo  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = 'ID: ' + n_atnav + '\n'
            else:
                if pu == 'filmgo_filmek':
                    self.aid_ki = 'Filmego  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = ''
            bv = self.aid_ki + psz
        return bv
        
    def malvadst(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu}
        t_s = ''
        temp_vn = ''
        temp_vni = ''
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a_div', '</div>')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '/>')
                if len(data) == 0: return t_s
                for item in data:
                    t_i = self.cm.ph.getSearchGroups(item, 'id=[\'"]([^"^\']+?)[\'"]')[0]
                    if t_i == 'vn':
                        temp_vn = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                    elif t_i == 'vni':
                        temp_vni = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                if temp_vn != '':
                    t_s = temp_vn
            return t_s
        except Exception:
            return t_s
            
    def malvadnav(self, cItem, i_md='', i_hgk='', i_mptip='', i_mpdb=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzy0tSQQTxYklKUl6BRkFABGoFBk='))
        t_s = []
        try:
            if i_md != '' and i_hgk != '' and i_mptip != '':
                if i_hgk != '': i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                if i_mptip != '': i_mptip = base64.b64encode(i_mptip).replace('\n', '').strip()
                if i_mpdb != '': i_mpdb = base64.b64encode(i_mpdb).replace('\n', '').strip()
                pstd = {'md':i_md, 'hgk':i_hgk, 'mptip':i_mptip, 'mpdb':i_mpdb}
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a1_div"', '<div id="div_a2_div"')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="d_sor_d"', '</div>')
                if len(data) == 0: return t_s
                for temp_item in data:
                    temp_data = self.cm.ph.getAllItemsBeetwenMarkers(temp_item, '<span', '</span>')
                    if len(temp_data) == 0: return t_s
                    for item in temp_data:
                        t_vp = self.cm.ph.getSearchGroups(item, 'class=[\'"]([^"^\']+?)[\'"]')[0]
                        if t_vp == 'c_sor_u':
                            temp_u = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_u">', '</span>', False)[1]
                            if temp_u != '': temp_u = base64.b64decode(temp_u)
                        if t_vp == 'c_sor_t':
                            temp_t = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_t">', '</span>', False)[1]
                            if temp_t != '': temp_t = base64.b64decode(temp_t)
                        if t_vp == 'c_sor_i':
                            temp_i = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_i">', '</span>', False)[1]
                            if temp_i != '': temp_i = base64.b64decode(temp_i)
                        if t_vp == 'c_sor_l':
                            temp_l = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_l">', '</span>', False)[1]
                            if temp_l != '': temp_l = base64.b64decode(temp_l)
                        if t_vp == 'c_sor_n':
                            temp_n = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_n">', '</span>', False)[1]
                            if temp_n != '': temp_n = base64.b64decode(temp_n)
                        if t_vp == 'c_sor_tip':
                            temp_tp = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_tip">', '</span>', False)[1]
                            if temp_tp != '': temp_tp = base64.b64decode(temp_tp)
                    if temp_u == '' and temp_t =='': continue
                    if temp_n == '': temp_n = '1'
                    params = MergeDicts(cItem, {'good_for_fav': True, 'url':temp_u, 'title':temp_t, 'icon':temp_i, 'desc':temp_l, 'nztsg':temp_n, 'tps':temp_tp})
                    t_s.append(params)       
            return t_s
        except Exception:
            return []
            
    def susn(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu, 'hv':self.vivn, 'orv':self.porv, 'bts':self.pbtp}
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
    
    def ebbtit(self):
        try:
            if '' == self.btps.strip() or '' == self.brdr.strip():
                msg = 'A Set-top-Box típusát és a használt rendszer (image) nevét egyszer meg kell adni!\n\nA kompatibilitás és a megfelelő használat miatt kellenek ezek az adatok a programnak.\nKérlek, a helyes működéshez a valóságnak megfelelően írd be azokat.\n\nA "HU Telepítő" keretrendszerben tudod ezt megtenni.\n\nKilépek és megyek azt beállítani?'
                ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
                return False
            else:
                return True
        except Exception:
            return False
    
    def gits(self):
        bv = '-'
        tt = []
        try:
            if fileExists(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE'))):
                fr = open(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE')),'r')
                for ln in fr:
                    ln = ln.rstrip('\n')
                    if ln != '':
                        tt.append(ln)
                fr.close()
                if len(tt) == 1:
                    bv = tt[0].strip()[:-6].capitalize()
                if len(tt) == 2:
                    bv = tt[1].strip()[:-6].capitalize()
            return bv
        except:
            return '-'
            
    def malvadkrttmk(self, i_md='', i_hgk=''):
        bv = []
        ukszrz = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzwbywERxYklKkl5BRgEAD/4T/Q=='))
        try:
            if i_md != '' and i_hgk != '':
                i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                pstd = {'md':i_md, 'hgk':i_hgk}
                sts, data = self.cm.getPage(ukszrz, self.defaultParams, pstd)
                if not sts: return []
                if len(data) == 0: return []
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div>', '</div>', False)
                if len(data) == 0: return []
                for item in data:
                    if item != '':
                        bv.append(base64.b64decode(item))
            return bv
        except Exception:
            return []
        
    def Vdakstmk(self, baseItem={'name': 'history', 'category': 'search'}, desc_key='plot', desc_base=(_("Type: ")), tabID='' ):
        if tabID != '':
            self.susn('2', '13', tabID)
            
        def _vdakstmk(data,lnp=50):
            ln = 0
            for histItem in data:
                plot = ''
                try:
                    ln += 1
                    if type(histItem) == type({}):
                        pattern = histItem.get('pattern', '')
                        search_type = histItem.get('type', '')
                        if '' != search_type: plot = desc_base + _(search_type)
                    else:
                        pattern = histItem
                        search_type = None
                    params = dict(baseItem)
                    params.update({'title': pattern, 'search_type': search_type,  desc_key: plot, 'tps':'0'})
                    self.addDir(params)
                    if ln >= lnp:
                        break
                except Exception: return
            
        try:
            list = self.malvadkrttmk('1','13')
            if len(list) > 0:
                _vdakstmk(list,2)
            if len(list) > 0:
                list = list[2:]
                random.shuffle(list)
                _vdakstmk(list,48)
        except Exception:
            return
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        self.currList = []
        if name == None:
            self.listMainMenu( {'name':'category'} )
        elif category == 'list_movies':
            self.listMovies(self.currItem, 'list_sort')
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_sort')
        elif category == 'list_sort':
            self.listSort(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'list_evad':
            self.listEvad(self.currItem)
        elif category == 'list_evad_item':
            self.listEvadItem(self.currItem)
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
        elif category == 'list_main':
            self.listMainItems(self.currItem)
        elif category == 'list_third':
            self.listThirdItems(self.currItem)
        elif category in ["search", "search_next_page"]:
            if self.currItem['tab_id'] == 'filmgo_kereses':
                self.susn('2', '13', 'filmgo_kereses')
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == "search_history":
            if self.currItem['tab_id'] == 'filmgo_kereses_elozmeny':
                self.susn('2', '13', 'filmgo_kereses_elozmeny')
            self.listsHistory({'name':'history', 'category': 'search', 'tab_id':'', 'tps':'0'}, 'desc', _("Type: "))
        else:
            return
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Filmgo(), True, [])
        
    def withArticleContent(self, cItem):
        if (cItem['type'] != 'video' and cItem['category'] != 'explore_item'):
            return False
        return True
