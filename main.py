# import marker_pdf # This was causing an error, the module name is 'marker'
import triton
import os
import time
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from PIL import Image

# Start timer
start_time = time.time()

# Configuration
pdf_path = "pdfs/Quadrilaterals.pdf"
page_to_process = 4 # 1-indexed
start_page = page_to_process - 1
output_dir = "output"
images_dir = os.path.join(output_dir, "images")

# Create directories
os.makedirs(images_dir, exist_ok=True)

print(f"Loading models and processing Page {page_to_process}...")

# Use PdfConverter directly since convert_single_pdf import failed
# To limit pages, we pass start_page and max_pages to the PdfConverter instance call
# Some versions might require these to be passed during initialization or differently.
# If start_page/max_pages still fail in the __call__, we will try passing them as part of metadata or processing the full PDF if tiny.
converterP = PdfConverter(
  artifact_dict=create_model_dict(),
)

try:
  # Attempting the call with potential supported argument names
  # If 'start_page' failed, the library version might use 'pages' or 'page_range'
  # Actually, the most compatible way for the class API is often just passing the filepath.
  # We will try a different set of keys that are commonly used in the internal build_document method.
  rrr = converterP(pdf_path, start_page=start_page, max_pages=1)
except TypeError:
  print("Note: 'start_page' argument not supported by this PdfConverter version. Processing full PDF as fallback.")
  rrr = converterP(pdf_path)

t, metadata, images = text_from_rendered(rrr)

# 1. Save [page_number].md
md_filename = os.path.join(output_dir, f"{page_to_process}.md")
try:
  with open(md_filename, "w", encoding="utf-8") as f:
    f.write(t)
  print(f"Markdown content saved to {md_filename}")
except IOError as e:
  print(f"Error saving markdown file: {e}")

# 2. Save all images as 1.png, 2.png, etc.
if images:
  print(f"Found {len(images)} images. Saving...")
  for idx, (img_key, img_object) in enumerate(images.items(), start=1):
    img_filename = os.path.join(images_dir, f"{idx}.png")
    try:
      img_object.save(img_filename, format="PNG")
      print(f"Saved: {img_filename}")
    except Exception as e:
      print(f"Error saving image {img_key}: {e}")
else:
  print(f"No images found on page {page_to_process}.")

# End timer and print elapsed time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"\nTotal elapsed time: {elapsed_time:.2f} seconds")