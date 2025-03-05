#!/usr/bin/env node
/**
 * run-vite.js - 独立vite执行脚本
 * 
 * 此脚本用于解决群辉NAS环境中的XSym符号链接问题
 * 它提供了crypto polyfill并直接调用vite.js
 */

// 添加crypto polyfill
global.crypto = {
  getRandomValues: function(arr) {
    console.log("使用自定义getRandomValues函数");
    for (let i = 0; i < arr.length; i++) {
      arr[i] = Math.floor(Math.random() * 256);
    }
    return arr;
  }
};

// 设置环境变量
process.env.NODE_ENV = process.env.NODE_ENV || 'production';

// 捕获并处理可能的错误
try {
  console.log("正在加载vite...");
  
  // 直接调用vite.js，而不是通过符号链接
  require('./node_modules/vite/bin/vite.js');
  
} catch (error) {
  console.error("执行vite时发生错误:");
  console.error(error);
  process.exit(1);
} 