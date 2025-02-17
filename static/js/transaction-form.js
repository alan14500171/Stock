// 交易表单控制模块
const TransactionForm = {
    // 初始化
    init() {
        // 如果没有成交明细行，添加第一行
        if (document.querySelectorAll('.trade-detail').length === 0) {
            this.addTradeDetail();
        }
        this.bindKeyboardNavigation();
        this.initFormValidation();
        this.initDateHandling();
        this.initDepositFeeAutoSave();  // 添加存入证券费自动保存初始化
    },

    // 初始化日期处理
    initDateHandling() {
        const dateInput = document.getElementById('transaction_date');
        if (!dateInput) return;

        // 设置默认日期
        if (!dateInput.value) {
            this.setDefaultDate();
        }

        // 绑定日期输入处理
        dateInput.addEventListener('input', this.handleDateInput);
    },

    // 设置默认日期
    setDefaultDate() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        document.getElementById('transaction_date').value = `${year}-${month}-${day}`;
    },

    // 处理日期输入
    handleDateInput(event) {
        const input = event.target;
        const value = input.value;
        
        // 处理快速输入，例如: 20250103 => 2025-01-03
        if (value.length === 8 && !value.includes('-')) {
            const year = value.substring(0, 4);
            const month = value.substring(4, 6);
            const day = value.substring(6, 8);
            input.value = `${year}-${month}-${day}`;
        }
    },

    // 添加成交明细行
    addTradeDetail() {
        const container = document.getElementById('trade-details');
        const newDetail = document.createElement('div');
        newDetail.className = 'row mb-2 trade-detail';
        newDetail.innerHTML = `
            <div class="col-md-5">
                <label class="form-label">数量</label>
                <input type="number" class="form-control quantity-input" name="quantities[]" min="1" required>
            </div>
            <div class="col-md-5">
                <label class="form-label">价格</label>
                <input type="number" class="form-control price-input" name="prices[]" step="0.001" min="0" required>
            </div>
            <div class="col-md-2 d-flex align-items-end">
                <button type="button" class="btn btn-outline-danger btn-sm delete-detail" onclick="TransactionForm.deleteTradeDetail(this)">
                    <i class="bi bi-trash"></i> 删除
                </button>
            </div>
        `;
        container.appendChild(newDetail);
        
        // 获取新添加的输入框并绑定键盘导航
        const quantityInput = newDetail.querySelector('.quantity-input');
        const priceInput = newDetail.querySelector('.price-input');
        this.bindTradeDetailInputs(quantityInput, priceInput);
        
        // 自动聚焦到新添加的数量输入框
        quantityInput.focus();
        
        return newDetail;
    },

    // 删除成交明细行
    deleteTradeDetail(button) {
        const detailRow = button.closest('.trade-detail');
        const container = document.getElementById('trade-details');
        
        if (container.children.length > 1) {
            detailRow.remove();
        } else {
            // 如果是最后一行，清空输入值
            const quantityInput = detailRow.querySelector('.quantity-input');
            const priceInput = detailRow.querySelector('.price-input');
            quantityInput.value = '';
            priceInput.value = '';
            quantityInput.focus();
        }
    },

    // 绑定单个成交明细行的键盘导航
    bindTradeDetailInputs(quantityInput, priceInput) {
        // 数量 -> 价格
        quantityInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                priceInput.focus();
            }
        });

        // 价格特殊处理
        priceInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('broker_fee').focus();
            } else if (e.key === 'Tab' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('addDetailBtn').focus();
            }
        });
    },

    // 绑定键盘导航
    bindKeyboardNavigation() {
        // 日期输入框 -> 股票代码
        const dateInput = document.getElementById('transaction_date');
        if (dateInput) {
            dateInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const stockCodeInput = document.getElementById('stock_code');
                    if (stockCodeInput) stockCodeInput.focus();
                }
            });
        }

        // 股票代码 -> 交易编号
        const stockCodeInput = document.getElementById('stock_code');
        if (stockCodeInput) {
            stockCodeInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !document.getElementById('stock_suggestions')?.contains(e.target)) {
                    e.preventDefault();
                    const transactionCodeInput = document.getElementById('transaction_code');
                    if (transactionCodeInput) transactionCodeInput.focus();
                }
            });
        }

        // 交易编号 -> 第一个数量输入框
        const transactionCodeInput = document.getElementById('transaction_code');
        if (transactionCodeInput) {
            transactionCodeInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || (e.key === 'Tab' && !e.shiftKey)) {
                    e.preventDefault();
                    
                    // 自动设置交易类型（如果是P开头为买入，S开头为卖出）
                    const transactionCode = e.target.value.trim().toUpperCase();
                    const transactionType = document.getElementById('transaction_type');
                    if (transactionType && !transactionType.readOnly) {
                        if (transactionCode.startsWith('P')) {
                            transactionType.value = 'BUY';
                        } else if (transactionCode.startsWith('S')) {
                            transactionType.value = 'SELL';
                        }
                    }
                    
                    // 确保有成交明细行
                    if (document.querySelectorAll('.trade-detail').length === 0) {
                        this.addTradeDetail();
                    }
                    
                    // 直接跳转到第一个数量输入框
                    const firstQuantityInput = document.querySelector('.trade-detail:first-child .quantity-input');
                    if (firstQuantityInput) {
                        firstQuantityInput.focus();
                    }
                }
            });
        }

        // 绑定成交明细的键盘导航
        this.bindTradeDetailNavigation();

        // 绑定费用明细的键盘导航
        this.bindFeeNavigation();
    },

    // 绑定成交明细的键盘导航
    bindTradeDetailNavigation() {
        document.querySelectorAll('.trade-detail').forEach(detail => {
            const quantityInput = detail.querySelector('.quantity-input');
            const priceInput = detail.querySelector('.price-input');
            this.bindTradeDetailInputs(quantityInput, priceInput);
        });
    },

    // 绑定费用明细的键盘导航
    bindFeeNavigation() {
        const feeInputs = [
            'broker_fee',
            'transaction_levy',
            'stamp_duty',
            'trading_fee',
            'deposit_fee'
        ];

        feeInputs.forEach((id, index) => {
            const input = document.getElementById(id);
            if (!input) return;

            input.addEventListener('keydown', (e) => {
                if ((e.key === 'Enter' || e.key === 'Tab') && !e.shiftKey) {
                    e.preventDefault();
                    if (id === 'deposit_fee') {
                        if (e.key === 'Enter') {
                            // 存入证券费按回车键处理
                            const saveAndAddButton = document.querySelector('button[value="save_and_add"]');
                            if (saveAndAddButton && !this.isSubmitting) {
                                saveAndAddButton.focus();
                                saveAndAddButton.click();
                            }
                        } else {
                            // 存入证券费按Tab跳转到取消按钮
                            document.querySelector('a.btn-outline-secondary').focus();
                        }
                    } else {
                        // 其他费用输入框都跳转到下一个费用输入框
                        const nextInput = document.getElementById(feeInputs[index + 1]);
                        if (nextInput) nextInput.focus();
                    }
                }
            });
        });
    },

    // 初始化存入证券费自动保存功能
    initDepositFeeAutoSave() {
        const depositFeeInput = document.getElementById('deposit_fee');
        if (!depositFeeInput) return;

        depositFeeInput.addEventListener('blur', async () => {
            if (this.isSubmitting) return;  // 如果正在提交，则直接返回

            const form = document.getElementById('transactionForm');
            const formData = new FormData(form);
            formData.append('action', 'save_and_add');  // 使用保存并添加下一条的模式

            try {
                this.isSubmitting = true;
                
                // 禁用所有提交按钮
                form.querySelectorAll('button[type="submit"]').forEach(btn => {
                    btn.disabled = true;
                });

                const response = await fetch('/stock/add', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // 显示成功提示
                    this.showSuccess(result.message || '保存成功');
                    
                    // 清空表单并重置焦点
                    this.resetFormAndFocus();
                } else if (result.error) {
                    this.showError(result.error);
                }
            } catch (error) {
                console.error('自动保存失败:', error);
                this.showError('自动保存时发生错误，请重试');
            } finally {
                this.isSubmitting = false;
                // 重新启用提交按钮
                form.querySelectorAll('button[type="submit"]').forEach(btn => {
                    btn.disabled = false;
                });
            }
        });
    },

    // 重置表单并设置焦点
    resetFormAndFocus() {
        const form = document.getElementById('transactionForm');
        const dateInput = document.getElementById('transaction_date');
        
        // 清空表单
        form.reset();
        
        // 清空股票代码控件
        const stockCodeInput = document.getElementById('stock_code');
        if (stockCodeInput) {
            StockCodeControl.clearControl(stockCodeInput);
        }
        
        // 清空所有成交明细
        const tradeDetails = document.getElementById('trade-details');
        if (tradeDetails) {
            tradeDetails.innerHTML = '';
            // 添加一个新的空白成交明细行
            this.addTradeDetail();
        }
        
        // 清空日期并设置焦点
        if (dateInput) {
            dateInput.value = '';
            // 延迟聚焦，等待其他字段清空后
            setTimeout(() => {
                dateInput.focus();
            }, 100);
        }
    },

    // 修改原有的表单提交处理代码
    initFormValidation() {
        const form = document.getElementById('transactionForm');
        this.isSubmitting = false;
        
        // 禁用所有输入框的默认回车提交行为
        form.querySelectorAll('input').forEach(input => {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                }
            });
        });
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (this.isSubmitting) return;
            
            const formData = new FormData(form);
            const submitButton = document.activeElement;
            
            if (submitButton && submitButton.name === 'action') {
                formData.append('action', submitButton.value);
            }

            try {
                this.isSubmitting = true;
                
                form.querySelectorAll('button[type="submit"]').forEach(btn => {
                    btn.disabled = true;
                });

                const response = await fetch('/stock/add', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.showSuccess(result.message || '保存成功');
                    
                    if (submitButton.value === 'save_and_add') {
                        this.resetFormAndFocus();  // 使用统一的重置方法
                    } else if (result.redirect) {
                        setTimeout(() => {
                            window.location.href = result.redirect;
                        }, 1500);
                    }
                    return;
                } else if (result.error) {
                    this.showError(result.error);
                }
            } catch (error) {
                console.error('提交失败:', error);
                this.showError('提交时发生错误，请重试');
            } finally {
                this.isSubmitting = false;
                form.querySelectorAll('button[type="submit"]').forEach(btn => {
                    btn.disabled = false;
                });
            }
        });
    },

    // 显示成功提示
    showSuccess(message) {
        Toastify({
            text: message,
            duration: 2000,
            gravity: "top",
            position: "center",
            backgroundColor: "#28a745"
        }).showToast();
    },

    // 显示错误提示
    showError(message) {
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "center",
            backgroundColor: "#dc3545"
        }).showToast();
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    TransactionForm.init();
}); 