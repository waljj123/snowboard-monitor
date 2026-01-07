// weapp/utils/api.js
const API_BASE = 'https://yourusername.github.io/snowboard-monitor/data'

class SnowboardAPI {
  // 获取雪板数据
  static async getSnowboards() {
    try {
      const response = await fetch(`${API_BASE}/snowboards.json?t=${Date.now()}`)
      const data = await response.json()
      return data
    } catch (error) {
      console.error('API请求失败:', error)
      // 降级到本地缓存
      return this.getCachedData()
    }
  }

  // 本地缓存
  static getCachedData() {
    return new Promise((resolve) => {
      wx.getStorage({
        key: 'snowboards_data',
        success: (res) => resolve(res.data),
        fail: () => resolve({ products: [], last_updated: null })
      })
    })
  }

  // 保存到缓存
  static cacheData(data) {
    wx.setStorage({
      key: 'snowboards_data',
      data: data
    })
  }
}

module.exports = SnowboardAPI