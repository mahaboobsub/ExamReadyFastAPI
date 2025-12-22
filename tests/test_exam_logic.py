from app.routers.exam import _calculate_distribution

def test_distribution_math_exact():
    # 50 questions, 10% / 40% / 50%
    total = 50
    dist = {"Remember": 10, "Understand": 40, "Apply": 50}
    
    result = _calculate_distribution(total, dist)
    
    assert result["Remember"] == 5
    assert result["Understand"] == 20
    assert result["Apply"] == 25
    assert sum(result.values()) == 50

def test_distribution_math_rounding():
    # 3 questions, 33% / 33% / 33% -> Should sum to 3
    total = 3
    dist = {"A": 33, "B": 33, "C": 34}
    
    result = _calculate_distribution(total, dist)
    
    # 33% of 3 is 0.99 (0). Remainder logic should fill the gap.
    assert sum(result.values()) == 3