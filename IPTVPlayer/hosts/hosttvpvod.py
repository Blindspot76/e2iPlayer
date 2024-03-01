# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, MergeDicts, readCFG
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getMPDLinksWithMeta
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.components.captcha_helper import CaptchaHelper
###################################################
from Plugins.Extensions.IPTVPlayer.p2p3.manipulateStrings import ensure_str
from Plugins.Extensions.IPTVPlayer.p2p3.UrlLib import urllib_quote
from Plugins.Extensions.IPTVPlayer.p2p3.pVer import isPY2
###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import datetime, timedelta, date
import re
import time
###################################################


###################################################
# E2 GUI COMMPONENTS
###################################################
from Screens.MessageBox import MessageBox
###################################################
config.plugins.iptvplayer.tvpvod_premium = ConfigYesNo(default=False)
config.plugins.iptvplayer.tvpvod_login = ConfigText(default=readCFG('tvpvod_login',""), fixed_size=False)
config.plugins.iptvplayer.tvpvod_password = ConfigText(default=readCFG('tvpvod_password',""), fixed_size=False)

config.plugins.iptvplayer.tvpVodProxyEnable = ConfigYesNo(default=False)
config.plugins.iptvplayer.tvpVodDefaultformat = ConfigSelection(default="590000", choices=[("360000", "320x180"),
                                                                                               ("590000", "398x224"),
                                                                                               ("820000", "480x270"),
                                                                                               ("1250000", "640x360"),
                                                                                               ("1750000", "800x450"),
                                                                                               ("2850000", "960x540"),
                                                                                               ("5420000", "1280x720"),
                                                                                               ("6500000", "1600x900"),
                                                                                               ("9100000", "1920x1080")])
config.plugins.iptvplayer.tvpVodUseDF = ConfigYesNo(default=True)
config.plugins.iptvplayer.tvpVodPreferedformat = ConfigSelection(default="mp4", choices=[("mp4", "MP4"), ("m3u8", "HLS/m3u8"), ("mpd", "MPD")])

###################################################
# Config options for HOST
###################################################


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Strefa Widza", config.plugins.iptvplayer.tvpvod_premium))
    if config.plugins.iptvplayer.tvpvod_premium.value:
        optionList.append(getConfigListEntry("  email:", config.plugins.iptvplayer.tvpvod_login))
        optionList.append(getConfigListEntry("  hasło:", config.plugins.iptvplayer.tvpvod_password))
    optionList.append(getConfigListEntry("Peferowany format wideo", config.plugins.iptvplayer.tvpVodPreferedformat))
    optionList.append(getConfigListEntry("Domyślna jakość wideo", config.plugins.iptvplayer.tvpVodDefaultformat))
    optionList.append(getConfigListEntry("Używaj domyślnej jakości wideo:", config.plugins.iptvplayer.tvpVodUseDF))
    optionList.append(getConfigListEntry("Korzystaj z proxy?", config.plugins.iptvplayer.tvpVodProxyEnable))
    return optionList
###################################################


def gettytul():
    return 'https://vod.tvp.pl/'


