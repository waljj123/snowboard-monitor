import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
import re
import os
import sys
import logging
from datetime import datetime
from urllib.parse import urljoin

# 确保必要的目录存在
def setup_directories():
    """创建必要的目录"""
    directories = ['logs', 'data', 'web/images']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ 创建目录: {directory}")

# 初始化目录
setup_directories()

# 配置日志
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 创建目录
        self.web_dir = 'web'
        self.data_dir = 'data'
        self.images_dir = os.path.join(self.web_dir, 'images')
        os.makedirs(self.web_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # 预定义品牌列表
        self.brands = [
            'Burton', 'Lib Tech', 'Salomon', 'K2', 'Capita', 'Ride', 'Rome',
            'Never Summer', 'Gnu', 'Arbor', 'Bataleon', 'YES', 'Rossignol',
            'Roxy', 'Forum', 'Gilson', 'Public', 'United Shapes', 'WhiteSpace',
            'Nidecker', 'Jones', 'DC', 'Switchback', 'Slash', 'Telos', 'Weston'
        ]

    def get_page(self, page_num=1):
        """获取页面内容"""
        try:
            if page_num == 1:
                url = f'{self.base_url}/products/2672/equipment-snowboards?view=all'
            else:
                url = f'{self.base_url}/products/2672/equipment-snowboards?page={page_num}&view=all'
            
            logger.info(f'📄 获取页面 {page_num}')
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            if len(response.text) < 1000:
                logger.warning('页面内容过少')
                return None
                
            logger.info(f'✅ 成功获取页面 {page_num}')
            return response.text
            
        except Exception as e:
            logger.error(f'❌ 获取页面失败: {e}')
            return None

    def parse_products(self, html_content):
        """解析产品信息"""
        if not html_content:
            return []
            
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # 保存HTML用于调试
        debug_file = os.path.join(self.data_dir, f'debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f'💾 保存调试HTML到: {debug_file}')
        
        # 尝试多种选择器定位产品
        product_selectors = [
            '.product-item', '.product-card', '.product', 
            'div[data-product-id]', '.item', '.grid-item',
            '.tile', '.product-tile', 'li.product',
            'article.product', 'div.product-tile'
        ]
        
        products_found = []
        for selector in product_selectors:
            products_found = soup.select(selector)
            if products_found:
                logger.info(f'🔍 使用选择器 "{selector}" 找到 {len(products_found)} 个产品')
                break
        
        if not products_found:
            logger.info('尝试通用选择器')
            products_found = soup.find_all(['div', 'li', 'article'], 
                                         class_=lambda x: x and any(word in str(x) for word in ['product', 'item', 'card', 'tile']))
        
        logger.info(f'📊 找到 {len(products_found)} 个潜在产品容器')
        
        for i, container in enumerate(products_found[:50]):
            try:
                product = self.extract_product(container)
                if product and product.get('name') and product.get('name') != '未知产品':
                    products.append(product)
                    logger.info(f'✅ 提取产品 {i+1}: {product.get("brand", "未知")} - {product.get("name")[:30]}...')
            except Exception as e:
                logger.error(f'❌ 解析产品 {i+1} 失败: {e}')
                continue
        
        return products

    def extract_product(self, container):
        """从容器提取单个产品信息"""
        try:
            # 获取产品名称
            name = self.extract_name(container)
            if not name or name == '未知产品':
                return None
            
            # 获取品牌
            brand = self.extract_brand(name, container.get_text())
            
            # 获取价格
            price_data = self.extract_price(container)
            
            # 获取图片
            image_url = self.extract_image(container)
            
            # 获取链接
            product_url = self.extract_url(container)
            
            # 下载图片
            image_filename = self.download_image(image_url, brand, name) if image_url else None
            
            product = {
                'id': f'prod_{int(time.time())}_{random.randint(1000, 9999)}',
                'brand': brand,
                'name': name[:200],
                'current_price': price_data.get('current'),
                'original_price': price_data.get('original'),
                'discount': price_data.get('discount'),
                'image_url': image_url,
                'local_image': image_filename,
                'product_url': product_url,
                'category': self.detect_category(name, brand),
                'scraped_at': datetime.now().isoformat(),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return product
            
        except Exception as e:
            logger.error(f'提取产品失败: {e}')
            return None

    def extract_name(self, container):
        """提取产品名称"""
        # 尝试多种选择器
        name_selectors = [
            '.product-name', '.name', 'h1', 'h2', 'h3', 'h4',
            '.title', '[itemprop="name"]', '.product-title',
            'a.product-name', '.product-link', '.card-title',
            '.product-name a', 'h2 a', '.product__title'
        ]
        
        for selector in name_selectors:
            element = container.select_one(selector)
            if element and element.text.strip():
                name = element.text.strip()
                if len(name) > 3 and not name.lower().startswith(('$', 'from', 'select')):
                    return name
        
        # 从整个容器文本中提取
        text = container.get_text(strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if 10 <= len(line) <= 100:
                if not line.startswith('$') and not any(word in line.lower() for word in ['compare', 'select', 'size', 'color']):
                    return line
        
        return "未知产品"

    def extract_brand(self, product_name, text):
        """提取品牌"""
        text_lower = text.lower()
        product_name_lower = product_name.lower()
        
        # 从预定义品牌列表匹配
        for brand in self.brands:
            if brand.lower() in text_lower or brand.lower() in product_name_lower:
                return brand
        
        # 常见品牌关键词
        brand_keywords = {
            'burton': 'Burton',
            'lib tech': 'Lib Tech',
            'libtech': 'Lib Tech',
            'salomon': 'Salomon',
            'k2': 'K2',
            'capita': 'Capita',
            'ride': 'Ride',
            'rome': 'Rome',
            'never summer': 'Never Summer',
            'gnu': 'Gnu',
            'arbor': 'Arbor',
            'bataleon': 'Bataleon',
            'yes.': 'YES',
            'rossignol': 'Rossignol',
            'roxy': 'Roxy'
        }
        
        for keyword, brand in brand_keywords.items():
            if keyword in text_lower or keyword in product_name_lower:
                return brand
        
        # 从产品名称开头提取可能的品牌
        words = product_name.split()
        if len(words) > 1:
            first_word = words[0]
            if len(first_word) > 1 and first_word[0].isupper():
                return first_word
        
        return "其他品牌"

    def extract_price(self, container):
        """提取价格信息"""
        text = container.get_text()
        
        # 查找所有价格
        price_pattern = r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        prices = re.findall(price_pattern, text)
        
        # 清理价格
        price_values = []
        for price in prices:
            try:
                clean_price = price.replace(',', '')
                price_float = float(clean_price)
                price_values.append(price_float)
            except ValueError:
                continue
        
        price_values = sorted(set(price_values))
        price_data = {}
        
        if len(price_values) >= 2:
            price_data['current'] = f"${price_values[0]:.2f}"
            price_data['original'] = f"${price_values[1]:.2f}"
            if price_values[1] > 0:
                discount = (price_values[1] - price_values[0]) / price_values[1] * 100
                price_data['discount'] = f"-{int(discount)}%"
        elif price_values:
            price_data['current'] = f"${price_values[0]:.2f}"
            price_data['original'] = None
            price_data['discount'] = None
        else:
            price_data['current'] = None
            price_data['original'] = None
            price_data['discount'] = None
        
        return price_data

    def extract_image(self, container):
        """提取图片URL"""
        img_selectors = [
            'img[src]', 'img[data-src]', 'img[data-original]',
            '.product-image img', '.main-image img', '.product-img',
            '[data-product-image]', 'source[srcset]', 'img.product-image',
            'img[class*="image"]', 'img[loading="lazy"]'
        ]
        
        for selector in img_selectors:
            img = container.select_one(selector)
            if img:
                src = None
                for attr in ['src', 'data-src', 'data-original', 'srcset', 'data-srcset']:
                    if img.get(attr):
                        src = img.get(attr)
                        break
                
                if src:
                    # 处理srcset
                    if ' ' in src and ',' in src:
                        src = src.split(',')[0].split(' ')[0]
                    
                    # 清理URL
                    src = src.strip()
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    
                    if src and not src.startswith(('data:', 'javascript:')):
                        return src
        
        return None

    def extract_url(self, container):
        """提取产品链接"""
        link_selectors = ['a[href]', '.product-link', 'a.product-name', 'a[class*="link"]', 'a.product__link']
        
        for selector in link_selectors:
            link = container.select_one(selector)
            if link and link.get('href'):
                href = link.get('href').strip()
                if href and not href.startswith(('#', 'javascript:')):
                    if href.startswith('/'):
                        return urljoin(self.base_url, href)
                    elif href.startswith('http'):
                        return href
        
        return None

    def detect_category(self, name, brand):
        """检测产品类别"""
        name_lower = name.lower()
        
        categories = {
            '男子雪板': ['men', "men's", '男子', '男款', 'male'],
            '女子雪板': ['women', "women's", '女子', '女款', 'female', 'ladies'],
            '儿童雪板': ['kid', 'child', '儿童', '少儿', 'youth', 'junior'],
            '自由式雪板': ['freestyle', 'park', 'jib', 'twin'],
            '全能雪板': ['all-mountain', 'all mountain', 'freeride'],
            '野雪雪板': ['powder', 'pow', 'backcountry', '野雪']
        }
        
        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return '雪板'

    def download_image(self, image_url, brand, name):
        """下载产品图片"""
        if not image_url:
            return None
        
        try:
            safe_brand = re.sub(r'[<>:"/\\|?*]', '', brand)[:20]
            safe_name = re.sub(r'[<>:"/\\|?*]', '', name)[:30]
            safe_name = re.sub(r'\s+', '_', safe_name)
            
            ext = 'jpg'
            if '.' in image_url:
                url_ext = image_url.split('.')[-1].lower().split('?')[0]
                if url_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    ext = url_ext
            
            filename = f"{safe_brand}_{safe_name}_{int(time.time())%10000}.{ext}"
            filepath = os.path.join(self.images_dir, filename)
            
            if os.path.exists(filepath):
                return filename
            
            logger.info(f'⬇️ 下载图片: {image_url[:50]}...')
            response = self.session.get(image_url, timeout=15)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f'✅ 图片保存: {filename}')
            return filename
            
        except Exception as e:
            logger.error(f'❌ 下载图片失败: {e}')
            return None

    def save_data(self, products):
        """保存数据到JSON和CSV"""
        if not products:
            logger.warning('⚠️ 没有数据可保存')
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON数据
        json_data = {
            'metadata': {
                'total_products': len(products),
                'unique_brands': len(set(p['brand'] for p in products)),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': self.base_url
            },
            'products': products
        }
        
        # 保存到web目录用于GitHub Pages
        json_file = os.path.join(self.web_dir, 'data.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # 同时保存到data目录备份
        json_file_backup = os.path.join(self.data_dir, f'snowboards_{timestamp}.json')
        with open(json_file_backup, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f'💾 保存JSON数据: {json_file}')
        
        # 保存CSV备份
        csv_file_backup = os.path.join(self.data_dir, f'snowboards_{timestamp}.csv')
        with open(csv_file_backup, 'w', newline='', encoding='utf-8-sig') as f:
            if products:
                fieldnames = products[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(products)
        
        logger.info(f'💾 保存CSV数据: {csv_file_backup}')
        
        return {
            'json': json_file,
            'csv': csv_file_backup,
            'count': len(products)
        }

    def scrape_all_pages(self, max_pages=2):
        """爬取所有页面"""
        logger.info('🚀 开始爬取雪板数据...')
        logger.info(f'📁 数据目录: {self.data_dir}')
        logger.info(f'🖼️ 图片目录: {self.images_dir}')
        
        all_products = []
        
        for page in range(1, max_pages + 1):
            logger.info(f'📄 正在处理第 {page}/{max_pages} 页')
            
            # 获取页面
            html = self.get_page(page)
            if not html:
                logger.warning(f'⚠️ 第 {page} 页获取失败')
                if page == 1:
                    logger.error('❌ 第一页获取失败')
                    break
                continue
            
            # 解析产品
            products = self.parse_products(html)
            logger.info(f'✅ 第 {page} 页找到 {len(products)} 个产品')
            
            all_products.extend(products)
            
            # 页间延迟
            if page < max_pages and products:
                delay = random.uniform(2, 4)
                logger.info(f'⏳ 等待 {delay:.1f} 秒后继续...')
                time.sleep(delay)
        
        # 去重
        seen = set()
        unique_products = []
        for product in all_products:
            product_key = f"{product.get('brand')}_{product.get('name')}_{product.get('current_price')}"
            if product_key not in seen:
                seen.add(product_key)
                unique_products.append(product)
        
        logger.info(f'📊 去重后剩余 {len(unique_products)} 个产品')
        
        if unique_products:
            # 保存数据
            saved_files = self.save_data(unique_products)
            
            # 统计信息
            brands = set(p['brand'] for p in unique_products)
            categories = set(p['category'] for p in unique_products)
            
            logger.info('=' * 50)
            logger.info(f'✅ 爬取完成！')
            logger.info(f'📦 总计产品: {len(unique_products)} 个')
            logger.info(f'🏷️ 品牌数量: {len(brands)} 个')
            logger.info(f'📁 类别数量: {len(categories)} 个')
            logger.info('=' * 50)
            
            return {
                'products': unique_products,
                'files': {
                    'json': saved_files["json"] if saved_files else None,
                    'csv': saved_files["csv"] if saved_files else None
                }
            }
        else:
            logger.error('❌ 没有获取到任何产品数据')
            return None

def main():
    """主函数"""
    print("=" * 60)
    print("🏂 雪板数据爬虫")
    print("=" * 60)
    
    try:
        # 创建爬虫实例
        scraper = SnowboardsScraper()
        
        # 爬取数据
        result = scraper.scrape_all_pages(max_pages=2)
        
        if result:
            products = result['products']
            files = result['files']
            
            print(f"\n✅ 爬取完成！共获取 {len(products)} 个产品")
            print(f"\n📁 生成的文件:")
            print(f"  📄 JSON文件: {files.get('json', '无')}")
            print(f"  📊 CSV文件: {files.get('csv', '无')}")
            print(f"  🖼️ 图片目录: {scraper.images_dir}/")
            
            # 显示统计信息
            brands = {}
            for product in products:
                brand = product.get('brand', '未知品牌')
                brands[brand] = brands.get(brand, 0) + 1
            
            print(f"\n📈 品牌统计:")
            for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {brand}: {count} 个产品")
            
            # 显示前几个产品示例
            print(f"\n🎯 产品示例 (前3个):")
            for i, product in enumerate(products[:3]):
                print(f"{i+1}. {product.get('brand')} - {product.get('name')[:40]}...")
                price_info = product.get('current_price', '价格待定')
                if product.get('discount'):
                    price_info += f" ({product.get('discount')} 折扣)"
                print(f"   💰 价格: {price_info}")
                print(f"   🏷️ 类别: {product.get('category')}")
                print()
        else:
            print("❌ 爬取失败，没有获取到数据")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 程序运行出错: {e}", exc_info=True)
        print(f"\n❌ 程序运行出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()