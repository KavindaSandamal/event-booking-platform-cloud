import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export const generateTicketPDF = async (booking, event, receipt = null) => {
    // Create a temporary div for the ticket content
    const ticketDiv = document.createElement('div');
    ticketDiv.style.position = 'absolute';
    ticketDiv.style.left = '-9999px';
    ticketDiv.style.top = '0';
    ticketDiv.style.width = '800px';
    ticketDiv.style.height = '600px';
    ticketDiv.style.backgroundColor = 'white';
    ticketDiv.style.padding = '40px';
    ticketDiv.style.fontFamily = 'Arial, sans-serif';
    ticketDiv.style.boxSizing = 'border-box';
    
    // Generate ticket content
    ticketDiv.innerHTML = `
        <div style="
            border: 3px solid #2c3e50;
            border-radius: 15px;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            position: relative;
            overflow: hidden;
        ">
            <!-- Background Pattern -->
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-image: 
                    radial-gradient(circle at 20% 80%, rgba(255,255,255,0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(255,255,255,0.1) 0%, transparent 50%);
                pointer-events: none;
            "></div>
            
            <!-- Header -->
            <div style="position: relative; z-index: 1;">
                <h1 style="
                    margin: 0 0 10px 0;
                    font-size: 36px;
                    font-weight: bold;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                ">🎫 EVENT TICKET</h1>
                
                <div style="
                    width: 100px;
                    height: 4px;
                    background: #f39c12;
                    margin: 0 auto 20px auto;
                    border-radius: 2px;
                "></div>
            </div>
            
            <!-- Event Details -->
            <div style="
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 25px;
                margin: 20px 0;
                backdrop-filter: blur(10px);
                position: relative;
                z-index: 1;
            ">
                <h2 style="
                    margin: 0 0 15px 0;
                    font-size: 28px;
                    color: #f39c12;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                ">${event.title}</h2>
                
                <div style="
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    text-align: left;
                    margin: 20px 0;
                ">
                    <div>
                        <strong style="color: #f39c12;">📍 Venue:</strong><br>
                        <span>${event.venue || 'TBD'}</span>
                    </div>
                    <div>
                        <strong style="color: #f39c12;">🎭 Seats:</strong><br>
                        <span>${booking.seats} seat(s)</span>
                    </div>
                    <div>
                        <strong style="color: #f39c12;">📅 Booked On:</strong><br>
                        <span>${new Date(booking.created_at).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        })}</span>
                    </div>
                    <div>
                        <strong style="color: #f39c12;">🆔 Booking ID:</strong><br>
                        <span style="font-family: monospace; font-size: 12px;">${booking.id}</span>
                    </div>
                </div>
                
                ${event.description ? `
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);">
                        <strong style="color: #f39c12;">📝 Description:</strong><br>
                        <span>${event.description}</span>
                    </div>
                ` : ''}
            </div>
            
            <!-- Payment Information -->
            ${receipt ? `
                <div style="
                    background: rgba(46, 204, 113, 0.2);
                    border: 2px solid #2ecc71;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                    position: relative;
                    z-index: 1;
                ">
                    <h3 style="
                        margin: 0 0 10px 0;
                        color: #2ecc71;
                        font-size: 20px;
                    ">💳 Payment Confirmed</h3>
                    <div style="
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 15px;
                        text-align: left;
                    ">
                        <div>
                            <strong style="color: #2ecc71;">💰 Amount:</strong><br>
                            <span>$${receipt.amount}</span>
                        </div>
                        <div>
                            <strong style="color: #2ecc71;">📱 Phone:</strong><br>
                            <span>${receipt.phone_number}</span>
                        </div>
                        <div>
                            <strong style="color: #2ecc71;">🆔 Payment ID:</strong><br>
                            <span style="font-family: monospace; font-size: 11px;">${receipt.payment_id}</span>
                        </div>
                        <div>
                            <strong style="color: #2ecc71;">📅 Paid On:</strong><br>
                            <span>${new Date(receipt.created_at).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            })}</span>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            <!-- Footer -->
            <div style="
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid rgba(255,255,255,0.3);
                position: relative;
                z-index: 1;
            ">
                <p style="
                    margin: 0;
                    font-size: 14px;
                    opacity: 0.8;
                ">🎉 Thank you for your booking! 🎉</p>
                <p style="
                    margin: 5px 0 0 0;
                    font-size: 12px;
                    opacity: 0.6;
                ">Event Booking Platform - Secure & Reliable</p>
            </div>
        </div>
    `;
    
    // Add to document temporarily
    document.body.appendChild(ticketDiv);
    
    try {
        // Convert to canvas
        const canvas = await html2canvas(ticketDiv, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff'
        });
        
        // Remove temporary div
        document.body.removeChild(ticketDiv);
        
        // Create PDF
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF('p', 'mm', 'a4');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = pdf.internal.pageSize.getHeight();
        
        // Calculate dimensions to fit the ticket properly
        const imgWidth = 190; // mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        
        // Center the image on the page
        const x = (pdfWidth - imgWidth) / 2;
        const y = (pdfHeight - imgHeight) / 2;
        
        pdf.addImage(imgData, 'PNG', x, y, imgWidth, imgHeight);
        
        // Generate filename
        const eventName = event.title.replace(/[^a-zA-Z0-9]/g, '-');
        const filename = `ticket-${eventName}-${booking.id}.pdf`;
        
        // Download PDF
        pdf.save(filename);
        
        return filename;
    } catch (error) {
        // Remove temporary div in case of error
        if (document.body.contains(ticketDiv)) {
            document.body.removeChild(ticketDiv);
        }
        console.error('Error generating PDF:', error);
        throw error;
    }
};

export const generateReceiptPDF = async (receipt, booking, event) => {
    const receiptDiv = document.createElement('div');
    receiptDiv.style.position = 'absolute';
    receiptDiv.style.left = '-9999px';
    receiptDiv.style.top = '0';
    receiptDiv.style.width = '800px';
    receiptDiv.style.height = '600px';
    receiptDiv.style.backgroundColor = 'white';
    receiptDiv.style.padding = '40px';
    receiptDiv.style.fontFamily = 'Arial, sans-serif';
    receiptDiv.style.boxSizing = 'border-box';
    
    receiptDiv.innerHTML = `
        <div style="
            border: 2px solid #34495e;
            border-radius: 10px;
            padding: 30px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
        ">
            <h1 style="
                margin: 0 0 20px 0;
                font-size: 32px;
                text-align: center;
                color: #ecf0f1;
            ">🧾 PAYMENT RECEIPT</h1>
            
            <div style="
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            ">
                <h2 style="margin: 0 0 15px 0; color: #f39c12;">Event: ${event.title}</h2>
                
                <div style="
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin: 15px 0;
                ">
                    <div><strong>Payment ID:</strong><br>${receipt.payment_id}</div>
                    <div><strong>Amount:</strong><br>$${receipt.amount}</div>
                    <div><strong>Phone:</strong><br>${receipt.phone_number}</div>
                    <div><strong>Status:</strong><br>${receipt.status}</div>
                    <div><strong>Date:</strong><br>${new Date(receipt.created_at).toLocaleString()}</div>
                    <div><strong>Booking ID:</strong><br>${booking.id}</div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; opacity: 0.8;">
                <p>Thank you for your payment!</p>
                <p style="font-size: 12px;">Event Booking Platform</p>
            </div>
        </div>
    `;
    
    document.body.appendChild(receiptDiv);
    
    try {
        const canvas = await html2canvas(receiptDiv, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff'
        });
        
        document.body.removeChild(receiptDiv);
        
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF('p', 'mm', 'a4');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = pdf.internal.pageSize.getHeight();
        
        const imgWidth = 190;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        
        const x = (pdfWidth - imgWidth) / 2;
        const y = (pdfHeight - imgHeight) / 2;
        
        pdf.addImage(imgData, 'PNG', x, y, imgWidth, imgHeight);
        
        const filename = `receipt-${receipt.payment_id}.pdf`;
        pdf.save(filename);
        
        return filename;
    } catch (error) {
        if (document.body.contains(receiptDiv)) {
            document.body.removeChild(receiptDiv);
        }
        console.error('Error generating receipt PDF:', error);
        throw error;
    }
};
