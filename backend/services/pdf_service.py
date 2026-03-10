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


def generate_monthly_report_pdf(data: dict):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    import io, calendar

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 20*mm

    month_name = calendar.month_name[data["month"]]

    # Titolo
    c.setFillColorRGB(0.25, 0.13, 0.06)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20*mm, y, f"Report Mensile — {month_name} {data['year']}")
    y -= 12*mm

    # Linea separatrice
    c.setStrokeColorRGB(0.8, 0.7, 0.5)
    c.setLineWidth(1)
    c.line(20*mm, y, width - 20*mm, y)
    y -= 10*mm

    # Riquadro KPI
    c.setFillColorRGB(0.98, 0.96, 0.92)
    c.roundRect(20*mm, y - 22*mm, width - 40*mm, 22*mm, 4, fill=1, stroke=0)
    c.setFillColorRGB(0.25, 0.13, 0.06)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(25*mm, y - 8*mm, f"Fatturato Totale: €{data['total_revenue']:.2f}")
    c.drawString(25*mm, y - 15*mm, f"Ordini Totali: {data['total_orders']}     Scontrino Medio: €{data['avg_order']:.2f}")
    y -= 30*mm

    # Prodotti più venduti
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.25, 0.13, 0.06)
    c.drawString(20*mm, y, "Prodotti più venduti")
    y -= 8*mm
    c.setFont("Helvetica", 11)
    for i, p in enumerate(data["top_products"]):
        c.setFillColorRGB(0.9, 0.88, 0.84) if i % 2 == 0 else c.setFillColorRGB(1, 1, 1)
        c.rect(20*mm, y - 4*mm, width - 40*mm, 7*mm, fill=1, stroke=0)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(25*mm, y, f"{i+1}. {p['name']}")
        c.drawRightString(width - 25*mm, y, f"x{p['quantity']}")
        y -= 7*mm
        if y < 40*mm:
            c.showPage()
            y = height - 20*mm

    y -= 8*mm

    # Clienti top
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.25, 0.13, 0.06)
    c.drawString(20*mm, y, "Clienti top")
    y -= 8*mm
    c.setFont("Helvetica", 11)
    for i, cust in enumerate(data["top_customers"]):
        c.setFillColorRGB(0.9, 0.88, 0.84) if i % 2 == 0 else c.setFillColorRGB(1, 1, 1)
        c.rect(20*mm, y - 4*mm, width - 40*mm, 7*mm, fill=1, stroke=0)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(25*mm, y, f"{i+1}. {cust['name']}")
        c.drawRightString(width - 25*mm, y, f"€{cust['total']:.2f} ({cust['orders']} ordini)")
        y -= 7*mm
        if y < 40*mm:
            c.showPage()
            y = height - 20*mm

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    from datetime import datetime
    c.drawString(20*mm, 12*mm, f"Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')} — DolceVita Bakery OS")

    c.save()
    buffer.seek(0)
    return buffer
