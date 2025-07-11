#!/usr/bin/env python3

import requests
import json

def test_api_mixed_watermarks():
    print("🧪 Testing mixed text and image watermarks via API...")
    
    # Report definition with both text and image watermarks
    report_definition = {
        "docElements": [
            {
                "id": 1,
                "containerId": "0_content",
                "elementType": "text",
                "x": 62,
                "y": 80,
                "width": 400,
                "height": 20,
                "content": "Document with both text and image watermarks",
                "eval": False,
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "font": "helvetica",
                "fontSize": 16,
                "bold": True,
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
                "elementType": "watermark_text",
                "id": 129,
                "x": 200,
                "y": 600,
                "width": 250,
                "height": 80,
                "content": "CONFIDENTIAL",
                "eval": False,
                "rotateDeg": 45,
                "opacity": 25,
                "showInForeground": False,
                "styleId": "",
                "bold": True,
                "italic": False,
                "underline": False,
                "strikethrough": False,
                "horizontalAlignment": "center",
                "verticalAlignment": "middle",
                "textColor": "#FF0000",
                "backgroundColor": "",
                "font": "helvetica",
                "fontSize": "36",
                "lineSpacing": 1,
                "borderColor": "#000000",
                "borderWidth": 1,
                "borderAll": False,
                "borderLeft": False,
                "borderTop": False,
                "borderRight": False,
                "borderBottom": False,
                "paddingLeft": 2,
                "paddingTop": 2,
                "paddingRight": 2,
                "paddingBottom": 2,
                "printIf": ""
            },
            {
                "elementType": "watermark_image",
                "id": 130,
                "x": 100,
                "y": 300,
                "width": 80,
                "height": 80,
                "source": "",
                "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "eval": False,
                "rotateDeg": 15,
                "opacity": 40,
                "showInForeground": True,
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
            content_type = response.headers.get('content-type', '')
            if 'text/plain' in content_type:
                download_key = response.text.strip()
                print(f"✅ Download key received: {download_key}")
                
                download_url = f"http://127.0.0.1:8000/api/templates/review/generate?key={download_key}"
                download_response = requests.get(download_url)
                
                if download_response.status_code == 200:
                    pdf_data = download_response.content
                    print(f"✅ PDF download successful: {len(pdf_data)} bytes")
                    
                    # Save to temp file for verification
                    with open('/tmp/api_test_mixed_watermarks.pdf', 'wb') as f:
                        f.write(pdf_data)
                    print("✅ API test PDF with mixed watermarks saved to /tmp/api_test_mixed_watermarks.pdf")
                    print("🎉 Mixed watermarks API test passed!")
                    return True
                else:
                    print(f"❌ Failed to download PDF: {download_response.status_code}")
                    return False
            else:
                print(f"❌ Unexpected content type: {content_type}")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_mixed_watermarks()
    exit(0 if success else 1)
