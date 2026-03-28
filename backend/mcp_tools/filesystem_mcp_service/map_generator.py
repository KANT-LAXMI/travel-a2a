"""
Map Page Generator for Travel Plans
Generates an illustrated infographic-style map page with location images
"""
import logging
from typing import Dict, Any, List
from io import BytesIO
import urllib.request

logger = logging.getLogger(__name__)


def convert_to_thumbnail_url(url: str, width: int = 400) -> str:
    """
    Convert Wikipedia full-size image URL to thumbnail URL
    This helps avoid rate limiting as suggested by Wikipedia
    
    Example:
    https://upload.wikimedia.org/wikipedia/commons/3/3f/Image.jpg
    -> https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Image.jpg/400px-Image.jpg
    """
    try:
        # Check if already a thumbnail URL
        if '/thumb/' in url:
            return url
        
        # Parse the URL - handle both commons and language-specific wikis
        if 'upload.wikimedia.org/wikipedia/' in url:
            # Find the position after 'wikipedia/'
            wiki_pos = url.find('/wikipedia/') + len('/wikipedia/')
            base_url = url[:wiki_pos]  # e.g., "https://upload.wikimedia.org/wikipedia/"
            
            # Get the rest: "commons/3/3f/Image.jpg" or "en/3/3f/Image.jpg"
            rest = url[wiki_pos:]
            
            # Split into parts
            parts = rest.split('/')
            if len(parts) >= 4:  # e.g., ['commons', '3', '3f', 'Image.jpg']
                wiki_type = parts[0]  # 'commons' or 'en', etc.
                hash1 = parts[1]
                hash2 = parts[2]
                filename = '/'.join(parts[3:])  # Handle filenames with slashes
                
                # Build thumbnail URL
                thumb_url = f"{base_url}{wiki_type}/thumb/{hash1}/{hash2}/{filename}/{width}px-{filename.split('/')[-1]}"
                logger.info(f"🔄 Converted to thumbnail: {thumb_url[:80]}...")
                return thumb_url
        
        # If conversion fails, return original
        logger.warning(f"⚠️ Could not convert URL to thumbnail, using original")
        return url
    except Exception as e:
        logger.warning(f"⚠️ Could not convert to thumbnail URL: {e}")
        return url


def download_image(url: str, max_size=(400, 300), max_retries=3) -> 'Image':
    """Download and resize image from URL with retry logic and thumbnail conversion"""
    try:
        from PIL import Image
        import time
        import ssl
        
        # Convert to thumbnail URL to avoid rate limiting
        thumbnail_url = convert_to_thumbnail_url(url, width=400)
        
        # Create SSL context that doesn't verify certificates (for Wikipedia)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        for attempt in range(max_retries):
            try:
                # Add delay to avoid rate limiting with exponential backoff
                if attempt > 0:
                    wait_time = 10 * (2 ** (attempt - 1))  # 10s, 20s, 40s (longer delays for rate limiting)
                    logger.info(f"⏳ Retry {attempt + 1}/{max_retries} after {wait_time}s wait...")
                    time.sleep(wait_time)
                else:
                    time.sleep(5.0)  # Initial delay 5 seconds
                
                # Add comprehensive headers to mimic a real browser
                req = urllib.request.Request(
                    thumbnail_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Referer': 'https://en.wikipedia.org/',
                        'Sec-Fetch-Dest': 'image',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'same-site',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                )
                
                logger.info(f"📥 Downloading: {thumbnail_url}")
                
                with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                    img_data = response.read()
                    logger.info(f"✅ Downloaded {len(img_data)} bytes")
                    
                    img = Image.open(BytesIO(img_data))
                    logger.info(f"✅ Image opened: {img.size}, mode: {img.mode}")
                    
                    # Convert to RGB if needed
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        if img.mode in ('RGBA', 'LA'):
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                        logger.info(f"✅ Converted to RGB")
                    
                    # Resize maintaining aspect ratio
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    logger.info(f"✅ Resized to: {img.size}")
                    return img
                    
            except urllib.error.HTTPError as e:
                if (e.code == 429 or e.code == 403) and attempt < max_retries - 1:
                    logger.warning(f"⚠️ HTTP {e.code}, will retry with longer wait...")
                    continue
                else:
                    logger.error(f"❌ HTTP Error {e.code}: {e.reason}")
                    # Try original URL as fallback
                    if thumbnail_url != url and attempt == max_retries - 1:
                        logger.info(f"🔄 Trying original URL as fallback...")
                        thumbnail_url = url
                        continue
                    return None
            except urllib.error.URLError as e:
                logger.error(f"❌ URL Error: {e.reason}")
                return None
                
        return None
            
    except Exception as e:
        logger.error(f"❌ Error downloading image: {e}")
        return None


