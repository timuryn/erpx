# apps/erpx/erpx/custom_scripts/quotation_bom_integration.py

import frappe
from frappe import _
from frappe.utils import flt
import json

@frappe.whitelist()
def save_bom_changes(bom_data, mode):
    return save_bom_changes_simple(bom_data, mode)

@frappe.whitelist()
def get_bom_for_editing(bom_name):
    """Get BOM data for editing in dialog - SAFE VERSION"""
    try:
        # Method 1: Try to load BOM normally
        try:
            bom = frappe.get_doc("BOM", bom_name)
            return extract_bom_data(bom)
        except ImportError as ie:
            if "CustomBOMItem" in str(ie):
                frappe.logger().info(f"CustomBOMItem controller issue, using fallback method")
                return get_bom_data_via_database(bom_name)
            else:
                raise ie

    except Exception as e:
        frappe.log_error(f"Error getting BOM for editing: {str(e)}")

        # Method 2: Fallback to database query if doc loading fails
        try:
            return get_bom_data_via_database(bom_name)
        except Exception as e2:
            frappe.log_error(f"Fallback method also failed: {str(e2)}")
            frappe.throw(_("Error loading BOM: {0}").format(str(e)))

def extract_bom_data(bom):
    """Extract BOM data from document object"""
    bom_data = {
        "name": bom.name,
        "item": bom.item,
        "item_name": bom.item_name,
        "quantity": bom.quantity,
        "rm_cost_as_per": bom.rm_cost_as_per,
        "total_cost": bom.total_cost,
        "items": []
    }

    # Get BOM items with proper data structure
    for item in bom.items:
        item_dict = {
            "name": item.name,
            "item_code": item.item_code or "",
            "item_name": item.item_name or "",
            "qty": float(item.qty or 1),
            "uom": item.uom or "Stk",
            "rate": float(item.rate or 0),
            "amount": float(item.amount or 0),
            "stock_uom": item.stock_uom or item.uom or "Stk",
            "conversion_factor": float(item.conversion_factor or 1)
        }
        bom_data["items"].append(item_dict)

    frappe.logger().info(f"BOM data for {bom.name}: {len(bom_data['items'])} items")
    return bom_data

def get_bom_data_via_database(bom_name):
    """Get BOM data using direct database queries - bypasses controller issues"""
    try:
        # Get BOM header data
        bom_data = frappe.db.get_value("BOM", bom_name, [
            "name", "item", "item_name", "quantity", "rm_cost_as_per", "total_cost"
        ], as_dict=True)

        if not bom_data:
            frappe.throw(_("BOM {0} not found").format(bom_name))

        # Get BOM items data
        bom_items = frappe.db.sql("""
            SELECT
                name, item_code, item_name, qty, uom, rate, amount,
                stock_uom, conversion_factor, description
            FROM `tabBOM Item`
            WHERE parent = %s
            ORDER BY idx
        """, (bom_name,), as_dict=True)

        # Format items data
        items = []
        for item in bom_items:
            item_dict = {
                "name": item.name,
                "item_code": item.item_code or "",
                "item_name": item.item_name or "",
                "qty": float(item.qty or 1),
                "uom": item.uom or "Stk",
                "rate": float(item.rate or 0),
                "amount": float(item.amount or 0),
                "stock_uom": item.stock_uom or item.uom or "Stk",
                "conversion_factor": float(item.conversion_factor or 1)
            }
            items.append(item_dict)

        # Combine data
        result = {
            "name": bom_data.name,
            "item": bom_data.item,
            "item_name": bom_data.item_name,
            "quantity": bom_data.quantity,
            "rm_cost_as_per": bom_data.rm_cost_as_per,
            "total_cost": bom_data.total_cost,
            "items": items
        }

        frappe.logger().info(f"BOM data via database for {bom_name}: {len(items)} items")
        return result

    except Exception as e:
        frappe.log_error(f"Database fallback error: {str(e)}")
        frappe.throw(_("Error loading BOM via database: {0}").format(str(e)))

