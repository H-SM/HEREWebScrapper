
# -*- coding: utf-8 -*-

import scrapy
import pycountry
import uuid
from locations.categories import Code
from locations.items import GeojsonPointItem
from typing import List, Dict
import json

class SlovnaftSpider(scrapy.Spider):
    name = "slovnaft_svk_dpa"
    brand_name = "Slovnaft"
    spider_type = "chain"
    spider_chain_id = "958"
    spider_categories = [Code.PETROL_GASOLINE_STATION.value]
    spider_countries = [pycountry.countries.lookup("SVK").alpha_3]
    base_url = "https://cerpaciestanice.slovnaft.sk/en/portlet/routing/"

    def start_requests(self):
        body = {
            "country": "Slovakia",
            "lat": '48.1462386',
            "lng": '17.1072618',
            "radius": "9999",
        }
        yield scrapy.FormRequest(
            url=self.base_url + "along_latlng.json",
            formdata=body,
            callback=self.parse,
        )

    def parse(self, response):
        store_list = json.loads(response.text)

        for store in store_list:
            store_id = store["id"]
            body = {"id": store_id}
            yield scrapy.FormRequest(
                url=self.base_url + "station_info.json",
                formdata=body,
                callback=self.parse_store_details,
                meta={"store_data": store},
            )

    def parse_store_details(self, response):
        store_data = response.meta["store_data"]
        store_details = json.loads(response.text)

        opening_hours = self.parse_opening_hours(store_details["fs"])
        phone = store_details["fs"]["fs_phone_num"] or store_details["fs"]["fs_mobile_num"] or None
        addr_full = f"{store_details['fs']['address']}, {store_details['fs']['postcode']}, {store_details['fs']['city']}"

        mappedAttributes = {
            "ref": uuid.uuid4().hex,
            "chain_name": self.brand_name,
            "chain_id": self.spider_chain_id,
            "addr_full": addr_full,
            "city": store_details["fs"]["city"],
            "state": None,
            "postcode": store_details["fs"]["postcode"],
            "phone": phone,
            "email": None,
            "opening_hours": opening_hours,
            "website": "https://cerpaciestanice.slovnaft.sk/en",
            "lat": store_data["lat"],
            "lon": store_data["lng"],
        }

        yield GeojsonPointItem(**mappedAttributes)

    def parse_opening_hours(self, store_details: Dict) -> List[str]:
        opening_hours = []

        winter_hours = [
            {
                "day": "Monday",
                "hours": store_details["opn_hrs_wtr_wd"],
            },
            {
                "day": "Tuesday",
                "hours": store_details["opn_hrs_wtr_wd"],
            },
            {
                "day": "Wednesday",
                "hours": store_details["opn_hrs_wtr_wd"],
            },
            {
                "day": "Thursday",
                "hours": store_details["opn_hrs_wtr_wd"],
            },
            {
                "day": "Friday",
                "hours": store_details["opn_hrs_wtr_wd"],
            },
            {
                "day": "Saturday",
                "hours": store_details["opn_hrs_wtr_sat"],
            },
            {
                "day": "Sunday",
                "hours": store_details["opn_hrs_wtr_sun"],
            },
        ]

        summer_hours = [
            {
                "day": "Monday",
                "hours": store_details["opn_hrs_smr_wd"],
            },
            {
                "day": "Tuesday",
                "hours": store_details["opn_hrs_smr_wd"],
            },
            {
                "day": "Wednesday",
                "hours": store_details["opn_hrs_smr_wd"],
            },
            {
                "day": "Thursday",
                "hours": store_details["opn_hrs_smr_wd"],
            },
            {
                "day": "Friday",
                "hours": store_details["opn_hrs_smr_wd"],
            },
            {
                "day": "Saturday",
                "hours": store_details["opn_hrs_smr_sat"],
            },
            {
                "day": "Sunday",
                "hours": store_details["opn_hrs_smr_sun"],
            },
        ]

        for hours in winter_hours:
            opening_hours.append(f"{hours['day']} Winter: {hours['hours']}")

        for hours in summer_hours:
            opening_hours.append(f"{hours['day']} Summer: {hours['hours']}")

        return opening_hours