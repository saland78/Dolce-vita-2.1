from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
from datetime import datetime

def generate_production_sheet_pdf(order: dict):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    y = height - 20*mm
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, y, f"Scheda Produzione - Ordine #{order.get('wc_order_id', '???')}")
    y -= 10*mm
    
    # Customer Info
    c.setFont("Helvetica", 12)
    cust = order.get('customer', {})
    c.drawString(20*mm, y, f"Cliente: {cust.get('first_name')} {cust.get('last_name')}")
    y -= 5*mm
    c.drawString(20*mm, y, f"Telefono: {cust.get('phone', 'N/A')}")
    y -= 5*mm
    
    # Pickup Info
    pickup_date = order.get('pickup_date') or "Non specificata"
    pickup_time = order.get('pickup_time') or ""
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, y, f"RITIRO: {pickup_date} {pickup_time}")
    y -= 15*mm
    
    # Items
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, y, "Articoli da produrre:")
    y -= 10*mm
    
    c.setFont("Helvetica", 12)
    for item in order.get('items', []):
        meta = item.get('meta', {})
        qty = item.get('quantity', 1)
        name = item.get('product_name', 'Prodotto')
        
        # Main Line
        item_text = f"• {qty}x {name}"
        c.setFont("Helvetica-Bold", 12)
        c.drawString(25*mm, y, item_text)
        y -= 6*mm
        
        # Details (Writing, Flavor, etc)
        details = []
        if meta.get('flavor'): details.append(f"Gusto: {meta['flavor']}")
        if meta.get('writing'): details.append(f"Scritta: \"{meta['writing']}\"")
        if meta.get('weight_kg'): details.append(f"Peso: {meta['weight_kg']} kg")
        
        c.setFont("Helvetica", 11)
        for det in details:
            c.drawString(30*mm, y, det)
            y -= 5*mm
            
        # Allergens (RED)
        if meta.get('allergens_note'):
            c.setFillColorRGB(1, 0, 0) # Red
            c.setFont("Helvetica-Bold", 11)
            c.drawString(30*mm, y, f"⚠ ALLERGENI: {meta['allergens_note']}")
            c.setFillColorRGB(0, 0, 0) # Reset to black
            y -= 6*mm
            
        y -= 2*mm # Spacing between items
        
        if y < 30*mm:
            c.showPage()
            y = height - 20*mm

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(20*mm, 15*mm, f"Stampato il {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    c.save()
    buffer.seek(0)
    return buffer
