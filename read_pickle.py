import pickle
from pprint import pprint

# Replace 'your_file.pkl' with the actual path to your file
file_path = 'calibration_data/grid_calib.pkl'

try:
    with open(file_path, 'rb') as file:
        data = pickle.load(file)
    
    print("--- File Loaded Successfully ---\n")
    print(f"Data Type: {type(data)}\n")
    print("--- Contents ---")
    
    # pprint makes complex data (like dictionaries or lists) easier to read
    pprint(data)

except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found. Check the path.")
except pickle.UnpicklingError:
    print("Error: Could not unpickle the file. It might be corrupted.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
