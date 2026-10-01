#!/usr/bin/env python3
import requests
username = "5y1kzxasyth0lgu-country-tw"
password = "gaq4kdfa60jfl4d"
proxy = "rp.scrapegw.com:6060"
proxy_auth = "{}:{}@{}".format(username, password, proxy)
proxies = {
    "http":"http://{}".format(proxy_auth)
}
urlToGet = "http://ip-api.com/json"
r = requests.get(urlToGet , proxies=proxies)
print("Response:\n{}".format(r.text))