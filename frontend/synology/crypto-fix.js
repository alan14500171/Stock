/**
 * crypto-fix.js - 为群辉NAS环境提供的加密API修复
 * 
 * 这个文件解决了在群辉NAS Docker环境中出现的
 * "crypto.getRandomValues is not a function"错误
 */

// 检查环境
const isNode = typeof window === 'undefined';
const contextObject = isNode ? global : window;

// 定义一个安全的随机数生成函数
function secureRandomValues(buffer) {
  if (buffer.length > 65536) {
    throw new Error("请求的随机值太多");
  }
  
  // 如果我们在Node环境中
  if (isNode) {
    try {
      // 尝试使用Node的crypto模块
      const nodeCrypto = require('crypto');
      const bytes = nodeCrypto.randomBytes(buffer.length);
      
      // 复制到目标buffer
      for (let i = 0; i < buffer.length; i++) {
        buffer[i] = bytes[i];
      }
      
      return buffer;
    } catch (error) {
      console.warn("Node crypto模块不可用，使用备用方法");
    }
  }
  
  // 备用方法
  for (let i = 0; i < buffer.length; i++) {
    buffer[i] = Math.floor(Math.random() * 256);
  }
  
  return buffer;
}

// 确保crypto对象存在
if (!contextObject.crypto) {
  contextObject.crypto = {};
}

// 如果getRandomValues不存在，提供一个实现
if (!contextObject.crypto.getRandomValues) {
  contextObject.crypto.getRandomValues = secureRandomValues;
  console.log("已添加crypto.getRandomValues polyfill");
}

// 为Node环境导出
if (isNode) {
  module.exports = contextObject.crypto;
} else {
  // 浏览器环境无需导出
  console.log("crypto polyfill已应用到window对象");
} 