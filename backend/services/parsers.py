import re
import logging

logger = logging.getLogger(__name__)

def parse_wc_order_meta(wc_order_data: dict) -> dict:
    """
    Extract pickup date/time from order-level meta data.
    Looking for common plugins keys.
    """
    meta_data = wc_order_data.get("meta_data", [])
    
    pickup_date = None
    pickup_time = None
    
    # Common keys used by Delivery Date plugins
    date_keys = ["_delivery_date", "pickup_date", "orddd_date", "delivery_date", "jckwds_date"]
    time_keys = ["_delivery_time", "pickup_time", "orddd_time", "delivery_time", "jckwds_time_slot"]

    for meta in meta_data:
        key = meta.get("key", "").lower()
        value = meta.get("value")
        
        if not value:
            continue
            
        # Match Date
        if not pickup_date and any(k in key for k in date_keys):
            pickup_date = str(value)
            
        # Match Time
        if not pickup_time and any(k in key for k in time_keys):
            pickup_time = str(value)

    return {
        "pickup_date": pickup_date,
        "pickup_time": pickup_time
    }

def parse_wc_item_meta(item_data: dict) -> dict:
    """
    Extract writing, flavor, weight, allergens from line_item meta data.
    Using regex for tolerant matching.
    """
    meta_data = item_data.get("meta_data", [])
    
    result = {
        "writing": None,
        "flavor": None,
        "allergens_note": None,
        "weight_kg": None,
        "raw": meta_data
    }
    
    for meta in meta_data:
        key = meta.get("key", "").lower() # Display key usually
        value = str(meta.get("value", ""))
        
        if not value: 
            continue

        # 1. Writing / Scritta / Dedica
        if re.search(r"(scritta|writing|testo|dedica|frase)", key):
            result["writing"] = value
            continue
            
        # 2. Flavor / Gusto / Farcitura
        if re.search(r"(gusto|farcitura|ripieno|flavor|crema)", key):
            result["flavor"] = value
            continue
            
        # 3. Allergens / Intolleranze
        if re.search(r"(allerg|intolleranz|senza|gluten|lactose)", key):
            result["allergens_note"] = f"{key}: {value}"
            continue
            
        # 4. Weight / Peso
        if re.search(r"(peso|weight|kg|gramm|misura)", key):
            # Try to extract float
            try:
                # Remove non-numeric chars except dot and comma
                clean_val = re.sub(r"[^\d\.,]", "", value)
                if clean_val:
                    val = float(clean_val.replace(",", "."))
                    # Normalization heuristic: if > 50, assume grams, else kg
                    if val > 50:
                        val = val / 1000.0
                    result["weight_kg"] = val
            except:
                pass
            continue

    return result
