from config import *
from groq import Groq
import re
client = Groq(api_key=groq_api_key)  # Replace with your API key

import streamlit as st
import re

def calculate_score(org_std_text, new_code):
    # Define prompts based on organizational code standards
    explain_prompt = (
                        "Give only Score out of 10 of following code based on Organisation Standards:\n"
                        f"Code: {new_code}"
                        f"Organisation Standards: {org_std_text}"
                    )
            
    explain_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": explain_prompt}],
                        model="Llama3-70b-8192",
                    )
                    
    explanation = explain_response.choices[0].message.content
    
    # Assuming the response is a score as a float, parse it
    score_match = re.search(r'\d+(\.\d+)?', explanation)  # This will match a number (integer or float)

    if score_match:
        score = float(score_match.group(0))  # Extract the score and convert it to a float
    else:
        st.error("Failed to parse the score from the response.")
        return None, None

    # Display color based on score
    if score >= 9:
        color = "green"
        message = "Excellent"
    elif score >= 7:
        color = "yellow"
        message = "Good"
    elif score >= 4:
        color = "orange"
        message = "Average"
    else:
        color = "red"
        message = "Poor"

    # Display the score with color
    score_colored = f'<span style="color:{color}; font-size: 20px;">{score}</span>'
    message_colored = f'<span style="color:{color}; font-size: 20px;">{message}</span>'
    st.subheader('Overall score based on standards')
    st.markdown(f'Overall Score: {score_colored} - {message_colored}', unsafe_allow_html=True)

    return explanation  # Ensure both are returned


# Enhanced URL classification
def classify_urls(code_text):
    if isinstance(code_text, st.runtime.uploaded_file_manager.UploadedFile):
        code_text = code_text.read().decode("utf-8")  # Decode as text

    # Ensure code_text is a string to avoid errors
    if not isinstance(code_text, str):
        code_text = str(code_text) if code_text is not None else ""

    url_pattern = r'https?://[^\s")]+'
    urls = re.findall(url_pattern, code_text)
    url_classification = {}

    for url in urls:
        if url.startswith("https"):
            url_classification[url] = "Low Risk - Secure (HTTPS)"
        elif url.startswith("http"):
            url_classification[url] = "Medium Risk - Insecure (HTTP)"
        elif "localhost" in url or "127.0.0.1" in url:
            url_classification[url] = "Low Risk - Localhost"
        else:
            url_classification[url] = "High Risk - Unknown or Suspicious Domain"

    return url_classification

# Define weights for each error type
error_weights = {
    "Syntax Errors": 3,
    "Run-time Errors": 4,
    "Logical Errors": 2,
    "Validation Errors": 1,
    "Compile-time Errors": 4
}

# Function to calculate total severity score from the dictionary {error_type: count}
def calculate_severity(error_count):
    total_score = 0
    
    # Iterate over the error_count dictionary
    for error_type, count in error_count.items():
        # Check if the error_type exists in the predefined weights
        if error_type in error_weights:
            # Multiply the count by the weight of the error type and add it to the total score
            
            total_score += count * error_weights[error_type]
    
    return total_score

# Determine severity level based on the total score
def determine_severity_from_score(total_score):
    if total_score == 0:
        color = "darkgreen"
        message = "No errors, perfect!"
    elif total_score <= 10:
        color = "lightgreen"
        message =  "Low severity"
    elif 11 <= total_score <= 20:
        color = "yellow"
        message = "Medium severity"
    elif 21 <= total_score <= 30:
        color = "orange"
        message = "High severity"
    else:
        color = "red"
        message = "Critical severity"
    

    return color, message

# Define a function for vulnerability detection
def detect_vulnerabilities(code):

    if isinstance(code, st.runtime.uploaded_file_manager.UploadedFile):
        code = code.read().decode("utf-8")  # Decode as text

    # Ensure code is a string to avoid errors
    if not isinstance(code, str):
        code = str(code) if code is not None else ""

    vulnerabilities = []

    # Example checks for vulnerabilities
    if "eval(" in code or "exec(" in code:
        vulnerabilities.append("Avoid using eval() or exec() as they can lead to code injection vulnerabilities.")

    if re.search(r"(\bSELECT\b|\bUPDATE\b|\bDELETE\b|\bINSERT\b)\s+\w+\s+FROM\s+\w+\s*;", code, re.IGNORECASE):
        vulnerabilities.append("Possible SQL Injection vulnerability detected. Use parameterized queries instead.")

    # Check for common XSS patterns
    if re.search(r"<script.*?>", code, re.IGNORECASE):
        vulnerabilities.append("Potential Cross-Site Scripting (XSS) vulnerability detected. Avoid using inline scripts.")

    # Check for hardcoded credentials (this is a simplistic check)
    if re.search(r"(password|secret|api_key)\s*=\s*['\"].*['\"]", code, re.IGNORECASE):
        vulnerabilities.append("Hardcoded credentials detected. Consider using environment variables or a secure vault.")

    return vulnerabilities


def parse_review_content(review_content):
    # Initialize the dictionary to hold errors by type
    errors_by_type = {
        'Syntax Errors': [],
        'Semantic Errors': [],
        'Compilation Errors': [],
        'Structural Errors': [],
        'Logic Errors': [],
        'Runtime Errors': [],
        'Unused Code': [],
        'Unused Variables': [],
        'Vulnerabilities': [],
        'Improved Code': []  # Separate section for improved code
    }

    current_error_type = None
    lines = review_content.strip().split('\n')

    for line in lines:
        line = line.strip()

        # Detecting the error type section headers
        if "Syntax Errors" in line:
            current_error_type = 'Syntax Errors'
        elif "Semantic Errors" in line:
            current_error_type = 'Semantic Errors'
        elif "Structural Errors" in line:
            current_error_type = 'Structural Errors'
        elif "Compilation Errors" in line:
            current_error_type = 'Compilation Errors'
        elif "Logical Errors" in line or "Logic Errors" in line:
            current_error_type = 'Logic Errors'
        elif "Runtime Errors" in line:
            current_error_type = 'Runtime Errors'
        elif "Unused Code" in line:
            current_error_type = 'Unused Code'
        elif "Unused Variables" in line:
            current_error_type = 'Unused Variables'
        elif "Vulnerabilities" in line:
            current_error_type = 'Vulnerabilities'
        else:
            # If in an error section, append the line to the corresponding section
            if current_error_type and line:
                errors_by_type[current_error_type].append(line)

    return errors_by_type



