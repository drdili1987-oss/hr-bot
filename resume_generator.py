import os
from fpdf import FPDF
from datetime import datetime

class ResumePDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 20)
        self.cell(0, 15, "REZYUME (CV)", border=0, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"HR Bot orqali {datetime.now().strftime('%Y-%m-%d %H:%M')} da yaratildi", align="C")

def generate_pdf_resume(candidate_data: dict, output_path: str):
    pdf = ResumePDF()
    pdf.add_page()
    
    # Check if photo exists and insert it
    photo_path = candidate_data.get('photo_path')
    if photo_path and os.path.exists(photo_path):
        # Insert image at top right corner: x=160, y=20, width=35
        try:
            pdf.image(photo_path, x=160, y=25, w=35)
        except Exception as e:
            print("Could not load image:", e)
    
    # Title / Name
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(0, 51, 102)
    # Give some space so text doesn't overlap if image is very large
    pdf.cell(140, 10, candidate_data.get('full_name', 'Noma\'lum'), new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(140, 8, f"Telefon: {candidate_data.get('phone', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(140, 8, f"Vakansiya / Soha: {candidate_data.get('vacancy_title', '')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Sections
    sections = [
        ("Tug'ilgan yili:", candidate_data.get('birth_year', '')),
        ("Yashash manzili:", candidate_data.get('address', '')),
        ("Ta'lim darajasi:", candidate_data.get('education', '')),
        ("Tillarni bilishi:", candidate_data.get('languages', '')),
        ("Kutilayotgan maosh:", candidate_data.get('expected_salary', '')),
        ("Oldingi ish joyi:", candidate_data.get('previous_work', '')),
        ("Qo'shimcha qobiliyatlar:", candidate_data.get('skills', '')),
        ("Ish tajribasi (qisqacha):", candidate_data.get('experience', ''))
    ]
    
    for title, content in sections:
        if not content:
            continue
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 8, title, fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 11)
        # Ensure text is encoded to latin-1 to avoid errors with special chars
        safe_content = str(content).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, safe_content, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        
    pdf.output(output_path)
    return output_path
