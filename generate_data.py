"""
Generate SYNTHETIC procurement data for the Power BI dashboard.
All data is artificial. Fixed seed => identical output every run.

Outputs (in ./data):
  suppliers.xlsx       supplier master
  items.csv            item master with contract prices
  purchase_orders.csv  ~2,000 POs + deliberate data problems
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)
out = Path("data")
out.mkdir(exist_ok=True)

# ---------- Suppliers (Excel) ----------
n_sup = 25
suppliers = pd.DataFrame({
    "SupplierID": [f"S{i:03d}" for i in range(1, n_sup + 1)],
    "SupplierName": [f"Supplier {i:02d}" for i in range(1, n_sup + 1)],
    "Country": rng.choice(["India", "China", "Germany", "USA", "Vietnam", "Mexico"], n_sup),
    "Tier": rng.choice(["Strategic", "Preferred", "Approved"], n_sup, p=[0.2, 0.4, 0.4]),
    "PaymentTerms": rng.choice(["Net 30", "Net 45", "Net 60"], n_sup),
})
# Hidden reliability traits: some suppliers are consistently late
sup_delay_mean = rng.uniform(-1, 9, n_sup)   # average days late
sup_delay_sd = rng.uniform(1, 5, n_sup)

# ---------- Items (CSV) ----------
n_items = 60
categories = ["Raw Materials", "Packaging", "Electronics", "MRO", "Logistics", "IT Services"]
items = pd.DataFrame({
    "ItemID": [f"I{i:03d}" for i in range(1, n_items + 1)],
    "ItemName": [f"Item {i:02d}" for i in range(1, n_items + 1)],
    "Category": rng.choice(categories, n_items),
    "UoM": rng.choice(["EA", "KG", "BOX"], n_items),
    "ContractPrice": np.round(rng.uniform(5, 500, n_items), 2),
})

# ---------- Purchase orders ----------
n_po = 2000
w = rng.dirichlet(np.ones(n_sup) * 0.6)        # uneven weights => supplier concentration
sup_idx = rng.choice(n_sup, n_po, p=w)
item_idx = rng.integers(0, n_items, n_po)

order_date = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 540, n_po), unit="D")
promised = order_date + pd.to_timedelta(rng.integers(7, 46, n_po), unit="D")
delay = np.round(rng.normal(sup_delay_mean[sup_idx], sup_delay_sd[sup_idx])).astype(int)
actual = promised + pd.to_timedelta(delay, unit="D")

contract = items["ContractPrice"].values[item_idx]
off = rng.random(n_po) < 0.25                  # ~25% priced off-contract (-5% to +20%)
unit_price = np.where(off, contract * rng.uniform(0.95, 1.20, n_po), contract).round(2)

po = pd.DataFrame({
    "PO_ID": [f"PO{i:05d}" for i in range(1, n_po + 1)],
    "OrderDate": order_date,
    "SupplierID": suppliers["SupplierID"].values[sup_idx],
    "ItemID": items["ItemID"].values[item_idx],
    "Quantity": rng.integers(10, 500, n_po),
    "UnitPrice": unit_price,
    "PromisedDate": promised,
    "ActualDeliveryDate": actual,
})

# ---------- Deliberate data problems ----------
bad = rng.choice(po.index, 25, replace=False)          # delivery before order date
po.loc[bad, "ActualDeliveryDate"] = po.loc[bad, "OrderDate"] - pd.to_timedelta(rng.integers(1, 10, 25), unit="D")
po.loc[rng.choice(po.index, 30, replace=False), "SupplierID"] = np.nan   # missing supplier
neg = rng.choice(po.index, 20, replace=False)          # negative quantity
po.loc[neg, "Quantity"] = -po.loc[neg, "Quantity"]
dups = po.sample(40, random_state=SEED)                # duplicate POs (same PO_ID)
po = pd.concat([po, dups], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)

# ---------- Save ----------
suppliers.to_excel(out / "suppliers.xlsx", index=False)
items.to_csv(out / "items.csv", index=False)
po.to_csv(out / "purchase_orders.csv", index=False)
print(f"POs: {len(po)} | Suppliers: {len(suppliers)} | Items: {len(items)}")
