// 股票管理模块
const StockManagement = {
    // 初始化
    init() {
        this.initElements();
        this.bindEvents();
        this.startPriceUpdates();
    },

    // 初始化元素引用
    initElements() {
        this.elements = {
            stockCodeInput: document.getElementById('stockCode'),
            submitStockBtn: document.getElementById('submitStock'),
            marketSelect: document.getElementById('marketSelect'),
            stockNameInput: document.getElementById('stockName'),
            googleCodeInput: document.getElementById('googleCode'),
            currentPriceInput: document.getElementById('currentPrice'),
            addStockForm: document.getElementById('addStockForm'),
            addStockModal: document.getElementById('addStockModal')
        };
    },

    // 绑定事件
    bindEvents() {
        let queryTimeout;
        
        // 股票代码输入事件
        this.elements.stockCodeInput.addEventListener('input', () => {
            clearTimeout(queryTimeout);
            const code = this.elements.stockCodeInput.value.trim();
            const market = this.elements.marketSelect.value;
            
            if (code) {
                queryTimeout = setTimeout(() => {
                    this.queryStockInfo(market, code);
                }, 500);
            }
        });

        // 回车键处理
        this.elements.stockCodeInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const code = this.elements.stockCodeInput.value.trim();
                if (code) {
                    this.elements.submitStockBtn.click();
                }
            }
        });

        // 市场选择变更事件
        this.elements.marketSelect.addEventListener('change', () => {
            const code = this.elements.stockCodeInput.value.trim();
            if (code) {
                this.queryStockInfo(this.elements.marketSelect.value, code);
            }
        });

        // 提交表单事件
        this.elements.submitStockBtn.addEventListener('click', () => this.submitForm());

        // 模态框关闭事件
        this.elements.addStockModal.addEventListener('hidden.bs.modal', () => this.resetForm());

        // 编辑按钮事件
        document.querySelectorAll('.edit-stock').forEach(button => {
            button.addEventListener('click', () => this.startEditing(button));
        });

        // 取消编辑事件
        document.querySelectorAll('.cancel-edit').forEach(button => {
            button.addEventListener('click', () => this.cancelEditing(button));
        });

        // 保存编辑事件
        document.querySelectorAll('.save-stock, .save-google-code').forEach(button => {
            button.addEventListener('click', () => this.saveEdit(button));
        });

        // 删除股票事件
        document.querySelectorAll('.delete-stock').forEach(button => {
            button.addEventListener('click', () => this.deleteStock(button));
        });
    },

    // 查询股票信息
    async queryStockInfo(market, code) {
        try {
            const response = await fetch(`/api/stock/info?market=${market}&code=${code}`);
            const result = await response.json();
            
            if (result.success) {
                this.elements.stockNameInput.value = result.data.name || '';
                this.elements.googleCodeInput.value = result.data.google_code || '';
                this.elements.currentPriceInput.value = result.data.current_price ? 
                    `${result.data.current_price} ${market === 'HK' ? 'HKD' : 'USD'}` : '-';
                this.elements.submitStockBtn.disabled = false;
            } else {
                this.resetStockInfo();
                this.elements.submitStockBtn.disabled = true;
            }
        } catch (error) {
            console.error('查询股票信息失败:', error);
            this.resetStockInfo();
            this.elements.submitStockBtn.disabled = true;
        }
    },

    // 提交表单
    async submitForm() {
        const currentPrice = this.elements.currentPriceInput.value;
        
        if (currentPrice === '-' || currentPrice === '查询失败' || !currentPrice) {
            alert('无法添加股票：未能获取当前股价');
            return;
        }
        
        const formData = new FormData(this.elements.addStockForm);
        
        try {
            const response = await fetch('/stocks/add', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.success) {
                location.reload();
            } else {
                alert('添加失败：' + result.error);
            }
        } catch (error) {
            alert('添加失败：' + error);
        }
    },

    // 重置表单
    resetForm() {
        this.elements.addStockForm.reset();
        this.resetStockInfo();
        this.elements.submitStockBtn.disabled = true;
    },

    // 重置股票信息
    resetStockInfo() {
        this.elements.stockNameInput.value = '';
        this.elements.googleCodeInput.value = '';
        this.elements.currentPriceInput.value = '查询失败';
    },

    // 开始编辑
    startEditing(button) {
        const row = button.closest('tr');
        row.querySelector('.stock-value').classList.add('d-none');
        row.querySelector('.stock-edit').classList.remove('d-none');
        row.querySelector('.google-code-value').classList.add('d-none');
        row.querySelector('.google-code-edit').classList.remove('d-none');
        button.classList.add('d-none');
    },

    // 取消编辑
    cancelEditing(button) {
        const row = button.closest('tr');
        row.querySelector('.stock-value').classList.remove('d-none');
        row.querySelector('.stock-edit').classList.add('d-none');
        row.querySelector('.google-code-value').classList.remove('d-none');
        row.querySelector('.google-code-edit').classList.add('d-none');
        row.querySelector('.edit-stock').classList.remove('d-none');
    },

    // 保存编辑
    async saveEdit(button) {
        const row = button.closest('tr');
        const stockId = button.dataset.id;
        const name = row.querySelector('.stock-edit input').value;
        const googleCode = row.querySelector('.google-code-edit input').value;
        
        try {
            const response = await fetch(`/stocks/edit/${stockId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `name=${encodeURIComponent(name)}&full_name=${encodeURIComponent(googleCode)}`
            });
            
            const result = await response.json();
            if (result.success) {
                location.reload();
            } else {
                alert('更新失败：' + result.error);
            }
        } catch (error) {
            alert('更新失败：' + error);
        }
    },

    // 删除股票
    async deleteStock(button) {
        if (!confirm('确定要删除这支股票吗？')) {
            return;
        }
        
        const stockId = button.dataset.id;
        
        try {
            const response = await fetch(`/stocks/delete/${stockId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            if (result.success) {
                location.reload();
            } else {
                alert('删除失败：' + result.error);
            }
        } catch (error) {
            alert('删除失败：' + error);
        }
    },

    // 开始定期更新股价
    startPriceUpdates() {
        this.updateStockPrices();
        setInterval(() => this.updateStockPrices(), 60000);
    },

    // 更新股价
    async updateStockPrices() {
        try {
            const response = await fetch('/api/stock/prices');
            const result = await response.json();
            
            if (result.success) {
                result.data.forEach(stock => {
                    const row = document.querySelector(`tr[data-code="${stock.code}"]`);
                    if (row) {
                        const priceCell = row.querySelector('.current-price');
                        priceCell.textContent = stock.current_price ? 
                            `${stock.current_price} ${stock.market === 'HK' ? 'HKD' : 'USD'}` : '-';
                    }
                });
            }
        } catch (error) {
            console.error('更新股价失败:', error);
        }
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => StockManagement.init()); 