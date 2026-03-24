import os
import time
import torch
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser
from PIL import Image

def select_best_device():
  """Automatically detects and returns the fastest available torch device."""
  try:
    import torch_xla.core.xla_model as xm
    print("🚀 Hardware Detected: Google TPU")
    return "xla"
  except ImportError:
    pass

  if torch.cuda.is_available():
    print(f"🚀 Hardware Detected: NVIDIA GPU ({torch.cuda.get_device_name(0)})")
    return "cuda"
  
  if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    print("🚀 Hardware Detected: Apple Silicon GPU (MPS)")
    return "mps"

  print("💻 Hardware Detected: CPU")
  return "cpu"

# --- AUTOMATIC HARDWARE OPTIMIZATION ---
best_device = select_best_device()
os.environ["TORCH_DEVICE"] = best_device
if best_device in ["cuda", "xla"]:
  os.environ["INFERENCE_RAM"] = "16"
else:
  os.environ.pop("INFERENCE_RAM", None)
# ----------------------------------------

# --- CONFIGURATION ---
PAGE_NUMBER = None
pdf_path = "pdfs/20240909_Hilton.pdf"
output_dir = "output"
images_dir = os.path.join(output_dir, "images")
# ---------------------

# Official Config Mapping
options = {}
if PAGE_NUMBER is not None:
  options["page_range"] = str(PAGE_NUMBER - 1)
  md_filename = os.path.join(output_dir, f"{PAGE_NUMBER}.md")
  print(f"Mode: Single Page (Page {PAGE_NUMBER})")
else:
  md_filename = os.path.join(output_dir, "full_pdf.md")
  print("Mode: Full PDF")

config_parser = ConfigParser(options)
marker_config = config_parser.generate_config_dict()

# Create directories
os.makedirs(images_dir, exist_ok=True)

# 1. LOAD MODELS (Excluded from timer)
print("⌛ Loading AI models into memory (this takes ~30s)...")
models = create_model_dict()

# 2. START CONVERSION (Timer starts here)
print("🤖 Models loaded. Starting actual conversion run...")
conversion_start_time = time.time()

# Initialize converter with pre-loaded models
converterP = PdfConverter(
  artifact_dict=models,
  config=marker_config
)

# Process the PDF
rrr = converterP(pdf_path)
t, metadata, images = text_from_rendered(rrr)

# 3. END CONVERSION (Timer ends here)
conversion_end_time = time.time()

# --- Saving Output ---
try:
  with open(md_filename, "w", encoding="utf-8") as f:
    f.write(t)
  print(f"Markdown content saved to {md_filename}")
except IOError as e:
  print(f"Error saving markdown file: {e}")

if images:
  print(f"Found {len(images)} images. Saving to {images_dir}/...")
  for idx, (img_key, img_object) in enumerate(images.items(), start=1):
    img_filename = os.path.join(images_dir, f"{idx}.png")
    img_object.save(img_filename, format="PNG")

# --- Final Stats ---
elapsed_time = conversion_end_time - conversion_start_time
print(f"\n✅ Conversion Complete!")
print(f"⏱️ Actual Run Time (excluding loading): {elapsed_time:.2f} seconds")