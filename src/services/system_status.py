import random

class MockSystemStatusService:
    """Simulates live infrastructure and cloud service health checks for technical support."""
    
    @staticmethod
    def check_service_status(service_name: str = "all") -> dict:
        """Returns mock operational health metrics for internal infrastructure."""
        # For realistic simulation, we can define a couple of common mock components
        services = {
            "payment_gateway": {"status": "Operational", "latency_ms": 142, "incident": None},
            "user_authentication": {"status": "Operational", "latency_ms": 89, "incident": None},
            "cloud_api": {"status": "Degraded Performance", "latency_ms": 1250, "incident": "INC-8832: Latency spike in US-East region."}
        }
        
        if service_name in services:
            return {service_name: services[service_name]}
        return services