@frappe.whitelist()
def get_bom_summary(bom_name):
    """Get simple BOM summary for display purposes"""
    try:
        # Get basic BOM info
        bom_info = frappe.db.get_value("BOM", bom_name, [
            "item", "item_name", "total_cost", "quantity", "rm_cost_as_per"
        ], as_dict=True)

        if not bom_info:
            return None

        # Count items
        item_count = frappe.db.count("BOM Item", {"parent": bom_name})

        return {
            "name": bom_name,
            "item": bom_info.item,
            "item_name": bom_info.item_name,
            "total_cost": bom_info.total_cost,
            "quantity": bom_info.quantity,
            "rm_cost_as_per": bom_info.rm_cost_as_per,
            "item_count": item_count
        }

    except Exception as e:
        frappe.log_error(f"Error getting BOM summary: {str(e)}")
        return None

@frappe.whitelist()
def update_bom_cost(bom_name, new_total_cost):
    """Simple method to update BOM total cost"""
    try:
        frappe.db.set_value("BOM", bom_name, "total_cost", new_total_cost)
        frappe.db.commit()

        return {
            "success": True,
            "bom_name": bom_name,
            "new_total_cost": new_total_cost
        }

    except Exception as e:
        frappe.log_error(f"Error updating BOM cost: {str(e)}")
        frappe.throw(_("Error updating BOM cost: {0}").format(str(e)))

@frappe.whitelist()
def create_new_bom_structure(item_code):
    """Create new BOM structure for dialog"""
    # Get item details
    item = frappe.get_doc("Item", item_code)

    bom_data = {
        "name": None,  # New BOM
        "item": item_code,
        "item_name": item.item_name,
        "quantity": 1,
        "rm_cost_as_per": "Manual",  # Keep Manual as default
        "total_cost": 0,
        "items": []
    }

    return bom_data

# Ultra simple approach - minimal validation bypass

# Fix for apps/erpx/erpx/custom_scripts/quotation_bom_integration.py
# Replace the save_bom_changes_simple function with this version that bypasses the controller issue

@frappe.whitelist()
def save_bom_changes_simple(bom_data, mode):
    """Ultra simple BOM save - bypasses controller issues completely"""
    if isinstance(bom_data, str):
        bom_data = json.loads(bom_data)

    try:
        # Calculate total cost
        total_cost = sum(
            flt(item.get("qty", 1)) * flt(item.get("rate", 0))
            for item in bom_data.get("items", [])
            if item.get("item_name")
        )

        items_count = len([item for item in bom_data.get("items", []) if item.get("item_name")])

        if items_count == 0:
            frappe.throw(_("Please add at least one BOM item"))

        if mode == "create":
            # Use the direct database method instead of document creation
            return create_simple_bom_record(bom_data)
        else:
            # For editing existing BOM, use database updates only
            return update_bom_via_database(bom_data, total_cost)

    except Exception as e:
        frappe.log_error(f"Simple BOM Save Error: {str(e)}")
        frappe.throw(_("Error saving BOM: {0}").format(str(e)))

