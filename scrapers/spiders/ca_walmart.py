import scrapy

from scrapers.items import ProductItem
from urllib.parse import urlencode
from urllib.parse import urljoin
import json
import re
import ast
import json

API_KEY = '' #use scrapperapi to generate key
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.walmart.ca',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

#to request walmart api for Store, stock and price
def get_url_with_headers(url):
    payload = {'api_key': API_KEY, 'url': url, 'keep_headers': 'true'}
    proxy_url = 'http://api.scraperapi.com/?'+urlencode(payload)
    print(proxy_url)
    return proxy_url

#to render main page
def get_url_rendered(url):
    payload = {'api_key': API_KEY, 'url': url, 'render': 'true'}
    proxy_url = 'http://api.scraperapi.com/?'+urlencode(payload)
    return proxy_url

#to render product page
def get_url(url):
    payload = {'api_key': API_KEY, 'url': url}
    proxy_url = 'http://api.scraperapi.com/?'+urlencode(payload)
    return proxy_url

class CaWalmartSpider(scrapy.Spider):
    name = "ca_walmart"
    custom_settings = {'CONCURRENT_REQUESTS': 5,  # free plan limit
                       'RETRY_TIMES': 10}
    # allowed_domains = ["walmart.ca"]
    # start_urls = ["https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852"]

    def start_requests(self):
        urls = ['https://www.walmart.ca/en/grocery/fruits-vegetables/fruits/N-3852'] #can add more urls
        for url in urls:
            yield scrapy.Request(get_url_rendered(url), callback=self.parse)

    def parse(self, response):
        top_link = "https://www.walmart.ca"
        #get product links and parse each product
        for product_link in response.xpath("//div/a[@class='product-link']/@href").extract():
            product_link_full = urljoin(top_link, product_link)
            product_sku = product_link.split('/')[-1]
            yield scrapy.Request(get_url(product_link_full), callback=self.parse_product, meta={'product_link_full': product_link_full, 'product_sku':product_sku})

        #goto next page and repeat parsing for the new page
        next_page = response.xpath("//div/a[@class='page-select-list-btn']/@href").extract_first()
        if next_page is not None:
            next_page_link = urljoin(top_link, next_page)
            yield scrapy.Request(get_url_rendered(next_page_link), callback=self.parse)

    def parse_product(self, response):
        store = 'Walmart'
        sku =  response.meta['product_sku']
        barcodes = re.search('"upc":(.+?),"endecaDimensions"', response.text)
        if barcodes:
            barcodes_api = ast.literal_eval(barcodes.group(1)) #to be sent to walmart api
            barcodes = ','.join(ast.literal_eval(barcodes.group(1)))
        else:
            barcodes = 'n/a'
        brand = re.search('"Brand","value":(.+?)},{"id"', response.text)
        if brand:
            brand = str(brand.group(1))
        else:
            brand = 'n/a'
        name = response.xpath("//h1/text()").extract_first()
        description=re.search('"longDescription":"(.+?).",', response.text)
        if description:
            description = str((description).group(1))
        else:
            description = 'n/a'
        package = response.xpath("//p[@data-automation='short-description']/text()").extract_first()
        #image_url = re.search('"image":["(.+?)],"description"', response.text)
        image_url =str(','.join(response.xpath("//div[@role='presentation']/img/@src").extract()))
        category = str('›'.join(response.xpath("//*[@data-automation='desktop-breadcrumbs']/li//text()").extract()))
        url = response.meta['product_link_full']
        print('URL', url)

        product = ProductItem()
        product['store'] = store
        product['barcodes'] = barcodes
        product['sku'] = sku
        product['brand']= brand
        product['name'] = name
        product['description'] = description
        product['package'] = str(package)
        product['image_url'] = image_url
        product['category'] = str(category)
        product['url'] = str(url)

        #The following api was being used to fetch stock and price data
        #With latitude, longitude and barcode as input parameters
        # "id": 3124,
        store_api_3124 = f'https://www.walmart.ca/api/product-page/find-in-store?latitude=43.656845&longitude=-79.435406&lang=en&upc={barcodes_api[0]}'
        yield scrapy.Request(get_url_with_headers(store_api_3124), callback=self.store_data, meta={'product': product}, headers=headers)

        # "id": 3106,
        store_api_3106 = f'https://www.walmart.ca/api/product-page/find-in-store?latitude=48.4120872&longitude=-89.2413988&lang=en&upc={barcodes_api[0]}'
        yield scrapy.Request(get_url_with_headers(store_api_3106), callback=self.store_data, meta={'product': product}, headers=headers)

        # yield product

    def store_data(self, response):
        #Storing products with quantiy greater than 0
        product =  response.meta['product']
        response_json = json.loads(response.text)
        # print(response_json)
        for info in response_json['info']:
            if info['id'] == 3124 or info['id'] == 3106:
                branch = info['id']
                price = info['sellPrice']
                stock = info['availableToSellQty']
                if stock > 0:
                    product['branch'] = branch
                    product['price'] = price
                    product['stock'] = stock
                    yield product
