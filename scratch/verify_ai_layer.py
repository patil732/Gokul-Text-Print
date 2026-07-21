import sys
sys.path.insert(0, '.')

# 1. BusinessAILayer itself
from app.business_ai_layer import BusinessAILayer, business_ai
print('BusinessAILayer imported OK')

# 2. Check the lazy-import paths resolve via source inspection
import inspect
src = inspect.getsource(BusinessAILayer.get_sales_insight)
assert 'app.sales.predict' in src, "app.sales.predict not in get_sales_insight source"
src2 = inspect.getsource(BusinessAILayer.get_inventory_insight)
assert 'app.inventory.predict' in src2, "app.inventory.predict not in get_inventory_insight source"
print('Lazy import strings verified in source')

# 3. Error handling: NotImplementedError from inventory stub
result = business_ai.get_inventory_insight({'total_stock': 10})
print('Inventory stub result:', result)
assert result['status'] == 'error'
assert result['domain'] == 'inventory'
assert 'not yet implemented' in result['message']
print('PASS: inventory returns graceful error dict')

# 4. FileNotFoundError from sales (no model on disk yet)
result2 = business_ai.get_sales_insight({'sales': 1000})
print('Sales missing model result:', result2)
assert result2['status'] == 'error'
assert result2['domain'] == 'sales'
print('PASS: sales missing model returns graceful error dict')

# 5. Admin route imports and cfg paths
from routes.admin import admin_bp, _csv_stats
from app.config import cfg
import os
print('Admin route imports OK')
print('  SALES_MODEL_PATH   :', cfg.SALES_MODEL_PATH)
print('  INVENTORY_MODEL_PATH:', cfg.INVENTORY_MODEL_PATH)

# 6. CEO route imports
from routes.ceo import ceo_bp, _ai
assert isinstance(_ai, BusinessAILayer)
print('CEO route imports OK — _ai is BusinessAILayer instance')

# 7. _to_dataframe helper
import pandas as pd
df = BusinessAILayer._to_dataframe({'a': 1, 'b': 2.5})
assert list(df.columns) == ['a', 'b']
assert len(df) == 1
print('PASS: _to_dataframe produces single-row DataFrame')

print()
print('All checks passed.')
