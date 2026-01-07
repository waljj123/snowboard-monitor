# src/scraper.py
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
import logging

class GitHubSnowboardScraper:
    def __init__(self):
        self.base_url = "https://snowboards.com"
        self.data_dir = "data"
        self.images_dir = os.path.join(self.data_dir, "images")
        
        # 创建目录
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def scrape_all_products(self):
        """爬取所有雪板产品"""
        self.logger.info("开始爬取雪板数据...")
        
        all_products = []
        page = 1
        
        while True:
            self.logger.info(f"正在爬取第 {page} 页...")
            
            if page == 1:
                url = f"{self.base_url}/products/2672/equipment-snowboards?view=all"
            else:
                url = f"{self.base_url}/products/2672/equipment-snowboards?page={page}&view=all"
            
            try:
                response = requests.get(url, timeout=30)
                if response.status_code != 200:
                    break
                    
                products = self.parse_products_page(response.text)
                if not products:
                    break
                    
                all_products.extend(products)
                self.logger.info(f"第 {page} 页获取到 {len(products)} 个产品")
                page += 1
                
            except Exception as e:
                self.logger.error(f"爬取第 {page} 页时出错: {e}")
                break
        
        return all_products
    
    def parse_products_page(self, html):
        """解析产品页面"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # 基于您提供的HTML结构解析产品
        product_items = soup.find_all('div', class_=lambda x: x and 'product' in x.lower() if x else False)
        
        for item in product_items:
            try:
                product_data = self.extract_product_info(item)
                if product_data:
                    products.append(product_data)
            except Exception as e:
                self.logger.warning(f"解析产品失败: {e}")
                continue
                
        return products
    
    def extract_product_info(self, product_element):
        """提取单个产品信息"""
        # 产品名称
        name_elem = product_element.find(['h1', 'h2', 'h3', 'h4'])
        name = name_elem.get_text(strip=True) if name_elem else "未知产品"
        
        # 品牌检测
        brand = self.detect_brand(name)
        
        # 价格信息
        price_data = self.extract_prices(product_element.get_text())
        
        # 图片URL
        img_elem = product_element.find('img')
        image_url = img_elem.get('src') if img_elem else ""
        
        return {
            'id': self.generate_id(brand, name),
            'brand': brand,
            'name': name,
            'current_price': price_data.get('current'),
            'original_price': price_data.get('original'),
            'discount': price_data.get('discount'),
            'image_url': image_url,
            'product_url': self.extract_product_url(product_element),
            'category': self.detect_category(name),
            'scraped_at': datetime.now().isoformat()
        }
    
    def detect_brand(self, product_name):
        """检测品牌"""
        brands = ['Burton', 'Lib Tech', 'Salomon', 'K2', 'Capita', 'Ride', 'Rome', 
                 'Never Summer', 'Gnu', 'Arbor', 'Bataleon', 'YES', 'Rossignol', 'Roxy']
        
        for brand in brands:
            if brand.lower() in product_name.lower():
                return brand
        return "其他品牌"
    
    def extract_prices(self, text):
        """提取价格信息"""
        prices = re.findall(r'\$([\d,]+\.?\d*)', text)
        price_values = [float(p.replace(',', '')) for p in prices if p.replace(',', '').replace('.', '').isdigit()]
        
        if len(price_values) >= 2:
            return {
                'current': min(price_values),
                'original': max(price_values),
                'discount': f"{int((max(price_values) - min(price_values)) / max(price_values) * 100)}%"
            }
        elif price_values:
            return {'current': price_values[0], 'original': None, 'discount': None}
        else:
            return {'current': None, 'original': None, 'discount': None}
    
    def generate_id(self, brand, name):
        """生成产品ID"""
        import hashlib
        unique_str = f"{brand}_{name}".encode('utf-8')
        return hashlib.md5(unique_str).hexdigest()[:8]
    
    def save_data(self, products):
        """保存数据"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'product_count': len(products),
            'products': products
        }
        
        with open(os.path.join(self.data_dir, 'snowboards.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"数据已保存，共 {len(products)} 个产品")

def main():
    scraper = GitHubSnowboardScraper()
    products = scraper.scrape_all_products()
    scraper.save_data(products)

if __name__ == "__main__":
    main()