Page({
  data: {
    stats: {
      total: 0,
      brands: 0,
      lastUpdated: ''
    },
    latestProducts: [],
    loading: true
  },

  onLoad() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 加载数据
  loadData(callback) {
    const app = getApp()
    
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
      latestProducts: products.slice(0, 6).map(p => ({
        id: p.id,
        brand: p.brand,
        name: p.name,
        current_price: p.current_price,
        image: p.local_image ? 
          `${getApp().globalData.baseUrl}/web/images/${p.local_image}` : 
          p.image_url
      }))
    })
  },

  // 跳转到雪板列表
  goToSnowboards() {
    wx.navigateTo({
      url: '/pages/snowboards/snowboards'
    })
  },

  // 查看产品详情
  viewProduct(e) {
    const product = e.currentTarget.dataset.product
    wx.navigateTo({
      url: `/pages/detail/detail?id=${product.id}`
    })
  }
})