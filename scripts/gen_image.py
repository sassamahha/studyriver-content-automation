# scripts/gen_image.py

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
    return f"A colorful anime-style illustration representing the topic: '{title}'. Futuristic but hopeful tone, with children or students, digital technology, and bright lighting. Size: 1792x1024."

def generate_image(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",  # DALL·E 3 は現状で固定サイズのみ
        n=1,
        quality="standard"
    )
    return response.data[0].url

def save_image(url, path):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print(f"✅ Image saved to {path}")

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        news = json.load(f)
    title = news["articles"][0]["title"]
    prompt = build_prompt(title)
    image_url = generate_image(prompt)
    save_image(image_url, OUTPUT_FILE)

if __name__ == "__main__":
    main()
