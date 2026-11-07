from app.db import query_db, execute_db

class Supplier:
    @staticmethod
    def create(name, contact_person=None, email=None, phone=None, address=None):
        """Create a new supplier."""
        supplier_id, _ = execute_db(
            """INSERT INTO suppliers (name, contact_person, email, phone, address)
               VALUES (?, ?, ?, ?, ?)""",
            (name.strip(), contact_person, email, phone, address)
        )
        return supplier_id

    @staticmethod
    def get_by_id(supplier_id):
        """Get supplier by ID with product count."""
        return query_db(
            """SELECT s.*, COUNT(p.id) as product_count 
               FROM suppliers s 
               LEFT JOIN products p ON s.id = p.supplier_id 
               WHERE s.id = ?
               GROUP BY s.id""",
            (supplier_id,),
            one=True
        )

    @staticmethod
    def list_all(search=None):
        """List all suppliers with optional search and product count."""
        query = """
            SELECT s.*, COUNT(p.id) as product_count 
            FROM suppliers s 
            LEFT JOIN products p ON s.id = p.supplier_id
        """
        args = []
        if search:
            query += " WHERE s.name LIKE ? OR s.contact_person LIKE ? OR s.phone LIKE ? OR s.email LIKE ?"
            term = f"%{search.strip()}%"
            args = [term, term, term, term]
            
        query += " GROUP BY s.id ORDER BY s.name ASC"
        return query_db(query, args)

    @staticmethod
    def update(supplier_id, name, contact_person=None, email=None, phone=None, address=None):
        """Update supplier details."""
        execute_db(
            """UPDATE suppliers 
               SET name = ?, contact_person = ?, email = ?, phone = ?, address = ?
               WHERE id = ?""",
            (name.strip(), contact_person, email, phone, address, supplier_id)
        )

    @staticmethod
    def delete(supplier_id):
        """Delete supplier (associated products will have supplier_id set to NULL)."""
        execute_db("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
