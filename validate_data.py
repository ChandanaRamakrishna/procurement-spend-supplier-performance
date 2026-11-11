"""
Independent pandas calculation of the same logic as the Power Query + DAX.
Use it to cross-check your Power BI numbers (they should match).
Run after generate_data.py.
"""
import pandas as pd

po = pd.read_csv("data/purchase_orders.csv",
                 parse_dates=["OrderDate", "PromisedDate", "ActualDeliveryDate"])
items = pd.read_csv("data/items.csv")

po["IsDuplicate"] = po.duplicated("PO_ID", keep="first")
po["IsMissingSupplier"] = po["SupplierID"].isna()
po["IsInvalidQty"] = po["Quantity"] <= 0
po["IsDateError"] = po["ActualDeliveryDate"] < po["OrderDate"]
flags = ["IsDuplicate", "IsMissingSupplier", "IsInvalidQty", "IsDateError"]
po["Flagged"] = po[flags].any(axis=1)

print("=== DATA QUALITY (expected on Data Quality page) ===")
print("Raw rows:", len(po))
for f in flags:
    print(f"{f}: {int(po[f].sum())}")
print("Flagged rows (any issue):", int(po["Flagged"].sum()))

v = po[~po["Flagged"]].merge(items[["ItemID", "ContractPrice"]], on="ItemID", how="left")
v["Line"] = v["Quantity"] * v["UnitPrice"]
v["ContractLine"] = v["Quantity"] * v["ContractPrice"]
v["Delay"] = (v["ActualDeliveryDate"] - v["PromisedDate"]).dt.days
v["Lead"] = (v["ActualDeliveryDate"] - v["OrderDate"]).dt.days
v["Off"] = (v["UnitPrice"] - v["ContractPrice"]).abs() > 0.005

by_sup = v.groupby("SupplierID")["Line"].sum().sort_values(ascending=False)
print("\n=== KPIs on VALID rows (expected on Overview page, no filters) ===")
print(f"Total Spend:              {v['Line'].sum():,.2f}")
print(f"PO Count:                 {v['PO_ID'].nunique()}")
print(f"On-Time %:                {(v['Delay'] <= 0).mean():.2%}")
print(f"Average Lead Time (days): {v['Lead'].mean():.2f}")
print(f"Average Delay Days:       {v['Delay'].mean():.2f}")
print(f"Price Variance vs Contract: {v['Line'].sum() - v['ContractLine'].sum():,.2f}")
print(f"Off-Contract Spend %:     {v.loc[v['Off'], 'Line'].sum() / v['Line'].sum():.2%}")
print(f"Top-5 Supplier Share:     {by_sup.head(5).sum() / by_sup.sum():.2%}")

ot = v.groupby("SupplierID")["Delay"].apply(lambda s: (s <= 0).mean()).sort_values()
print("\nLeast on-time suppliers:\n", ot.head(3).round(3).to_string())
print("Most on-time suppliers:\n", ot.tail(3).round(3).to_string())
