import pandas as pd
from pandas.api.types import (is_numeric_dtype,is_datetime64_any_dtype)
def detect_chart(df:pd.DataFrame):
    if df.empty:
      return None
    cols=list(df.columns)

    if len(cols)==1 and is_numeric_dtype(df[cols[0]]):
       return {
            "type": "kpi",
            "label": cols[0],
            "value": float(df.iloc[0, 0])
        }
    if len(cols)!=2:
       return None
    x,y= cols

    if not is_numeric_dtype(df[y]):
       return None

    if is_datetime64_any_dtype(df[x]):
        return {
            "type": "line",
            "labels": df[x].dt.strftime("%Y-%m-%d").tolist(),
            "values": df[y].tolist(),
            "x_label": x,
            "y_label": y
        }
    if 'year' in x.lower() or 'month' in x.lower():
        return {
            "type": "line",
            "labels": df[x].astype(str).tolist(),
            "values": df[y].tolist(),
            "x_label": x,
            "y_label": y
        }

    unique=df[x].nunique()

    if unique<=8:
        return {
            "type": "pie",
            "labels": df[x].astype(str).tolist(),
            "values": df[y].tolist(),
            "x_label": x,
            "y_label": y
        }

    return {
        "type": "bar",
        "labels": df[x].astype(str).tolist(),
        "values": df[y].tolist(),
        "x_label": x,
        "y_label": y
    }