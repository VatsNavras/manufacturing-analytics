# sheets.py - Google Sheets integration
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from functools import lru_cache

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

CREDENTIALS_SHEET_NAME = "Manufacturing_Data"
DATA_WORKSHEET_NAME = "Production"

def get_sheets_client():
    """Initialize and return authenticated Google Sheets client"""
    try:
        credentials_dict = st.secrets.get("google_credentials")
        
        if not credentials_dict:
            import json
            with open("credentials.json") as f:
                credentials_dict = json.load(f)
        
        creds = Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )
        return gspread.authorize(creds)
    
    except FileNotFoundError:
        st.error("credentials.json not found.")
        return None
    except Exception as e:
        st.error(f"Failed to authenticate: {e}")
        return None

@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    """Load manufacturing data from Google Sheets"""
    
    try:
        client = get_sheets_client()
        if not client:
            return create_sample_data()
        
        sheet = client.open(CREDENTIALS_SHEET_NAME)
        worksheet = sheet.worksheet(DATA_WORKSHEET_NAME)
        data = worksheet.get_all_values()
        
        if not data or len(data) < 2:
            st.warning("No data found. Using sample data.")
            return create_sample_data()
        
        headers = data[0]
        rows = data[1:]
        
        df = pd.DataFrame(rows, columns=headers)
        
        numeric_columns = [
            'Produced Qty', 'Order Qty', 'Per Item Price', 
            'CutWt', 'Cycle Time'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['Date'])
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        st.success(f"✓ Loaded {len(df)} records")
        
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return create_sample_data()

def create_sample_data() -> pd.DataFrame:
    """Create sample manufacturing data for testing"""
    
    import random
    from datetime import datetime, timedelta
    
    dates = pd.date_range(start='2024-01-01', periods=90, freq='D')
    
    modules = ['CNC Zone A', 'CNC Zone B', 'CNC Zone C']
    machines = ['Machine-01', 'Machine-02', 'Machine-03', 'Machine-04']
    operators = ['Operator-A', 'Operator-B', 'Operator-C', 'Operator-D', 'Operator-E']
    shifts = ['Morning', 'Afternoon', 'Night']
    
    data = []
    
    for date in dates:
        for shift in shifts:
            for module in modules:
                for machine in machines:
                    for operator in operators:
                        produced_qty = random.randint(50, 500)
                        order_qty = random.randint(300, 1000)
                        per_item_price = random.choice([100, 150, 200, 250, 300])
                        cut_wt = random.randint(100, 500)
                        cycle_time = random.randint(5, 30)
                        
                        data.append({
                            'Date': date,
                            'ModuleName': module,
                            'MachineName': machine,
                            'OperatorName': operator,
                            'Shift': shift,
                            'Produced Qty': produced_qty,
                            'Order Qty': order_qty,
                            'Per Item Price': per_item_price,
                            'CutWt': cut_wt,
                            'Cycle Time': cycle_time
                        })
    
    return pd.DataFrame(data)

def refresh_data():
    """Clear cached data and reload"""
    st.cache_data.clear()
    st.success("Data refreshed successfully!")

def export_to_csv(df: pd.DataFrame, filename: str = "production_data.csv"):
    """Export DataFrame to CSV"""
    return df.to_csv(index=False)