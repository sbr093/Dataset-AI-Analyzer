import os
from typing import List, Optional

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".json", ".jsonl"}


def load_dataframe(
    file_path: str,
    columns: Optional[List[str]] = None,
    nrows: Optional[int] = None,
) -> pd.DataFrame:
    """Read a supported dataset file (CSV, TSV, Excel, JSON/JSONL) into a DataFrame.

    `columns` and `nrows` are applied natively where the underlying pandas
    reader supports it (CSV/TSV/Excel); for JSON, which has no native
    column/row pushdown, the file is read in full and then sliced.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        return pd.read_csv(file_path, usecols=columns, nrows=nrows, low_memory=False)
    if ext == ".tsv":
        return pd.read_csv(file_path, sep="\t", usecols=columns, nrows=nrows, low_memory=False)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path, usecols=columns, nrows=nrows)
    if ext in (".json", ".jsonl"):
        df = pd.read_json(file_path, lines=(ext == ".jsonl"))
        if columns:
            df = df[columns]
        if nrows is not None:
            df = df.head(nrows)
        return df

    raise ValueError(
        f"Unsupported file type '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )
