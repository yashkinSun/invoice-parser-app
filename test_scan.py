"""
Test script for scan/image processing
"""

import os
from utils.pdf_processor import PDFProcessor
from utils.llm_connector import LLMConnector
from utils.validators import DataValidator
import json

def test_scan_processing():
    """Test processing of a scanned invoice image"""
    
    scan_path = "/home/ubuntu/invoice-parser/sample_invoices/invoice_scan_test.jpg"
    
    print(f"\n{'='*80}")
    print(f"Testing SCAN/IMAGE Processing: {os.path.basename(scan_path)}")
    print(f"{'='*80}\n")
    
    try:
        # Read file
        with open(scan_path, 'rb') as f:
            file_bytes = f.read()
        
        file_type = 'jpg'
        
        # Step 1: Process file
        print("Step 1: Processing image file...")
        processor = PDFProcessor()
        processing_type, text_content, image_base64 = processor.process_file(file_bytes, file_type)
        
        print(f"✓ File classified as: {processing_type}")
        print(f"✓ Image converted to base64: {len(image_base64)} characters")
        
        # Step 2: Parse with AI Vision
        print("\nStep 2: Parsing with AI Vision...")
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("✗ OPENAI_API_KEY not found in environment")
            return False
        
        llm = LLMConnector(api_key=api_key, model="gpt-4.1-mini")
        parsed_data = llm.parse_invoice_image(image_base64)
        
        print(f"✓ Data parsed successfully using Vision API")
        
        # Step 3: Validate and normalize
        print("\nStep 3: Validating and normalizing...")
        parsed_data = llm.validate_and_normalize(parsed_data)
        
        warnings = DataValidator.validate_invoice_data(parsed_data)
        
        if warnings:
            print(f"⚠ Found {len(warnings)} warnings:")
            for warning in warnings:
                print(f"  • {warning}")
        else:
            print("✓ All validations passed")
        
        # Display results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        
        print(f"\nInvoice Number: {parsed_data.get('invoice_number')}")
        print(f"Date: {parsed_data.get('invoice_date')}")
        print(f"Vendor: {parsed_data.get('vendor_name')}")
        print(f"Customer: {parsed_data.get('customer_name')}")
        print(f"Total Amount: {parsed_data.get('total_amount')} {parsed_data.get('currency')}")
        print(f"Line Items: {len(parsed_data.get('line_items', []))}")
        print(f"Confidence: {parsed_data.get('confidence_score')}%")
        
        # Save results
        output_file = scan_path.replace('.jpg', '_parsed.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        print("\n✓ SCAN PROCESSING TEST PASSED")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_scan_processing()
