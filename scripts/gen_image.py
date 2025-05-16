from openai import OpenAI
import os
import json
from PIL import Image
from io import BytesIO
import requests

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "tmp/news.json"
OUTPUT_FILE = "tmp/thumbnail.png"

def build_prompt(title):
    return f"A colorful anime-style illustration representing the topic: '{title}'. Futuristic but hopeful tone, with children or students, digital technology, and bright lighting."

def generate_image(prompt):
    response = client.images.generate(
        model="dall-e-2",  # ← GPTが自動アップグレードされても対応できる構成にしておく
        prompt=prompt,
        size="1024x1024",
        n=1,
        quality="standard"
    )
    return response.data[0].url

def save_image_as_png(image_url, output_path):
    res = requests.get(image_url)
    img = Image.open(BytesIO(res.content)).convert("RGB")  # RGBにしておくとWordPressも安定
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, format="PNG")
    print(f"✅ Image saved as PNG: {output_path}")

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        news = json.load(f)
    title = news["articles"][0]["title"]
    prompt = build_prompt(title)
    image_url = generate_image(prompt)
    save_image_as_png(image_url, OUTPUT_FILE)

if __name__ == "__main__":
    main()
