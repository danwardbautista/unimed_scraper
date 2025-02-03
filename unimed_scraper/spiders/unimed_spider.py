import scrapy
import json
import os
from datetime import datetime


class ProductSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["unimed.cn"]
    start_urls = ["https://www.unimed.cn/collections/all"]

    all_products = []

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 3,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "AUTOTHROTTLE_DEBUG": False,
    }

    def parse(self, response):
        product_items = response.css("div.ProductItem")
        for product in product_items:
            title = product.css("h2.ProductItem__Title a::text").get().strip()
            part_number = product.css("p.meta.sku::text").get()
            part_number = part_number.strip() if part_number else ""
            category = product.css("p.meta:not(.sku)::text").get()
            category = category.strip() if category else ""
            product_link = product.css("a.ProductItem__ImageWrapper::attr(href)").get()
            product_link = (
                response.urljoin(product_link.strip()) if product_link else ""
            )
            main_image_url = product.css(
                "img.ProductItem__Image:not(.ProductItem__Image--alternate)::attr(src)"
            ).get()
            main_image_url = (
                response.urljoin(main_image_url.strip()) if main_image_url else ""
            )
            hover_image_url = product.css(
                "img.ProductItem__Image--alternate::attr(src)"
            ).get()
            hover_image_url = (
                response.urljoin(hover_image_url.strip()) if hover_image_url else ""
            )
            if title:
                product_id = product_link.rstrip("/").split("/")[
                    -1
                ]  # Extract last part of URL

                self.all_products.append(
                    {
                        # "title": title,
                        # "category": category,
                        # "part_number": part_number,
                        "product_link": product_link,
                        "id": product_id,
                        # "main_image_url": main_image_url,
                        # "hover_image_url": hover_image_url,
                    }
                )
        self.log(f"Collected {len(product_items)} products from {response.url}.")
        next_page = response.css('link[rel="next"]::attr(href)').get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            if "page=" in next_page_url:
                page_number = int(next_page_url.split("page=")[-1])
                if page_number <= 44:
                    yield scrapy.Request(next_page_url, callback=self.parse)

    def close(self, reason):
        if not os.path.exists("results"):
            os.makedirs("results")

        today = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join("results", f"product_data_{today}.json")

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.all_products, f, ensure_ascii=False, indent=4)
            self.log(
                f"Successfully saved {len(self.all_products)} products to {filename}."
            )
        except Exception as e:
            self.log(f"Failed to save data to JSON file: {e}")
