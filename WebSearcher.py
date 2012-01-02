# -*- coding: utf-8 -*-

from CacheManager import CacheManager
from elementtree.ElementTree import *
import re
import sys
import urllib

class WebSearcher:
	def __init__(self):
		self.cm = False
		self.sleeptime = 2  #キャッシュ生成後にsleepする秒数
		self.swWrited = False #検索結果のキャッシュを強制的に上書きするか(swWritedがTrueの場合に有効)
		self.__params = {}

	def activeCache(self, cachedir):
		"""キャッシュ保存先の設定とキャッシュ保存関数の有効化"""
		self.cm = CacheManager(cachedir)
	def getHitCount(self):
		"""get the number of retrieved pages
		@return int the number of retrieved pages
		"""
		hits = False
		if self.__engine == "tsubaki":
			url = "http://tsubaki.ixnlp.nii.ac.jp/api.cgi?query=%s&only_hitcount=1" % self.__query
			force_dpnd = self.getParameter("force_dpnd")
			if force_dpnd:
				url += "&force_dpnd=" + str(force_dpnd)
			print url
			if self.is_available_caching():
				res = self.runCacheFunc(url)
			else:
				res = urllib.urlopen(url).read()
			if not re.match("^[0-9]+$", res):
				return "error"
			hits = res.rstrip()
		elif self.__engine == "yahoo" or self.__engine == "yahoo2":
			if self.is_available_caching():
				xmlstr = self.runCacheFunc(self.getResultURI(1, 1))
				print xmlstr
				doc = ElementTree(fromstring(xmlstr))
			else:
				url = self.getResultURI(1, 1)
				fd = file(url, "rb")
				doc = ElementTree(file=fd)
			e = doc.getroot()
			hits = e.attrib["totalResultsAvailable"]
		return hits
	def getResultURI(self, start, num):
		engine = self.getEngine()
		if engine == "tsubaki":
			url = "http://tsubaki.ixnlp.nii.ac.jp/api.cgi?query=" + self.getQuery() + "&start=" + str(start) + "&results=" + str(num) + "&Snippet=1"
		elif engine == "yahoo":
			appid = self.getParameter("appid")
			if not appid:
				sys.exit("You must assign appid!!")
			type = self.getParameter("type")
			if not type:
				type = "all"
			url = "http://search.yahooapis.jp/WebSearchService/V1/webSearch?query=%s&appid=%s&type=%s&start=%s&results=%s&format=any" % (self.__query, appid, type, start, num)
			print url
		elif engine == "yahoo2":
			appid = self.getParameter("appid")
			if not appid:
				sys.exit("You must assign appid!!")
			type = self.getParameter("type")
			if not type:
				type = "all"
			url = "http://search.yahooapis.jp/WebSearchService/V2/webSearch?query=%s&appid=%s&type=%s&start=%s&results=%s&format=html" % (self.__query, appid, type, start, num)
		else:
			url = False
		return url

	#"?query=" + urlencode(fnkf("-w", $this->query)) \
	
	def is_available(self, engine):
		"""check which defined search engine is available"""
		available_engines = ["okwave", "tsubaki", "yahoo", "yahooQA"]
		return engine in available_engines
	
	def is_available_caching(self):
		return self.cm != False
	
	def runCacheFunc(self, url):
		return self.cm.rwCache(url, self.sleeptime, self.swWrited)
	def search(self, start, max):
		"""run searching Web"""
		engine = self.getEngine()
		
		result = {}
		rank = 1
		if engine == "tsubaki":
			url = self.getResultURI(start, max)
			if self.is_available_caching():
				xmlstr = self.runCacheFunc(url)
				doc = ElementTree(fromstring(xmlstr))
			else:
				fd = file(url, "rb")
				doc = ElementTree(file=fd)
			for e in doc.findall("//Result"):
				tmp = {"title":e.find("Title").text, "url":e.find("Url").text, "snippet":e.find("Snippet").text, "cache":"http://tsubaki.ixnlp.nii.ac.jp/api.cgi?id=" + e.attrib["Id"] + "&format=html"}
				result[rank] = tmp
				rank += 1

		return result
		
		
	def getEngine(self):
		return self.__engine
	def setEngine(self, engine):
		self.__engine = engine
	def getParameter(self, name):
		if self.__params.has_key(name):
			return self.__params[name]
		else:
			return False
	def setParameter(self, name, value):
		self.__params[name] = value
	def getQuery(self):
		return self.__query
	def setQuery(self, query):
		self.__query = query
		
	## プロパティ ##
	engine = property(getEngine, setEngine)
	query = property(getQuery, setQuery)

