#!/usr/bin/env python3
"""
Test script for watermark image functionality
"""
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/Users/dipankarsaha/reportbro-designer-api')

from reportbro_designer_api.utils.report import ReportPdf
from reportbro_designer_api.clients import FONTS_LOADER

def test_watermark_image():
    """Test watermark image functionality"""
    
    # Sample report definition with watermark image
    report_definition = {
        "docElements": [
            {
                "elementType": "watermark_image",
                "id": 130,
                "containerId": "0_watermark_images", 
                "x": 150,
                "y": 300,
                "width": 200,
                "height": 100,
                "source": "",
                "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                "opacity": 50,
                "rotateDeg": 0,
                "showInForeground": False,
                "horizontalAlignment": "left",
                "verticalAlignment": "top"
            },
            {
                "elementType": "text",
                "id": 1,
                "containerId": "0_content",
                "x": 50,
                "y": 100,
                "width": 400,
                "height": 50,
                "content": "This is a test document with image watermark",
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
    
    # Sample data
    data = {}
    
    try:
        # Create ReportPdf instance
        report_pdf = ReportPdf(
            report_definition=report_definition,
            data=data,
            font_loader=FONTS_LOADER,
            is_test_data=True
        )
        
        # Check if report was created successfully
        if report_pdf.report.errors:
            print("❌ Report has errors:")
            for error in report_pdf.report.errors:
                print(f"   - {error}")
            return False
        
        # Check if watermarks were processed
        if hasattr(report_pdf.report, 'watermarks'):
            print(f"✅ Watermarks found: {len(report_pdf.report.watermarks)}")
            for i, watermark in enumerate(report_pdf.report.watermarks):
                print(f"   - Watermark {i+1}: {type(watermark).__name__}")
        else:
            print("❌ No watermarks attribute found")
            return False
        
        # Generate PDF to test rendering
        pdf_data = report_pdf.generate_pdf(filename="", add_watermark=False)
        
        if pdf_data:
            print(f"✅ PDF generated successfully: {len(pdf_data)} bytes")
            
            # Save test PDF
            with open("/tmp/test_watermark_image.pdf", "wb") as f:
                f.write(pdf_data)
            print("✅ Test PDF saved to /tmp/test_watermark_image.pdf")
            
            return True
        else:
            print("❌ PDF generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing watermark image functionality...")
    success = test_watermark_image()
    if success:
        print("🎉 Image watermark test passed!")
        sys.exit(0)
    else:
        print("💥 Image watermark test failed!")
        sys.exit(1)