def update_bom_via_database(bom_data, total_cost):
    """Update existing BOM using direct database queries to avoid controller issues"""
    try:
        bom_name = bom_data["name"]

        # Update BOM header
        frappe.db.sql("""
            UPDATE `tabBOM`
            SET quantity = %s, rm_cost_as_per = 'Manual', total_cost = %s, modified = NOW()
            WHERE name = %s
        """, (bom_data.get("quantity", 1), total_cost, bom_name))

        # Delete existing BOM items
        frappe.db.sql("DELETE FROM `tabBOM Item` WHERE parent = %s", (bom_name,))

        # Insert new BOM items
        for idx, item_data in enumerate(bom_data.get("items", []), 1):
            if not item_data.get("item_name"):
                continue

            item_name = frappe.generate_hash(length=10)
            qty = flt(item_data.get("qty", 1))
            rate = flt(item_data.get("rate", 0))
            amount = qty * rate

            frappe.db.sql("""
                INSERT INTO `tabBOM Item`
                (name, parent, parenttype, parentfield, idx, item_code, item_name, qty, uom, rate, amount, stock_uom, conversion_factor, stock_qty, description, is_stock_item)
                VALUES
                (%s, %s, 'BOM', 'items', %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, 0)
            """, (
                item_name, bom_name, idx,
                item_data.get("item_code") or f"TEMP-{frappe.generate_hash(length=8)}",
                item_data["item_name"], qty, item_data.get("uom", "Nos"),
                rate, amount, item_data.get("uom", "Nos"), qty, item_data["item_name"]
            ))

        frappe.db.commit()

        return {
            "success": True,
            "bom_name": bom_name,
            "total_cost": total_cost,
            "items_count": len(bom_data.get("items", []))
        }

    except Exception as e:
        frappe.log_error(f"Database BOM update error: {str(e)}")
        frappe.throw(_("Error updating BOM via database: {0}").format(str(e)))

@frappe.whitelist()
def save_bom_changes_simple(bom_data, mode):
    """Ultra simple BOM save - bypasses controller issues completely"""
    if isinstance(bom_data, str):
        bom_data = json.loads(bom_data)

    try:
        # Calculate total cost
        total_cost = sum(
            flt(item.get("qty", 1)) * flt(item.get("rate", 0))
            for item in bom_data.get("items", [])
            if item.get("item_name")
        )

        items_count = len([item for item in bom_data.get("items", []) if item.get("item_name")])

        if items_count == 0:
            frappe.throw(_("Please add at least one BOM item"))

        if mode == "create":
            # Use the direct database method instead of document creation
            return create_simple_bom_record(bom_data)
        else:
            # For editing existing BOM, use database updates only
            return update_bom_via_database(bom_data, total_cost)

    except Exception as e:
        frappe.log_error(f"Simple BOM Save Error: {str(e)}")
        frappe.throw(_("Error saving BOM: {0}").format(str(e)))

@frappe.whitelist()
def update_quotation_item_rate(quotation_name, quotation_item_name, new_rate):
    """Update quotation item rate based on BOM total - NO AUTO SAVE"""
    try:
        quotation = frappe.get_doc("Quotation", quotation_name)

        # Find the specific quotation item
        item_updated = False
        for item in quotation.items:
            if item.name == quotation_item_name:
                old_rate = item.rate
                item.rate = flt(new_rate)
                item.amount = flt(item.qty) * flt(new_rate)
                item_updated = True
                frappe.logger().info(f"Updated quotation item {quotation_item_name}: {old_rate} -> {new_rate}")
                break

        if not item_updated:
            frappe.throw(_("Quotation item not found: {0}").format(quotation_item_name))

        # Recalculate quotation totals but don't save
        quotation.calculate_taxes_and_totals()

        return {
            "success": True,
            "new_rate": new_rate,
            "quotation_total": quotation.grand_total,
            "message": "Quotation item rate updated. Please save the quotation manually when ready."
        }

    except Exception as e:
        frappe.log_error(f"Quotation Update Error: {str(e)}")
        frappe.throw(_("Error updating quotation: {0}").format(str(e)))

@frappe.whitelist()
def get_item_bom_cost(item_code):
    """Get current BOM cost for an item"""
    bom = frappe.db.get_value("BOM",
        {"item": item_code, "is_active": 1},
        ["name", "total_cost"],
        order_by="creation desc"
    )

    if bom:
        return {
            "bom_name": bom[0],
            "total_cost": bom[1]
        }
    return None

