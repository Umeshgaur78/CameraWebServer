import re

text = """Please contact us at support@college.edu or
admin.office@university.ac.in
for queries. You can also reach john_doe123@gmail.com for technical
help."""

pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

emails = re.findall(pattern, text)

print("Extracted Email IDs:")
print(emails)