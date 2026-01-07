Page({
  onLoad() {
    // 自动跳转回首页
    wx.switchTab({
      url: '/pages/index/index'
    })
  }
})