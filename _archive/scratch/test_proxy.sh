#!/usr/bin/env bash
export USERNAME=5y1kzxasyth0lgu-country-tw
export PASSWORD=gaq4kdfa60jfl4d
export PROXYSCRAPE_HOSTNAME=rp.scrapegw.com:6060
curl -x http://$USERNAME:$PASSWORD@$PROXYSCRAPE_HOSTNAME http://ip-api.com/json && echo