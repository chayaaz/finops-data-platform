import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://chayaazran@localhost:5432/chayaazran"
)

query = "SELECT * FROM raw_transactions LIMIT 10;"
df = pd.read_sql(query, engine)

print(df.head())
print(df.shape)