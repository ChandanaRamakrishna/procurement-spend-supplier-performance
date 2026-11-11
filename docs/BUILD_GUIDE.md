# Build guide (Steps 2-7)

Step 1 (data) is done by `generate_data.py`. Run `python validate_data.py` any time to get the numbers Power BI should match.

## Step 2: Load and clean in Power Query
1. Power BI Desktop > Home > Transform data > Manage Parameters > New: `DataFolder` (Text), value = full path of `data\` with a trailing `\` (see `powerquery/00_parameter_DataFolder.pq`).
2. Create four blank queries (New Source > Blank Query > Advanced Editor), paste the code, rename the query exactly:
   | File | Query name |
   |---|---|
   | 01_DimSupplier.pq | DimSupplier |
   | 02_DimItem.pq | DimItem |
   | 03_DQ_Log.pq | DQ_Log |
   | 04_FactPO.pq | FactPO |
3. Close & Apply.

How the cleaning works: `DQ_Log` keeps all 2,040 raw rows, adds four 0/1 flags (duplicate, missing supplier, invalid quantity, delivery before order), an `IssueReason` text, `DelayDays` (actual - promised), `LeadTimeDays` (actual - order) and `LineAmount`. `FactPO` references it and keeps only rows with no issue. Keeping the flagged rows in a separate table is what makes the Data Quality page possible.

Check: `FactPO` should have 1,924 rows; `DQ_Log` 2,040, of which 116 are flagged.

## Step 3: Star schema
Model view, create relationships (all one-to-many, single direction, from the dimension to the fact):
- `DimSupplier[SupplierID]` -> `FactPO[SupplierID]`
- `DimItem[ItemID]` -> `FactPO[ItemID]`
- `DimDate[Date]` -> `FactPO[OrderDate]`

Create `DimDate` with `dax/DimDate.dax`, then Table tools > Mark as date table (column `Date`). Sort `Month` by `MonthNo`. Hide the key columns in FactPO. `DQ_Log` stays unrelated on purpose.

All time-based measures use order date. Say this in the README.

## Step 4: DAX measures
Create an empty `_Measures` table and paste in `dax/measures.dax` one measure at a time. Format: spend as currency, percentages as %, lead time and delay with 1 decimal.

You should be able to explain each measure out loud. The ones people ask about:
- **On-Time %**: POs delivered on or before the promised date / all POs.
- **Price Variance vs Contract**: what we paid minus what we would have paid at contract price (positive = overpaying). Uses `RELATED` to fetch the contract price from DimItem for each PO row.
- **Top-5 Supplier Share**: `TOPN` finds the five biggest suppliers in the current filter, `SUMX` adds their spend, divided by total spend. `ALLSELECTED` keeps slicers working.
- **Spend MoM %**: `DATEADD(..., -1, MONTH)` shifts the date filter back one month, then (this month - last month) / last month.
- **Supplier Rank**: `RANKX` over supplier names by Total Spend.

Cross-check against `validate_data.py` (no filters applied):
| Measure | Expected |
|---|---|
| Total Spend | 123,585,280.98 |
| PO Count | 1,924 |
| On-Time % | 30.46% |
| Average Lead Time | 28.70 |
| Average Delay Days | 2.68 |
| Price Variance vs Contract | 1,973,367.68 |
| Off-Contract Spend % | 23.86% |
| Top-5 Supplier Share | 66.47% |
| DQ Duplicate POs / Missing Supplier / Invalid Qty / Delivery Before Order | 40 / 30 / 20 / 28 |

(28 delivery-before-order, not 25, because three of the 40 duplicate copies were copies of already-bad rows.) If your numbers differ, find out why before building visuals.

## Step 5: Report pages
Use one consistent theme, titles that say what the page answers, and the same slicers' positions on every page.

**Page 1 Overview** ("Where does the money go?")
- KPI cards: Total Spend, PO Count, On-Time %, Average Delay Days, Off-Contract Spend %, Top-5 Supplier Share.
- Line chart: Total Spend by DimDate[YearMonth]; add Spend MoM % as a card or tooltip.
- Bar chart: Total Spend by DimItem[Category].
- Slicers: Year, Category, Country, Supplier Tier.

**Page 2 Supplier Performance** ("Who delivers?")
- Table: SupplierName, Supplier Rank, Total Spend, On-Time %, Average Lead Time, Average Delay Days, Price Variance %. Sort by Rank; conditional formatting (red/green) on On-Time %.
- Scatter: X = Average Lead Time, Y = On-Time %, size = Total Spend, details = SupplierName.
- Drill-through: add a page "Supplier Detail" (Page information > hide it), put SupplierName in the Drill-through well, show that supplier's monthly spend, on-time trend, Price Variance and its POs. Right-click a supplier on page 2 > Drill through.

**Page 3 Data Quality** ("Can we trust the data?")
- Cards: DQ Raw Rows, DQ Flagged Rows, DQ Flagged %.
- Bar chart: the four DQ measures (use a small helper table or four cards).
- Table: DQ_Log with PO_ID, SupplierID, ItemID, Quantity, OrderDate, ActualDeliveryDate, IssueReason; visual-level filter IssueReason is not blank.
- Text box: "Flagged rows are excluded from all spend and delivery metrics."

## Step 6: Package
1. Save `procurement_dashboard.pbix` in the repo root.
2. Screenshots of each page into `screenshots/` (PNG).
3. Fill in `README.md` (the [FILL] parts, with your own real findings).
4. `git init`, commit, push. Check `.gitignore`: data files can be committed (small and synthetic) so the project reproduces.
5. Note: `.pbix` is binary and must be under GitHub's 100 MB limit (it will be tiny).

## Step 7: Resume (only when finished)
Add it only when you can explain every measure and relationship without notes. Draft bullets once you have real findings:
- Built a Power BI procurement dashboard on synthetic PO data (2,000+ rows, Python-generated) covering spend, supplier on-time delivery, contract price variance and supplier concentration.
- Cleaned data in Power Query, flagging duplicates, missing suppliers and invalid dates; modeled a star schema and wrote [N] DAX measures including Top-5 supplier share and month-over-month spend.
Put real numbers from your findings in a third bullet.

## Interview questions to rehearse
- Why a star schema? Why is DQ_Log not related to the model?
- Why exclude flagged rows instead of fixing them? What would you do with real data?
- What's the difference between a calculated column and a measure, and why is DelayDays a column and On-Time % a measure?
- How does `ALLSELECTED` differ from `ALL`?
- What are the limits of synthetic data?

## Optional upgrades (only after the above works)
- SQL: load the CSVs into SQLite/PostgreSQL and write views for spend and supplier KPIs; connect Power BI to those.
- Python: add a `data_quality_report.py` that outputs the same checks as a CSV.
- A "What-if" parameter to model a price renegotiation on top suppliers.
- Row-level security by supplier country.
