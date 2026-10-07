import re

text = "The event has 25 participants, a budget of 15000.50 rupees, and 3 sponsors this year 2026."

pattern = r'\d+\.?\d*'
numbers = re.findall(pattern, text)

print(numbers)