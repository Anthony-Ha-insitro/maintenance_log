import streamlit as st
import pandas as pd
import os
import datetime
import re
import fnmatch
import json  # Keep this import

# Set page configuration
st.set_page_config(page_title="Maintenance Monitor", page_icon="🔬", layout="wide")

# Function to process TRC files with tracking of previously processed files
def process_trc_files(folder_path):
    """
    Process .trc files, check for maintenance status.
    Skips files that haven't changed since last processing.
    """
    results = []

    # Check if folder exists
    if not os.path.exists(folder_path):
        st.error(f"Folder not found: {folder_path}")
        return results
    
    # Path for tracking processed files
    # tracking_file = os.path.join(folder_path, ".processed_files.json")
    
    # Load previously processed files data if available
    # processed_files = {}
    # if os.path.exists(tracking_file):
    #     try:
    #         with open(tracking_file, 'r') as f:
    #             processed_files = json.load(f)
    #     except Exception as e:
    #         st.warning(f"Could not load tracking file: {str(e)}")
    
    serial_patterns = [
        r"Instrument\s+Serial\s+No:\s+(\d+)"
    ]

    # List files in the directory
    try:
        files = os.listdir(folder_path)
    except Exception as e:
        st.error(f"Error accessing directory: {str(e)}")
        return results

    # Count stats
    # new_or_modified_count = 0
    # skipped_count = 0

    for filename in files:
        if filename.lower().endswith(".trc") and fnmatch.fnmatch(filename, "VOVDailyMaintenance*"):
            trc_path = os.path.join(folder_path, filename)
            
            # Get file modification time
            try:
                mod_time = os.path.getmtime(trc_path)
                
                # Skip if file hasn't changed since last processing
                # if filename in processed_files and processed_files[filename]["mod_time"] == mod_time:
                #     # File unchanged - use cached result
                #     results.append(processed_files[filename]["result"])
                #     skipped_count += 1
                #     continue
                
                # File is new or modified - process it
                # new_or_modified_count += 1
                
                date_str = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')

                # Read content directly
                with open(trc_path, 'r', errors='ignore') as f:
                    content = f.read()

                # Extract the serial number
                serial_number = "Unknown"
                for pattern in serial_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        serial_number = match.group(1).strip()

                # Assign instrument name based on serial number
                if serial_number == "1000":
                    instrument_name = "Banyan"
                elif serial_number == "1526":
                    instrument_name = "Eucalyptus"
                elif serial_number == "1650":
                    instrument_name = "Palm"
                else:
                    instrument_name = f"Unknown instrument: {serial_number}"

                # Check for success keyword
                if "daily maintenance succeeded" in content.lower():
                    status = "Success"
                elif "daily maintenance failed" in content.lower():
                    status = "Failed"
                else:
                    status = "Error"
 
                # Create result dictionary
                result = {
                    "filename": filename,
                    "instrument_name": instrument_name,
                    "serial_number": serial_number,
                    "date": date_str,
                    "status": status,
                    "method": "VOVDailyMaintenance.hsl"
                }
                
                # Store result
                results.append(result)
                
                # Update tracking information
                # processed_files[filename] = {
                #     "mod_time": mod_time,
                #     "result": result
                # }
                
            except Exception as e:
                error_msg = f"{filename}: ERROR - {str(e)}"
                print(error_msg)
                results.append({
                    "filename": filename,
                    "error": str(e),
                    "status": "ERROR"
                })

    # Save updated tracking information
    # try:
    #     with open(tracking_file, 'w') as f:
    #         json.dump(processed_files, f)
    # except Exception as e:
    #     st.warning(f"Could not save tracking file: {str(e)}")

    # Show processing stats
    # st.info(f"Processed {new_or_modified_count} new/modified files. Skipped {skipped_count} unchanged files.")
    
    return results

# Begin Streamlit app UI
st.title("🔬 Maintenance Monitoring Dashboard")
st.markdown("### Track instrument maintenance status")

