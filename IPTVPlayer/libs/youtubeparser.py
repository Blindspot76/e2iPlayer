# -*- coding: utf-8 -*-
# Blindspot - 2020-08-24
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.youtube import YoutubeIE
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, IsExecutable
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import decorateUrl
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getMPDLinksWithMeta
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs import ph
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
from urlparse import urlparse, urlunparse, parse_qsl
from datetime import timedelta
from Components.config import config, ConfigSelection, ConfigYesNo
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.ytformat        = ConfigSelection(default = "mp4", choices = [("flv, mp4", "flv, mp4"),("flv", "flv"),("mp4", "mp4")]) 
config.plugins.iptvplayer.ytDefaultformat = ConfigSelection(default = "720", choices = [("0", _("the worst")), ("144", "144p"), ("240", "240p"), ("360", "360p"),("720", "720p"), ("1080", "1080p"), ("1440", "1440p"), ("2160", "2160p"), ("9999", _("the best"))])
config.plugins.iptvplayer.ytUseDF         = ConfigYesNo(default = True)
config.plugins.iptvplayer.ytAgeGate       = ConfigYesNo(default = False)
config.plugins.iptvplayer.ytVP9           = ConfigYesNo(default = False)
config.plugins.iptvplayer.ytShowDash      = ConfigSelection(default = "auto", choices = [("auto", _("Auto")),("true", _("Yes")),("false", _("No"))])
config.plugins.iptvplayer.ytSortBy        = ConfigSelection(default = "", choices = [("", _("Relevance")),("video_date_uploaded", _("Upload date")),("video_view_count", _("View count")),("video_avg_rating", _("Rating"))]) 


