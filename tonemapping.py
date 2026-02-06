#%%
"""
Bilateral Tone Mapping (Durand & Dorsey)

Entrée :
- Radiance map HDR (image flottante, valeurs non bornées)
- Format attendu : H x W x 3, float32 ou float64

Sortie :
- Image LDR affichable (valeurs dans [0, 1])
"""

import numpy as np
import cv2

print("Done")
#%% test : chargement d'une image HDR

#hdr = cv2.imread("../../memorial.hdr", cv2.IMREAD_UNCHANGED)
#print(hdr.dtype, hdr.min(), hdr.max())

#%% fonctions de tone mapping bilatéral

# ==================================================
# 1. Chargement de la radiance map HDR
# ==================================================

def load_hdr_image(path):
    """
    Charge une image HDR (.hdr, .exr, etc.)

    Args:
        path (str): chemin vers la radiance map

    Returns:
        hdr (np.ndarray): image HDR float, shape (H, W, 3)
    """
    hdr = cv2.imread(path, cv2.IMREAD_UNCHANGED)

    if hdr is None:
        raise IOError("Impossible de charger l'image HDR")

    hdr = hdr.astype(np.float32)
    return hdr


# ==================================================
# 2. Calcul de la luminance
# ==================================================

def compute_luminance(hdr):
    """
    Calcule la luminance à partir de l'image HDR RGB

    Args:
        hdr (np.ndarray): image HDR (H, W, 3)

    Returns:
        L (np.ndarray): luminance (H, W)
        R, G, B (np.ndarray): canaux couleur
    """
    # OpenCV charge en BGR
    B = hdr[:, :, 0]
    G = hdr[:, :, 1]
    R = hdr[:, :, 2]

    # TODO : calculer la luminance selon la norme Rec.709
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B

    return L, R, G, B


# ==================================================
# 3. Filtrage bilatéral sur la log-luminance
# ==================================================

def compute_base_layer(logL, sigma_spatial, sigma_range, nb_segments=16, downsample_factor=2):
    """
    Approximation du filtre bilatéral selon Durand & Dorsey
    - segmentation en intensité
    - filtrage spatial sur chaque segment
    - interpolation
    """

    # 1) downsample spatial
    logL_small = logL[::downsample_factor, ::downsample_factor]

    # 2) segmentation en intensité
    Imin, Imax = logL_small.min(), logL_small.max()
    levels = np.linspace(Imin, Imax, nb_segments)

    H_acc = np.zeros_like(logL_small, dtype=np.float32)
    K_acc = np.zeros_like(logL_small, dtype=np.float32)

    # 3) pour chaque segment
    for i in range(nb_segments):
        c = levels[i]

        # fonction g(I - c)
        G = np.exp(-((logL_small - c) ** 2) / (2 * sigma_range**2))

        # images H et K
        H = G * logL_small
        K = G

        # filtrage spatial (gaussien)
        H_blur = cv2.GaussianBlur(H, (0, 0), sigma_spatial)
        K_blur = cv2.GaussianBlur(K, (0, 0), sigma_spatial)

        # accumulation
        H_acc += H_blur
        K_acc += K_blur

    # 4) base = H/K
    base_small = H_acc / (K_acc + 1e-6)

    # 5) upsample à la taille originale
    base = cv2.resize(base_small, (logL.shape[1], logL.shape[0]), interpolation=cv2.INTER_LINEAR)

    return base

# ==================================================
# 4. Compression de la couche de base
# ==================================================

def compress_base_layer(base, desired_contrast):
    """
    Compresse la dynamique de la couche de base

    Args:
        base (np.ndarray): couche de base
        desired_contrast (float): contraste final désiré

    Returns:
        base_compressed (np.ndarray)
    """
    base_min = base.min()
    base_max = base.max()

    # TODO :
    # - calculer le facteur de compression
    # - appliquer la compression de Durand & Dorsey

    contrast = base_max - base_min
    factor = contrast / desired_contrast

    base_compressed = base_min + (base - base_min) / (factor + 1e-6)

    return base_compressed


# ==================================================
# 5. Tone mapping bilatéral complet
# ==================================================

def bilateral_tone_mapping(
    hdr,
    sigma_spatial,
    sigma_range,
    desired_contrast
):
    """
    Applique le tone mapping bilatéral à une radiance map HDR

    Args:
        hdr (np.ndarray): image HDR
        sigma_spatial (float)
        sigma_range (float)
        desired_contrast (float)

    Returns:
        ldr (np.ndarray): image LDR dans [0, 1]
    """
    epsilon = 1e-6

    # --- 1. Luminance
    L, R, G, B = compute_luminance(hdr)
    print("Luminance stats :")
    print(" min:", L.min())
    print(" max:", L.max())
    print(" mean:", L.mean())
    print(" median:", np.median(L))
    print(" std:", L.std())
    print(" % pixels > 1:", np.mean(L > 1) * 100)

    # --- 2. Passage en log
    logL = np.log(L + epsilon)

    # --- 3. Décomposition base / détail
    base = compute_base_layer(logL, sigma_spatial, sigma_range)
    detail = logL - base

    # --- 4. Compression de la base
    base_compressed = compress_base_layer(base, desired_contrast)

    # --- 5. Reconstruction de la luminance
    logL_out = base_compressed + detail
    L_out = np.exp(logL_out)

    # --- 6. Recomposition couleur
    R_out = (R / (L + epsilon)) * L_out
    G_out = (G / (L + epsilon)) * L_out
    B_out = (B / (L + epsilon)) * L_out

    ldr = np.stack([B_out, G_out, R_out], axis=2)

    # --- 7. Normalisation pour affichage (percentile)
    ldr = np.clip(ldr, 0, None)

    p = np.percentile(ldr, 99.5)
    ldr = np.clip(ldr / (p + 1e-6), 0, 1)

    # gamma
    ldr = np.power(ldr, 1/2.2)

    return ldr


# ==================================================
# 6. Programme principal (test)
# ==================================================

if __name__ == "__main__":

    # TODO : mettre le chemin vers votre radiance map HDR
    hdr_path = "../memorial.hdr"

    hdr = load_hdr_image(hdr_path)

    ldr = bilateral_tone_mapping(
        hdr,
        sigma_spatial=2.0,
        sigma_range=0.1,
        desired_contrast=2.0
    )

    # Sauvegarde pour affichage
    cv2.imwrite(".\\output.png", (ldr * 255).astype(np.uint8))