# Define your specific paths here
predefined_paths = {
    "Main Laboratory": "/Users/anthony.ha/Documents/TEST FOLDER/Files",
    "Backup Server": "/path/to/backup/server/traces",
    "Lab Station 1": "/path/to/lab1/traces",
    "Lab Station 2": "/path/to/lab2/traces",
    # Add more paths as needed
}

# Path selection
st.markdown("### Select Folder to Process")
path_option = st.radio(
    "Choose path option:",
    ["Use Predefined Path", "Enter Custom Path"]
)

if path_option == "Use Predefined Path":
    location_name = st.selectbox(
        "Select location:",
        list(predefined_paths.keys())
    )
    folder_path = predefined_paths[location_name]
    st.info(f"Selected path: {folder_path}")
else:
    folder_path = st.text_input(
        "Enter custom folder path:",
        value="/Users/anthony.ha/Documents/TEST FOLDER/Files"
    )

# Process files when user clicks the button
if st.button("Process Maintenance Files"):
    with st.spinner(f"Processing files from {folder_path}..."):
        results = process_trc_files(folder_path)
    
    if not results:
        st.warning("No maintenance files found in the specified folder.")
    else:
        # Convert results to DataFrame for easy display
        df = pd.DataFrame(results)
        
        # Show summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Files", len(df))
        
        with col2:
            if 'status' in df.columns:
                success_count = len(df[df['status'] == 'Success'])
                st.metric("Successful Maintenance", success_count)
        
        with col3:
            if 'status' in df.columns:
                fail_count = len(df[df['status'].isin(['Failed', 'Error'])])
                st.metric("Failed Maintenance", fail_count, delta=None, delta_color="inverse")
        
        # Filter options
        st.markdown("### Filter Results")
        
        # Filters if available columns exist
        if 'instrument_name' in df.columns:
            instruments = ['All'] + sorted(df['instrument_name'].unique().tolist())
            selected_instrument = st.selectbox("Select Instrument:", instruments)
        
        if 'date' in df.columns:
            dates = ['All'] + sorted(df['date'].unique().tolist())
            selected_date = st.selectbox("Select Date:", dates)
            
        # Apply filters
        filtered_df = df.copy()
        
        if 'instrument_name' in df.columns and selected_instrument != 'All':
            filtered_df = filtered_df[filtered_df['instrument_name'] == selected_instrument]
            
        if 'date' in df.columns and selected_date != 'All':
            filtered_df = filtered_df[filtered_df['date'] == selected_date]
        
        # Display the filtered results
        st.markdown("### Maintenance Results")
        
        # Determine which columns to show
        if 'error' in filtered_df.columns:
            # Show different columns for error records
            error_df = filtered_df[filtered_df['status'] == 'ERROR']
            if not error_df.empty:
                st.error("Errors found in processing")
                st.dataframe(error_df[['filename', 'error']])
        
        # Show main results
        if 'status' in filtered_df.columns:
            # Define highlight function
            def highlight_status(val):
                if val == 'Success':
                    return 'background-color: #8eff8e'
                elif val == 'Failed' or val == 'Error':
                    return 'background-color: #ff8e8e'
                return ''
            
            display_cols = ['instrument_name', 'serial_number', 'date', 'status', 'method']
            display_cols = [col for col in display_cols if col in filtered_df.columns]
            filtered_display_df = filtered_df[display_cols]

            # Apply styling to the selected dataframe
            styled_df = filtered_display_df.style.applymap(
                highlight_status, subset=['status'] if 'status' in display_cols else []
            )
            
            # FIXED: Don't select columns from Styler object
            st.dataframe(styled_df, width=800)
        else:
            st.dataframe(filtered_df)
        
        # Download option
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name="maintenance_results.csv",
                mime="text/csv",
            )

# Add sidebar information
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    This dashboard monitors instrument maintenance status.
    
    It processes trace files to extract maintenance results for various instruments.
    """
)
