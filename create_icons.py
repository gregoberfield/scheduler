#!/usr/bin/env python3
"""
Create placeholder class icons
Simple colored squares representing each WoW TBC class
"""

import os

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("PIL/Pillow not installed. Install with: pip install Pillow")
    print("Creating basic placeholders instead...")

# WoW TBC class colors (RGB)
CLASS_COLORS = {
    'warrior': (199, 156, 110),
    'paladin': (245, 140, 186),
    'hunter': (171, 212, 115),
    'rogue': (255, 245, 105),
    'priest': (255, 255, 255),
    'shaman': (0, 112, 222),
    'mage': (105, 204, 240),
    'warlock': (148, 130, 201),
    'druid': (255, 125, 10)
}

CLASS_INITIALS = {
    'warrior': 'W',
    'paladin': 'P',
    'hunter': 'H',
    'rogue': 'R',
    'priest': 'Pr',
    'shaman': 'S',
    'mage': 'M',
    'warlock': 'Wl',
    'druid': 'D'
}

def create_icon_with_pil(class_name, color, initial):
    """Create icon using PIL with text"""
    size = (36, 36)
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fall back to default
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
    except:
        try:
            font = ImageFont.truetype('arial.ttf', 18)
        except:
            font = ImageFont.load_default()
    
    # Determine text color (white for dark backgrounds, black for light)
    text_color = (0, 0, 0) if class_name in ['priest', 'rogue'] else (255, 255, 255)
    
    # Get text size and position to center it
    bbox = draw.textbbox((0, 0), initial, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2 - 2)
    
    draw.text(position, initial, fill=text_color, font=font)
    
    return img

def create_icon_simple(class_name, color):
    """Create simple colored square without PIL"""
    # Create a simple PPM file (a basic image format)
    size = 36
    filename = f'{class_name}.jpg'
    
    # For systems without PIL, create a minimal colored square
    # This creates a PPM file which can be viewed in most browsers
    with open(filename.replace('.jpg', '.ppm'), 'w') as f:
        f.write('P3\n')
        f.write(f'{size} {size}\n')
        f.write('255\n')
        for _ in range(size):
            for _ in range(size):
                f.write(f'{color[0]} {color[1]} {color[2]} ')
            f.write('\n')
    
    print(f"  Created {filename.replace('.jpg', '.ppm')} (convert to JPG manually)")

def main():
    # Change to classes directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    classes_dir = os.path.join(script_dir, 'app', 'static', 'img', 'classes')
    
    if not os.path.exists(classes_dir):
        print(f"Error: Directory not found: {classes_dir}")
        return
    
    os.chdir(classes_dir)
    print(f"Creating placeholder class icons in {classes_dir}...")
    print()
    
    for class_name, color in CLASS_COLORS.items():
        filename = f'{class_name}.jpg'
        initial = CLASS_INITIALS[class_name]
        
        if HAS_PIL:
            img = create_icon_with_pil(class_name, color, initial)
            img.save(filename, 'JPEG')
            print(f"  ✓ Created {filename}")
        else:
            create_icon_simple(class_name, color)
    
    print()
    if HAS_PIL:
        print("✓ All placeholder class icons created!")
    else:
        print("✓ Basic placeholder files created (PPM format)")
        print("  Install Pillow for better quality: pip install Pillow")
    print()
    print("Note: For better quality, replace these with official WoW icons from Wowhead")
    print("      Visit: https://www.wowhead.com/icons?filter=11;1;0")

if __name__ == '__main__':
    main()
