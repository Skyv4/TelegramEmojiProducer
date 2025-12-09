from PIL import Image

# Create a new transparent image (RGBA mode)
img = Image.new('RGBA', (100, 100), (255, 255, 255, 0)) # White, fully transparent background

# Draw a red square in the center
for x in range(25, 75):
    for y in range(25, 75):
        img.putpixel((x, y), (255, 0, 0, 255)) # Red, fully opaque

# Save the image
img.save("transparent_test.png")
print("Generated transparent_test.png")
