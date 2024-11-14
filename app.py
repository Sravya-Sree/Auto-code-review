
import os
from dotenv import load_dotenv
import streamlit as st
from groq import Groq
from github import Github  # You'll need to install PyGithub

from ado import *
from pr import *
from config import *
from prompt import *
from metrics import *
from compare import *
from folder_review import *
from repo_review import *
from styles import get_styles
import pandas as pd
from IPython.display import display, HTML

# Load environment variables
load_dotenv()

st.markdown(get_styles(), unsafe_allow_html=True)

st.sidebar.image("/content/Picture1.png", width=700)
st.title("Automated Code Review")

client = Groq(api_key=groq_api_key)  # Replace with your API key

SUPPORTED_TEXT_TYPES = ['txt', 'docx', 'pdf', 'pptx']
SUPPORTED_CODE_TYPES = ['py', 'txt', 'java', 'js', 'html', 'css', 'sql', 'cs', 'c', 'cpp']

# File upload for organization code standard
org_std = st.file_uploader("Upload Organization Code Standard File", type=SUPPORTED_TEXT_TYPES)

# Radio button for code review type
review_type = st.sidebar.selectbox("Select Auto Code Review Type:", ["Files", "Folder", "Repos", "Pull Request", "ADO"])

# User role selection (Developer or Client)
user_type = st.selectbox("Do you need  Complete Code Review or a Summary?", ["Complete CodeReview", "Summary"])
developer_mode = (user_type == "Complete CodeReview")