class YouTubeParser():
    
    def __init__(self):
        self.cm = common()
        self.HTTP_HEADER = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                            'X-YouTube-Client-Name': '1', 
                            'X-YouTube-Client-Version': '2.20200207.03.01', 
                            'X-Requested-With':'XMLHttpRequest'
                            }
        self.http_params={'header':self.HTTP_HEADER, 'return_data': True}
        self.postdata = {}
        self.sessionToken = ""
        
        return

    @staticmethod
    def isDashAllowed():
        value = config.plugins.iptvplayer.ytShowDash.value
        printDBG("ALLOW DASH: >> %s" % value)
        if value == "true" and IsExecutable('ffmpeg'):
            return True
        elif value == "auto" and IsExecutable('ffmpeg') and IsExecutable(config.plugins.iptvplayer.exteplayer3path.value):
            return True
        else:
            return False

    @staticmethod
    def isVP9Allowed():
        value = config.plugins.iptvplayer.ytVP9.value
        printDBG("1. ALLOW VP9: >> %s" % value)
        value = YouTubeParser.isDashAllowed() and value
        printDBG("2. ALLOW VP9: >> %s" % value)
        return value

    @staticmethod
    def isAgeGateAllowed():
        value = config.plugins.iptvplayer.ytAgeGate.value
        printDBG("ALLOW Age-Gate bypass: >> %s" % value)
        return value
        
    def checkSessionToken(self, data):
        if not self.sessionToken:
            token = self.cm.ph.getSearchGroups(data, '''"XSRF_TOKEN":"([^"]+?)"''')[0]
            if token:
                printDBG("Update session token: %s" % token)
                self.sessionToken = token
                self.postdata = {"session_token": token}


    def getDirectLinks(self, url, formats = 'flv, mp4', dash=True, dashSepareteList = False, allowVP9 = None, allowAgeGate = None):
        printDBG("YouTubeParser.getDirectLinks")
        list = []
        try:
            if self.cm.isValidUrl(url) and '/channel/' in url and url.endswith('/live'):
                sts, data = self.cm.getPage(url)
                if sts:
                    videoId = self.cm.ph.getSearchGroups(data, '''<meta[^>]+?itemprop=['"]videoId['"][^>]+?content=['"]([^'^"]+?)['"]''')[0]
                    if videoId == '': videoId = self.cm.ph.getSearchGroups(data, '''['"]REDIRECT_TO_VIDEO['"]\s*\,\s*['"]([^'^"]+?)['"]''')[0]
                    if videoId == '': videoId = ph.search(data, 'video_id=(.*?)"')[0]
                    if videoId != '': url = 'https://www.youtube.com/watch?v=' + videoId
            list = YoutubeIE()._real_extract(url, allowVP9 = allowVP9, allowAgeGate = allowAgeGate)
        except Exception:
            printExc()
            if dashSepareteList:
                return [], []
            else: return []
        
        reNum = re.compile('([0-9]+)')
        retHLSList = []
        retList = []
        dashList = []
        # filter dash
        dashAudioLists = []
        dashVideoLists = []
        if dash:
            # separete audio and video links
            for item in list:
                if 'mp4a' == item['ext']:
                    dashAudioLists.append(item)
                elif item['ext'] in ('mp4v', 'webmv'):
                    dashVideoLists.append(item)
                elif 'mpd' == item['ext']:
                    tmpList = getMPDLinksWithMeta(item['url'], checkExt=False)
                    printDBG(tmpList)
                    for idx in range(len(tmpList)):
                        tmpList[idx]['format'] = "%sx%s" % (tmpList[idx].get('height', 0), tmpList[idx].get('width', 0))
                        tmpList[idx]['ext']  = "mpd"
                        tmpList[idx]['dash'] = True
                    dashList.extend(tmpList)
            # sort by quality -> format
            def _key(x):
                if x['format'].startswith('>'):
                     int(x['format'][1:-1])
                else:
                     int(ph.search(x['format'], reNum)[0])
                    
            dashAudioLists = sorted(dashAudioLists, key=_key, reverse=True)
            dashVideoLists = sorted(dashVideoLists, key=_key, reverse=True)

        for item in list:
            printDBG(">>>>>>>>>>>>>>>>>>>>>")
            printDBG( item )
            printDBG("<<<<<<<<<<<<<<<<<<<<<")
            if -1 < formats.find( item['ext'] ):
                if 'yes' == item['m3u8']:
                    format = re.search('([0-9]+?)p$', item['format'])
                    if format != None:
                        item['format'] = format.group(1) + "x"
                        item['ext']  = item['ext'] + "_M3U8"
                        item['url']  = decorateUrl(item['url'], {"iptv_proto":"m3u8"})
                        retHLSList.append(item)
                else:
                    format = re.search('([0-9]+?x[0-9]+?$)', item['format'])
                    if format != None:
                        item['format'] = format.group(1)
                        item['url']  = decorateUrl(item['url'])
                        retList.append(item)
        
        if len(dashAudioLists):
            # use best audio
            for item in dashVideoLists:
                item = dict(item)
                item["url"] = decorateUrl("merge://audio_url|video_url", {'audio_url':dashAudioLists[0]['url'], 'video_url':item['url']})
                dashList.append(item)
        
        # try to get hls format with alternative method 
        if 0 == len(retList):
            try:
                video_id = YoutubeIE()._extract_id(url)
                url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id
                sts, data = self.cm.getPage(url, {'header':{'User-agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'}})
                if sts:
                    data = data.replace('\\"', '"').replace('\\\\\\/', '/')
                    hlsUrl = self.cm.ph.getSearchGroups(data, '''"hlsvp"\s*:\s*"(https?://[^"]+?)"''')[0]
                    hlsUrl= json_loads('"%s"' % hlsUrl)
                    if self.cm.isValidUrl(hlsUrl):
                        hlsList = getDirectM3U8Playlist(hlsUrl)
                        if len(hlsList):
                            dashList = []
                            for item in hlsList:
                                item['format'] = "%sx%s" % (item.get('with', 0), item.get('heigth', 0))
                                item['ext']  = "m3u8"
                                item['m3u8'] = True
                                retList.append(item)
            except Exception:
                printExc()
            if 0 == len(retList):
                retList = retHLSList
            
            if dash:
                try:
                    sts, data = self.cm.getPage(url, {'header':{'User-agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}})
                    data = data.replace('\\"', '"').replace('\\\\\\/', '/').replace('\\/', '/')
                    dashUrl = self.cm.ph.getSearchGroups(data, '''"dashmpd"\s*:\s*"(https?://[^"]+?)"''')[0]
                    dashUrl = json_loads('"%s"' % dashUrl)
                    if '?' not in dashUrl: dashUrl += '?mpd_version=5'
                    else: dashUrl += '&mpd_version=5'
                    printDBG("DASH URL >> [%s]" % dashUrl)
                    if self.cm.isValidUrl(dashUrl):
                        dashList = getMPDLinksWithMeta(dashUrl, checkExt=False)
                        printDBG(dashList)
                        for idx in range(len(dashList)):
                            dashList[idx]['format'] = "%sx%s" % (dashList[idx].get('height', 0), dashList[idx].get('width', 0))
                            dashList[idx]['ext']  = "mpd"
                            dashList[idx]['dash'] = True
                except Exception:
                    printExc()
        
        for idx in range(len(retList)):
            if retList[idx].get('m3u8', False):
                retList[idx]['url'] = strwithmeta(retList[idx]['url'], {'iptv_m3u8_live_start_index':-30})
        
        if dashSepareteList:
            return retList, dashList
        else:
            retList.extend(dashList)
            return retList
        
        
    ########################################################
    # List Base PARSER
    ########################################################
    def parseListBase(self, data, type='video'):
        printDBG("parseListBase----------------")
        urlPatterns = { 'video'    :    ['video'   , 'href="[ ]*?(/watch\?v=[^"]+?)"'            , ''], 
                        'channel'  :    ['category', 'href="(/[^"]+?)"'                     , ''],
                        'playlist' :    ['category', 'list=([^"]+?)"'                       , '/playlist?list='],
                        'movie'    :    ['video'   , 'data-context-item-id="([^"]+?)"'      , '/watch?v='],
                        'live'     :    ['video'   , 'href="(/watch\?v=[^"]+?)"'            , ''],
                        'tray'     :    ['video'   , 'data-video-id="([^"]+?)"'             , '/watch?v='], }
        currList = []
        for i in range(len(data)):
            #printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # get requaired params
            url   = urlPatterns[type][2] + self.getAttributes(urlPatterns[type][1], data[i])
            
            # get title
            title = '' #self.getAttributes('title="([^"]+?)"', data[i])
            if '' == title: title = self.getAttributes('data-context-item-title="([^"]+?)"', data[i])
            if '' == title: title = self.getAttributes('data-video-title="([^"]+?)"', data[i])
            if '' == title: sts,title = CParsingHelper.getDataBeetwenMarkers(data[i], '<h3 class="yt-lockup-title">', '</h3>', False) 
            if '' == title: sts,title = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('<span [^>]*?class="title[^>]*?>'), re.compile('</span>'), False) 
            if '' == title: sts,title = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('class="pl-video-title-link[^>]*?>'), re.compile('<'), False)
            
            if '' == title:
                titleMarker = self.cm.ph.getSearchGroups(data[i], '(<[^">]+?"yt-lockup-title[^"]*?"[^>]*?>)')[0]
                if '' != titleMarker:
                    tidx = titleMarker.find(' ')
                    if tidx > 0:
                        tmarker = titleMarker[1:tidx]
                        title = self.cm.ph.getDataBeetwenMarkers(data[i],  titleMarker, '</%s>' % tmarker)[1]
            
            if '' != title:
                title = CParsingHelper.cleanHtmlStr(title)
            if i == 0:
                printDBG(data[i])
                
            img   = self.getAttributes('data-thumb="([^"]+?\.jpg[^"]*?)"', data[i])
            if '' == img:  img = self.getAttributes('src="([^"]+?\.jpg[^"]*?)"', data[i])
            if '' == img:  img = self.getAttributes('<img[^>]+?data\-thumb="([^"]+?)"', data[i])
            if '' == img:  img = self.getAttributes('<img[^>]+?src="([^"]+?)"', data[i])
            if '.gif' in img: img = ''
            time  = self.getAttributes('data-context-item-time="([^"]+?)"', data[i])
            if '' == time: time  = self.getAttributes('class="video-time">([^<]+?)</span>', data[i])
            if '' == time: sts, time = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('pl-video-time"[^>]*?>'), re.compile('<'), False)
            if '' == time: sts, time = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('timestamp"[^>]*?>'), re.compile('<'), False)
            time = time.strip()
            
            # desc
            descTab = []
            
            desc = self.cm.ph.getDataBeetwenMarkers(data[i], '<div class="yt-lockup-meta', '</div>')[1]
            if desc != '': descTab.append(desc)
            desc = self.cm.ph.getDataBeetwenMarkers(data[i], '<span class="formatted-video-count', '</span>')[1]
            if desc != '': descTab.append(desc)
            
            desc  = self.cm.ph.getDataBeetwenReMarkers(data[i], re.compile('class="video-description[^>]+?>'), re.compile('</p>'), False)[1]
            if '' == desc: desc = self.cm.ph.getDataBeetwenReMarkers(data[i], re.compile('class="yt-lockup-description[^>]+?>'), re.compile('</div>'), False)[1]
            if desc != '': descTab.append(desc)
            
            newDescTab = []
            for desc in descTab:
                desc = CParsingHelper.cleanHtmlStr(desc)
                if desc != '':
                    newDescTab.append(desc)
            
            urlTmp = url.split(';')
            if len(urlTmp) > 0: url = urlTmp[0]
            if type == 'video': url = url.split('&')[0] 
            #printDBG("#####################################") 
            #printDBG('url   [%s] ' % url)
            #printDBG('title [%s] ' % title)
            #printDBG('img   [%s] ' % img)
            #printDBG('time  [%s] ' % time)
            #printDBG('desc  [%s] ' % desc)
            if title != '' and url != '' and img != '':
                correctUrlTab = [url, img]
                for i in range(len(correctUrlTab)):
                    if not correctUrlTab[i].startswith('http:') and not correctUrlTab[i].startswith('https:'):
                        if correctUrlTab[i].startswith("//"):
                            correctUrlTab[i] = 'http:' + correctUrlTab[i]
                        else:
                            correctUrlTab[i] = 'http://www.youtube.com' + correctUrlTab[i]
                    #else:
                    #    if correctUrlTab[i].startswith('https:'):
                    #        correctUrlTab[i] = "http:" + correctUrlTab[i][6:]

                title = CParsingHelper.cleanHtmlStr(title)
                params = {'type': urlPatterns[type][0], 'category': type, 'title': title, 'url': correctUrlTab[0], 'icon': correctUrlTab[1].replace('&amp;', '&'), 'time': time, 'desc': '[/br]'.join(newDescTab)}
                currList.append(params)

        return currList
    #end parseListBase
    
    def getMenuItemData(self, itemJson):
        
        try:
            title = itemJson['title']['simpleText'] 
            icon = self.getThumbnailUrl(itemJson["thumbnail"]["thumbnails"])

            try:
                feedId = itemJson["navigationEndpoint"]["browseEndpoint"]["params"]
                url = "https://www.youtube.com/feed/trending?bp=%s&pbj=1" % feedId
                cat = "feeds_" + title
            except:
                try:
                    url = "https://www.youtube.com" + itemJson["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"]
                except:
                    printExc()
                    return {}

            if '/channel/' in url:
                return {'type': 'category', 'category': 'channel', 'title': title, 'url': url, 'icon': icon, 'time': '' ,'desc': ''}
            else:
                return {'type': 'feed', 'category': cat, 'title': title, 'url': url, 'icon': icon, 'time': '' ,'desc': ''}
                
        except:
            printExc()
            return {}
    
    def getFeedsList(self, url):
        printDBG('YouTubeParser.getFeedList')
        
        currList = []
        try:
            sts,data =  self.cm.getPage(url, self.http_params)
            if sts:
                self.checkSessionToken(data)

                data2 = self.cm.ph.getDataBeetwenMarkers(data,"window[\"ytInitialData\"] =", "};", False)[1]
                
                try:
                    response = json_loads(data2 + "}")
                
                    submenu = response['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['subMenu']
                    for item in submenu["channelListSubMenuRenderer"]["contents"]:
                        menuJson = item.get("channelListSubMenuAvatarRenderer", '') 
                        if menuJson:
                            params = self.getMenuItemData(menuJson)
                            
                            if params:
                                printDBG(str(params))
                                currList.append(params)    
                except:
                    printExc()

        except Exception:
            printExc()
            
        return currList

    
    def getVideoFromFeed(self, url):
        printDBG('YouTubeParser.getVideosFromFeed')
        
        currList = []
        try:
            sts,data =  self.cm.getPage(url, self.http_params)
            if sts:
                self.checkSessionToken(data)

                try:
                    response = json_loads(data)
                    
                    rr = {}
                    for r in response:
                        if r.get("response",""):
                            rr = r
                            break

                    if not rr:
                        return []
                    
                    r1 = rr["response"]["contents"]['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents']
                    r2 = r1[0]['itemSectionRenderer']['contents'][0]["shelfRenderer"]["content"]["expandedShelfContentsRenderer"]["items"]
                    
                    for item in r2:
                        chJson = item.get('channelRenderer', '')
                        videoJson = item.get('videoRenderer','')
                        plJson = item.get('playlistRenderer','')
                        
                        params = {}
                        if videoJson:
                            # it is a video
                            params = self.getVideoData(videoJson)
                        elif chJson:
                            # it is a channel
                            params = self.getChannelData(chJson)
                        elif plJson:
                            # it is a playlist
                            params = self.getPlaylistData(plJson)
                            
                        if params:
                            printDBG(str(params))
                            currList.append(params)

                except:
                    printExc()

        except Exception:
            printExc()

        return currList
    
    ########################################################
    # Tray List PARSER
    ########################################################
    def getVideosFromTraylist(self, url, category, page, cItem):
        printDBG('YouTubeParser.getVideosFromTraylist')
        return self.getVideosApiPlayList(url, category, page, cItem)

        currList = []
        try:
            sts,data =  self.cm.getPage(url, self.http_params)
            if sts:
                sts,data = CParsingHelper.getDataBeetwenMarkers(data, 'class="playlist-videos-container', '<div class="watch-sidebar-body">', False)
                data = data.split('class="yt-uix-scroller-scroll-unit')
                del data[0]
                return self.parseListBase(data, 'tray')
        except Exception:
            printExc()
            return []
            
        return currList
    # end getVideosFromPlaylist
       
    ########################################################
    # PLAYLIST PARSER
    ########################################################
    def getVideosFromPlaylist(self, url, category, page, cItem):
        printDBG('YouTubeParser.getVideosFromPlaylist')
        currList = []
        page = 0
        currList = []

        try:
            sts,data =  self.cm.getPage(url, self.http_params, self.postdata)
            #printDBG('YouTubeParser.getVideosFromPlaylist data[%s]' % (data) )

            if sts:
                if data:
                    data2 = self.cm.ph.getAllItemsBeetwenMarkers(data, '"playlistVideoRenderer"', '}},')
                    for item in data2:
                        tmp = item.replace('}},','}}}}').replace('\u0026','&')
                        title = self.cm.ph.getSearchGroups(item, '''"label"\s*:\s*"([^"]+?)"''')[0]
                        url = 'http://www.youtube.com/watch?v=%s' % self.cm.ph.getSearchGroups(item, '''"videoId"\s*:\s*"([^"]+?)"''')[0]
                        icon = self.cm.ph.getSearchGroups(item, '''"url"\s*:\s*"([^"]+?)"''')[0]
                        time = ''
                        desc = title
                        params = {'type': 'video', 'category': 'video', 'title': title, 'url': url, 'icon': icon.replace('&amp;', '&'), 'time': time, 'desc': desc}
                        currList.append(params)
                    data2 = None
                   
                    # nextPage
                try:
                    match = re.search('"continuation":"([^"]+?)"', data)
                    xsrf_token = data.split("XSRF_TOKEN\":\"")[1].split("\"")[0]
                    ctoken = data.split("\"nextContinuationData\":{\"continuation\":\"")[1].split("\"")[0]
                    itct = data.split("\"{}\",\"clickTrackingParams\":\"".format(ctoken))[1].split("\"")[0]
                    self.postdata = {"session_token": xsrf_token}
                    if not match: nextPage = ""
                    else: nextPage = 'https://www.youtube.com/comment_service_ajax?action_get_comments=1&continuation=%s&pbj=1&ctoken=%s&itct=%s' % (ctoken, ctoken, itct)
                except Exception:
                    printExc()
                try:
                    if '' != nextPage:
                        item = dict(cItem)
                        item.update({'title': _("Next page"), 'page': str(int(page) + 1), 'url': nextPage})
                        currList.append(item)
                except Exception:
                    printExc()
        except Exception:
            printExc()
            return []
        return currList
    # end getVideosFromPlaylist

    ########################################################
    # CHANNEL LIST PARSER
    ########################################################
    def getAttributes(self, regx, data, num=1):
        match = re.search(regx, data)
        if not match: return ''
        else: return match.group(1)
        
    def getVideosFromChannelList(self, url, category, page, cItem):
        printDBG('YouTubeParser.getVideosFromChannelList cItem[%s]' % (cItem) )
        printDBG('YouTubeParser.getVideosFromChannelList page[%s]' % (page) )

        page = 0
        currList = []

        try:
            sts,data =  self.cm.getPage(url, self.http_params, self.postdata)
            #printDBG('YouTubeParser.getVideosFromChannelList data[%s]' % (data) )

            if sts:
                if data:
                    data2 = self.cm.ph.getAllItemsBeetwenMarkers(data, '"gridVideoRenderer"', '}},')
                    for item in data2:
                        tmp = item.replace('}},','}}}}').replace('\u0026','&')
                        icon = self.cm.ph.getSearchGroups(item, '''"url"\s*:\s*"([^"]+?)"''')[0] 
                        url = 'http://www.youtube.com/watch?v=%s' % self.cm.ph.getSearchGroups(item, '''"videoId"\s*:\s*"([^"]+?)"''')[0]
                        data = json_loads('{'+tmp+'}')
                        title = data['gridVideoRenderer']['title']['accessibility']['accessibilityData']['label'] 
                        time = ''
                        desc = title
                        params = {'type': 'video', 'category': 'video', 'title': title, 'url': url, 'icon': icon.replace('&amp;', '&'), 'time': time, 'desc': desc}
                        currList.append(params)
                    data2 = None

                    # nextPage
                try:
                    match = re.search('"continuation":"([^"]+?)"', data)
                    xsrf_token = data.split("XSRF_TOKEN\":\"")[1].split("\"")[0]
                    ctoken = data.split("\"nextContinuationData\":{\"continuation\":\"")[1].split("\"")[0]
                    itct = data.split("\"{}\",\"clickTrackingParams\":\"".format(ctoken))[1].split("\"")[0]
                    self.postdata = {"session_token": xsrf_token}
                    if not match: nextPage = ""
                    else: nextPage = 'https://www.youtube.com/comment_service_ajax?action_get_comments=1&continuation=%s&pbj=1&ctoken=%s&itct=%s' % (ctoken, ctoken, itct)
                except Exception:
                    printExc()
                try:
                    if '' != nextPage:
                        item = dict(cItem)
                        item.update({'title': _("Next page"), 'page': str(int(page) + 1), 'url': nextPage})
                        currList.append(item)
                except Exception:
                    printExc()
        except Exception:
            printExc()
            return []
        return currList
    # end getVideosFromChannel

    ########################################################
    # SEARCH PARSER
    ########################################################
    #def getVideosFromSearch(self, pattern, page='1'):
    def getSearchResult(self, pattern, searchType, page, nextPageCategory, sortBy=''):
        printDBG('YouTubeParser.getSearchResult pattern[%s], searchType[%s], page[%s]' % (pattern, searchType, page))
        currList = []
        try:
            url = 'http://www.youtube.com/results?search_query=%s&filters=%s&search_sort=%s&page=%s' % (pattern, searchType, sortBy, page) 
            sts,data =  self.cm.getPage(url, self.http_params)
            #printDBG('YouTubeParser.getSearchResult pattern[%s], searchType[%s], page[%s]' % (pattern, searchType, data))

            if sts:
                if data:
                    data2 = self.cm.ph.getAllItemsBeetwenMarkers(data, '"videoRenderer"', '}},')
                    for item in data2:
                        tmp = item.replace('}},','}}}').replace('\u0026','&')
                        icon = self.cm.ph.getSearchGroups(item, '''"url"\s*:\s*"([^"]+?)"''')[0]
                        url = 'http://www.youtube.com/watch?v=%s' % self.cm.ph.getSearchGroups(item, '''"videoId"\s*:\s*"([^"]+?)"''')[0]
                        data = json_loads('{'+tmp+'}')
                        title = data['videoRenderer']['title']['accessibility']['accessibilityData']['label'] 
                        time = ''
                        desc = title
                        params = {'type': 'video', 'category': 'video', 'title': title, 'url': url, 'icon': icon.replace('&amp;', '&'), 'time': time, 'desc': desc}
                        currList.append(params)
                    data2 = None

                    # nextPage
                try:
                    match = re.search('"continuation":"([^"]+?)"', data)
                    xsrf_token = data.split("XSRF_TOKEN\":\"")[1].split("\"")[0]
                    ctoken = data.split("\"nextContinuationData\":{\"continuation\":\"")[1].split("\"")[0]
                    itct = data.split("\"{}\",\"clickTrackingParams\":\"".format(ctoken))[1].split("\"")[0]
                    self.postdata = {"session_token": xsrf_token}
                    if not match: nextPage = ""
                    else: nextPage = 'https://www.youtube.com/comment_service_ajax?action_get_comments=1&continuation=%s&pbj=1&ctoken=%s&itct=%s' % (ctoken, ctoken, itct)
                except Exception:
                    printExc()
                try:
                    if '' != nextPage:
                        item = dict(cItem)
                        item.update({'title': _("Next page"), 'page': str(int(page) + 1), 'url': nextPage})
                        currList.append(item)
                except Exception:
                    printExc()
        except Exception:
            printExc()
            return []
        return currList
                
    # end getVideosFromSearch
    
    ########################################################
    # PLAYLISTS PARSER
    ########################################################
    def getListPlaylistsItems(self, url, category, page, cItem):
        printDBG('YouTubeParser.getListPlaylistsItems page[%s]' % (page))
        currList = []
        try:
            sts,data =  self.cm.getPage(url, self.http_params)
            if sts:
                #self.cm.ph.writeToFile('/mnt/new2/yt.html', data)
                if '1' == page:
                    sts,data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="yt-lockup clearfix', 'footer-container')
                else:
                    data = json_loads(data)
                    data = data['load_more_widget_html'] + '\n' + data['content_html']
                    
                # nextPage
                match = re.search('data-uix-load-more-href="([^"]+?)"', data)
                if not match: 
                    nextPage = ""
                else: 
                    nextPage = match.group(1).replace('&amp;', '&')
                
                itemsTab = data.split('<div class="yt-lockup clearfix')
                printDBG(itemsTab[0])
                currList = self.parseListBase(itemsTab, 'playlist')
                if '' != nextPage:
                    item = dict(cItem)
                    item.update({'title': 'Następna strona', 'page': str(int(page) + 1), 'url': 'http://www.youtube.com' + nextPage})
                    currList.append(item)
        except Exception:
            printExc()
            
        return currList
    # end getListPlaylistsItems
    
    
    ########################################################
    # PLAYLIST API
    ########################################################
    def getVideosApiPlayList(self, url, category, page, cItem):
        printDBG('YouTubeParser.getVideosApiPlayList url[%s]' % url)
        playlistID = self.cm.ph.getSearchGroups(url + '&', 'list=([^&]+?)&')[0]
        baseUrl = 'https://www.youtube.com/list_ajax?style=json&action_get_list=1&list=%s' % playlistID

        currList = []
        if baseUrl != '':
            sts, data =  self.cm.getPage(baseUrl, self.http_params)
            try:
                data = json_loads(data)['video']
                for item in data:
                    url   = 'http://www.youtube.com/watch?v=' + item['encrypted_id']
                    title = item['title']
                    img   = item['thumbnail']
                    time  = item['length_seconds']
                    if '' != time: time = str( timedelta( seconds = int(time) ) )
                    if time.startswith("0:"): time = time[2:]
                    desc  = item['description']
                    try:
                        added = item['added']
                    except Exception:
                        printExc()
                        added = ''
                    params = {'type': 'video', 'category': 'video', 'title': title, 'url': url, 'icon': img, 'time': time, 'desc': added +'\n'+ desc}
                    currList.append(params)
            except Exception:
                printExc()
        return currList    

