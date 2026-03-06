
"""
Script fusionné pour la création d'image HDR à partir de séquences PNG ou JPG.
Paramètres utilisateurs configurables ci-dessous.
"""

# === PARAMÈTRES UTILISATEUR ===
# Type d'images à charger : 'png' ou 'jpg'
MODE = 'png'  # ou 'jpg'
# Calculer uniquement les courbes de réponse (True = plus rapide, pas de HDR)
ONLY_RESPONSE_CURVES = True
# Chemin du dossier d'entrée (images)
IMAGE_FOLDER_PNG = "../images/reduced/scene_1"
IMAGE_FOLDER_JPG = "../images/Images_supop/Scène 1"
# Chemin de sauvegarde des courbes de réponse
RESPONSE_CURVE_PATH = 'response_curves.png'
# Chemin de sauvegarde du fichier HDR
HDR_OUTPUT_PATH = 'output_hdr.hdr'
# Nombre de points à sélectionner pour la courbe de réponse
NUM_SAMPLES = 20
# Paramètre de lissage lambda
LAMBDA_SMOOTH = 50.0
# =============================

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import imageio.v3 as imageio
from PIL import Image
from PIL.ExifTags import TAGS
from debevec import hdr_debevec, save_hdr

def load_exposure_sequence_png(image_folder: str | Path) -> tuple[list[np.ndarray], np.ndarray]:
    """
    Charge une séquence d'images PNG (ou PPM) et les temps d'exposition depuis un fichier texte.
    """
    image_folder = Path(image_folder)
    hdr_list_file = image_folder / "hdr_image_list.txt"
    if not hdr_list_file.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {hdr_list_file}")
    print(f"Lecture du fichier : {hdr_list_file}")
    image_files = []
    exposure_times = []
    with open(hdr_list_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                filename = parts[0]
                exposure_time = float(1/float(parts[1]))
                img_path = image_folder / filename
                if not img_path.exists():
                    img_path = image_folder / filename.replace('.ppm', '.png')
                image_files.append(img_path)
                exposure_times.append(exposure_time)
    if not image_files:
        raise ValueError(f"Aucune image trouvée dans {hdr_list_file}")
    images = []
    for img_file in image_files:
        if not img_file.exists():
            raise FileNotFoundError(f"Image introuvable : {img_file}")
        img = imageio.imread(img_file)
        images.append(img)
    exposure_times = np.array(exposure_times)
    print(f"Loaded {len(images)} PNG images")
    print(f"Exposure times: {exposure_times}")
    return images, exposure_times

def load_exposure_sequence_jpg(image_folder: str | Path) -> tuple[list[np.ndarray], np.ndarray]:
    """
    Charge toutes les images JPG d'un dossier et récupère le temps d'exposition depuis les EXIF.
    """
    image_folder = Path(image_folder)
    image_files = sorted([f for f in image_folder.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg']])
    if not image_files:
        raise ValueError(f"Aucune image JPG trouvée dans {image_folder}")
    images = []
    exposure_times = []
    for img_path in image_files:
        img = imageio.imread(img_path)
        images.append(img)
        try:
            pil_img = Image.open(img_path)
            exif_data = pil_img._getexif()
            exposure = None
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == 'ExposureTime':
                        if isinstance(value, tuple) and len(value) == 2:
                            exposure = value[0] / value[1]
                        else:
                            exposure = float(value)
                        break
            if exposure is None:
                print(f"[Avertissement] ExposureTime non trouvé pour {img_path}, valeur par défaut 1.0s utilisée.")
                exposure = 1.0
            exposure_times.append(exposure)
        except Exception as e:
            print(f"[Erreur] Impossible de lire EXIF pour {img_path}: {e}. Valeur par défaut 1.0s utilisée.")
            exposure_times.append(1.0)
    exposure_times = np.array(exposure_times)
    print(f"Loaded {len(images)} JPG images")
    print(f"Exposure times: {exposure_times}")
    return images, exposure_times

def plot_response_curves(response_curves: np.ndarray, save_path: str | None = None) -> None:
    # Courbe classique : g(Z) en fonction de Z
    plt.figure(figsize=(10, 6))
    if response_curves.ndim == 1:
        plt.plot(range(256), response_curves, 'k-', label='Grayscale')
    else:
        colors = ['red', 'green', 'blue']
        labels = ['Red', 'Green', 'Blue']
        for i, (color, label) in enumerate(zip(colors, labels)):
            plt.plot(range(256), response_curves[i], color=color, label=label)
    plt.xlabel('Pixel Value (Z)', fontsize=12)
    plt.ylabel('Log Exposure (g(Z))', fontsize=12)
    plt.title('Camera Response Function', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Response curve saved to {save_path}")
    plt.show()

    # Courbe inversée : Z en fonction de g(Z)
    plt.figure(figsize=(10, 6))
    if response_curves.ndim == 1:
        plt.plot(response_curves, range(256), 'k-', label='Grayscale')
    else:
        colors = ['red', 'green', 'blue']
        labels = ['Red', 'Green', 'Blue']
        for i, (color, label) in enumerate(zip(colors, labels)):
            plt.plot(response_curves[i], range(256), color=color, label=label)
    plt.xlabel('Log Exposure (g(Z))', fontsize=12)
    plt.ylabel('Pixel Value (Z)', fontsize=12)
    plt.title('Inverse Camera Response Function', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    if save_path:
        inv_path = save_path.replace('.png', '_inverse.png')
        plt.savefig(inv_path, dpi=150, bbox_inches='tight')
        print(f"Inverse response curve saved to {inv_path}")
    plt.show()

def main():
    print("=== HDR Image Creation using Debevec Algorithm ===\n")

    if MODE == 'png':
        image_folder = IMAGE_FOLDER_PNG
        images, exposure_times = load_exposure_sequence_png(image_folder)
    else:
        image_folder = IMAGE_FOLDER_JPG
        images, exposure_times = load_exposure_sequence_jpg(image_folder)

    print("\nComputing HDR radiance map and response curves...")
    print("This may take a few moments...")
    hdr_image, response_curves = hdr_debevec(
        images=images,
        exposure_times=exposure_times,
        lambda_smooth=LAMBDA_SMOOTH,
        num_samples=NUM_SAMPLES,
        only_response_curves=ONLY_RESPONSE_CURVES
    )

    print("\nPlotting camera response curves...")
    plot_response_curves(response_curves, save_path=RESPONSE_CURVE_PATH)

    if not ONLY_RESPONSE_CURVES:
        print(f"\nHDR image shape: {hdr_image.shape}")
        print(f"HDR dynamic range: {hdr_image.min():.6f} to {hdr_image.max():.6f}")
        print("\nSaving HDR image...")
        save_hdr(HDR_OUTPUT_PATH, hdr_image)
        print(f"HDR image saved as: {HDR_OUTPUT_PATH}")
    else:
        print("\nAucun fichier HDR n'a été créé (mode courbes de réponse uniquement, calcul HDR ignoré).")
    print("\n=== Done! ===")

if __name__ == "__main__":
    main()
