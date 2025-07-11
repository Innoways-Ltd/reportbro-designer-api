#!/usr/bin/env python3
"""
Test script to verify watermark opacity works for text watermarks.
"""

import sys
import os

# Add the reportbro-lib to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'reportbro-lib'))

from reportbro import Report

def test_watermark_opacity():
    """Test watermark opacity functionality."""
    
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
                "content": "This is a test document with text watermarks at different opacity levels.",
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
                "content": "30% OPACITY WATERMARK",
                "textColor": "#ff0000",
                "font": "helvetica",
                "fontSize": 24,
                "fontStyle": "B",
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "opacity": 30,
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
                "content": "60% OPACITY WATERMARK",
                "textColor": "#00ff00",
                "font": "helvetica",
                "fontSize": 24,
                "fontStyle": "B",
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "opacity": 60,
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
                "content": "90% OPACITY WATERMARK",
                "textColor": "#0000ff",
                "font": "helvetica",
                "fontSize": 24,
                "fontStyle": "B",
                "horizontalAlignment": "left",
                "verticalAlignment": "top",
                "opacity": 90,
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
        # Create and generate the report
        print("Creating report with opacity watermarks...")
        report = Report(report_definition, data)
        
        print("Generating PDF...")
        pdf_report = report.generate_pdf()
        
        # Save the PDF
        output_file = "watermark_opacity_test.pdf"
        with open(output_file, 'wb') as f:
            f.write(pdf_report)
        
        print(f"PDF generated successfully: {output_file}")
        print("Check the PDF to see if text watermarks show different opacity levels.")
        print("Expected: Red watermark (30%) should be lightest, Blue (90%) should be darkest")
        
        return True
        
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_watermark_opacity()
    sys.exit(0 if success else 1)
