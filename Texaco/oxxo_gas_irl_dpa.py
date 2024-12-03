# -*- coding: utf-8 -*-
import scrapy
import pycountry
import uuid
from locations.categories import Code
from locations.items import GeojsonPointItem
import json

class OXXOGASSpider(scrapy.Spider):
       
    name = "oxxo_gas_irl_dpa"
    brand_name = "OXXO GAS"
    spider_type = "chain"
    spider_chain_id = "30670"
    spider_categories = [
        Code.PETROL_GASOLINE_STATION.value
    ]
    spider_countries = [
        pycountry.countries.lookup("IRL").alpha_3
    ]

    # start_urls = ["https://texaco.ie/station-locator"]

    def start_requests(self):
        payload = {
            "NEBound_Lat": "59.34269882647968",
            "NEBound_Long": "9.345090428682932",
            "SWBound_Lat": "43.050403625725544",
            "SWBound_Long": "-29.019167383817067",
            "center_Lat": "51.19655122610261",
            "center_Long": "-9.837038477567067"
        }
        yield scrapy.FormRequest(
            url="https://locations.valero.com/en-us/Home/SearchForLocations",
            method="POST",
            formdata=payload,
            callback=self.parse,
        )

    def parse(self, response):
        data = json.loads(response.text)
        for place in data:
            if place.get('Country') == 'IE':

                mappedAttributes = {
                    'chain_name': self.brand_name,
                    'chain_id': self.spider_chain_id,
                    'ref': uuid.uuid4().hex,
                    'addr_full': ' '.join(place['DisplayAddressLines']),
                    'city': place['City'],
                    'state': place['State'],
                    'postcode': place['PostalCode'],
                    'phone': place['Phone'],
                    'website': "https://texaco.ie/station-locator",
                    'lat': place['Latitude'],
                    'lon': place['Longitude'],
                }
                yield GeojsonPointItem(**mappedAttributes)