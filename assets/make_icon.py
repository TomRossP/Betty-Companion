"""Draws assets/betty.ico (the exe's and the window's icon): a green rounded square with a white B. Run once."""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = 256
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((8, 8, SIZE - 8, SIZE - 8), radius=48, fill=(46, 125, 50, 255))
font = ImageFont.truetype(os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arialbd.ttf"), 184)
d.text((SIZE / 2, SIZE / 2 + 6), "B", font=font, fill=(255, 255, 255, 255), anchor="mm")
d.ellipse((SIZE - 84, SIZE - 84, SIZE - 30, SIZE - 30), fill=(230, 81, 0, 255), outline=(255, 255, 255, 255), width=6)
img.save(os.path.join(HERE, "betty.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save(os.path.join(HERE, "betty.png"))
print("assets/betty.ico written")
