#!/usr/bin/env python3
"""
Test script to verify complex parameter-based imageUrl resolution scenarios.
"""

import json
import requests

# Test payload with multiple scenarios
test_payload = {
    "report": {
        "docElements": [
            {
                "elementType": "image",
                "id": 1,
                "containerId": "0_header",
                "x": 10,
                "y": 10,
                "width": 100,
                "height": 50,
                "source": "",
                "image": "",
                "imageFilename": "company_logo.png",
                "imageUrl": "${branding.company_logo}",  # Simple parameter reference
                "styleId": "",
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "backgroundColor": "",
                "printIf": "",
                "removeEmptyElement": False,
                "link": "",
                "spreadsheet_hide": True,
                "spreadsheet_column": "",
                "spreadsheet_addEmptyRow": False
            },
            {
                "elementType": "image",
                "id": 2,
                "containerId": "0_content",
                "x": 10,
                "y": 100,
                "width": 80,
                "height": 40,
                "source": "",
                "image": "",
                "imageFilename": "static_image.png",
                "imageUrl": "https://a4aportaldiag.blob.core.windows.net/gima/irmsdev-dev/news/e4399f74-17f0-442a-3513-4a7bd65b10a8.png",  # Static URL
                "styleId": "",
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "backgroundColor": "",
                "printIf": "",
                "removeEmptyElement": False,
                "link": "",
                "spreadsheet_hide": True,
                "spreadsheet_column": "",
                "spreadsheet_addEmptyRow": False
            }
        ],
        "parameters": [
            {
                "id": 1,
                "name": "branding",
                "type": "map",
                "arrayItemType": "string",
                "eval": False,
                "nullable": False,
                "pattern": "",
                "expression": "",
                "showOnlyNameType": False,
                "testData": "{\"company_logo\":\"https://a4aportaldiag.blob.core.windows.net/gima/irmsdev-dev/news/e4399f74-17f0-442a-3513-4a7bd65b10a8.png\"}",
                "testDataBoolean": False,
                "testDataImage": "",
                "testDataImageFilename": "",
                "testDataRichText": "",
                "children": [
                    {
                        "id": 2,
                        "name": "company_logo",
                        "type": "string",
                        "arrayItemType": "string",
                        "eval": False,
                        "nullable": False,
                        "pattern": "",
                        "expression": "",
                        "showOnlyNameType": False,
                        "testData": "",
                        "testDataBoolean": False,
                        "testDataImage": "",
                        "testDataImageFilename": "",
                        "testDataRichText": ""
                    }
                ]
            }
        ],
        "styles": [],
        "watermarks": [],
        "version": 5,
        "documentProperties": {
            "pageFormat": "A4",
            "pageWidth": "",
            "pageHeight": "",
            "unit": "mm",
            "orientation": "portrait",
            "contentHeight": "",
            "marginLeft": "20",
            "marginTop": "20",
            "marginRight": "20",
            "marginBottom": "10",
            "header": True,
            "headerSize": "60",
            "headerDisplay": "always",
            "footer": False,
            "footerSize": "60",
            "footerDisplay": "always",
            "watermark": False,
            "patternLocale": "en",
            "patternCurrencySymbol": "$",
            "patternNumberGroupSymbol": ""
        }
    },
    "outputFormat": "pdf",
    "data": {
        "branding": {
            "company_logo": "https://a4aportaldiag.blob.core.windows.net/gima/irmsdev-dev/news/e4399f74-17f0-442a-3513-4a7bd65b10a8.png"
        }
    },
    "isTestData": True
}

def test_complex_scenarios():
    """Test complex parameter-based imageUrl resolution scenarios."""
    url = "http://localhost:8000/api/templates/review/generate"
    
    print("Testing complex imageUrl resolution scenarios...")
    print(f"Element 1 imageUrl (parameter): {test_payload['report']['docElements'][0]['imageUrl']}")
    print(f"Element 2 imageUrl (static): {test_payload['report']['docElements'][1]['imageUrl']}")
    print(f"Data branding.company_logo: {test_payload['data']['branding']['company_logo']}")
    
    try:
        # Send the PUT request
        response = requests.put(
            url,
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Complex imageUrl scenarios working correctly!")
            print(f"Response Body: {response.text}")
            
            # Extract file key and fetch PDF
            file_key = response.text[4:] if response.text.startswith('key:') else response.text
            print(f"📄 Generated file key: {file_key}")
            
            # Try to fetch the generated PDF
            pdf_response = requests.get(
                f"http://localhost:8000/api/templates/review/generate?key={file_key}&outputFormat=pdf"
            )
            
            if pdf_response.status_code == 200:
                print("✅ PDF with multiple images (parameter + static) successfully generated!")
                print(f"PDF size: {len(pdf_response.content)} bytes")
                
                # Save the PDF
                with open("/tmp/test_complex_imageurl.pdf", "wb") as f:
                    f.write(pdf_response.content)
                print("📄 PDF saved to /tmp/test_complex_imageurl.pdf")
            else:
                print(f"❌ Failed to fetch PDF: {pdf_response.status_code}")
                print(f"Error: {pdf_response.text}")
                
        else:
            print("❌ FAILED: Complex imageUrl scenarios not working")
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_complex_scenarios()
