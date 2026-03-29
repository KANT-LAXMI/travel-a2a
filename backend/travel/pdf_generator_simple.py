"""
Simple PDF Generator using HTML to PDF conversion
Works on Vercel without heavy dependencies
"""
import logging
import os
import requests
from typing import Dict, Optional
from datetime import datetime
import base64

logger = logging.getLogger(__name__)


def generate_pdf_html(plan_data: Dict) -> str:
    """Generate HTML for PDF conversion"""
    
    destination = plan_data.get('destination', 'Unknown')
    duration = plan_data.get('duration_days', 0)
    budget = plan_data.get('budget', {})
    itinerary = plan_data.get('itinerary', {})
    locations = plan_data.get('map', {}).get('locations', [])
    
    # Get location images
    location_images = []
    for loc in locations[:10]:  # Limit to 10 images
        if loc.get('image'):
            location_images.append({
                'name': loc.get('name', ''),
                'image': loc.get('image', ''),
                'description': loc.get('extract', '')[:200] if loc.get('extract') else ''
            })
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 20mm; }}
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; margin: -20mm -20mm 20px -20mm; }}
            .header h1 {{ margin: 0; font-size: 32px; }}
            .header p {{ margin: 10px 0 0 0; font-size: 16px; opacity: 0.9; }}
            .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
            .stat {{ text-align: center; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
            .stat-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
            .section {{ margin: 30px 0; page-break-inside: avoid; }}
            .section-title {{ font-size: 20px; color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
            .day-header {{ background: #764ba2; color: white; padding: 15px; margin: 20px 0 10px 0; border-radius: 5px; font-size: 18px; font-weight: bold; }}
            .activity {{ margin: 10px 0; padding: 10px; background: #f5f5f5; border-left: 4px solid #667eea; }}
            .activity-time {{ color: #667eea; font-weight: bold; }}
            .location-card {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; page-break-inside: avoid; }}
            .location-card img {{ width: 100%; max-height: 300px; object-fit: cover; border-radius: 5px; margin: 10px 0; }}
            .location-name {{ font-size: 18px; font-weight: bold; color: #667eea; margin-bottom: 10px; }}
            .location-desc {{ color: #666; font-size: 14px; line-height: 1.5; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{destination} Travel Plan</h1>
            <p>{duration} Days • ₹{budget.get('total', 0):,.0f} Budget • AI-Powered Planning</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{duration}</div>
                <div class="stat-label">Days</div>
            </div>
            <div class="stat">
                <div class="stat-value">₹{budget.get('total', 0):,.0f}</div>
                <div class="stat-label">Total Budget</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(locations)}</div>
                <div class="stat-label">Locations</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">💰 Budget Breakdown</div>
            <table>
                <tr>
                    <th>Category</th>
                    <th>Amount</th>
                </tr>
                <tr><td>Transport</td><td>₹{budget.get('transport', 0):,.0f}</td></tr>
                <tr><td>Accommodation</td><td>₹{budget.get('accommodation', 0):,.0f}</td></tr>
                <tr><td>Food</td><td>₹{budget.get('food', 0):,.0f}</td></tr>
                <tr><td>Activities</td><td>₹{budget.get('activities', 0):,.0f}</td></tr>
                <tr><td>Miscellaneous</td><td>₹{budget.get('miscellaneous', 0):,.0f}</td></tr>
                <tr style="background: #667eea; color: white; font-weight: bold;">
                    <td>TOTAL</td><td>₹{budget.get('total', 0):,.0f}</td>
                </tr>
            </table>
        </div>
    """
    
    # Add itinerary
    if itinerary.get('days'):
        html += '<div class="section"><div class="section-title">📅 Day-by-Day Itinerary</div>'
        for day in itinerary['days']:
            html += f'<div class="day-header">Day {day["day"]}</div>'
            for activity in day.get('activities', [])[:8]:  # Limit activities
                html += f'''
                <div class="activity">
                    <span class="activity-time">{activity.get('time', '')}</span> - 
                    <strong>{activity.get('location', {}).get('name', activity.get('title', ''))}</strong>
                    <div style="color: #666; font-size: 14px; margin-top: 5px;">{activity.get('description', '')[:150]}</div>
                </div>
                '''
        html += '</div>'
    
    # Add location images
    if location_images:
        html += '<div class="section"><div class="section-title">📸 Featured Locations</div>'
        for loc in location_images:
            html += f'''
            <div class="location-card">
                <div class="location-name">{loc['name']}</div>
                <img src="{loc['image']}" alt="{loc['name']}" onerror="this.style.display='none'">
                <div class="location-desc">{loc['description']}</div>
            </div>
            '''
        html += '</div>'
    
    html += '''
        <div style="text-align: center; margin-top: 50px; color: #999; font-size: 12px;">
            Generated by Anywhere App • AI-Powered Travel Planning
        </div>
    </body>
    </html>
    '''
    
    return html


def generate_and_upload_pdf(plan_data: Dict, query: str) -> Optional[str]:
    """Generate PDF and upload to Vercel Blob - using PDFShift API"""
    try:
        # Generate HTML
        html_content = generate_pdf_html(plan_data)
        
        # Use PDFShift API (has free tier)
        api_key = "api_YourPDFShiftAPIKey"  # You'll need to get this from pdfshift.io
        
        # For now, just upload the HTML to Blob as a viewable file
        blob_token = os.getenv('BLOB_READ_WRITE_TOKEN')
        if not blob_token:
            logger.warning("BLOB_READ_WRITE_TOKEN not set")
            return None
        
        # Generate filename
        destination = plan_data.get('destination', 'trip').replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{plan_data.get('duration_days', 0)}_day_plan_to_{destination}_{timestamp}.html"
        
        # Upload HTML to Vercel Blob (can be viewed in browser and printed as PDF)
        upload_url = f"https://blob.vercel-storage.com/{filename}"
        headers = {
            'Authorization': f'Bearer {blob_token}',
            'x-content-type': 'text/html'
        }
        
        upload_response = requests.put(upload_url, data=html_content.encode('utf-8'), headers=headers, timeout=30)
        
        if upload_response.status_code == 200:
            blob_url = upload_response.json().get('url')
            logger.info(f"✅ HTML uploaded to Vercel Blob: {blob_url}")
            return blob_url
        else:
            logger.error(f"Failed to upload HTML: {upload_response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        return None
