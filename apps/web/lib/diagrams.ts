/**
 * Mermaid diagram definitions (aligned with scripts/generate_diagrams.py).
 * Used by the Metadata page for lineage, data model, and architecture.
 */

export const DATA_ARCHITECTURE_MMD = `flowchart LR
    subgraph Sources["NMDPRA Public"]
        A1[OilGasData]
        A2[VesselSchedule]
        A3[DailyTruckout]
        A4[StockReport]
    end

    subgraph Ingestion["Ingestion & validation"]
        B1[Discover]
        B2[Download]
        B3[Parse]
        B4[DQ]
        B5[Silver Build]
        B6[Gold Build]
        B7[Publish Metadata]
        B1 --> B2 --> B3 --> B4 --> B5 --> B6 --> B7
    end

    subgraph Parsers["Parsers"]
        P1[oilgasdata_parser]
        P2[vesselschedule_parser]
        P3[dailytruckout_parser]
        P4[stockreport_parser]
    end

    subgraph Postgres["PostgreSQL"]
        D1[(bronze)]
        D2[(silver)]
        D3[(gold)]
        D4[(meta)]
    end

    subgraph API["FastAPI"]
        E1[Business APIs]
        E2[Governance APIs]
    end

    subgraph UI["Next.js"]
        F1[Dashboard]
    end

    Sources --> Ingestion
    B3 --> Parsers
    Parsers --> D1
    B5 --> D2
    B6 --> D3
    B7 --> D4
    D1 --> D2
    D2 --> D3
    D1 --> D4
    D2 --> D4
    D3 --> D4
    D1 --> E1
    D2 --> E1
    D3 --> E1
    D4 --> E2
    E1 --> F1
    E2 --> F1
`;

export const LINEAGE_MMD = `flowchart TB
    subgraph Bronze["Bronze"]
        B1[file_registry]
        B2[performance_highlights]
        B3[refinery_status]
        B4[modular_refinery_output]
        B7[fuel_prices_city]
        B9[chart_series_values]
        B10[vessel_clearance_schedule]
        B11[truckout_*]
        B14[stock_*]
    end

    subgraph Silver["Silver"]
        S1[dim_date]
        S2[dim_product]
        S3[dim_location]
        S4[dim_facility]
        S5[fact_prices]
        S6[fact_stock]
        S7[fact_truckout]
        S8[fact_refinery_output]
        S9[fact_vessel_clearance]
        S10[fact_chart_series]
    end

    subgraph Gold["Gold"]
        G1[dim_date]
        G2[dim_product]
        G3[dim_location]
        G4[dim_facility]
        G5[dim_report]
        G6[fact_fuel_prices]
        G7[fact_stock_sufficiency]
        G8[fact_truckout]
        G9[fact_refinery]
        G10[fact_vessel_clearance]
        G11[fact_series]
    end

    B7 --> S5
    B2 --> S1
    B3 --> S4
    B4 --> S4
    B7 --> S2
    B7 --> S3
    B11 --> S3
    B11 --> S7
    B14 --> S6
    B10 --> S9
    B9 --> S10

    S1 --> S5
    S2 --> S5
    S3 --> S5
    S1 --> S6
    S2 --> S6
    S1 --> S7
    S2 --> S7
    S3 --> S7
    S1 --> S8
    S4 --> S8
    S1 --> S9
    S10 --> S1

    S1 --> G1
    S2 --> G2
    S3 --> G3
    S4 --> G4
    S5 --> G6
    S6 --> G7
    S7 --> G8
    S8 --> G9
    S9 --> G10
    S10 --> G11
    G1 --> G6
    G2 --> G6
    G3 --> G6
    G5 --> G6
    G5 --> G7
    G5 --> G8
    G5 --> G9
    G5 --> G10
    G5 --> G11
`;

export const DATA_MODEL_MMD = `erDiagram
    gold_dim_date ||--o{ gold_fact_fuel_prices : "date_month_key"
    gold_dim_date ||--o{ gold_fact_stock_sufficiency : "date_key"
    gold_dim_date ||--o{ gold_fact_truckout : "date_key"
    gold_dim_date ||--o{ gold_fact_refinery : "month_key"
    gold_dim_date ||--o{ gold_fact_vessel_clearance : "month_key"
    gold_dim_date ||--o{ gold_fact_series : "date_key"

    gold_dim_location ||--o{ gold_fact_fuel_prices : "location_key"
    gold_dim_location ||--o{ gold_fact_truckout : "location_key"

    gold_dim_product ||--o{ gold_fact_fuel_prices : "product_key"
    gold_dim_product ||--o{ gold_fact_stock_sufficiency : "product_key"
    gold_dim_product ||--o{ gold_fact_truckout : "product_key"

    gold_dim_facility ||--o{ gold_fact_refinery : "facility_key"

    gold_dim_report ||--o{ gold_fact_fuel_prices : "report_key"
    gold_dim_report ||--o{ gold_fact_stock_sufficiency : "report_key"
    gold_dim_report ||--o{ gold_fact_truckout : "report_key"
    gold_dim_report ||--o{ gold_fact_refinery : "report_key"
    gold_dim_report ||--o{ gold_fact_vessel_clearance : "report_key"
    gold_dim_report ||--o{ gold_fact_series : "report_key"

    gold_dim_date {
        date date_key PK
        int year
        int month
        int day
    }

    gold_dim_product {
        uuid product_key PK
        string product_code
        string product_name
    }

    gold_dim_location {
        uuid location_key PK
        string location_name
        string location_type
    }

    gold_dim_facility {
        uuid facility_key PK
        string facility_name
        string facility_type
    }

    gold_dim_report {
        uuid report_key PK
        string source_name
        string report_title
        string status
    }

    gold_fact_fuel_prices {
        uuid id PK
        date date_month_key FK
        uuid location_key FK
        uuid product_key FK
        uuid report_key FK
        numeric indicative
        numeric avg_price
    }

    gold_fact_stock_sufficiency {
        uuid id PK
        date date_key FK
        uuid product_key FK
        uuid report_key FK
        numeric days_sufficiency
    }

    gold_fact_truckout {
        uuid id PK
        date date_key FK
        uuid location_key FK
        uuid product_key FK
        uuid report_key FK
        numeric volume_litres
    }

    gold_fact_refinery {
        uuid id PK
        date month_key FK
        uuid facility_key FK
        uuid report_key FK
        numeric utilization_pct
    }

    gold_fact_vessel_clearance {
        uuid id PK
        date month_key FK
        uuid report_key FK
        string vessel
        numeric processing_days
    }

    gold_fact_series {
        uuid id PK
        date date_key FK
        uuid report_key FK
        string series_name
        numeric metric_value
    }
`;
