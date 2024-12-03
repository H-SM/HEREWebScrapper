# -*- coding: utf-8 -*-

import scrapy
import pycountry
import uuid
from locations.categories import Code
from locations.items import GeojsonPointItem


class NacionalInnSpider(scrapy.Spider):
    
    name = "nacional_inn_bra_dpa"
    brand_name = "Nacional Inn"
    spider_type = "chain"
    spider_chain_id = "33455"
    spider_categories = [
        Code.HOTEL.value
    ]
    spider_countries = [
        pycountry.countries.lookup("BRA").alpha_3
    ]

    # start_urls = ["https://www.nacionalinn.com.br/"]

    def start_requests(self):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        url = "https://api.letsbook.com.br/landing/NACINN/hoteisLanding/1/pt-br"

        yield scrapy.Request(
            url=url,
            headers=headers,
            method="GET",
            callback=self.parse,
        )

    def parse(self, response):
        list_of_places = response.json()
        
        for place in list_of_places:
            opening_hours = self.parse_opening_hours(place['Amenidades'])
            mappedAttributes = {
                'chain_name': self.brand_name,
                'chain_id': self.spider_chain_id,
                'ref': uuid.uuid4().hex,
                'city': place['Destino']['Cidade'],
                'state': place['Destino']['Estado'],
                'postcode': place['CEP'],
                'phone': place.get('Telefone') or place.get('Celular') or "",
                'email': place['Email'],
                'street': f"{place['Endereco']}, {place['Bairro']}",
                'opening_hours': opening_hours,
                'website': "https://www.nacionalinn.com.br/",
                'lat': place['Latitude'],
                'lon': place['Longitude'],
            }
            yield GeojsonPointItem(**mappedAttributes)

    def parse_opening_hours(self, amenities):
        if any(amenity['Nome'] == "Recepção 24 horas" for amenity in amenities):
            return "Mo-Su 00:00-23:59"
        return None