# Conditional display based on selected review type
if review_type == "Files":
    # File uploads for new and old code
    new_code_file = st.file_uploader("Upload New Code File", type=SUPPORTED_CODE_TYPES)
    old_code_file = st.file_uploader("Upload Old Code File (Optional)", type=SUPPORTED_CODE_TYPES)

    # Warning if org std and new code files are not uploaded
    if org_std and new_code_file:
        st.success("Both Organization Standard and New Code Files uploaded.")
    elif org_std and not new_code_file:
        st.warning("Please upload the New Code File.")
    elif not org_std and new_code_file:
        st.warning("Please upload the Organization Code Standard File.")

    if org_std and not org_std.name.startswith("EStandards"):
        st.warning("The Org standards file must start with 'EStandards'.")
    if  new_code_file and old_code_file:
    #Call the function after deciding whether to analyze changes or the entire file
        new_code_file_name = new_code_file.name  # Get the name of the new code file
        old_code_file_name = old_code_file.name if old_code_file else None  # Check if old_code_file is None

            # Process the organizational standard and new code files
        org_std_text = process_file(org_std)
        new_code_text = process_file(new_code_file)

        # Use one if block to handle both the file name and content for old code file
        if old_code_file:
            old_file_extension = os.path.splitext(old_code_file_name)[1]
            old_code_text = process_file(old_code_file)
            #old_code_text = truncate_text(old_code_text)  # Truncate if the file exists
        else:
            old_code_text = None

        # Truncate large input texts to avoid exceeding token limits
        org_std_text = truncate_text(org_std_text)
        #new_code_text = truncate_text(new_code_text)
        if old_code_file:
            # Detect changes between old and new files
            data, changes = compare_code(old_code_text, new_code_text)
        else:
            changes = None

        if changes:
                #st.write(changes)
                st.write("Code Comparison")
                st.dataframe(data)
        else:
            if old_code_file:
                st.write("No changes were detected.")

    if org_std and new_code_file and org_std.name.startswith("EStandards"):
        # Extract file names and additional metadata
        new_code_file_name = new_code_file.name  # Get the name of the new code file
        old_code_file_name = old_code_file.name if old_code_file else None  # Check if old_code_file is None

        language_map = {
            ".py": "Python",
            ".java": "Java",
            ".js": "JavaScript",
            ".html": "HTML",
            ".css": "CSS",
            ".sql": "SQL",
            ".cs": ".NET",
            ".c": "C",
            ".cpp": "C++"
        }

        # Extract the file extension for new code file
        file_extension = os.path.splitext(new_code_file_name)[1]

        # Set the language dynamically for the new code file
        language = language_map.get(file_extension, "Unknown Language")

        # Additional metadata placeholders
        author = "Unknown"  # Placeholder for author's name
        reviewer = "Unknown"  # Placeholder for reviewer's name

        # Process the organizational standard and new code files
        org_std_text = process_file(org_std)
        new_code_text = process_file(new_code_file)

        # Use one if block to handle both the file name and content for old code file
        if old_code_file:
            old_file_extension = os.path.splitext(old_code_file_name)[1]
            old_code_text = process_file(old_code_file)
            #old_code_text = truncate_text(old_code_text)  # Truncate if the file exists
        else:
            old_code_text = None

        # Truncate large input texts to avoid exceeding token limits
        org_std_text = truncate_text(org_std_text)
        #new_code_text = truncate_text(new_code_text)

        # Save new code to a temporary file for linters
        temp_file_path = f"/tmp/{new_code_file_name}"
        with open(temp_file_path, "w") as temp_file:
            temp_file.write(new_code_text)

        # Call the function after deciding whether to analyze changes or the entire file
        if old_code_file:
            # Detect changes between old and new files
            data, changes = compare_code(old_code_text, new_code_text)
        else:
            changes = None

        # Generate review prompt with truncated text
        final_output, review1, review, errors_by_type= generate_review_prompt(org_std_text, new_code_text, changes,
                                                                            new_code_file_name=new_code_file_name,
                                                                            old_code_file_name=old_code_file_name,
                                                                            developer_mode=developer_mode,
                                                                            language=language, author=author,
                                                                            reviewer=reviewer)

        # Display results or error message based on the presence of changes
        if not final_output.strip():
            if old_code_file:
                st.markdown("**Select to analyze changes or new file**")
            else:
                st.error("Error: Generated review prompt is empty!")
        else:
            #st.write("Generated Review Prompt:")  # Display the prompt for debugging
            #st.code(review_prompt)  # Show the generated prompt
            
            # Call LLM with truncated text (LLM integration can stay the same)
            try:
                
                # Display response with the file name in the heading
                st.subheader(f"Code Review for [{new_code_file_name}]") 
                # Display the content with filename references replaced
                review_output = st.empty()
                review_output.markdown(f"<div class='response-box'>{final_output}</div>", unsafe_allow_html=True)

                # Calculate score based on the organization standards
                score_explain = calculate_score(org_std_text, new_code_text)
                if developer_mode:
                    st.write(f"Explanation: {score_explain}")  # Display dynamic score based on quality standards
                
                temp_file_path = "/tmp/" + new_code_file.name  # Create a temporary file path
                with open(temp_file_path, 'wb') as f:
                    f.write(new_code_file.getbuffer())
                error_counts = {error_type: len(errors) for error_type, errors in errors_by_type.items()}
                errors = error_counts
                # Read code lines if a file is uploaded
                code_lines = read_code_file(new_code_file)

                errors_by_type = {key: value for key, value in errors_by_type.items() if value}
                error_tabs_labels = [
                    f"{error_type} ({len(errors)})" 
                    for error_type, errors in errors_by_type.items() 
                    if errors
                ]
                error_tabs_labels.append("Improvements")

                if error_tabs_labels:  # Only create tabs if there are error types with errors
                    error_tabs = st.tabs(error_tabs_labels)
                    for error_tab, (error_type, errors) in zip(error_tabs, errors_by_type.items()):
                    # Only create a tab if there are errors of that type
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

                # Display the score with color
                st.markdown(f"### Severity Analysis")
                st.write(f"Total Errors: {sum(value for key, value in error_counts.items() if 'error' in key.lower())}")
                total_score_colored = f'<span style="color:{color}; font-size: 20px;">{total_score}</span>'
                message_colored = f'<span style="color:{color}; font-size: 20px;">{severity}</span>'
                st.markdown(f'Total Severity Score: {total_score_colored } - Severity: { message_colored }', unsafe_allow_html=True)
        
                # st.write(f"Total Severity Score: {total_score_colored }")
                # st.write(f"Severity: { message_colored }")              
                vulnerabilities_found = detect_vulnerabilities(new_code_text)
                # Display vulnerabilities and improvements
                if vulnerabilities_found:
                    st.subheader("Detected Vulnerabilities")
                    for vulnerability in vulnerabilities_found:
                        st.markdown(f"- {vulnerability}")
                else:
                    st.success("No vulnerabilities detected.")
                # Determine and display quality level of code
                # Determine and display quality level of code
                
                #st.write(f"Quality Level of Code: {severity}")

                # Classify URLs in the new code
                url_classification = classify_urls(new_code_text)
                if url_classification:
                    st.subheader("URL Classification")
                    for url, risk in url_classification.items():
                        st.write(f"{url}: {risk}")                  
                #review_content = chat_completion.choices[0].message.content.replace("[filename].(extension)", new_code_file_name)
                #st.write(review_content)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    else:
        st.warning("Please upload both the organization code standards file and the new code file.")  

