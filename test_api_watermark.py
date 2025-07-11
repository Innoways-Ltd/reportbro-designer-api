#!/usr/bin/env python3
"""
Test API call for watermark functionality
"""
import requests
import json

def test_api_watermark():
    """Test watermark functionality via API"""
    
    # Sample report definition with watermark text
    report_definition = {
        "docElements": [
            {
                "elementType": "watermark_text",
                "id": 129,
                "containerId": "0_watermark_texts",
                "x": 200,
                "y": 400,
                "width": 200,
                "height": 50,
                "content": "SAMPLE WATERMARK",
                "bold": True,
                "italic": True,
                "underline": True,
                "font": "helvetica",
                "fontSize": 24,
                "opacity": 50,
                "rotateDeg": 45,
                "showInForeground": False,
                "textColor": "#FF0000",
                "horizontalAlignment": "center",
                "verticalAlignment": "middle"
            },
            {
                "elementType": "text",
                "id": 1,
                "containerId": "0_content",
                "x": 50,
                "y": 100,
                "width": 400,
                "height": 50,
                "content": "This is a test document with API watermark",
                "font": "helvetica",
                "fontSize": 14,
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "textColor": "#000000",
                "backgroundColor": "",
                "bold": False,
                "italic": False,
                "underline": False,
                "strikethrough": False
            }
        ],
        "parameters": [],
        "styles": [],
        "documentProperties": {
            "pageFormat": "a4",
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
        },
        "version": 5
    }
    
    # API request payload
    payload = {
        "output_format": "pdf",
        "report": report_definition,
        "data": {},
        "is_test_data": True
    }
    
    try:
        # Make API call to generate preview
        response = requests.put(
            "http://127.0.0.1:8000/api/templates/review/generate/download",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"   Response: {result}")
            
            # Check if the response has the expected structure
            if 'data' in result and 'downloadKey' in result['data']:
                print(f"   Download key: {result['data']['downloadKey']}")
                print(f"   Download URL: {result['data']['downloadUrl']}")
                
                # Test the download URL
                download_response = requests.get(result['data']['downloadUrl'])
                if download_response.status_code == 200:
                    print(f"✅ PDF download successful: {len(download_response.content)} bytes")
                    
                    # Save the PDF
                    with open("/tmp/api_test_watermark.pdf", "wb") as f:
                        f.write(download_response.content)
                    print("✅ API test PDF saved to /tmp/api_test_watermark.pdf")
                    
                    return True
                else:
                    print(f"❌ Download failed: {download_response.status_code}")
                    return False
            else:
                print("❌ Unexpected response structure")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing watermark functionality via API...")
    success = test_api_watermark()
    if success:
        print("🎉 API test passed!")
    else:
        print("💥 API test failed!")
