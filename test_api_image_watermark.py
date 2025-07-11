#!/usr/bin/env python3

import requests
import json

def test_api_image_watermark():
    print("🧪 Testing image watermark functionality via API...")
    
    # Report definition with image watermark
    report_definition = {
        "docElements": [
            {
                "id": 1,
                "containerId": "0_content",
                "elementType": "text",
                "x": 62,
                "y": 80,
                "width": 120,
                "height": 20,
                "content": "API Test with Image Watermark",
                "eval": False,
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "font": "helvetica",
                "fontSize": 14,
                "bold": False,
                "italic": False,
                "underline": False,
                "strikethrough": False,
                "textColor": "#000000"
            }
        ],
        "parameters": [],
        "styles": [],
        "watermarks": [
            {
                "elementType": "watermark_image",
                "id": 130,
                "x": 400,
                "y": 400,
                "width": 100,
                "height": 100,
                "source": "",
                "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "eval": False,
                "rotateDeg": 30,
                "opacity": 50,
                "showInForeground": False,
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "backgroundColor": "",
                "printIf": ""
            }
        ],
        "version": 5,
        "documentProperties": {
            "pageFormat": "A4",
            "orientation": "portrait",
            "unit": "mm",
            "marginLeft": 20,
            "marginTop": 20,
            "marginRight": 20,
            "marginBottom": 20,
            "header": False,
            "footer": False,
            "patternLocale": "en",
            "patternCurrencySymbol": "$"
        }
    }

    data = {}

    # API endpoint
    url = "http://127.0.0.1:8000/api/templates/review/generate"
    
    payload = {
        "report": report_definition,
        "data": data,
        "is_test_data": False
    }
    
    try:
        response = requests.put(url, json=payload)
        
        if response.status_code == 200:
            # Check if the response is JSON or binary data
            content_type = response.headers.get('content-type', '')
            if 'text/plain' in content_type:
                # Response is a download key
                download_key = response.text.strip()
                print(f"✅ Download key received: {download_key}")
                
                # Use the GET endpoint to download the PDF
                download_url = f"http://127.0.0.1:8000/api/templates/review/generate?key={download_key}"
                download_response = requests.get(download_url)
                
                if download_response.status_code == 200:
                    pdf_data = download_response.content
                    print(f"✅ PDF download successful: {len(pdf_data)} bytes")
                    
                    # Save to temp file for verification
                    with open('/tmp/api_test_image_watermark.pdf', 'wb') as f:
                        f.write(pdf_data)
                    print("✅ API test PDF with image watermark saved to /tmp/api_test_image_watermark.pdf")
                    print("🎉 API image watermark test passed!")
                    return True
                else:
                    print(f"❌ Failed to download PDF: {download_response.status_code}")
                    print(f"   Response: {download_response.text}")
                    return False
            else:
                print(f"❌ Unexpected content type: {content_type}")
                print(f"   Response: {response.text[:200]}...")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_image_watermark()
    exit(0 if success else 1)
