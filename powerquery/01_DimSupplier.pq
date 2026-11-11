let
    Source  = Excel.Workbook(File.Contents(DataFolder & "suppliers.xlsx"), null, true),
    Sheet   = Source{[Item = "Sheet1", Kind = "Sheet"]}[Data],
    Headers = Table.PromoteHeaders(Sheet, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
                {"SupplierID", type text}, {"SupplierName", type text}, {"Country", type text},
                {"Tier", type text}, {"PaymentTerms", type text}}),
    Dedup   = Table.Distinct(Typed, {"SupplierID"})
in
    Dedup
