"""
Example script demonstrating HDR image creation using the Debevec algorithm.

This script shows how to:
1. Load a series of images with different exposures
2. Compute the HDR radiance map
3. Save the HDR image
4. Create a tonemapped LDR version for display
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

import imageio.v3 as imageio
from PIL import Image
from PIL.ExifTags import TAGS

from debevec import hdr_debevec, save_hdr


def load_exposure_sequence_memorial(image_folder: str | Path) -> tuple[list[np.ndarray], np.ndarray]:
    """
    Charge toutes les images JPG d'un dossier et récupère le temps d'exposition depuis les EXIF.

    Args:
        image_folder: dossier contenant les images

    Returns:
        images: liste d'images (np.ndarray)
        exposure_times: np.ndarray des temps d'exposition (en secondes)
    """
    image_folder = Path(image_folder)
    image_files = sorted([f for f in image_folder.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg']])
    if not image_files:
        raise ValueError(f"Aucune image JPG trouvée dans {image_folder}")

    images = []
    exposure_times = []
    for img_path in image_files:
        # Charger l'image
        img = imageio.imread(img_path)
        images.append(img)

        # Extraire le temps d'exposition depuis les EXIF
        try:
            pil_img = Image.open(img_path)
            exif_data = pil_img._getexif()
            exposure = None
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == 'ExposureTime':
                        # ExposureTime peut être un tuple (num, den)
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
    """
    Plot the camera response function.

    Args:
        response_curves: Response curves for each channel (shape: (3, 256) or (256,))
        save_path: Optional path to save the plot
    """
    plt.figure(figsize=(10, 6))

    if response_curves.ndim == 1:
        # Grayscale
        plt.plot(range(256), response_curves, 'k-', label='Grayscale')
    else:
        # RGB
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

def main():
    """Main function to demonstrate HDR creation."""
    print("=== HDR Image Creation using Debevec Algorithm ===\n")

    image_folder = "../images/Images_supop/Scène 1"
    images, exposure_times = load_exposure_sequence_memorial(image_folder)

    # Create HDR image
    print("\nComputing HDR radiance map...")
    print("This may take a few moments...")
    hdr_image, response_curves = hdr_debevec(
        images=images,
        exposure_times=exposure_times,
        lambda_smooth=50.0,
        num_samples=10
    )

    print(f"HDR image shape: {hdr_image.shape}")
    print(f"HDR dynamic range: {hdr_image.min():.6f} to {hdr_image.max():.6f}")

    # Plot response curves
    print("\nPlotting camera response curves...")
    plot_response_curves(response_curves, save_path='response_curves.png')

    # Save HDR image
    print("\nSaving HDR image...")
    save_hdr('output_hdr.hdr', hdr_image)
    print("HDR image saved as: output_hdr.hdr")

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
