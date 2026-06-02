"""
Export transcriptions to multiple formats.
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger("vosk_stt.export")

class ExportManager:
    """Handle exporting transcriptions to various formats."""
    
    def __init__(self, output_folder: str):
        self.output_folder = Path(output_folder).expanduser()
        logger.info("ExportManager initialized")
    
    def export(self, content: str, base_filename: str, format_type: str) -> Optional[Path]:
        """
        Export content to specified format.
        
        Args:
            content: Text content to export
            base_filename: Base name without extension
            format_type: Export format (txt, md, pdf, docx, html, srt, json)
            
        Returns:
            Path to exported file or None if failed
        """
        exporters = {
            'txt': self._export_txt,
            'md': self._export_markdown,
            'html': self._export_html,
            'json': self._export_json,
            'srt': self._export_srt,
            'pdf': self._export_pdf,
            'docx': self._export_docx,
        }
        
        exporter = exporters.get(format_type)
        if not exporter:
            logger.error(f"Unknown format: {format_type}")
            return None
        
        try:
            return exporter(content, base_filename)
        except Exception as e:
            logger.error(f"Export to {format_type} failed: {e}", exc_info=True)
            print(f"\n✗ Export to {format_type} failed: {e}")
            return None
    
    def _export_txt(self, content: str, base_filename: str) -> Path:
        """Export as plain text."""
        filepath = self.output_folder / f"{base_filename}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Exported to TXT: {filepath.name}")
        return filepath
    
    def _export_markdown(self, content: str, base_filename: str) -> Path:
        """Export as Markdown with formatting."""
        filepath = self.output_folder / f"{base_filename}.md"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {base_filename}\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write("---\n\n")
            
            # Split into paragraphs (sentences ending with . ! ?)
            sentences = content.replace('! ', '!||').replace('? ', '?||').replace('. ', '.||').split('||')
            
            # Group sentences into paragraphs (every 3-5 sentences)
            paragraph_size = 4
            for i in range(0, len(sentences), paragraph_size):
                paragraph = ' '.join(sentences[i:i+paragraph_size]).strip()
                if paragraph:
                    f.write(f"{paragraph}\n\n")
        
        logger.info(f"Exported to Markdown: {filepath.name}")
        return filepath
    
    def _export_html(self, content: str, base_filename: str) -> Path:
        """Export as HTML with basic styling."""
        filepath = self.output_folder / f"{base_filename}.html"
        
        # Split into paragraphs
        sentences = content.replace('! ', '!||').replace('? ', '?||').replace('. ', '.||').split('||')
        paragraphs = []
        
        for i in range(0, len(sentences), 4):
            paragraph = ' '.join(sentences[i:i+4]).strip()
            if paragraph:
                paragraphs.append(f"<p>{paragraph}</p>")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{base_filename}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .meta {{
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 30px;
        }}
        p {{
            margin-bottom: 20px;
            text-align: justify;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
            font-size: 0.85em;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{base_filename}</h1>
        <div class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        {''.join(paragraphs)}
        
        <div class="footer">
            Transcribed with Vosk Speech-to-Text
        </div>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Exported to HTML: {filepath.name}")
        return filepath
    
    def _export_json(self, content: str, base_filename: str) -> Path:
        """Export as JSON with metadata."""
        import json
        
        filepath = self.output_folder / f"{base_filename}.json"
        
        # Split into sentences
        sentences = content.replace('! ', '!||').replace('? ', '?||').replace('. ', '.||').split('||')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        data = {
            'filename': base_filename,
            'generated': datetime.now().isoformat(),
            'word_count': len(content.split()),
            'character_count': len(content),
            'sentence_count': len(sentences),
            'full_text': content,
            'sentences': sentences
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported to JSON: {filepath.name}")
        return filepath
    
    def _export_srt(self, content: str, base_filename: str) -> Path:
        """Export as SRT subtitle format."""
        filepath = self.output_folder / f"{base_filename}.srt"
        
        # Split into sentences
        sentences = content.replace('! ', '!||').replace('? ', '?||').replace('. ', '.||').split('||')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Each sentence = ~3 seconds
            for i, sentence in enumerate(sentences, 1):
                start_time = (i - 1) * 3
                end_time = i * 3
                
                # Format: HH:MM:SS,mmm
                start_str = f"{start_time//3600:02d}:{(start_time%3600)//60:02d}:{start_time%60:02d},000"
                end_str = f"{end_time//3600:02d}:{(end_time%3600)//60:02d}:{end_time%60:02d},000"
                
                f.write(f"{i}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{sentence}\n\n")
        
        logger.info(f"Exported to SRT: {filepath.name}")
        return filepath
    
    def _export_pdf(self, content: str, base_filename: str) -> Path:
        """
        Export as PDF (requires reportlab).
        Falls back to HTML if reportlab not available.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            
            filepath = self.output_folder / f"{base_filename}.pdf"
            
            # Create PDF
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
            )
            story.append(Paragraph(base_filename, title_style))
            
            # Metadata
            meta_style = ParagraphStyle(
                'Meta',
                parent=styles['Normal'],
                fontSize=10,
                textColor='grey',
            )
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Content - split into paragraphs
            sentences = content.replace('! ', '!||').replace('? ', '?||').replace('. ', '.||').split('||')
            
            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=12,
                leading=18,
                spaceAfter=12,
                alignment=4,  # Justify
            )
            
            for i in range(0, len(sentences), 4):
                paragraph_text = ' '.join(sentences[i:i+4]).strip()
                if paragraph_text:
                    story.append(Paragraph(paragraph_text, body_style))
            
            doc.build(story)
            logger.info(f"Exported to PDF: {filepath.name}")
            return filepath
            
        except ImportError:
            print("\n⚠ PDF export requires 'reportlab' package")
            print("  Installing: pip install reportlab")
            print("  Falling back to HTML export...")
            return self._export_html(content, base_filename)
    
    def _export_docx(self, content: str, base_filename: str) -> Path:
        """
        Export as DOCX (requires python-docx).
        Falls back to HTML if not available.
        """
        try:
            from docx import Document
            from docx.shared import Inches, Pt
            
            filepath = self.output_folder / f"{base_filename}.docx"
            
            doc = Document()
            
            # Title
            title = doc.add_heading(base_filename, 0)
            
            # Metadata
            meta = doc.add_paragraph()
            meta.add_run(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").italic = True
            
            doc.add_paragraph()  # Spacer
            
            # Content - split into paragraphs
            sentences = content.replace('! ', '!||').replace('? ', '?||').replace('. ', '.||').split('||')
            
            for i in range(0, len(sentences), 4):
                paragraph_text = ' '.join(sentences[i:i+4]).strip()
                if paragraph_text:
                    p = doc.add_paragraph(paragraph_text)
                    p.paragraph_format.line_spacing = 1.5
                    p.paragraph_format.space_after = Pt(12)
            
            doc.save(str(filepath))
            logger.info(f"Exported to DOCX: {filepath.name}")
            return filepath
            
        except ImportError:
            print("\n⚠ DOCX export requires 'python-docx' package")
            print("  Installing: pip install python-docx")
            print("  Falling back to HTML export...")
            return self._export_html(content, base_filename)
    
    def show_export_menu(self) -> str:
        """
        Show export format menu.
        
        Returns:
            Selected format code
        """
        print("\n" + "="*60)
        print("EXPORT FORMAT")
        print("="*60)
        print("1. Plain Text (.txt)")
        print("2. Markdown (.md)")
        print("3. HTML (.html) - Web-ready with styling")
        print("4. JSON (.json) - Structured data")
        print("5. SRT (.srt) - Subtitle format")
        print("6. PDF (.pdf) - Requires reportlab")
        print("7. Word Document (.docx) - Requires python-docx")
        print("="*60)
        
        choice = input("\nFormat (1-7, default 1): ").strip() or '1'
        
        format_map = {
            '1': 'txt',
            '2': 'md',
            '3': 'html',
            '4': 'json',
            '5': 'srt',
            '6': 'pdf',
            '7': 'docx'
        }
        
        return format_map.get(choice, 'txt')
