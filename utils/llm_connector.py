"""
LLM connector module for invoice parsing using OpenAI API
"""

import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from config.prompts import INVOICE_PARSER_SYSTEM_PROMPT


class LLMConnector:
    """
    Handles communication with OpenAI API for invoice parsing
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1-mini"):
        """
        Initialize LLM connector
        
        Args:
            api_key: OpenAI API key (if None, will use environment variable)
            model: Model to use for parsing
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
    
    def parse_invoice_text(self, text: str, retry_count: int = 2) -> Dict[str, Any]:
        """
        Parse invoice from extracted text
        
        Args:
            text: Extracted text from PDF
            retry_count: Number of retries on failure
            
        Returns:
            Parsed invoice data as dictionary
        """
        user_prompt = f"""Please extract all invoice information from the following text:

{text}

Remember to respond with valid JSON only."""

        return self._call_api(user_prompt, retry_count=retry_count)
    
    def parse_invoice_image(self, base64_image: str, retry_count: int = 2) -> Dict[str, Any]:
        """
        Parse invoice from image using Vision API
        
        Args:
            base64_image: Base64 encoded image
            retry_count: Number of retries on failure
            
        Returns:
            Parsed invoice data as dictionary
        """
        user_prompt = "Please extract all invoice information from this image. Remember to respond with valid JSON only."
        
        return self._call_api(user_prompt, image_base64=base64_image, retry_count=retry_count)
    
    def _call_api(self, user_prompt: str, image_base64: Optional[str] = None, 
                  retry_count: int = 2) -> Dict[str, Any]:
        """
        Internal method to call OpenAI API with retry logic
        
        Args:
            user_prompt: User prompt text
            image_base64: Optional base64 encoded image
            retry_count: Number of retries on failure
            
        Returns:
            Parsed response as dictionary
        """
        for attempt in range(retry_count + 1):
            try:
                # Prepare messages
                messages = [
                    {"role": "system", "content": INVOICE_PARSER_SYSTEM_PROMPT}
                ]
                
                # Add user message with or without image
                if image_base64:
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": user_prompt
                    })
                
                # Call API with JSON mode
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_tokens=4096
                )
                
                # Extract and parse JSON response
                content = response.choices[0].message.content
                parsed_data = json.loads(content)
                
                # Validate that we got the expected structure
                if not isinstance(parsed_data, dict):
                    raise ValueError("Response is not a valid JSON object")
                
                if "invoice_number" not in parsed_data:
                    raise ValueError("Response missing required field: invoice_number")
                
                return parsed_data
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response (attempt {attempt + 1}/{retry_count + 1}): {e}"
                if attempt == retry_count:
                    raise Exception(f"{error_msg}\nRaw response: {content if 'content' in locals() else 'N/A'}")
                print(error_msg)
                continue
                
            except Exception as e:
                error_msg = f"API call failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                if attempt == retry_count:
                    raise Exception(error_msg)
                print(error_msg)
                continue
        
        raise Exception("All retry attempts exhausted")
    
    def validate_and_normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize extracted data
        
        Args:
            data: Raw extracted data
            
        Returns:
            Validated and normalized data
        """
        # Ensure numeric fields are properly typed
        numeric_fields = ['subtotal', 'vat_amount', 'total_amount', 'vat_rate', 'confidence_score']
        
        for field in numeric_fields:
            if field in data and data[field] is not None:
                try:
                    # Remove any currency symbols, spaces, or commas
                    if isinstance(data[field], str):
                        cleaned = data[field].replace(' ', '').replace(',', '').replace('₽', '').replace('руб', '').strip()
                        data[field] = float(cleaned) if '.' in cleaned else int(cleaned)
                except (ValueError, AttributeError):
                    pass  # Keep original value if conversion fails
        
        # Normalize line items (handle both 'line_items' and 'items' keys)
        items_key = 'line_items' if 'line_items' in data else 'items' if 'items' in data else None
        
        if items_key and isinstance(data[items_key], list):
            # Normalize the key to 'line_items'
            if items_key == 'items':
                data['line_items'] = data.pop('items')
            
            for item in data['line_items']:
                for num_field in ['quantity', 'unit_price', 'total_price']:
                    if num_field in item and item[num_field] is not None:
                        try:
                            if isinstance(item[num_field], str):
                                cleaned = item[num_field].replace(' ', '').replace(',', '').replace('₽', '').replace('руб', '').strip()
                                item[num_field] = float(cleaned)
                        except (ValueError, AttributeError):
                            pass
        
        return data