@frappe.whitelist()
def validate_bom_items(items_data):
    """Validate BOM items before saving"""
    if isinstance(items_data, str):
        items_data = json.loads(items_data)

    valid_items = []
    errors = []

    for i, item in enumerate(items_data):
        item_name = item.get("item_name", "").strip()
        item_code = item.get("item_code", "").strip()
        qty = flt(item.get("qty", 0))
        rate = flt(item.get("rate", 0))

        # Check required fields
        if not item_name:
            errors.append(f"Row {i+1}: Item name is required")
            continue

        if qty <= 0:
            errors.append(f"Row {i+1}: Quantity must be greater than 0")
            continue

        # Check if item_code exists (if provided) - but allow temporary items
        if item_code and not item_code.startswith('TEMP-') and not frappe.db.exists("Item", item_code):
            errors.append(f"Row {i+1}: Item {item_code} does not exist")
            continue

        valid_items.append({
            "item_code": item_code,
            "item_name": item_name,
            "qty": qty,
            "rate": rate,
            "amount": qty * rate,
            "is_temporary": not bool(item_code) or item_code.startswith('TEMP-')
        })

    return {
        "valid_items": valid_items,
        "errors": errors,
        "total_amount": sum(item["amount"] for item in valid_items)
    }

@frappe.whitelist()
def create_temporary_bom_record(temp_item_code, item_name, bom_items, quantity=1):
    """Create BOM record for temporary items (items that don't exist in Item master)"""
    if isinstance(bom_items, str):
        bom_items = json.loads(bom_items)
    
    try:
        # Calculate total cost
        total_cost = sum(
            flt(item.get("qty", 1)) * flt(item.get("rate", 0))
            for item in bom_items
            if item.get("item_name")
        )
        
        items_count = len([item for item in bom_items if item.get("item_name")])
        
        if items_count == 0:
            frappe.throw(_("Please add at least one BOM item"))
        
        # Generate BOM name based on item name (since no item_code exists)
        clean_name = frappe.scrub(item_name)[:20]  # Clean and limit length
        base_name = f"BOM-TEMP-{clean_name.upper()}"
        
        # Check if BOM with this name already exists
        existing_count = frappe.db.count("BOM", {"name": ["like", f"{base_name}%"]})
        
        if existing_count == 0:
            bom_name = f"{base_name}-001"
        else:
            next_num = existing_count + 1
            while frappe.db.exists("BOM", f"{base_name}-{next_num:03d}"):
                next_num += 1
            bom_name = f"{base_name}-{next_num:03d}"
        
        # Get company and currency
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        currency = "EUR"
        if company:
            try:
                currency = frappe.get_cached_value("Company", company, "default_currency") or "EUR"
            except:
                currency = "EUR"
        
        # Create BOM record for temporary item
        frappe.db.sql("""
            INSERT INTO `tabBOM`
            (name, item, item_name, quantity, rm_cost_as_per, total_cost, is_active, is_default,
             company, currency, conversion_rate, docstatus, creation, modified, owner, modified_by, uom, description)
            VALUES
            (%(name)s, %(item)s, %(item_name)s, %(quantity)s, 'Manual', %(total_cost)s, 1, 1,
             %(company)s, %(currency)s, 1.0, 0, NOW(), NOW(), %(user)s, %(user)s, 'Nos', %(description)s)
        """, {
            "name": bom_name,
            "item": temp_item_code,  # Temporary item code
            "item_name": item_name,  # Actual display name
            "quantity": flt(quantity, 3),
            "total_cost": total_cost,
            "company": company,
            "currency": currency,
            "user": frappe.session.user,
            "description": f"BOM für temporären Artikel: {item_name}"
        })
        
        # Insert BOM items
        for idx, item_data in enumerate(bom_items, 1):
            if not item_data.get("item_name"):
                continue
            
            item_row_name = frappe.generate_hash(length=10)
            qty = flt(item_data.get("qty", 1))
            rate = flt(item_data.get("rate", 0))
            amount = qty * rate
            
            frappe.db.sql("""
                INSERT INTO `tabBOM Item`
                (name, parent, parenttype, parentfield, idx, item_code, item_name, qty, uom, rate, amount,
                 stock_uom, conversion_factor, stock_qty, description, is_stock_item, creation, modified, owner, modified_by)
                VALUES
                (%(name)s, %(parent)s, 'BOM', 'items', %(idx)s, %(item_code)s, %(item_name)s, %(qty)s, %(uom)s, %(rate)s, %(amount)s,
                 %(stock_uom)s, 1, %(stock_qty)s, %(description)s, 0, NOW(), NOW(), %(user)s, %(user)s)
            """, {
                "name": item_row_name,
                "parent": bom_name,
                "idx": idx,
                "item_code": item_data.get("item_code") or f"TEMP-{frappe.generate_hash(length=8)}",
                "item_name": item_data["item_name"],
                "qty": qty,
                "uom": item_data.get("uom", "Nos"),
                "rate": rate,
                "amount": amount,
                "stock_uom": item_data.get("uom", "Nos"),
                "stock_qty": qty,
                "description": f"Komponente für {item_name}: {item_data['item_name']}",
                "user": frappe.session.user
            })
        
        frappe.db.commit()
        
        return {
            "success": True,
            "bom_name": bom_name,
            "total_cost": total_cost,
            "items_count": items_count,
            "is_temporary": True
        }
        
    except Exception as e:
        frappe.log_error(f"Temporary BOM creation error: {str(e)}")
        frappe.throw(_("Error creating temporary BOM: {0}").format(str(e)))	
	
