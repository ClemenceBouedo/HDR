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

from debevec import hdr_debevec, save_hdr, tonemap_simple


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

    # Example: assuming images are named like img_001.jpg, img_002.jpg, etc.
    # and exposure times are stored in a separate file or known
    image_files = sorted(image_folder.glob("*.jpg")) + sorted(image_folder.glob("*.png"))

    if not image_files:
        raise ValueError(f"No images found in {image_folder}")

    images = []
    for img_file in image_files:
        img = imageio.imread(img_file)
        images.append(img)

    # Example exposure times (you should replace these with actual values)
    # These are typically in seconds: 1/1000, 1/500, 1/250, etc.
    num_images = len(images)
    # Generate example exposure times: exponentially increasing
    exposure_times = np.array([1/1000 * (2**i) for i in range(num_images)])

    print(f"Loaded {num_images} images")
    print(f"Exposure times: {exposure_times}")

    return images, exposure_times


def create_synthetic_exposures(base_image: np.ndarray, num_exposures: int = 7) -> tuple[list[np.ndarray], np.ndarray]:
    """
    Create synthetic exposure bracketing from a single image (for testing).

    Args:
        base_image: Base image to create exposures from
        num_exposures: Number of synthetic exposures to create

    Returns:
        images: List of synthetic exposure images
        exposure_times: Array of exposure times
    """
    # Generate exposure times centered around 1.0
    exposure_times = np.array([2**i for i in range(-num_exposures//2, num_exposures//2 + 1)])

    images = []
    for exp_time in exposure_times:
        # Simulate different exposures by scaling and clipping
        scaled = (base_image.astype(float) * exp_time).clip(0, 255).astype(np.uint8)
        images.append(scaled)

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


def compare_exposures_and_hdr(images: list[np.ndarray], hdr_image: np.ndarray, tonemapped: np.ndarray) -> None:
    """
    Display original exposures alongside HDR and tonemapped result.

    Args:
        images: List of input images
        hdr_image: HDR radiance map
        tonemapped: Tonemapped LDR image
    """
    num_images = len(images)
    fig, axes = plt.subplots(2, (num_images + 2) // 2, figsize=(15, 8))
    fig.suptitle('Exposure Bracketing and HDR Result', fontsize=16)

    axes = axes.flatten()

    # Show input images
    for i, img in enumerate(images):
        axes[i].imshow(img)
        axes[i].set_title(f'Exposure {i+1}')
        axes[i].axis('off')

    # Show HDR (log scale for visualization)
    if len(axes) > num_images:
        hdr_display = np.log1p(hdr_image)
        hdr_display = (hdr_display / hdr_display.max() * 255).astype(np.uint8)
        axes[num_images].imshow(hdr_display)
        axes[num_images].set_title('HDR (log scale)')
        axes[num_images].axis('off')

    # Show tonemapped result
    if len(axes) > num_images + 1:
        axes[num_images + 1].imshow(tonemapped)
        axes[num_images + 1].set_title('Tonemapped Result')
        axes[num_images + 1].axis('off')

    # Hide unused subplots
    for i in range(num_images + 2, len(axes)):
        axes[i].axis('off')

    plt.tight_layout()
    plt.show()


def main():
    """Main function to demonstrate HDR creation."""
    print("=== HDR Image Creation using Debevec Algorithm ===\n")

    # Option 1: Load real exposure sequence
    # Uncomment and modify path to use real images
    # image_folder = "path/to/your/exposure/sequence"
    # images, exposure_times = load_exposure_sequence(image_folder)

    # Option 2: Create synthetic exposures for testing
    print("Loading test image...")
    # Try to load a sample image, or create a synthetic one
    try:
        base_image = imageio.imread('sample_image.jpg')
    except FileNotFoundError:
        print("No sample image found. Creating synthetic test image...")
        # Create a gradient test image
        h, w = 480, 640
        x = np.linspace(0, 1, w)
        y = np.linspace(0, 1, h)
        X, Y = np.meshgrid(x, y)
        base_image = np.stack([
            (X * 255).astype(np.uint8),
            (Y * 255).astype(np.uint8),
            ((X + Y) / 2 * 255).astype(np.uint8)
        ], axis=2)

    print("Creating synthetic exposure sequence...")
    images, exposure_times = create_synthetic_exposures(base_image, num_exposures=5)

    # Create HDR image
    print("\nComputing HDR radiance map...")
    print("This may take a few moments...")
    hdr_image, response_curves = hdr_debevec(
        images=images,
        exposure_times=exposure_times,
        lambda_smooth=50.0,
        num_samples=100
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

    # Create tonemapped version
    print("\nCreating tonemapped LDR image...")
    tonemapped = tonemap_simple(hdr_image, gamma=2.2)
    imageio.imwrite('output_tonemapped.jpg', tonemapped)
    print("Tonemapped image saved as: output_tonemapped.jpg")

    # Display results
    print("\nDisplaying results...")
    compare_exposures_and_hdr(images, hdr_image, tonemapped)

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
