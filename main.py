import os
import time
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser
from PIL import Image

# --- CONFIGURATION ---
# Set to a number (1-indexed, e.g., 4) to process a specific page.
# Set to None to process the full PDF.
PAGE_NUMBER = 4 

pdf_path = "pdfs/Quadrilaterals.pdf"
output_dir = "output"
images_dir = os.path.join(output_dir, "images")
# ---------------------

# Start timer
start_time = time.time()

# We use the official ConfigParser to ensure correct mapping for the library
# This ensures that 'page_range' is formatted exactly how the library expects it.
options = {}
if PAGE_NUMBER is not None:
  options["page_range"] = str(PAGE_NUMBER - 1)
  md_filename = os.path.join(output_dir, f"{PAGE_NUMBER}.md")
else:
  md_filename = os.path.join(output_dir, "full_pdf.md")

config_parser = ConfigParser(options)
marker_config = config_parser.generate_config_dict()

# Create directories
os.makedirs(images_dir, exist_ok=True)

# Important for debugging in Colab
if PAGE_NUMBER is not None:
  print(f"Mode: Single Page (Page {PAGE_NUMBER}) - Requested index: {PAGE_NUMBER - 1}")
else:
  print("Mode: Full PDF")

print("Loading models and starting conversion...")

# Initialize converter with the library-standard config dict
converterP = PdfConverter(
  artifact_dict=create_model_dict(),
  config=marker_config
)

# Process the PDF
rrr = converterP(pdf_path)
t, metadata, images = text_from_rendered(rrr)

# 1. Save the .md file
try:
  with open(md_filename, "w", encoding="utf-8") as f:
    f.write(t)
  print(f"Markdown content saved to {md_filename}")
except IOError as e:
  print(f"Error saving markdown file: {e}")

# 2. Save all images extracted in the session
if images:
  print(f"Found {len(images)} images. Saving to {images_dir}/...")
  for idx, (img_key, img_object) in enumerate(images.items(), start=1):
    img_filename = os.path.join(images_dir, f"{idx}.png")
    try:
      img_object.save(img_filename, format="PNG")
      print(f"Saved: {img_filename}")
    except Exception as e:
      print(f"Error saving image {img_key}: {e}")
else:
  print("No images found in the selected range.")

# End timer and print elapsed time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"\nTotal elapsed time: {elapsed_time:.2f} seconds")