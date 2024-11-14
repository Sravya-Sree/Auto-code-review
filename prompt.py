from config import *
from groq import Groq
from datetime import datetime, timedelta
import streamlit as st
client = Groq(api_key=groq_api_key)  # Replace with your API key
import re
from collections import defaultdict
from metrics import *

# Function to truncate text to a certain number of characters
def truncate_text(text, max_length=1500):  # Reduce max length if necessary
    return text[:max_length] if len(text) > max_length else text

# LLM prompt generation based on developer or client role
def get_code_review(file_content, file_name):
    prompt = (
        f"Review the following code in the file {file_name}. Provide an explanation of the code, "
        f"identify any errors for each type of error, and display the type of error in bold as a title. "
        f"Include all the errors belonging to that type, using numbering in different lines, and include line numbers for each error identified.\n"
        f"{file_content}\n\n"
        
        f"Your code has been rated at <rating>/10\n"
        f"--- Errors ---\n"
    )  
    try:
        # Call the LLaMA model to generate the review and improved code
        prompt_response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="Llama3-70b-8192",
        )

        # Access the correct attribute for the response content
        if prompt_response and prompt_response.choices:
            review_content = prompt_response.choices[0].message.content
            # Parse the review content to get errors
            errors_by_type = parse_review_content(review_content)
            return review_content, errors_by_type
        else:
            return "No response received from the model.", {}

    except Exception as e:
        if '401' in str(e):
            return "Authentication failed. Please check your API key.", {}
        else:
            return f"Error while fetching code review: {str(e)}", {}
        

