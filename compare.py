import difflib
from difflib import SequenceMatcher
import pandas as pd

def highlight_diff(old_line, new_line):
    """Highlight differences between two lines."""
    matcher = difflib.SequenceMatcher(None, old_line, new_line)
    highlighted_new = ""
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            highlighted_new += new_line[j1:j2]  # Unchanged part
        elif tag == 'replace':
            highlighted_new += f'**{new_line[j1:j2]}**'  # Highlight modified part
        elif tag == 'insert':
            highlighted_new += f'**{new_line[j1:j2]}**'  # Highlight added part

    return highlighted_new

def compare_code(old_code, new_code):
    # Split the code into lines
    old_code_lines = old_code.splitlines(keepends = True)
    new_code_lines = new_code.splitlines(keepends = True)

    # Use difflib to find differences
    diff = list(difflib.ndiff(old_code_lines, new_code_lines))

    changes = {
        'Old Code': [],
        'New Code': [],
        'Old Line Number': [],
        'New Line Number': [],
        'Change Type': [],
    }
    old_line_count = 1
    new_line_count = 1
    i = 0
    while i < len(diff):
        line = diff[i]

        if line.startswith('- '):
            # Handle removal or modification
            if i + 1 < len(diff) and diff[i + 1].startswith('? '):
                # This indicates a modification
                if i + 2 < len(diff) and diff[i + 2].startswith('+ '):
                    # Get the new modified line
                    new_line = diff[i + 2][2:]
                    highlighted_new = highlight_diff(line[2:], new_line)
                    
                    # Store the old and new lines along with the change type
                    changes['Old Code'].append(line[2:])
                    changes['New Code'].append(highlighted_new)
                    changes['Old Line Number'].append(old_line_count)
                    changes['New Line Number'].append(new_line_count)
                    changes['Change Type'].append('Modified')
                    old_line_count += 1
                    new_line_count += 1
                    i += 2  # Skip the next modification marker
                else:
                    # Handle a removed line
                    changes['Old Code'].append(line[2:])
                    changes['New Code'].append('')
                    changes['Old Line Number'].append(old_line_count)
                    changes['New Line Number'].append('')
                    changes['Change Type'].append('Removed')
                    old_line_count += 1
            else:
                # Handle a removed line without modification
                changes['Old Code'].append(line[2:])
                changes['New Code'].append('')
                changes['Old Line Number'].append(old_line_count)
                changes['New Line Number'].append('')
                changes['Change Type'].append('Removed')
                old_line_count += 1

        elif line.startswith('+ '):
            # Handle added line
            if i == 0 or not diff[i - 1].startswith('- '):
                changes['Old Code'].append('')
                changes['New Code'].append(line[2:])
                changes['Old Line Number'].append('')
                changes['New Line Number'].append(new_line_count)
                changes['Change Type'].append('Added')
                new_line_count += 1

        elif line.startswith('? '):
            # Ignore these lines, they are used by ndiff to indicate character-level differences
            pass
        
        else:
            # Handle unchanged lines
            old_line_count += 1
            new_line_count += 1
        
        i += 1  # Move to the next line

    # Convert to DataFrame for tabular display
    df_changes = pd.DataFrame(changes)
    # Remove rows where both 'Old Code' and 'New Code' are empty
    # Remove rows where both 'Old Code' and 'New Code' are empty or whitespace
    df_changes = df_changes[~((df_changes['Old Code'].str.strip() == '') & (df_changes['New Code'].str.strip() == ''))]


    
    return df_changes, diff
