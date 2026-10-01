import requests

proxy_url = "http://username-country-tw:password@residential.proxyscrape.com:8080"
proxies = {"http": proxy_url, "https": proxy_url}

response = requests.get("https://ipinfo.io/json", proxies=proxies)
print(response.json())