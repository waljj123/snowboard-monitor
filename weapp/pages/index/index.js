Page({
  data: {
    stats: {
      total: 0,
      brands: 0,
      updated: '--'
    },
    latestProducts: []
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
        wx.showToast({
          title: '数据加载失败',
          icon: 'none'
        })
      },
      complete: () => {
        callback && callback()
      }
    })
  },

  // 处理数据
  processData(data) {
    const products = data.products || []
    const metadata = data.metadata || {}
    
    // 更新统计信息
    this.setData({
      stats: {
        total: metadata.total_products || products.length,
        brands: metadata.unique_brands || new Set(products.map(p => p.brand)).size,
        updated: metadata.last_updated ? metadata.last_updated.split(' ')[1] : '--'
      },
      latestProducts: products.slice(0, 6).map(p => ({
        id: p.id,
        brand: p.brand,
        name: p.name,
        image: p.local_image ? `${getApp().globalData.baseUrl}/web/images/${p.local_image}` : p.image_url
      }))
    })
  },

  // 页面跳转
  goToSnowboards() {
    wx.navigateTo({
      url: '/pages/snowboards/snowboards'
    })
  },

  searchDiscount() {
    wx.navigateTo({
      url: '/pages/snowboards/snowboards?filter=discount'
    })
  },

  viewFavorites() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  },

  viewProduct(e) {
    const product = e.currentTarget.dataset.product
    wx.navigateTo({
      url: `/pages/detail/detail?id=${product.id}`
    })
  }
})