def generate_map_page_content(
    destination: str,
    locations: List[Dict[str, Any]],
    duration_days: int,
    city_tagline: str = None,
    travel_tips: List[str] = None
) -> bytes:
    """
    Generate an infographic-style travel guide page
    
    Args:
        destination: City/place name
        locations: List of location dictionaries with lat/lon/image/extract
        duration_days: Trip duration
        city_tagline: One-liner description of the city
        travel_tips: List of travel tips for the destination
    
    Returns:
        PNG image bytes
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # A4 dimensions at 200 DPI
        W, H = 1654, 2339
        
        # Colors - vibrant travel poster style
        SKY_BLUE = (135, 206, 250)
        HEADER_ORANGE = (255, 140, 0)
        SECTION_BLUE = (30, 144, 255)
        WHITE = (255, 255, 255)
        TEXT_DARK = (40, 40, 40)
        CARD_BG = (255, 250, 240)
        
        # Create canvas with gradient background
        img = Image.new('RGB', (W, H), SKY_BLUE)
        draw = ImageDraw.Draw(img)
        
        # Gradient background (light blue)
        for y in range(H):
            ratio = y / H
            r = int(135 + (240 - 135) * ratio)
            g = int(206 + (248 - 206) * ratio)
            b = 250
            draw.line([(0, y), (W, y)], fill=(r, g, b))
        
        # Load fonts
        try:
            font_title = ImageFont.truetype("arialbd.ttf", 120)
            font_subtitle = ImageFont.truetype("arial.ttf", 45)
            font_section = ImageFont.truetype("arialbd.ttf", 80)
            font_card_title = ImageFont.truetype("arialbd.ttf", 36)
            font_card_text = ImageFont.truetype("arial.ttf", 26)
        except:
            try:
                font_title = ImageFont.truetype("Arial.ttf", 120)
                font_subtitle = ImageFont.truetype("Arial.ttf", 45)
                font_section = ImageFont.truetype("Arial.ttf", 80)
                font_card_title = ImageFont.truetype("Arial.ttf", 36)
                font_card_text = ImageFont.truetype("Arial.ttf", 26)
            except:
                font_title = ImageFont.load_default()
                font_subtitle = ImageFont.load_default()
                font_section = ImageFont.load_default()
                font_card_title = ImageFont.load_default()
                font_card_text = ImageFont.load_default()
        
        # Header section
        header_h = 300
        draw.rectangle([0, 0, W, header_h], fill=HEADER_ORANGE)
        
        # Title
        title_text = destination.upper()
        try:
            bbox = draw.textbbox((0, 0), title_text, font=font_title)
            title_w = bbox[2] - bbox[0]
        except:
            title_w = len(title_text) * 60
        
        # Shadow
        draw.text(((W - title_w) // 2 + 4, 84), title_text, fill=(0, 0, 0, 100), font=font_title)
        draw.text(((W - title_w) // 2, 80), title_text, fill=WHITE, font=font_title)
        
        # Subtitle
        subtitle = city_tagline or f"Explore the beauty and culture of {destination}"
        try:
            bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
            sub_w = bbox[2] - bbox[0]
        except:
            sub_w = len(subtitle) * 22
        
        draw.text(((W - sub_w) // 2, 220), subtitle, fill=(255, 255, 200), font=font_subtitle)
        
        y_pos = header_h + 80
        
        # Get locations with images
        locs_with_images = [loc for loc in locations if loc.get('image')]
        logger.info(f"📸 Found {len(locs_with_images)} locations with images")
        
        # Alternating image layout (left/right with extract text beside)
        if locs_with_images:
            margin = 100
            img_width = 600
            text_width = W - (2 * margin) - img_width - 60
            row_height = 380
            
            successful_downloads = 0  # Track successfully downloaded images
            
            for i, loc in enumerate(locs_with_images):  # Process ALL images (no limit)
                logger.info(f"Processing location {i+1}/{len(locs_with_images)}: {loc.get('name')}")
                
                # Download image
                img_obj = download_image(loc['image'], max_size=(img_width, 350))
                
                if img_obj:
                    logger.info(f"✅ Image downloaded for {loc.get('name')}")
                    
                    # Determine if image goes on left or right (alternating based on successful downloads)
                    is_left = (successful_downloads % 2 == 0)
                    
                    if is_left:
                        # Image on left, text on right
                        img_x = margin
                        text_x = margin + img_width + 40
                    else:
                        # Image on right, text on left
                        img_x = W - margin - img_width
                        text_x = margin
                    
                    img_y = y_pos
                    
                    # Draw image with border
                    img_w, img_h = img_obj.size
                    draw.rectangle([img_x - 3, img_y - 3, img_x + img_w + 3, img_y + img_h + 3],
                                  outline=SECTION_BLUE, width=4)
                    img.paste(img_obj, (img_x, img_y))
                    
                    # Draw extract text beside image
                    extract = loc.get('extract', '')[:300]  # Limit text length
                    
                    # Location name (bold)
                    name = loc.get('name', '')
                    draw.text((text_x, img_y), name, fill=TEXT_DARK, font=font_card_title)
                    
                    # Extract text (wrapped)
                    text_y = img_y + 50
                    words = extract.split()
                    lines = []
                    current_line = ""
                    
                    for word in words:
                        test_line = current_line + " " + word if current_line else word
                        try:
                            bbox = draw.textbbox((0, 0), test_line, font=font_card_text)
                            if bbox[2] - bbox[0] < text_width:
                                current_line = test_line
                            else:
                                if current_line:
                                    lines.append(current_line)
                                current_line = word
                        except:
                            if len(test_line) * 13 < text_width:
                                current_line = test_line
                            else:
                                if current_line:
                                    lines.append(current_line)
                                current_line = word
                    
                    if current_line:
                        lines.append(current_line)
                    
                    # Draw wrapped text (max 10 lines)
                    for line_idx, line in enumerate(lines[:10]):
                        draw.text((text_x, text_y + line_idx * 32), line, fill=TEXT_DARK, font=font_card_text)
                    
                    # Only increment position and counter if image was successfully added
                    y_pos += row_height
                    successful_downloads += 1
                else:
                    logger.warning(f"⚠️ Could not download image for {loc.get('name')}, skipping...")
            
            logger.info(f"✅ Successfully added {successful_downloads}/{len(locs_with_images)} images to map page")
        
        # TRAVEL TIPS Section
        draw.rectangle([100, y_pos, W - 100, y_pos + 100], fill=SECTION_BLUE)
        section_title = "Travel Tips"
        try:
            bbox = draw.textbbox((0, 0), section_title, font=font_section)
            sec_w = bbox[2] - bbox[0]
        except:
            sec_w = len(section_title) * 40
        
        draw.text(((W - sec_w) // 2, y_pos + 15), section_title, fill=WHITE, font=font_section)
        y_pos += 130
        
        # Tips - use provided tips or fallback to defaults
        if travel_tips and len(travel_tips) > 0:
            tips = travel_tips[:4]  # Max 4 tips
        else:
            tips = [
                f"📅 Best time to visit: October to March",
                f"🚗 {destination} is easily accessible by train and flight",
                f"🏨 Book accommodation in advance during peak season",
                f"📸 Don't forget your camera for stunning photos",
            ]
        
        for tip in tips:
            draw.text((150, y_pos), tip, fill=TEXT_DARK, font=font_card_text)
            y_pos += 55
        
        # Footer
        y_pos = H - 120
        footer_text = f"{duration_days}-Day Travel Plan • {len(locations)} Amazing Locations"
        try:
            bbox = draw.textbbox((0, 0), footer_text, font=font_subtitle)
            footer_w = bbox[2] - bbox[0]
        except:
            footer_w = len(footer_text) * 22
        
        draw.text(((W - footer_w) // 2, y_pos), footer_text, fill=TEXT_DARK, font=font_subtitle)
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG', dpi=(200, 200))
        logger.info("✅ Map page generated successfully")
        return buffer.getvalue()
        
    except ImportError as e:
        logger.error(f"❌ PIL/Pillow not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error generating map: {e}", exc_info=True)
        return None


def can_generate_map() -> bool:
    """Check if map generation is available"""
    try:
        from PIL import Image
        return True
    except ImportError:
        return False