elif review_type == "Folder":
    # Inputs for directory path and folder number
    directory_path = st.text_input("Enter Directory Path:", key='directory_input')
    folder_number = st.text_input("Enter Folder Number (5-6 digits):", key='folder_input')
    if org_std:
        # Display a message about the inputs
        if directory_path and folder_number:
            st.success("Directory path and folder number provided.")
        elif directory_path and not folder_number:
            st.warning("Please enter the Folder Number.")
        elif not directory_path and folder_number:
            st.warning("Please enter the Directory Path.")

        if org_std and directory_path and folder_number:
        # Create a placeholder for output and add some space below the input
            output_placeholder = st.empty()  # This will be used to display the output

            # When both inputs are provided, perform the code review
            if directory_path and folder_number:
                with output_placeholder.container():  # Use the placeholder to display output
                    st.write("")  # Add an empty line to create space
                    perform_code_review(directory_path, folder_number, org_std= org_std, developer_mode=developer_mode)
    else:
        st.warning("Please upload the organization code standards file")
elif review_type == 'Repos':
    access_token = st.text_input("Enter your GitHub Token:", type="password", key='github_token')
    repo_url = st.text_input("Enter GitHub Repository URL:", key='repo_url')
    
    if org_std:
        org_std_text = process_file(org_std)
        org_std_text = truncate_text(org_std_text)

        if access_token and repo_url:
            repo = fetch_repo_files(repo_url, access_token)
            # Check if the repository URL has changed
            if 'previous_repo_url' not in st.session_state or st.session_state.previous_repo_url != repo_url:
                # Clear relevant session state variables for new repo
                st.session_state.current_files = []
                st.session_state.current_path = []
                st.session_state.root_contents = []  # To store initial contents
                st.session_state.refresh_display = False  # Reset refresh display

                # Update previous_repo_url in session state
                st.session_state.previous_repo_url = repo_url

                # Fetch the repository contents
                repo = fetch_repo_files(repo_url, access_token)

                try:
                    root_contents = repo.get_contents("")  # Get root-level contents
                    st.session_state.root_contents = root_contents  # Save in session state
                    st.session_state.current_files = root_contents  # Initialize current files to root contents
                except Exception as e:
                    st.sidebar.error(f"Failed to load root contents: {e}")

            # Display the contents, passing the repo and root contents
            display_repo_contents(repo, st.session_state.current_files, org_std_text, developer_mode)
