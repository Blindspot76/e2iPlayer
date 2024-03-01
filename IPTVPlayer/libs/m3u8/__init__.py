import os
import re
from Plugins.Extensions.IPTVPlayer.p2p3.UrlParse import urlparse, urljoin
from Plugins.Extensions.IPTVPlayer.p2p3.UrlLib import urllib2_urlopen

from Plugins.Extensions.IPTVPlayer.libs.m3u8.model import M3U8, Playlist
from Plugins.Extensions.IPTVPlayer.libs.m3u8.parser import parse, is_url

__all__ = 'M3U8', 'Playlist', 'loads', 'load', 'parse'


def inits(content, uri):
    '''
    Given a string with a m3u8 content and uri from which
    this content was downloaded returns a M3U8 object.
    Raises ValueError if invalid content
    '''
    parsed_url = urlparse(uri)
    prefix = parsed_url.scheme + '://' + parsed_url.netloc
    base_path = os.path.normpath(parsed_url.path + '/..')
    base_uri = urljoin(prefix, base_path)
    return M3U8(content, base_uri=base_uri)


def loads(content):
    '''
    Given a string with a m3u8 content, returns a M3U8 object.
    Raises ValueError if invalid content
    '''
    return M3U8(content)


def load(uri):
    '''
    Retrieves the content from a given URI and returns a M3U8 object.
    Raises ValueError if invalid content or IOError if request fails.
    '''
    if is_url(uri):
        return _load_from_uri(uri)
    else:
        return _load_from_file(uri)


def _load_from_uri(uri):
    open = urllib2_urlopen(uri)
    uri = open.geturl()
    content = open.read().strip()
    parsed_url = urlparse(uri)
    prefix = parsed_url.scheme + '://' + parsed_url.netloc
    base_path = os.path.normpath(parsed_url.path + '/..')
    base_uri = urljoin(prefix, base_path)
    return M3U8(content, base_uri=base_uri)


def _load_from_file(uri):
    with open(uri) as fileobj:
        raw_content = fileobj.read().strip()
    base_uri = os.path.dirname(uri)
    return M3U8(raw_content, base_uri=base_uri)
