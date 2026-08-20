from src.agents.classifier import classify_email
from src.schemas.tickets import SupportCategory, ClassificationResult

def test_classify_order_status():
    """Test that an inquiry about shipping is correctly classified as order_status."""
    email_text = "Where is my package? Tracking number #998877 hasn't updated in 4 days."
    result = classify_email(email_text)
    
    assert isinstance(result, ClassificationResult)
    assert result.category == SupportCategory.ORDER_STATUS
    assert 0.0 <= result.confidence_score <= 1.0

def test_classify_returns():
    """Test that a return request is correctly classified as returns."""
    email_text = "I would like to return a defective jacket and request a full refund."
    result = classify_email(email_text)
    
    assert isinstance(result, ClassificationResult)
    assert result.category == SupportCategory.RETURNS
    assert isinstance(result.reasoning, str)

def test_classify_subscriptions():
    """Test that a billing question is correctly classified as subscriptions."""
    email_text = "Why did my annual plan automatically renew? I want to cancel my subscription."
    result = classify_email(email_text)
    
    assert isinstance(result, ClassificationResult)
    assert result.category == SupportCategory.SUBSCRIPTIONS