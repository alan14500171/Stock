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
        document.querySelectorAll('[data-stock-code-control]').forEach(input => {
            this.bindStockCodeEvents(input);
            this.createUIElements(input);
        });
    }

    static clearControl(input) {
        // 清除输入值
        input.value = '';
        // 清除市场值
        const marketInput = document.getElementById('market');
        if (marketInput) {
            marketInput.value = 'HK';
        }
        // 清除选中的股票信息
        const selectedInfo = input.parentElement.querySelector('.selected-stock-info');
        if (selectedInfo) {
            selectedInfo.remove();
        }
    }

    static bindStockCodeEvents(input) {
        let currentSuggestions = [];
        let currentIndex = -1;
        let suggestionsDiv = null;

        // 创建建议列表容器
        const createSuggestionsDiv = () => {
            if (!suggestionsDiv) {
                suggestionsDiv = document.createElement('div');
                suggestionsDiv.id = 'stock_suggestions';
                suggestionsDiv.style.position = 'absolute';
                suggestionsDiv.style.width = '100%';
                suggestionsDiv.style.zIndex = '1000';
                suggestionsDiv.style.maxHeight = '200px';
                suggestionsDiv.style.overflowY = 'auto';
                input.parentElement.appendChild(suggestionsDiv);
            }
            return suggestionsDiv;
        };

        // 清除建议列表
        const clearSuggestions = () => {
            if (suggestionsDiv) {
                suggestionsDiv.innerHTML = '';
                suggestionsDiv.style.display = 'none';
            }
            currentIndex = -1;
            currentSuggestions = [];
        };

        // 处理输入事件
        let searchTimeout;
        input.addEventListener('input', async (e) => {
            clearTimeout(searchTimeout);
            const keyword = e.target.value.trim();
            
            if (keyword.length === 0) {
                this.clearControl(input);
                clearSuggestions();
                return;
            }

            searchTimeout = setTimeout(async () => {
                try {
                    const response = await fetch(`/api/stock/search?keyword=${encodeURIComponent(keyword)}`);
                    const result = await response.json();

                    if (result.success && result.data.length > 0) {
                        currentSuggestions = result.data;
                        const suggestions = createSuggestionsDiv();
                        suggestions.innerHTML = '';
                        suggestions.style.display = 'block';

                        result.data.forEach((stock, index) => {
                            const div = document.createElement('div');
                            div.className = 'suggestion-item';
                            div.innerHTML = `
                                <div>
                                    <span class="stock-code">${stock.code}</span>
                                    <span class="stock-name">${stock.name || ''}</span>
                                </div>
                                <span class="stock-market">${stock.market}</span>
                            `;
                            div.addEventListener('click', () => {
                                this.selectSuggestion(stock, input);
                                clearSuggestions();
                            });
                            suggestions.appendChild(div);
                        });
                    } else {
                        clearSuggestions();
                    }
                } catch (error) {
                    console.error('搜索股票时出错:', error);
                    clearSuggestions();
                }
            }, 300);
        });

        // 处理键盘事件
        input.addEventListener('keydown', (e) => {
            if (!suggestionsDiv || suggestionsDiv.style.display === 'none') {
                return;
            }

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    currentIndex = Math.min(currentIndex + 1, currentSuggestions.length - 1);
                    this.updateSuggestionHighlight(suggestionsDiv, currentIndex);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    currentIndex = Math.max(currentIndex - 1, -1);
                    this.updateSuggestionHighlight(suggestionsDiv, currentIndex);
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (currentIndex >= 0 && currentIndex < currentSuggestions.length) {
                        this.selectSuggestion(currentSuggestions[currentIndex], input);
                        clearSuggestions();
                    }
                    break;
                case 'Escape':
                    clearSuggestions();
                    break;
            }
        });

        // 处理失焦事件
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !suggestionsDiv?.contains(e.target)) {
                clearSuggestions();
            }
        });
    }

    static createUIElements(input) {
        // 创建选中股票信息显示区域
        const selectedInfo = document.createElement('div');
        selectedInfo.className = 'selected-stock-info d-none';
        input.parentElement.appendChild(selectedInfo);
    }

    static updateSuggestionHighlight(suggestions, currentIndex) {
        const items = suggestions.querySelectorAll('.suggestion-item');
        items.forEach((item, index) => {
            item.classList.toggle('active', index === currentIndex);
        });
    }

    static selectSuggestion(stock, input) {
        // 设置股票代码
        input.value = stock.code;
        
        // 设置市场
        const marketInput = document.getElementById('market');
        if (marketInput) {
            marketInput.value = stock.market;
        }
        
        // 更新选中的股票信息显示
        let selectedInfo = input.parentElement.querySelector('.selected-stock-info');
        if (!selectedInfo) {
            selectedInfo = document.createElement('div');
            selectedInfo.className = 'selected-stock-info';
            input.parentElement.appendChild(selectedInfo);
        }
        
        selectedInfo.innerHTML = `
            <span class="stock-market">${stock.market}</span>
            <span class="selected-stock-code">${stock.code}</span>
            <span class="selected-stock-name">${stock.name || ''}</span>
        `;
        selectedInfo.classList.remove('d-none');

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