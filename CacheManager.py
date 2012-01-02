# -*- coding: utf-8 -*-

"""
CacheManager class
"""

import datetime
import os.path
import re
import time
import urllib
import sqlite
import sys

ver = sys.version_info
if ver[1] == 4:
	import md5
else:
	import hashlib

class CacheManager:
	def __init__(self, dbpath):
		"""コンストラクタ。プロパティをセットする。
		@param string dbpath 作成／読み込むSQLiteのDBファイルのパス
		"""
		flag = os.path.exists(dbpath)
		self.con = sqlite.connect(dbpath)
		self.cur = self.con.cursor()
		if not flag:
			self.createDB()
	def __del__(self):
		"""デストラクタ。データベース接続を解除する。"""
		self.cur.close()
		self.con.close()
	def createDB(self):
		"""キャッシュを保存するデータベースを作成する。"""
		str = "1234567890abcdef"
		for s1 in str:
			for s2 in str:
				for s3 in str:
					prefix = s1 + s2 + s3
					sql = u"CREATE TABLE cache%s(ID INT NOT NULL PRIMARY KEY, URL TEXT NOT NULL, DATE TEXT NOT NULL, HTML TEXT);" % prefix
					self.cur.execute(sql)
		self.con.commit()
	def getPrefix(self, url):
		"""get prefix for managing cachelist efficiently
		@param string url prefixの生成源となるURL
		@return string prefix
		"""
		if ver[1] == 4:
			m = md5.new(url).hexdigest()
		else:
			m = hashlib.md5(url).hexdigest()
		return m[0:3]
	def getCache(self, url):
		"""指定したURLのキャッシュを取得する。
		@param string url キャッシュを取得したいWebページのURL
		@return string キャッシュ
		"""
		prefix = self.getPrefix(url)
		self.cur.execute("SELECT HTML FROM %s WHERE URL = %s;", "cache" + prefix, url)
		cache = False
		for row in self.cur:
			cache = row[0]
		return cache
	def insertCache(self, url, cache):
		"""指定したURLのキャッシュを新規挿入する。
		@param string url キャッシュ元WebページのURL
		@param string cache HTMLソース
		"""
		prefix = self.getPrefix(url)
		id = self.getRecordNum(prefix)
		date = str(datetime.datetime.now())
		date = date[0:19]
		self.cur.execute("INSERT INTO %s(ID, URL, DATE, HTML) values (%s, %s, %s, %s);", "cache" + prefix, id, url, date, self.sanitize(cache))
		self.con.commit()
	def updateCache(self, url, cache):
		"""登録済みのURLのキャッシュを上書きする。
		@param string url キャッシュ元WebページのURL
		@param string cache HTMLソース
		"""
		prefix = self.getPrefix(url)
		self.cur.execute("SELECT ID FROM %s WHERE URL = %s;", "cache" + prefix, url)
		id = False
		for row in self.cur:
			id = int(row[0])
		self.cur.execute("UPDATE %s SET HTML = %s WHERE ID = %s;", "cache" + prefix, self.sanitize(cache), id)
		self.con.commit()
	def getRecordNum(self, prefix):
		"""指定したprefixのテーブルに登録されているテーブル数を取得する。
		@param string prefix テーブルのprefix
		@return int テーブル数
		"""
		self.cur.execute("SELECT COUNT(*) FROM %s", "cache" + prefix)
		num = 0
		for row in self.cur:
			num = int(row[0])
		return num
	def rwCache(self, url, sec=2, enforce=False):
		"""指定したURLのキャッシュを取得する。もしキャッシュがなければWebからキャッシュを生成する。
		@param string url キャッシュを取得したいWebページのURL
		@param int sec キャッシュを生成した直後にsleepさせる秒数
		@param bool enforce Trueならキャッシュが既に作成済みでも、Webからキャッシュを取得し直して上書きする
		@return string キャッシュのHTMLソース
		"""
		cache = self.getCache(url)
		if not cache:
			cache = self.wget(url)
			if not cache:
				return False
			else:
				self.insertCache(url, cache)
				time.sleep(sec)
		elif enforce:
			cache = self.wget(url)
			if cache:
				self.updateCache(url, cache)
				time.sleep(sec)
		return cache
	def wget(self, url):
		"""指定したURLにアクセスして、HTMLソースを取得する。
		@param string url URL
		@return string HTMLソース
		"""
		try:
			io = urllib.urlopen(url)
			html = io.read()
			io.close()
		except IOError:
			html = False
		return html
	def sanitize(self, str):
		"""文字列中のヌルバイトを標準的な半角スペースに置換する。
		@param string str サニタイズしたい文字列
		@return string サニタイズした結果
		"""
		return re.sub(chr(0), " ", str)
