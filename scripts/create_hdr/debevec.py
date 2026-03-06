"""
Implementation of the Debevec and Malik HDR algorithm.

Based on the paper:
"Recovering High Dynamic Range Radiance Maps from Photographs"
by Paul E. Debevec and Jitendra Malik, SIGGRAPH 1997
"""

import numpy as np
import matplotlib.pyplot as plt


def select_points_interactive(image: np.ndarray, num_samples: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Permet à l'utilisateur de sélectionner des points sur une image.
    Args:
        image (np.ndarray): Image sur laquelle sélectionner les points.
        num_samples (int): Nombre de points à sélectionner.
    Returns:
        tuple[np.ndarray, np.ndarray]: Coordonnées x et y des points sélectionnés.
    """
    selected_points = []
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(image)
    ax.set_title(f'Cliquez pour sélectionner {num_samples} points\n({len(selected_points)}/{num_samples} sélectionnés)')
    
    def onclick(event):
        if event.inaxes == ax and len(selected_points) < num_samples:
            x, y = int(event.xdata), int(event.ydata)
            selected_points.append((x, y))
            ax.plot(x, y, 'r+', markersize=10, markeredgewidth=2)
            ax.set_title(f'Cliquez pour sélectionner {num_samples} points\n({len(selected_points)}/{num_samples} sélectionnés)')
            fig.canvas.draw()
            
            if len(selected_points) >= num_samples:
                print(f"{num_samples} points sélectionnés. Fermez la fenêtre pour continuer.")
    
    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()
    
    if len(selected_points) < num_samples:
        raise ValueError(f"Pas assez de points sélectionnés : {len(selected_points)}/{num_samples}")
    
    sample_x = np.array([p[0] for p in selected_points])
    sample_y = np.array([p[1] for p in selected_points])
    
    return sample_x, sample_y


def gsolve(Z: np.ndarray, B: np.ndarray, l: float, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Résout la fonction de réponse du système d'imagerie.
    Args:
        Z (np.ndarray): Valeurs de pixels pour plusieurs emplacements et images.
        B (np.ndarray): Log des temps d'exposition pour chaque image.
        l (float): Paramètre de lissage.
        w (np.ndarray): Fonction de pondération pour chaque valeur de pixel.
    Returns:
        tuple[np.ndarray, np.ndarray]: Courbe de réponse g et irradiance log lE.
    """
    n = 256 #Nombre de niveaux de gris
    num_pixels = Z.shape[0] # Nombre de pixels échantillonnés
    num_images = Z.shape[1] # Nombre d'images

    # Initialisation du système d'équation
    A = np.zeros((num_pixels * num_images + n + 1, n + num_pixels))
    b = np.zeros((A.shape[0], 1))

    # Include the data-fitting equations
    k = 0
    for i in range(num_pixels):
        for j in range(num_images):
            z_ij = Z[i, j]
            wij = w[z_ij]
            A[k, z_ij] = wij
            A[k, n + i] = -wij
            b[k, 0] = wij * B[j]
            k += 1

    # Fix the curve by setting its middle value to 0
    A[k, 128] = 1
    k += 1

    # Include the smoothness equations
    for i in range(n - 2):
        A[k, i] = l * w[i + 1]
        A[k, i + 1] = -2 * l * w[i + 1]
        A[k, i + 2] = l * w[i + 1]
        k += 1

    # Solve the system using least squares
    x = np.linalg.lstsq(A, b, rcond=None)[0]

    # Extract the response curve and irradiance values
    g = x[:n].flatten()
    lE = x[n:].flatten()

    return g, lE


def weight_function(z: int | np.ndarray, z_min: int = 0, z_max: int = 255) -> float | np.ndarray:
    """
    Fonction de pondération pour les valeurs de pixels.
    Donne plus de poids aux valeurs intermédiaires.
    Args:
        z (int | np.ndarray): Valeur(s) de pixel (0-255).
        z_min (int): Valeur minimale (par défaut 0).
        z_max (int): Valeur maximale (par défaut 255).
    Returns:
        float | np.ndarray: Valeur(s) de pondération.
    """
    z_mid = (z_min + z_max) / 2
    if z <= z_mid:
        w = z - z_min
    else:
        w = z_max - z
    return w


def hdr_debevec(
    images: list[np.ndarray],
    exposure_times: np.ndarray,
    lambda_smooth: float = 50.0,
    num_samples: int = 10,
    only_response_curves: bool = False
) -> tuple[np.ndarray | None, np.ndarray]:
    """
    Crée une image HDR avec l'algorithme de Debevec et Malik.
    Args:
        images (list[np.ndarray]): Liste d'images avec différents temps d'exposition.
        exposure_times (np.ndarray): Tableau des temps d'exposition.
        lambda_smooth (float): Paramètre de lissage pour la courbe de réponse.
        num_samples (int): Nombre de pixels à échantillonner.
        only_response_curves (bool): Si True, ne calcule que les courbes de réponse.
    Returns:
        tuple[np.ndarray | None, np.ndarray]: Image HDR et courbes de réponse.
    """
    num_images = len(images)
    height, width = images[0].shape[:2]
    num_channels = images[0].shape[2] if len(images[0].shape) == 3 else 1
    n = 256 #Nombre de niveaux de gris

    # Convert exposure times to log space
    B = np.log(exposure_times)

    # Create weighting function
    w = np.array([weight_function(z) for z in range(n)])

    # Sélectionner l'image médiane pour l'échantillonnage
    median_idx = num_images // 2
    median_image = images[median_idx]
    
    # Sélection interactive des points
    print(f"\nSélection de {num_samples} points sur l'image médiane (image {median_idx+1}/{num_images})")
    print("Cliquez sur l'image pour sélectionner les points. Fermez la fenêtre quand terminé.")
    
    sample_x, sample_y = select_points_interactive(median_image, num_samples)

    # Initialisation des courbes de réponse
    response_curves = []
    hdr_image = None if only_response_curves else np.zeros((height, width, num_channels))

    # Process each color channel
    for channel in range(num_channels):
        print(f"\n[DEBUG] Traitement du canal {channel+1}/{num_channels}...")
        # Extract pixel values for sampled locations
        Z = np.zeros((num_samples, num_images), dtype=int)
        for j, img in enumerate(images):
            if num_channels == 1:
                Z[:, j] = img[sample_y, sample_x]
            else:
                Z[:, j] = img[sample_y, sample_x, channel]

        print(f"[DEBUG] Extraction des valeurs d'échantillons pour le canal {channel+1} terminée.")

        # Solve for the response curve
        print(f"[DEBUG] Calcul de la courbe de réponse pour le canal {channel+1}...")
        g, lE = gsolve(Z, B, lambda_smooth, w)
        response_curves.append(g)
        print(f"[DEBUG] Courbe de réponse calculée pour le canal {channel+1}.")

        if not only_response_curves:
            # Reconstruct the HDR image for this channel
            print(f"[DEBUG] Reconstruction de l'image HDR pour le canal {channel+1}...")
            for y in range(height):
                if y % max(1, height // 10) == 0:
                    print(f"[DEBUG]   Canal {channel+1}: {int(100*y/height)}% des lignes traitées...")
                for x in range(width):
                    # Get pixel values across all exposures
                    if num_channels == 1:
                        pixel_values = np.array([img[y, x] for img in images])
                    else:
                        pixel_values = np.array([img[y, x, channel] for img in images])

                    # Weighted average of log irradiance
                    numerator = 0.0
                    denominator = 0.0
                    for j, z in enumerate(pixel_values):
                        wz = w[z]
                        numerator += wz * (g[z] - B[j])
                        denominator += wz

                    if denominator > 0:
                        hdr_image[y, x, channel] = np.exp(numerator / denominator)
            print(f"[DEBUG] Canal {channel+1} terminé.")

    response_curves = np.array(response_curves).squeeze()
    if not only_response_curves:
        hdr_image = hdr_image.squeeze()

    return hdr_image, response_curves


def save_hdr(filename: str, hdr_image: np.ndarray) -> None:
    """
    Sauvegarde une image HDR au format Radiance RGBE (.hdr).
    Args:
        filename (str): Nom du fichier de sortie (.hdr).
        hdr_image (np.ndarray): Carte de radiance HDR.
    Returns:
        None
    """
    import cv2
    
    # OpenCV expects BGR format, so convert RGB to BGR if needed
    if len(hdr_image.shape) == 3 and hdr_image.shape[2] == 3:
        hdr_bgr = cv2.cvtColor(hdr_image.astype(np.float32), cv2.COLOR_RGB2BGR)
    else:
        hdr_bgr = hdr_image.astype(np.float32)
    
    # Save as HDR
    cv2.imwrite(filename, hdr_bgr)
    print(f"HDR image saved: {filename}")

