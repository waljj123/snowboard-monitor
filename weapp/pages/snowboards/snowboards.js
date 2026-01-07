Page({
  data: {
    snowboards: [],
    loading: true,
    searchKeyword: '',
    filterBrand: '',
    sortBy: 'name'
  },

  onLoad(options) {
    console.log('雪板列表页面加载', options)
    this.loadSnowboardData()
  },

  onPullDownRefresh() {
    this.loadSnowboardData(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 加载雪板数据
  loadSnowboardData(callback) {
    const app = getApp()
    
    this.setData({ loading: true })
    
    wx.request({
      url: `${app.globalData.baseUrl}/web/data.json`,
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({
            snowboards: res.data.products || [],
            loading: false
          })
        }
      },
      fail: (err) => {
        console.error('数据加载失败:', err)
        this.setData({ loading: false })
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

  // 搜索功能
  onSearchInput(e) {
    const keyword = e.detail.value.toLowerCase()
    this.setData({ searchKeyword: keyword })
  },

  // 品牌筛选
  onBrandFilter(e) {
    this.setData({ filterBrand: e.detail.value })
  },

  // 排序
  onSortChange(e) {
    this.setData({ sortBy: e.detail.value })
  },

  // 查看产品详情
  viewProductDetail(e) {
    const product = e.currentTarget.dataset.product
    wx.navigateTo({
      url: `/pages/detail/detail?id=${product.id}`
    })
  },

  // 复制产品链接
  copyProductLink(e) {
    const url = e.currentTarget.dataset.url
    if (url) {
      wx.setClipboardData({
        data: url,
        success: () => {
          wx.showToast({
            title: '链接已复制',
            icon: 'success'
          })
        }
      })
    }
  }
})