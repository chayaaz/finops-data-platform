from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


engine = create_engine(
    "postgresql+psycopg2://chayaazran@localhost:5432/chayaazran"
)

@app.get("/raw")
def get_raw():
    df = pd.read_sql("SELECT * FROM raw_transactions LIMIT 100;", engine)
    return df.to_dict(orient="records")

@app.get("/clean")
def get_clean():
    df = pd.read_sql("SELECT * FROM clean_transactions LIMIT 100;", engine)
    return df.to_dict(orient="records")

@app.get("/issues")
def get_issues():
    df = pd.read_sql("SELECT * FROM data_quality_issues;", engine)
    return df.to_dict(orient="records")

@app.get("/summary")
def get_summary():
    summary = {}

    total_raw = pd.read_sql("SELECT COUNT(*) FROM raw_transactions;", engine).iloc[0,0]
    total_clean = pd.read_sql("SELECT COUNT(*) FROM clean_transactions;", engine).iloc[0,0]
    total_issues = pd.read_sql("SELECT COUNT(*) FROM data_quality_issues;", engine).iloc[0,0]

    top_vendors = pd.read_sql("""
        SELECT vendor_name, SUM(total_amount) AS total
        FROM clean_transactions
        GROUP BY vendor_name
        ORDER BY total DESC
        LIMIT 5;
    """, engine)

    summary["total_raw"] = int(total_raw)
    summary["total_clean"] = int(total_clean)
    summary["total_issues"] = int(total_issues)
    summary["top_vendors"] = top_vendors.to_dict(orient="records")

    return summary