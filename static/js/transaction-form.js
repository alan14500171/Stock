// 交易表单控制模块
const TransactionForm = {
    // 初始化
    init() {
        // 如果没有成交明细行，添加第一行
        if (document.querySelectorAll('.trade-detail').length === 0) {
            addTradeDetail();
        }
        this.bindKeyboardNavigation();
        this.initFormValidation();
        this.initFormSubmission();
    },

    // 绑定键盘导航
    bindKeyboardNavigation() {
        // 日期输入框 -> 股票代码
        document.getElementById('transaction_date').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('stock_code').focus();
            }
        });

        // 股票代码 -> 交易编号
        document.getElementById('stock_code').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !document.getElementById('stock_suggestions')?.contains(e.target)) {
                e.preventDefault();
                document.getElementById('transaction_code').focus();
            }
        });

        // 交易编号 -> 交易类型
        document.getElementById('transaction_code').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('transaction_type').focus();
            }
        });

        // 交易类型 -> 第一个数量输入框
        document.getElementById('transaction_type').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.querySelector('.quantity-input').focus();
            }
        });

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
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (id === 'deposit_fee') {
                        // 存入证券费按回车触发保存并添加下一条
                        document.querySelector('button[value="save_and_add"]').click();
                    } else {
                        // 跳转到下一个费用输入框
                        const nextInput = document.getElementById(feeInputs[index + 1]);
                        if (nextInput) nextInput.focus();
                    }
                } else if (e.key === 'Tab' && !e.shiftKey) {
                    e.preventDefault();
                    if (id === 'broker_fee') {
                        // 经纪佣金按Tab跳转到保存按钮
                        document.querySelector('button[value="save"]').focus();
                    } else if (id === 'deposit_fee') {
                        // 存入证券费按Tab跳转到取消按钮
                        document.querySelector('a.btn-outline-secondary').focus();
                    } else {
                        // 其他费用按Tab跳转到下一个费用
                        const nextInput = document.getElementById(feeInputs[index + 1]);
                        if (nextInput) nextInput.focus();
                    }
                }
            });
        });
    },

    // 初始化表单验证
    initFormValidation() {
        const form = document.getElementById('transactionForm');
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // 检查必填字段
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    this.showError(`${field.previousElementSibling.textContent}不能为空`);
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (isValid) {
                this.submitForm(e.submitter.value);
            }
        });
    },

    // 初始化表单提交
    initFormSubmission() {
        const form = document.getElementById('transactionForm');
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const action = e.submitter.value;
            this.submitForm(action);
        });
    },

    // 提交表单
    async submitForm(action) {
        const form = document.getElementById('transactionForm');
        const formData = new FormData(form);
        formData.append('action', action);

        try {
            const response = await fetch('/stock/add', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('交易记录添加成功');
                if (action === 'save') {
                    window.location.href = result.redirect;
                } else {
                    form.reset();
                    setDefaultDate();
                    document.querySelector('.quantity-input').focus();
                }
            } else {
                this.showError(result.error || '保存失败，请重试');
            }
        } catch (error) {
            this.showError('提交表单时发生错误，请重试');
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