#!/usr/bin/env python3
"""
Test script to verify watermark opacity works via API.
"""

import requests
import json

def test_watermark_opacity_api():
    """Test watermark opacity functionality via API."""
    
    # Report definition with text watermark and different opacity levels
    report_definition = {
        "docElements": [
            {
                "id": 1,
                "x": 100,
                "y": 100,
                "width": 400,
                "height": 50,
                "elementType": "text",
                "content": "This is a test document with text watermarks at different opacity levels via API.",
                "textColor": "#000000",
                "font": "helvetica",
                "fontSize": 12,
                "fontStyle": "",
                "horizontalAlignment": "left",
                "verticalAlignment": "top"
            }
        ],
        "watermarks": [
            {
                "id": 100,
                "x": 50,
                "y": 200,
                "width": 500,
                "height": 100,
                "elementType": "watermark_text",
                "content": "20% OPACITY WATERMARK VIA API",
                "textColor": "#ff0000",
                "font": "helvetica",
                "fontSize": 24,
                "fontStyle": "B",
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "opacity": 20,
                "rotateDeg": 0,
                "showInForeground": False
            },
            {
                "id": 101,
                "x": 50,
                "y": 350,
                "width": 500,
                "height": 100,
                "elementType": "watermark_text",
                "content": "50% OPACITY WATERMARK VIA API",
                "textColor": "#00ff00",
                "font": "helvetica",
                "fontSize": 24,
                "fontStyle": "B",
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "opacity": 50,
                "rotateDeg": 0,
                "showInForeground": False
            },
            {
                "id": 102,
                "x": 50,
                "y": 500,
                "width": 500,
                "height": 100,
                "elementType": "watermark_text",
                "content": "80% OPACITY WATERMARK VIA API",
                "textColor": "#0000ff",
                "font": "helvetica",
                "fontSize": 24,
                "fontStyle": "B",
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "opacity": 80,
                "rotateDeg": 0,
                "showInForeground": False
            }
        ],
        "parameters": [],
        "styles": [],
        "documentProperties": {
            "pageFormat": "A4",
            "pageWidth": 595,
            "pageHeight": 842,
            "unit": "pt",
            "orientation": "portrait",
            "contentHeight": 762,
            "marginLeft": 40,
            "marginTop": 40,
            "marginRight": 40,
            "marginBottom": 40,
            "patternLocale": "en",
            "patternCurrencySymbol": "$"
        }
    }
    
    # Test data (empty for this test)
    data = {}
    
    try:
        # API endpoint for generating reports
        url = "http://localhost:8000/api/templates/review/generate/download"
        
        payload = {
            "report": report_definition,
            "data": data,
            "isTestData": False,
            "outputFormat": "pdf"
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        print("Sending request to API...")
        response = requests.put(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            # Extract the download URL from the response
            response_data = response.json()
            
            if 'data' in response_data and 'downloadUrl' in response_data['data']:
                download_url = response_data['data']['downloadUrl']
                print(f"Got download URL: {download_url}")
                
                # Download the PDF
                download_response = requests.get(download_url)
                
                if download_response.status_code == 200:
                    # Save the PDF
                    output_file = "watermark_opacity_api_test.pdf"
                    with open(output_file, 'wb') as f:
                        f.write(download_response.content)
                    
                    print(f"PDF generated successfully via API: {output_file}")
                    print("Check the PDF to see if text watermarks show different opacity levels.")
                    print("Expected: Red watermark (20%) should be lightest, Blue (80%) should be darkest")
                    return True
                else:
                    print(f"Failed to download PDF: {download_response.status_code}")
                    return False
            else:
                print("No download URL in response")
                print(f"Response: {response_data}")
                return False
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"Error testing API: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_watermark_opacity_api()
    if success:
        print("✅ Watermark opacity test via API successful")
    else:
        print("❌ Watermark opacity test via API failed")
