from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'BakeryOS - Manuale Tecnico', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, label, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, body)
        self.ln()

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    
    with open('/app/backend/manuale_tecnico.md', 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if line.startswith('## '):
            pdf.chapter_title(line.replace('## ', ''))
        elif line.startswith('### '):
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 6, line.replace('### ', ''), 0, 1)
            pdf.set_font('Arial', '', 11)
        elif line.startswith('* '):
             pdf.cell(10) # Indent
             pdf.cell(0, 5, '\x95 ' + line.replace('* ', ''), 0, 1)
        elif line.startswith('|'):
             pass # Skip tables for simple text PDF
        elif line == '---':
             pdf.ln(5)
             pdf.line(10, pdf.get_y(), 200, pdf.get_y())
             pdf.ln(5)
        else:
            if line:
                pdf.multi_cell(0, 5, line)
                pdf.ln(1)

    pdf.output('/app/manuale_tecnico.pdf', 'F')
    print("PDF Generated successfully: /app/manuale_tecnico.pdf")

if __name__ == '__main__':
    create_pdf()
