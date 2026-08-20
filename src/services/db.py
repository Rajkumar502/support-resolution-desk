import datetime

class MockDatabaseService:
    @staticmethod
    def fetch_order_details(order_id: str) -> dict:
        """Simulates querying a live SQL database or shipping API with dynamic dates."""
        today = datetime.date.today()
        
        # Calculate dynamic relative dates
        est_delivery = today + datetime.timedelta(days=4)
        delivered_date = today - datetime.timedelta(days=2)
        
        # Simulated database records with dynamic formatting
        db = {
            "#12345": {
                "status": "In Transit",
                "carrier": "FedEx",
                "tracking_number": "FX-987654321",
                "estimated_delivery": est_delivery.strftime("%B %d, %Y"),
                "item": "Wireless Mechanical Keyboard"
            },
            "#99887": {
                "status": "Delivered",
                "carrier": "Royal Mail",
                "tracking_number": "RM-123456789",
                "estimated_delivery": f"Delivered on {delivered_date.strftime('%B %d, %Y')}",
                "item": "Ergonomic Mouse"
            }
        }
        
        # Default fallback if order ID isn't found
        return db.get(order_id, {
            "status": "Processing / Not Found",
            "carrier": "N/A",
            "tracking_number": "N/A",
            "estimated_delivery": "Unknown",
            "item": "Unknown Item"
        })