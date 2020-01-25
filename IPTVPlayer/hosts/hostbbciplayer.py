# -*- coding: utf-8 -*-

#
#
# @Codermik release, based on @Samsamsam's E2iPlayer public.
# Released with kind permission of Samsamsam.
# All code developed by Samsamsam is the property of the Samsamsam and the E2iPlayer project,  
# all other work is © E2iStream Team, aka Codermik.  TSiPlayer is © Rgysoft, his group can be
# found here:  https://www.facebook.com/E2TSIPlayer/
#
# https://www.facebook.com/e2iStream/
#
#

from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, rm, MergeDicts
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.bbc import BBCCoUkIE

import re, urllib
from Components.config import config, getConfigListEntry

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_('Default video quality:'), config.plugins.iptvplayer.bbc_default_quality))
    optionList.append(getConfigListEntry(_('Use default video quality:'), config.plugins.iptvplayer.bbc_use_default_quality))
    optionList.append(getConfigListEntry(_('Preferred format:'), config.plugins.iptvplayer.bbc_prefered_format))
    optionList.append(getConfigListEntry(_('Use web-proxy (it may be illegal):'), config.plugins.iptvplayer.bbc_use_web_proxy))
    return optionList

def gettytul():
    return 'https://www.bbc.co.uk/iplayer'

