-- 为stock_transactions表添加has_splits和avg_price字段
ALTER TABLE stock.stock_transactions 
ADD COLUMN has_splits TINYINT(1) DEFAULT 0 COMMENT '是否有分单记录：0-无，1-有',
ADD COLUMN avg_price DECIMAL(10,4) DEFAULT NULL COMMENT '平均价格';

-- 为transaction_splits表添加avg_price字段
ALTER TABLE stock.transaction_splits
ADD COLUMN avg_price DECIMAL(10,4) DEFAULT NULL COMMENT '平均价格';

-- 更新stock_transactions表中的has_splits字段
UPDATE stock.stock_transactions t
SET t.has_splits = 1
WHERE EXISTS (
    SELECT 1 FROM stock.transaction_splits ts 
    WHERE ts.original_transaction_id = t.id
);

-- 更新stock_transactions表中的avg_price字段
UPDATE stock.stock_transactions
SET avg_price = total_amount / total_quantity
WHERE total_quantity > 0;

-- 更新transaction_splits表中的avg_price字段
UPDATE stock.transaction_splits
SET avg_price = total_amount / total_quantity
WHERE total_quantity > 0; 