# -*- coding: utf-8 -*-

import urllib, urllib2, re
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import *
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.jsinterp import JSInterpreter
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.base import InfoExtractor
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError

try: import json
except: import simplejson as json

from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry

config.plugins.iptvplayer.vevo_default_quality = ConfigSelection(default = "1228800", choices = [
("0", _("the worst")),
("245760",  "30 KB/s"), 
("655360",  "80 KB/s"), 
("409600",  "50 KB/s"), 
("655360",  "80 KB/s"), 
("737280",  "90 KB/s"), 
("1228800", "150 KB/s"),
("1638400", "200 KB/s"),
("2867200", "350 KB/s"),
("4096000", "500 KB/s"),
("4915200", "600 KB/s"),
("6553600", "800 KB/s"),
("99999999", _("the best"))
])
config.plugins.iptvplayer.vevo_use_default_quality = ConfigYesNo(default = True)
config.plugins.iptvplayer.vevo_allow_hls           = ConfigYesNo(default = True)

class VevoIE(InfoExtractor):
    """
    Accepts urls from vevo.com or in the format 'vevo:{id}'
    (currently used by MTVIE and MySpaceIE)
    """
    _VALID_URL = r'''(?x)
        (?:https?://www\.vevo\.com/watch/(?:[^/]+/(?:[^/]+/)?)?|
           https?://cache\.vevo\.com/m/html/embed\.html\?video=|
           https?://videoplayer\.vevo\.com/embed/embedded\?videoId=|
           vevo:)
        (?P<id>[^&?#]+)'''
    _SMIL_BASE_URL = 'http://smil.lvl3.vevo.com/'

    def __init__(self):
        InfoExtractor.__init__(self)
        self._real_initialize()
        
    def printDBG(self, data):
        printDBG("=======================================================")
        printDBG(data)
        printDBG("=======================================================")
    
    def _real_initialize(self):
        webpage = self._download_webpage(
            'http://www.vevo.com/auth', None,
            note='Retrieving oauth token',
            errnote='Unable to retrieve oauth token',
            fatal=False,
            data=b'')
        try:
            self.authData = byteify(json.loads(webpage))
        except:
            printExc()
            self.authData = {}
        self._oauth_token = self.authData.get('access_token')

    def _formats_from_json(self, video_info):
        last_version = {'version': -1}
        for version in video_info['videoVersions']:
            # These are the HTTP downloads, other types are for different manifests
            if version['sourceType'] == 2:
                if version['version'] > last_version['version']:
                    last_version = version
        if last_version['version'] == -1:
            raise ExtractorError('Unable to extract last version of the video')

        renditions = re.compile('<rendition ([^>]+?)>').findall(last_version['data'])
        formats = []
        # Already sorted from worst to best quality
        for attr in renditions:
            #format_note = '%(videoCodec)s@%(videoBitrate)4sk, %(audioCodec)s@%(audioBitrate)3sk' % attr
            formats.append({
                'url': self.xmlGetArg(attr, 'url'),
                'format_id': self.xmlGetArg(attr, 'name'),
                'bitrate': (int(self.xmlGetArg(attr, 'videoBitrate')) + int(self.xmlGetArg(attr, 'audioBitrate')))*1000,
                #'format_note': format_note,
                'height': int(self.xmlGetArg(attr, 'frameheight')),
                'width': int(self.xmlGetArg(attr, 'frameWidth')),
            })
        return formats

    def _formats_from_smil(self, smil_xml):
        formats = []
        
        els = re.compile('<video ([^>]+?)>').findall(smil_xml)
        for el in els:
            src =  self.xmlGetArg(el, 'src')
            m = re.match(r'''(?xi)
                (?P<ext>[a-z0-9]+):
                (?P<path>
                    [/a-z0-9]+     # The directory and main part of the URL
                    _(?P<cbr>[0-9]+)k
                    _(?P<width>[0-9]+)x(?P<height>[0-9]+)
                    _(?P<vcodec>[a-z0-9]+)
                    _(?P<vbr>[0-9]+)
                    _(?P<acodec>[a-z0-9]+)
                    _(?P<abr>[0-9]+)
                    \.[a-z0-9]+  # File extension
                )''', src)
            if not m:
                continue

            format_url = self._SMIL_BASE_URL + m.group('path')
            formats.append({
                'url': format_url,
                'format_id': 'SMIL_' + m.group('cbr'),
                'vcodec': m.group('vcodec'),
                'acodec': m.group('acodec'),
                'bitrate': (int(m.group('vbr')) + int(m.group('abr'))) * 1000,
                'ext': m.group('ext'),
                'width': int(m.group('width')),
                'height': int(m.group('height')),
            })
        return formats

    def _download_api_formats(self, video_id):
        if not self._oauth_token:
            self._downloader.report_warning(
                'No oauth token available, skipping API HLS download')
            return []

        api_url = 'https://apiv2.vevo.com/video/%s/streams/hls?token=%s' % (
            video_id, self._oauth_token)
        api_data = self._download_json(
            api_url, video_id,
            note='Downloading HLS formats',
            errnote='Failed to download HLS format list', fatal=False)
        if api_data is None:
            return []

        m3u8_url = api_data[0]['url']
        return self._extract_m3u8_formats(
            m3u8_url, video_id, entry_protocol='m3u8_native', ext='mp4',
            preference=0)

    def _real_extract(self, url, hls=None, smil=True):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        
        if hls == None: hls = config.plugins.iptvplayer.vevo_allow_hls.value

        json_url = 'http://videoplayer.vevo.com/VideoService/AuthenticateVideo?isrc=%s' % video_id
        response = self._download_json(json_url, video_id)
        video_info = response['video']

        if not video_info:
            if 'statusMessage' in response:
                SetIPTVPlayerLastHostError(response['statusMessage'])
                raise ExtractorError('%s said: %s' % (self.IE_NAME, response['statusMessage']), expected=True)
            raise ExtractorError('Unable to extract videos')

        formats = self._formats_from_json(video_info)

        is_explicit = video_info.get('isExplicit')
        if is_explicit is True:
            age_limit = 18
        elif is_explicit is False:
            age_limit = 0
        else:
            age_limit = None

        # Download via HLS API
        if hls or 0 == len(formats):
            formats.extend(self._download_api_formats(video_id))

        # Download SMIL
        if smil or 0 == len(formats):
            smil_blocks = sorted((
                f for f in video_info['videoVersions']
                if f['sourceType'] == 13),
                key=lambda f: f['version'])
            smil_url = '%s/Video/V2/VFILE/%s/%sr.smil' % (
                self._SMIL_BASE_URL, video_id, video_id.lower())
            if smil_blocks:
                smil_url_m = self._search_regex(
                    r'url="([^"]+)"', smil_blocks[-1]['data'], 'SMIL URL',
                    default=None)
                if smil_url_m is not None:
                    smil_url = smil_url_m
            if smil_url:
                smil_xml = self._download_webpage(
                    smil_url, video_id, 'Downloading SMIL info', fatal=False)
                if smil_xml:
                    formats.extend(self._formats_from_smil(smil_xml))

        return {
            'id': video_id,
            'title': video_info['title'],
            'formats': formats,
            'thumbnail': video_info['imageUrl'],
            'uploader': video_info['mainArtists'][0]['artistName'],
            'duration': video_info['duration'],
            'age_limit': age_limit,
        }