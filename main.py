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
options = {
  "batch_multiplier": 4,             # General GPU batch boost
  "TableProcessor_recognition_batch_size": 192,  # Table cell OCR: default 48, push it up (T4 has 16GB)
}
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

# --- Per-step timing patch ---
from marker.builders.document import DocumentBuilder
from marker.builders.layout import LayoutBuilder
from marker.builders.line import LineBuilder
from marker.builders.ocr import OcrBuilder
from marker.builders.structure import StructureBuilder

_orig_build_document = PdfConverter.build_document

def _timed_build_document(self, filepath):
  from marker.providers.registry import provider_from_filepath
  step_times = {}

  provider_cls = provider_from_filepath(filepath)
  provider = provider_cls(filepath, self.config)

  def _run(label, fn, *args, **kwargs):
    t0 = time.time()
    result = fn(*args, **kwargs)
    step_times[label] = time.time() - t0
    return result

  layout_builder = self.resolve_dependencies(LayoutBuilder)
  line_builder = self.resolve_dependencies(LineBuilder)
  ocr_builder = self.resolve_dependencies(OcrBuilder)

  document = _run(
    "DocumentBuilder",
    DocumentBuilder(self.config),
    provider, layout_builder, line_builder, ocr_builder
  )

  _run("StructureBuilder", self.resolve_dependencies(StructureBuilder), document)

  for processor in self.processor_list:
    label = type(processor).__name__
    _run(label, processor, document)

  print("\n📊 Per-step timing breakdown:")
  for label, secs in step_times.items():
    if secs > 0.5:
      print(f"  {label:45s} {secs:7.2f}s")
  print()

  return document

PdfConverter.build_document = _timed_build_document
# -----------------------------

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