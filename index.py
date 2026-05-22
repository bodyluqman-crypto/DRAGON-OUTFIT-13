from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import os
import random
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)  
main_key = "DRAGON-TEAM"
executor = ThreadPoolExecutor(max_workers=10)

# الرابط السري لصور Free Fire (بيشتغل)
INFO_URL = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG"

def fetch_player_info(uid):
    url = f'https://otman-info.vercel.app/player-info?uid={uid}'
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def fetch_and_process_image(image_url, size=None):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, timeout=10, headers=headers)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)).convert("RGBA")
            if size:
                image = image.resize(size, Image.Resampling.LANCZOS)
            return image
        return None
    except:
        return None

def make_circle_with_border(image, size, border_color):
    """صورة دائرية مع إطار ملون"""
    if image is None:
        return None
    
    img = image.resize((size, size), Image.Resampling.LANCZOS)
    
    # قناع دائري
    mask = Image.new('L', (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size, size), fill=255)
    
    # الصورة الدائرية
    circular = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    circular.paste(img, (0, 0), mask)
    
    # إضافة إطار ملون
    border = Image.new('RGBA', (size + 16, size + 16), (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border)
    
    # توهج خارجي
    for i in range(6, 0, -1):
        alpha = 50 - i * 5
        draw_border.ellipse((8 - i, 8 - i, size + 8 + i, size + 8 + i),
                           outline=(border_color[0], border_color[1], border_color[2], alpha), width=2)
    
    # الإطار الرئيسي
    draw_border.ellipse((8, 8, size + 8, size + 8), outline=border_color, width=4)
    draw_border.ellipse((12, 12, size + 4, size + 4), outline=(255, 255, 255, 150), width=1)
    
    border.paste(circular, (8, 8), circular)
    return border

def create_fancy_background():
    """خلفية فخمة متدرجة الألوان"""
    width, height = 1024, 1024
    img = Image.new('RGBA', (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # تدرج لوني فخم
    for y in range(height):
        ratio = y / height
        r = int(30 + ratio * 70)
        g = int(10 + ratio * 90)
        b = int(50 + ratio * 160)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255), width=1)
    
    # دوائر زخرفية
    colors = [
        (255, 100, 100, 40), (100, 255, 100, 40), (100, 100, 255, 40),
        (255, 255, 100, 40), (255, 100, 255, 40), (100, 255, 255, 40)
    ]
    for i, color in enumerate(colors):
        r = 130 + i * 70
        draw.ellipse((width//2 - r, height//2 - r, width//2 + r, height//2 + r),
                    outline=color, width=3)
    
    # خطوط زخرفية
    for i in range(0, width, 50):
        draw.line([(i, 0), (i, height)], fill=(255, 255, 255, 15), width=1)
        draw.line([(0, i), (width, i)], fill=(255, 255, 255, 15), width=1)
    
    # نجوم
    for _ in range(150):
        x = random.randint(0, width)
        y = random.randint(0, height)
        intensity = random.randint(100, 255)
        draw.point((x, y), fill=(intensity, intensity, intensity, 255))
    
    return img

@app.route('/outfit-image', methods=['GET'])
def outfit_image():
    uid = request.args.get('uid')
    key = request.args.get('key')

    if not uid:
        return jsonify({'error': 'Missing uid'}), 400
    if key != main_key:
        return jsonify({'error': 'Invalid or missing API key'}), 403

    data = fetch_player_info(uid)
    if not data:
        return jsonify({'error': 'Failed to fetch player info'}), 500

    clothes_ids = data.get("profileInfo", {}).get("clothes", [])
    equipped_skills = data.get("profileInfo", {}).get("equipedSkills", [])
    pet_id = data.get("petInfo", {}).get("id")
    weapon_ids = data.get("basicInfo", {}).get("weaponSkinShows", [])
    weapon_id = weapon_ids[0] if weapon_ids else None
    player_name = data.get("basicInfo", {}).get("nickname", "WARRIOR")

    required_starts = ["211", "214", "211", "203", "204", "205", "203"]
    fallback_ids = ["211000000", "214000000", "208000000", "203000000", "204000000", "205000000", "203000000"]
    used_ids = set()
    outfit_images = []

    def fetch_outfit_image(idx, code):
        matched = None
        for oid in clothes_ids:
            str_oid = str(oid)
            if str_oid.startswith(code) and oid not in used_ids:
                matched = oid
                used_ids.add(oid)
                break
        if matched is None:
            matched = fallback_ids[idx]
        # استخدام الرابط الجديد
        url = f'{INFO_URL}/{matched}.png'
        return fetch_and_process_image(url, size=(150, 150))

    for idx, code in enumerate(required_starts):
        outfit_images.append(executor.submit(fetch_outfit_image, idx, code))

    # خلفية فخمة (بدل القديمة)
    background_image = create_fancy_background()
    W, H = 1024, 1024
    draw = ImageDraw.Draw(background_image)

    # تحميل الخطوط
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        watermark_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        watermark_font = ImageFont.load_default()

    # ===== شعار DRAGONX1M@ في الأعلى =====
    watermark = "⚡ DRAGONX1M@ ⚡"
    for offset in range(3, 0, -1):
        draw.text((W//2 - 120 + offset, 15 + offset), watermark,
                 fill=(50, 50, 100, 120), font=watermark_font)
    draw.text((W//2 - 120, 15), watermark, fill=(255, 215, 0, 255), font=watermark_font)
    draw.line([(W//2 - 180, 50), (W//2 + 180, 50)], fill=(255, 215, 0, 200), width=2)

    # عنوان
    title = "ELITE OUTFIT"
    draw.text((W//2 - 130, 65), title, fill=(0, 255, 255, 255), font=title_font)

    # أماكن العناصر (نفس الكود الأصلي)
    positions = [
        {'x': 720, 'y': 130, 'width': 140, 'height': 140, 'color': (0, 255, 255), 'name': 'HELMET'},
        {'x': 770, 'y': 310, 'width': 140, 'height': 100, 'color': (255, 0, 255), 'name': 'VISOR'},
        {'x': 740, 'y': 470, 'width': 140, 'height': 140, 'color': (255, 255, 0), 'name': 'BACK'},
        {'x': 60,  'y': 480, 'width': 140, 'height': 140, 'color': (0, 255, 0), 'name': 'ARMOR'},
        {'x': 110, 'y': 730, 'width': 140, 'height': 140, 'color': (255, 100, 0), 'name': 'LEG'},
        {'x': 690, 'y': 700, 'width': 140, 'height': 140, 'color': (255, 0, 255), 'name': 'BOOTS'},
        {'x': 50,  'y': 230, 'width': 140, 'height': 140, 'color': (100, 255, 255), 'name': 'EXTRA'},
    ]

    # لصق الملابس
    for idx, future in enumerate(outfit_images):
        outfit_image = future.result()
        if outfit_image and idx < len(positions):
            pos = positions[idx]
            # تحويل الصورة إلى دائرة مع إطار
            circular = make_circle_with_border(outfit_image, pos['width'], pos['color'])
            if circular:
                background_image.paste(circular, (pos['x'] - 8, pos['y'] - 8), circular)
            # اسم القطعة
            bbox = draw.textbbox((0, 0), pos['name'], font=small_font)
            text_w = bbox[2] - bbox[0]
            draw.text((pos['x'] + pos['width']//2 - text_w//2, pos['y'] + pos['height'] + 5),
                     pos['name'], fill=pos['color'], font=small_font)

    # لصق البت
    if pet_id:
        pet_url = f'{INFO_URL}/{pet_id}.png'
        pet_image = fetch_and_process_image(pet_url, size=(130, 130))
        if pet_image:
            circular_pet = make_circle_with_border(pet_image, 130, (255, 100, 200))
            background_image.paste(circular_pet, (682, 692), circular_pet)

    # لصق الأفاتار
    avatar_id = next((s for s in equipped_skills if str(s).endswith("06")), 406)
    avatar_url = f'https://characteriroxmar.vercel.app/chars?id={avatar_id}'
    avatar_image = fetch_and_process_image(avatar_url, size=(380, 450))
    if avatar_image:
        center_x = (W - avatar_image.width) // 2
        background_image.paste(avatar_image, (center_x, 200), avatar_image)
        # إطار حول الـ Avatar
        draw.rectangle([center_x - 8, 192, center_x + avatar_image.width + 8, 200 + avatar_image.height + 8],
                      outline=(0, 255, 255, 200), width=3)

    # لصق السلاح
    if weapon_id:
        weapon_url = f'{INFO_URL}/weapon_{weapon_id}.png'
        weapon_image = fetch_and_process_image(weapon_url, size=(180, 100))
        if not weapon_image:
            weapon_url = f'{INFO_URL}/{weapon_id}.png'
            weapon_image = fetch_and_process_image(weapon_url, size=(180, 100))
        if weapon_image:
            background_image.paste(weapon_image, (420, 820), weapon_image)
            draw.text((470, 930), "WEAPON", fill=(255, 50, 100), font=small_font)

    # اسم اللاعب
    name_text = f"🏆 {player_name.upper()} 🏆"
    for offset in range(2, 0, -1):
        draw.text((W//2 - len(name_text)*9 + offset, H - 60 + offset),
                 name_text, fill=(100, 100, 200, 120), font=name_font)
    draw.text((W//2 - len(name_text)*9, H - 60),
             name_text, fill=(255, 215, 0, 255), font=name_font)

    # تذييل
    draw.text((W - 150, H - 25), "@DRAGONX1M", fill=(255, 255, 255, 150), font=small_font)

    # إخراج الصورة
    img_io = BytesIO()
    background_image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': '✅ API Working!',
        'creator': 'DRAGONX1M@',
        'endpoints': {
            '/outfit-image': 'GET - uid=ID&key=DRAGON-TEAM'
        },
        'example': '/outfit-image?uid=2129828082&key=DRAGON-TEAM'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)