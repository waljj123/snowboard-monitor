# README.md
# 🏂 雪板价格监控系统

基于GitHub Actions的自动化雪板价格监控系统，每日自动更新数据并部署到GitHub Pages。

## ✨ 功能特性

- 🤖 **自动爬取**: 每日自动爬取snowboards.com的最新雪板数据
- 🌐 **静态部署**: 自动生成HTML页面并部署到GitHub Pages
- 📱 **小程序支持**: 提供微信小程序接口
- 💰 **价格监控**: 实时追踪价格变化和折扣信息

## 🚀 快速开始

### 本地开发
bash

git clone https://github.com/yourusername/snowboard-monitor.git

cd snowboard-monitor

pip install -r requirements.txt

python src/scraper.py

### 访问页面
- Web页面: https://yourusername.github.io/snowboard-monitor
- 数据API: https://yourusername.github.io/snowboard-monitor/data/snowboards.json

## ⏰ 自动化流程

1. **每日02:00 (UTC)**: 自动运行爬虫脚本
2. **数据更新**: 爬取最新雪板价格信息
3. **静态生成**: 生成更新的HTML页面
4. **自动部署**: 部署到GitHub Pages
5. **小程序同步**: 微信小程序自动获取最新数据

## 📊 项目结构
(同上文项目结构)