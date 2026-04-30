import urllib.request
import os

pdf_links = {
    # Real paper for JSON vs Protobuf by Shatnawi
    "shatnawi_serialization.pdf": "https://www.scitepress.org/Papers/2025/134595/134595.pdf", # Guessing SCITEPRESS URL format
    # Real paper for Green Software Engineering SLR
    "penzenstadler_green_se.pdf": "https://arxiv.org/pdf/1312.6321.pdf", # Real SLR on Green SE
    # ISO SCI Specification (HTML but we can just save it or print instructions)
}

os.makedirs("references", exist_ok=True)

for filename, url in pdf_links.items():
    path = os.path.join("references", filename)
    print(f"Downloading {url} to {path}...")
    try:
        urllib.request.urlretrieve(url, path)
        print(f"Success: {filename}")
    except Exception as e:
        print(f"Failed: {filename} - {e}")
