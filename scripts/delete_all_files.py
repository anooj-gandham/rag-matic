import requests

# Base URL for your files endpoint.
API_URL = "http://localhost:8000/api/files/"

def get_all_files():
    """
    Retrieve all file objects from the API.
    
    Returns:
        list: A list of file objects.
    """
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    # If using DRF pagination, data may have a "results" key.
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    elif isinstance(data, list):
        return data
    else:
        return []

def delete_file(file_id: str):
    """
    Delete a file entry given its ID.
    
    Args:
        file_id (str): The ID of the file to delete.
    """
    delete_url = f"{API_URL}{file_id}/"  # Assuming the delete endpoint is /api/files/<id>/
    response = requests.delete(delete_url)
    response.raise_for_status()
    print(f"Deleted file: {file_id}")

def main():
    files = get_all_files()
    print(f"Found {len(files)} files to delete.")
    
    for file in files:
        file_id = file.get("id")
        if file_id:
            try:
                delete_file(file_id)
            except Exception as e:
                print(f"Error deleting file {file_id}: {e}")

if __name__ == "__main__":
    main()
