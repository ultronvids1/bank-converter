import os
import re
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

@dataclass
class ExtractionResult:
    rows: List[Dict[str, Any]]
    meta: Dict[str, Any]

DATE_RE = re.compile(r"""^\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\s*$""")

def _normalize_amount(s: str) -> Optional[float]:
    if s is None:
        return None
    t = str(s).strip()
    if not t:
        return None
    t = t.replace(",", "")
    # parentheses negative
    neg = False
    if t.startswith("(") and t.endswith(")"):
        neg = True
        t = t[1:-1]
    # remove currency symbols
    t = re.sub(r"[^0-9.\-]", "", t)
    if t in {"", "-", "."}:
        return None
    try:
        val = float(t)
        return -val if neg else val
    except ValueError:
        return None

def _pick_schema(df: pd.DataFrame) -> Tuple[str, List[str]]:
    # Try to map columns to a standard schema.
    cols = [str(c).strip().lower() for c in df.columns]
    joined = " | ".join(cols)
    # common hints
    if "description" in joined or "details" in joined or "narration" in joined:
        pass
    # Return a simple schema label and cols
    return "generic", cols

def _df_to_transactions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    df = df.copy()
    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]
    # Drop empty rows
    df = df.dropna(how="all")
    if df.empty:
        return []

    # Heuristic column mapping
    col_lower = {c: str(c).lower() for c in df.columns}
    date_col = next((c for c in df.columns if "date" in col_lower[c]), None)
    desc_col = next((c for c in df.columns if any(k in col_lower[c] for k in ["description","details","narration","particular","merchant"])), None)
    debit_col = next((c for c in df.columns if any(k in col_lower[c] for k in ["debit","withdraw","payment","out"])), None)
    credit_col = next((c for c in df.columns if any(k in col_lower[c] for k in ["credit","deposit","in"])), None)
    balance_col = next((c for c in df.columns if "balance" in col_lower[c]), None)
    amount_col = next((c for c in df.columns if "amount" in col_lower[c]), None)

    txs: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        date = row.get(date_col) if date_col else None
        desc = row.get(desc_col) if desc_col else None

        debit = _normalize_amount(row.get(debit_col)) if debit_col else None
        credit = _normalize_amount(row.get(credit_col)) if credit_col else None
        balance = _normalize_amount(row.get(balance_col)) if balance_col else None

        if amount_col and debit is None and credit is None:
            amt = _normalize_amount(row.get(amount_col))
            # If we have balance but no direction, keep amount as 'amount'
        else:
            amt = None

        # skip rows that look like headers or separators
        if isinstance(date, str) and not DATE_RE.match(date.strip()) and (desc is None or str(desc).strip() == ""):
            continue

        txs.append({
            "date": str(date).strip() if date is not None else None,
            "description": str(desc).strip() if desc is not None else None,
            "debit": debit,
            "credit": credit,
            "amount": amt,
            "balance": balance,
        })
    # Remove fully empty txs
    txs = [t for t in txs if any(v not in (None, "", []) for v in t.values())]
    return txs

def extract_transactions(pdf_path: str) -> ExtractionResult:
    """Extract transactions from a PDF using layered engines and normalize to a common schema."""
    meta: Dict[str, Any] = {"engines_tried": [], "pages": None, "confidence": 0.6}

    # 1) pdfplumber
    try:
        import pdfplumber
        meta["engines_tried"].append("pdfplumber")
        txs: List[Dict[str, Any]] = []
        with pdfplumber.open(pdf_path) as pdf:
            meta["pages"] = len(pdf.pages)
            for page in pdf.pages:
                tables = page.extract_tables()
                for t in tables or []:
                    if not t or len(t) < 2:
                        continue
                    header = t[0]
                    rows = t[1:]
                    df = pd.DataFrame(rows, columns=header)
                    txs.extend(_df_to_transactions(df))
        if txs:
            meta["confidence"] = 0.88
            return ExtractionResult(rows=txs, meta=meta)
    except Exception as e:
        meta["pdfplumber_error"] = str(e)

    # 2) Camelot
    try:
        import camelot
        for flavor in ["lattice", "stream"]:
            meta["engines_tried"].append(f"camelot:{flavor}")
            tables = camelot.read_pdf(pdf_path, pages="all", flavor=flavor)
            txs: List[Dict[str, Any]] = []
            for t in tables:
                df = t.df
                if df is None or df.empty:
                    continue
                # Camelot returns data without header; best-effort header inference:
                df.columns = [f"col_{i}" for i in range(df.shape[1])]
                txs.extend(_df_to_transactions(df))
            if txs:
                meta["confidence"] = 0.82 if flavor == "stream" else 0.86
                return ExtractionResult(rows=txs, meta=meta)
    except Exception as e:
        meta["camelot_error"] = str(e)

    # 3) PyMuPDF table detection + text blocks
    try:
        import fitz  # PyMuPDF
        meta["engines_tried"].append("pymupdf")
        doc = fitz.open(pdf_path)
        meta["pages"] = doc.page_count
        txs: List[Dict[str, Any]] = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            # Try tables if available
            try:
                tables = page.find_tables()
                for t in tables.tables:
                    df = t.to_pandas()
                    txs.extend(_df_to_transactions(df))
            except Exception:
                pass
        if txs:
            meta["confidence"] = 0.78
            return ExtractionResult(rows=txs, meta=meta)
    except Exception as e:
        meta["pymupdf_error"] = str(e)

    # 4) OCR fallback
    try:
        from pdf2image import convert_from_path
        import pytesseract
        import cv2
        import numpy as np

        meta["engines_tried"].append("ocr:tesseract")
        images = convert_from_path(pdf_path, dpi=250)
        full_text = []
        for img in images:
            arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            # light denoise + threshold
            arr = cv2.GaussianBlur(arr, (3,3), 0)
            _, th = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            txt = pytesseract.image_to_string(th)
            full_text.append(txt)

        # Very rough OCR parsing: return text lines as descriptions.
        lines = []
        for block in full_text:
            for line in block.splitlines():
                l = line.strip()
                if len(l) < 6:
                    continue
                lines.append({"date": None, "description": l, "debit": None, "credit": None, "amount": None, "balance": None})
        if lines:
            meta["confidence"] = 0.55
            meta["note"] = "OCR fallback produced text lines; consider adding a review UI for these."
            return ExtractionResult(rows=lines, meta=meta)
    except Exception as e:
        meta["ocr_error"] = str(e)

    return ExtractionResult(rows=[], meta={**meta, "confidence": 0.0})
