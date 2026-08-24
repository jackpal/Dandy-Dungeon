from PIL import Image

img = Image.open('/usr/local/google/home/jackpal/Developer/Dandy-Dungeon/.agents/explorer_m1_1/strike_original_test.png')
print(f"Image Size: {img.size}")
print(f"Image Mode: {img.mode}")

unique_colors = img.getcolors(maxcolors=256)
print("Unique Colors (count, color):")
for item in sorted(unique_colors, key=lambda x: x[0], reverse=True):
    print(item)
