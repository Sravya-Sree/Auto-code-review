import streamlit as st
import requests
import base64
import re
from io import BytesIO
from PIL import Image
from prompt import *
from metrics import *

# Function to parse the Azure DevOps URL and extract organization, project, and repository details
def parse_azure_devops_url(url):
    pattern = r'https://dev\.azure\.com/(?P<organization>[^/]+)/(?P<project>[^/]+)/_git/(?P<repository>[^/]+)'
    match = re.match(pattern, url)
    if match:
        return match.group('organization'), match.group('project'), match.group('repository')
    else:
        st.error("Invalid Azure DevOps URL format. Please check the URL and try again.")
        return None, None, None

# Function to fetch all repository items recursively from Azure DevOps
def get_repo_files(org, project, repo, pat):
    url = f'https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/items?recursionLevel=Full&api-version=6.0'
    headers = {
        'Authorization': f'Basic {base64.b64encode(f":{pat}".encode()).decode()}'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch repository contents: {response.status_code} - {response.text}")
        return None

# Function to fetch specific file content from Azure DevOps
def get_file_content(org, project, repo, path, pat):
    url = f'https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/items?path={path}&api-version=6.0'
    headers = {
        'Authorization': f'Basic {base64.b64encode(f":{pat}".encode()).decode()}'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        st.error(f"Failed to fetch file content for {path}: {response.status_code} - {response.text}")
        return None

# Display repository contents with support for Azure DevOps
def display_ado_repo_contents(org, project, repo, contents, org_std_text, developer_mode, pat=None):
    content_placeholder = st.empty()
    folders, files = [], []

    repo_contents = get_repo_files(org, project, repo, pat)
    
    if repo_contents:
        folders, files = [], []
        for item in repo_contents['value']:
            # Debug: print the item to see its structure
            # This will help you understand what keys are available
            if 'isFolder' in item and item['isFolder']:  # Check for 'isFolder'
                folders.append(item['path'])  # Store folder path as a string
            elif 'gitObjectType' in item and item['gitObjectType'] == 'blob':  # Check for blobs
                files.append(item['path'])  # Store file path as a string
        
        # Display folders in the sidebar
        for folder in folders:
            if st.sidebar.button(f"📁 {folder}"):
                st.session_state.current_path = folder
                st.session_state.refresh_display = not st.session_state.refresh_display
        
        with content_placeholder.container():
        # Display files in the sidebar
          for file in files:
              # Determine the file name based on the type of 'file'
              if isinstance(file, dict):  # Check if 'file' is a dictionary
                  file_name = file.get("path", "")  # Retrieve 'path' if available
              elif isinstance(file, str):  # Check if 'file' is a string
                  file_name = file  # Use the string directly as the file name
              else:
                  file_name = ""  # Default case for unexpected types
              if st.sidebar.button(f"📄 {file}"):
                try:
                  file_content = get_file_content(org, project, repo, file_name, pat)
                  if file_content:
                      st.write(f"### Content for [{file}]")
                      st.code(file_content, language='plaintext')  # Display the content in a code block

                      # Example parameters for review prompt
                      new_code_text = file_content
                      new_code_file_name = file_name
                      old_code_file_name = None
                      changes = None
                      language = "Python"
                      author = "Author Name"
                      reviewer = "Reviewer Name"
                      
                      # Generate review prompt (placeholder function call)
                      final_output, review1, review, errors_by_type = generate_review_prompt(
                          org_std_text, new_code_text, changes,
                          new_code_file_name=new_code_file_name,
                          old_code_file_name=old_code_file_name,
                          developer_mode=developer_mode,
                          language=language, author=author,
                          reviewer=reviewer
                      )

                        # Display review prompt output
                      st.write(f"### Code Review for [{new_code_file_name}]") 
                      review_output = st.empty()
                      review_output.markdown(f"<div class='response-box'>{final_output}</div>", unsafe_allow_html=True)

                      # Calculate score based on organizational standards
                      score_explain = calculate_score(org_std_text, new_code_text)
                      if developer_mode:
                          st.write(f"Explanation: {score_explain}") 

                      # Temporary file path for further analysis
                      temp_file_path = "/tmp/" + new_code_file_name
                      with open(temp_file_path, 'w') as f:  # Use 'w' for text files
                          f.write(new_code_text)

                      error_counts = {error_type: len(errors) for error_type, errors in errors_by_type.items()}
                      errors = error_counts
                      errors_by_type = {key: value for key, value in errors_by_type.items() if value}

                      # Display error information in tabs
                      error_tabs_labels = [
                          f"{error_type} ({len(errors)})" 
                          for error_type, errors in errors_by_type.items() 
                          if errors
                      ]
                      error_tabs_labels.append("Improvements")

                      if error_tabs_labels:  # Only create tabs if there are error types with errors
                          error_tabs = st.tabs(error_tabs_labels)
                          for error_tab, (error_type, errors) in zip(error_tabs, errors_by_type.items()):
                              if errors:  # Only create a tab if there are errors of that type
                                  with error_tab:
                                      st.write(f"### **{error_type}**")
                                      for i, error in enumerate(errors, start=1):
                                          st.write(f"{error}")
                          with error_tabs[len(errors_by_type)]:
                              st.write("### **Improvements**")
                              st.write(review)
                      else:
                          st.write("No errors found in this file.")

                      # Display the calculated total severity score and its classification
                      total_score = calculate_severity(error_counts)  # Calculate total severity score
                      color, severity = determine_severity_from_score(total_score)  # Determine the severity level
                      total_score_colored = f'<span style="color:{color}; font-size: 20px;">{total_score}</span>'
                      message_colored = f'<span style="color:{color}; font-size: 20px;">{severity}</span>'
                      st.markdown(f'Total Severity Score: {total_score_colored } - Severity: { message_colored }', unsafe_allow_html=True)

                      # Detect vulnerabilities
                      vulnerabilities_found = detect_vulnerabilities(new_code_text)
                      if vulnerabilities_found:
                          st.subheader("Detected Vulnerabilities")
                          for vulnerability in vulnerabilities_found:
                              st.markdown(f"- {vulnerability}")
                      else:
                          st.success("No vulnerabilities detected.")

                      # Classify URLs in the new code
                      url_classification = classify_urls(new_code_text)
                      if url_classification:
                          st.subheader("URL Classification")
                          for url, risk in url_classification.items():
                              st.write(f"{url}: {risk}")   
                  else:
                        st.warning(f"File '{file.name}' has unsupported encoding: {file.encoding}")               

                except UnicodeDecodeError:
                # If a decoding error occurs, check if the file is an image
                  if file.name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')):
                      # Display the image directly
                      image_data = repo.get_contents(file.path).decoded_content
                      image = Image.open(BytesIO(image_data))  # Open image with PIL
                      st.image(image, caption=f"Image: {file.name}", use_column_width=True)
                  else:
                      # For non-image files, display the raw bytes
                      raw_bytes = repo.get_contents(file.path).decoded_content
                      st.write(f"### Raw Content for [{file.name}]")
                      st.text(raw_bytes)  # Display the raw bytes

  