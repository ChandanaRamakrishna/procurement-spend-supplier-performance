// Staging table: ALL raw PO rows, typed, with problem flags + reason.
// Loaded to the model (no relationships) to power the Data Quality page.
let
    Source   = Csv.Document(File.Contents(DataFolder & "purchase_orders.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Headers, {
                 {"PO_ID", type text}, {"OrderDate", type date}, {"SupplierID", type text},
                 {"ItemID", type text}, {"Quantity", Int64.Type}, {"UnitPrice", type number},
                 {"PromisedDate", type date}, {"ActualDeliveryDate", type date}}, "en-US"),

    // Blank supplier -> null
    CleanSup = Table.ReplaceValue(Typed, "", null, Replacer.ReplaceValue, {"SupplierID"}),

    // Number repeated PO_IDs: first occurrence = 0, copies = 1, 2, ...
    Grouped  = Table.Group(CleanSup, {"PO_ID"},
                 {{"T", each Table.AddIndexColumn(_, "DupIndex", 0, 1, Int64.Type), type table}}),
    Combined = Table.Combine(Grouped[T]),

    // Problem flags (1 = problem)
    F1 = Table.AddColumn(Combined, "IsDuplicate",
           each if [DupIndex] > 0 then 1 else 0, Int64.Type),
    F2 = Table.AddColumn(F1, "IsMissingSupplier",
           each if [SupplierID] = null then 1 else 0, Int64.Type),
    F3 = Table.AddColumn(F2, "IsInvalidQty",
           each if [Quantity] <> null and [Quantity] <= 0 then 1 else 0, Int64.Type),
    F4 = Table.AddColumn(F3, "IsDateError",
           each if [ActualDeliveryDate] <> null and [OrderDate] <> null
                   and [ActualDeliveryDate] < [OrderDate] then 1 else 0, Int64.Type),

    // Human-readable reason (null = valid row)
    Reason = Table.AddColumn(F4, "IssueReason", each
               let parts = List.Select({
                     if [IsDuplicate] = 1       then "Duplicate PO"          else null,
                     if [IsMissingSupplier] = 1 then "Missing Supplier"      else null,
                     if [IsInvalidQty] = 1      then "Invalid Quantity"      else null,
                     if [IsDateError] = 1       then "Delivery Before Order" else null
                   }, each _ <> null)
               in if List.Count(parts) = 0 then null else Text.Combine(parts, "; "),
             type nullable text),

    // Derived metrics
    Delay  = Table.AddColumn(Reason, "DelayDays",
               each Duration.Days([ActualDeliveryDate] - [PromisedDate]), Int64.Type),
    Lead   = Table.AddColumn(Delay, "LeadTimeDays",
               each Duration.Days([ActualDeliveryDate] - [OrderDate]), Int64.Type),
    Amount = Table.AddColumn(Lead, "LineAmount",
               each [Quantity] * [UnitPrice], type number),

    Result = Table.RemoveColumns(Amount, {"DupIndex"})
in
    Result
