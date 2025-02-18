/**
 * 股票选择器模块
 */
class StockSelector {
    constructor(options = {}) {
        this.options = {
            containerId: '',              // 容器元素ID
            dropdownId: 'stockSearchDropdown',  // 下拉按钮ID
            searchInputId: 'searchInput', // 搜索输入框ID
            selectAllId: 'selectAll',     // 全选checkbox ID
            stockListId: 'stockList',     // 股票列表容器ID
            selectedContainerId: 'selectedStocksContainer', // 已选股票展示区ID
            hiddenInputName: 'stock_codes', // 隐藏输入字段名称
            maxDisplayCount: 2,           // 下拉按钮最多显示几个股票名称
            marketFilterId: '',           // 市场筛选select ID（可选）
            onSelectionChange: null,      // 选择变更回调函数
            ...options
        };

        this.init();
    }

    init() {
        // 获取DOM元素
        this.container = document.getElementById(this.options.containerId);
        if (!this.container) {
            console.error('Container element not found');
            return;
        }

        this.renderHTML();
        this.initElements();
        this.bindEvents();
        this.updateButtonLabel();
    }

    renderHTML() {
        // 生成HTML结构
        const html = `
            <div class="dropdown w-100">
                <button class="btn btn-outline-secondary dropdown-toggle w-100 text-start" type="button" 
                        id="${this.options.dropdownId}" data-bs-toggle="dropdown" aria-expanded="false" 
                        title="">
                    请选择股票
                </button>
                <ul class="dropdown-menu w-100 p-2" aria-labelledby="${this.options.dropdownId}">
                    <li class="px-2">
                        <input type="text" class="form-control form-control-sm" id="${this.options.searchInputId}" placeholder="搜索股票...">
                    </li>
                    <hr class="my-1">
                    <li>
                        <label class="dropdown-item">
                            <input type="checkbox" class="form-check-input" id="${this.options.selectAllId}"> 全选
                        </label>
                    </li>
                    <hr class="my-1">
                    <div id="${this.options.stockListId}"></div>
                </ul>
                <input type="hidden" name="${this.options.hiddenInputName}" id="selectedCodes">
            </div>
            <div id="${this.options.selectedContainerId}" class="mt-2 small"></div>
        `;
        this.container.innerHTML = html;
    }

    initElements() {
        this.dropdownButton = document.getElementById(this.options.dropdownId);
        this.searchInput = document.getElementById(this.options.searchInputId);
        this.selectAll = document.getElementById(this.options.selectAllId);
        this.stockList = document.getElementById(this.options.stockListId);
        this.selectedContainer = document.getElementById(this.options.selectedContainerId);
        this.selectedCodesInput = document.getElementById('selectedCodes');
        this.marketSelect = this.options.marketFilterId ? document.getElementById(this.options.marketFilterId) : null;
    }

