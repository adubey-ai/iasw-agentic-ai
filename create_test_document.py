#!/usr/bin/env python3
"""
Create a sample marriage certificate for testing
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_marriage_certificate():
    """Create a sample marriage certificate image"""

    # Create white background
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a default font
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        # Fallback to default
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Draw border
    draw.rectangle([(20, 20), (width-20, height-20)], outline='black', width=3)
    draw.rectangle([(30, 30), (width-30, height-30)], outline='black', width=1)

    # Title
    y_position = 60
    draw.text((width//2, y_position), "GOVERNMENT OF INDIA", fill='black',
              font=header_font, anchor='mm')

    y_position += 50
    draw.text((width//2, y_position), "MARRIAGE CERTIFICATE", fill='black',
              font=title_font, anchor='mm')

    # Certificate content
    y_position += 80
    content = [
        ("", ""),
        ("This is to certify that the marriage between:", ""),
        ("", ""),
        ("Bride Name:", "Priya Sharma"),
        ("Date of Birth:", "15-May-1990"),
        ("Father's Name:", "Rajesh Sharma"),
        ("", ""),
        ("AND", ""),
        ("", ""),
        ("Groom Name:", "Rahul Mehta"),
        ("Date of Birth:", "10-March-1988"),
        ("Father's Name:", "Vijay Mehta"),
        ("", ""),
        ("Was solemnized on:", "12th June 2025"),
        ("", ""),
        ("Post Marriage Name:", "Priya Mehta"),
        ("", ""),
        ("Certificate No:", "MC-2025-12345"),
        ("Issued By:", "Municipal Corporation, Mumbai"),
        ("Issue Date:", "15th June 2025"),
    ]

    for label, value in content:
        if not label and not value:
            y_position += 20
            continue

        if label and value:
            text = f"{label:.<30} {value}"
        elif label:
            text = label
        else:
            text = value

        draw.text((80, y_position), text, fill='black', font=body_font)
        y_position += 35

    # Signature area
    y_position += 50
    draw.line([(500, y_position), (700, y_position)], fill='black', width=1)
    y_position += 10
    draw.text((600, y_position), "Authorized Signatory", fill='black',
              font=body_font, anchor='mm')

    # Official stamp placeholder
    draw.ellipse([(100, height-250), (250, height-100)], outline='blue', width=3)
    draw.text((175, height-175), "OFFICIAL\nSTAMP", fill='blue',
              font=body_font, anchor='mm')

    # Save
    output_dir = "data/documents"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/test_marriage_certificate.png"
    img.save(output_path)

    print(f"✅ Test marriage certificate created: {output_path}")
    print(f"   This can be used to test the Legal Name Change flow")
    print(f"   Customer: C001 (Priya Sharma → Priya Mehta)")

    return output_path

if __name__ == "__main__":
    create_marriage_certificate()
