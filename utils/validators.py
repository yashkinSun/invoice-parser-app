"""
Data validation and normalization utilities
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class DataValidator:
    """
    Validates and normalizes invoice data
    """
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """
        Validate date format (YYYY-MM-DD)
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def normalize_date(date_str: str) -> Optional[str]:
        """
        Try to normalize various date formats to YYYY-MM-DD
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Normalized date string or None if parsing fails
        """
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d-%m-%Y",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                continue
        
        return None
    
    @staticmethod
    def validate_inn(inn: str) -> bool:
        """
        Validate Russian INN (ИНН) format
        
        Args:
            inn: INN string to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not inn:
            return False
        
        # Remove spaces and non-digits
        inn = re.sub(r'\D', '', str(inn))
        
        # INN can be 10 or 12 digits
        return len(inn) in [10, 12]
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone string to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not phone:
            return False
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', str(phone))
        
        # Should have at least 10 digits
        return len(digits) >= 10
    
    @staticmethod
    def validate_number(value: Any) -> bool:
        """
        Check if value is a valid number
        
        Args:
            value: Value to check
            
        Returns:
            True if valid number, False otherwise
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def clean_number(value: Any) -> Optional[float]:
        """
        Clean and convert value to float
        
        Args:
            value: Value to clean
            
        Returns:
            Float value or None if conversion fails
        """
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            # Remove currency symbols, spaces, and other non-numeric characters
            cleaned = str(value).replace(' ', '').replace(',', '.').replace('₽', '').replace('руб', '').strip()
            
            # Remove any remaining non-numeric characters except dot and minus
            cleaned = re.sub(r'[^\d.-]', '', cleaned)
            
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def validate_invoice_data(data: Dict[str, Any]) -> List[str]:
        """
        Validate complete invoice data and return list of warnings
        
        Args:
            data: Invoice data dictionary
            
        Returns:
            List of validation warning messages
        """
        warnings = []
        
        # Check required fields
        required_fields = ['invoice_number', 'invoice_date', 'vendor_name', 'customer_name', 'total_amount']
        for field in required_fields:
            if field not in data or not data[field]:
                warnings.append(f"Missing required field: {field}")
        
        # Validate date
        if 'invoice_date' in data and data['invoice_date']:
            if not DataValidator.validate_date(data['invoice_date']):
                warnings.append(f"Invalid date format: {data['invoice_date']} (expected YYYY-MM-DD)")
        
        # Validate INNs
        if 'vendor_inn' in data and data['vendor_inn']:
            if not DataValidator.validate_inn(data['vendor_inn']):
                warnings.append(f"Invalid vendor INN format: {data['vendor_inn']}")
        
        if 'customer_inn' in data and data['customer_inn']:
            if not DataValidator.validate_inn(data['customer_inn']):
                warnings.append(f"Invalid customer INN format: {data['customer_inn']}")
        
        # Validate amounts
        if 'total_amount' in data:
            if not DataValidator.validate_number(data['total_amount']):
                warnings.append(f"Invalid total amount: {data['total_amount']}")
        
        # Validate line items
        if 'line_items' in data and isinstance(data['line_items'], list):
            for idx, item in enumerate(data['line_items']):
                if 'quantity' in item and not DataValidator.validate_number(item['quantity']):
                    warnings.append(f"Invalid quantity in line item {idx + 1}")
                if 'unit_price' in item and not DataValidator.validate_number(item['unit_price']):
                    warnings.append(f"Invalid unit price in line item {idx + 1}")
                if 'total_price' in item and not DataValidator.validate_number(item['total_price']):
                    warnings.append(f"Invalid total price in line item {idx + 1}")
        
        # Check confidence score
        if 'confidence_score' in data:
            score = data['confidence_score']
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                warnings.append(f"Invalid confidence score: {score} (expected 0-100)")
            elif score < 70:
                warnings.append(f"Low confidence score: {score}% - please review carefully")
        
        return warnings