class TvpVod(CBaseHostClass, CaptchaHelper):
    DEFAULT_ICON_URL = 'https://s.tvp.pl/files/vod.tvp.pl/img/menu/logo_vod.png' #'http://sd-xbmc.org/repository/xbmc-addons/tvpvod.png'
    PAGE_SIZE = 12
    SPORT_PAGE_SIZE = 30
    ALL_FORMATS = [{"video/mp4": "mp4"}, {"application/x-mpegurl": "m3u8"}, {"video/x-ms-wmv": "wmv"}]
    REAL_FORMATS = {'m3u8': 'ts', 'mp4': 'mp4', 'wmv': 'wmv'}
    MAIN_VOD_URL = "https://vod.tvp.pl/"
    LOGIN_URL = "https://user.tvp.pl/login.php?ref="
    ACCOUNT_URL = "https://user.tvp.pl/account.php"
    STREAMS_URL_TEMPLATE = 'http://www.api.v3.tvp.pl/shared/tvpstream/listing.php?parent_id=13010508&type=epg_item&direct=false&filter={%22release_date_dt%22:%22[iptv_date]%22,%22epg_play_mode%22:{%22$in%22:[0,1,3]}}&count=-1&dump=json'
    SEARCH_VOD_URL = MAIN_VOD_URL + 'szukaj?query=%s'
    IMAGE_URL = 'http://s.v3.tvp.pl/images/%s/%s/%s/uid_%s_width_500_gs_0.%s'
    HTTP_HEADERS = {}

    VOD_CAT_TAB = [{'category': 'tvp_api', 'title': 'Seriale', 'id': '18'},
                    {'category': 'tvp_api', 'title': 'Filmy', 'id': '136'},
                    {'category': 'tvp_api', 'title': 'Programy', 'id': '88'},
                    {'category': 'tvp_api', 'title': 'Dokumenty', 'id': '163'},
                    {'category': 'tvp_api', 'title': 'Teatr', 'id': '202'},
                    {'category': 'tvp_api', 'title': 'News', 'id': '205'},
                    {'category': 'tvp_api', 'title': 'Dla dzieci', 'id': '24'},
                    {'category': 'tvp_sport', 'title': 'TVP Sport', 'url': 'http://sport.tvp.pl/wideo'},
                    {'category': 'streams', 'title': 'TVP na żywo', 'url': 'http://tvpstream.tvp.pl/'},
                    {'category': 'digi_menu', 'title': 'Rekonstrukcja cyfrowa TVP', 'url': 'https://cyfrowa.tvp.pl/'},

                    #{'category':'vods_list_items1',    'title':'Polecamy',                  'url':MAIN_VOD_URL},
                    #{'category':'vods_sub_categories', 'title':'Polecane',                  'marker':'Polecane'},
                    #{'category':'vods_sub_categories', 'title':'VOD',                       'marker':'VOD'},
                    #{'category':'vods_sub_categories', 'title':'Programy',                  'marker':'Programy'},
                    #{'category':'vods_sub_categories', 'title':'Informacje i publicystyka', 'marker':'Informacje i publicystyka'},
                    {'category': 'search', 'title': _('Search'), 'search_item': True},
                    {'category': 'search_history', 'title': _('Search history')}]

    STREAMS_CAT_TAB = [{'category': 'tvp3_streams', 'title': 'TVP 3', 'url': 'http://tvpstream.tvp.pl/', 'icon': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/TVP3_logo_2016.png/240px-TVP3_logo_2016.png'},
                       {'category': 'week_epg', 'title': 'TVP SPORT', 'url': STREAMS_URL_TEMPLATE, 'icon': 'https://upload.wikimedia.org/wikipedia/commons/9/9d/TVP_Sport_HD_Logo.png'},
                       #{'category': 'tvpsport_streams', 'title': 'Transmisje sport.tvp.pl', 'url': 'http://sport.tvp.pl/transmisje', 'icon': 'https://upload.wikimedia.org/wikipedia/commons/9/9d/TVP_Sport_HD_Logo.png'},
                      ]

    def __init__(self):
        printDBG("TvpVod.__init__")
        CBaseHostClass.__init__(self, {'history': 'TvpVod', 'cookie': 'tvpvod.cookie', 'proxyURL': config.plugins.iptvplayer.proxyurl.value, 'useProxy': config.plugins.iptvplayer.tvpVodProxyEnable.value})
        self.defaultParams = {'with_metadata': True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE, 'header': TvpVod.HTTP_HEADERS}

        self.loggedIn = None
        self.fixUrlMap = {'nadobre.tvp.pl': 'http://vod.tvp.pl/8514270/na-dobre-i-na-zle',
                          'mjakmilosc.tvp.pl': 'http://vod.tvp.pl/1654521/m-jak-milosc',
                          'barwyszczescia.tvp.pl': 'http://vod.tvp.pl/8514286/barwy-szczescia',
                          'nasygnale.tvp.pl': 'http://vod.tvp.pl/13883615/na-sygnale'}
        self.FormatBitrateMap = [("360000", "320x180"), ("590000", "398x224"), ("820000", "480x270"), ("1250000", "640x360"),
                                  ("1750000", "800x450"), ("2850000", "960x540"), ("5420000", "1280x720"), ("6500000", "1600x900"), ("9100000", "1920x1080")]
        self.MAIN_URL = 'https://vod.tvp.pl/'
        self.loginMessage = ''

    def getJItemStr(self, item, key, default=''):
        v = item.get(key, None)
        if None == v:
            return default
        return str(v)

    def getImageUrl(self, item):
        keys = ['logo_4x3', 'image_16x9', 'image_4x3', 'image_ns954', 'image_ns644', 'image']
        iconFile = ""
        for key in keys:
            if None != item.get(key, None):
                iconFile = self.getJItemStr(item[key][0], 'file_name')
            if len(iconFile):
                tmp = iconFile.split('.')
                return self.IMAGE_URL % (iconFile[0], iconFile[1], iconFile[2], tmp[0], tmp[1])
        return ''

    def _getPage(self, url, addParams={}, post_data=None):

        try:
            if isPY2():
                import httplib
            else:
                import http.client as httplib

            def patch_http_response_read(func):
                def inner(*args):
                    try:
                        return func(*args)
                    except httplib.IncompleteRead as e:
                        return e.partial
                return inner
            prev_read = httplib.HTTPResponse.read
            httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)
        except Exception:
            printExc()
        sts, data = self.cm.getPage(url, addParams, post_data)
        try:
            httplib.HTTPResponse.read = prev_read
        except Exception:
            printExc()
        return sts, data

    def _getStr(self, v, default=''):
        return self.cleanHtmlStr(self._encodeStr(v, default))

    def _encodeStr(self, v, default=''):
        return ensure_str(v)

    def _getNum(self, v, default=0):
        try:
            return int(v)
        except Exception:
            try:
                return float(v)
            except Exception:
                return default

    def _getFullUrl(self, url, baseUrl=None):
        if None == baseUrl:
            baseUrl = TvpVod.MAIN_VOD_URL
        if 0 < len(url) and not url.startswith('http'):
            if url.startswith('//'):
                url = 'http:' + url
            else:
                if not baseUrl.endswith('/'):
                    baseUrl += '/'
                if url.startswith('/'):
                    url = url[1:]
                url = baseUrl + url
        return url

    def getFormatFromBitrate(self, bitrate):
        ret = ''
        for item in self.FormatBitrateMap:
            if int(bitrate) == int(item[0]):
                ret = item[1]
        if '' == ret:
            ret = 'Bitrate[%s]' % bitrate
        return ret

    def getBitrateFromFormat(self, format):
        ret = 0
        for item in self.FormatBitrateMap:
            if format == item[1]:
                ret = int(item[0])
        return ret

    def tryTologin(self):
        self.loginMessage = ''
        email = config.plugins.iptvplayer.tvpvod_login.value
        password = config.plugins.iptvplayer.tvpvod_password.value
        msg = 'Wystąpił problem z zalogowaniem użytkownika "%s"!' % email
        params = dict(self.defaultParams)
        sts, data = self._getPage(TvpVod.ACCOUNT_URL, params)
        if not sts or 'action=sign-out' not in data:
            params.update({'load_cookie': False})
            sts, data = self._getPage(TvpVod.LOGIN_URL, params)
            if sts:
                ref = self.cm.ph.getSearchGroups(data, 'name="ref".+?value="([^"]+?)"')[0]
                post_data = {'ref': ref, 'email': email, 'password': password, 'action': 'login'}
                sitekey = self.cm.ph.getSearchGroups(data, '''sitekey=['"]([^'^"]+?)['"]''')[0]
                if sitekey != '':
                    token, errorMsgTab = self.processCaptcha(sitekey, self.cm.meta['url'])
                    if token == '':
                        msg = _('Link protected with google recaptcha v2.') + '\n' + msg
                        sts = False
                    else:
                        post_data['g-recaptcha-response'] = token
                sts, data = self._getPage(TvpVod.LOGIN_URL + ref, self.defaultParams, post_data)
                sts, data = self._getPage(TvpVod.ACCOUNT_URL, self.defaultParams)
        if sts and 'action=sign-out' in data:
            printDBG(">>>\n%s\n<<<" % data)
            tmp = self.cm.ph.getDataBeetwenNodes(data, ('<section', '>', 'abo__section'), ('</section', '>'), False)[1]
            if tmp == '':
                tmp = self.cm.ph.getDataBeetwenNodes(data, ('<section', '>', 'abo-inactive'), ('</section', '>'), False)[1]
            data = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(tmp, ('<p', '>'), ('</p', '>'), False)[1])
            msg = ['Użytkownik "%s"' % email]
            msg.append('Strefa Abo %s' % data)
            self.loginMessage = '[/br]'.join(msg)
            msg = self.loginMessage.replace('[/br]', '\n')
            post_data = {'approve': '1'}
            params = dict(self.defaultParams)
            sts, data = self._getPage('https://user.tvp.pl/oauth/auth_code.php?client_id=tvp-sso&redirect_uri=https%3A%2F%2Fvod.tvp.pl%2Fsubscriber%2Flogin%2Ftvp&scope=basic&response_type=code', params, post_data)
            params['max_data_size'] = 0
            params['no_redirection'] = True
            sts, data = self._getPage('https://user.tvp.pl/oauth/auth_code.php?client_id=tvp-sso&redirect_uri=https%3A%2F%2Fvod.tvp.pl%2Fsubscriber%2Flogin%2Ftvp&scope=basic&response_type=code', params, post_data)
            url = self.cm.meta.get('location', '')
            printDBG("TvpVod.location %s" % url)
            post_data = '{"auth":{"type":"SSO","value":"","app":"tvp"},"rememberMe":true}'
            url = 'https://vod.tvp.pl/api/subscribers/sso/tvp/login?lang=pl&platform=BROWSER&code=' + self.cm.ph.getSearchGroups(url + '&', 'code=([^\?^&]+)[\?&]')[0]
            params = dict(self.defaultParams)
            params['raw_post_data'] = True
            params['header']['Content-Type'] = 'application/x-www-form-urlencoded'
            params['header']['Connection'] = 'keep-alive'
            params['header']['Referer'] = 'https://user.tvp.pl/oauth/auth_code.php?client_id=tvp-sso&redirect_uri=https%3A%2F%2Fvod.tvp.pl%2Fsubscriber%2Flogin%2Ftvp&scope=basic&response_type=code'
            sts, data = self._getPage(url, params, post_data)
            printDBG(">>>\n%s\n<<<" % data)
        else:
            sts = False
        return sts, msg

    def _addNavCategories(self, data, cItem, category):
        data = re.findall('href="([^"]+?)"[^>]*?>([^<]+?)<', data)
        for item in data:
            params = dict(cItem)
            params.update({'category': category, 'title': self.cleanHtmlStr(item[1]), 'url': item[0]})
            self.addDir(params)

    def _getAjaxUrl(self, parent_id, location):
        if location == 'directory_series':
            order = ''
            type = 'website'
            template = 'listing_series.html'
            direct = '&direct=false'
        elif location == 'directory_stats':
            order = ''
            type = 'video'
            template = 'listing_stats.html'
            direct = '&filter=%7B%22playable%22%3Atrue%7D&direct=false'
        elif location == 'directory_video':
            order = '&order=position,1'
            type = 'video'
            template = 'listing.html'
            direct = '&filter=%7B%22playable%22%3Atrue%7D&direct=false'
        elif location == 'website':
            order = '&order=release_date_long,-1'
            type = 'video'
            template = 'listing.html'
            direct = '&filter=%7B%22playable%22%3Atrue%7D&direct=false'
        else:
            order = '&order=release_date_long,-1'
            type = 'video'
            template = 'listing.html'
            direct = '&filter=%7B%22playable%22%3Atrue%7D&direct=true'

        url = '/shared/listing.php?parent_id=' + parent_id + '&type=' + type + order + direct + '&template=directory/' + template + '&count=' + str(TvpVod.PAGE_SIZE)

        return self._getFullUrl(url)

    def listTVP3Streams(self, cItem):
        printDBG("TvpVod.listTVP3Streams")
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts:
            return
        data = self.cm.ph.getSearchGroups(data, 'window.__channels =([^;]+?);')[0]
        data = json_loads(data)
        for item in data:
            video_id = self.cm.ph.getSearchGroups(json_dumps(item.get('items', '')), '''['"]video_id['"]\s*:\s*([^,]+?),''')[0]
            if video_id != '':
                desc = ''
                icon = self.cm.ph.getSearchGroups(json_dumps(item.get('image_logo', '')), '''['"](http[^'^"]+?\.jpg)['"]''')[0]
                if icon == '':
                    icon = self.cm.ph.getSearchGroups(json_dumps(item.get('image_logo', '')), '''['"](http[^'^"]+?\.png)['"]''')[0]
                icon = icon.format(width = '300', height = '0')
