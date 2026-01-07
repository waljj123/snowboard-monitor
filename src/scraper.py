import requests
from bs4 import BeautifulSoup
import json
import os
import re
import logging
from datetime import datetime
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_snowboards():
    """爬取雪板数据 - 修复版本"""
    logger.info("开始爬取雪板数据...")
    
    try:
        # 模拟真实数据 - 实际使用时替换为真实爬取逻辑
        sample_products = [
            {
                "id": "1",
                "brand": "Burton",
                "name": "Custom X Snowboard 2024",
                "current_price": 899.99,
                "original_price": 999.99,
                "discount": "10%",
                "image_url": "https://images.unsplash.com/photo-1511895426328-dc8714191300?w=300",
                "product_url": "https://snowboards.com/products/burton-custom-x",
                "category": "男子雪板",
                "scraped_at": datetime.now().isoformat()
            },
            {
                "id": "2",
                "brand": "Lib Tech", 
                "name": "Golden Orca Snowboard",
                "current_price": 849.99,
                "original_price": None,
                "discount": None,
                "image_url": "https://images.unsplash.com/photo-1543457508-8d5d0ef5d65b?w=300",
                "product_url": "https://snowboards.com/products/libtech-golden-orca",
                "category": "男子雪板",
                "scraped_at": datetime.now().isoformat()
            },
            {
                "id": "3", 
                "brand": "Salomon",
                "name": "Women's Rhythm Snowboard",
                "current_price": 599.99,
                "original_price": 699.99,
                "discount": "14%",
                "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300",
                "product_url": "https://snowboards.com/products/salomon-womens-rhythm",
                "category": "女子雪板",
                "scraped_at": datetime.now().isoformat()
            }
        ]
        
        # 保存数据
        data = {
            "last_updated": datetime.now().isoformat(),
            "product_count": len(sample_products),
            "products": sample_products
        }
        
        # 确保data目录存在
        os.makedirs("data", exist_ok=True)
        
        with open("data/snowboards.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存，共 {len(sample_products)} 个产品")
        return sample_products
        
    except Exception as e:
        logger.error(f"爬取数据时出错: {e}")
        # 返回空数据避免后续错误
        return []

if __name__ == "__main__":
    scrape_snowboards()