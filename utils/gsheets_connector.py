"""
Google Sheets integration module
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Any, List, Optional
from datetime import datetime


class GoogleSheetsConnector:
    """
    Handles integration with Google Sheets API
    """
    
    # Google Sheets API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self, service_account_file: str):
        """
        Initialize Google Sheets connector
        
        Args:
            service_account_file: Path to service account JSON file
        """
        try:
            credentials = Credentials.from_service_account_file(
                service_account_file,
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(credentials)
            self.service_account_email = credentials.service_account_email
        except Exception as e:
            raise Exception(f"Failed to initialize Google Sheets connector: {e}")
    
    def get_service_account_email(self) -> str:
        """
        Get the service account email
        
        Returns:
            Service account email address
        """
        return self.service_account_email
    
    def open_spreadsheet(self, spreadsheet_id: str, worksheet_name: str = None):
        """
        Open a spreadsheet and optionally a specific worksheet
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            worksheet_name: Name of worksheet (if None, uses first sheet)
            
        Returns:
            Worksheet object
        """
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            if worksheet_name:
                try:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                except gspread.exceptions.WorksheetNotFound:
                    # Create worksheet if it doesn't exist
                    worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=30)
            else:
                worksheet = spreadsheet.sheet1
            
            return worksheet
            
        except gspread.exceptions.SpreadsheetNotFound:
            raise Exception(f"Spreadsheet not found. Please make sure the spreadsheet ID is correct and shared with {self.service_account_email}")
        except gspread.exceptions.APIError as e:
            raise Exception(f"Google Sheets API error: {e}")
        except Exception as e:
            raise Exception(f"Failed to open spreadsheet: {e}")
    
    def ensure_headers(self, worksheet, headers: List[str]):
        """
        Ensure the worksheet has proper headers
        
        Args:
            worksheet: Worksheet object
            headers: List of header names
        """
        try:
            # Check if first row exists and has content
            existing_headers = worksheet.row_values(1) if worksheet.row_count > 0 else []
            
            if not existing_headers or existing_headers == ['']:
                # No headers exist, create them
                worksheet.update('A1', [headers])
            elif existing_headers != headers:
                # Headers exist but are different - update them
                worksheet.update('A1', [headers])
                
        except Exception as e:
            raise Exception(f"Failed to ensure headers: {e}")
    
    def append_invoice_data(self, worksheet, invoice_data: Dict[str, Any]) -> int:
        """
        Append invoice data to the worksheet
        
        Args:
            worksheet: Worksheet object
            invoice_data: Parsed invoice data
            
        Returns:
            Row number where data was inserted
        """
        try:
            # Define headers
            headers = [
                'Timestamp',
                'Invoice Number',
                'Invoice Date',
                'Currency',
                'Vendor Name',
                'Vendor INN',
                'Vendor KPP',
                'Vendor Address',
                'Vendor Phone',
                'Vendor Bank',
                'Vendor BIK',
                'Vendor Account',
                'Customer Name',
                'Customer INN',
                'Customer KPP',
                'Customer Address',
                'Customer Phone',
                'Items Count',
                'Subtotal',
                'VAT Rate (%)',
                'VAT Amount',
                'Total Amount',
                'Confidence Score (%)',
                'Line Items (JSON)'
            ]
            
            # Ensure headers exist
            self.ensure_headers(worksheet, headers)
            
            # Prepare row data
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                invoice_data.get('invoice_number', ''),
                invoice_data.get('invoice_date', ''),
                invoice_data.get('currency', ''),
                invoice_data.get('vendor_name', ''),
                invoice_data.get('vendor_inn', ''),
                invoice_data.get('vendor_kpp', ''),
                invoice_data.get('vendor_address', ''),
                invoice_data.get('vendor_phone', ''),
                invoice_data.get('vendor_bank', ''),
                invoice_data.get('vendor_bik', ''),
                invoice_data.get('vendor_account', ''),
                invoice_data.get('customer_name', ''),
                invoice_data.get('customer_inn', ''),
                invoice_data.get('customer_kpp', ''),
                invoice_data.get('customer_address', ''),
                invoice_data.get('customer_phone', ''),
                len(invoice_data.get('line_items', [])),
                invoice_data.get('subtotal', ''),
                invoice_data.get('vat_rate', ''),
                invoice_data.get('vat_amount', ''),
                invoice_data.get('total_amount', ''),
                invoice_data.get('confidence_score', ''),
                str(invoice_data.get('line_items', []))
            ]
            
            # Append row
            worksheet.append_row(row, value_input_option='USER_ENTERED')
            
            # Return the row number
            return worksheet.row_count
            
        except gspread.exceptions.APIError as e:
            raise Exception(f"Google Sheets API error while appending data: {e}")
        except Exception as e:
            raise Exception(f"Failed to append invoice data: {e}")
    
    def append_line_items_separately(self, worksheet, invoice_data: Dict[str, Any]) -> int:
        """
        Append invoice with each line item as a separate row
        This is an alternative format where line items are expanded
        
        Args:
            worksheet: Worksheet object
            invoice_data: Parsed invoice data
            
        Returns:
            Number of rows inserted
        """
        try:
            # Define headers for line-item-per-row format
            headers = [
                'Timestamp',
                'Invoice Number',
                'Invoice Date',
                'Vendor Name',
                'Vendor INN',
                'Customer Name',
                'Customer INN',
                'Item Number',
                'Item Description',
                'Quantity',
                'Unit',
                'Unit Price',
                'Item Total',
                'Invoice Subtotal',
                'VAT Amount',
                'Invoice Total',
                'Currency'
            ]
            
            # Ensure headers exist
            self.ensure_headers(worksheet, headers)
            
            # Prepare common data
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            common_data = [
                timestamp,
                invoice_data.get('invoice_number', ''),
                invoice_data.get('invoice_date', ''),
                invoice_data.get('vendor_name', ''),
                invoice_data.get('vendor_inn', ''),
                invoice_data.get('customer_name', ''),
                invoice_data.get('customer_inn', '')
            ]
            
            # Prepare rows for each line item
            rows = []
            line_items = invoice_data.get('line_items', [])
            
            for item in line_items:
                row = common_data + [
                    item.get('item_number', ''),
                    item.get('description', ''),
                    item.get('quantity', ''),
                    item.get('unit', ''),
                    item.get('unit_price', ''),
                    item.get('total_price', ''),
                    invoice_data.get('subtotal', ''),
                    invoice_data.get('vat_amount', ''),
                    invoice_data.get('total_amount', ''),
                    invoice_data.get('currency', '')
                ]
                rows.append(row)
            
            # Append all rows at once
            if rows:
                worksheet.append_rows(rows, value_input_option='USER_ENTERED')
            
            return len(rows)
            
        except gspread.exceptions.APIError as e:
            raise Exception(f"Google Sheets API error while appending line items: {e}")
        except Exception as e:
            raise Exception(f"Failed to append line items: {e}")
    
    def test_connection(self, spreadsheet_id: str) -> bool:
        """
        Test connection to a spreadsheet
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            return True
        except Exception:
            return False