#                printDBG("TvpVod.listTVP3Streams icon [%s]" % icon)
                title = item.get('title', '').replace('EPG - ', '')
                params = dict(cItem)
                params.update({'title': title, 'url': 'https://stream.tvp.pl/sess/TVPlayer2/embed.php?ID=%s' % video_id, 'icon': icon, 'desc': desc})
                self.addVideo(params)

    def listTVPSportStreams(self, cItem, nextCategory):
        printDBG("TvpVod.listTVPSportStreams")
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts:
            return
        cUrl = self.cm.getBaseUrl(data.meta['url'])

        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'epg-broadcasts'), ('</section', '>'), False)[1]
        data = re.compile('''<div[^>]*?class=['"]date['"][^>]*?>''').split(data)
        for idx in range(1, len(data), 1):
            dateTitle = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data[idx], '<span', '</span>')[1])
            subItems = []
            tmp = re.compile('''<div[^>]+?class=['"]item(?:\s*playing)?['"][^>]*?>''').split(data[idx])
            for i in range(1, len(tmp), 1):
                time = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(tmp[i], ('<span', '>', 'time'), ('</span', '>'), False)[1])
                desc = []
                t = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(tmp[i], ('<div', '>', 'category'), ('</div', '>'), False)[1])
                if t != '':
                    desc.append(t)
                t = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(tmp[i], ('<div', '>', 'meta'), ('</div', '>'), False)[1])
                if t != '':
                    desc.append(t)
                desc = '[/br]'.join(desc)
                t = self.cm.ph.getDataBeetwenNodes(tmp[i], ('<div', '>', 'title'), ('</div', '>'), False)[1]
                url = self._getFullUrl(self.cm.ph.getSearchGroups(t, '''<a[^>]+?href=['"]([^'^"]+?)['"]''')[0], cUrl)
                title = '%s - %s' % (time, self.cleanHtmlStr(t))

                params = dict(cItem)
                params.update({'good_for_fav': False, 'title': title, 'url': url, 'desc': desc})
                if url == '':
                    params['type'] = 'article'
                else:
                    params['type'] = 'video'
                subItems.append(params)
            if len(subItems):
                params = dict(cItem)
                params.update({'category': nextCategory, 'good_for_fav': True, 'title': dateTitle, 'sub_items': subItems})
                self.addDir(params)

    def listWeekEPG(self, cItem, nextCategory):
        printDBG("TvpVod.listWeekEPG")
        urlTemplate = cItem['url']

        d = datetime.today()
        for i in range(7):
            url = urlTemplate.replace('[iptv_date]', d.strftime('%Y-%m-%d'))
            title = d.strftime('%a %d.%m.%Y')
            params = dict(cItem)
            params.update({'category': nextCategory, 'title': title, 'url': url})
            self.addDir(params)
            d += timedelta(days=1)

    def listEPGItems(self, cItem):
        printDBG("TvpVod.listEPGItems")
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts:
            return
        try:
            #date.fromtimestamp(item['release_date']['sec']).strftime('%H:%M')
            data = json_loads(data)
            data['items'].sort(key=lambda item: item['release_date_hour'])
            for item in data['items']:
                if not item.get('is_live', False):
                    continue
                title = str(item['title'])
                desc = self.cleanHtmlStr(str(item['lead']))
                asset_id = str(item['asset_id'])
                asset_id = str(item['video_id'])
                icon = self.getImageUrl(item)
                desc = item['release_date_hour'] + ' - ' + item['broadcast_end_date_hour'] + '[/br]' + desc
                self.addVideo({'title': title, 'url': '', 'object_id': asset_id, 'icon': icon, 'desc': desc})
            printDBG(data)
        except Exception:
            printExc()

    def listTVPSportCategories(self, cItem, nextCategory):
        printDBG("TvpVod.listTVPSportCategories")
        sts, data = self._getPage(cItem['url'], self.defaultParams)
        if not sts:
            return

        data = self.cm.ph.getDataBeetwenMarkers(data, '__directoryData ', '</script>', False)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, '{', '}', True)[1]
        data = json_loads(data.replace(';', ''))

        sts, data = self._getPage('https://sport.tvp.pl/api/sport/www/directory/list?direct=true&sort=position,1&limit=30&id=%s' % data.get('_id', '548369'), self.defaultParams)
        if not sts:
            return []

        data = json_loads(data)
        data = data.get('data', [])
        data = data.get('items', [])
        for item in data:
