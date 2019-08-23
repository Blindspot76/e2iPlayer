# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG,GetDefaultLang
import logging
import random
import re
import ssl
import subprocess
import copy
import time
import os
from base64 import b64encode
from collections import OrderedDict
import urllib
from requests.sessions import Session
from requests.adapters import HTTPAdapter
from requests.compat import urlparse, urlunparse
from requests.exceptions import RequestException

from urllib3.util.ssl_ import create_urllib3_context, DEFAULT_CIPHERS

from .user_agents import USER_AGENTS

__version__ = "2.0.7"

#DEFAULT_USER_AGENT = random.choice(USER_AGENTS)
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'
DEFAULT_HEADERS = OrderedDict(
    (
        ("Host", None),
        ("Connection", "keep-alive"),
        ("Upgrade-Insecure-Requests", "1"),
        ("User-Agent", DEFAULT_USER_AGENT),
        (
            "Accept",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        ),
        ("Accept-Language", "en-US,en;q=0.9"),
        ("Accept-Encoding", "gzip, deflate"),
    )
)

BUG_REPORT = """\
Cloudflare may have changed their technique, or there may be a bug in the script.

Please read https://github.com/Anorov/cloudflare-scrape#updates, then file a \
bug report at https://github.com/Anorov/cloudflare-scrape/issues."\
"""

ANSWER_ACCEPT_ERROR = """\
The challenge answer was not properly accepted by Cloudflare. This can occur if \
the target website is under heavy load, or if Cloudflare is experiencing issues. You can
potentially resolve this by increasing the challenge answer delay (default: 8 seconds). \
For example: cfscrape.create_scraper(delay=15)

If increasing the delay does not help, please open a GitHub issue at \
https://github.com/Anorov/cloudflare-scrape/issues\
"""

# Remove a few problematic TLSv1.0 ciphers from the defaults
DEFAULT_CIPHERS += ":!ECDHE+SHA:!AES128-SHA"

def getFullUrl(url, mainUrl='http://fake/'):
	if not url: return ''
	if url.startswith('./'):
		url = url[1:]
	from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
	currUrl = mainUrl
	mainUrl = common.getBaseUrl(currUrl)

	if url.startswith('//'):
		proto = mainUrl.split('://', 1)[0]
		url = proto + ':' + url
	elif url.startswith('://'):
		proto = mainUrl.split('://', 1)[0]
		url = proto + url
	elif url.startswith('/'):
		url = mainUrl + url[1:]
	elif 0 < len(url) and '://' not in url:
		if currUrl == mainUrl:
			url =  mainUrl + url
		else:
			url = urljoin(currUrl, url)
	return url


class CloudflareAdapter(HTTPAdapter):
    """ HTTPS adapter that creates a SSL context with custom ciphers """

    def get_connection(self, *args, **kwargs):
        conn = super(CloudflareAdapter, self).get_connection(*args, **kwargs)

        if conn.conn_kw.get("ssl_context"):
            conn.conn_kw["ssl_context"].set_ciphers(DEFAULT_CIPHERS)
        else:
            context = create_urllib3_context(ciphers=DEFAULT_CIPHERS)
            conn.conn_kw["ssl_context"] = context

        return conn


class CloudflareError(RequestException):
    pass


class CloudflareCaptchaError(CloudflareError):
    pass


