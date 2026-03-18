# import marker_pdf # This was causing an error, the module name is 'marker'
import triton
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

converterP = PdfConverter(
    artifact_dict=create_model_dict(),
)

rrr=converterP("Quadrilaterals.pdf")
t, metadata, i = text_from_rendered(rrr)

print(t)

print(i)

from PIL import Image

# The provided dictionary

# 1. Access the image object from the dictionary
# Assuming you want to save the first (and only) image in the dictionary
image_object = list(i.values())[0]

# 2. Define the output filename with the .png extension
output_filename = "saved_image.png"

# 3. Use the save() method to save the image as a PNG file
try:
    image_object.save(output_filename, format="PNG")
    print(f"Image successfully saved as {output_filename}")
except IOError as e:
    print(f"Error saving image: {e}")