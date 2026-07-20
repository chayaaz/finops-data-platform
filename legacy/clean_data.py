import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://chayaazran@localhost:5432/chayaazran"
)

query = "SELECT * FROM raw_transactions;"
df = pd.read_sql(query, engine)

print("Raw shape:", df.shape)

for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

date_cols = ["load_date", "transaction_date", "posting_date"]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors='coerce')

numeric_cols = ["quantity", "net_amount", "tax_amount", "total_amount"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df["currency"] = df["currency"].str.upper()

duplicates = df[df.duplicated(subset=["record_id"], keep=False)]
print("Duplicates:", duplicates.shape)

nulls = df[df["vendor_name"].isnull() | df["total_amount"].isnull()]
print("Null issues:", nulls.shape)

invalid_amounts = df[df["total_amount"] < df["net_amount"]]
print("Invalid amounts:", invalid_amounts.shape)

df_clean = df.drop_duplicates(subset=["record_id"])

print("Clean shape:", df_clean.shape)

df_clean.to_csv("clean_transactions.csv", index=False)

print("Cleaning done!")


issues = []


dup_ids = df[df.duplicated(subset=["record_id"], keep=False)]
for _, row in dup_ids.iterrows():
    issues.append({
        "record_id": row["record_id"],
        "issue_type": "DUPLICATE",
        "description": "Duplicate record_id detected"
    })

missing_vendor = df[df["vendor_name"].isnull()]
for _, row in missing_vendor.iterrows():
    issues.append({
        "record_id": row["record_id"],
        "issue_type": "MISSING_VENDOR",
        "description": "Vendor name is missing"
    })


invalid_amounts = df[df["total_amount"] < df["net_amount"]]
for _, row in invalid_amounts.iterrows():
    issues.append({
        "record_id": row["record_id"],
        "issue_type": "INVALID_AMOUNT",
        "description": "total_amount < net_amount"
    })


negative_amounts = df[df["total_amount"] < 0]
for _, row in negative_amounts.iterrows():
    issues.append({
        "record_id": row["record_id"],
        "issue_type": "NEGATIVE_AMOUNT",
        "description": "Negative total amount"
    })


issues_df = pd.DataFrame(issues)

print("Issues found:", issues_df.shape)


issues_df.to_csv("data_quality_issues.csv", index=False)
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(
    "postgresql+psycopg2://chayaazran@localhost:5432/chayaazran"
)

df_clean.to_sql("clean_transactions", engine, if_exists="replace", index=False)


issues_df.to_sql("data_quality_issues", engine, if_exists="replace", index=False)

print("Tables clean_transactions and data_quality_issues were saved to PostgreSQL")