class CloudflareScraper(Session):
	def __init__(self, *args, **kwargs):
		
		
		
		
		
		
		
		
		self.delay = kwargs.pop("delay", None)
		# Use headers with a random User-Agent if no custom headers have been set
		headers = OrderedDict(kwargs.pop("headers", DEFAULT_HEADERS))

		# Set the User-Agent header if it was not provided
		headers.setdefault("User-Agent", DEFAULT_USER_AGENT)

		super(CloudflareScraper, self).__init__(*args, **kwargs)

		# Define headers to force using an OrderedDict and preserve header order
		self.headers = headers

		self.mount("https://", CloudflareAdapter())

	@staticmethod
	def is_cloudflare_iuam_challenge(resp):
		return (
			resp.status_code in (503, 429)
			and resp.headers.get("Server", "").startswith("cloudflare")
			and b"jschl_vc" in resp.content
			and b"jschl_answer" in resp.content
		)

	@staticmethod
	def is_cloudflare_captcha_challenge(resp):
		return (
			resp.status_code == 403
			and resp.headers.get("Server", "").startswith("cloudflare")
			and b"/cdn-cgi/l/chk_captcha" in resp.content
		)
        
	def request(self, method, url, *args, **kwargs):
		resp = super(CloudflareScraper, self).request(method, url, *args, **kwargs)

		# Check if Cloudflare captcha challenge is presented
		if self.is_cloudflare_captcha_challenge(resp):
			#self.handle_captcha_challenge(resp, url)*
			sitekey_data=re.findall('data-sitekey="([^"]+?)"', resp.content, re.S)
			if sitekey_data:
				sitekey = sitekey_data[0]
			else:
				sitekey = ''
				
			id_data=re.findall('data-ray="([^"]+?)"', resp.content, re.S)
			if id_data:
				id = id_data[0]
			else:
				id = ''				
				
			if sitekey != '':
				from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
				cm = common()
				sts, tmp = cm.ph.getDataBeetwenMarkers(resp.content, '<form', '</form>', caseSensitive=False)
				actionType = cm.ph.getSearchGroups(tmp, 'method="([^"]+?)"', 1, True)[0].lower()
				url5 = cm.ph.getSearchGroups(tmp, 'action="([^"]+?)"')[0]
				url5 = getFullUrl(url5, url)
				post_data2 = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))





				from Plugins.Extensions.IPTVPlayer.libs.recaptcha_v2 import UnCaptchaReCaptcha
				# google captcha
				recaptcha = UnCaptchaReCaptcha(lang=GetDefaultLang())
				recaptcha.HTTP_HEADER['Referer'] = url
				recaptcha.HTTP_HEADER['User-Agent'] = DEFAULT_USER_AGENT
				token = recaptcha.processCaptcha(sitekey)
				printDBG('tttttttttttttttttttttt'+str(token))
				if '' != token:
					post_data2['g-recaptcha-response'] = token

				USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36'
				MAIN_URL = 'https://www.planet-streaming.net'
				HTTP_HEADER = {'User-Agent': USER_AGENT, 'DNT':'1','Connection':'close','Cache-Control': 'no-cache','Pragma': 'no-cache', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language':'en-US,en;q=0.5', 'Referer':url}
				defaultParams = {'with_metadata':True,'no_redirection':False,'header':HTTP_HEADER}




				if actionType == 'get':
					if '?' in url5:
						url5 += '&'
					else:
						url5 += '?'
					url5 += urllib.urlencode(post_data2)
					post_data2 = None
							
				sts, data = cm.getPage(url5, defaultParams, post_data2)



				#if token != '': resp = super(CloudflareScraper, self).request(method, url5, *args, **kwargs)
				printDBG('rrrrrrrrrrrrrrrrrrrrrrrrrrrr'+data)
		# Check if Cloudflare anti-bot "I'm Under Attack Mode" is enabled
		elif self.is_cloudflare_iuam_challenge(resp):
			resp = self.solve_cf_challenge(resp, **kwargs)
 
		return resp

	def cloudflare_is_bypassed(self, url, resp=None):
		cookie_domain = ".{}".format(urlparse(url).netloc)
		return (
			self.cookies.get("cf_clearance", None, domain=cookie_domain) or
			(resp and resp.cookies.get("cf_clearance", None, domain=cookie_domain))
		)

	def handle_captcha_challenge(self, resp, url):
		error = (
			"Cloudflare captcha challenge presented for %s (cfscrape cannot solve captchas)"
			% urlparse(url).netloc
		)
		if ssl.OPENSSL_VERSION_NUMBER < 0x10101000:
			error += ". Your OpenSSL version is lower than 1.1.1. Please upgrade your OpenSSL library and recompile Python."

		raise CloudflareCaptchaError(error, response=resp)

	def solve_cf_challenge(self, resp, **original_kwargs):
		start_time = time.time()

		body = resp.text
		parsed_url = urlparse(resp.url)
		domain = parsed_url.netloc
		submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, domain)

		cloudflare_kwargs = copy.deepcopy(original_kwargs)

		headers = cloudflare_kwargs.setdefault("headers", {})
		headers["Referer"] = resp.url

		try:
			params = cloudflare_kwargs["params"] = OrderedDict(
				re.findall(r'name="(s|jschl_vc|pass)"(?: [^<>]*)? value="(.+?)"', body)
			)

			for k in ("jschl_vc", "pass"):
				if k not in params:
					raise ValueError("%s is missing from challenge form" % k)
		except Exception as e:
			# Something is wrong with the page.
			# This may indicate Cloudflare has changed their anti-bot
			# technique. If you see this and are running the latest version,
			# please open a GitHub issue so I can update the code accordingly.
			raise ValueError(
				"Unable to parse Cloudflare anti-bot IUAM page: %s %s"
				% (e.message, BUG_REPORT)
			)

		# Solve the Javascript challenge
		answer, delay = self.solve_challenge(body, domain)
		params["jschl_answer"] = answer

		# Requests transforms any request into a GET after a redirect,
		# so the redirect has to be handled manually here to allow for
		# performing other types of requests even as the first request.
		method = resp.request.method
		cloudflare_kwargs["allow_redirects"] = False

		# Cloudflare requires a delay before solving the challenge
		time.sleep(max(delay - (time.time() - start_time), 0))

		# Send the challenge response and handle the redirect manually
		redirect = self.request(method, submit_url, **cloudflare_kwargs)
		#printDBG(str(redirect))
		redirect_location = urlparse(redirect.headers["Location"])

		if not redirect_location.netloc:
			redirect_url = urlunparse(
				(
					parsed_url.scheme,
					domain,
					redirect_location.path,
					redirect_location.params,
					redirect_location.query,
					redirect_location.fragment,
				)
			)
			return self.request(method, redirect_url, **original_kwargs)
		return self.request(method, redirect.headers["Location"], **original_kwargs)


	def solve_challenge(self, body, domain):
		params={}
		verData= body
		form_index = verData.find('id="challenge-form"')
		sub_body = verData[form_index:]
		cf_delay = float(re.search('submit.*?(\d+)', verData, re.DOTALL).group(1)) / 1000.0	
		printDBG('CCCCCCCCCCCCCCloud cf_delay:'+str(cf_delay))
		
		if body.find('id="cf-dn-', form_index) != -1:
			extra_div_expression = re.search('id="cf-dn-.*?>(.+?)<', sub_body).group(1)	
		js_answer = self.cf_parse_expression( re.search('setTimeout\(function\(.*?:(.*?)}', verData, re.DOTALL).group(1))		
		printDBG('CCCCCCCCCCCCCCloud Init js_answer:'+str(js_answer))
		
		builder = re.search("challenge-form'\);\s*;(.*);a.value", verData, re.DOTALL).group(1)
		printDBG('CCCCCCCCCCCCCCloud builder:'+str(builder))
		lines = builder.replace(' return +(p)}();', '', 1).split(';')
		printDBG('CCCCCCCCCCCCCCloud lines:'+str(lines))
		
		for line in lines:
			if len(line) and '=' in line:
				heading, expression = line.split('=', 1)
				if 'eval(eval(' in expression:
					# Uses the expression in an external <div>.
					expression_value = self.cf_parse_expression(extra_div_expression)
				elif 'function(p' in expression:
					# Expression + domain sampling function.
					expression_value = self.cf_parse_expression(expression, domain)
				else:
					expression_value = self.cf_parse_expression(expression)
				#printDBG('CCCCCCCCCCCCCCloud expression_value:'+str(expression_value))	
				js_answer = self.cf_arithmetic_op(heading[-1], js_answer, expression_value)		
				#printDBG('CCCCCCCCCCCCCCloud js_answer:'+str(js_answer)) 
		
		if '+ t.length' in verData:
			js_answer += len(domain) # Only older variants add the domain length.
		printDBG('CCCCCCCCCCCCCCloud js_answer:'+str(js_answer))

		return js_answer, cf_delay


	def cf_parse_expression(self, expression, domain=None):
		def _get_jsfuck_number(section):
			digit_expressions = section.replace('!+[]', '1').replace('+!![]', '1').replace('+[]', '0').split('+')
			return int(
				# Form a number string, with each digit as the sum of the values inside each parenthesis block.
				''.join(
					str(sum(int(digit_char) for digit_char in digit_expression[1:-1])) # Strip the parenthesis.
					for digit_expression in digit_expressions
				)
			)

		if '/' in expression:
			dividend, divisor = expression.split('/')
			dividend = dividend[2:-1] # Strip the leading '+' char and the enclosing parenthesis.

			if domain:
				# 2019-04-02: At this moment, this extra domain sampling function always appears on the
				# divisor side, at the end.
				divisor_a, divisor_b = divisor.split('))+(')
				divisor_a = _get_jsfuck_number(divisor_a[5:]) # Left-strip the sequence of "(+(+(".
				divisor_b = self.cf_sample_domain_function(divisor_b, domain)
				return _get_jsfuck_number(dividend) / float(divisor_a + divisor_b)
			else:
				divisor = divisor[2:-1]
				return _get_jsfuck_number(dividend) / float(_get_jsfuck_number(divisor))
		else:
			return _get_jsfuck_number(expression[2:-1])



	def cf_arithmetic_op(self, op, a, b):
		if op == '+':
			return a + b
		elif op == '/':
			return a / float(b)
		elif op == '*':
			return a * float(b)
		elif op == '-':
			return a - b
		else:
			raise Exception('Unknown operation')


	def cf_sample_domain_function(self, func_expression, domain):
		parameter_start_index = func_expression.find('}(') + 2
		# Send the expression with the "+" char and enclosing parenthesis included, as they are
		# stripped inside ".cf_parse_expression()'.
		sample_index = self.cf_parse_expression(
			func_expression[parameter_start_index : func_expression.rfind(')))')]
		)
		return ord(domain[int(sample_index)])




	@classmethod
	def create_scraper(cls, sess=None, **kwargs):
		"""
		Convenience function for creating a ready-to-go CloudflareScraper object.
		"""
		scraper = cls(**kwargs)

		if sess:
			attrs = [
				"auth",
				"cert",
				"cookies",
				"headers",
				"hooks",
				"params",
				"proxies",
				"data",
			]
			for attr in attrs:
				val = getattr(sess, attr, None)
				if val:
					setattr(scraper, attr, val)

		return scraper

	# Functions for integrating cloudflare-scrape with other applications and scripts

	@classmethod
	def get_tokens(cls, url, user_agent=None, **kwargs):
		scraper = cls.create_scraper()
		if user_agent:
			scraper.headers["User-Agent"] = user_agent

		try:
			resp = scraper.get(url, **kwargs)
			resp.raise_for_status()
		except Exception:
			logging.error("'%s' returned an error. Could not collect tokens." % url)
			raise

		domain = urlparse(resp.url).netloc
		cookie_domain = None

		for d in scraper.cookies.list_domains():
			if d.startswith(".") and d in ("." + domain):
				cookie_domain = d
				break
		else:
			raise ValueError(
				'Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM ("I\'m Under Attack Mode") enabled?'
			)

		return (
			{
				"__cfduid": scraper.cookies.get("__cfduid", "", domain=cookie_domain),
				"cf_clearance": scraper.cookies.get(
					"cf_clearance", "", domain=cookie_domain
				),
			},
			scraper.headers["User-Agent"],
		)

	@classmethod
	def get_cookie_string(cls, url, user_agent=None, **kwargs):
		"""
		Convenience function for building a Cookie HTTP header value.
		"""
		tokens, user_agent = cls.get_tokens(url, user_agent=user_agent, **kwargs)
		return "; ".join("=".join(pair) for pair in tokens.items()), user_agent


create_scraper = CloudflareScraper.create_scraper
get_tokens = CloudflareScraper.get_tokens
get_cookie_string = CloudflareScraper.get_cookie_string