def generate_review_prompt(org_std_text, new_code_text, changes, new_code_file_name=None, developer_mode=None, old_code_file_name=None, language=None, author=None, reviewer=None):
    date_str = datetime.now().strftime("%Y-%m-%d")  # Get current date
    org_std_text = truncate_text(org_std_text)  # Truncate organization standards
    new_code_text = truncate_text(new_code_text)  # Truncate new code text
    review = ""
    review1 = ""
    errors_by_type = {}
 
    # Initialize the prompt variable
    prompt = (f"""File: {new_code_file_name}
 
                    Language: {language}
                    Author: {author}
                    Reviewer: {reviewer}
                    Date: {date_str}
            """)
 
    prompt_response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="Llama3-70b-8192",
    )
 
    prompt_1 = prompt_response.choices[0].message.content
 
    if changes is None:
        if developer_mode:
            explain_prompt = (
                "\nExplain what the following code is trying to do in a detailed explaination\n"
                f"Code: {new_code_text}"
            )
 
            explain_response = client.chat.completions.create(
                messages=[{"role": "user", "content": explain_prompt}],
                model="Llama3-70b-8192",
            )
 
            explanation = explain_response.choices[0].message.content
 
            

 
            review_prompt = (
                "\nGenerate a complete code review for the following code file, "
                "including Improved Code, suggested improvements based on the provided organization standards:\n"
                f"Standards: {org_std_text}\n"
                f"Code: {new_code_text}"
            )
 
            review_response = client.chat.completions.create(
                messages=[{"role": "user", "content": review_prompt}],
                model="Llama3-70b-8192",
            )
 
            review = review_response.choices[0].message.content
            review1, errors_by_type = get_code_review(new_code_text, new_code_file_name)
 
            final_output = (
                f"{prompt_1}<br><br>"
                f"<strong>Explanation:</strong> {explanation}<br><br>"
            )
             
        else:
            
            explain_prompt = (
         "Provide a summary of code review for the following code file in 5 lines based on the standards, "
                        ""
                        f"Standards: {org_std_text}\n"
                        f"Code: {new_code_text}"
    )
            
            explain_response = client.chat.completions.create(
                messages=[{"role": "user", "content": explain_prompt}],
                model="Llama3-70b-8192",
            )
            
            explanation = explain_response.choices[0].message.content

            

            # Step 3: Generate the complete code review
            review_prompt = (
                "\nGenerate a complete code review for the following code file, "
                "including Improved Code, suggested improvements based on the provided organization standards:"
                f"Standards: {org_std_text}\n"
                f"Code: {new_code_text}"
            )

            review_response = client.chat.completions.create(
                messages=[{"role": "user", "content": review_prompt}],
                model="Llama3-70b-8192",
            )

            # Extract review content
            review = review_response.choices[0].message.content
            review1, errors_by_type = get_code_review(new_code_text, new_code_file_name)

            # Combine all responses
            final_output = (
        f"<strong>Explanation:</strong> {explanation}<br><br>"
)
        
    else:
        final_output = ''
        # Changes are provided, set up the prompt based on user interaction
        col1, col2 = st.columns(2)
        
        if developer_mode:
            # Developer mode logic
            with col1:
                if st.button('Analyze Changes'):
                    
                    explain_prompt = (
                        "\n Explain what the following code is trying to do in a detailed explaination\n"
                        f"Code: {changes}"
                    )
               
                    explain_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": explain_prompt}],
                        model="Llama3-70b-8192",
                    )
                    
                    explanation = explain_response.choices[0].message.content

                    # Step 1: Create prompts to get different types of errors

                    # Step 3: Generate the complete code review
                    review_prompt = (
                        "\nGenerate a complete code review for the following code file, "
                        "including Improved Code, suggested improvements based on the provided organization standards:"
                        f"Standards: {org_std_text}\n"
                        f"Code: {changes}"
                    )

                    review_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": review_prompt}],
                        model="Llama3-70b-8192",
                    )

                    # Extract review content
                    review = review_response.choices[0].message.content
                    review1, errors_by_type = get_code_review(new_code_text, new_code_file_name)

                    
                    # Combine all responses
                    final_output = (
        f"{prompt_1}<br><br>"
        f"<strong>Explanation:</strong> {explanation}<br><br>"
        )

            with col2:
                if st.button('Analyze with New File'):
                    
                    explain_prompt = (
                    "\n Explain what the following code is trying to do in a detailed explaination\n"
                    f"Code: {new_code_text}"
                )
               
                    explain_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": explain_prompt}],
                        model="Llama3-70b-8192",
                    )
                    
                    explanation = explain_response.choices[0].message.content

                    # Step 1: Create prompts to get different types of errors
                    

                    # Step 3: Generate the complete code review
                    review_prompt = (
                        "\nGenerate a complete code review for the following code file, "
                        "including Improved Code, suggested improvements based on the provided organization standards:"
                        f"Standards: {org_std_text}\n"
                        f"Code: {new_code_text}"
                    )

                    review_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": review_prompt}],
                        model="Llama3-70b-8192",
                    )

                    # Extract review content
                    review = review_response.choices[0].message.content
                    review1, errors_by_type = get_code_review(new_code_text, new_code_file_name)
                    

                    # Combine all responses
                    final_output = (
        f"{prompt_1}<br><br>"
        f"<strong>Explanation:</strong> {explanation}<br><br>"
        )
                    f"""
                    Date:
                    {date_str}
                    """
        else:
            # Client mode logic (summarize only)
            with col1:
                if st.button('Analyze Changes'):

                    explain_prompt = (
                        "Provide a summary of code review for the following code file in 5 lines based on the standards, "
                        ""
                        f"Standards: {org_std_text}\n"
                        f"Code: {changes}"
                    )
            
                    explain_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": explain_prompt}],
                        model="Llama3-70b-8192",
                    )
                    
                    explanation = explain_response.choices[0].message.content


                    # Step 3: Generate the complete code review
                    review_prompt = (
                        "\nGenerate a complete code review for the following code file, "
                        "including Improved Code, suggested improvements based on the provided organization standards:"
                        f"Standards: {org_std_text}\n"
                        f"Code: {changes}"
                    )

                    review_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": review_prompt}],
                        model="Llama3-70b-8192",
                    )

                    # Extract review content
                    review = review_response.choices[0].message.content

                    review1, errors_by_type = get_code_review(new_code_text, new_code_file_name)

                    # Combine all responses
                    final_output = (
        f"<strong>Explanation:</strong> {explanation}<br><br>"
        )
                    

            with col2:
                if st.button('Analyze with New File'):

                    explain_prompt = (
                        "Provide a summary of code review for the following code file in 5 lines based on the standards, "
                        ""
                        f"Standards: {org_std_text}\n"
                        f"Code: {new_code_text}"
                    )
            
                    explain_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": explain_prompt}],
                        model="Llama3-70b-8192",
                    )
                    
                    explanation = explain_response.choices[0].message.content

                    # Step 1: Create prompts to get different types of errors
                    

                    # Step 3: Generate the complete code review
                    review_prompt = (
                        "\nGenerate a complete code review for the following code file, "
                        "including Improved Code, suggested improvements based on the provided organization standards:"
                        f"Standards: {org_std_text}\n"
                        f"Code: {new_code_text}"
                    )

                    review_response = client.chat.completions.create(
                        messages=[{"role": "user", "content": review_prompt}],
                        model="Llama3-70b-8192",
                    )

                    # Extract review content
                    review = review_response.choices[0].message.content
                    review1, errors_by_type = get_code_review(new_code_text, new_code_file_name)
                    
                    # Combine all responses
                    final_output = (
        f"{prompt_1}<br><br>"
        f"<strong>Explanation:</strong> {explanation}<br><br>"
        )  
        
    return final_output, review1, review, errors_by_type




