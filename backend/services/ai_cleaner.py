"""
AI Cleaner Service
LangChain + Pandas-powered intelligent data cleaning agent (Google Gemini)
"""

import os
import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

import pandas as pd
import numpy as np
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from models.schemas import CleaningReport, CleaningAction


class CleaningDecision(BaseModel):
    """LLM output for cleaning decisions"""
    column: str = Field(description="Column name")
    action: str = Field(description="Action to take: 'impute_mean', 'impute_median', 'impute_mode', 'drop_rows', 'drop_column', 'convert_type', 'standardize_dates', 'fix_currency', 'none'")
    reason: str = Field(description="Reason for this decision")


class CleaningPlan(BaseModel):
    """Full cleaning plan from LLM"""
    decisions: List[CleaningDecision] = Field(description="List of cleaning decisions")
    summary: str = Field(description="Summary of data quality issues")


class AIDataCleaner:
    """
    Intelligent data cleaning using LangChain and pandas (Google Gemini)
    
    Cleaning capabilities:
    - Missing value handling (imputation based on data type and distribution)
    - Date format standardization
    - Currency string to float conversion
    - Type inference and correction
    - Outlier detection (informational, not auto-removed)
    """
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize the cleaner
        
        Args:
            use_llm: If True, use LLM for intelligent decisions. If False, use rule-based only.
        """
        self.use_llm = use_llm and bool(os.getenv("GOOGLE_API_KEY"))
        
        if self.use_llm:
            self.llm = ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-pro"),
                temperature=0.1,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        else:
            self.llm = None
    
    def clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        Clean the DataFrame using AI-powered decisions
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (cleaned DataFrame, cleaning report)
        """
        cleaned_df = df.copy()
        actions: List[CleaningAction] = []
        issues: List[str] = []
        recommendations: List[str] = []
        
        rows_before = len(cleaned_df)
        cols_before = len(cleaned_df.columns)
        
        # Step 1: Profile the data and detect issues
        profile = self._profile_for_cleaning(cleaned_df)
        
        # Step 2: Get cleaning plan (from LLM or rules)
        if self.use_llm:
            plan = self._get_llm_cleaning_plan(cleaned_df, profile)
        else:
            plan = self._get_rule_based_plan(cleaned_df, profile)
        
        issues = self._extract_issues(profile)
        
        # Step 3: Execute cleaning actions
        for decision in plan:
            action_result = self._execute_action(cleaned_df, decision)
            if action_result:
                cleaned_df, action = action_result
                actions.append(action)
        
        # Step 4: Final cleanup
        # Remove completely empty rows
        empty_rows = cleaned_df.isna().all(axis=1).sum()
        if empty_rows > 0:
            cleaned_df = cleaned_df.dropna(how='all')
            actions.append(CleaningAction(
                column="*",
                action="drop_empty_rows",
                details=f"Removed {empty_rows} completely empty rows",
                rows_affected=int(empty_rows)
            ))
        
        # Remove duplicate rows
        dupes = cleaned_df.duplicated().sum()
        if dupes > 0:
            cleaned_df = cleaned_df.drop_duplicates()
            actions.append(CleaningAction(
                column="*",
                action="remove_duplicates",
                details=f"Removed {dupes} duplicate rows",
                rows_affected=int(dupes)
            ))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(cleaned_df, profile)
        
        report = CleaningReport(
            total_actions=len(actions),
            actions=actions,
            rows_before=rows_before,
            rows_after=len(cleaned_df),
            columns_before=cols_before,
            columns_after=len(cleaned_df.columns),
            issues_detected=issues,
            recommendations=recommendations
        )
        
        return cleaned_df, report
    
    def _profile_for_cleaning(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Generate detailed profile for cleaning decisions"""
        profile = {}
        
        for col in df.columns:
            series = df[col]
            null_pct = (series.isna().sum() / len(series)) * 100
            
            # Detect potential type
            inferred_type = self._infer_type(series)
            
            # Check for date patterns
            is_date = self._looks_like_date(series)
            
            # Check for currency patterns
            is_currency = self._looks_like_currency(series)
            
            profile[col] = {
                "dtype": str(series.dtype),
                "null_percentage": round(null_pct, 2),
                "unique_count": series.nunique(),
                "unique_ratio": series.nunique() / len(series) if len(series) > 0 else 0,
                "inferred_type": inferred_type,
                "is_date": is_date,
                "is_currency": is_currency,
                "sample_values": series.dropna().head(3).tolist()
            }
        
        return profile
    
    def _infer_type(self, series: pd.Series) -> str:
        """Infer the semantic type of a column"""
        if series.dtype in ['int64', 'float64']:
            return 'numeric'
        
        # Check object columns
        non_null = series.dropna()
        if len(non_null) == 0:
            return 'unknown'
        
        # Sample for efficiency
        sample = non_null.head(100)
        
        # Check if numeric strings
        try:
            pd.to_numeric(sample.str.replace(r'[$,€£¥]', '', regex=True).str.strip())
            return 'numeric_string'
        except:
            pass
        
        # Check if dates
        try:
            pd.to_datetime(sample, infer_datetime_format=True)
            return 'datetime'
        except:
            pass
        
        # Check if boolean-like
        bool_values = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'}
        if set(sample.str.lower().unique()).issubset(bool_values):
            return 'boolean'
        
        return 'categorical' if series.nunique() / len(series) < 0.5 else 'text'
    
    def _looks_like_date(self, series: pd.Series) -> bool:
        """Check if column looks like dates"""
        if series.dtype == 'datetime64[ns]':
            return True
        
        sample = series.dropna().head(20)
        if len(sample) == 0:
            return False
        
        # Common date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO
            r'\d{2}/\d{2}/\d{4}',  # US
            r'\d{2}-\d{2}-\d{4}',  # EU
            r'\d{2}\.\d{2}\.\d{4}',  # German
        ]
        
        try:
            sample_str = sample.astype(str)
            for pattern in date_patterns:
                if sample_str.str.match(pattern).mean() > 0.8:
                    return True
        except:
            pass
        
        return False
    
    def _looks_like_currency(self, series: pd.Series) -> bool:
        """Check if column looks like currency values"""
        sample = series.dropna().head(50).astype(str)
        currency_pattern = r'^[$€£¥₹]?\s*[\d,]+\.?\d*$|^\d+\.?\d*\s*[$€£¥₹]?$'
        return sample.str.match(currency_pattern).mean() > 0.7
    
    def _get_llm_cleaning_plan(self, df: pd.DataFrame, profile: Dict) -> List[Dict]:
        """Get cleaning recommendations from LLM"""
        parser = PydanticOutputParser(pydantic_object=CleaningPlan)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data cleaning expert. Analyze the data profile and recommend cleaning actions.
            
Be conservative - only recommend actions that are clearly beneficial. For each column with issues, decide:
- impute_mean: For numeric columns with <30% missing, normal distribution
- impute_median: For numeric columns with outliers or skewed distribution  
- impute_mode: For categorical columns with <50% missing
- drop_rows: If a critical column has very few missing values (<5%)
- drop_column: If >70% missing or column is useless
- convert_type: If type needs correction (e.g., object to numeric)
- standardize_dates: If dates are in inconsistent formats
- fix_currency: If currency strings need to be converted to floats
- none: If no action needed

{format_instructions}"""),
            ("user", """Data Profile:
Rows: {row_count}
Columns: {col_count}

Column Details:
{profile_text}

What cleaning actions are needed?""")
        ])
        
        profile_text = "\n".join([
            f"- {col}: dtype={info['dtype']}, null%={info['null_percentage']}, " +
            f"inferred={info['inferred_type']}, is_date={info['is_date']}, is_currency={info['is_currency']}"
            for col, info in profile.items()
        ])
        
        try:
            chain = prompt | self.llm | parser
            result = chain.invoke({
                "row_count": len(df),
                "col_count": len(df.columns),
                "profile_text": profile_text,
                "format_instructions": parser.get_format_instructions()
            })
            
            return [{"column": d.column, "action": d.action, "reason": d.reason} 
                    for d in result.decisions if d.action != "none"]
        except Exception as e:
            print(f"LLM cleaning plan failed: {e}, falling back to rules")
            return self._get_rule_based_plan(df, profile)
    
    def _get_rule_based_plan(self, df: pd.DataFrame, profile: Dict) -> List[Dict]:
        """Generate cleaning plan using rules"""
        plan = []
        
        for col, info in profile.items():
            # Handle missing values
            if info['null_percentage'] > 0:
                if info['null_percentage'] > 70:
                    plan.append({
                        "column": col,
                        "action": "drop_column",
                        "reason": f"Column has {info['null_percentage']}% missing values"
                    })
                elif info['inferred_type'] in ['numeric', 'numeric_string']:
                    plan.append({
                        "column": col,
                        "action": "impute_median",
                        "reason": f"Numeric column with {info['null_percentage']}% missing"
                    })
                elif info['inferred_type'] in ['categorical', 'boolean']:
                    plan.append({
                        "column": col, 
                        "action": "impute_mode",
                        "reason": f"Categorical column with {info['null_percentage']}% missing"
                    })
            
            # Type corrections
            if info['is_currency'] and info['dtype'] == 'object':
                plan.append({
                    "column": col,
                    "action": "fix_currency",
                    "reason": "Currency strings detected"
                })
            elif info['is_date'] and info['dtype'] == 'object':
                plan.append({
                    "column": col,
                    "action": "standardize_dates",
                    "reason": "Date strings detected"
                })
            elif info['inferred_type'] == 'numeric_string':
                plan.append({
                    "column": col,
                    "action": "convert_type",
                    "reason": "Numeric values stored as strings"
                })
        
        return plan
    
    def _execute_action(self, df: pd.DataFrame, decision: Dict) -> Optional[Tuple[pd.DataFrame, CleaningAction]]:
        """Execute a single cleaning action"""
        col = decision["column"]
        action = decision["action"]
        
        if col not in df.columns and action != "drop_column":
            return None
        
        rows_affected = 0
        details = ""
        
        try:
            if action == "impute_mean":
                if df[col].dtype in ['int64', 'float64']:
                    null_count = df[col].isna().sum()
                    mean_val = df[col].mean()
                    df[col] = df[col].fillna(mean_val)
                    rows_affected = int(null_count)
                    details = f"Filled {null_count} missing values with mean ({mean_val:.2f})"
            
            elif action == "impute_median":
                null_count = df[col].isna().sum()
                # Convert to numeric first if needed
                if df[col].dtype == 'object':
                    df[col] = pd.to_numeric(df[col].str.replace(r'[,$€£¥]', '', regex=True), errors='coerce')
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                rows_affected = int(null_count)
                details = f"Filled {null_count} missing values with median ({median_val:.2f})"
            
            elif action == "impute_mode":
                null_count = df[col].isna().sum()
                mode_val = df[col].mode().iloc[0] if len(df[col].mode()) > 0 else "Unknown"
                df[col] = df[col].fillna(mode_val)
                rows_affected = int(null_count)
                details = f"Filled {null_count} missing values with mode ({mode_val})"
            
            elif action == "drop_column":
                df = df.drop(columns=[col])
                details = f"Dropped column due to poor data quality"
                rows_affected = 0
            
            elif action == "drop_rows":
                null_count = df[col].isna().sum()
                df = df.dropna(subset=[col])
                rows_affected = int(null_count)
                details = f"Dropped {null_count} rows with missing values"
            
            elif action == "convert_type":
                original_nulls = df[col].isna().sum()
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[,$]', '', regex=True), errors='coerce')
                new_nulls = df[col].isna().sum() - original_nulls
                rows_affected = int(abs(new_nulls))
                details = f"Converted to numeric type"
            
            elif action == "standardize_dates":
                df[col] = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
                rows_affected = int((~df[col].isna()).sum())
                details = f"Standardized {rows_affected} date values to ISO format"
            
            elif action == "fix_currency":
                # Remove currency symbols and convert to float
                df[col] = df[col].astype(str).str.replace(r'[$€£¥₹,]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                rows_affected = int((~df[col].isna()).sum())
                details = f"Converted {rows_affected} currency values to numeric"
            
            else:
                return None
            
            return df, CleaningAction(
                column=col,
                action=action,
                details=details,
                rows_affected=rows_affected
            )
            
        except Exception as e:
            print(f"Action {action} on {col} failed: {e}")
            return None
    
    def _extract_issues(self, profile: Dict) -> List[str]:
        """Extract list of detected issues"""
        issues = []
        
        for col, info in profile.items():
            if info['null_percentage'] > 20:
                issues.append(f"{col}: {info['null_percentage']}% missing values")
            if info['is_currency'] and info['dtype'] == 'object':
                issues.append(f"{col}: Currency values stored as text")
            if info['is_date'] and info['dtype'] == 'object':
                issues.append(f"{col}: Dates stored as text strings")
        
        return issues[:10]  # Limit to top 10
    
    def _generate_recommendations(self, df: pd.DataFrame, profile: Dict) -> List[str]:
        """Generate post-cleaning recommendations"""
        recs = []
        
        # Check for remaining issues
        for col in df.columns:
            null_pct = (df[col].isna().sum() / len(df)) * 100
            if null_pct > 0:
                recs.append(f"Column '{col}' still has {null_pct:.1f}% missing values - consider manual review")
        
        # Check for potential outliers in numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = ((df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)).sum()
            if outliers > 0:
                recs.append(f"Column '{col}' has {outliers} potential outliers")
        
        return recs[:5]  # Limit recommendations
