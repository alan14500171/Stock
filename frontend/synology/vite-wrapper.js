/**
 * vite-wrapper.js - Vite构建包装器
 * 
 * 为Vite提供必要的全局对象和polyfill，
 * 解决群辉NAS环境中的构建问题
 */

// 加载crypto修复
require('./crypto-fix.js');

// 确保全局对象存在
if (typeof global === 'undefined') {
  global = typeof window !== 'undefined' ? window : {};
}

// 确保process.env存在
if (!global.process) {
  global.process = { env: {} };
}

// 设置Node环境
global.process.env.NODE_ENV = 'production';

// 使用基于命令行参数的方式运行vite
const { execSync } = require('child_process');
const args = process.argv.slice(2).join(' ');

try {
  // 输出构建信息
  console.log('\n===== 开始使用自定义wrapper构建 =====');
  console.log(`执行命令: vite ${args}`);
  
  // 使用相对路径执行vite命令
  require('../node_modules/vite/bin/vite.js');
  
  console.log('===== 构建成功完成 =====\n');
} catch (error) {
  console.error('===== 构建过程中发生错误 =====');
  console.error(error);
  console.error('================================\n');
  process.exit(1);
} 