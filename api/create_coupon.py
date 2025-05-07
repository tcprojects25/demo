# create_coupon.py
from PIL import Image, ImageDraw, ImageFont
import os

def generate_coupon_image(coupon_code, save_path):
    width, height = 600, 300
    background_color = 'white'

    image = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", size=36)
    except:
        font = ImageFont.load_default()

    text = f"Coupon: {coupon_code}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    position = ((width - text_width) // 2, height // 2)

    draw.text(position, text, fill='black', font=font)
    image.save(save_path)
