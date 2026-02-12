# password_utils.py
import re

def validate_password_strength(password):
    """
    Validate password strength:
    - At least 8 characters long
    - Contains at least 1 uppercase letter
    - Contains at least 1 lowercase letter
    - Contains at least 1 number
    - Contains at least 1 special character
    """
    errors = []
    
    # Check length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    # Check for uppercase
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check for lowercase
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check for numbers
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    # Check for special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common passwords (you can expand this list)
    common_passwords = ['password123', 'admin123', '12345678', 'qwerty123', 
                       'password1', 'abc12345', 'iloveyou', 'monkey123']
    
    if password.lower() in common_passwords:
        errors.append("This password is too common. Please choose a stronger password")
    
    return errors

def check_password_complexity(password):
    """Return a score and feedback for password strength"""
    score = 0
    feedback = []
    
    # Length scoring
    if len(password) >= 12:
        score += 3
        feedback.append("✓ Excellent length")
    elif len(password) >= 10:
        score += 2
        feedback.append("✓ Good length")
    elif len(password) >= 8:
        score += 1
        feedback.append("✓ Minimum length met")
    else:
        feedback.append("✗ Too short")
    
    # Character variety scoring
    if re.search(r'[A-Z]', password):
        score += 1
        feedback.append("✓ Has uppercase letters")
    else:
        feedback.append("✗ Missing uppercase letters")
    
    if re.search(r'[a-z]', password):
        score += 1
        feedback.append("✓ Has lowercase letters")
    else:
        feedback.append("✗ Missing lowercase letters")
    
    if re.search(r'\d', password):
        score += 1
        feedback.append("✓ Has numbers")
    else:
        feedback.append("✗ Missing numbers")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 2
        feedback.append("✓ Has special characters")
    else:
        feedback.append("✗ Missing special characters")
    
    # Determine strength
    if score >= 7:
        strength = "Strong"
        color = "#6A8D53"
    elif score >= 4:
        strength = "Medium"
        color = "#FFA500"
    else:
        strength = "Weak"
        color = "#E74C3C"
    
    return {
        'score': score,
        'max_score': 8,
        'strength': strength,
        'color': color,
        'feedback': feedback
    }