let
    Source  = Csv.Document(File.Contents(DataFolder & "items.csv"),
                [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
                {"ItemID", type text}, {"ItemName", type text}, {"Category", type text},
                {"UoM", type text}, {"ContractPrice", type number}}, "en-US"),
    Dedup   = Table.Distinct(Typed, {"ItemID"})
in
    Dedup
