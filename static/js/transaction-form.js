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

    // 初始化表单验证和提交
    initFormValidation() {
        const form = document.getElementById('transactionForm');
        this.isSubmitting = false;  // 添加提交状态标记
        
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
            
            if (this.isSubmitting) return;  // 如果正在提交，则直接返回
            
            // 检查必填字段
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            let firstInvalidField = null;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    if (!firstInvalidField) firstInvalidField = field;
                    this.showError(`${field.previousElementSibling.textContent}不能为空`);
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            // 检查数值字段
            const numberFields = form.querySelectorAll('input[type="number"]');
            numberFields.forEach(field => {
                const value = field.value.trim();
                if (value) {
                    const num = parseFloat(value);
                    if (isNaN(num) || num < 0) {
                        isValid = false;
                        field.classList.add('is-invalid');
                        if (!firstInvalidField) firstInvalidField = field;
                        this.showError(`${field.previousElementSibling.textContent}必须是有效的正数`);
                    } else {
                        field.classList.remove('is-invalid');
                    }
                }
            });
            
            // 检查成交明细
            const details = document.querySelectorAll('.trade-detail');
            if (details.length === 0) {
                isValid = false;
                this.showError('请至少添加一条成交明细');
            } else {
                let hasValidDetail = false;
                details.forEach(detail => {
                    const quantity = detail.querySelector('.quantity-input').value.trim();
                    const price = detail.querySelector('.price-input').value.trim();
                    if (quantity && price) {
                        hasValidDetail = true;
                    }
                });
                if (!hasValidDetail) {
                    isValid = false;
                    this.showError('请至少填写一条完整的成交明细');
                }
            }
            
            if (isValid) {
                const action = e.submitter.value;
                await this.submitForm(action);
            } else if (firstInvalidField) {
                firstInvalidField.focus();
            }
        });
    },

    // 提交表单
    async submitForm(action) {
        this.isSubmitting = true;  // 设置提交状态

        const form = document.getElementById('transactionForm');
        const submitButtons = form.querySelectorAll('button[type="submit"]');
        
        // 禁用所有提交按钮
        submitButtons.forEach(button => {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
        });

        try {
            // 构建表单数据
            const formData = new FormData(form);
            formData.append('action', action);

            // 处理费用字段，确保为数字
            ['broker_fee', 'transaction_levy', 'stamp_duty', 'trading_fee', 'deposit_fee'].forEach(field => {
                const value = formData.get(field);
                formData.set(field, value ? parseFloat(value) : 0);
            });

            // 发送请求
            const response = await fetch(form.getAttribute('action') || '/stock/add', {
                method: 'POST',
                body: formData
            });

            let result;
            try {
                result = await response.json();
            } catch (e) {
                throw new Error('服务器返回的数据格式不正确');
            }

            if (!response.ok) {
                throw new Error(`服务器错误 (${response.status}): ${result?.error || '未知错误'}`);
            }
            
            if (result.success) {
                this.showSuccess('保存成功');
                if (action === 'save') {
                    window.location.href = result.redirect;
                } else {
                    // 重置表单
                    form.reset();
                    // 设置默认日期
                    this.setDefaultDate();
                    // 添加一行成交明细
                    const container = document.getElementById('trade-details');
                    container.innerHTML = '';  // 清空所有成交明细
                    this.addTradeDetail();  // 添加一行新的成交明细
                    // 聚焦到第一个输入框
                    document.getElementById('stock_code').focus();
                }
            } else {
                this.showError(result.error || '保存失败，请重试');
                // 如果是汇率相关错误，自动聚焦到日期输入框
                if (result.error && result.error.includes('汇率')) {
                    document.getElementById('transaction_date').focus();
                }
            }
        } catch (error) {
            console.error('提交表单时发生错误:', error);
            let errorMessage = '提交表单时发生错误';
            
            if (error.message.includes('服务器错误')) {
                errorMessage = error.message;
            } else if (!navigator.onLine) {
                errorMessage = '网络连接已断开，请检查网络设置后重试';
            } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                errorMessage = '无法连接到服务器，请检查网络连接并重试';
            } else if (error.message.includes('数据格式不正确')) {
                errorMessage = '服务器响应格式错误，请刷新页面重试';
            }
            
            this.showError(errorMessage);
        } finally {
            // 恢复提交状态和按钮状态
            this.isSubmitting = false;
            submitButtons.forEach(button => {
                button.disabled = false;
                button.innerHTML = button.value === 'save' ? '保存' : '保存并添加下一条';
            });
        }
    },

    // 显示成功提示
    showSuccess(message) {
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: 'right',
            backgroundColor: "#4caf50"
        }).showToast();
    },

    // 显示错误提示
    showError(message) {
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: 'right',
            backgroundColor: "#f44336"
        }).showToast();
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    TransactionForm.init();
}); 