class BBCiPlayer(CBaseHostClass):

    def __init__(self):
        CBaseHostClass.__init__(self, {'history': 'BBCiPlayer.tv', 'cookie': 'bbciplayer.cookie'})
        self.HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding': 'gzip, deflate'}
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update({'X-Requested-With': 'XMLHttpRequest'})
        self.cm.HEADER = self.HEADER
        self.defaultParams = {'header': self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.MAIN_URL = 'https://www.bbc.co.uk/'
        self.DEFAULT_ICON_URL = 'http://iplayer-web.files.bbci.co.uk/tviplayer-static-assets/10.75.0-1/img/navigation/iplayer_pink.png'
        self.HOST_VER = '2.3 (22/09/2019)'
        self.MAIN_CAT_TAB = [{'category': 'list_channels', 'title': _('Channels'), 'url': self.getFullUrl('iplayer'),'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik / SamSamSam\\n'}, 
                             {'category': 'list_categories', 'title': _('Categories'), 'url': self.getFullUrl('iplayer'),'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik / SamSamSam\\n'}, 
                             {'category': 'list_az_menu', 'title': _('A-Z'), 'url': self.getFullUrl('iplayer/a-z/'),'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik / SamSamSam\\n'}, 
                             {'category': 'list_items', 'title': _('Most Popular'), 'url': self.getFullUrl('iplayer/group/most-popular'),'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik / SamSamSam\\n'}, 
                             {'category': 'search', 'title': _('Search'), 'search_item': True, 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik / SamSamSam\\n'}, 
                             {'category': 'search_history', 'title': _('Search history'),'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik / SamSamSam\\n'}]
        self.otherIconsTemplate = 'https://raw.githubusercontent.com/vonH/plugin.video.iplayerwww/master/media/%s.png'
        self.reSrcset = re.compile('<source[^>]+?srcset=[\'"]([^\'^"]+?)[\'"]', re.I)

    def getFullUrl(self, url, baseUrl=None):
        return CBaseHostClass.getFullUrl(self, url, baseUrl).replace('&amp;', '&')

    def listAZMenu(self, cItem, nextCategory):
        characters = [
         ('A', 'a'), ('B', 'b'), ('C', 'c'), ('D', 'd'), ('E', 'e'), ('F', 'f'),
         ('G', 'g'), ('H', 'h'), ('I', 'i'), ('J', 'j'), ('K', 'k'), ('L', 'l'),
         ('M', 'm'), ('N', 'n'), ('O', 'o'), ('P', 'p'), ('Q', 'q'), ('R', 'r'),
         ('S', 's'), ('T', 't'), ('U', 'u'), ('V', 'v'), ('W', 'w'), ('X', 'x'),
         ('Y', 'y'), ('Z', 'z'), ('0-9', '0-9')]

        for title, url in characters:
            params = {'good_for_fav': True, 'category': nextCategory, 'title': title, 'url': cItem['url'] + url,'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}
            self.addDir(params)

    def listItems2(self, cItem, nextCategory):
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts:
            return

        cUrl = self.cm.meta['url']
        nextPage = ph.find(data, ('<a','>','Next Page'))[1]
        nextPage = self.getFullUrl(ph.search(nextPage, ph.A)[1], cUrl)
        data = ph.find(data, ('<ul', '>', 'gel-layout'), '</ul>', flags=0)[1]
        self.currList = self.getItems(cItem, nextCategory, data)		
        if nextPage:
            params = MergeDicts(cItem, {'good_for_fav': False, 'title': _('Next page'), 'url': nextPage, 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'})
            self.addDir(params)

    def getItems(self, cItem, nextCategory, data):
        retList = []
        data = ph.findall(data, '<li','</li>')
        for item in data:
            title = ph.clean_html(ph.find(item, ('<p', '>', 'title'), '</p>', flags=0)[1])
            if not title:
                title = ph.clean_html(ph.find(item, ('<div', '>', 'title'), '</div>', flags=0)[1])
            url = ph.search(item, ph.A)[1]
            icon = ph.search(item, self.reSrcset)[0]
            desc = []
            for key in (('div', 'sublabels'), ('p', 'synopsis')):
                tmp = ph.clean_html(ph.find(item, ('<%s' % key[0], '>', key[1]), '</%s>' % key[0], flags=0)[1])
                if tmp:
                    desc.append(tmp)
            
            if '/brand/' in url:
                url = url.replace('/brand/', '/episodes/')
                
            params = MergeDicts(cItem, {'good_for_fav': False, 'title': title, 'url': self.getFullUrl(url), 'desc': ('[/br]').join(desc), 'icon': self.getFullIconUrl(icon)})

            if nextCategory != 'video' and ('/episodes/' in url or '/episode/' in url):
                params['category'] = nextCategory
            else:
                params.update({'good_for_fav': True, 'type': 'video'})		
                
            retList.append(params)
        return retList

    def listEpisodes(self, cItem):
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts: return
        tmpurl = cItem['url']          
        # if we are not already viewing all we need to grab the url and load it up.
        hadViewAll = False
        viewAllUrl = ph.rfind(data, '>View all', '<a', flags=ph.I | ph.START_E | ph.END_E)[1]
        viewAllUrl = self.getFullUrl(ph.search(viewAllUrl, ph.A)[1], self.cm.meta['url'])        
        if viewAllUrl:
            sts, data = self.cm.getPage(viewAllUrl, self.defaultParams)
            if not sts: return
            tmpurl = viewAllUrl
            hadViewAll = True
        nextPage = ph.find(data, ('<a', '>', 'Next Page'))[1]
        nextPage = self.getFullUrl(ph.search(nextPage, ph.A)[1], tmpurl)
        if 'class="button series-nav__button series-nav__button' in data:
            # we have a season navigation
            block = self.cm.ph.getAllItemsBeetwenNodes(data,'class="button series-nav__button series-nav__button', ('</li>'))
            for series in block:
                seriesTitle = self.cm.ph.getAllItemsBeetwenNodes(series,'<span class="button__text typo typo--bullfinch typo--bold">', '</span>',False)[0]
                self.addMarker({'title':'\c0000??00'+seriesTitle,'desc':seriesTitle})  
                seriesUrl = self.cm.ph.getSearchGroups(series, 'href="([^"]+?)"')[0]
                if seriesUrl == '': seriesUrl = tmpurl    # add landing url (season 1)  
                else: seriesUrl = self.MAIN_URL + seriesUrl[:0] + seriesUrl[1:]
                icon = ph.search(series, self.reSrcset)[0]
                # get the page as per the url, read the episodes.
                sts, data = self.cm.getPage(seriesUrl, self.defaultParams)
                if not sts: return
                episodes = self.cm.ph.getAllItemsBeetwenNodes(data,'<ul class="gel-layout">', '</ul>')[0]
                episodes = self.cm.ph.getAllItemsBeetwenNodes(episodes,'<li class="grid__item', '</li>')  
                for episode in episodes:
                    tmpTitle = self.cleanHtmlStr(self.cm.ph.getAllItemsBeetwenNodes(episode,'<div class="content-item__title typo typo--skylark typo--bold">', '</div>', False)[0])
                    title = '%s - %s' %(cItem['title'],tmpTitle)
                    videoUrl = self.cm.ph.getSearchGroups(episode, 'href="([^"]+?)"')[0]
                    videoUrl = self.MAIN_URL + videoUrl[:0] + videoUrl[1:]                    
                    desc = self.cm.ph.getAllItemsBeetwenNodes(episode,'<div class="content-item__description typo typo--bullfinch">', '<',False)[0] + '...'
                    desc = '\c00????00Description: \c00??????'+desc
                    params = MergeDicts(cItem, {'good_for_fav': True, 'title': ph.clean_html(title), 'url': videoUrl, 'desc': desc, 'icon': self.getFullIconUrl(icon)})
                    self.addVideo(params)
        elif '/episodes/' in tmpurl and hadViewAll:
            episodes = self.cm.ph.getAllItemsBeetwenNodes(data,'<ul class="gel-layout">', '</ul>')[0]
            episodes = self.cm.ph.getAllItemsBeetwenNodes(episodes,'<li class="grid__item', '</li>')  
            seriesTitle = self.cm.ph.getAllItemsBeetwenNodes(data,'<h1 class="hero-header__title typo typo--bold typo--buzzard">', '</h1>',False)[0]
            icon = ph.search(data, self.reSrcset)[0]
            for episode in episodes:
                tmpTitle = self.cleanHtmlStr(self.cm.ph.getAllItemsBeetwenNodes(episode,'<div class="content-item__title typo typo--skylark typo--bold">', '</div>',False)[0])
                title = '%s - %s'%(seriesTitle, tmpTitle)
                videoUrl = self.cm.ph.getSearchGroups(episode, 'href="([^"]+?)"')[0]
                videoUrl = self.MAIN_URL + videoUrl[:0] + videoUrl[1:]
                desc = self.cm.ph.getAllItemsBeetwenNodes(episode,'<div class="content-item__description typo typo--bullfinch">', '<',False)[0] + '...'
                desc = '\c00????00Description: \c00??????'+desc
                params = MergeDicts(cItem, {'good_for_fav': True, 'title': ph.clean_html(title), 'url': videoUrl, 'desc': desc, 'icon': self.getFullIconUrl(icon)})
                self.addVideo(params)
        elif '/episode/' in tmpurl and not hadViewAll:
            icon = ph.search(data, self.reSrcset)[0]
            title = ph.clean_html(self.cm.ph.getAllItemsBeetwenNodes(data, '<h1 class="tvip-hide">', '</h1>',False)[0])
            desc = self.cm.ph.getAllItemsBeetwenNodes(data, '<p class="synopsis__paragraph">', '<',False)[0]
            desc = '\c00????00Description: \c00??????' + desc
            params = MergeDicts(cItem, {'good_for_fav': True, 'title': title, 'url': tmpurl, 'desc': desc, 'icon': self.getFullIconUrl(icon)})
            self.addVideo(params)
            block = self.cm.ph.getAllItemsBeetwenNodes(data, '<li class="related-episodes__item', '</li>')
            seriesTitle = self.cm.ph.getAllItemsBeetwenNodes(data, '<span class="typo typo--bold play-cta__title typo--buzzard">', '</span>',False)[0] 
            for episodes in block:
                if 'Description: This episode' in episodes: continue
                desc = self.cm.ph.getAllItemsBeetwenNodes(episodes, 'aria-label="', '"',False)[0]
                tmp = desc.split('Description: ')
                title = seriesTitle + ' - ' + ph.clean_html(tmp[0])
                desc = tmp[1]
                videoUrl = self.cm.ph.getSearchGroups(episodes, 'href="([^"]+?)"')[0] 
                videoUrl = self.MAIN_URL + videoUrl[:0] + videoUrl[1:]
                desc = '\c00????00Description: \c00??????'+desc
                params = MergeDicts(cItem, {'good_for_fav': True, 'title': title, 'url': videoUrl, 'desc': desc, 'icon': self.getFullIconUrl(icon)})
                self.addVideo(params)
        if nextPage:
            params = MergeDicts(cItem, {'good_for_fav': False, 'title': _('Next page'), 'url': nextPage})
            self.addDir(params)

    def listLive(self, cItem):
        channel_list = [
         ('bbc_one_hd', 'BBC One'),
         ('bbc_two_hd', 'BBC Two'),
         ('bbc_four_hd', 'BBC Four'),
         ('cbbc_hd', 'CBBC'),
         ('cbeebies_hd', 'CBeebies'),
         ('bbc_news24', 'BBC News Channel'),
         ('bbc_parliament', 'BBC Parliament'),
         ('bbc_alba', 'Alba'),
         ('s4cpbs', 'S4C'),
         ('bbc_one_london', 'BBC One London'),
         ('bbc_one_scotland_hd', 'BBC One Scotland'),
         ('bbc_one_northern_ireland_hd', 'BBC One Northern Ireland'),
         ('bbc_one_wales_hd', 'BBC One Wales'),
         ('bbc_two_scotland', 'BBC Two Scotland'),
         ('bbc_two_northern_ireland_digital', 'BBC Two Northern Ireland'),
         ('bbc_two_wales_digital', 'BBC Two Wales'),
         ('bbc_two_england', 'BBC Two England'),
         ('bbc_one_cambridge', 'BBC One Cambridge'),
         ('bbc_one_channel_islands', 'BBC One Channel Islands'),
         ('bbc_one_east', 'BBC One East'),
         ('bbc_one_east_midlands', 'BBC One East Midlands'),
         ('bbc_one_east_yorkshire', 'BBC One East Yorkshire'),
         ('bbc_one_north_east', 'BBC One North East'),
         ('bbc_one_north_west', 'BBC One North West'),
         ('bbc_one_oxford', 'BBC One Oxford'),
         ('bbc_one_south', 'BBC One South'),
         ('bbc_one_south_east', 'BBC One South East'),
         ('bbc_one_west', 'BBC One West'),
         ('bbc_one_west_midlands', 'BBC One West Midlands'),
         ('bbc_one_yorks', 'BBC One Yorks')]

        for id, title in channel_list:
            params = {'good_for_fav': True, 'title': title, 'url': self.getFullUrl('vpid/' + id + '/'), 'icon': self.otherIconsTemplate % id, 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}
            self.addVideo(params)

    def listChannels(self, cItem, nextCategory):
        params = {'good_for_fav': True, 'category': 'live_streams', 'title': _('Live'), 'icon': 'https://raw.githubusercontent.com/vonH/plugin.video.iplayerwww/master/media/live.png', 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}
        self.addDir(params)
        channel_list = [
         ('bbcone', 'bbc_one_hd', 'BBC One'),
         ('bbctwo', 'bbc_two_hd', 'BBC Two'),
         ('tv/bbcthree', 'bbc_three_hd', 'BBC Three'),
         ('bbcfour', 'bbc_four_hd', 'BBC Four'),
         ('tv/cbbc', 'cbbc_hd', 'CBBC'),
         ('tv/cbeebies', 'cbeebies_hd', 'CBeebies'),
         ('tv/bbcnews', 'bbc_news24', 'BBC News Channel'),
         ('tv/bbcparliament', 'bbc_parliament', 'BBC Parliament'),
         ('tv/bbcalba', 'bbc_alba', 'Alba'),
         ('tv/s4c', 's4cpbs', 'S4C')]

        for url, icon, title in channel_list:
            params = {'good_for_fav': True, 'category': nextCategory, 'title': title, 'url': self.getFullUrl(url), 'icon': self.otherIconsTemplate % icon, 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}
            self.addDir(params)

    def listChannelMenu(self, cItem, nextCategory1, nextCategory2):
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts:
            return
        data = ph.findall(data, ('<section', '>', 'aria-label'), '</section>')
        for section in data:
            tmp = ph.find(section, ('<div', '>', 'section__header'), '</div>', flags=0)[1]
            sTtile = ph.clean_html(tmp)
            sUrl = self.getFullUrl(ph.search(tmp, ph.A)[1])
            if sUrl:
                self.addDir(MergeDicts(cItem, {'good_for_fav': True, 'title': sTtile, 'category': nextCategory1, 'url': sUrl}))
            else:
                tmp = ph.find(section, '<ul', '</ul>', flags=0)[1]
                tmp = self.getItems(cItem, nextCategory2, tmp)
                if not tmp:
                    continue
                self.addDir(MergeDicts(cItem, {'good_for_fav': False, 'title': sTtile, 'category': 'sub_items', 'sub_items': tmp, 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}))

        self.addDir(MergeDicts(cItem, {'good_for_fav': True, 'title': cItem['title'] + ' ' + _('A-Z'), 'category': nextCategory1, 'url': cItem['url'] + '/a-z', 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}))

    def listMainMenu(self, cItem, nextCategory):
        printDBG('BBCiPlayer.listMainMenu')
        self.listsTab(self.MAIN_CAT_TAB, cItem)

    def listCategories(self, cItem, nextCategory):
        printDBG('BBCiPlayer.listCategories')
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts:
            return
        cUrl = self.cm.meta['url']
        data = ph.find(data, ('"id":"categories"', '['), ']', flags=0)[1]
        try:
            data = json_loads('[%s]' % data)
            for item in data:
                url = self.getFullUrl(item['href'], cUrl)
                title = ph.clean_html(item['title'])
                self.addDir(MergeDicts(cItem, {'category': nextCategory, 'title': title, 'url': url, 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}))
        except Exception:
            printExc()

    def listCatFilters(self, cItem, nextCategory):
        printDBG('BBCiPlayer.listCatFilters')
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts:
            return
        baseUrl = self.cm.meta['url']
        baseUrl = baseUrl[:baseUrl.rfind('/') + 1]
        data = ph.find(data, ('<select', '>', 'change_sort'), '</select>', flags=0)[1]
        data = ph.findall(data, ('<option', '>'), '</option>', flags=ph.START_S)
        for idx in range(1, len(data), 2):
            url = baseUrl + ph.getattr(data[(idx - 1)], 'value')
            title = ph.clean_html(data[idx])
            self.addDir(MergeDicts(cItem, {'good_for_fav': True, 'title': title, 'category': nextCategory, 'url': url, 'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}))

    def listItems(self, cItem, nextCategory):
        printDBG('BBCiPlayer.listItems')
        url = cItem['url']
        page = cItem.get('page', 1)
        if page > 1:
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += 'page=%s' % page
        sts, data = self.cm.getPage(url, self.defaultParams)

        if not sts:
            return

        printDBG('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        printDBG(data)
        printDBG('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        t1 = '<div id="tvip-footer-wrap">'
        t2 = '<div class="footer js-footer">'

        if t1 in data:
            endTag = t1
        else:
            endTag = t2

        nextPage = self.cm.ph.getDataBeetwenNodes(data, ('<ol', '>', 'pagination'), ('</ol',
                                                                                     '>'))[1]
        if nextPage != '':
            nextPage = self.cm.ph.getSearchGroups(nextPage, 'page=(%s)[^0-9]' % (page + 1))[0]

            if '' != nextPage:
                nextPage = True
            else:
                nextPage = False

            endTag = '<ol[^>]+?pagination[^>]+?>'
        else:
            mTag = '<div class="paginate">'
            nextPage = self.cm.ph.getDataBeetwenMarkers(data, mTag, '</div>', withMarkers=False)[1]
            if '' != nextPage:
                if '' != self.cm.ph.getSearchGroups(nextPage, 'page=(%s)[^0-9]' % (page + 1))[0]:
                    nextPage = True
                else:
                    nextPage = False
                endTag = mTag
            else:
                mTag = '<ul class="pagination'
                nextPage = self.cm.ph.getDataBeetwenMarkers(data, mTag, '</ul>', withMarkers=False)[1]
                if '' != nextPage:
                    if '' != self.cm.ph.getSearchGroups(nextPage, 'page&#x3D;(%s)[^0-9]' % (page + 1))[0]:
                        nextPage = True
                    else:
                        nextPage = False
                    endTag = mTag

        startTag = re.compile('<li[^>]+?(?:class=[\'"]list-item|list__grid__item|layout__item)[^>]*?>')
        data = self.cm.ph.getDataBeetwenReMarkers(data, startTag, re.compile(endTag), withMarkers=False)[1]
        data = startTag.split(data)
        subTitleReOb1 = re.compile('<h2[^>]+?class="[^"]*?subtitle[^"]*?"')
        subTitleReOb2 = re.compile('</h2>')

        for item in data:
            title = ph.clean_html(self.cm.ph.getDataBeetwenNodes(item, ('<div', '>','title'), ('</div','>'))[1])
            if title == '':
                title = ph.clean_html(self.cm.ph.getDataBeetwenMarkers(item, '<h1 class="list-item__title', '</h1>')[1])
            icon = ph.search(item, self.reSrcset)[0]
            printDBG(item)
            descTab = []
            descTab.append(ph.clean_html(item.split('<div class="primary">')[(-1)]))
            tmp = self.cm.ph.getDataBeetwenNodes(item, ('<a', '>', 'content-item__secondary'), ('</a','>'))[1]
            
            if tmp != '':
                url = self.cm.ph.getSearchGroups(tmp, 'href=[\'"]([^\'^"]+?)[\'"]')[0]
                type = 'category'
            else:
                url = self.cm.ph.getSearchGroups(item, 'href=[\'"]([^\'^"]+?)[\'"]')[0]
                type = 'video'
            if '/episode/' in url:
                type = 'category'
            if type == 'video':
                subtitle = ph.clean_html(self.cm.ph.getDataBeetwenMarkers(item, '<div class="subtitle', '</div>')[1])
                if subtitle == '':
                    subtitle = ph.clean_html(self.cm.ph.getDataBeetwenReMarkers(item, subTitleReOb1, subTitleReOb2)[1])
                if subtitle != '':
                    title += ' ' + subtitle
            if 'data-timeliness-type="unavailable"' in item:
                title = '[' + ph.clean_html(self.cm.ph.getDataBeetwenMarkers(item, '<span class="signpost editorial">', '</span>')[1]) + '] ' + title
            if title.lower().startswith('episode '):
                title = '%s - %s' % (cItem['title'], title)
            else:
                if cItem['category'] == 'list_episodes':
                    title = cItem['title'] + ' ' + title
            if url == '' or title == '':
                printDBG('+++++++++++++++ NO TITLE url[%s], title[%s]' % (url, title))
                continue
            if '/iplayer' not in url:
                printDBG('+++++++++++++++ URL NOT SUPPORTED AT NOW url[%s], title[%s]' % (url, title))
                continue
            params = {'good_for_fav': True, 'title': title, 'url': self.getFullUrl(url), 'icon': self.getFullIconUrl(icon), 'desc': ('[/br]').join(descTab),'desc': '\c00????00 Info: \c00??????BBC iPlayer\\n \c00????00Version: \c00??????'+self.HOST_VER+'\\n \c00????00Developer: \c00??????Codermik\\n'}
            if type == 'video':
                self.addVideo(params)
            else:
                params['category'] = nextCategory
                self.addDir(params)

        if nextPage:
            params = dict(cItem)
            params.update({'good_for_fav': False, 'title': _('Next page'), 'page': page + 1})
            self.addDir(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG('BBCiPlayer.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]' % (cItem, searchPattern, searchType))
        baseUrl = self.getFullUrl('iplayer/search?q=' + urllib.quote_plus(searchPattern))
        cItem = dict(cItem)
        cItem['url'] = baseUrl
        self.listItems(cItem, 'list_episodes')

    def getLinksForVideo(self, cItem):
        printDBG('BBCiPlayer.getLinksForVideo [%s]' % cItem)
        retTab = []
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts:
            return retTab
        tmp = self.cm.ph.getSearchGroups(data, 'mediator\\.bind\\(({.+?})\\s*,\\s*document\\.getElementById')[0]
        if tmp == '':
            tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('window\\.mediatorDefer\\s*=\\s*[^,]*?\\,'), re.compile('\\);'), False)[1]
        try:
            uniqueTab = []
            data = json_loads.loads(tmp)
            for item in data['episode']['versions']:
                url = self.getFullUrl('/iplayer/vpid/%s/' % item['id'])
                if url in uniqueTab:
                    continue
                uniqueTab.append(url)
                name = item['kind'].title()
                retTab.append({'name': name, 'url': url, 'need_resolve': 1})

        except Exception:
            printExc()
        else:
            if len(retTab):
                return retTab

        retTab.append({'name': '', 'url': cItem['url'], 'need_resolve': 1})
        return retTab

    def getVideoLinks(self, url):
        printDBG('BBCiPlayer.getVideoLinks [%s]' % url)
        return self.up.getVideoLinkExt(url)

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        self.informAboutGeoBlockingIfNeeded('GB')
        name = self.currItem.get('name', '')
        category = self.currItem.get('category', '')
        mode = self.currItem.get('mode', '')
        printDBG('handleService: || name[%s], category[%s] ' % (name, category))
        self.currList = []
        if name == None:
            rm(self.COOKIE_FILE)
            self.listMainMenu({'name': 'category', 'url': self.getMainUrl()}, 'list_items')
        else:
            if 'sub_items' == category:
                self.currList = self.currItem.get('sub_items', [])
            elif 'live_streams' == category:
                    self.listLive(self.currItem)
            elif 'list_channels' == category:
                        self.listChannels(self.currItem, 'list_channel')
            elif 'list_channel' == category:
                self.listChannelMenu(self.currItem, 'list_items', 'list_episodes')
            elif 'list_az_menu' == category:
                self.listAZMenu(self.currItem, 'list_az')
            elif category in ('list_az', 'list_items', 'list_category'):
                self.listItems2(self.currItem, 'list_episodes')
            elif 'list_categories' == category:
                self.listCategories(self.currItem, 'list_cat_filters')
            elif category in 'list_cat_filters':
                self.listCatFilters(self.currItem, 'list_category')
                if not self.currList:
                    self.listItems2(self.currItem, 'list_episodes')
            elif 'list_items' == category:
                self.listItems(self.currItem, 'list_episodes')
            elif 'list_episodes' == category:
                self.listEpisodes(self.currItem)
            elif category in ('search', 'search_next_page'):
                cItem = dict(self.currItem)
                cItem.update({'search_item': False, 'name': 'category'})
                self.listSearchResult(cItem, searchPattern, searchType)
            elif category == 'search_history':
                self.listsHistory({'name': 'history', 'category': 'search'}, 'desc', _('Type: '))
            else:
                printExc()

        CBaseHostClass.endHandleService(self, index, refresh)
        return


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, BBCiPlayer(), True, [])