import numpy as np
import matplotlib.pyplot as plt
import cv2

def plot_false_color_luminance(hdr_path: str, channel: str = 'all', cmap: str = 'jet', save_path: str = None) -> None:
    """
    Affiche et enregistre une carte de luminance en fausses couleurs à partir d'un fichier .hdr.
    Peut afficher chaque canal ("r", "g", "b") ou la luminance globale ("all" ou "luminance").
    L'échelle colorée est en log10.

    Args:
        hdr_path: Chemin du fichier .hdr
        channel: 'r', 'g', 'b', ou 'all'/'luminance' (par défaut)
        cmap: Colormap matplotlib à utiliser (par défaut 'jet')
        save_path: Chemin du fichier de sortie (PNG, optionnel)
    """
    hdr = cv2.imread(hdr_path, cv2.IMREAD_UNCHANGED)
    if hdr is None:
        raise FileNotFoundError(f"Impossible de lire le fichier HDR : {hdr_path}")
    if len(hdr.shape) == 2:
        # Image mono
        img = hdr
        title = f"Luminance (mono)"
    elif channel.lower() in ['r', 'g', 'b']:
        idx = {'b': 0, 'g': 1, 'r': 2}[channel.lower()]
        img = hdr[..., idx]
        title = f"Canal {channel.upper()}"
    else:
        # Luminance (pondération standard)
        # OpenCV charge en BGR, donc pondération dans cet ordre
        b, g, r = hdr[..., 0], hdr[..., 1], hdr[..., 2]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        img = luminance
        title = "Luminance (pondérée)"
    # Passage en log10, en évitant les valeurs <= 0
    img_log = np.log10(np.clip(img, a_min=1e-6, a_max=None))
    plt.figure(figsize=(8, 6))
    vmin = np.percentile(img_log, 1)
    vmax = np.percentile(img_log, 99)
    im = plt.imshow(img_log, cmap=cmap, vmin=vmin, vmax=vmax)
    cbar = plt.colorbar(im, label='log10(Luminance)')
    plt.title(f"Carte fausses couleurs (log10) : {title}")
    plt.axis('off')
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Image enregistrée : {save_path}")
    plt.show()


if __name__ == "__main__":
    # À personnaliser : chemins d'entrée et de sortie
    hdr_path = "../output/saved/scene_1/output_hdr.hdr"  # Chemin du fichier HDR à afficher
    cmap = "jet"      # Colormap matplotlib
    output_dir = "../output/saved/scene_1/"  # Dossier de sauvegarde

    for channel in ["r", "g", "b", "all"]:
        if channel == "all":
            suffix = "luminance"
        else:
            suffix = channel
        save_path = f"{output_dir}false_color_{suffix}.png"
        print(f"Génération de la carte pour le canal : {channel}")
        plot_false_color_luminance(hdr_path, channel=channel, cmap=cmap, save_path=save_path)
