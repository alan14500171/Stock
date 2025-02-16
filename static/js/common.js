/**
 * 通用工具类
 */
const CommonUtils = {
    // 市场选项配置
    MARKETS: {
        'HK': 'HK',
        'USA': 'USA'
    },

    /**
     * 初始化日期输入字段
     * @param {string} selector - 日期输入字段的选择器
     */
    initDateInputs: function(selector = 'input[name*="date"]') {
        document.querySelectorAll(selector).forEach(input => {
            // 将type从date改为text
            input.type = 'text';
            input.placeholder = 'YYYY-MM-DD';
            input.pattern = '\\d{4}-\\d{2}-\\d{2}';
            
            // 设置默认值为当天
            if (!input.value) {
                const today = new Date();
                const year = today.getFullYear();
                const month = String(today.getMonth() + 1).padStart(2, '0');
                const day = String(today.getDate()).padStart(2, '0');
                input.value = `${year}-${month}-${day}`;
            }

            // 处理日期输入
            const handleDateInput = (value) => {
                value = value.replace(/[^0-9]/g, '');
                let formattedDate = '';
                const today = new Date();
                const currentYear = today.getFullYear();
                const currentMonth = today.getMonth() + 1;

                try {
                    if (value.length === 8) {
                        // YYYYMMDD
                        const year = value.substring(0, 4);
                        const month = value.substring(4, 6);
                        const day = value.substring(6, 8);
                        formattedDate = `${year}-${month}-${day}`;
                    } else if (value.length === 4) {
                        // MMDD
                        const month = value.substring(0, 2);
                        const day = value.substring(2, 4);
                        formattedDate = `${currentYear}-${month}-${day}`;
                    } else if (value.length === 3) {
                        // MDD
                        const month = value.substring(0, 1).padStart(2, '0');
                        const day = value.substring(1, 3).padStart(2, '0');
                        formattedDate = `${currentYear}-${month}-${day}`;
                    } else if (value.length === 2) {
                        // DD
                        const day = value.padStart(2, '0');
                        formattedDate = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${day}`;
                    } else {
                        return null;
                    }

                    // 验证日期是否有效
                    const date = new Date(formattedDate);
                    if (isNaN(date.getTime())) {
                        return null;
                    }

                    return formattedDate;
                } catch (e) {
                    return null;
                }
            };

            // 处理日期格式化
            const formatDate = function() {
                const value = this.value;
                if (value) {
                    const formattedDate = handleDateInput(value);
                    if (formattedDate) {
                        this.value = formattedDate;
                    } else {
                        this.value = '';
                        alert('请输入有效的日期格式：YYYYMMDD、MMDD、MDD 或 DD');
                    }
                }
            };

            // 按回车键时格式化
            input.addEventListener('keydown', function(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    formatDate.call(this);
                }
            });

            // 失焦时格式化
            input.addEventListener('blur', formatDate);
        });
    },

    /**
     * 初始化市场选择下拉框
     * @param {string} selector - 市场选择下拉框的选择器
     * @param {boolean} showEmpty - 是否显示空选项
     */
    initMarketSelects: function(selector = 'select[name="market"]', showEmpty = true) {
        document.querySelectorAll(selector).forEach(select => {
            // 保存当前选中的值
            const currentValue = select.value;
            
            // 清空现有选项
            select.innerHTML = '';
            
            // 添加空选项
            if (showEmpty) {
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = '--';
                select.appendChild(defaultOption);
            }
            
            // 添加市场选项
            Object.entries(this.MARKETS).forEach(([value, text]) => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = text;
                // 如果与当前选中值相同，则设置为选中状态
                if (value === currentValue) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        });
    },

    /**
     * 获取市场名称
     * @param {string} market - 市场代码
     * @returns {string} 市场名称
     */
    getMarketName: function(market) {
        return this.MARKETS[market] || market;
    }
};

// 在页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    CommonUtils.initDateInputs();
    CommonUtils.initMarketSelects();
}); 