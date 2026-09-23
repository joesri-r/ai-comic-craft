import os
import time
import tempfile
from fpdf import FPDF

def save_pdf(layout: list) -> str:
    """
    Generate a PDF from the comic layout using FPDF2.
    
    :param layout: List of dictionaries containing panel data (title, image_path, narration, dialogue).
    :return: Absolute path to the generated PDF.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"comic_{timestamp}.pdf"
    
    temp_dir = tempfile.gettempdir()
    export_dir = os.path.join(temp_dir, "comiccraft", "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    filepath = os.path.join(export_dir, filename)
    
    # We use FPDF2
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for panel in layout:
        pdf.add_page()
        
        # Panel Title
        pdf.set_font("helvetica", "B", 24)
        pdf.set_text_color(0, 0, 0)
        # Using multi_cell to handle long titles and encode safely
        # We replace some common unicode chars if not using unicode fonts, or encode to latin-1
        title = panel.get("title", f"Panel {panel.get('panel_number')}")
        title = title.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 15, title, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)
        
        # Image
        image_path = panel.get("image_path", "")
            
        if os.path.exists(image_path):
            try:
                # Add image centered
                # A4 width is 210mm. If image is 150mm wide, margin is (210-150)/2 = 30
                pdf.image(image_path, x=30, y=pdf.get_y(), w=150)
                pdf.set_y(pdf.get_y() + 150 + 10) # Move Y below the image (assuming square image ~150h)
            except Exception as e:
                print(f"Error adding image to PDF: {e}")
                pdf.cell(0, 10, "Image Error", new_x="LMARGIN", new_y="NEXT", align="C")
        else:
            pdf.cell(0, 10, "Image Not Found", new_x="LMARGIN", new_y="NEXT", align="C")
            
        # Narration
        narration = panel.get("narration", "")
        if narration:
            pdf.set_font("helvetica", "I", 14)
            pdf.set_text_color(50, 50, 50)
            narration = narration.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 8, narration, align="L")
            pdf.ln(5)
            
        # Dialogue
        dialogue = panel.get("dialogue", "")
        if dialogue:
            pdf.set_font("helvetica", "", 16)
            pdf.set_text_color(0, 0, 0)
            dialogue = dialogue.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, f'"{dialogue}"', align="C")
            
    pdf.output(filepath)
    return filepath
