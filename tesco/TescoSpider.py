# -*- coding: utf-8 -*-
import scrapy
import pycountry
import uuid
import json
from locations.categories import Code
from locations.items import GeojsonPointItem

class TescoSpider(scrapy.Spider):
   
    name = "tesco_cze_dpa"
    brand_name = "Tesco"
    spider_type = "chain"
    spider_chain_id = "44"
    spider_categories = [
        Code.GROCERY.value
    ]
    spider_countries = [
        pycountry.countries.lookup("CZE").alpha_3
    ]

    def start_requests(self):
        url = "https://itesco.cz/Ajax?type=fetch-stores-for-area&bounds[nw][lat]=51.91433728600013&bounds[nw][lng]=7.863363671875008&bounds[ne][lat]=51.91433728600013&bounds[ne][lng]=23.134359765625007&bounds[sw][lat]=41.2247979261739&bounds[sw][lng]=7.863363671875008&bounds[se][lat]=41.2247979261739&bounds[se][lng]=23.134359765625007&currentCoords[lat]=46.834510593737406&currentCoords[lng]=15.498861718750007&instanceUUID=b5c4aa5f-9819-47d9-9e5a-d631e931c007"
        yield scrapy.Request(
            url=url,
            method="GET",
            callback=self.parse,
        )

    def parse(self, response):
        data = response.json()
        
        for store in data.get('stores', []):
            opening_hours = self.parse_opening_hours(store.get('opening'))
            
            mappedAttributes = {
                'chain_name': self.brand_name,
                'chain_id': self.spider_chain_id,
                'ref': uuid.uuid4().hex,
                'addr_full': f"{store.get('address')}, {store.get('city_name')}, {store.get('zipcode')}",
                'city': store.get('city_name'),
                'state': None,  # No details 
                'postcode': store.get('zipcode'),
                'phone': store.get('phone'),
                'email': None,  # No details 
                'opening_hours': opening_hours,
                'website': "https://itesco.cz/prodejny/",
                'lat': store.get('gpslat'),
                'lon': store.get('gpslng'),
            }
            yield GeojsonPointItem(**mappedAttributes)

    def parse_opening_hours(self, opening_str):
        if not opening_str:
            return ""
        
        try:
            opening_dict = json.loads(opening_str)
            days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
            hours = []
            for i, day in enumerate(days):
                if str(i) in opening_dict:
                    start, end = opening_dict[str(i)]
                    hours.append(f"{day} {start}-{end}")
            return "; ".join(hours)
        except json.JSONDecodeError:
            return ""