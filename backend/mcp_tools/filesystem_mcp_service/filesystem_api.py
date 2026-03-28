"""
Filesystem API Service
======================
Provides file system operations for saving travel plans as PDFs.

Features:
- Save travel plans as PDF files with illustrated map page
- Organize plans in folders
- Read/write travel documents
- Manage trip data files

File naming convention:
- Format: {duration}_day_plan_to_{destination}.pdf
- Example: 2_day_plan_to_mumbai.pdf
- Location: plans/ folder
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class FilesystemAPI:
    """
    Filesystem API Client for Travel Plan Management
    
    Handles saving travel plans as PDF files with proper organization.
    """
    
    def __init__(self, base_dir: str = "plans"):
        """
        Initialize Filesystem API
        
        Args:
            base_dir: Base directory for storing plans (default: "plans")
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        logger.info(f"✅ Filesystem API initialized - Base dir: {self.base_dir}")
    
    def save_plan_as_pdf(
        self,
        destination: str,
        duration_days: int,
        plan_data: Dict[str, Any],
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Save travel plan as PDF file
        
        Args:
            destination: Destination name (e.g., "Mumbai", "Goa")
            duration_days: Trip duration in days
            plan_data: Complete plan data (budget, itinerary, map, etc.)
            session_id: Optional session ID for tracking
        
        Returns:
            Dictionary with:
            - success: bool
            - filename: str (PDF filename)
            - filepath: str (full path)
            - size_kb: float (file size)
        
        Example:
            >>> fs = FilesystemAPI()
            >>> result = fs.save_plan_as_pdf("Mumbai", 2, plan_data)
            >>> print(result['filename'])
            '2_day_plan_to_mumbai.pdf'
        """
        logger.info(f"💾 Saving plan: {duration_days} days to {destination}")
        
        try:
            # Generate filename
            filename = self._generate_filename(destination, duration_days)
            filepath = self.base_dir / filename
            
            # Generate PDF content
            pdf_content = self._generate_pdf_content(
                destination, duration_days, plan_data
            )
            
            # Save PDF file
            self._save_pdf(filepath, pdf_content)
            
            # Get file size
            file_size_kb = filepath.stat().st_size / 1024
            
            # Save metadata JSON
            self._save_metadata(filepath, plan_data, session_id)
            
            result = {
                'success': True,
                'filename': filename,
                'filepath': str(filepath.absolute()),
                'size_kb': round(file_size_kb, 2),
                'created_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Plan saved: {filename} ({file_size_kb:.2f} KB)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error saving plan: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_filename(self, destination: str, duration_days: int) -> str:
        """
        Generate filename for travel plan
        
        Format: {duration}_day_plan_to_{destination}.pdf
        Example: 2_day_plan_to_mumbai.pdf
        """
        # Clean destination name (remove spaces, special chars)
        clean_destination = destination.lower().replace(' ', '_')
        clean_destination = ''.join(c for c in clean_destination if c.isalnum() or c == '_')
        
        # Generate filename
        filename = f"{duration_days}_day_plan_to_{clean_destination}.pdf"
        
        return filename
    
    def _generate_pdf_content(
        self,
        destination: str,
        duration_days: int,
        plan_data: Dict[str, Any]
    ) -> bytes:
        """
        Generate professional PDF with cover page, budget, itinerary, and locations
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import mm
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                HRFlowable, PageBreak
            )
            from io import BytesIO
            
            # Color palette
            SAFFRON = colors.HexColor("#E87722")
            DARK_NAVY = colors.HexColor("#1A2C4E")
            TEAL = colors.HexColor("#2E8B8B")
            LIGHT_BG = colors.HexColor("#FFF8F2")
            MID_GREY = colors.HexColor("#6B7280")
            LIGHT_LINE = colors.HexColor("#E5E7EB")
            WHITE = colors.white
            GREEN = colors.HexColor("#16A34A")
            
            W, H = A4
            DAY_COLORS = {1: SAFFRON, 2: TEAL, 3: GREEN, 4: colors.HexColor("#9333EA")}
            
            # Extract data
            budget = plan_data.get('budget', {})
            itinerary = plan_data.get('itinerary', {})
            days = itinerary.get('days', [])
            locations = plan_data.get('map', {}).get('locations', [])
            total_budget = budget.get('total', 0)
            total_meals = sum(len(d.get('activities', [])) for d in days)
            
            # Styles
            def S(name, **kw):
                return ParagraphStyle(name, **kw)
            
            SECTION_HEAD = S("SecHead", fontSize=16, textColor=DARK_NAVY,
                           fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)
            BODY_STYLE = S("Body", fontSize=10, textColor=MID_GREY,
                          fontName="Helvetica", spaceAfter=4, leading=14)
            DAY_HEAD = S("DayHead", fontSize=18, textColor=WHITE,
                        fontName="Helvetica-Bold", alignment=TA_CENTER)
            TIME_STYLE = S("Time", fontSize=9, textColor=SAFFRON, fontName="Helvetica-Bold")
            ACT_TITLE = S("ActTitle", fontSize=11, textColor=DARK_NAVY,
                         fontName="Helvetica-Bold", spaceAfter=1)
            ACT_DESC = S("ActDesc", fontSize=9, textColor=MID_GREY,
                        fontName="Helvetica", spaceAfter=3)
            
            # Canvas callbacks for header/footer
            def make_first_page_cb():
                def callback(canvas, doc):
                    canvas.saveState()
                    # Dark cover block
                    canvas.setFillColor(DARK_NAVY)
                    canvas.rect(0, H - 115 * mm, W, 115 * mm, fill=1, stroke=0)
                    canvas.setFillColor(SAFFRON)
                    canvas.rect(0, H - 115 * mm - 4, W, 4, fill=1, stroke=0)
                    
                    cx = W / 2
                    # Trip title
                    canvas.setFont("Helvetica-Bold", 26)
                    canvas.setFillColor(WHITE)
                    canvas.drawCentredString(cx, H - 38 * mm, f"{destination} Travel Plan")
                    
                    # Destination line
                    canvas.setFont("Helvetica", 13)
                    canvas.setFillColor(colors.HexColor("#FFD8A8"))
                    canvas.drawCentredString(cx, H - 52 * mm,
                                           f"{destination}  •  Rs. {int(total_budget):,} Total Budget")
                    
                    # Tagline
                    canvas.setFont("Helvetica-Oblique", 11)
                    canvas.drawCentredString(cx, H - 63 * mm, "AI-Powered Travel Planning")
                    
                    # Stat pills
                    stats = [
                        (f"{duration_days} Days", "Duration"),
                        (f"Rs. {int(total_budget):,}", "Budget"),
                        (f"{len(locations)} Spots", "Locations"),
                    ]
                    pill_w = 36 * mm
                    gap = 6 * mm
                    total_w = len(stats) * pill_w + (len(stats) - 1) * gap
                    x0 = (W - total_w) / 2
                    y_pill = H - 100 * mm
                    
                    for idx, (val, label) in enumerate(stats):
                        px = x0 + idx * (pill_w + gap)
                        canvas.setFillColor(colors.HexColor("#243A5E"))
                        canvas.roundRect(px, y_pill, pill_w, 18 * mm, 4, fill=1, stroke=0)
                        canvas.setFont("Helvetica-Bold", 15)
                        canvas.setFillColor(SAFFRON)
                        canvas.drawCentredString(px + pill_w / 2, y_pill + 10 * mm, val)
                        canvas.setFont("Helvetica", 8)
                        canvas.setFillColor(colors.HexColor("#9CA3AF"))
                        canvas.drawCentredString(px + pill_w / 2, y_pill + 4 * mm, label)
                    
                    canvas.restoreState()
                return callback
            
            def make_later_pages_cb():
                def callback(canvas, doc):
                    canvas.saveState()
                    # Top bar
                    canvas.setFillColor(DARK_NAVY)
                    canvas.rect(0, H - 18 * mm, W, 18 * mm, fill=1, stroke=0)
                    canvas.setFillColor(SAFFRON)
                    canvas.rect(0, H - 18 * mm - 3, W, 3, fill=1, stroke=0)
                    canvas.setFont("Helvetica-Bold", 9)
                    canvas.setFillColor(WHITE)
                    canvas.drawString(20 * mm, H - 12 * mm, f"{destination} Travel Plan")
                    canvas.setFont("Helvetica", 9)
                    canvas.drawRightString(W - 20 * mm, H - 12 * mm, f"Page {doc.page}")
                    
                    # Footer
                    canvas.setFillColor(LIGHT_LINE)
                    canvas.rect(0, 0, W, 10 * mm, fill=1, stroke=0)
                    canvas.setFont("Helvetica", 7)
                    canvas.setFillColor(MID_GREY)
                    canvas.drawCentredString(W / 2, 3.5 * mm,
                                           f"{destination}  •  Budget: Rs. {int(total_budget):,}  •  {datetime.now().strftime('%B %Y')}")
                    canvas.restoreState()
                return callback
            
            # Build story
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer, pagesize=A4,
                leftMargin=20 * mm, rightMargin=20 * mm,
                topMargin=20 * mm, bottomMargin=15 * mm,
                title=f"{destination} Travel Plan"
            )
            story = []
            
            # Cover spacer
            story.append(Spacer(1, 122 * mm))
            story.append(Spacer(1, 8 * mm))
            
            # Try to add illustrated map page
            try:
                from backend.mcp_tools.filesystem_mcp_service.map_generator import (
                    generate_map_page_content, can_generate_map
                )
                
                if can_generate_map() and locations:
                    logger.info("🗺️ Adding illustrated locations section...")
                    
                    # Get city tagline and tips from itinerary data
                    city_tagline = None
                    itinerary_data = plan_data.get('itinerary', {})
                    
                    if 'summary' in plan_data:
                        city_tagline = plan_data['summary']
                    elif itinerary_data and itinerary_data.get('summary'):
                        city_tagline = itinerary_data['summary']
                    
                    travel_tips = None
                    if itinerary_data and itinerary_data.get('tips'):
                        tips_data = itinerary_data['tips']
                        if isinstance(tips_data, list):
                            travel_tips = tips_data
                        elif isinstance(tips_data, str):
                            travel_tips = [t.strip() for t in tips_data.split('\n') if t.strip()]
                    
                    # Add destination header with orange background
                    from reportlab.platypus import Image as RLImage, Table, TableStyle
                    
                    # Header table with orange background
                    header_title = Paragraph(f"<b>{destination.upper()}</b>",
                                            S("dest_title", fontSize=24, fontName="Helvetica-Bold",
                                              textColor=WHITE, alignment=TA_CENTER))
                    header_subtitle = Paragraph(city_tagline or f"Explore the beauty and culture of {destination}",
                                               S("dest_sub", fontSize=12, fontName="Helvetica",
                                                 textColor=colors.HexColor("#FFE4B5"), alignment=TA_CENTER))
                    
                    header_table = Table([[header_title], [header_subtitle]], colWidths=[170 * mm])
                    header_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), SAFFRON),
                        ("TOPPADDING", (0, 0), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]))
                    story.append(header_table)
                    story.append(Spacer(1, 8))
                    
                    # Add locations with alternating layout
                    from io import BytesIO
                    from backend.mcp_tools.filesystem_mcp_service.map_generator import download_image
                    
                    locs_with_images = [loc for loc in locations if loc.get('image')]
                    logger.info(f"📸 Found {len(locs_with_images)} locations with images")
                    
                    # Download ALL images (no limit)
                    successful_images = 0
                    for i, loc in enumerate(locs_with_images):
                        try:
                            # Try to download image
                            img_obj = download_image(loc['image'], max_size=(350, 250))
                            
                            if img_obj:
                                # Convert PIL image to bytes
                                img_buffer = BytesIO()
                                img_obj.save(img_buffer, format='PNG')
                                img_buffer.seek(0)
                                
                                # Create image element
                                img_width = min(img_obj.width, 350)
                                img_height = int(img_obj.height * (img_width / img_obj.width))
                                rl_img = RLImage(img_buffer, width=img_width * 0.45, height=img_height * 0.45)
                                
                                # Location name and extract
                                loc_name = loc.get('name', 'Location')
                                extract = loc.get('extract', '')[:250]
                                
                                # Create text content
                                name_para = Paragraph(f"<b>{loc_name}</b>", 
                                                     S(f"loc{i}", fontSize=11, fontName="Helvetica-Bold", 
                                                       textColor=DARK_NAVY, spaceAfter=4))
                                extract_para = Paragraph(extract if extract else "", 
                                                        S(f"ext{i}", fontSize=9, fontName="Helvetica", 
                                                          textColor=MID_GREY, leading=12))
                                
                                # Alternate left/right layout
                                if i % 2 == 0:
                                    # Image on left, text on right
                                    row_data = [[rl_img, [name_para, extract_para]]]
                                    col_widths = [80 * mm, 90 * mm]
                                else:
                                    # Text on left, image on right
                                    row_data = [[[name_para, extract_para], rl_img]]
                                    col_widths = [90 * mm, 80 * mm]
                                
                                # Create table for this location with blue background
                                loc_table = Table(row_data, colWidths=col_widths)
                                loc_table.setStyle(TableStyle([
                                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E0F2FE")),
                                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#7DD3FC")),
                                ]))
                                
                                story.append(loc_table)
                                story.append(Spacer(1, 6))
                                successful_images += 1
                                logger.info(f"✅ Added location {i+1}: {loc_name}")
                            else:
                                logger.warning(f"⚠️ No image for {loc.get('name')}")
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Could not add location {loc.get('name')}: {e}")
                    
                    logger.info(f"📊 Successfully added {successful_images}/{len(locs_with_images)} images")
                    
                    # Add travel tips section with blue header
                    if travel_tips:
                        story.append(Spacer(1, 8))
                        tips_header = Paragraph("<b>Travel Tips</b>",
                                               S("tips_h", fontSize=16, fontName="Helvetica-Bold",
                                                 textColor=WHITE, alignment=TA_CENTER))
                        tips_header_table = Table([[tips_header]], colWidths=[170 * mm])
                        tips_header_table.setStyle(TableStyle([
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2563EB")),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]))
                        story.append(tips_header_table)
                        story.append(Spacer(1, 6))
                        
                        for tip in travel_tips[:4]:
                            story.append(Paragraph(f"• {tip}", BODY_STYLE))
                            story.append(Spacer(1, 3))
                    
                    # Add spacing before next section
                    story.append(Spacer(1, 12))
                    logger.info("✅ Locations section added to PDF")
                else:
                    if not locations:
                        logger.info("ℹ️ No locations available for map")
                    else:
                        logger.info("ℹ️ PIL not available, skipping map page")
            except Exception as map_error:
                logger.warning(f"⚠️ Could not generate map page: {map_error}")
                # Continue without map - not critical
            
            # Budget Section
            if budget:
                story.append(Paragraph("Budget Breakdown", SECTION_HEAD))
                story.append(HRFlowable(width="100%", thickness=1, color=SAFFRON, spaceAfter=6))
                
                transport = budget.get('transport', 0)
                accommodation = budget.get('accommodation', 0)
                food = budget.get('food', 0)
                activities = budget.get('activities', 0)
                miscellaneous = budget.get('miscellaneous', 0)
                total = budget.get('total', 0)
                
                budget_data = [
                    ["Category", "Amount", "Notes"],
                    ["Transport", f"Rs. {int(transport):,}", "Local auto / cab / fuel"],
                    ["Accommodation", f"Rs. {int(accommodation):,}", "Hotel for trip duration"],
                    ["Food", f"Rs. {int(food):,}", "All meals & snacks"],
                    ["Activities", f"Rs. {int(activities):,}", "Entry fees & experiences"],
                    ["Miscellaneous", f"Rs. {int(miscellaneous):,}", "Incidentals & extras"],
                    ["TOTAL", f"Rs. {int(total):,}", "Complete trip budget"],
                ]
                
                budget_table = Table(budget_data, colWidths=[52 * mm, 35 * mm, 83 * mm])
                budget_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), DARK_NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("BACKGROUND", (0, -1), (-1, -1), SAFFRON),
                    ("TEXTCOLOR", (0, -1), (-1, -1), WHITE),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [LIGHT_BG, WHITE]),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_LINE),
                ]))
                story.append(budget_table)
                story.append(Spacer(1, 12))  # Just spacing, no page break
            
            # Day-by-day itinerary
            for day_data in days:
                day_num = day_data.get('day', 1)
                activities = day_data.get('activities', [])
                accent = DAY_COLORS.get(day_num, TEAL)
                
                # Day header
                header_p = Paragraph(f"DAY {day_num}", DAY_HEAD)
                header_tbl = Table([[header_p]], colWidths=[170 * mm])
                header_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), accent),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ]))
                story.append(header_tbl)
                story.append(Spacer(1, 4 * mm))
                
                # Activities
                for i, act in enumerate(activities):
                    bg = LIGHT_BG if i % 2 == 0 else WHITE
                    title = act.get('title', '').replace('**', '')
                    desc = act.get('description', '').replace('**', '')
                    time = act.get('time', '')
                    
                    time_p = Paragraph(time, TIME_STYLE)
                    title_p = Paragraph(title, ACT_TITLE)
                    desc_p = Paragraph(desc, ACT_DESC)
                    
                    inner = Table([[title_p], [desc_p]], colWidths=[120 * mm])
                    inner.setStyle(TableStyle([
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]))
                    
                    row = Table([[time_p, inner]], colWidths=[25 * mm, 120 * mm])
                    row.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), bg),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("LINEBELOW", (0, 0), (-1, -1), 0.3, LIGHT_LINE),
                    ]))
                    story.append(row)
                
                # Highlights strip
                top5 = " • ".join(a.get('title', '').replace('**', '') for a in activities[:5])
                hl_bg = colors.HexColor("#EFF6FF") if day_num % 2 == 1 else colors.HexColor("#ECFDF5")
                hl_bdr = TEAL if day_num % 2 == 0 else accent
                
                hl_tbl = Table([[
                    Paragraph(f"<b>Day {day_num} Highlights</b>",
                             S(f"hlh{day_num}", fontSize=9, fontName="Helvetica-Bold", textColor=DARK_NAVY)),
                    Paragraph(top5, S(f"hlb{day_num}", fontSize=9, fontName="Helvetica", textColor=MID_GREY)),
                ]], colWidths=[40 * mm, 130 * mm])
                hl_tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), hl_bg),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("BOX", (0, 0), (-1, -1), 0.5, hl_bdr),
                ]))
                story.append(Spacer(1, 6 * mm))
                story.append(hl_tbl)
                story.append(Spacer(1, 10 * mm))  # Spacing between days, no page break
            
            # Locations reference
            if locations:
                story.append(Paragraph("Key Locations Reference", SECTION_HEAD))
                story.append(HRFlowable(width="100%", thickness=1, color=SAFFRON, spaceAfter=6))
                
                header_row = [
                    Paragraph("<b>#</b>", S("lh1", fontSize=9, fontName="Helvetica-Bold",
                                          textColor=WHITE, alignment=TA_CENTER)),
                    Paragraph("<b>Location</b>", S("lh2", fontSize=9, fontName="Helvetica-Bold", textColor=WHITE)),
                    Paragraph("<b>Day</b>", S("lh3", fontSize=9, fontName="Helvetica-Bold",
                                            textColor=WHITE, alignment=TA_CENTER)),
                    Paragraph("<b>Time</b>", S("lh4", fontSize=9, fontName="Helvetica-Bold",
                                             textColor=WHITE, alignment=TA_CENTER)),
                    Paragraph("<b>Open in Map</b>", S("lh5", fontSize=9, fontName="Helvetica-Bold",
                                                      textColor=WHITE, alignment=TA_CENTER)),
                ]
                
                loc_data = [header_row]
                for i, loc in enumerate(locations, 1):
                    day_num = loc.get('day', 1)
                    time = loc.get('time', '')
                    name = loc.get('name', '')
                    lat = loc.get('latitude', 0)
                    lon = loc.get('longitude', 0)
                    day_color = DAY_COLORS.get(day_num, TEAL)
                    
                    # Create Google Maps link
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                    link_p = Paragraph(
                        f'<link href="{maps_url}"><u>📍 View on Map</u></link>',
                        S(f"ml{i}", fontSize=8, fontName="Helvetica",
                          textColor=colors.HexColor("#1D6FB8"), alignment=TA_CENTER)
                    )
                    
                    loc_data.append([
                        Paragraph(str(i), S(f"ln{i}", fontSize=8, fontName="Helvetica",
                                          textColor=MID_GREY, alignment=TA_CENTER)),
                        Paragraph(name, S(f"lname{i}", fontSize=8, fontName="Helvetica", textColor=DARK_NAVY)),
                        Paragraph(f"Day {day_num}", S(f"lday{i}", fontSize=8, fontName="Helvetica-Bold",
                                                      textColor=day_color, alignment=TA_CENTER)),
                        Paragraph(time, S(f"ltime{i}", fontSize=8, fontName="Helvetica",
                                        textColor=MID_GREY, alignment=TA_CENTER)),
                        link_p,
                    ])
                
                loc_table = Table(loc_data, colWidths=[8 * mm, 65 * mm, 18 * mm, 22 * mm, 57 * mm])
                loc_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), DARK_NAVY),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, WHITE]),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 0), (2, -1), "CENTER"),
                    ("ALIGN", (3, 0), (3, -1), "CENTER"),
                    ("ALIGN", (4, 0), (4, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.3, LIGHT_LINE),
                ]))
                story.append(loc_table)
            
            # Build PDF
            doc.build(story,
                     onFirstPage=make_first_page_cb(),
                     onLaterPages=make_later_pages_cb())
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
            
        except ImportError:
            logger.error("❌ reportlab not installed. Install with: pip install reportlab")
            raise ImportError("reportlab is required for PDF generation. Install with: pip install reportlab")
    
    def _save_pdf(self, filepath: Path, content: bytes):
        """Save PDF content to file, creating directory if needed"""
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(content)
    
    def _save_metadata(self, pdf_filepath: Path, plan_data: Dict[str, Any], session_id: str = None):
        """
        Save plan metadata as JSON file alongside PDF
        
        Filename: {pdf_name}_metadata.json
        """
        metadata_filepath = pdf_filepath.with_suffix('.json')
        
        metadata = {
            'pdf_file': pdf_filepath.name,
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'plan_data': plan_data
        }
        
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Metadata saved: {metadata_filepath.name}")
    
    def list_plans(self) -> list:
        """
        List all saved travel plans
        
        Returns:
            List of dictionaries with plan information
        """
        plans = []
        
        for pdf_file in self.base_dir.glob("*.pdf"):
            metadata_file = pdf_file.with_suffix('.json')
            
            plan_info = {
                'filename': pdf_file.name,
                'filepath': str(pdf_file.absolute()),
                'size_kb': round(pdf_file.stat().st_size / 1024, 2),
                'created_at': datetime.fromtimestamp(pdf_file.stat().st_mtime).isoformat()
            }
            
            # Load metadata if exists
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    plan_info['metadata'] = metadata
            
            plans.append(plan_info)
        
        return plans
    
    def get_plan(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get plan data by filename
        
        Args:
            filename: PDF filename
        
        Returns:
            Plan metadata or None if not found
        """
        pdf_path = self.base_dir / filename
        metadata_path = pdf_path.with_suffix('.json')
        
        if not pdf_path.exists():
            return None
        
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'filename': filename,
            'filepath': str(pdf_path.absolute())
        }


# Convenience functions
def save_travel_plan_pdf(destination: str, duration_days: int, plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to save travel plan as PDF
    
    Args:
        destination: Destination name
        duration_days: Trip duration
        plan_data: Complete plan data
    
    Returns:
        Result dictionary with success status and file info
    """
    fs = FilesystemAPI()
    return fs.save_plan_as_pdf(destination, duration_days, plan_data)


def list_all_plans() -> list:
    """
    Convenience function to list all saved plans
    
    Returns:
        List of plan information dictionaries
    """
    fs = FilesystemAPI()
    return fs.list_plans()
