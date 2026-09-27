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

    
    chart={
                "labels": df[x].astype(str).tolist(),
                "values": df[y].tolist(),
                "x_label": x.replace('_',' ').title(),
                "y_label": y.replace('_',' ').title(),
                "title":f"{y.replace('_',' ').title()} by {x.replace('_',' ').title()}"
        }
    
    # ---------- LINE ----------
    if "year" in x.lower() or "month" in x.lower():
        chart["type"] = "line"
        return chart

    if is_datetime64_any_dtype(df[x]):
        chart["type"] = "line"
        chart["labels"] = df[x].dt.strftime("%Y-%m-%d").tolist()
        return chart

    # ---------- PIE ----------
    if df[x].nunique() <= 8:
        chart["type"] = "pie"
        return chart

    # ---------- BAR ----------
    chart["type"] = "bar"
    return chart

    

def genrate_insides(df:pd.DataFrame):
    if df.empty:
      return None
    cols=df.columns
    if len(cols)==1:
      value=df.iloc[0,0]
      return f"{cols[0].replace('_',' ').title()} is {value}."
    if len(cols)==2:
      x,y=cols
      if pd.api.types.is_numeric_dtype(df[y]):
         highest=df.iloc[df[y].idxmax()]
         lowest=df.iloc[df[y].idxmin()]
         return (
                f"{highest[x]} has the highest {y.replace('_',' ')} "
                f"({highest[y]}), while {lowest[x]} has the lowest "
                f"({lowest[y]})."
            )
    return f"The query returned {len(df)} rows."
