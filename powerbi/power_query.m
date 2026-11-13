// Global Supply Chain & Logistics Intelligence - Power Query (M) Script
let
    BasePath = "C:\path\to\global-supply-chain-logistics-intelligence\data\processed\",
    Source = Csv.Document(File.Contents(BasePath & "fact_shipments.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Promoted, {
        {"shipment_id", Int64.Type}, {"date_key", Int64.Type}, {"route_id", Int64.Type},
        {"carrier_id", Int64.Type}, {"category_id", Int64.Type}, {"weather_id", Int64.Type},
        {"disrupted_flag", Int64.Type}, {"carrier_reliable_flag", Int64.Type}, {"high_risk_flag", Int64.Type},
        {"lead_time_days", type number}, {"risk_index", type number}, {"fuel_price_usd", type number}
    })
in
    Typed