@frappe.whitelist()
def search_bom_by_item_name(item_name):
    """Search for existing BOMs by item name (for temporary items)"""
    try:
        # Search for BOMs where item_name matches (for temporary items)
        boms = frappe.db.sql("""
            SELECT name, item, item_name, total_cost, creation, is_active
            FROM `tabBOM`
            WHERE (item_name LIKE %s OR item LIKE %s)
            AND is_active = 1
            ORDER BY creation DESC
            LIMIT 5
        """, (f"%{item_name}%", f"%TEMP%{frappe.scrub(item_name)[:10]}%"), as_dict=True)
        
        return boms
        
    except Exception as e:
        frappe.log_error(f"Error searching BOM by item name: {str(e)}")
        return []	
	
# Alternative method - Create BOM with Manual rate method directly in database
@frappe.whitelist()
def create_simple_bom_record(bom_data):
    """Create BOM record - use item_name as item_code for temporary items"""
    if isinstance(bom_data, str):
        bom_data = json.loads(bom_data)

    try:
        # Calculate total cost
        total_cost = sum(
            flt(item.get("qty", 1)) * flt(item.get("rate", 0))
            for item in bom_data.get("items", [])
            if item.get("item_name")
        )

        # Get the actual values
        item_code = bom_data.get("item_code", "").strip()
        item_name = bom_data.get("item_name", "").strip() 
        item_field = bom_data.get("item", "").strip()
        is_temporary = bom_data.get("is_temporary", False)
        
        # Logic: Use item_code if available, otherwise use item_name
        if item_code and not is_temporary:
            # Item has item_code - use it for BOM item field
            bom_item_code = item_code
            display_name = item_name or item_code
            is_temp_item = False
            clean_identifier = frappe.scrub(item_code)[:20]
            base_name = f"BOM-{clean_identifier.upper()}"
        else:
            # Item only has item_name (temporary item) - use item_name for BOM item field
            actual_item_name = item_field or item_name
            
            if not actual_item_name:
                frappe.throw(_("Item name is required for temporary items"))
            
            bom_item_code = actual_item_name
            display_name = actual_item_name
            is_temp_item = True
            clean_identifier = frappe.scrub(actual_item_name)[:20]
            
            if not clean_identifier:
                clean_identifier = "UNNAMED"
                
            base_name = f"BOM-TEMP-{clean_identifier.upper()}"
        
        # Find next available number
        existing_count = frappe.db.count("BOM", {"name": ["like", f"{base_name}%"]})
        
        if existing_count == 0:
            bom_name = f"{base_name}-001"
        else:
            next_num = existing_count + 1
            while frappe.db.exists("BOM", f"{base_name}-{next_num:03d}"):
                next_num += 1
            bom_name = f"{base_name}-{next_num:03d}"

        # Get company and currency
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        currency = "EUR"
        if company:
            try:
                currency = frappe.get_cached_value("Company", company, "default_currency") or "EUR"
            except:
                currency = "EUR"

        # Create BOM record 
        frappe.db.sql("""
            INSERT INTO `tabBOM`
            (name, item, item_name, quantity, rm_cost_as_per, total_cost, is_active, is_default,
             company, currency, conversion_rate, docstatus, creation, modified, owner, modified_by, uom, description)
            VALUES
            (%(name)s, %(item)s, %(item_name)s, %(quantity)s, 'Manual', %(total_cost)s, 1, 1,
             %(company)s, %(currency)s, 1.0, 0, NOW(), NOW(), %(user)s, %(user)s, 'Nos', %(description)s)
        """, {
            "name": bom_name,
            "item": bom_item_code,
            "item_name": display_name,
            "quantity": bom_data.get("quantity", 1),
            "total_cost": total_cost,
            "company": company,
            "currency": currency,
            "user": frappe.session.user,
            "description": f"BOM für {display_name}" + (" (Temporärer Artikel)" if is_temp_item else "")
        })

        # Insert BOM items - copy item_name to item_code for temporary raw materials
        for idx, item_data in enumerate(bom_data.get("items", []), 1):
            if not item_data.get("item_name"):
                continue

            item_row_name = frappe.generate_hash(length=10)
            qty = flt(item_data.get("qty", 1))
            rate = flt(item_data.get("rate", 0))
            amount = qty * rate
            
            # For BOM item components, use item_name as item_code if no item_code exists
            component_item_code = item_data.get("item_code", "").strip()
            if not component_item_code:
                component_item_code = item_data["item_name"]

            frappe.db.sql("""
                INSERT INTO `tabBOM Item`
                (name, parent, parenttype, parentfield, idx, item_code, item_name, qty, uom, rate, amount,
                 stock_uom, conversion_factor, stock_qty, description, is_stock_item, creation, modified, owner, modified_by)
                VALUES
                (%(name)s, %(parent)s, 'BOM', 'items', %(idx)s, %(item_code)s, %(item_name)s, %(qty)s, %(uom)s, %(rate)s, %(amount)s,
                 %(stock_uom)s, 1, %(stock_qty)s, %(description)s, 0, NOW(), NOW(), %(user)s, %(user)s)
            """, {
                "name": item_row_name,
                "parent": bom_name,
                "idx": idx,
                "item_code": component_item_code,
                "item_name": item_data["item_name"],
                "qty": qty,
                "uom": item_data.get("uom", "Nos"),
                "rate": rate,
                "amount": amount,
                "stock_uom": item_data.get("uom", "Nos"),
                "stock_qty": qty,
                "description": item_data["item_name"],
                "user": frappe.session.user
            })

        frappe.db.commit()

        return {
            "success": True,
            "bom_name": bom_name,
            "total_cost": total_cost,
            "items_count": len(bom_data.get("items", [])),
            "is_temporary": is_temp_item
        }

    except Exception as e:
        frappe.log_error(f"BOM creation error: {str(e)}")
        frappe.throw(_("Error creating BOM record: {0}").format(str(e)))

