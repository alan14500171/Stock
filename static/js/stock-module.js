// 股票管理模块
const StockModule = {
    // 标记是否已初始化
    initialized: false,
    modalInstance: null,
    onSuccess: null,

    // 初始化模态框
    init() {
        if (this.initialized) {
            return this;
        }

        // 移除可能存在的旧模态框和事件监听器
        this.cleanup();
        
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
            // 如果存在 Bootstrap 模态框实例，先销毁它
            const bsModal = bootstrap.Modal.getInstance(existingModal);
            if (bsModal) {
                bsModal.dispose();
            }
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
                                <select class="form-select" name="market" id="stockMarket" required>
                                    <option value="HK">HK</option>
                                    <option value="USA">USA</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">股票代码</label>
                                <input type="text" class="form-control" name="code" id="stockCode" required>
                                <div class="form-text">输入股票代码后将自动查询股票信息</div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">股票名称</label>
                                <input type="text" class="form-control" name="name" id="stockName" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">谷歌查询代码</label>
                                <input type="text" class="form-control" name="full_name" id="googleCode" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">当前股价</label>
                                <input type="text" class="form-control" id="currentPrice" readonly disabled>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="submitStock">确认添加</button>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
    },

    // 绑定事件
    bindEvents() {
        const modal = document.getElementById('stockManagementModal');
        const form = document.getElementById('stockManagementForm');
        const codeInput = document.getElementById('stockCode');
        const marketSelect = document.getElementById('stockMarket');
        let queryTimeout;

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
        document.getElementById('submitStock').addEventListener('click', () => {
            this.submitForm();
        });

        // 模态框关闭事件
        modal.addEventListener('hidden.bs.modal', () => {
            form.reset();
            document.getElementById('currentPrice').value = '';
            document.getElementById('stockName').value = '';
            document.getElementById('googleCode').value = '';
            // 重置初始化状态，确保下次打开时重新初始化
            this.cleanup();
        });

        // 创建 Bootstrap 模态框实例
        this.modalInstance = new bootstrap.Modal(modal);
    },

    // 查询股票信息
    async queryStockInfo(market, code) {
        try {
            // 显示加载状态
            document.getElementById('currentPrice').value = '查询中...';
            
            const response = await fetch(`/api/stock/info?market=${market}&code=${code}`);
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('stockName').value = result.data.name || '';
                document.getElementById('googleCode').value = result.data.google_code || '';
                document.getElementById('currentPrice').value = result.data.current_price ? 
                    `${result.data.current_price} ${market === 'HK' ? 'HKD' : 'USD'}` : '暂无数据';
                document.getElementById('submitStock').disabled = false;
            } else {
                this.resetStockInfo();
                document.getElementById('submitStock').disabled = true;
            }
        } catch (error) {
            console.error('查询股票信息失败:', error);
            this.resetStockInfo();
            document.getElementById('submitStock').disabled = true;
        }
    },

    // 重置股票信息
    resetStockInfo() {
        document.getElementById('stockName').value = '';
        document.getElementById('googleCode').value = '';
        document.getElementById('currentPrice').value = '查询失败';
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
                // 设置主界面的市场和股票代码
                document.getElementById('market').value = formData.get('market');
                document.getElementById('stock_code').value = formData.get('code');
                
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
        
        // 每次打开都重新初始化
        this.init();
        
        const modal = document.getElementById('stockManagementModal');
        if (!modal) {
            console.error('Modal element not found');
            return;
        }

        // 设置初始值
        document.getElementById('stockMarket').value = market;
        document.getElementById('stockCode').value = code;
        
        if (code) {
            this.queryStockInfo(market, code);
        }
        
        // 显示模态框
        this.modalInstance.show();
    }
};

// 导出模块
window.StockModule = StockModule;

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', () => {
    StockModule.init();
}); 