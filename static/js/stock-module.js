// 股票管理模块
const StockModule = {
    // 标记是否已初始化
    initialized: false,
    modalInstance: null,
    onSuccess: null,

    // 初始化模态框
    init() {
        // 确保只初始化一次
        if (this.initialized) {
            return this;
        }

        // 创建新的模态框
        this.createModal();
        this.bindEvents();
        
        this.initialized = true;
        return this;
    },

    // 清理函数
    cleanup() {
        const existingModal = document.getElementById('stockManagementModal');
        if (existingModal) {
            existingModal.remove();
        }
        // 重置初始化状态
        this.initialized = false;
        this.modalInstance = null;
    },

    // 创建模态框
    createModal() {
        const modalHtml = `
        <div class="modal fade" id="stockManagementModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">添加新股票</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="stockManagementForm">
                            <div class="mb-3">
                                <label class="form-label">市场</label>
                                <select class="form-select" name="market" id="stockManagementMarket" required>
                                    <option value="HK">HK</option>
                                    <option value="USA">USA</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">股票代码</label>
                                <input type="text" class="form-control" name="code" id="stockManagementCode" required>
                                <div class="form-text">输入股票代码后将自动查询股票信息</div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">股票名称</label>
                                <input type="text" class="form-control" name="name" id="stockManagementName" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">谷歌查询代码</label>
                                <input type="text" class="form-control" name="full_name" id="stockManagementGoogleCode" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">当前股价</label>
                                <input type="text" class="form-control" id="stockManagementPrice" readonly disabled>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="stockManagementSubmit">确认添加</button>
                    </div>
                </div>
            </div>
        </div>`;

        // 移除可能存在的旧模态框
        const existingModal = document.getElementById('stockManagementModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新模态框到body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    },

    // 绑定事件
    bindEvents() {
        const modal = document.getElementById('stockManagementModal');
        const form = document.getElementById('stockManagementForm');
        const codeInput = document.getElementById('stockManagementCode');
        const marketSelect = document.getElementById('stockManagementMarket');
        let queryTimeout;

        // 初始化Bootstrap模态框
        this.modalInstance = new bootstrap.Modal(modal, {
            keyboard: false,
            backdrop: 'static'
        });

        // 股票代码输入事件
        codeInput.addEventListener('input', () => {
            clearTimeout(queryTimeout);
            const code = codeInput.value.trim();
            const market = marketSelect.value;
            
            if (code) {
                queryTimeout = setTimeout(() => {
                    this.queryStockInfo(market, code);
                }, 500);
            }
        });

        // 市场选择变更事件
        marketSelect.addEventListener('change', () => {
            const code = codeInput.value.trim();
            if (code) {
                this.queryStockInfo(marketSelect.value, code);
            }
        });

        // 提交表单事件
        document.getElementById('stockManagementSubmit').addEventListener('click', () => {
            this.submitForm();
        });

        // 模态框关闭事件
        modal.addEventListener('hidden.bs.modal', () => {
            form.reset();
            document.getElementById('stockManagementPrice').value = '';
            document.getElementById('stockManagementName').value = '';
            document.getElementById('stockManagementGoogleCode').value = '';
            // 重置初始化状态，确保下次打开时重新初始化
            this.cleanup();
        });
    },

    // 查询股票信息
    async queryStockInfo(market, code) {
        try {
            // 显示加载状态
            document.getElementById('stockManagementPrice').value = '查询中...';
            document.getElementById('stockManagementName').value = '查询中...';
            document.getElementById('stockManagementGoogleCode').value = '查询中...';
            document.getElementById('stockManagementSubmit').disabled = true;
            
            const response = await fetch(`/api/stock/info?market=${market}&code=${code}`);
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('stockManagementName').value = result.data.name || '';
                document.getElementById('stockManagementGoogleCode').value = result.data.google_code || '';
                document.getElementById('stockManagementPrice').value = result.data.current_price ? 
                    `${result.data.current_price} ${market === 'HK' ? 'HKD' : 'USD'}` : '暂无数据';
                document.getElementById('stockManagementSubmit').disabled = false;
            } else {
                this.resetStockInfo('查询失败，请检查股票代码是否正确');
                document.getElementById('stockManagementSubmit').disabled = true;
            }
        } catch (error) {
            console.error('查询股票信息失败:', error);
            this.resetStockInfo('查询失败，请稍后重试');
            document.getElementById('stockManagementSubmit').disabled = true;
        }
    },

    // 重置股票信息
    resetStockInfo(message = '查询失败') {
        document.getElementById('stockManagementName').value = '';
        document.getElementById('stockManagementGoogleCode').value = '';
        document.getElementById('stockManagementPrice').value = message;
    },

    // 提交表单
    async submitForm() {
        const form = document.getElementById('stockManagementForm');
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/stocks/add', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });
            
            const result = await response.json();
            if (result.success) {
                // 关闭模态框
                this.modalInstance.hide();
                
                // 触发成功回调
                if (this.onSuccess) {
                    this.onSuccess({
                        code: formData.get('code'),
                        market: formData.get('market'),
                        name: formData.get('name')
                    });
                }
            } else {
                alert('添加失败：' + result.error);
            }
        } catch (error) {
            alert('添加失败：' + error);
        }
    },

    // 打开添加股票模态框
    open(market = 'HK', code = '', onSuccess = null) {
        this.onSuccess = onSuccess;
        
        // 确保模态框已初始化
        this.init();
        
        // 设置初始值
        document.getElementById('stockManagementMarket').value = market;
        document.getElementById('stockManagementCode').value = code;
        
        if (code) {
            this.queryStockInfo(market, code);
        }
        
        // 显示模态框
        if (this.modalInstance) {
            this.modalInstance.show();
        } else {
            console.error('Modal instance not initialized');
        }
    }
};

