Page({
  data: {
    stats: {
      total: 0,
      brands: 0,
      lastUpdated: ''
    },
    allProducts: [],           // 存储所有产品
    displayedProducts: [],     // 当前显示的产品
    loading: true,
    searchKeyword: '',
    filterBrand: '',
    sortBy: 'name',
    currentPage: 1,
    pageSize: 10,             // 每页显示数量
    hasMore: true
  },

  onLoad() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    this.loadMore()
  },

  // 加载数据
  loadData(callback) {
    const app = getApp()
    
    this.setData({ loading: true })
    
    wx.request({
      url: `${app.globalData.baseUrl}/web/data.json`,
      success: (res) => {
        if (res.statusCode === 200) {
          this.processData(res.data)
        }
      },
      fail: (err) => {
        console.error('数据加载失败:', err)
        wx.showToast({
          title: '数据加载失败',
          icon: 'none'
        })
      },
      complete: () => {
        this.setData({ loading: false })
        callback && callback()
      }
    })
  },

  // 处理数据
  processData(data) {
    const products = data.products || []
    const metadata = data.metadata || {}
    
    this.setData({
      stats: {
        total: metadata.total_products || products.length,
        brands: metadata.unique_brands || new Set(products.map(p => p.brand)).size,
        lastUpdated: metadata.last_updated || '未知'
      },
      allProducts: products.map(p => ({
        id: p.id,
        brand: p.brand,
        name: p.name,
        current_price: p.current_price,
        original_price: p.original_price,
        discount: p.discount,
        category: p.category,
        image: p.local_image ? 
          `${getApp().globalData.baseUrl}/web/images/${p.local_image}` : 
          p.image_url,
        product_url: p.product_url
      })),
      displayedProducts: products.slice(0, this.data.pageSize),
      hasMore: products.length > this.data.pageSize
    })
  },

  // 加载更多
  loadMore() {
    if (this.data.loading || !this.data.hasMore) return
    
    const startIndex = this.data.currentPage * this.data.pageSize
    const endIndex = startIndex + this.data.pageSize
    const moreProducts = this.data.allProducts.slice(startIndex, endIndex)
    
    if (moreProducts.length > 0) {
      this.setData({
        displayedProducts: [...this.data.displayedProducts, ...moreProducts],
        currentPage: this.data.currentPage + 1,
        hasMore: endIndex < this.data.allProducts.length
      })
    } else {
      this.setData({ hasMore: false })
    }
  },

  // 搜索功能
  onSearchInput(e) {
    const keyword = e.detail.value.toLowerCase()
    this.setData({ searchKeyword: keyword })
    this.filterProducts()
  },

  // 品牌筛选
  onBrandFilter(e) {
    this.setData({ filterBrand: e.detail.value })
    this.filterProducts()
  },

  // 排序
  onSortChange(e) {
    this.setData({ sortBy: e.detail.value })
    this.sortProducts()
  },

  // 筛选产品
  filterProducts() {
    let filtered = this.data.allProducts
    
    // 关键词搜索
    if (this.data.searchKeyword) {
      filtered = filtered.filter(item => 
        item.name.toLowerCase().includes(this.data.searchKeyword) || 
        item.brand.toLowerCase().includes(this.data.searchKeyword)
      )
    }
    
    // 品牌筛选
    if (this.data.filterBrand) {
      filtered = filtered.filter(item => item.brand === this.data.filterBrand)
    }
    
    this.setData({
      displayedProducts: filtered.slice(0, this.data.pageSize),
      currentPage: 1,
      hasMore: filtered.length > this.data.pageSize
    })
  },

  // 排序产品
  sortProducts() {
    const sorted = [...this.data.displayedProducts]
    
    switch(this.data.sortBy) {
      case 'price_low':
        sorted.sort((a, b) => {
          const priceA = parseFloat(a.current_price?.replace('$', '') || 0)
          const priceB = parseFloat(b.current_price?.replace('$', '') || 0)
          return priceA - priceB
        })
        break
      case 'price_high':
        sorted.sort((a, b) => {
          const priceA = parseFloat(a.current_price?.replace('$', '') || 0)
          const priceB = parseFloat(b.current_price?.replace('$', '') || 0)
          return priceB - priceA
        })
        break
      case 'brand':
        sorted.sort((a, b) => a.brand.localeCompare(b.brand))
        break
      default: // name
        sorted.sort((a, b) => a.name.localeCompare(b.name))
    }
    
    this.setData({ displayedProducts: sorted })
  },

  // 查看产品详情
  viewProduct(e) {
    const product = e.currentTarget.dataset.product
    if (product.product_url) {
      wx.setClipboardData({
        data: product.product_url,
        success: () => {
          wx.showToast({
            title: '链接已复制',
            icon: 'success'
          })
        }
      })
    }
  },

  // 复制价格信息
  copyPriceInfo(e) {
    const product = e.currentTarget.dataset.product
    const priceInfo = `${product.brand} ${product.name} - ${product.current_price}`
    
    wx.setClipboardData({
      data: priceInfo,
      success: () => {
        wx.showToast({
          title: '价格信息已复制',
          icon: 'success'
        })
      }
    })
  }
})