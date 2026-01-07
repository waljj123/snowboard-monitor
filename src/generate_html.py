# src/generate_html.py
import json
import os
from datetime import datetime

def generate_html_report():
    """生成HTML报告"""
    
    # 读取数据
    with open('data/snowboards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data['products']
    
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏂 雪板价格监控 - GitHub Pages</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header { 
                background: #2c3e50; 
                color: white; 
                padding: 30px; 
                text-align: center;
            }
            .stats { 
                display: flex; 
                justify-content: center; 
                gap: 20px; 
                flex-wrap: wrap;
                margin: 20px 0;
            }
            .stat-item { 
                background: #3498db; 
                padding: 10px 20px; 
                border-radius: 20px; 
                font-size: 14px;
            }
            .product-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
                gap: 20px; 
                padding: 20px;
            }
            .product-card { 
                border: 1px solid #ddd; 
                border-radius: 10px; 
                overflow: hidden; 
                transition: transform 0.3s;
            }
            .product-card:hover { 
                transform: translateY(-5px); 
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .product-image { 
                width: 100%; 
                height: 200px; 
                object-fit: cover; 
                background: #f5f5f5;
            }
            .product-info { 
                padding: 15px; 
            }
            .product-brand { 
                color: #7f8c8d; 
                font-size: 12px; 
                text-transform: uppercase;
            }
            .product-name { 
                font-weight: bold; 
                margin: 5px 0; 
                line-height: 1.4;
            }
            .price { 
                color: #e74c3c; 
                font-weight: bold; 
                font-size: 1.2em;
            }
            .original-price { 
                text-decoration: line-through; 
                color: #95a5a6; 
                margin-right: 10px;
            }
            .discount { 
                background: #27ae60; 
                color: white; 
                padding: 2px 6px; 
                border-radius: 3px;
                font-size: 0.8em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏂 雪板价格监控系统</h1>
                <p>基于GitHub Actions的自动更新系统</p>
                <div class="stats">
                    <div class="stat-item">产品总数: {product_count}</div>
                    <div class="stat-item">最后更新: {last_updated}</div>
                    <div class="stat-item">数据来源: Snowboards.com</div>
                </div>
            </div>
            
            <div class="product-grid">
                {products_html}
            </div>
            
            <div style="text-align: center; padding: 20px; color: #7f8c8d; font-size: 14px;">
                <p>🤖 本页面由GitHub Actions自动生成 | 更新频率: 每日</p>
                <p>📱 微信小程序: 搜索"雪板监控"</p>
            </div>
        </div>
        
        <script>
            // 简单的搜索功能
            function searchProducts() {
                const input = document.getElementById('searchInput').value.toLowerCase();
                const products = document.querySelectorAll('.product-card');
                
                products.forEach(product => {
                    const text = product.textContent.toLowerCase();
                    product.style.display = text.includes(input) ? 'block' : 'none';
                });
            }
        </script>
    </body>
    </html>
    """
    
    # 生成产品HTML
    products_html = ""
    for product in products[:50]:  # 限制显示数量
        products_html += f"""
        <div class="product-card">
            <img src="{product.get('image_url', '')}" 
                 alt="{product['name']}" 
                 class="product-image"
                 onerror="this.src='https://via.placeholder.com/300x200?text=暂无图片'">
            <div class="product-info">
                <div class="product-brand">{product['brand']}</div>
                <div class="product-name">{product['name']}</div>
                <div class="price">
                    {f"<span class='original-price'>${product['original_price']}</span>" if product['original_price'] else ''}
                    <span class="current-price">${product['current_price']}</span>
                    {f"<span class='discount'>{product['discount']}</span>" if product['discount'] else ''}
                </div>
            </div>
        </div>
        """
    
    # 填充模板
    html_content = html_template.format(
        product_count=len(products),
        last_updated=data['last_updated'],
        products_html=products_html
    )
    
    # 保存HTML文件
    with open('web/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML页面已生成，包含 {len(products)} 个产品")

if __name__ == "__main__":
    generate_html_report()