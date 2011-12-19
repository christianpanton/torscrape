#!/usr/bin/env python
#-*- coding:utf-8 -*-

import torscrape

urls = ["http://icanhazip.com/", "http://queryip.net/ip/"] * 10

def my_handler(url, data):
    print "-"*10
    print url
    print data
    print "-"*10

torscrape.process(urls, my_handler, refresh_ip=2, verbose=True)
