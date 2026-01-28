"""
Data Parser Service
Handles parsing of CSV, XLSX, and JSON files into pandas DataFrames
"""

import io
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import numpy as np

from models.schemas import DataProfile, ColumnInfo


class DataParser:
    """Unified data parser for multiple file formats"""
    
    SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json'}
    
    @classmethod
    def parse(cls, file_content: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
        """
        Parse file content into a pandas DataFrame
        
        Args:
            file_content: Raw file bytes
            filename: Original filename (used to detect format)
            
        Returns:
            Tuple of (DataFrame, detected_file_type)
        """
        ext = Path(filename).suffix.lower()
        
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {ext}. Supported: {cls.SUPPORTED_EXTENSIONS}")
        
        if ext == '.csv':
            return cls._parse_csv(file_content), 'csv'
        elif ext in {'.xlsx', '.xls'}:
            return cls._parse_excel(file_content), 'excel'
        elif ext == '.json':
            return cls._parse_json(file_content), 'json'
        
        raise ValueError(f"Unable to parse file: {filename}")
    
    @classmethod
    def _parse_csv(cls, content: bytes) -> pd.DataFrame:
        """Parse CSV with auto-detection of encoding and delimiter"""
        # Try common encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Unable to decode CSV file. Unsupported encoding.")
        
        # Try to detect delimiter
        delimiters = [',', ';', '\t', '|']
        best_delimiter = ','
        max_columns = 0
        
        first_line = text.split('\n')[0] if '\n' in text else text
        for delim in delimiters:
            col_count = len(first_line.split(delim))
            if col_count > max_columns:
                max_columns = col_count
                best_delimiter = delim
        
        # Parse with detected settings
        df = pd.read_csv(
            io.StringIO(text),
            delimiter=best_delimiter,
            on_bad_lines='warn',
            low_memory=False
        )
        
        return cls._clean_column_names(df)
    
    @classmethod
    def _parse_excel(cls, content: bytes) -> pd.DataFrame:
        """Parse Excel file (first sheet)"""
        df = pd.read_excel(
            io.BytesIO(content),
            engine='openpyxl'
        )
        return cls._clean_column_names(df)
    
    @classmethod
    def _parse_json(cls, content: bytes) -> pd.DataFrame:
        """Parse JSON file (handles arrays and objects)"""
        try:
            data = json.loads(content.decode('utf-8'))
        except UnicodeDecodeError:
            data = json.loads(content.decode('latin-1'))
        
        # Handle different JSON structures
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Check if it's a dict of arrays (column-oriented)
            if all(isinstance(v, list) for v in data.values()):
                df = pd.DataFrame(data)
            # Check for nested 'data' or 'records' key
            elif 'data' in data and isinstance(data['data'], list):
                df = pd.DataFrame(data['data'])
            elif 'records' in data and isinstance(data['records'], list):
                df = pd.DataFrame(data['records'])
            else:
                # Single record, wrap in list
                df = pd.DataFrame([data])
        else:
            raise ValueError("JSON must be an array or object")
        
        return cls._clean_column_names(df)
    
    @staticmethod
    def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names"""
        # Remove leading/trailing whitespace
        df.columns = df.columns.str.strip()
        # Replace spaces and special chars with underscores
        df.columns = df.columns.str.replace(r'[^\w]', '_', regex=True)
        # Remove consecutive underscores
        df.columns = df.columns.str.replace(r'_+', '_', regex=True)
        # Remove leading/trailing underscores
        df.columns = df.columns.str.strip('_')
        # Make lowercase for consistency
        df.columns = df.columns.str.lower()
        
        return df
    
    @classmethod
    def profile(cls, df: pd.DataFrame) -> DataProfile:
        """
        Generate a comprehensive profile of the DataFrame
        
        Args:
            df: pandas DataFrame to profile
            
        Returns:
            DataProfile with column statistics
        """
        columns = []
        
        for col in df.columns:
            series = df[col]
            null_count = series.isna().sum()
            non_null = len(series) - null_count
            
            # Get sample values (up to 5 non-null unique values)
            unique_vals = series.dropna().unique()
            samples = [cls._serialize_value(v) for v in unique_vals[:5]]
            
            col_info = ColumnInfo(
                name=col,
                dtype=str(series.dtype),
                non_null_count=non_null,
                null_count=int(null_count),
                null_percentage=round((null_count / len(series)) * 100, 2) if len(series) > 0 else 0,
                unique_count=int(series.nunique()),
                sample_values=samples
            )
            columns.append(col_info)
        
        # Calculate memory usage in MB
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        return DataProfile(
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
            memory_usage_mb=round(memory_mb, 3)
        )
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Convert numpy/pandas types to JSON-serializable Python types"""
        if pd.isna(value):
            return None
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        if isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, (np.ndarray, pd.Series)):
            return value.tolist()
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        return str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value
    
    @classmethod
    def to_preview(cls, df: pd.DataFrame, rows: int = 10) -> List[Dict[str, Any]]:
        """Convert DataFrame to list of dicts for JSON response"""
        preview_df = df.head(rows).copy()
        
        # Replace NaN with None for JSON serialization
        preview_df = preview_df.where(pd.notnull(preview_df), None)
        
        records = []
        for _, row in preview_df.iterrows():
            record = {}
            for col in preview_df.columns:
                record[col] = cls._serialize_value(row[col])
            records.append(record)
        
        return records
