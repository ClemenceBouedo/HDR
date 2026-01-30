"""
Implementation of the Debevec and Malik HDR algorithm.

Based on the paper:
"Recovering High Dynamic Range Radiance Maps from Photographs"
by Paul E. Debevec and Jitendra Malik, SIGGRAPH 1997
"""

import numpy as np


def gsolve(Z: np.ndarray, B: np.ndarray, l: float, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Solve for imaging system response function.

    Given a set of pixel values observed for several pixels in several
    images with different exposure times, this function returns the
    imaging system's response function g as well as the log film irradiance
    values for the observed pixels.

    Assumes:
        Zmin = 0
        Zmax = 255

    Args:
        Z: Array of shape (num_pixels, num_images) where Z[i,j] is the pixel
           value of pixel location number i in image j
        B: Array of shape (num_images,) where B[j] is the log delta t,
           or log shutter speed, for image j
        l: Lambda, the constant that determines the amount of smoothness
        w: Weighting function array of shape (256,) where w[z] is the
           weighting function value for pixel value z

    Returns:
        g: Array of shape (256,) where g[z] is the log exposure corresponding
           to pixel value z
        lE: Array of shape (num_pixels,) where lE[i] is the log film irradiance
            at pixel location i
    """
    n = 256
    num_pixels = Z.shape[0]
    num_images = Z.shape[1]

    # Initialize the system of equations
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
    Weighting function for pixel values.

    This function gives more weight to middle-range pixel values
    and less weight to extremely dark or bright pixels.

    Args:
        z: Pixel value(s) (0-255)
        z_min: Minimum pixel value (default: 0)
        z_max: Maximum pixel value (default: 255)

    Returns:
        Weight value(s) between 0 and 1
    """
    z_mid = (z_min + z_max) / 2
    if isinstance(z, np.ndarray):
        w = np.where(z <= z_mid, z - z_min, z_max - z)
    else:
        w = z - z_min if z <= z_mid else z_max - z
    return w


def hdr_debevec(
    images: list[np.ndarray],
    exposure_times: np.ndarray,
    lambda_smooth: float = 50.0,
    num_samples: int = 100
) -> tuple[np.ndarray, np.ndarray]:
    """
    Create an HDR image using the Debevec and Malik algorithm.

    Args:
        images: List of images with different exposures (assumed to be uint8)
        exposure_times: Array of exposure times for each image
        lambda_smooth: Smoothness parameter for the response curve (default: 50)
        num_samples: Number of pixels to sample for computing response curve (default: 100)

    Returns:
        hdr_image: The resulting HDR radiance map
        response_curve: The computed camera response function for each channel
    """
    num_images = len(images)
    height, width = images[0].shape[:2]
    num_channels = images[0].shape[2] if len(images[0].shape) == 3 else 1

    # Convert exposure times to log space
    B = np.log(exposure_times)

    # Create weighting function
    w = np.array([weight_function(z) for z in range(256)])

    # Sample pixels uniformly across the image
    np.random.seed(42)
    sample_indices = np.random.choice(height * width, size=num_samples, replace=False)
    sample_y = sample_indices // width
    sample_x = sample_indices % width

    # Initialize response curves and HDR image
    response_curves = []
    hdr_image = np.zeros((height, width, num_channels))

    # Process each color channel
    for channel in range(num_channels):
        # Extract pixel values for sampled locations
        Z = np.zeros((num_samples, num_images), dtype=int)
        for j, img in enumerate(images):
            if num_channels == 1:
                Z[:, j] = img[sample_y, sample_x]
            else:
                Z[:, j] = img[sample_y, sample_x, channel]

        # Solve for the response curve
        g, _ = gsolve(Z, B, lambda_smooth, w)
        response_curves.append(g)

        # Reconstruct the HDR image for this channel
        for y in range(height):
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

    response_curves = np.array(response_curves).squeeze()
    hdr_image = hdr_image.squeeze()

    return hdr_image, response_curves


def save_hdr(filename: str, hdr_image: np.ndarray) -> None:
    """
    Save HDR image in Radiance RGBE format (.hdr).

    Args:
        filename: Output filename (should end with .hdr)
        hdr_image: HDR radiance map
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


def tonemap_simple(hdr_image: np.ndarray, gamma: float = 2.2) -> np.ndarray:
    """
    Simple tonemapping using gamma correction.

    Args:
        hdr_image: HDR radiance map
        gamma: Gamma value for correction (default: 2.2)

    Returns:
        8-bit LDR image
    """
    # Normalize to [0, 1]
    normalized = hdr_image / np.max(hdr_image)

    # Apply gamma correction
    corrected = np.power(normalized, 1.0 / gamma)

    # Convert to 8-bit
    ldr_image = (corrected * 255).clip(0, 255).astype(np.uint8)

    return ldr_image