#            printDBG("TvpVod.listTVPSportCategories item [%s]" % item)
            sts, data = self._getPage('https://sport.tvp.pl/api/sport/www/block/list?device=www&id=%s' % item.get('_id', ''), self.defaultParams)
            if not sts:
                continue
            try:
                data = json_loads(data)
                _id = data['data']['items'][0]['_id']
            except Exception:
                printExc()
            url = 'https://sport.tvp.pl/api/sport/www/block/items?device=www&id=%s' % _id
            name = item.get('title', '')
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category': nextCategory, 'title': name, 'url': url, 'desc': ''})
            self.addDir(params)

    def listTVPSportVideos(self, cItem):
        printDBG("TvpVod.listTVPSportVideos")

        page = cItem.get('page', 1)
        videosNum = cItem.get('videosNum', 0)

        url = cItem['url']
        url += '&page=%d' % (page)

        sts, data = self._getPage(url, self.defaultParams)
        if not sts:
            return
        try:
            data = json_loads(data)
            for item in data['data']['items']:
                url = self._getFullUrl(item['url'], 'http://sport.tvp.pl')
                desc = self.cleanHtmlStr(item['lead'])
                title = item['title']
                icon = item['image']['url'].format(width='480', height='360')
                if url.startswith('http'):
                    videosNum += 1
                    params = dict(cItem)
                    params.update({'title': title, 'icon': icon, 'url': url, 'desc': desc})
                    self.addVideo(params)
        except Exception:
            printExc()

        params = dict(cItem)
        params.update({'page': page + 1, 'videosNum': videosNum})
        if videosNum >= self.SPORT_PAGE_SIZE:
            params['title'] = _('Next page')
            params.update({'videosNum': 0})
            self.addDir(params)
        else:
            params['title'] = _('More')
            self.addMore(params)

    def listCatalogApi(self, cItem, nextCategory):
        printDBG("TvpVod.listCatalogApi")
        sts, data = self._getPage('https://vod.tvp.pl/api/items/categories?mainCategoryId=%s&lang=pl&platform=BROWSER' % cItem['id'], self.defaultParams)
        if not sts:
            return []

        data = json_loads(data)
        for item in data:
            url = 'https://vod.tvp.pl/api/products/vods?&firstResult=0&maxResults=100&mainCategoryId[]=%s&categoryId[]=%s&lang=pl&platform=BROWSER' % (cItem['id'], item.get('id', ''))
            name = item.get('name', '')
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category': nextCategory, 'title': name, 'url': url, 'desc': ''})
            self.addDir(params)

    def exploreApiItem(self, cItem, nextCategory):
        printDBG("TvpVod.exploreApiItem")

        baseUrl = cItem['url']
        sts, data = self._getPage(baseUrl, self.defaultParams)
        if not sts:
            return []

        tmp = json_loads(data)
        if '/seasons' not in baseUrl:
            tmp = tmp.get('items', [])

        nextPageUrl = ''
        itemsTab = []
        for item in tmp:
