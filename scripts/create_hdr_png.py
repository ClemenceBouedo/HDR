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

from debevec import hdr_debevec, save_hdr



def load_exposure_sequence(image_folder: str | Path) -> tuple[list[np.ndarray], np.ndarray]:
    """
    Load a sequence of images with different exposures.

    Args:
        image_folder: Path to folder containing images

    Returns:
        images: List of images as numpy arrays
        exposure_times: Array of exposure times in seconds
    """
    image_folder = Path(image_folder)

    # Lire le fichier d'info HDR
    hdr_list_file = image_folder / "hdr_image_list.txt"
    
    if not hdr_list_file.exists():
        raise FileNotFoundError(f"Fichier non trouvé : {hdr_list_file}")
    
    print(f"Lecture du fichier : {hdr_list_file}")
    
    # Parser le fichier pour extraire les noms de fichiers et temps d'exposition
    image_files = []
    exposure_times = []
    
    with open(hdr_list_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Ignorer les lignes de commentaire et les lignes vides
            if line.startswith('#') or not line:
                continue
            
            # Parser la ligne : filename exposure_time f_stop gain nd_filters
            parts = line.split()
            if len(parts) >= 2:
                filename = parts[0]
                exposure_time = float(1/float(parts[1]))
                
                # Essayer le fichier tel quel, sinon changer l'extension en .png
                img_path = image_folder / filename
                if not img_path.exists():
                    img_path = image_folder / filename.replace('.ppm', '.png')
                
                image_files.append(img_path)
                exposure_times.append(exposure_time)
    
    if not image_files:
        raise ValueError(f"Aucune image trouvée dans {hdr_list_file}")
    
    # Charger les images
    images = []
    for img_file in image_files:
        if not img_file.exists():
            raise FileNotFoundError(f"Image introuvable : {img_file}")
        img = imageio.imread(img_file)
        images.append(img)
    
    exposure_times = np.array(exposure_times)
    
    print(f"Loaded {len(images)} images")
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

    image_folder = "../images/reduced/scene_1"
    images, exposure_times = load_exposure_sequence(image_folder)

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
