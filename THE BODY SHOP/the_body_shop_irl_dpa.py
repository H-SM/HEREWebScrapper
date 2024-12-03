import scrapy
import pycountry
import uuid
from locations.categories import Code
from locations.items import GeojsonPointItem

class BodyshopspiderSpider(scrapy.Spider):
    name = "the_body_shop_เดอะบอดี้ช็อป_irl_dpa"
    # name = "the_body_shop_irl_dpa"
    brand_name = "THE BODY SHOP เดอะบอดี้ช็อป"
    spider_chain_id = "8201"
    spider_categories = [
        Code.SPECIALTY_STORE.value
    ]
    spider_countries = [
        pycountry.countries.lookup("IRL").alpha_3
    ]

    def start_requests(self):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        url = "https://api.thebodyshop.com/rest/v2/thebodyshop-uk/stores?fields=FULL&latitude=&longitude=&query=&pageSize=&lang=en_GB&curr=GBP"

        yield scrapy.Request(
            url=url,
            headers=headers,
            method='GET',
            callback=self.parse,
            meta={'current_page': 0}
        )

    def parse(self, response):
        data = response.json()
        stores = data.get('stores', [])
        for store in stores:
            address = store.get('address', {})
            formatted_address = address.get('formattedAddress')
            geopoint = store.get('geoPoint', {})
            latitude = geopoint.get('latitude')
            longitude = geopoint.get('longitude')
            opening_hours = store.get('openingHours', {})
            week_day_opening_list = opening_hours.get('weekDayOpeningList', [])
            opening_hours_list = []
            for day in week_day_opening_list:
                opening_time = day.get('openingTime', {}).get('formattedHour', '')
                closing_time = day.get('closingTime', {}).get('formattedHour', '')
                day_name = day.get('weekDay', '')
                opening_hours_list.append(f"{day_name}: {opening_time} - {closing_time}")

            # Parse city, state, and postcode from formatted_address
            address_parts = formatted_address.split(',')
            # "14 Lion Walk, COLCHESTER, Essex, CO1 1LX, United Kingdom"
            postcode = address_parts[-2].strip() if len(address_parts) >= 2 else None
            state = address_parts[-3].strip() if len(address_parts) >= 3 else None
            city = address_parts[-4].strip() if len(address_parts) >= 4 else None

            mapped_attributes = {
                'chain_name': self.brand_name,
                'chain_id': self.spider_chain_id,
                'ref': uuid.uuid4().hex,
                'addr_full': formatted_address,
                'city': city,
                'state': state,
                'postcode': postcode,
                'phone': address.get('phone', ''),
                'email': None, # no email in the data
                'opening_hours': opening_hours_list,
                'website': "https://www.thebodyshop.com/en-gb/store-finder",
                'lat': float(latitude),
                'lon': float(longitude),
            }
            yield GeojsonPointItem(**mapped_attributes)

        # Overlooked each page of data
        pagination = data.get('pagination', {})
        current_page = pagination.get('currentPage', 0)
        total_pages = pagination.get('totalPages', 1)
        if current_page + 1 < total_pages:
            next_page = current_page + 1
            next_url = f"https://api.thebodyshop.com/rest/v2/thebodyshop-uk/stores?fields=FULL&latitude=&longitude=&query=&pageSize=&lang=en_GB&curr=GBP&currentPage={next_page}"
            yield scrapy.Request(
                url=next_url,
                headers=response.request.headers,
                callback=self.parse,
                meta={'current_page': next_page}
            )