// 导出模块
window.StockModule = StockModule;

// 添加主界面的股票代码查询功能
class StockCodeControl {
    static init() {
        // 查找所有需要绑定股票查询功能的输入框
        document.querySelectorAll('input[data-stock-code-control]').forEach(input => {
            this.bindStockCodeEvents(input);
        });
    }

    static bindStockCodeEvents(input) {
        // 创建必要的DOM元素
        this.createUIElements(input);

        let searchTimeout;
        let currentSuggestionIndex = -1;
        const suggestionsContainer = input.parentElement.querySelector('.stock-suggestions');
        const searchSpinner = input.parentElement.querySelector('.search-spinner');

        // 处理输入事件
        input.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            currentSuggestionIndex = -1;
            const code = e.target.value.trim();
            
            if (!code) {
                suggestionsContainer.classList.add('d-none');
                return;
            }
            
            // 显示加载状态
            searchSpinner.classList.remove('d-none');
            
            searchTimeout = setTimeout(async () => {
                try {
                    // 从数据库中搜索股票
                    const response = await fetch(`/api/stock/search?keyword=${code}`);
                    const result = await response.json();
                    
                    if (result.success && result.data.length > 0) {
                        // 显示建议列表
                        suggestionsContainer.innerHTML = result.data.map(stock => `
                            <div class="suggestion-item" data-code="${stock.code}" data-market="${stock.market}" data-name="${stock.name}">
                                <div>
                                    <span class="stock-code">${stock.code}</span>
                                    <span class="stock-name">${stock.name}</span>
                                </div>
                                <span class="stock-market">${stock.market}</span>
                            </div>
                        `).join('');
                        
                        suggestionsContainer.classList.remove('d-none');
                        
                        // 绑定建议项点击事件
                        suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
                            item.addEventListener('click', () => this.selectSuggestion(item, input));
                        });
                    } else {
                        suggestionsContainer.classList.add('d-none');
                    }
                } catch (error) {
                    console.error('搜索股票失败:', error);
                    suggestionsContainer.classList.add('d-none');
                } finally {
                    searchSpinner.classList.add('d-none');
                }
            }, 300);
        });

        // 键盘导航处理
        input.addEventListener('keydown', (e) => {
            const suggestions = suggestionsContainer.querySelectorAll('.suggestion-item');
            
            if (suggestions.length === 0 || suggestionsContainer.classList.contains('d-none')) {
                return;
            }
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    currentSuggestionIndex = Math.min(currentSuggestionIndex + 1, suggestions.length - 1);
                    this.updateSuggestionHighlight(suggestions, currentSuggestionIndex);
                    break;
                    
                case 'ArrowUp':
                    e.preventDefault();
                    currentSuggestionIndex = Math.max(currentSuggestionIndex - 1, 0);
                    this.updateSuggestionHighlight(suggestions, currentSuggestionIndex);
                    break;
                    
                case 'Enter':
                    e.preventDefault();
                    if (currentSuggestionIndex >= 0 && currentSuggestionIndex < suggestions.length) {
                        this.selectSuggestion(suggestions[currentSuggestionIndex], input);
                    }
                    break;
                    
                case 'Escape':
                    e.preventDefault();
                    suggestionsContainer.classList.add('d-none');
                    currentSuggestionIndex = -1;
                    break;
            }
        });

        // 处理失焦事件
        input.addEventListener('blur', async () => {
            const code = input.value.trim();
            if (!code) return;

            const marketInput = input.closest('form').querySelector('input[name="market"]');
            const market = marketInput ? marketInput.value : 'HK';
            
            try {
                // 先从数据库中查询股票是否存在
                const searchResponse = await fetch(`/api/stock/search?keyword=${code}`);
                const searchResult = await searchResponse.json();
                
                if (!searchResult.success || searchResult.data.length === 0) {
                    console.log('股票不存在，打开添加模态框');
                    // 确保StockModule已经初始化
                    if (!window.StockModule) {
                        console.error('StockModule not found');
                        return;
                    }
                    
                    // 打开添加模态框，并在模态框中查询股票信息
                    window.StockModule.open(market, code, (newStock) => {
                        if (newStock) {
                            console.log('股票添加成功，更新输入框', newStock);
                            // 更新输入框的值
                            input.value = newStock.code;
                            
                            // 更新市场选择框
                            if (marketInput) {
                                marketInput.value = newStock.market;
                            }

                            // 更新选中的股票信息
                            const stockInfoDiv = input.parentElement.querySelector('.selected-stock-info');
                            if (stockInfoDiv) {
                                stockInfoDiv.classList.remove('d-none');
                                stockInfoDiv.querySelector('.selected-stock-code').textContent = newStock.code;
                                stockInfoDiv.querySelector('.selected-stock-name').textContent = newStock.name;
                            }

                            // 将焦点移动到下一个输入框
                            const nextInput = input.closest('form').querySelector('#transaction_code');
                            if (nextInput) {
                                nextInput.focus();
                            }
                        }
                    });
                } else {
                    // 股票已存在，显示股票信息
                    const stock = searchResult.data[0];
                    const stockInfoDiv = input.parentElement.querySelector('.selected-stock-info');
                    if (stockInfoDiv) {
                        stockInfoDiv.classList.remove('d-none');
                        stockInfoDiv.querySelector('.selected-stock-code').textContent = stock.code;
                        stockInfoDiv.querySelector('.selected-stock-name').textContent = stock.name;
                    }
                }
            } catch (error) {
                console.error('查询股票信息失败:', error);
            }
        });

        // 点击其他地方时隐藏建议列表
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                suggestionsContainer.classList.add('d-none');
                currentSuggestionIndex = -1;
            }
        });
    }

    static createUIElements(input) {
        const container = input.parentElement;
        
        // 创建建议列表容器
        if (!container.querySelector('.stock-suggestions')) {
            const suggestionsDiv = document.createElement('div');
            suggestionsDiv.className = 'stock-suggestions position-absolute w-100 mt-1 d-none';
            suggestionsDiv.style.cssText = 'z-index: 1000; max-height: 200px; overflow-y: auto; background: white; border: 1px solid #ced4da; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);';
            container.appendChild(suggestionsDiv);
        }
        
        // 创建加载动画
        if (!container.querySelector('.search-spinner')) {
            const spinnerDiv = document.createElement('div');
            spinnerDiv.className = 'search-spinner spinner-border spinner-border-sm text-primary position-absolute d-none';
            spinnerDiv.style.cssText = 'right: 10px; top: 10px;';
            spinnerDiv.innerHTML = '<span class="visually-hidden">搜索中...</span>';
            container.appendChild(spinnerDiv);
        }
        
        // 创建选中股票信息显示区域
        if (!container.querySelector('.selected-stock-info')) {
            const stockInfoDiv = document.createElement('div');
            stockInfoDiv.className = 'selected-stock-info position-absolute d-none';
            stockInfoDiv.style.cssText = 'right: 10px; top: 50%; transform: translateY(-50%); font-size: 0.9em; padding-right: 25px;';
            stockInfoDiv.innerHTML = `
                <span class="selected-stock-code"></span>
                <span class="selected-stock-name text-muted" style="margin-left: 8px;"></span>
            `;
            container.appendChild(stockInfoDiv);
        }
    }

    static updateSuggestionHighlight(suggestions, currentIndex) {
        suggestions.forEach((item, index) => {
            if (index === currentIndex) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    static selectSuggestion(item, input) {
        const selectedCode = item.dataset.code;
        const selectedMarket = item.dataset.market;
        const selectedName = item.dataset.name;
        
        // 设置选中的值
        input.value = selectedCode;
        const marketInput = input.closest('form').querySelector('input[name="market"]');
        if (marketInput) {
            marketInput.value = selectedMarket;
        }
        
        // 显示选中的股票信息
        const stockInfo = input.parentElement.querySelector('.selected-stock-info');
        if (stockInfo) {
            stockInfo.classList.remove('d-none');
            stockInfo.querySelector('.selected-stock-code').textContent = selectedCode;
            stockInfo.querySelector('.selected-stock-name').textContent = selectedName;
        }
        
        // 隐藏建议列表
        const suggestionsContainer = input.parentElement.querySelector('.stock-suggestions');
        if (suggestionsContainer) {
            suggestionsContainer.classList.add('d-none');
        }
        
        // 将焦点移动到下一个输入框
        const nextInput = input.closest('form').querySelector('#transaction_code');
        if (nextInput) {
            nextInput.focus();
        }
    }
}

// 页面加载完成后初始化股票代码控件
document.addEventListener('DOMContentLoaded', () => {
    StockCodeControl.init();
}); 