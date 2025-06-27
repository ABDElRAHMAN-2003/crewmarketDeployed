from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.units import inch
import io
import base64
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from textwrap import wrap

load_dotenv()

class PDFReportInput(BaseModel):
    analysis_text: str = Field(..., description="Textual analysis and summary for the report.")
    graph_images: List[str] = Field(..., description="List of base64-encoded PNG images for the report.")
    pdf_filename: str = Field(default="market_comparison_report.pdf", description="Filename for the PDF report.")
    store_in_mongo: bool = Field(default=True, description="Whether to store the PDF in MongoDB.")
    mongo_collection: str = Field(default="Market_Report", description="MongoDB collection name for PDF.")

class PDFReportTool(BaseTool):
    name: str = "PDFReportTool"
    description: str = "Generates a professional PDF market comparison report from analysis text and graph images, and stores it in MongoDB."
    args_schema: Type[BaseModel] = PDFReportInput

    def _run(self, analysis_text: str, graph_images: List[str], pdf_filename: str = "market_comparison_report.pdf", store_in_mongo: bool = True, mongo_collection: str = "Market_Report") -> str:
        try:
            # Create PDF
            pdf_path, image_log = self._create_pdf(analysis_text, graph_images, pdf_filename)
            msg = f"✅ PDF report created at {pdf_path}\n"
            msg += image_log
            # Optionally store in MongoDB
            if store_in_mongo:
                uri = os.getenv("MONGODB_URI", "mongodb+srv://Ali:suy4C1XDn5fHQOyd@nulibrarysystem.9c6hrww.mongodb.net/sample_db")
                db_name = os.getenv("DB_NAME", "sample_db")
                client = MongoClient(uri)
                db = client[db_name]
                collection = db[mongo_collection]
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
                doc = {
                    "filename": pdf_filename,
                    "created_at": datetime.utcnow(),
                    "pdf": pdf_data
                }
                result = collection.insert_one(doc)
                msg += f"Stored in MongoDB with ID: {result.inserted_id}\n"
            return msg
        except Exception as e:
            return f"❌ Error creating or storing PDF: {str(e)}"

    def _create_pdf(self, analysis_text: str, graph_images: List[str], pdf_filename: str):
        pdf_path = os.path.abspath(pdf_filename)
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkblue
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leading=14
        )
        
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=3,
            leftIndent=20,
            leading=14
        )
        
        # Build the story (content)
        story = []
        
        # Title Page
        story.append(Paragraph("MARKET COMPARISON ANALYSIS REPORT", title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("Innovatech Solutions Ltd.", heading_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}", body_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph("Prepared by: AI Market Analysis Team", body_style))
        story.append(PageBreak())
        
        # Parse and format the analysis text
        sections = self._parse_analysis_text(analysis_text)
        
        # Executive Summary
        if 'EXECUTIVE SUMMARY' in sections:
            story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
            story.append(Paragraph(sections['EXECUTIVE SUMMARY'], body_style))
            story.append(Spacer(1, 20))
        
        # Key Findings
        if 'KEY FINDINGS' in sections:
            story.append(Paragraph("KEY FINDINGS", heading_style))
            story.append(Paragraph(sections['KEY FINDINGS'], body_style))
            story.append(Spacer(1, 20))
        
        # SWOT Analysis
        if 'SWOT ANALYSIS' in sections:
            story.append(Paragraph("SWOT ANALYSIS", heading_style))
            story.append(Paragraph(sections['SWOT ANALYSIS'], body_style))
            story.append(Spacer(1, 20))
        
        # Add graphs with proper sizing and spacing
        for idx, img_b64 in enumerate(graph_images):
            try:
                img_data = base64.b64decode(img_b64)
                # Save debug image for inspection
                debug_img_path = f"debug_img_{idx}.png"
                with open(debug_img_path, "wb") as f:
                    f.write(img_data)
                
                # Create image with proper sizing
                img_io = io.BytesIO(img_data)
                img = Image(img_io, width=6*inch, height=4*inch)  # Fixed size for consistency
                story.append(img)
                story.append(Spacer(1, 20))
                
                # Add graph captions
                captions = [
                    "Figure 1: Revenue Growth Trend (2023-2024)",
                    "Figure 2: SWOT Analysis Summary",
                    "Figure 3: Market Share Distribution"
                ]
                if idx < len(captions):
                    story.append(Paragraph(captions[idx], body_style))
                    story.append(Spacer(1, 15))
                
            except Exception as e:
                story.append(Paragraph(f"Error rendering graph {idx+1}: {str(e)}", body_style))
                story.append(Spacer(1, 15))
        
        # Competitive Positioning
        if 'COMPETITIVE POSITIONING' in sections:
            story.append(Paragraph("COMPETITIVE POSITIONING", heading_style))
            story.append(Paragraph(sections['COMPETITIVE POSITIONING'], body_style))
            story.append(Spacer(1, 20))
        
        # Pricing Analysis
        if 'PRICING ANALYSIS' in sections:
            story.append(Paragraph("PRICING ANALYSIS", heading_style))
            story.append(Paragraph(sections['PRICING ANALYSIS'], body_style))
            story.append(Spacer(1, 20))
        
        # Market Trends
        if 'MARKET TRENDS' in sections:
            story.append(Paragraph("MARKET TRENDS", heading_style))
            story.append(Paragraph(sections['MARKET TRENDS'], body_style))
            story.append(Spacer(1, 20))
        
        # Strategic Recommendations
        if 'STRATEGIC RECOMMENDATIONS' in sections:
            story.append(Paragraph("STRATEGIC RECOMMENDATIONS", heading_style))
            story.append(Paragraph(sections['STRATEGIC RECOMMENDATIONS'], body_style))
            story.append(Spacer(1, 20))
        
        # Conclusion
        if 'CONCLUSION' in sections:
            story.append(Paragraph("CONCLUSION", heading_style))
            story.append(Paragraph(sections['CONCLUSION'], body_style))
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        image_log = f"Generated professional market comparison report with {len(graph_images)} graphs.\n"
        return pdf_path, image_log

    def _parse_analysis_text(self, text: str) -> dict:
        """Parse the analysis text into sections for better formatting"""
        sections = {}
        current_section = None
        current_content = []
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a section header (all uppercase, no = required)
            if line.isupper() and len(line) > 3 and not line.startswith('•'):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections 