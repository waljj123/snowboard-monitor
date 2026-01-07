import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import random
import re
import os
import sys
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SnowboardsScraper:
    def __init__(self, base_url='https://snowboards.com'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        Path('data').mkdir(exist_ok=True)
        Path('web/images').mkdir(exist_ok=True, parents=True)
        Path('logs').mkdir(exist_ok=True)
        
        self.product_count = 0
        
        self.brands = [
            'Burton', 'Lib Tech', 'Salomon', 'K2', 'Capita', 'Ride', 'Rome',
            'Never Summer', 'Gnu', 'Arbor', 'Bataleon', 'YES', 'Rossignol',
            'Roxy', 'Forum', 'Gilson', 'Public', 'United Shapes', 'WhiteSpace',
            'Nidecker', 'Jones', 'DC', 'Switchback', 'Slash', 'Telos', 'Weston',
            'Signal', 'Kemper', 'Dinosaurs Will Die', 'Salty Peaks'
        ]

    def get_page(self, page_num=1):
        try:
            if page_num == 1:
                url = f'{self.base_url}/products/2672/equipment-snowboards?view=all'
            else:
                url = f'{self.base_url}/products/2672/equipment-snowboards?page={page_num}&view=all'
            
            logger.info(f'获取页面 {page_num}: {url[:80]}...')
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            if response.status_code != 200:
                logger.warning(f'状态码异常: {response.status_code}')
                return None
            
            if len(response.text) < 5000:
                logger.warning('页面内容过少')
                return None
                
            return response.text
            
        except requests.exceptions.Timeout:
            logger.error(f'页面 {page_num} 请求超时')
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f'页面 {page_num} 请求失败: {e}')
            return None
        except Exception as e:
            logger.error(f'获取页面 {page_num} 时发生错误: {e}')
            return None

    def parse_products(self, html_content, page_num):
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        debug_file = f'logs/debug_page_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{page_num}.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        product_selectors = [
            '[data-product-id]', '.product-card', '.product-item', 
            '.product', '.grid-item', '.tile', '.product-tile',
            '.item.product', 'li.product-item', 'div.product-block'
        ]
        
        products_found = []
        for selector in product_selectors:
            found = soup.select(selector)
            if found and len(found) > 3:
                products_found = found
                logger.info(f'使用选择器 "{selector}" 找到 {len(products_found)} 个产品容器')
                break
        
        if not products_found:
            logger.warning('尝试备用解析方法')
            all_divs = soup.find_all(['div', 'li'], class_=lambda x: x and any(key in str(x).lower() for key in ['product', 'item', 'card']))
            products_found = all_divs[:50]
        
        logger.info(f'页面 {page_num} 找到 {len(products_found)} 个潜在产品容器')
        
        for i, container in enumerate(products_found):
            try:
                product = self.extract_product(container, i+1)
                if product and product.get('name') and product.get('name') != '未知产品':
                    self.product_count += 1
                    product['id'] = f'product_{self.product_count}'
                    products.append(product)
                    
                    if len(products) % 5 == 0:
                        logger.info(f'页面 {page_num} 已提取 {len(products)} 个产品')
                        
            except Exception as e:
                logger.error(f'解析产品 {i+1} 失败: {e}')
                continue
        
        return products

    def extract_product(self, container, index):
        try:
            container_html = str(container)[:500]
            
            name = self.extract_name(container)
            if not name or len(name) < 3 or name == '未知产品':
                return None
            
            brand = self.extract_brand(name, container.get_text())
            price_data = self.extract_price(container)
            image_url = self.extract_image(container)
            product_url = self.extract_url(container)
            category = self.detect_category(name, brand)
            
            image_filename = None
            if image_url:
                try:
                    image_filename = self.download_image(image_url, brand, name, index)
                except Exception as e:
                    logger.warning(f'下载图片失败: {e}')
            
            product = {
                'id': f'prod_{int(time.time())}_{index}',
                'brand': brand,
                'name': name[:150].strip(),
                'current_price': price_data.get('current'),
                'original_price': price_data.get('original'),
                'discount': price_data.get('discount'),
                'image_url': image_url,
                'local_image': image_filename,
                'product_url': product_url,
                'category': category,
                'scraped_at': datetime.now().isoformat(),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if not product.get('current_price'):
                product['current_price'] = None
            
            return product
            
        except Exception as e:
            logger.error(f'提取产品失败: {e}', exc_info=True)
            return None

    def extract_name(self, container):
        name_selectors = [
            '.product-name', '.name', 'h1', 'h2', 'h3', 'h4',
            '.title', '[itemprop="name"]', '.product-title',
            'a.product-name', '.card-title', '.item-name',
            '.product-name a', 'h2 a', 'h3 a', 'h4 a',
            '[data-product-title]', '.productName'
        ]
        
        for selector in name_selectors:
            element = container.select_one(selector)
            if element and element.text.strip():
                name = element.text.strip()
                if len(name) > 3 and not re.match(r'^\$[\d,]+', name):
                    return name
        
        link = container.find('a', href=True)
        if link and link.text.strip():
            name = link.text.strip()
            if len(name) > 3:
                return name
        
        text = container.get_text(strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            if 5 <= len(line) <= 100:
                if not re.match(r'^\$[\d,]+', line) and not re.match(r'^[A-Z\s]+$', line):
                    if not any(word in line.lower() for word in ['select', 'compare', 'size', 'color', 'quantity', 'add to cart']):
                        return line
        
        alt_text = container.find('img', alt=True)
        if alt_text and alt_text.get('alt'):
            return alt_text.get('alt')[:100]
        
        return "未知产品"

    def extract_brand(self, product_name, text):
        text_lower = text.lower()
        name_lower = product_name.lower()
        
        for brand in self.brands:
            if brand.lower() in text_lower or brand.lower() in name_lower:
                return brand
        
        brand_patterns = {
            r'(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+snowboard|\s+board)': 1,
            r'brand[:\s]+([A-Z][a-zA-Z\s]+)': 1,
        }
        
        for pattern, group in brand_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_brand = match.group(group).strip()
                if len(potential_brand) > 1 and len(potential_brand) < 30:
                    return potential_brand
        
        words = product_name.split()
        if words and len(words[0]) > 1:
            first_word = words[0]
            if first_word[0].isupper() and not first_word.isupper():
                return first_word
        
        return "其他品牌"

    def extract_price(self, container):
        text = container.get_text()
        
        price_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|usd)',
            r'price[:\s]+\$(\d+[\d,.]*)',
            r'now[:\s]+\$(\d+[\d,.]*)',
        ]
        
        all_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    clean_price = str(match).replace(',', '')
                    price_float = float(clean_price)
                    if price_float > 0 and price_float < 10000:
                        all_prices.append(price_float)
                except ValueError:
                    continue
        
        all_prices = list(set(all_prices))
        all_prices.sort()
        
        price_data = {}
        
        if len(all_prices) >= 2:
            price_data['current'] = f"${all_prices[0]:.2f}"
            price_data['original'] = f"${all_prices[-1]:.2f}"
            if all_prices[-1] > 0:
                discount = ((all_prices[-1] - all_prices[0]) / all_prices[-1]) * 100
                price_data['discount'] = f"-{int(discount)}%"
        elif all_prices:
            price_data['current'] = f"${all_prices[0]:.2f}"
            price_data['original'] = None
            price_data['discount'] = None
        else:
            price_selectors = [
                '.price', '.current-price', '.sale-price', 
                '.product-price', '[data-price]', '.amount',
                '.Price', '.price--current'
            ]
            for selector in price_selectors:
                element = container.select_one(selector)
                if element:
                    price_text = element.get_text(strip=True)
                    matches = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_text)
                    if matches:
                        try:
                            price = float(matches[0].replace(',', ''))
                            price_data['current'] = f"${price:.2f}"
                            break
                        except:
                            continue
        
        if not price_data.get('current'):
            price_data['current'] = None
            price_data['original'] = None
            price_data['discount'] = None
        
        return price_data

    def extract_image(self, container):
        img_selectors = [
            'img[src]', 'img[data-src]', 'img[data-original-src]',
            'img[data-original]', 'img[data-lazy-src]', 'source[srcset]',
            '.product-image img', '.main-image img', '.thumbnail img',
            '[data-product-image]', 'img.product-image', '.card-img img'
        ]
        
        for selector in img_selectors:
            img = container.select_one(selector)
            if not img:
                continue
                
            src = None
            src_attrs = ['src', 'data-src', 'data-original-src', 'data-original', 'data-lazy-src', 'srcset']
            
            for attr in src_attrs:
                if img.get(attr):
                    src = img.get(attr)
                    break
            
            if not src:
                continue
            
            if isinstance(src, str) and ' ' in src and ',' in src:
                src = src.split(',')[0].split(' ')[0]
            
            src = src.strip()
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(self.base_url, src)
            elif not src.startswith(('http://', 'https://')):
                src = urljoin(self.base_url, '/' + src.lstrip('/'))
            
            if src and not src.startswith(('data:', 'javascript:', 'about:')):
                if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    return src
        
        return None

    def extract_url(self, container):
        link_selectors = [
            'a[href]', '.product-link', 'a.product-name',
            'a[data-product-link]', 'a.title', 'h2 a', 'h3 a',
            '.product-title a', '.name a'
        ]
        
        for selector in link_selectors:
            link = container.select_one(selector)
            if link and link.get('href'):
                href = link.get('href').strip()
                if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    if href.startswith('/'):
                        return urljoin(self.base_url, href)
                    elif href.startswith(('http://', 'https://')):
                        return href
                    else:
                        return urljoin(self.base_url, '/' + href.lstrip('/'))
        
        parent_link = container.find_parent('a', href=True)
        if parent_link and parent_link.get('href'):
            href = parent_link.get('href').strip()
            if href and not href.startswith(('#', 'javascript:')):
                if href.startswith('/'):
                    return urljoin(self.base_url, href)
                elif href.startswith('http'):
                    return href
        
        return None

    def detect_category(self, name, brand):
        name_lower = name.lower()
        
        categories = {
            '男子雪板': ['men', "men's", '男子', '男款', 'male', 'man', "man's"],
            '女子雪板': ['women', "women's", '女子', '女款', 'female', 'lady', 'ladies', "lady's"],
            '儿童雪板': ['kids', "kid's", 'child', 'children', 'youth', 'junior', '儿童', '少儿'],
            '自由式雪板': ['freestyle', 'park', 'jib', 'twin', 'twin-tip'],
            '全能雪板': ['all-mountain', 'all mountain', 'all-mtn', 'allmtn', 'freeride', 'allround'],
            '野雪雪板': ['powder', 'pow', 'backcountry', '野雪', 'powder board'],
            '定向板': ['directional', 'directional twin'],
            '初学者雪板': ['beginner', 'starter', 'learn', '初学者', '新手']
        }
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        if 'women' in name_lower or "women's" in name_lower or 'female' in name_lower:
            return '女子雪板'
        elif 'men' in name_lower or "men's" in name_lower or 'male' in name_lower:
            return '男子雪板'
        elif 'kids' in name_lower or 'youth' in name_lower or 'junior' in name_lower:
            return '儿童雪板'
        
        return '其他雪板'

    def download_image(self, image_url, brand, name, index):
        if not image_url:
            return None
        
        try:
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                ext = '.jpg'
            else:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    ext = '.jpg'
            
            safe_brand = re.sub(r'[<>:"/\\|?*]', '', brand or 'unknown')[:20]
            safe_name = re.sub(r'[<>:"/\\|?*]', '', name or 'product')[:30]
            safe_name = re.sub(r'\s+', '_', safe_name)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_brand}_{safe_name}_{index}_{timestamp}{ext}"
            filepath = Path('web/images') / filename
            
            if filepath.exists():
                return filename
            
            logger.info(f'下载图片: {image_url[:60]}...')
            response = self.session.get(image_url, timeout=10)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            file_size = filepath.stat().st_size
            if file_size < 1024:
                filepath.unlink()
                logger.warning('图片文件过小，已删除')
                return None
            
            return filename
            
        except requests.exceptions.RequestException as e:
            logger.warning(f'图片下载失败 {image_url[:50]}: {e}')
            return None
        except Exception as e:
            logger.error(f'图片处理失败: {e}')
            return None

    def save_data(self, products):
        if not products:
            logger.warning('没有数据可保存')
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        json_data = {
            'metadata': {
                'total_products': len(products),
                'unique_brands': len(set(p.get('brand', '') for p in products if p.get('brand'))),
                'scraped_at': datetime.now().isoformat(),
                'source': self.base_url,
                'version': '1.0'
            },
            'products': products
        }
        
        json_file_web = 'web/data.json'
        with open(json_file_web, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        json_file_backup = f'data/snowboards_{timestamp}.json'
        with open(json_file_backup, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        csv_file = f'data/snowboards_{timestamp}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            if products:
                fieldnames = ['id', 'brand', 'name', 'current_price', 'original_price', 
                            'discount', 'category', 'product_url', 'image_url', 
                            'local_image', 'scraped_at']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for product in products:
                    row = {field: product.get(field, '') for field in fieldnames}
                    writer.writerow(row)
        
        logger.info(f'保存JSON数据: {json_file_web} 和 {json_file_backup}')
        logger.info(f'保存CSV数据: {csv_file}')
        
        with open('data/snowboards_latest.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return {
            'json': json_file_web,
            'csv': csv_file,
            'count': len(products)
        }

    def scrape(self, max_pages=3, delay_between_pages=2):
        logger.info('开始爬取雪板数据...')
        logger.info(f'目标网站: {self.base_url}')
        logger.info(f'计划爬取页数: {max_pages}')
        
        all_products = []
        successful_pages = 0
        
        for page in range(1, max_pages + 1):
            logger.info(f'处理第 {page}/{max_pages} 页')
            
            html = self.get_page(page)
            if not html:
                logger.warning(f'第 {page} 页获取失败，跳过')
                continue
            
            products = self.parse_products(html, page)
            all_products.extend(products)
            successful_pages += 1
            
            logger.info(f'第 {page} 页完成，获取 {len(products)} 个产品')
            
            if page < max_pages and products:
                delay = delay_between_pages + random.uniform(0.5, 2.0)
                logger.info(f'等待 {delay:.1f} 秒后继续...')
                time.sleep(delay)
        
        if not all_products:
            logger.error('没有获取到任何产品数据')
            return None
        
        seen = set()
        unique_products = []
        for product in all_products:
            key = f"{product.get('brand')}_{product.get('name')}_{product.get('current_price')}"
            if key not in seen:
                seen.add(key)
                unique_products.append(product)
        
        logger.info(f'去重后剩余 {len(unique_products)} 个产品，来自 {successful_pages} 个有效页面')
        
        saved_files = self.save_data(unique_products)
        
        brands = {}
        categories = {}
        price_stats = {'under_500': 0, '500_1000': 0, 'over_1000': 0}
        
        for product in unique_products:
            brand = product.get('brand', '未知品牌')
            brands[brand] = brands.get(brand, 0) + 1
            
            category = product.get('category', '其他')
            categories[category] = categories.get(category, 0) + 1
            
            try:
                price_str = str(product.get('current_price', '0')).replace('$', '').replace(',', '')
                price = float(price_str) if price_str else 0
                if price < 500:
                    price_stats['under_500'] += 1
                elif price <= 1000:
                    price_stats['500_1000'] += 1
                else:
                    price_stats['over_1000'] += 1
            except:
                pass
        
        logger.info('=' * 60)
        logger.info('爬取统计:')
        logger.info(f'  总计产品: {len(unique_products)} 个')
        logger.info(f'  有效页面: {successful_pages}/{max_pages}')
        logger.info(f'  品牌数量: {len(brands)} 个')
        logger.info(f'  类别数量: {len(categories)} 个')
        logger.info(f'  价格分布: <$500: {price_stats["under_500"]}, $500-$1000: {price_stats["500_1000"]}, >$1000: {price_stats["over_1000"]}')
        logger.info('=' * 60)
        
        return {
            'products': unique_products,
            'stats': {
                'total': len(unique_products),
                'brands': len(brands),
                'categories': len(categories),
                'price_stats': price_stats
            },
            'files': saved_files
        }

def main():
    print("=" * 60)
    print("🏂 雪板数据爬虫 v1.0")
    print("=" * 60)
    
    try:
        scraper = SnowboardsScraper()
        
        result = scraper.scrape(max_pages=3, delay_between_pages=2)
        
        if result:
            products = result['products']
            stats = result['stats']
            files = result['files']
            
            print(f"\n✅ 爬取完成！")
            print(f"📊 统计信息:")
            print(f"  📦 产品总数: {stats['total']}")
            print(f"  🏷️ 品牌数量: {stats['brands']}")
            print(f"  📁 类别数量: {stats['categories']}")
            
            price_stats = stats['price_stats']
            print(f"  💰 价格分布:")
            print(f"    < $500: {price_stats['under_500']}")
            print(f"    $500-$1000: {price_stats['500_1000']}")
            print(f"    > $1000: {price_stats['over_1000']}")
            
            print(f"\n📁 生成文件:")
            print(f"  🌐 Web数据: web/data.json")
            print(f"  💾 JSON备份: data/snowboards_*.json")
            print(f"  📄 CSV数据: data/snowboards_*.csv")
            print(f"  🖼️ 图片目录: web/images/")
            
            if products:
                print(f"\n🎯 前5个产品示例:")
                for i, product in enumerate(products[:5]):
                    print(f"{i+1}. {product.get('brand')} - {product.get('name')[:40]}...")
                    price = product.get('current_price', '价格待定')
                    if product.get('discount'):
                        price += f" ({product.get('discount')})"
                    print(f"   💰 {price} | 🏷️ {product.get('category')}")
            
            return 0
        else:
            print("❌ 爬取失败，没有获取到数据")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断")
        return 130
    except Exception as e:
        logger.error(f"主程序错误: {e}", exc_info=True)
        print(f"\n❌ 错误: {e}")
        return 1

if __name__ == '__main__':
    exit(main())