#!/usr/bin/env python3
import os
import json
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_github_pages_html():
    data_file = 'web/data.json'
    if not os.path.exists(data_file):
        logger.error(f'数据文件不存在: {data_file}')
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data.get('products', [])
    metadata = data.get('metadata', {})
    
    if not products:
        logger.warning('没有产品数据')
        return None
    
    total_products = len(products)
    brands = {}
    categories = {}
    price_stats = {
        'under_500': 0,
        '500_1000': 0,
        'over_1000': 0
    }
    
    for product in products:
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
    
    top_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]
    brands_data_js = ',\n            '.join([f"{{brand: '{b}', count: {c}}}" for b, c in top_brands])
    
    product_cards = []
    for product in products[:50]:
        image_src = product.get('local_image', '')
        if image_src and os.path.exists(os.path.join('web/images', image_src)):
            img_tag = f'<img src="images/{image_src}" alt="{product["name"]}" class="product-img">'
        elif product.get('image_url'):
            img_tag = f'<img src="{product["image_url"]}" alt="{product["name"]}" class="product-img">'
        else:
            img_tag = '<div class="no-image">暂无图片</div>'
        
        price_html = f'<span class="current-price">{product.get("current_price", "价格待定")}</span>'
        if product.get('original_price'):
            price_html = f'<span class="original-price">{product["original_price"]}</span> {price_html}'
        if product.get('discount'):
            price_html += f' <span class="discount-badge">{product["discount"]}</span>'
        
        card = f'''
        <div class="product-card">
            <div class="product-image">
                {img_tag}
            </div>
            <div class="product-info">
                <h3>{product.get("brand", "")} - {product.get("name", "")}</h3>
                <div class="product-category">{product.get("category", "")}</div>
                <div class="product-price">
                    {price_html}
                </div>
                {f'<a href="{product.get("product_url", "#")}" target="_blank" class="view-btn">查看详情 →</a>' if product.get("product_url") else ''}
            </div>
        </div>
        '''
        product_cards.append(card)
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏂 雪板产品数据看板</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary-color: #3498db;
            --secondary-color: #2ecc71;
            --accent-color: #e74c3c;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333333;
            --text-light: #777777;
            --border-color: #e0e0e0;
        }}
        
        [data-theme="dark"] {{
            --primary-color: #2980b9;
            --secondary-color: #27ae60;
            --accent-color: #c0392b;
            --bg-color: #1a1a2e;
            --card-bg: #16213e;
            --text-color: #ffffff;
            --text-light: #aaaaaa;
            --border-color: #2d3748;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            transition: all 0.3s ease;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--primary-color), #8e44ad);
            color: white;
            padding: 3rem 0;
            margin-bottom: 2rem;
            border-radius: 0 0 20px 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .header-text h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .header-text p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .control-panel {{
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        
        .theme-toggle, .filter-btn, .refresh-btn {{
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover, .filter-btn:hover, .refresh-btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            gap: 20px;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-icon {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary-color), #9b59b6);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
        }}
        
        .stat-content h3 {{
            font-size: 2rem;
            color: var(--primary-color);
            margin-bottom: 5px;
        }}
        
        .stat-content p {{
            color: var(--text-light);
            font-size: 0.9rem;
        }}
        
        .products-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
            margin: 2rem 0;
        }}
        
        .product-card {{
            background: var(--card-bg);
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            border: 1px solid var(--border-color);
        }}
        
        .product-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 12px 25px rgba(0,0,0,0.15);
        }}
        
        .product-image {{
            height: 220px;
            overflow: hidden;
            position: relative;
        }}
        
        .product-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s ease;
        }}
        
        .product-card:hover .product-image img {{
            transform: scale(1.05);
        }}
        
        .product-badge {{
            position: absolute;
            top: 15px;
            right: 15px;
            background: var(--accent-color);
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }}
        
        .product-content {{
            padding: 1.5rem;
        }}
        
        .product-brand {{
            color: var(--primary-color);
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .product-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 10px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .product-category {{
            display: inline-block;
            background: var(--bg-color);
            color: var(--primary-color);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-bottom: 15px;
        }}
        
        .product-price {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .current-price {{
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }}
        
        .original-price {{
            text-decoration: line-through;
            color: var(--text-light);
            font-size: 1rem;
        }}
        
        .product-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
        }}
        
        .view-btn {{
            background: var(--primary-color);
            color: white;
            text-decoration: none;
            padding: 8px 20px;
            border-radius: 25px;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        }}
        
        .view-btn:hover {{
            background: var(--secondary-color);
            transform: translateX(5px);
        }}
        
        .filters {{
            display: flex;
            gap: 15px;
            margin: 2rem 0;
            flex-wrap: wrap;
        }}
        
        .filter-select {{
            padding: 10px 20px;
            border: 2px solid var(--border-color);
            border-radius: 25px;
            background: var(--card-bg);
            color: var(--text-color);
            min-width: 150px;
        }}
        
        footer {{
            text-align: center;
            padding: 2rem 0;
            margin-top: 3rem;
            border-top: 1px solid var(--border-color);
            color: var(--text-light);
        }}
        
        .update-time {{
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}
        
        .github-link {{
            color: var(--primary-color);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        
        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin: 2rem 0;
        }}
        
        .chart-container {{
            background: var(--card-bg);
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--text-color);
        }}
        
        .search-input {{
            padding: 10px 20px;
            border: 2px solid var(--border-color);
            border-radius: 25px;
            background: var(--card-bg);
            color: var(--text-color);
            width: 100%;
            max-width: 300px;
            font-size: 1rem;
        }}
        
        .search-input:focus {{
            outline: none;
            border-color: var(--primary-color);
        }}
        
        .pagination {{
            margin: 2rem 0;
            text-align: center;
        }}
        
        .pagination-controls {{
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .pagination-btn {{
            padding: 8px 16px;
            border: 2px solid var(--border-color);
            background: var(--card-bg);
            color: var(--text-color);
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .pagination-btn:hover {{
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }}
        
        .pagination-btn.active {{
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }}
        
        .pagination-ellipsis {{
            padding: 8px 5px;
            color: var(--text-light);
        }}
        
        .notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            background: var(--card-bg);
            color: var(--text-color);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }}
        
        .notification.success {{
            border-left: 4px solid var(--secondary-color);
        }}
        
        .notification.error {{
            border-left: 4px solid var(--accent-color);
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        @keyframes slideOut {{
            from {{ transform: translateX(0); opacity: 1; }}
            to {{ transform: translateX(100%); opacity: 0; }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .product-card {{
            animation: fadeIn 0.5s ease forwards;
        }}
        
        .no-image {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-light);
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                text-align: center;
            }}
            
            .control-panel {{
                justify-content: center;
            }}
            
            .products-grid {{
                grid-template-columns: 1fr;
            }}
            
            .filters {{
                justify-content: center;
            }}
            
            .charts {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <div class="header-text">
                    <h1><i class="fas fa-snowboarding"></i> 雪板产品数据看板</h1>
                    <p>每日自动更新 | 全网雪板价格监控 | 优惠信息提醒</p>
                </div>
                <div class="control-panel">
                    <button class="theme-toggle" onclick="toggleTheme()">
                        <i class="fas fa-moon"></i> 主题切换
                    </button>
                    <button class="refresh-btn" onclick="refreshData()">
                        <i class="fas fa-sync-alt"></i> 刷新数据
                    </button>
                </div>
            </div>
        </div>
    </header>
    
    <main class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-snowboarding"></i>
                </div>
                <div class="stat-content">
                    <h3 id="total-products">{total_products}</h3>
                    <p>总产品数量</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-tags"></i>
                </div>
                <div class="stat-content">
                    <h3 id="brands-count">{len(brands)}</h3>
                    <p>品牌数量</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-filter"></i>
                </div>
                <div class="stat-content">
                    <h3 id="categories-count">{len(categories)}</h3>
                    <p>类别数量</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-calendar-alt"></i>
                </div>
                <div class="stat-content">
                    <h3 id="update-time">{metadata.get('last_updated', '').split(' ')[1] if metadata.get('last_updated') else '--:--'}</h3>
                    <p>最后更新时间</p>
                </div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-container">
                <div class="chart-title">热门品牌TOP 10</div>
                <canvas id="brandsChart" height="200"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">价格分布</div>
                <canvas id="priceChart" height="200"></canvas>
            </div>
        </div>
        
        <div class="filters">
            <input type="text" id="search-input" class="search-input" placeholder="搜索产品名称、品牌..." oninput="handleSearch()">
            <select class="filter-select" id="brand-filter" onchange="filterProducts()">
                <option value="">所有品牌</option>
            </select>
            <select class="filter-select" id="category-filter" onchange="filterProducts()">
                <option value="">所有类别</option>
            </select>
            <select class="filter-select" id="price-filter" onchange="filterProducts()">
                <option value="">所有价格</option>
                <option value="under_500">$500以下</option>
                <option value="500_1000">$500-$1000</option>
                <option value="over_1000">$1000以上</option>
            </select>
            <select class="filter-select" id="sort-by" onchange="sortProducts()">
                <option value="name">按名称排序</option>
                <option value="price_low">价格从低到高</option>
                <option value="price_high">价格从高到低</option>
                <option value="brand">按品牌排序</option>
            </select>
        </div>
        
        <div id="products-container" class="products-grid">
            {''.join(product_cards)}
        </div>
        
        <div id="pagination" class="pagination">
        </div>
    </main>
    
    <footer>
        <div class="update-time">
            数据最后更新时间: <span id="last-updated">{metadata.get('last_updated', '未知')}</span>
        </div>
        <p>
            <a href="https://github.com/yourusername/snowboard-scraper" class="github-link" target="_blank">
                <i class="fab fa-github"></i> GitHub仓库
            </a>
            | 本页面由GitHub Actions自动生成
        </p>
    </footer>
    
    <script>
        let allProducts = {json.dumps(products, ensure_ascii=False)};
        let currentProducts = [...allProducts];
        let currentPage = 1;
        const productsPerPage = 12;
        
        function toggleTheme() {{
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            const themeIcon = document.querySelector('.theme-toggle i');
            themeIcon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }}
        
        function refreshData() {{
            const btn = document.querySelector('.refresh-btn i');
            btn.className = 'fas fa-spinner fa-spin';
            
            setTimeout(() => {{
                location.reload();
            }}, 1000);
        }}
        
        function handleSearch() {{
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            if (searchTerm.length >= 2 || searchTerm.length === 0) {{
                filterProducts();
            }}
        }}
        
        function initFilters() {{
            const brands = [...new Set(allProducts.map(p => p.brand).filter(b => b))].sort();
            const categories = [...new Set(allProducts.map(p => p.category).filter(c => c))].sort();
            
            const brandFilter = document.getElementById('brand-filter');
            const categoryFilter = document.getElementById('category-filter');
            
            brands.forEach(brand => {{
                const option = document.createElement('option');
                option.value = brand;
                option.textContent = brand;
                brandFilter.appendChild(option);
            }});
            
            categories.forEach(category => {{
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categoryFilter.appendChild(option);
            }});
        }}
        
        function filterProducts() {{
            const brandFilter = document.getElementById('brand-filter').value;
            const categoryFilter = document.getElementById('category-filter').value;
            const priceFilter = document.getElementById('price-filter').value;
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            
            currentProducts = allProducts.filter(product => {{
                if (brandFilter && product.brand !== brandFilter) return false;
                if (categoryFilter && product.category !== categoryFilter) return false;
                
                if (searchTerm) {{
                    const nameMatch = product.name && product.name.toLowerCase().includes(searchTerm);
                    const brandMatch = product.brand && product.brand.toLowerCase().includes(searchTerm);
                    if (!nameMatch && !brandMatch) return false;
                }}
                
                if (priceFilter) {{
                    const priceStr = String(product.current_price || '0').replace('$', '').replace(',', '');
                    const price = parseFloat(priceStr) || 0;
                    
                    switch(priceFilter) {{
                        case 'under_500':
                            if (price >= 500) return false;
                            break;
                        case '500_1000':
                            if (price < 500 || price > 1000) return false;
                            break;
                        case 'over_1000':
                            if (price <= 1000) return false;
                            break;
                    }}
                }}
                
                return true;
            }});
            
            currentPage = 1;
            displayProducts(currentProducts);
        }}
        
        function sortProducts() {{
            const sortBy = document.getElementById('sort-by').value;
            
            currentProducts.sort((a, b) => {{
                switch(sortBy) {{
                    case 'price_low':
                        const priceA = parseFloat(String(a.current_price || '0').replace('$', '').replace(',', '')) || 0;
                        const priceB = parseFloat(String(b.current_price || '0').replace('$', '').replace(',', '')) || 0;
                        return priceA - priceB;
                        
                    case 'price_high':
                        const priceA2 = parseFloat(String(a.current_price || '0').replace('$', '').replace(',', '')) || 0;
                        const priceB2 = parseFloat(String(b.current_price || '0').replace('$', '').replace(',', '')) || 0;
                        return priceB2 - priceA2;
                        
                    case 'brand':
                        return (a.brand || '').localeCompare(b.brand || '');
                        
                    default:
                        return (a.name || '').localeCompare(b.name || '');
                }}
            }});
            
            displayProducts(currentProducts);
        }}
        
        function displayProducts(products) {{
            const container = document.getElementById('products-container');
            
            if (products.length === 0) {{
                container.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-light);">
                        <i class="fas fa-search" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                        <h3>没有找到匹配的产品</h3>
                        <p>尝试调整筛选条件</p>
                    </div>
                `;
                updatePagination(0);
                return;
            }}
            
            const startIndex = (currentPage - 1) * productsPerPage;
            const endIndex = startIndex + productsPerPage;
            const pageProducts = products.slice(startIndex, endIndex);
            const totalPages = Math.ceil(products.length / productsPerPage);
            
            let html = '';
            pageProducts.forEach(product => {{
                const imageUrl = product.local_image ? `images/${{product.local_image}}` : 
                                product.image_url || 'https://via.placeholder.com/300x200?text=No+Image';
                
                const priceHtml = product.current_price ? 
                    `<div class="current-price">${{product.current_price}}</div>` : 
                    `<div class="current-price">价格待定</div>`;
                
                const originalPriceHtml = product.original_price ? 
                    `<div class="original-price">${{product.original_price}}</div>` : '';
                
                const discountBadge = product.discount ? 
                    `<span class="product-badge">${{product.discount}}</span>` : '';
                
                const categoryBadge = product.category ? 
                    `<div class="product-category">${{product.category}}</div>` : '';
                
                const viewButton = product.product_url ? 
                    `<a href="${{product.product_url}}" class="view-btn" target="_blank">
                        <i class="fas fa-external-link-alt"></i> 查看详情
                    </a>` : 
                    `<button class="view-btn" disabled>
                        <i class="fas fa-ban"></i> 无链接
                    </button>`;
                
                html += `
                <div class="product-card">
                    <div class="product-image">
                        <img src="${{imageUrl}}" alt="${{product.name}}" 
                             onerror="this.src='https://via.placeholder.com/300x200?text=图片加载失败'">
                        ${{discountBadge}}
                    </div>
                    <div class="product-content">
                        <div class="product-brand">${{product.brand || '未知品牌'}}</div>
                        <h3 class="product-title">${{product.name || '未命名产品'}}</h3>
                        ${{categoryBadge}}
                        <div class="product-price">
                            ${{originalPriceHtml}}
                            ${{priceHtml}}
                        </div>
                        <div class="product-footer">
                            ${{viewButton}}
                            <small>${{product.scraped_at ? new Date(product.scraped_at).toLocaleDateString('zh-CN') : ''}}</small>
                        </div>
                    </div>
                </div>
                `;
            }});
            
            container.innerHTML = html;
            updatePagination(totalPages);
        }}
        
        function updatePagination(totalPages) {{
            const pagination = document.getElementById('pagination');
            
            if (totalPages <= 1) {{
                pagination.innerHTML = '';
                return;
            }}
            
            let html = '<div class="pagination-controls">';
            
            if (currentPage > 1) {{
                html += `<button onclick="changePage(${{currentPage - 1}})" class="pagination-btn">
                    <i class="fas fa-chevron-left"></i> 上一页
                </button>`;
            }}
            
            for (let i = 1; i <= totalPages; i++) {{
                if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {{
                    html += `<button onclick="changePage(${{i}})" class="pagination-btn ${{i === currentPage ? 'active' : ''}}">
                        ${{i}}
                    </button>`;
                }} else if (i === currentPage - 3 || i === currentPage + 3) {{
                    html += '<span class="pagination-ellipsis">...</span>';
                }}
            }}
            
            if (currentPage < totalPages) {{
                html += `<button onclick="changePage(${{currentPage + 1}})" class="pagination-btn">
                    下一页 <i class="fas fa-chevron-right"></i>
                </button>`;
            }}
            
            html += '</div>';
            pagination.innerHTML = html;
        }}
        
        function changePage(page) {{
            currentPage = page;
            displayProducts(currentProducts);
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
        
        function showNotification(message, type = 'info') {{
            const existingNotification = document.querySelector('.notification');
            if (existingNotification) {{
                existingNotification.remove();
            }}
            
            const notification = document.createElement('div');
            notification.className = `notification ${{type}}`;
            notification.innerHTML = `
                <i class="fas fa-${{type === 'success' ? 'check-circle' : 'info-circle'}}"></i>
                ${{message}}
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }}, 3000);
        }}
        
        function initCharts() {{
            const brandsData = [{brands_data_js}];
            
            const brandsCtx = document.getElementById('brandsChart').getContext('2d');
            new Chart(brandsCtx, {{
                type: 'bar',
                data: {{
                    labels: brandsData.map(item => item.brand),
                    datasets: [{{
                        label: '产品数量',
                        data: brandsData.map(item => item.count),
                        backgroundColor: 'rgba(102, 126, 234, 0.7)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{ stepSize: 1 }}
                        }}
                    }}
                }}
            }});
            
            const priceCtx = document.getElementById('priceChart').getContext('2d');
            new Chart(priceCtx, {{
                type: 'pie',
                data: {{
                    labels: ['< $500', '$500-$1000', '> $1000'],
                    datasets: [{{
                        data: [{price_stats['under_500']}, {price_stats['500_1000']}, {price_stats['over_1000']}],
                        backgroundColor: [
                            'rgba(52, 152, 219, 0.7)',
                            'rgba(46, 204, 113, 0.7)',
                            'rgba(155, 89, 182, 0.7)'
                        ],
                        borderColor: [
                            'rgba(52, 152, 219, 1)',
                            'rgba(46, 204, 113, 1)',
                            'rgba(155, 89, 182, 1)'
                        ],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            
            const themeIcon = document.querySelector('.theme-toggle i');
            themeIcon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            
            initFilters();
            initCharts();
            
            const fontAwesome = document.createElement('link');
            fontAwesome.rel = 'stylesheet';
            fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
            document.head.appendChild(fontAwesome);
        }});
    </script>
</body>
</html>'''
    
    with open('web/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    with open('web/.nojekyll', 'w') as f:
        f.write('')
    
    logger.info('生成HTML报告: web/index.html')
    return 'web/index.html'

def main():
    print("=" * 60)
    print("GitHub Pages HTML生成器")
    print("=" * 60)
    
    try:
        html_file = generate_github_pages_html()
        if html_file:
            print(f"成功生成HTML文件: {html_file}")
            print("\n生成的文件:")
            print(f"  index.html - 主页面")
            print(f"  data.json - 数据文件")
            print(f"  images/ - 图片目录")
            print(f"  .nojekyll - GitHub Pages配置")
        else:
            print("生成HTML失败")
            return 1
            
    except Exception as e:
        logger.error(f"生成HTML时出错: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())