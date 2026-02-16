import os
from PIL import Image
import json
from PIL.ExifTags import TAGS

# Répertoire source et destination
SOURCE_DIR = "../images/Images_supop/Scène 1"  # À adapter selon votre dossier
DEST_DIR = "../images/reduced/scene_1"  # Dossier de sortie

FACTOR = 4  # Facteur de réduction entier (ex: 2 = divise largeur et hauteur par 2)
JPEG_QUALITY = 85  # Qualité JPEG

os.makedirs(DEST_DIR, exist_ok=True)


def get_exposure_time(img):
    if hasattr(img, '_getexif') and img._getexif() is not None:
        for tag, value in img._getexif().items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'ExposureTime':
                # Convertir les bytes en chaîne lisible ou en liste d'entiers
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8', errors='replace')
                    except Exception:
                        value = list(value)
                # Convertir les objets IFDRational ou fractions en float
                try:
                    if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                        num = value.numerator
                        den = value.denominator
                        exposure = num / den if den != 0 else float(num)
                    elif isinstance(value, tuple) and len(value) == 2:
                        num, den = value
                        exposure = num / den if den != 0 else float(num)
                    elif hasattr(value, 'num') and hasattr(value, 'den'):
                        num = value.num
                        den = value.den
                        exposure = num / den if den != 0 else float(num)
                    elif isinstance(value, str) and '/' in value:
                        num, den = value.split('/')
                        exposure = float(num) / float(den)
                    else:
                        exposure = float(value)
                    # Retourner l'inverse, sous forme décimale
                    if exposure != 0:
                        return 1.0 / exposure
                    else:
                        return 'N/A'
                except Exception:
                    return 'N/A'
    return 'N/A'

def reduce_image_size(input_path, output_path):
    with Image.open(input_path) as img:
        exposure = get_exposure_time(img)
        # Calculer la nouvelle taille selon le facteur
        new_width = img.width // FACTOR
        new_height = img.height // FACTOR
        img = img.resize((new_width, new_height), Image.LANCZOS)
        ext = os.path.splitext(output_path)[1].lower()
        if ext == '.png':
            img.save(output_path, format='PNG')
        else:
            quality = JPEG_QUALITY
            save_kwargs = {'format': 'JPEG', 'quality': quality}
            exif = img.info.get('exif')
            if exif:
                save_kwargs['exif'] = exif
            img.save(output_path, **save_kwargs)
        return exposure

if __name__ == "__main__":
    exposures = []
    for filename in os.listdir(SOURCE_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            input_path = os.path.join(SOURCE_DIR, filename)
            # Choisir l'extension de sortie : .jpg ou .png
            # Pour PNG, changez l'extension ci-dessous
            output_ext = ".png"  # ou ".jpg"
            output_path = os.path.join(DEST_DIR, os.path.splitext(filename)[0] + output_ext)
            exposure = reduce_image_size(input_path, output_path)
            exposures.append((os.path.basename(output_path), exposure))
            print(f"Image traitée : {output_path} ({os.path.getsize(output_path)//1024} Ko)")
    # Sauvegarder dans un fichier TXT au format hdr_image_list.txt
    if exposures:
        global_txt_path = os.path.join(DEST_DIR, "hdr_image_list.txt")
        with open(global_txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# Number of Images\n{len(exposures)}\n")
            f.write("# Filename  1/shutter_speed\n")
            for img_name, exposure in exposures:
                if exposure != 'N/A':
                    f.write(f"{img_name} {exposure}\n")
