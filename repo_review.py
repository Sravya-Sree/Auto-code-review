import streamlit as st
from github import Github 
from prompt import *
from metrics import *
import base64
from io import BytesIO
from PIL import Image

# Function to fetch files from a GitHub repository
def fetch_repo_files(repo_url, access_token):
    g = Github(access_token)
    repo_name = repo_url.rstrip('/').split("github.com/")[-1]
    repo = g.get_repo(repo_name)  # Try fetching the repository
    st.sidebar.success(f"Connected to {repo.full_name}")
    return repo  # Returns the repo object

# Function to display repository contents
def display_repo_contents(repo, contents,org_std_text,developer_mode):
    # Initialize placeholder for displaying folder/file contents
    content_placeholder = st.empty()

    # Store the initial contents on the first call
    if not st.session_state.root_contents:
        st.session_state.root_contents = contents
        st.session_state.current_files = contents  # Set initial files to root contents

    folders = []
    files = []

    # Separate folders and files based on the current directory contents
    for content in st.session_state.current_files:
        if content.type == "dir":
            folders.append(content)
        else:
            files.append(content)

    # Handle Back button if in a subfolder
    if st.session_state.current_path:
        if st.sidebar.button("🔙 Back"):
            # Go back to the previous path
            st.session_state.current_path.pop()
            # Set current files to previous folder's contents or root if at top level
            if st.session_state.current_path:
                previous_path = '/'.join(st.session_state.current_path)
                try:
                    st.session_state.current_files = repo.get_contents(previous_path)
                except Exception as e:
                    st.sidebar.write(f"Error retrieving contents of folder '{previous_path}': {e}")
            else:
                st.session_state.current_files = st.session_state.root_contents  # Reset to root contents
            
            # Toggle the refresh display to trigger a re-render
            st.session_state.refresh_display = not st.session_state.refresh_display

    # Display folders in the sidebar
    for folder in folders:
        folder_key = f"folder_{folder.path}"  # Use unique path as key
        if st.sidebar.button(f"📁 {folder.name}", key=folder_key):
            try:
                # Fetch contents of the folder on button click
                folder_contents = repo.get_contents(folder.path)
                # Update the current files state to the contents of this folder
                st.session_state.current_files = folder_contents
                # Update the current path
                st.session_state.current_path.append(folder.name)
                
                # Toggle the refresh display to trigger a re-render
                st.session_state.refresh_display = not st.session_state.refresh_display

            except Exception as e:
                st.sidebar.write(f"Error retrieving contents of folder '{folder.name}': {e}")

    # Display files at the current level in the content placeholder
    
    with content_placeholder.container():
        for file in files:
            if file.name == 'package-lock.json' or file.name == 'node_modules':
                st.text(file.name)  # Only display the name
            else:
                continue  # Skip displaying any other files

        # If `node_modules` folder is present, only display its name
        for folder in folders:
            if folder.name == 'node_modules':
                st.text(folder.name)  # Only display the name
                continue  # Skip displaying any other folders

        for file in files:
            file_key = f"file_{file.path}"  # Use unique path as key
            if st.sidebar.button(f"📄 {file.name}", key=file_key):
                # Fetch the file content directly from the repo
                try:
                  if file.encoding == "base64":
                      new_code_text = repo.get_contents(file.path).decoded_content.decode("utf-8")

                      # Define your parameters for generate_review_prompt
                      new_code_file_name = file.name
                      old_code_file_name = None  # Define this if you have an old code version
                      changes=None
                      language = "Python"  # Replace with actual language if necessary
                      author = "Author Name"  # Replace with actual author if needed
                      reviewer = "Reviewer Name"  # Replace with actual reviewer if needed
                      
                      # Call the function to generate the review prompt
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


