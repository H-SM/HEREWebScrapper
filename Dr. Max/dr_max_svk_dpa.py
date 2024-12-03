# -*- coding: utf-8 -*-

import scrapy
import pycountry
import uuid
from locations.categories import Code
from locations.items import GeojsonPointItem
import datetime

class DrMaxSpider(scrapy.Spider):
    
    name = "dr_max_svk_dpa"
    brand_name = "Dr. Max"
    spider_type = "chain"
    spider_chain_id = "8803"
    spider_categories = [
        Code.DRUGSTORE_OR_PHARMACY.value
    ]
    spider_countries = [
        pycountry.countries.lookup("SVK").alpha_3
    ]

    # start_urls = ["https://www.drmax.sk/lekarne"]

    def start_requests(self):
        url = "https://pharmacy.drmax.sk/api/v1/public/pharmacies" 

        yield scrapy.Request(
            url=url,
            method="GET",
            callback=self.parse,
        )

    def parse(self, response):
        json_response = response.json()

        for data in json_response.get("data", []):
            location = data.get("location", {})
            opening_hours = data.get("openingHours", [])

            mappedAttributes = {
                'chain_name': self.brand_name,
                'chain_id': self.spider_chain_id,
                'ref': uuid.uuid4().hex,
                'city': location.get('city', ''),
                'street': location.get('street', ''),
                'postcode': location.get('zipCode', ''),
                'phone': data.get("phoneNumbers", [{}])[0].get("number", ""),
                'email': data.get("additionalParams", {}).get("email", ""),
                'opening_hours': self.format_opening_hours(opening_hours),
                'website': "https://www.drmax.sk/lekarne",
                'lat': location.get('latitude', ''),
                'lon': location.get('longitude', ''),
            }

            yield GeojsonPointItem(**mappedAttributes)

    def format_opening_hours(self, opening_hours):
        formatted_hours = []
        day_abbr = {
            'Monday': 'Mo', 'Tuesday': 'Tu', 'Wednesday': 'We',
            'Thursday': 'Th', 'Friday': 'Fr', 'Saturday': 'Sa', 'Sunday': 'Su'
        }
        for day in opening_hours:
            if day['open']:
                try:
                    date_string = day['date']
                    day_date = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
                    day_name = day_date.strftime("%A")

                    opening_hour = day['openingHour'][0]

                    if opening_hour['open']:
                        from_time = datetime.datetime.strptime(opening_hour['from'], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M")
                        to_time = datetime.datetime.strptime(opening_hour['to'], "%Y-%m-%dT%H:%M:%SZ").strftime("%H:%M")
                        formatted_hours.append(f"{day_abbr[day_name]} {from_time} - {to_time}")
                except (ValueError, IndexError):
                    pass
        return "; ".join(formatted_hours)