#            printDBG("TvpVod.exploreApiItem item %s" % item)
            icon = self.cm.ph.getSearchGroups(json_dumps(item.get('images', '')), '''['"]([^'^"]+?\.jpg)['"]''')[0]
            if icon == '':
                icon = self.cm.ph.getSearchGroups(json_dumps(item.get('images', '')), '''['"]([^'^"]+?\.png)['"]''')[0]
            if icon == '':
                icon = cItem['icon']
            if icon.startswith('//'):
                icon = 'https:' + icon
            id = item.get('id', '')
            type = item.get('type', '')
            if type == 'EPISODE':
                url = 'https://vod.tvp.pl/api/products/%d/videos/playlist?platform=BROWSER&videoType=MOVIE' % id
            elif type == 'SERIAL':
                url = 'https://vod.tvp.pl/api/products/vods/serials/%d/seasons?lang=pl&platform=BROWSER' % id
            elif type == 'SEASON':
                sid = self.cm.ph.getSearchGroups(baseUrl, """/([0-9]+)/""")[0]
                url = 'https://vod.tvp.pl/api/products/vods/serials/%s/seasons/%s/episodes?lang=pl&platform=BROWSER' % (sid, id)
            else:
                url = 'https://vod.tvp.pl/api/products/%d/videos/playlist?platform=BROWSER&videoType=MOVIE' % id
            title = item.get('title', '')
            if item.get('payable', ''):
                title = title + ' [$]'
            desc = item.get('lead', '')
#            printDBG("TvpVod.exploreApiItem desc %s" % desc)
            if self.cm.isValidUrl(url) and title != '':
                params = dict(cItem)
                params.update({'good_for_fav': False, 'title': title, 'url': url, 'icon': icon, 'desc': desc})
                if 'playlist' in url:
                    params.update({'good_for_fav': True, 'type': 'video'})
                    itemsTab.append(params)
                else:
                    params.update({'category': nextCategory, })
                    itemsTab.append(params)

        if 0 == len(self.currList):
            self.currList = itemsTab

        if self.cm.isValidUrl(nextPageUrl):
            params = dict(cItem)
            params.update({'good_for_fav': False, 'category': nextCategory, 'title': _("Next page"), 'url': nextPageUrl, 'page': page + 1})
            self.addDir(params)

    def mapHoeverItem(self, cItem, item, rawItem, nextCategory):
        try:
            item = json_loads(item)
            title = self.getJItemStr(item, 'title')
            icon = self._getFullUrl(self.getJItemStr(item, 'image'))
            tmp = []
            labelMap = {'age': 'Wiek: %s'}
            for key in ['transmision', 'antena', 'age']:
                val = self.getJItemStr(item, key)
                if val != '':
                    tmp.append(labelMap.get(key, '%s') % val)

            paymentTag = self.cleanHtmlStr(self.cm.ph.getDataBeetwenNodes(rawItem, ('<div', '>', 'showPaymentTag'), ('</div', '>'))[1])
            if paymentTag != '':
                tmp.append(paymentTag)
            desc = ' | '.join(tmp)
            desc += '[/br]' + self.getJItemStr(item, 'description')

            params = {'good_for_fav': True, 'icon': icon, 'desc': self.cleanHtmlStr(desc)}
            seriesLink = self._getFullUrl(self.getJItemStr(item, 'seriesLink'))
            episodeUrl = self._getFullUrl(self.getJItemStr(item, 'episodeLink'))

            if self.cm.isValidUrl(episodeUrl) and '/video/' in episodeUrl:
                title += ' ' + self.getJItemStr(item, 'episodeCount')
                params.update({'title': title, 'url': episodeUrl})
                self.addVideo(params)
            else:
                params.update({'category': nextCategory, 'title': title, 'url': seriesLink})
                self.addDir(params)

            printDBG("======================")
            printDBG(item)
        except Exception:
            printExc()

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("TvpVod.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))

        if searchType == 'movies':
            url = 'https://vod.tvp.pl/api/products/vods/search/VOD?lang=pl&platform=BROWSER&keyword=%s' % urllib_quote(searchPattern)
        else:
            url = 'https://vod.tvp.pl/api/products/vods/search/SERIAL?lang=pl&platform=BROWSER&keyword=%s' % urllib_quote(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = url

        self.exploreApiItem(cItem, 'api_explore_item')

    def listsMenuGroups(self, cItem, category):
        printDBG("TvpVod.listsGroupsType1")
        url = self._getFullUrl(cItem['url'])
        sts, data = self._getPage(url, self.defaultParams)
        if sts:
            # check if
            data = self.cm.ph.getDataBeetwenMarkers(data, '<section id="menu"', '</section>', False)[1]
            self._addNavCategories(data, cItem, category)

    def listItems2(self, cItem, category, data):
        printDBG("TvpVod.listItems2")
        itemMarker = '<div class="'
        sectionMarker = '<section id="emisje">'

        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'class="siteNewscast">', '</section>', False)[1]
        icon = self.cm.ph.getSearchGroups(tmp, 'src="([^"]+?)"')[0]
        desc = self.cm.ph.getDataBeetwenMarkers(tmp, '<p>', '</div>', False)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, sectionMarker, '</section>', True)[1]

        printDBG("TvpVod.listItems2 start parse")
        data = data.split(itemMarker)
        if len(data):
            del data[0]
        for item in data:
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = self.cleanHtmlStr('<' + item)
            params = dict(cItem)
            params.update({'category': category, 'title': title, 'url': url, 'icon': icon, 'desc': desc, 'page': 0})
            self.addVideo(params)

    def getObjectID(self, url):
        sts, data = self.cm.getPage(url, self.defaultParams)
        if not sts:
            return ''

        sess_player_url = self.cm.ph.getSearchGroups(data, '''(https?://[^'^"]+?/sess/player/video/[^'^"]+?)['"]''')[0]
        if sess_player_url != '':
            sts, tmp = self.cm.getPage(sess_player_url, self.defaultParams)
            if sts:
                data = tmp

        asset_id = self.cm.ph.getSearchGroups(data, '''id=['"]tvplayer\-[0-9]+\-([0-9]+)''')[0]

        if asset_id == '':
            asset_id = self.cm.ph.getSearchGroups(data, 'object_id=([0-9]+?)[^0-9]')[0]
        if asset_id == '':
            asset_id = self.cm.ph.getSearchGroups(data, 'class="playerContainer"[^>]+?data-id="([0-9]+?)"')[0]
        if '' == asset_id:
            asset_id = self.cm.ph.getSearchGroups(data, 'data\-video-\id="([0-9]+?)"')[0]
        if '' == asset_id:
            asset_id = self.cm.ph.getSearchGroups(data, "object_id:'([0-9]+?)'")[0]
        if '' == asset_id:
            asset_id = self.cm.ph.getSearchGroups(data, 'data\-object\-id="([0-9]+?)"')[0]
        if '' == asset_id:
            asset_id = self.cm.ph.getSearchGroups(data, "videoID:\s*'([0-9]+?)'")[0]

        return asset_id

    def getLinksForVideo(self, cItem):
        asset_id = str(cItem.get('object_id', ''))
        url = self._getFullUrl(cItem.get('url', ''))

        videoTab = []

        def __getLinkQuality(itemLink):
            if 'width' in itemLink and 'height' in itemLink:
                bitrate = self.getBitrateFromFormat('%sx%s' % (itemLink['width'], itemLink['height']))
                if bitrate != 0:
                    return bitrate
            else:
                try:
                    return int(itemLink['bitrate'])
                except Exception:
                    return int(itemLink['bandwitch'])

        if 'stream.tvp.pl' in url:
            sts, data = self.cm.getPage(url)
            if not sts:
                return []
