/**
 * Client-Side PDF Generator - Matches Exact Template Design
 * Generates PDFs matching the filesystem_mcp_service template
 */

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export async function generateTripPDF(tripData) {
  try {
    console.log('📄 Starting PDF generation with data:', tripData);
    
    const container = document.createElement('div');
    container.style.position = 'absolute';
    container.style.left = '-9999px';
    container.style.width = '210mm';
    container.style.background = 'white';
    document.body.appendChild(container);

    container.innerHTML = generatePDFHTML(tripData);
    
    // Wait for ALL images to load with longer timeout
    console.log('🖼️ Waiting for images to load...');
    await waitForImages(container, 10000); // 10 second timeout
    console.log('✅ All images loaded');
    
    // Add extra delay to ensure rendering is complete
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('✅ Rendering delay complete');

    const pdf = new jsPDF('p', 'mm', 'a4');
    const pages = container.querySelectorAll('.pdf-page');
    
    console.log(`📄 Rendering ${pages.length} pages...`);
    
    for (let i = 0; i < pages.length; i++) {
      if (i > 0) pdf.addPage();
      
      console.log(`📄 Rendering page ${i + 1}/${pages.length}...`);
      
      const canvas = await html2canvas(pages[i], {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        backgroundColor: '#ffffff',
        logging: false,
        imageTimeout: 15000 // 15 second timeout for images
      });

      const imgData = canvas.toDataURL('image/png');
      pdf.addImage(imgData, 'PNG', 0, 0, 210, 297);
      
      console.log(`✅ Page ${i + 1} rendered`);
    }

    document.body.removeChild(container);

    // FIX: Use underscores instead of hyphens to match naming convention
    // e.g. 3_day_plan_to_mumbai.pdf
    const destination = tripData.destination || 'trip';
    const duration = tripData.duration_days || 1;
    const filename = `${duration}_day_plan_to_${destination.replace(/\s+/g, '_').toLowerCase()}.pdf`;
    
    console.log(`✅ PDF generated: ${filename}`);
    pdf.save(filename);

    return { success: true, filename };
  } catch (error) {
    console.error('❌ PDF generation error:', error);
    return { success: false, error: error.message };
  }
}