    bindEvents() {
        // 搜索框事件
        this.searchInput.addEventListener('input', () => this.filterStocks());
        this.searchInput.addEventListener('click', e => e.stopPropagation());

        // 全选按钮事件
        this.selectAll.addEventListener('change', () => {
            const isChecked = this.selectAll.checked;
            this.getCheckboxes().forEach(checkbox => {
                const item = checkbox.closest('.dropdown-item');
                if (item.style.display !== 'none') {
                    checkbox.checked = isChecked;
                }
            });
            this.updateButtonLabel();
        });

        // 市场筛选事件
        if (this.marketSelect) {
            this.marketSelect.addEventListener('change', () => this.filterStocks());
        }

        // 防止点击关闭下拉菜单
        this.container.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', e => e.stopPropagation());
        });
    }

    getCheckboxes() {
        return this.stockList.querySelectorAll('.stock-checkbox');
    }

    updateButtonLabel() {
        let selected = [];
        let selectedDetails = [];
        this.getCheckboxes().forEach(checkbox => {
            if (checkbox.checked) {
                const code = checkbox.value;
                const label = checkbox.closest('label').textContent.trim();
                selected.push(code);
                selectedDetails.push({ code, label });
            }
        });

        // 更新按钮文本和提示
        if (selected.length === 0) {
            this.dropdownButton.textContent = "请选择股票";
            this.dropdownButton.title = "";
        } else if (selected.length <= this.options.maxDisplayCount) {
            this.dropdownButton.textContent = selectedDetails.map(item => item.label).join(", ");
            this.dropdownButton.title = selectedDetails.map(item => item.label).join("\n");
        } else {
            this.dropdownButton.textContent = `${selected.length} 只股票已选`;
            this.dropdownButton.title = selectedDetails.map(item => item.label).join("\n");
        }

        // 更新隐藏输入字段
        this.selectedCodesInput.value = selected.join(",");

        // 更新选中项展示区
        this.updateSelectedStocksDisplay(selectedDetails);

        // 触发回调
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(selected, selectedDetails);
        }
    }

    updateSelectedStocksDisplay(selectedStocks) {
        this.selectedContainer.innerHTML = "";
        selectedStocks.forEach(stock => {
            const badge = document.createElement("span");
            badge.className = "badge";
            badge.textContent = stock.label;
            
            const removeBtn = document.createElement("button");
            removeBtn.className = "btn-close";
            removeBtn.setAttribute("aria-label", "Remove");
            removeBtn.onclick = () => {
                const checkbox = this.stockList.querySelector(`input[value="${stock.code}"]`);
                if (checkbox) {
                    checkbox.checked = false;
                    this.updateButtonLabel();
                    this.checkIfAllSelected();
                }
            };
            
            badge.appendChild(removeBtn);
            this.selectedContainer.appendChild(badge);
        });
    }

    checkIfAllSelected() {
        const visibleCheckboxes = [...this.getCheckboxes()].filter(checkbox => {
            const item = checkbox.closest('.dropdown-item');
            return item.style.display !== 'none';
        });
        const allChecked = visibleCheckboxes.length > 0 && 
                          visibleCheckboxes.every(checkbox => checkbox.checked);
        this.selectAll.checked = allChecked;
    }

    filterStocks() {
        const searchValue = this.searchInput.value.toLowerCase();
        const selectedMarket = this.marketSelect ? this.marketSelect.value : '';

        let visibleCount = 0;
        this.getCheckboxes().forEach(checkbox => {
            const item = checkbox.closest('.dropdown-item');
            const text = item.textContent.toLowerCase();
            const stockMarket = checkbox.dataset.market;
            
            const matchesSearch = text.includes(searchValue);
            const matchesMarket = !selectedMarket || stockMarket === selectedMarket;
            
            const isVisible = matchesSearch && matchesMarket;
            item.style.display = isVisible ? "block" : "none";
            if (isVisible) visibleCount++;
        });

        this.checkIfAllSelected();
    }

    // 设置股票列表数据
    setStocks(stocks) {
        this.stockList.innerHTML = stocks.map(stock => `
            <li>
                <label class="dropdown-item">
                    <input type="checkbox" class="form-check-input stock-checkbox" name="stock_codes" 
                           value="${stock.code}" data-market="${stock.market}">
                    ${stock.code} ${stock.name ? `(${stock.name})` : ''}
                </label>
            </li>
        `).join('');

        // 重新绑定事件
        this.getCheckboxes().forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateButtonLabel();
                this.checkIfAllSelected();
            });
        });
    }

    // 获取选中的股票代码
    getSelectedCodes() {
        return this.selectedCodesInput.value.split(',').filter(Boolean);
    }

    // 设置选中的股票代码
    setSelectedCodes(codes) {
        this.getCheckboxes().forEach(checkbox => {
            checkbox.checked = codes.includes(checkbox.value);
        });
        this.updateButtonLabel();
        this.checkIfAllSelected();
    }
}

// 日期处理函数
function formatDateInput(input) {
    // 如果输入为空，不做处理
    if (!input.value.trim()) {
        return;
    }
    
    let value = input.value.replace(/[^\d]/g, '');
    const currentYear = new Date().getFullYear();
    
    // 根据输入长度进行不同处理
    if (value.length === 4) { // 输入格式：MMDD
        const month = value.substring(0, 2);
        const day = value.substring(2, 4);
        if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            value = `${currentYear}-${month}-${day}`;
        }
    } else if (value.length === 3) { // 输入格式：MDD
        const month = value.substring(0, 1);
        const day = value.substring(1, 3);
        if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            value = `${currentYear}-0${month}-${day}`;
        }
    } else if (value.length === 2) { // 输入格式：DD
        const currentMonth = (new Date().getMonth() + 1).toString().padStart(2, '0');
        const day = value;
        if (day >= 1 && day <= 31) {
            value = `${currentYear}-${currentMonth}-${day}`;
        }
    } else if (value.length === 8) { // 输入格式：YYYYMMDD
        const year = value.substring(0, 4);
        const month = value.substring(4, 6);
        const day = value.substring(6, 8);
        if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            value = `${year}-${month}-${day}`;
        }
    }
    
    // 更新输入框的值
    if (value.match(/^\d{4}-\d{2}-\d{2}$/)) {
        input.value = value;
    }
}

// 导出日期处理函数
window.formatDateInput = formatDateInput;

// 导出模块
window.StockSelector = StockSelector; 