#            printDBG("TvpVod.getLinksForVideo data [%s]" % data)
            hlsUrl = self.cm.ph.getSearchGroups(data, '''['"](http[^'^"]*?\.m3u8[^'^"]*?)['"]''')[0].replace('\/', '/')
            if '' != hlsUrl:
                videoTab = getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=False)
                if 1 < len(videoTab):
                    max_bitrate = int(config.plugins.iptvplayer.tvpVodDefaultformat.value)

                    oneLink = CSelOneLink(videoTab, __getLinkQuality, max_bitrate)
                    if config.plugins.iptvplayer.tvpVodUseDF.value:
                        videoTab = oneLink.getOneLink()
                    else:
                        videoTab = oneLink.getSortedLinks()
                if 1 <= len(videoTab):
                    return videoTab

        if '/api/' in url:
            httpParams = dict(self.defaultParams)
            httpParams['ignore_http_code_ranges'] = [(403, 403)]
            sts, data = self._getPage(url, httpParams)
#            printDBG("getLinksForVideo data [%s]" % data)
            if not sts:
                return []

            if '"drm":' in data:
                SetIPTVPlayerLastHostError(_("Video with DRM protection."))

            if config.plugins.iptvplayer.tvpVodPreferedformat.value == 'm3u8':
                hlsUrl = self.cm.ph.getSearchGroups(data, '''['"](http[^'^"]*?\.m3u8[^'^"]*?)['"]''')[0].replace('\/', '/')
                if '' != hlsUrl:
                    videoTab = getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=False)
                    if 1 < len(videoTab):
                        max_bitrate = int(config.plugins.iptvplayer.tvpVodDefaultformat.value)
                    oneLink = CSelOneLink(videoTab, __getLinkQuality, max_bitrate)
                    if config.plugins.iptvplayer.tvpVodUseDF.value:
                        videoTab = oneLink.getOneLink()
                    else:
                        videoTab = oneLink.getSortedLinks()
            if config.plugins.iptvplayer.tvpVodPreferedformat.value == 'mpd':
                mpdLink = self.cm.ph.getSearchGroups(data, '''['"](http[^'^"]*?\.mpd[^'^"]*?)['"]''')[0].replace('\/', '/')
                if '' != mpdLink:
                    videoTab = getMPDLinksWithMeta(mpdLink, False, sortWithMaxBandwidth=999999999)
                    if 1 < len(videoTab):
                        max_bitrate = int(config.plugins.iptvplayer.tvpVodDefaultformat.value)
                    oneLink = CSelOneLink(videoTab, __getLinkQuality, max_bitrate)
                    if config.plugins.iptvplayer.tvpVodUseDF.value:
                        videoTab = oneLink.getOneLink()
                    else:
                        videoTab = oneLink.getSortedLinks()
            if config.plugins.iptvplayer.tvpVodPreferedformat.value == 'mp4':
                asset_id = self.cm.ph.getSearchGroups(data, '''['"]externalUid['"]:['"]([^'^"]*?)['"]''')[0]

            if 1 <= len(videoTab):
                return videoTab

        if '' == asset_id:
            asset_id = self.getObjectID(url)

        return self.getVideoLink(asset_id)

    def isVideoData(self, asset_id):
        sts, data = self.cm.getPage('http://www.tvp.pl/shared/cdn/tokenizer_v2.php?mime_type=video%2Fmp4&object_id=' + asset_id, self.defaultParams)
        if not sts:
            return False
        return not 'NOT_FOUND' in data

    def getVideoLink(self, asset_id):
        printDBG("getVideoLink asset_id [%s]" % asset_id)
        videoTab = []

        if '' == asset_id:
            return videoTab

        def _sortVideoLinks(videoTab):
            if 1 < len(videoTab):
                max_bitrate = int(config.plugins.iptvplayer.tvpVodDefaultformat.value)

                def __getLinkQuality(itemLink):
                    if 'width' in itemLink and 'height' in itemLink:
                        bitrate = self.getBitrateFromFormat('%sx%s' % (itemLink['width'], itemLink['height']))
                        if bitrate != 0:
                            return bitrate
                    try:
                        return int(itemLink['bitrate'])
                    except Exception:
                        return 0
                oneLink = CSelOneLink(videoTab, __getLinkQuality, max_bitrate)
                videoTab = oneLink.getSortedLinks()
            return videoTab

        # main routine
        if len(videoTab) == 0:
            sts, data = self.cm.getPage('http://www.tvp.pl/shared/cdn/tokenizer_v2.php?mime_type=video%2Fmp4&object_id=' + asset_id, self.defaultParams)
            printDBG("%s -> [%s]" % (sts, data))
            try:
                data = json_loads(data)

                def _getVideoLink(data, FORMATS):
                    videoTab = []
                    for item in data['formats']:
                        if item['mimeType'] in FORMATS.keys():
                            formatType = FORMATS[item['mimeType']]
                            format = self.REAL_FORMATS.get(formatType, '')
                            name = self.getFormatFromBitrate(str(item['totalBitrate'])) + '\t ' + formatType
                            url = item['url']
                            if 'm3u8' == formatType:
                                videoTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=False))
                            else:
                                meta = {'iptv_format': format}
                                if config.plugins.iptvplayer.tvpVodProxyEnable.value:
                                    meta['http_proxy'] = config.plugins.iptvplayer.proxyurl.value
                                videoTab.append({'name': name, 'bitrate': str(item['totalBitrate']), 'url': self.up.decorateUrl(url, meta)})
                    return videoTab

                preferedFormats = []
                if config.plugins.iptvplayer.tvpVodPreferedformat.value == 'm3u8':
                    preferedFormats = [TvpVod.ALL_FORMATS[1], TvpVod.ALL_FORMATS[0], TvpVod.ALL_FORMATS[2]]
                else:
                    preferedFormats = TvpVod.ALL_FORMATS

                for item in preferedFormats:
                    videoTab.extend(_sortVideoLinks(_getVideoLink(data, item)))

            except Exception:
                printExc("getVideoLink exception")

        # fallback routine
        if len(videoTab) == 0:
            formatMap = {'1': ("320x180", 360000), '2': ('398x224', 590000), '3': ('480x270', 820000), '4': ('640x360', 1250000), '5': ('800x450', 1750000), '6': ('960x540', 2850000), '7': ('1280x720', 5420000), '8': ("1600x900", 6500000), '9': ('1920x1080', 9100000)}

            params = dict(self.defaultParams)
            params['header'] = {'User-Agent': 'okhttp/3.8.1', 'Authorization': 'Basic YXBpOnZvZA==', 'Accept-Encoding': 'gzip'}
