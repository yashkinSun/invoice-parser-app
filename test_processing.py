"""
Test script for invoice processing modules
"""

import os
import sys
from utils.pdf_processor import PDFProcessor
from utils.llm_connector import LLMConnector
from utils.validators import DataValidator
import json

def test_invoice_processing(invoice_path: str):
    """Test processing of a single invoice"""
    
    print(f"\n{'='*80}")
    print(f"Testing: {os.path.basename(invoice_path)}")
    print(f"{'='*80}\n")
    
    try:
        # Read file
        with open(invoice_path, 'rb') as f:
            file_bytes = f.read()
        
        file_type = invoice_path.split('.')[-1].lower()
        
        # Step 1: Process file
        print("Step 1: Processing file...")
        processor = PDFProcessor()
        processing_type, text_content, image_base64 = processor.process_file(file_bytes, file_type)
        
        print(f"✓ File classified as: {processing_type}")
        if processing_type == 'text':
            print(f"✓ Extracted text length: {len(text_content)} characters")
        else:
            print(f"✓ Image converted to base64: {len(image_base64)} characters")
        
        # Step 2: Parse with AI
        print("\nStep 2: Parsing with AI...")
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("✗ OPENAI_API_KEY not found in environment")
            return False
        
        llm = LLMConnector(api_key=api_key, model="gpt-4.1-mini")
        
        if processing_type == 'text':
            parsed_data = llm.parse_invoice_text(text_content)
        else:
            parsed_data = llm.parse_invoice_image(image_base64)
        
        print(f"✓ Data parsed successfully")
        
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
        output_file = invoice_path.replace('.pdf', '_parsed.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test all sample invoices
    sample_dir = "/home/ubuntu/invoice-parser/sample_invoices"
    
    if not os.path.exists(sample_dir):
        print(f"Sample directory not found: {sample_dir}")
        sys.exit(1)
    
    invoices = [f for f in os.listdir(sample_dir) if f.endswith('.pdf')]
    
    if not invoices:
        print("No PDF files found in sample directory")
        sys.exit(1)
    
    print(f"\nFound {len(invoices)} invoices to test\n")
    
    results = {}
    for invoice in invoices:
        invoice_path = os.path.join(sample_dir, invoice)
        success = test_invoice_processing(invoice_path)
        results[invoice] = success
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for invoice, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {invoice}")
    
    total = len(results)
    passed = sum(1 for s in results.values() if s)
    print(f"\nTotal: {passed}/{total} passed")
