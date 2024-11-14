# styles.py
def get_styles():
    return """
    <style>
    /* Main background color */
    .main {
        background-color: white; /* Light grayish blue */
        color: #333333; /* Darker text color for contrast */
        font-family: 'Arial', sans-serif;
    }
    /* Title styling */
    h1 {
        text-align: center;
        color: #4a90e2; /* Soft blue */
    }
    /* Button styling */
    .stButton>button {
        background-color: #4a90e2; /* Soft blue button */
        color: white;
        border: None;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #357ab8; /* Darker shade on hover */
    }
    .sidebar-title {
        font-size: 30px;
        font-weight: bold;
        color: #2C6E91; /* Change this to the color of your choice */
        text-align: center;
        font-family: 'Arial', sans-serif;
        padding: 20px;
    }
   
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #e1e9f0; /* Lighter grayish blue */
        color: #333333; /* Text color for contrast */
        padding: 20px;
    }
    /* Input box styling */
    .stTextInput>div>input {
        background-color: #ffffff; /* White background for input */
        color: #333333; /* Input text color */
        border: 1px solid #4a90e2; /* Border color */
        border-radius: 5px;
        padding: 10px;
    }
    /* Response box styling */
    .response-box {
        background-color: #ffffff; /* White background for response box */
        color: #333333; /* Text color for readability */
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #4a90e2; /* Accent color */
        white-space: pre-wrap; /* Preserve formatting */
        width: 100%;
         /* Improved line height for readability */
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */
    }
   
    /* Footer styling */
    footer {
        text-align: center;
        padding: 20px;
        color: #4a90e2; /* Soft blue */
    }
    </style>
    """
