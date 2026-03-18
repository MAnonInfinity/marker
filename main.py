# import marker_pdf # This was causing an error, the module name is 'marker'
import triton
import os
import time
from marker.convert import convert_single_pdf
from marker.models import create_model_dict
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

# Use convert_single_pdf which properly supports start_page and max_pages
model_dict = create_model_dict()
t, images, metadata = convert_single_pdf(
  pdf_path,
  model_dict,
  start_page=start_page,
  max_pages=1
)

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