elif review_type == "Pull Request":
    access_token = st.text_input("Enter your GitHub Token:", type="password", key='github_token')
    repo_url = st.text_input("Enter GitHub Repository URL")   
    if access_token and repo_url:
        pull_requests = get_pull_requests(repo_url, access_token)
        
        
        pr_number = st.text_input("Enter Pull Request Number")
        st.session_state[f'merged_{pr_number}'] = False
        if not pr_number or not pr_number.strip():
            st.write("Error: PR number is empty or invalid.")
            exit()

        try:
            pr_number = int(pr_number)  # Ensure it's an integer
        except ValueError:
            st.write("Error: PR number must be a valid integer.")
            exit()
        g = Github(access_token)

        # Extract the repository name from the URL
        repo_name = repo_url.rstrip('/').split("github.com/")[-1]
        if not repo_name:
            raise ValueError("Invalid repository URL format.")

        # Fetch the repository
        repo = g.get_repo(repo_name)
        
        pull_request = repo.get_pull(pr_number)

        if org_std: 
          
          if pr_number:
            if not st.session_state[f'merged_{pr_number}']:
                    if st.sidebar.button('Approve Pull Request'):
                        try:
                            
                            pull_request.merge()
                          
                            st.session_state[f'merged_{pr_number}'] = True  # Set merged state to True
                            st.sidebar.success(f"Pull request {pr_number} merged successfully!")  # Show success message
                        except Exception as e:
                            st.error(f"Error merging pull request: {e}")
            files_changed = get_pull_request_diff(repo_url, pr_number, access_token)
                            
            # Display file diffs in a split view format with color-coding
            for file in files_changed:
                st.subheader(f"File: {file['filename']}")
                original, modified = st.columns(2)
                
                # Style and parse the patch data
                original_content, modified_content = style_diff_content(file['patch'])
                
                # Original content on the left
                with original:
                    st.markdown("#### Original Content")
                    st.markdown(original_content, unsafe_allow_html=True)
                
                # Modified content on the right
                with modified:
                    st.markdown("#### Modified Content")
                    st.markdown(modified_content, unsafe_allow_html=True)
             
            display_pr_review(repo_url,pr_number,org_std,access_token,developer_mode)
        else:
          st.warning("Upload Organisation Stamdards file")

elif review_type == 'ADO':

    # Input for Azure DevOps repository URL
    repo_url = st.text_input("Azure DevOps Repository URL", "https://dev.azure.com/everi/Everi-EnterpriseCoreServices/_git/AutomatedCodeReviewTest")
    pat = st.text_input("Personal Access Token", type="password")
    if org_std:
      org_std_text = process_file(org_std)
      org_std_text = truncate_text(org_std_text)

      if repo_url and pat:
          # Parse the URL to extract organization, project, and repository
          org, project, repo = parse_azure_devops_url(repo_url)
          if 'previous_repo_url' not in st.session_state or st.session_state.previous_repo_url != repo_url:
            # Clear relevant session state variables for new repo
            st.session_state.current_files = []
            st.session_state.current_path = []
            st.session_state.root_contents = []  # To store initial contents
            st.session_state.refresh_display = False  # Reset refresh display

            # Update previous_repo_url in session state
            st.session_state.previous_repo_url = repo_url

            # Fetch the repository contents
            org, project, repo = parse_azure_devops_url(repo_url)
            try:
                root_contents = repo.get_contents("")  # Get root-level contents
                st.session_state.root_contents = root_contents  # Save in session state
                st.session_state.current_files = root_contents  # Initialize current files to root contents
            except Exception as e:
                st.sidebar.error(f"Failed to load root contents: {e}")


          if org and project and repo:
              contents = get_repo_files(org, project, repo, pat)
          
              #display_repo_contents_ado(org, project, repo, org_std_text, developer_mode, pat)
              display_ado_repo_contents(org, project, repo, contents, org_std_text, developer_mode, pat=pat)
    else:
          st.warning("Upload Organisation Stamdards file")


st.markdown("<footer>&copy; 2024 Everi Holdings. All rights reserved.</footer>", unsafe_allow_html=True)
