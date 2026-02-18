/**
 * Utility functions for image processing
 */

/**
 * Convert Base64 image data to a data URL for display
 * @param base64Data - Base64 encoded image string
 * @param imageType - Image MIME type (e.g., 'jpeg', 'png')
 * @returns Data URL string for use in img src attribute
 */
export const getImageDataUrl = (
  base64Data: string | null | undefined,
  imageType: string = "jpeg",
): string | null => {
  if (!base64Data) {
    return null;
  }

  // Clean the imageType (remove 'image/' prefix if present)
  const cleanType = imageType.toLowerCase().replace("image/", "");

  // Return the complete data URL
  return `data:image/${cleanType};base64,${base64Data}`;
};

/**
 * Check if a frame has valid image data
 */
export const hasImageData = (frame: {
  imageData?: string | null;
  imagePath?: string | null;
}): boolean => {
  return !!(frame.imageData || frame.imagePath);
};

/**
 * Get the best available image source from a frame (prioritizes imageData over imagePath)
 */
export const getFrameImageSrc = (frame: {
  imageData?: string | null;
  imagePath?: string | null;
  imageType?: string;
}): string | null => {
  // Prefer imageData (Base64) over imagePath
  if (frame.imageData) {
    return getImageDataUrl(frame.imageData, frame.imageType || "jpeg");
  }

  // Fallback to imagePath if available
  if (frame.imagePath) {
    return frame.imagePath;
  }

  return null;
};