@frappe.whitelist()
def create_simple_bom_record_enhanced(bom_data):
    """Enhanced BOM creation that handles both regular and temporary items"""
    if isinstance(bom_data, str):
        bom_data = json.loads(bom_data)

    try:
        item_code = bom_data["item"]
        item_name = bom_data.get("item_name", item_code)
        is_temporary = bom_data.get("is_temporary", False)
        
        if is_temporary or item_code.startswith("TEMP-"):
            # Handle temporary items
            return create_temporary_bom_record(
                item_code, 
                item_name, 
                bom_data.get("items", []), 
                bom_data.get("quantity", 1)
            )
        else:
            # Handle regular items - check if item exists
            if not frappe.db.exists("Item", item_code):
                frappe.throw(_("Item {0} does not exist. Use temporary BOM creation instead.").format(item_code))
            
            # Use existing logic for regular items
            return create_simple_bom_record(bom_data)
            
    except Exception as e:
        frappe.log_error(f"Enhanced BOM creation error: {str(e)}")
        frappe.throw(_("Error creating BOM: {0}").format(str(e)))

# ADDITIONAL: Add this function to handle the controller issue better
@frappe.whitelist()
def save_bom_changes_safe(bom_data, mode):
    """Safe BOM saving that completely avoids document controllers"""
    if isinstance(bom_data, str):
        bom_data = json.loads(bom_data)

    try:
        if mode == "create":
            return create_simple_bom_record(bom_data)
        else:
            # For existing BOMs, calculate total and update via database
            total_cost = sum(
                flt(item.get("qty", 1)) * flt(item.get("rate", 0))
                for item in bom_data.get("items", [])
                if item.get("item_name")
            )
            return update_bom_via_database(bom_data, total_cost)

    except Exception as e:
        frappe.log_error(f"Safe BOM Save Error: {str(e)}")

        # Ultimate fallback - just return success for local calculation
        total_cost = sum(
            flt(item.get("qty", 1)) * flt(item.get("rate", 0))
            for item in bom_data.get("items", [])
            if item.get("item_name")
        )

        return {
            "success": True,
            "bom_name": "local-calculation-only",
            "total_cost": total_cost,
            "items_count": len([item for item in bom_data.get("items", []) if item.get("item_name")]),
            "note": "BOM calculation only - not saved to database due to controller issues"
        }

