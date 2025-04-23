import os
import shutil
import random
from pathlib import Path

# Define paths
dataset_root = os.path.join('dataset', 'real_vs_fake')              # Update with your dataset path
output_root = os.path.join('dataset', 'output_subset_20k')          # Update with your desired output path
real_dir = os.path.join(dataset_root, "train", "real")              # Directory with real images
fake_dir = os.path.join(dataset_root, "train", "fake")              # Directory with fake images

# Number of images to select
total_images = 20000
real_images_count = total_images // 2  # 10,000 real
fake_images_count = total_images // 2  # 10,000 fake

# Split ratios (80% train, 10% val, 10% test)
train_ratio = 0.8
val_ratio = 0.1
test_ratio = 0.1

# Create output directories
output_dirs = {
    "train": {
        "real": os.path.join(output_root, "train", "real"),
        "fake": os.path.join(output_root, "train", "fake")
    },
    "val": {
        "real": os.path.join(output_root, "val", "real"),
        "fake": os.path.join(output_root, "val", "fake")
    },
    "test": {
        "real": os.path.join(output_root, "test", "real"),
        "fake": os.path.join(output_root, "test", "fake")
    }
}

# Create directories if they don't exist
for split in output_dirs:
    for label in output_dirs[split]:
        Path(output_dirs[split][label]).mkdir(parents=True, exist_ok=True)

# Function to get list of image files
def get_image_files(directory):
    return [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# Get all real and fake images
real_images = get_image_files(real_dir)
fake_images = get_image_files(fake_dir)

# Ensure there are enough images
if len(real_images) < real_images_count or len(fake_images) < fake_images_count:
    raise ValueError("Not enough images in the dataset. Ensure real and fake directories have at least 10,000 images each.")

# Randomly sample images
random.seed(42)  # For reproducibility
selected_real = random.sample(real_images, real_images_count)
selected_fake = random.sample(fake_images, fake_images_count)

# Calculate split sizes
train_real_count = int(real_images_count * train_ratio)  # 8,000
val_real_count = int(real_images_count * val_ratio)      # 1,000
test_real_count = real_images_count - train_real_count - val_real_count  # 1,000

train_fake_count = int(fake_images_count * train_ratio)  # 8,000
val_fake_count = int(fake_images_count * val_ratio)      # 1,000
test_fake_count = fake_images_count - train_fake_count - val_fake_count  # 1,000

# Split images
real_splits = {
    "train": selected_real[:train_real_count],
    "val": selected_real[train_real_count:train_real_count + val_real_count],
    "test": selected_real[train_real_count + val_real_count:]
}

fake_splits = {
    "train": selected_fake[:train_fake_count],
    "val": selected_fake[train_fake_count:train_fake_count + val_fake_count],
    "test": selected_fake[train_fake_count + val_fake_count:]
}

# Copy images to respective directories
def copy_images(image_list, src_dir, dest_dir):
    for img in image_list:
        src_path = os.path.join(src_dir, img)
        dest_path = os.path.join(dest_dir, img)
        shutil.copy2(src_path, dest_path)

# Copy real images
for split in real_splits:
    copy_images(real_splits[split], real_dir, output_dirs[split]["real"])
    print(f"Copied {len(real_splits[split])} real images to {output_dirs[split]['real']}")

# Copy fake images
for split in fake_splits:
    copy_images(fake_splits[split], fake_dir, output_dirs[split]["fake"])
    print(f"Copied {len(fake_splits[split])} fake images to {output_dirs[split]['fake']}")

print(f"Subset creation complete! Total images: {total_images} (10,000 real, 10,000 fake)")
print(f"Output directory structure: {output_root}")
print(f"Train: {train_real_count + train_fake_count} images (8,000 real, 8,000 fake)")
print(f"Validation: {val_real_count + val_fake_count} images (1,000 real, 1,000 fake)")
print(f"Test: {test_real_count + test_fake_count} images (1,000 real, 1,000 fake)")