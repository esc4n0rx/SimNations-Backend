from typing import Dict, Any
from datetime import date, datetime

def validate_user_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate user registration data"""
    errors = {}
    
    if not data.get('name') or len(data['name']) < 2:
        errors['name'] = 'Name must be at least 2 characters'
    
    if not data.get('email') or '@' not in data['email']:
        errors['email'] = 'Valid email is required'
    
    if not data.get('password') or len(data['password']) < 8:
        errors['password'] = 'Password must be at least 8 characters'
    
    if not data.get('birth_date'):
        errors['birth_date'] = 'Birth date is required'
    elif isinstance(data['birth_date'], str):
        try:
            birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            if birth_date >= date.today():
                errors['birth_date'] = 'Birth date must be in the past'
        except ValueError:
            errors['birth_date'] = 'Invalid date format (YYYY-MM-DD)'
    
    return errors

def validate_quiz_answers(answers: list) -> Dict[str, str]:
    """Validate quiz answers"""
    errors = {}
    
    if len(answers) != 18:
        errors['answers'] = 'Must answer all 18 questions'
    
    categories = ['racionalidade', 'conservadorismo', 'audacia', 'autoridade', 'coletivismo', 'influencia']
    category_counts = {cat: 0 for cat in categories}
    
    for answer in answers:
        if answer.get('category') in category_counts:
            category_counts[answer['category']] += 1
        
        if not (1 <= answer.get('answer_value', 0) <= 5):
            errors['answer_value'] = 'Answer values must be between 1 and 5'
    
    for category, count in category_counts.items():
        if count != 3:
            errors[category] = f'Must have exactly 3 answers for {category}'
    
    return errors