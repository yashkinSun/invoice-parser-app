"""
PDF processing module for invoice parsing
Handles both digital PDFs (text-based) and scanned PDFs (image-based)
"""

import io
import base64
from typing import Tuple, Optional
from pypdf import PdfReader
from pdf2image import convert_from_bytes
from PIL import Image


class PDFProcessor:
    """
    Processes PDF files and determines the best extraction strategy
    """
    
    # Threshold for text extraction - if less than this many characters, treat as scan
    TEXT_THRESHOLD = 50
    
    def __init__(self):
        pass
    
    @staticmethod
    def classify_pdf(pdf_bytes: bytes) -> str:
        """
        Classify PDF as either 'digital' (text-based) or 'scan' (image-based)
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            'digital' or 'scan'
        """
        try:
            # Try to extract text from first page
            reader = PdfReader(io.BytesIO(pdf_bytes))
            
            if len(reader.pages) == 0:
                return 'scan'
            
            # Extract text from first page
            first_page = reader.pages[0]
            text = first_page.extract_text()
            
            # Count meaningful characters (excluding whitespace)
            char_count = len(text.strip())
            
            # If we have enough text, it's a digital PDF
            if char_count >= PDFProcessor.TEXT_THRESHOLD:
                return 'digital'
            else:
                return 'scan'
                
        except Exception as e:
            # If text extraction fails, assume it's a scan
            print(f"Error during PDF classification: {e}")
            return 'scan'
    
    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        """
        Extract raw text from all pages of a digital PDF
        
        Args:
            pdf_bytes: PDF file content as bytes
            
        Returns:
            Extracted text as string
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}\n")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {e}")
    
    @staticmethod
    def convert_to_image(pdf_bytes: bytes, first_page_only: bool = True) -> list:
        """
        Convert PDF pages to images
        
        Args:
            pdf_bytes: PDF file content as bytes
            first_page_only: If True, convert only the first page
            
        Returns:
            List of PIL Image objects
        """
        try:
            # Convert PDF to images (300 DPI for good quality)
            if first_page_only:
                images = convert_from_bytes(pdf_bytes, dpi=300, first_page=1, last_page=1)
            else:
                images = convert_from_bytes(pdf_bytes, dpi=300)
            
            return images
            
        except Exception as e:
            raise Exception(f"Failed to convert PDF to image: {e}")
    
    @staticmethod
    def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
        """
        Convert PIL Image to base64 string for API transmission
        
        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)
            
        Returns:
            Base64 encoded string
        """
        try:
            buffer = io.BytesIO()
            image.save(buffer, format=format)
            buffer.seek(0)
            
            image_bytes = buffer.read()
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            return base64_string
            
        except Exception as e:
            raise Exception(f"Failed to convert image to base64: {e}")
    
    @staticmethod
    def process_file(file_bytes: bytes, file_type: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Main processing function that handles both PDF and image files
        
        Args:
            file_bytes: File content as bytes
            file_type: File extension (pdf, jpg, png, etc.)
            
        Returns:
            Tuple of (processing_type, text_content, base64_image)
            - processing_type: 'text' or 'vision'
            - text_content: Extracted text (if digital PDF) or None
            - base64_image: Base64 encoded image (if scan/image) or None
        """
        file_type = file_type.lower()
        
        # Handle image files directly
        if file_type in ['jpg', 'jpeg', 'png', 'webp']:
            try:
                image = Image.open(io.BytesIO(file_bytes))
                base64_image = PDFProcessor.image_to_base64(image)
                return ('vision', None, base64_image)
            except Exception as e:
                raise Exception(f"Failed to process image file: {e}")
        
        # Handle PDF files
        elif file_type == 'pdf':
            pdf_type = PDFProcessor.classify_pdf(file_bytes)
            
            if pdf_type == 'digital':
                # Extract text
                text = PDFProcessor.extract_text(file_bytes)
                return ('text', text, None)
            else:
                # Convert to image
                images = PDFProcessor.convert_to_image(file_bytes, first_page_only=True)
                if len(images) > 0:
                    base64_image = PDFProcessor.image_to_base64(images[0])
                    return ('vision', None, base64_image)
                else:
                    raise Exception("Failed to convert PDF to image: no pages found")
        
        else:
            raise Exception(f"Unsupported file type: {file_type}")
