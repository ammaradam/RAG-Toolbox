import os

def save_uploaded_file(uploaded_file):
    file_path = os.path.join('data', 'temp.pdf')
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path