#            sts, data = self.cm.getPage( 'https://apivod.tvp.pl/tv/video/%s/default/default?device=android' % asset_id, params)
            sts, data = self.cm.getPage('https://apivod.tvp.pl/tv/video/%s/' % asset_id, params)
            printDBG("%s -> [%s]" % (sts, data))
            try:
                data = json_loads(data, '', True)
                for item in data['data']:
                    if 'formats' in item:
                        data = item
                        break
                hlsTab = []
                mp4Tab = []
                for item in data['formats']:
                    if not self.cm.isValidUrl(item.get('url', '')):
                        continue
                    if item.get('mimeType', '').lower() == "application/x-mpegurl":
                        hlsTab = getDirectM3U8Playlist(item['url'])
                    elif item.get('mimeType', '').lower() == "video/mp4":
                        id = self.cm.ph.getSearchGroups(item['url'], '''/video\-([1-9])\.mp4$''')[0]
                        fItem = formatMap.get(id, ('0x0', 0))
                        mp4Tab.append({'name': '%s \t mp4' % fItem[0], 'url': item['url'], 'bitrate': fItem[1], 'id': id})

                if len(hlsTab) > 0 and 1 == len(mp4Tab) and mp4Tab[0]['id'] != '':
                    for item in hlsTab:
                        res = '%sx%s' % (item['width'], item['height'])
                        for key in formatMap.keys():
                            if key == mp4Tab[0]['id']:
                                continue
                            if formatMap[key][0] != res:
                                continue
                            url = mp4Tab[0]['url']
                            url = url[:url.rfind('/')] + ('/video-%s.mp4' % key)
                            mp4Tab.append({'name': '%s \t mp4' % formatMap[key][0], 'url': url, 'bitrate': formatMap[key][1], 'id': key})

                hlsTab = _sortVideoLinks(hlsTab)
                mp4Tab = _sortVideoLinks(mp4Tab)
                if config.plugins.iptvplayer.tvpVodPreferedformat.value == 'm3u8':
                    videoTab.extend(hlsTab)
                    videoTab.extend(mp4Tab)
                else:
                    videoTab.extend(mp4Tab)
                    videoTab.extend(hlsTab)
            except Exception:
                printExc("getVideoLink exception")

        if config.plugins.iptvplayer.tvpVodUseDF.value and len(videoTab):
            videoTab = [videoTab[0]]

        return videoTab

    def getLinksForFavourite(self, fav_data):
        if None == self.loggedIn:
            premium = config.plugins.iptvplayer.tvpvod_premium.value
            if premium:
                self.loggedIn, msg = self.tryTologin()

        try:
            cItem = json_loads(fav_data)
            links = self.getLinksForVideo(cItem)
        except Exception:
            cItem = {'url': fav_data}
            try:
                ok = int(cItem['url'])
                if ok:
                    return self.getVideoLink(cItem['url'])
            except Exception:
                pass
        return self.getLinksForVideo(cItem)

    def getFavouriteData(self, cItem):
        printDBG('TvpVod.getFavouriteData')
        params = {'type': cItem['type'], 'category': cItem.get('category', ''), 'title': cItem['title'], 'url': cItem['url'], 'desc': cItem.get('desc', ''), 'icon': cItem.get('icon', '')}
        if 'list_episodes' in cItem:
            params['list_episodes'] = cItem['list_episodes']
        return json_dumps(params)

    def setInitListFromFavouriteItem(self, fav_data):
        printDBG('TvpVod.setInitListFromFavouriteItem')
        try:
            params = json_loads(fav_data)
        except Exception:
            params = {}
            printExc()
        self.addDir(params)
        return True

    def listDigiMenu(self, cItem, nextCategory):
        printDBG("listDigiMenu")
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts:
            return
        cUrl = self.cm.meta['url']

        tmp = ph.find(data, ('<nav', '>', 'navigation--menu'), '</nav>', flags=0)[1]
        tmp = ph.findall(tmp, ('<li', '>'), '</li>', flags=0)
        for item in tmp:
            tmp = item.split('<ul', 1)
            if len(tmp) > 1:
                item = tmp[1]
            sTitle = ph.find(item, ('<a', '>'), '</a>')[1]
            sUrl = self.getFullUrl(ph.getattr(sTitle, 'href'), cUrl)
            sTitle = ph.clean_html(sTitle)
            if ',' not in sUrl:
                continue
            self.addDir(MergeDicts(cItem, {'good_for_fav': True, 'category': nextCategory, 'title': sTitle, 'url': sUrl}))

    def exploreDigiSite(self, cItem):
        printDBG("exploreDigiSite")
        sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
        if not sts:
            return
        cUrl = self.cm.meta['url']

        if cItem.get('allow_sort', True):
            tmp = ph.find(data, ('<ul', '>', 'dropdown--sort'), '</ul>', flags=0)[1]
            tmp = ph.findall(tmp, ('<a', '>'), '</a>')
            for item in tmp:
                title = ph.clean_html(item)
                url = self.getFullUrl(ph.getattr(item, 'href'), cUrl)
                if '{title},{id}' in url:
                    url = cUrl + self.cm.ph.getSearchGroups(item, '''href=['"][^?]+?(\?[^'^"]+?)['"]''')[0]
                self.addDir(MergeDicts(cItem, {'good_for_fav': False, 'allow_sort': False, 'title': title, 'url': url}))

            if self.currList:
                return

        tmp = ph.find(data, ('<section', '>', 'episodes'), '</section>', flags=0)[1]
        nextPage = ph.find(tmp, ('<div', '>', 'common--title--container'), '</div>', flags=0)[1]
        nextPage = self.getFullUrl(ph.search(nextPage, ph.A_HREF_URI_RE)[1], cUrl)
        if nextPage != '':
            sts, data = self.cm.getPage(nextPage, self.defaultParams)
            if not sts:
                return
            tmp = ph.find(data, ('<section', '>', 'episodes'), '</section>', flags=0)[1]
        if tmp != '':
            tmp = ph.findall(tmp, ('<div', '>', 'film--block'), '</div>', flags=0)
        else:
            tmp = ph.findall(data, ('<div', '>', 'film--block'), '</div>', flags=0)
        for item in tmp:
            title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            url = self.getFullUrl(ph.search(item, ph.A_HREF_URI_RE)[1], cUrl)
            icon = self.getFullUrl(ph.search(item, ph.IMAGE_SRC_URI_RE)[1], cUrl)

            descData = ph.findall(item, ('<p', '>'), '</p>', flags=0)
            if not descData and not title:
                continue
            if not title:
                title = self.cleanHtmlStr(descData[0])
            desc = []
            for idx in range(1, len(descData)):
                t = ph.clean_html(descData[idx])
                if t:
                    desc.append(t)
            desc = ' | '.join(desc) + '[/br]' + ph.clean_html(item[-1])
            params = MergeDicts(cItem, {'good_for_fav': True, 'allow_sort': True, 'url': url, 'desc': desc, 'icon': icon})
            if '/video/' in url:
                if title.startswith('odc.') and cItem.get('prev_title'):
                    title = '%s: %s' % (cItem['prev_title'], title)
                params.update({'title': title})
                self.addVideo(params)
            else:
                params.update({'title': title, 'prev_title': title})
                self.addDir(params)

        if self.currList:
            return

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('TvpVod.handleService start')
#        if None == self.loggedIn:
#            premium = config.plugins.iptvplayer.tvpvod_premium.value
#            if premium:
#                self.loggedIn, msg = self.tryTologin()
#                if self.loggedIn != True:
#                    self.sessionEx.open(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=10)

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        self.informAboutGeoBlockingIfNeeded('PL')

        name = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG("TvpVod.handleService: ---------> name[%s], category[%s] " % (name, category))
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        currItem = dict(self.currItem)
        currItem.pop('good_for_fav', None)

        if None != name and self.currItem.get('desc', '').startswith('Użytkownik'):
            currItem.pop('desc', None)

        if None == name:
            self.listsTab(TvpVod.VOD_CAT_TAB, {'name': 'category', 'desc': self.loginMessage})
    # STREAMS
        elif category == 'streams':
            self.listsTab(TvpVod.STREAMS_CAT_TAB, currItem)
        elif category == 'tvp3_streams':
            self.listTVP3Streams(currItem)
        elif category == 'week_epg':
            self.listWeekEPG(currItem, 'epg_items')
        elif category == 'epg_items':
            self.listEPGItems(currItem)

        elif category == 'tvpsport_streams':
            self.listTVPSportStreams(currItem, 'sub_items')
        elif category == 'sub_items':
            self.currList = currItem.get('sub_items', [])
    # TVP SPORT
        elif category == 'tvp_sport':
            self.listTVPSportCategories(currItem, 'tvp_sport_list_items')
    # LIST TVP SPORT VIDEOS
        elif category == 'tvp_sport_list_items':
            self.listTVPSportVideos(currItem)
        elif category == 'tvp_api':
            self.listCatalogApi(currItem, 'api_explore_item')
        elif category == 'api_explore_item':
            self.exploreApiItem(currItem, 'api_explore_item')

    # Reconstruction
        elif category == 'digi_menu':
            self.listDigiMenu(currItem, 'digi_explore_site')
        elif category == 'digi_explore_site':
            self.exploreDigiSite(currItem)

    #WYSZUKAJ
        elif category == "search":
            cItem = dict(currItem)
            cItem.update({'category': 'list_search', 'searchPattern': searchPattern, 'searchType': searchType, 'search_item': False})
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == "list_search":
            cItem = dict(currItem)
            searchPattern = cItem.get('searchPattern', '')
            searchType = cItem.get('searchType', '')
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name': 'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, TvpVod(), True, [])

    def getSearchTypes(self):
        searchTypesOptions = []
        searchTypesOptions.append(("Filmy", "movies"))
        searchTypesOptions.append(("Seriale", "series"))
        return searchTypesOptions