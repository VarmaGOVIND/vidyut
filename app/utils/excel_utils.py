import pandas as pd
from io import BytesIO
from flask import send_file
from datetime import datetime

def create_excel_from_data(data, columns, filename):
    df = pd.DataFrame(data, columns=columns)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    return send_file(output, download_name=filename, as_attachment=True)

def read_products_from_excel(file):
    df = pd.read_excel(file)
    required_columns = ['name', 'category', 'cost_price', 'selling_price', 'stock', 'min_stock']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df.to_dict('records')