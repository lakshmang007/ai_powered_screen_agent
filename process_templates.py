import cv2
import os
import numpy as np

# Source image path (from user upload)
source_path = r"C:/Users/laksh/.gemini/antigravity/brain/f5492b27-34e9-4c14-8167-7686aa4a3060/uploaded_image_1764476022021.png"
output_dir = r"c:\5th sem\ai_powered_screen_agent\src\templates"

def process_templates():
    if not os.path.exists(source_path):
        print(f"Error: Source image not found at {source_path}")
        return

    # Load image
    img = cv2.imread(source_path)
    if img is None:
        print("Error: Failed to load image")
        return

    height, width = img.shape[:2]
    print(f"Image loaded: {width}x{height}")

    # Assuming the image contains the 3 buttons in a row: Minimize, Maximize, Close
    # We'll split it into 3 equal parts horizontally
    button_width = width // 3
    
    # Extract Minimize (Left)
    minimize_img = img[:, :button_width]
    cv2.imwrite(os.path.join(output_dir, "minimize.png"), minimize_img)
    print("Saved minimize.png")

    # Extract Maximize (Middle)
    maximize_img = img[:, button_width:button_width*2]
    cv2.imwrite(os.path.join(output_dir, "maximize.png"), maximize_img)
    print("Saved maximize.png")

    # Extract Close (Right)
    close_img = img[:, button_width*2:]
    cv2.imwrite(os.path.join(output_dir, "close.png"), close_img)
    print("Saved close.png")

if __name__ == "__main__":
    process_templates()
