import os, json
from typing import List, Dict, Any
import pandas as pd

def export_csv(rows: List[Dict[str, Any]], out_path: str) -> str:
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    return out_path

def export_json(rows: List[Dict[str, Any]], meta: Dict[str, Any], out_path: str) -> str:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "rows": rows}, f, ensure_ascii=False, indent=2)
    return out_path
