#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '/Users/dipankarsaha/reportbro-designer-api/reportbro-lib')

from reportbro import Report, ReportBroError

def test_watermark_image():
    print("🧪 Testing watermark image functionality with correct JSON format...")

    # Report definition with image watermark in separate section
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
                "content": "Hello World!",
                "eval": False,
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "font": "helvetica",
                "fontSize": 12,
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
                "x": 200,
                "y": 500,
                "width": 100,
                "height": 100,
                "source": "",
                "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "eval": False,
                "rotateDeg": 0,
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

    try:
        report = Report(report_definition, data)
        
        if report.errors:
            print(f"❌ Report errors: {report.errors}")
            return False
            
        print(f"✅ Watermarks found: {len(report.watermarks)}")
        for i, watermark in enumerate(report.watermarks):
            print(f"   - Watermark {i+1}: {watermark.__class__.__name__}")
        
        pdf_data = report.generate_pdf()
        print(f"✅ PDF generated successfully: {len(pdf_data)} bytes")
        
        # Save to temp file for verification
        with open('/tmp/test_watermark_image_corrected.pdf', 'wb') as f:
            f.write(pdf_data)
        print("✅ Test PDF saved to /tmp/test_watermark_image_corrected.pdf")
        
        print("🎉 Image watermark test passed!")
        return True
        
    except ReportBroError as e:
        print(f"❌ ReportBro error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_watermark_image()
    sys.exit(0 if success else 1)
