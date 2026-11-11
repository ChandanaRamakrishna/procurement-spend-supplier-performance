// Clean fact table = valid rows only (reference DQ_Log, don't re-read the file)
let
    Source = DQ_Log,
    Valid  = Table.SelectRows(Source, each [IssueReason] = null),
    Keep   = Table.SelectColumns(Valid, {
               "PO_ID", "OrderDate", "SupplierID", "ItemID", "Quantity", "UnitPrice",
               "PromisedDate", "ActualDeliveryDate", "DelayDays", "LeadTimeDays", "LineAmount"})
in
    Keep