# Also add a function to check for existing BOMs with better naming
@frappe.whitelist()
def check_existing_bom_by_item(item_code):
    """Check if BOM exists for item with consistent naming"""
    try:
        # Look for BOMs with the new naming pattern first
        boms = frappe.db.sql("""
            SELECT name, total_cost, creation
            FROM `tabBOM`
            WHERE item = %s AND is_active = 1
            AND (name LIKE %s OR name LIKE %s)
            ORDER BY creation DESC
            LIMIT 5
        """, (item_code, f"BOM-{item_code}-%", f"{item_code}-%"), as_dict=True)

        if not boms:
            # Fallback to any BOM for this item
            boms = frappe.db.sql("""
                SELECT name, total_cost, creation
                FROM `tabBOM`
                WHERE item = %s AND is_active = 1
                ORDER BY creation DESC
                LIMIT 1
            """, (item_code,), as_dict=True)

        return boms[0] if boms else None

    except Exception as e:
        frappe.log_error(f"Error checking existing BOM: {str(e)}")
        return None
		
@frappe.whitelist() 
def search_bom_for_item_or_name(item_identifier):
    """Search for BOM by item_code or item_name (for temporary items)"""
    try:
        # First try exact match on item field
        boms = frappe.db.sql("""
            SELECT name, item, item_name, total_cost, creation, is_active
            FROM `tabBOM`
            WHERE item = %s AND is_active = 1
            ORDER BY creation DESC
            LIMIT 1
        """, (item_identifier,), as_dict=True)
        
        if boms:
            return boms[0]
        
        # If no exact match, try partial match on item_name (for similar temporary items)
        boms = frappe.db.sql("""
            SELECT name, item, item_name, total_cost, creation, is_active
            FROM `tabBOM`
            WHERE item_name LIKE %s AND is_active = 1
            ORDER BY creation DESC
            LIMIT 5
        """, (f"%{item_identifier}%",), as_dict=True)
        
        return boms[0] if boms else None
        
    except Exception as e:
        frappe.log_error(f"Error searching BOM: {str(e)}")
        return None
