#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '/Users/dipankarsaha/reportbro-designer-api/reportbro-lib')

from reportbro import Report, ReportBroError

def test_watermark():
    print("🧪 Testing watermark functionality with correct JSON format...")

    # Report definition with watermarks in separate section
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
                "elementType": "watermark_text",
                "id": 129,
                "x": 260,
                "y": 630,
                "width": 210,
                "height": 60,
                "content": "CONFIDENTIAL",
                "eval": False,
                "rotateDeg": 45,
                "opacity": 30,
                "showInForeground": False,
                "styleId": "",
                "bold": True,
                "italic": False,
                "underline": False,
                "strikethrough": False,
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "textColor": "#FF0000",
                "backgroundColor": "",
                "font": "helvetica",
                "fontSize": "32",
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
            print(f"   - Watermark {i+1}: {watermark.__class__.__name__} - {getattr(watermark, 'content', 'N/A')}")
        
        pdf_data = report.generate_pdf()
        print(f"✅ PDF generated successfully: {len(pdf_data)} bytes")
        
        # Save to temp file for verification
        with open('/tmp/test_watermark_corrected.pdf', 'wb') as f:
            f.write(pdf_data)
        print("✅ Test PDF saved to /tmp/test_watermark_corrected.pdf")
        
        print("🎉 All tests passed!")
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
    success = test_watermark()
    sys.exit(0 if success else 1)
