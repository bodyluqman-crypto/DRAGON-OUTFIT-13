from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)  
main_key = "DRAGON-TEAM"
executor = ThreadPoolExecutor(max_workers=10)

# الرابط السري الجديد اللي بيشتغل (ده بس اللي ضفته)
INFO_URL = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG"

def fetch_player_info(uid):
    url = f'https://otman-info.vercel.app/player-info?uid={uid}'
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def fetch_and_process_image(image_url, size=None):
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)).convert("RGBA")
            if size:
                image = image.resize(size, Image.Resampling.LANCZOS)
            return image
    except:
        pass
    return None

@app.route('/outfit-image', methods=['GET'])
def outfit_image():
    uid = request.args.get('uid')
    key = request.args.get('key')

    if not uid:
        return jsonify({'error': 'Missing uid'}), 400
    if key != main_key:
        return jsonify({'error': 'Invalid API key'}), 403

    data = fetch_player_info(uid)
    if not data:
        return jsonify({'error': 'Failed to fetch'}), 500

    clothes_ids = data.get("profileInfo", {}).get("clothes", [])
    equipped_skills = data.get("profileInfo", {}).get("equipedSkills", [])
    pet_id = data.get("petInfo", {}).get("id")
    weapon_ids = data.get("basicInfo", {}).get("weaponSkinShows", [])
    weapon_id = weapon_ids[0] if weapon_ids else None

    required_starts = ["211", "214", "211", "203", "204", "205", "203"]
    fallback_ids = ["211000000", "214000000", "208000000", "203000000", "204000000", "205000000", "203000000"]
    used_ids = set()
    outfit_images = []

    def fetch_outfit_image(idx, code):
        matched = None
        for oid in clothes_ids:
            if str(oid).startswith(code) and oid not in used_ids:
                matched = oid
                used_ids.add(oid)
                break
        if matched is None:
            matched = fallback_ids[idx]
        # ده التغيير الوحيد - استخدم الرابط الجديد
        url = f'{INFO_URL}/{matched}.png'
        return fetch_and_process_image(url, size=(170, 170))

    for idx, code in enumerate(required_starts):
        outfit_images.append(executor.submit(fetch_outfit_image, idx, code))

    # خلفية بسيطة (عشان نتأكد إنها شغالة)
    bg_url = 'https://iili.io/KXvqKle.png'
    background = fetch_and_process_image(bg_url, size=(1024, 1024))
    if not background:
        return jsonify({'error': 'Background failed'}), 500

    positions = [
        {'x': 760, 'y': 92,  'width': 170, 'height': 170},
        {'x': 810, 'y': 310, 'width': 170, 'height': 120},
        {'x': 790, 'y': 490, 'width': 170, 'height': 170},
        {'x': 72,  'y': 505, 'width': 170, 'height': 170},
        {'x': 130, 'y': 792, 'width': 170, 'height': 170},
        {'x': 728, 'y': 760, 'width': 170, 'height': 170},
        {'x': 72,  'y': 230, 'width': 170, 'height': 170},
    ]

    for idx, future in enumerate(outfit_images):
        img = future.result()
        if img and idx < len(positions):
            pos = positions[idx]
            resized = img.resize((pos['width'], pos['height']), Image.Resampling.LANCZOS)
            background.paste(resized, (pos['x'], pos['y']), resized)

    if pet_id:
        pet_url = f'{INFO_URL}/{pet_id}.png'
        pet_img = fetch_and_process_image(pet_url, size=(140, 170))
        if pet_img:
            background.paste(pet_img, (700, 700), pet_img)

    avatar_id = "406"
    for s in equipped_skills:
        if str(s).endswith("06"):
            avatar_id = str(s)
            break
    avatar_url = f'https://characteriroxmar.vercel.app/chars?id={avatar_id}'
    avatar_img = fetch_and_process_image(avatar_url, size=(650, 780))
    if avatar_img:
        cx = (1024 - avatar_img.width) // 2
        background.paste(avatar_img, (cx, 145), avatar_img)

    if weapon_id:
        weapon_url = f'{INFO_URL}/weapon_{weapon_id}.png'
        weapon_img = fetch_and_process_image(weapon_url, size=(330, 200))
        if not weapon_img:
            weapon_url = f'{INFO_URL}/{weapon_id}.png'
            weapon_img = fetch_and_process_image(weapon_url, size=(330, 200))
        if weapon_img:
            background.paste(weapon_img, (670, 564), weapon_img)

    img_io = BytesIO()
    background.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': '✅ API Working!', 'endpoint': '/outfit-image?uid=ID&key=DRAGON-TEAM'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