function generatePDFHTML(tripData) {
  // Extract data with proper defaults
  const destination = tripData.destination || 'Unknown';
  const duration_days = tripData.duration_days || 0;
  const budget = tripData.budget || {};
  const itinerary = tripData.itinerary || {};
  const map = tripData.map || {};
  const locations = map.locations || [];
  const days = itinerary.days || [];
  
  const total_budget = budget.total || 0;
  const transport = budget.transport || 0;
  const accommodation = budget.accommodation || 0;
  const food = budget.food || 0;
  const activities = budget.activities || 0;
  const miscellaneous = budget.miscellaneous || 0;

  console.log('📊 PDF Data:', {
    destination,
    duration_days,
    total_budget,
    days: days.length,
    locations: locations.length
  });

  // Color palette
  const COLORS = {
    darkNavy: '#1A2C4E',
    saffron: '#E87722',
    teal: '#2E8B8B',
    lightBg: '#FFF8F2',
    midGrey: '#6B7280',
    white: '#FFFFFF',
    lightLine: '#E5E7EB'
  };

  const DAY_COLORS = {
    1: COLORS.saffron,
    2: COLORS.teal,
    3: '#16A34A',
    4: '#9333EA'
  };

  const currentDate = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  return `
    <!-- Page 1: Cover & Locations -->
    <div class="pdf-page" style="width: 210mm; height: 297mm; position: relative; font-family: Arial, Helvetica, sans-serif; background: white; padding: 0; margin: 0; box-sizing: border-box;">
      <!-- Dark Navy Header -->
      <div style="background: ${COLORS.darkNavy}; height: 115mm; position: relative;">
        <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 4px; background: ${COLORS.saffron};"></div>
        
        <!-- Title -->
        <div style="text-align: center; padding-top: 38mm;">
          <h1 style="color: ${COLORS.white}; font-size: 26px; font-weight: bold; margin: 0;">${destination} Travel Plan</h1>
          <p style="color: #FFD8A8; font-size: 13px; margin: 14mm 0 0 0;">${destination} • Rs. ${Math.round(total_budget).toLocaleString()} Total Budget</p>
          <p style="color: ${COLORS.white}; font-size: 11px; font-style: italic; margin: 11mm 0 0 0; opacity: 0.9;">AI-Powered Travel Planning</p>
        </div>

        <!-- Stat Pills -->
        <div style="display: flex; justify-content: center; gap: 6mm; margin-top: 18mm;">
          <div style="background: #243A5E; border-radius: 4px; padding: 10mm 18mm; text-align: center; min-width: 36mm;">
            <div style="color: ${COLORS.saffron}; font-size: 15px; font-weight: bold; margin-bottom: 6mm;">${duration_days} Days</div>
            <div style="color: #9CA3AF; font-size: 8px;">Duration</div>
          </div>
          <div style="background: #243A5E; border-radius: 4px; padding: 10mm 18mm; text-align: center; min-width: 36mm;">
            <div style="color: ${COLORS.saffron}; font-size: 15px; font-weight: bold; margin-bottom: 6mm;">Rs. ${Math.round(total_budget).toLocaleString()}</div>
            <div style="color: #9CA3AF; font-size: 8px;">Budget</div>
          </div>
          <div style="background: #243A5E; border-radius: 4px; padding: 10mm 18mm; text-align: center; min-width: 36mm;">
            <div style="color: ${COLORS.saffron}; font-size: 15px; font-weight: bold; margin-bottom: 6mm;">${locations.length} Spots</div>
            <div style="color: #9CA3AF; font-size: 8px;">Locations</div>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <div style="padding: 20mm;">
        <!-- Destination Header -->
        <div style="background: ${COLORS.saffron}; padding: 12mm; text-align: center; margin: -20mm -20mm 8mm -20mm;">
          <h2 style="color: ${COLORS.white}; font-size: 24px; font-weight: bold; margin: 0;">${destination.toUpperCase()}</h2>
          <p style="color: #FFE4B5; font-size: 12px; margin: 5px 0 0 0;">Explore the beauty and culture of ${destination}</p>
        </div>

        ${locations.filter(loc => loc.image).slice(0, 8).map((loc, i) => {
          const isLeft = i % 2 === 0;
          return `
            <div style="background: #E0F2FE; border: 1px solid #7DD3FC; padding: 8mm; margin-bottom: 6mm; display: flex; ${isLeft ? 'flex-direction: row' : 'flex-direction: row-reverse'}; gap: 8mm; align-items: flex-start;">
              <div style="flex-shrink: 0;">
                <img src="${loc.image}" alt="${loc.name}" style="width: 70mm; height: auto; max-height: 50mm; object-fit: cover; border-radius: 4px;" crossorigin="anonymous" onerror="this.style.display='none'" />
              </div>
              <div style="flex: 1;">
                <h3 style="color: ${COLORS.darkNavy}; font-size: 11px; font-weight: bold; margin: 0 0 4mm 0;">${loc.name}</h3>
                <p style="color: ${COLORS.midGrey}; font-size: 9px; line-height: 1.5; margin: 0;">${(loc.extract || loc.description || '').substring(0, 200)}</p>
              </div>
            </div>
          `;
        }).join('')}

        <!-- Travel Tips -->
        <div style="background: #2563EB; padding: 8mm; text-align: center; margin: 8mm 0;">
          <h2 style="color: ${COLORS.white}; font-size: 16px; font-weight: bold; margin: 0;">Travel Tips</h2>
        </div>
        <div style="padding: 6mm 0;">
          <p style="color: ${COLORS.darkNavy}; font-size: 9px; margin: 3mm 0; padding-left: 5mm;">• Use local trains and metro for faster city travel, but avoid rush hours.</p>
          <p style="color: ${COLORS.darkNavy}; font-size: 9px; margin: 3mm 0; padding-left: 5mm;">• Dress modestly and carry a scarf or shawl for temple visits.</p>
          <p style="color: ${COLORS.darkNavy}; font-size: 9px; margin: 3mm 0; padding-left: 5mm;">• Keep cash and small change handy; not all vendors accept cards.</p>
          <p style="color: ${COLORS.darkNavy}; font-size: 9px; margin: 3mm 0; padding-left: 5mm;">• Try local street food at busy stalls for freshness and authenticity.</p>
        </div>
      </div>

      <!-- Footer -->
      <div style="position: absolute; bottom: 0; left: 0; right: 0; background: ${COLORS.lightLine}; padding: 3.5mm; text-align: center;">
        <p style="color: ${COLORS.midGrey}; font-size: 7px; margin: 0;">${destination} • Budget: Rs. ${Math.round(total_budget).toLocaleString()} • ${currentDate}</p>
      </div>
    </div>

    <!-- Page 2: Budget & Itinerary -->
    <div class="pdf-page" style="width: 210mm; height: 297mm; position: relative; font-family: Arial, Helvetica, sans-serif; background: white; padding: 0; margin: 0; box-sizing: border-box;">
      <!-- Top Bar -->
      <div style="background: ${COLORS.darkNavy}; height: 18mm; position: relative;">
        <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: ${COLORS.saffron};"></div>
        <div style="padding: 12mm 20mm 0 20mm; display: flex; justify-content: space-between;">
          <span style="color: ${COLORS.white}; font-size: 9px; font-weight: bold;">${destination} Travel Plan</span>
          <span style="color: ${COLORS.white}; font-size: 9px;">Page 2</span>
        </div>
      </div>

      <!-- Content -->
      <div style="padding: 20mm;">
        <!-- Budget Breakdown -->
        <h2 style="color: ${COLORS.darkNavy}; font-size: 16px; font-weight: bold; border-bottom: 2px solid ${COLORS.saffron}; padding-bottom: 10px; margin-bottom: 15px;">Budget Breakdown</h2>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid ${COLORS.lightLine};">
          <thead>
            <tr style="background: ${COLORS.darkNavy};">
              <th style="color: ${COLORS.white}; padding: 12px; text-align: left; font-size: 10px; font-weight: bold;">Category</th>
              <th style="color: ${COLORS.white}; padding: 12px; text-align: center; font-size: 10px; font-weight: bold;">Amount</th>
              <th style="color: ${COLORS.white}; padding: 12px; text-align: left; font-size: 10px; font-weight: bold;">Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr style="background: ${COLORS.lightBg};">
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Transport</td>
              <td style="padding: 10px; text-align: center; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Rs. ${Math.round(transport).toLocaleString()}</td>
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Local auto / cab / fuel</td>
            </tr>
            <tr style="background: ${COLORS.white};">
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Accommodation</td>
              <td style="padding: 10px; text-align: center; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Rs. ${Math.round(accommodation).toLocaleString()}</td>
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Hotel for trip duration</td>
            </tr>
            <tr style="background: ${COLORS.lightBg};">
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Food</td>
              <td style="padding: 10px; text-align: center; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Rs. ${Math.round(food).toLocaleString()}</td>
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">All meals & snacks</td>
            </tr>
            <tr style="background: ${COLORS.white};">
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Activities</td>
              <td style="padding: 10px; text-align: center; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Rs. ${Math.round(activities).toLocaleString()}</td>
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Entry fees & experiences</td>
            </tr>
            <tr style="background: ${COLORS.lightBg};">
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Miscellaneous</td>
              <td style="padding: 10px; text-align: center; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Rs. ${Math.round(miscellaneous).toLocaleString()}</td>
              <td style="padding: 10px; font-size: 9px; border-bottom: 0.3px solid ${COLORS.lightLine};">Incidentals & extras</td>
            </tr>
            <tr style="background: ${COLORS.saffron};">
              <td style="color: ${COLORS.white}; padding: 15px; font-size: 10px; font-weight: bold;">TOTAL</td>
              <td style="color: ${COLORS.white}; padding: 15px; text-align: center; font-size: 10px; font-weight: bold;">Rs. ${Math.round(total_budget).toLocaleString()}</td>
              <td style="color: ${COLORS.white}; padding: 15px; font-size: 10px; font-weight: bold;">Complete trip budget</td>
            </tr>
          </tbody>
        </table>

        ${days.map((day, dayIdx) => {
          const dayColor = DAY_COLORS[day.day] || COLORS.teal;
          const dayActivities = day.activities || [];
          
          return `
            <div style="margin-top: 20mm;">
              <!-- Day Header -->
              <div style="background: ${dayColor}; padding: 15px; text-align: center; margin-bottom: 4mm;">
                <h3 style="color: ${COLORS.white}; font-size: 18px; font-weight: bold; margin: 0;">DAY ${day.day}</h3>
              </div>

              ${dayActivities.slice(0, 8).map((act, actIdx) => {
                const bg = actIdx % 2 === 0 ? COLORS.lightBg : COLORS.white;
                const title = (act.title || '').replace(/\*\*/g, '');
                const desc = (act.description || '').replace(/\*\*/g, '');
                const time = act.time || '';
                
                return `
                  <div style="background: ${bg}; padding: 4mm 6mm; border-bottom: 0.3px solid ${COLORS.lightLine}; display: flex; gap: 6mm;">
                    <div style="flex-shrink: 0; width: 25mm;">
                      <span style="color: ${COLORS.saffron}; font-size: 9px; font-weight: bold;">${time}</span>
                    </div>
                    <div style="flex: 1;">
                      <div style="color: ${COLORS.darkNavy}; font-size: 11px; font-weight: bold; margin-bottom: 1mm;">${title}</div>
                      <div style="color: ${COLORS.midGrey}; font-size: 9px; line-height: 1.4;">${desc}</div>
                    </div>
                  </div>
                `;
              }).join('')}

              ${dayActivities.length > 0 ? `
                <div style="background: ${day.day % 2 === 1 ? '#EFF6FF' : '#ECFDF5'}; border: 0.5px solid ${day.day % 2 === 0 ? COLORS.teal : dayColor}; padding: 6mm 8mm; margin-top: 6mm; display: flex; gap: 8mm;">
                  <div style="flex-shrink: 0;">
                    <span style="color: ${COLORS.darkNavy}; font-size: 9px; font-weight: bold;">Day ${day.day} Highlights</span>
                  </div>
                  <div style="flex: 1;">
                    <span style="color: ${COLORS.midGrey}; font-size: 9px;">${dayActivities.slice(0, 5).map(a => (a.title || '').replace(/\*\*/g, '')).join(' • ')}</span>
                  </div>
                </div>
              ` : ''}
            </div>
          `;
        }).join('')}
      </div>

      <!-- Footer -->
      <div style="position: absolute; bottom: 0; left: 0; right: 0; background: ${COLORS.lightLine}; padding: 3.5mm; text-align: center;">
        <p style="color: ${COLORS.midGrey}; font-size: 7px; margin: 0;">${destination} • Budget: Rs. ${Math.round(total_budget).toLocaleString()} • ${currentDate}</p>
      </div>
    </div>

    <!-- Page 3: Key Locations Reference -->
    <div class="pdf-page" style="width: 210mm; height: 297mm; position: relative; font-family: Arial, Helvetica, sans-serif; background: white; padding: 0; margin: 0; box-sizing: border-box;">
      <!-- Top Bar -->
      <div style="background: ${COLORS.darkNavy}; height: 18mm; position: relative;">
        <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: ${COLORS.saffron};"></div>
        <div style="padding: 12mm 20mm 0 20mm; display: flex; justify-content: space-between;">
          <span style="color: ${COLORS.white}; font-size: 9px; font-weight: bold;">${destination} Travel Plan</span>
          <span style="color: ${COLORS.white}; font-size: 9px;">Page 3</span>
        </div>
      </div>

      <!-- Content -->
      <div style="padding: 20mm;">
        <h2 style="color: ${COLORS.darkNavy}; font-size: 16px; font-weight: bold; border-bottom: 2px solid ${COLORS.saffron}; padding-bottom: 10px; margin-bottom: 15px;">Key Locations Reference</h2>
        
        <table style="width: 100%; border-collapse: collapse; border: 1px solid ${COLORS.lightLine};">
          <thead>
            <tr style="background: ${COLORS.darkNavy};">
              <th style="color: ${COLORS.white}; padding: 12px; text-align: center; font-size: 9px; font-weight: bold;">#</th>
              <th style="color: ${COLORS.white}; padding: 12px; text-align: left; font-size: 9px; font-weight: bold;">Location</th>
              <th style="color: ${COLORS.white}; padding: 12px; text-align: center; font-size: 9px; font-weight: bold;">Day</th>
              <th style="color: ${COLORS.white}; padding: 12px; text-align: center; font-size: 9px; font-weight: bold;">Time</th>
              <th style="color: ${COLORS.white}; padding: 12px; text-align: center; font-size: 9px; font-weight: bold;">Open in Map</th>
            </tr>
          </thead>
          <tbody>
            ${locations.map((loc, i) => {
              const dayNum = loc.day || 1;
              const dayColor = DAY_COLORS[dayNum] || COLORS.teal;
              const bg = i % 2 === 0 ? COLORS.lightBg : COLORS.white;
              const lat = loc.latitude || 0;
              const lon = loc.longitude || 0;
              const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
              
              return `
                <tr style="background: ${bg};">
                  <td style="padding: 10px; text-align: center; font-size: 8px; color: ${COLORS.midGrey}; border-bottom: 0.3px solid ${COLORS.lightLine};">${i + 1}</td>
                  <td style="padding: 10px; font-size: 8px; color: ${COLORS.darkNavy}; border-bottom: 0.3px solid ${COLORS.lightLine};">${loc.name || ''}</td>
                  <td style="padding: 10px; text-align: center; font-size: 8px; color: ${dayColor}; font-weight: bold; border-bottom: 0.3px solid ${COLORS.lightLine};">Day ${dayNum}</td>
                  <td style="padding: 10px; text-align: center; font-size: 8px; color: ${COLORS.midGrey}; border-bottom: 0.3px solid ${COLORS.lightLine};">${loc.time || ''}</td>
                  <td style="padding: 10px; text-align: center; font-size: 8px; border-bottom: 0.3px solid ${COLORS.lightLine};">
                    <a href="${mapsUrl}" style="color: #1D6FB8; text-decoration: underline;">📍 View on Map</a>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>

      <!-- Footer -->
      <div style="position: absolute; bottom: 0; left: 0; right: 0; background: ${COLORS.lightLine}; padding: 3.5mm; text-align: center;">
        <p style="color: ${COLORS.midGrey}; font-size: 7px; margin: 0;">${destination} • Budget: Rs. ${Math.round(total_budget).toLocaleString()} • ${currentDate}</p>
      </div>
    </div>
  `;
}

function waitForImages(container, timeout = 10000) {
  const images = container.getElementsByTagName('img');
  const promises = [];

  console.log(`🖼️ Found ${images.length} images to load`);

  for (let img of images) {
    if (!img.complete) {
      promises.push(
        new Promise((resolve) => {
          const timer = setTimeout(() => {
            console.log(`⏱️ Image timeout: ${img.src.substring(0, 50)}...`);
            resolve();
          }, timeout);
          
          img.onload = () => {
            clearTimeout(timer);
            console.log(`✅ Image loaded: ${img.src.substring(0, 50)}...`);
            resolve();
          };
          
          img.onerror = () => {
            clearTimeout(timer);
            console.log(`❌ Image failed: ${img.src.substring(0, 50)}...`);
            resolve();
          };
        })
      );
    } else {
      console.log(`✅ Image already loaded: ${img.src.substring(0, 50)}...`);
    }
  }

  return Promise.all(promises);
}