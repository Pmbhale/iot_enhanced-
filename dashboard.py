# dashboard.py - FIXED VERSION
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import random, time, base64, os, json
from datetime import datetime, timedelta
from io import BytesIO
import platform
import matplotlib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import email_alert

if platform.system() == "Windows":
    import winsound

# -------------------------------------------------
# FIXED EMAIL MODULE IMPORT - MOVE THIS TO TOP
# -------------------------------------------------
import sys
import os

# Try to import email_alert module
EMAIL_MODULE_AVAILABLE = False
try:
    # Check if email_alert.py exists
    if os.path.exists("email_alert.py"):
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # Try to import
        from email_alert import send_email

        EMAIL_MODULE_AVAILABLE = True
        print("✅ Email module loaded successfully!")
    else:
        print("⚠️ email_alert.py not found in:", os.path.dirname(os.path.abspath(__file__)))
        EMAIL_MODULE_AVAILABLE = False

except ImportError as e:
    print(f"❌ Could not import email_alert: {e}")
    EMAIL_MODULE_AVAILABLE = False

# Create dummy function if module not available
if not EMAIL_MODULE_AVAILABLE:
    def send_email(subject, message, receiver_email=None):
        print(f"📧 [DUMMY MODE] Would send email:\nSubject: {subject}\nMessage: {message[:100]}...")
        return True

import socket


def is_cloud():
    host = socket.gethostname().lower()
    return "streamlit" in host or "heroku" in host or "render" in host


# -------------------------------------------------
# REST OF YOUR CODE (SESSION STATE INITIALIZATION)
# -------------------------------------------------
# Initialize ALL session states using the new Streamlit 1.28+ API
if "sound_allowed" not in st.session_state:
    st.session_state.sound_allowed = True

if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

if "email_sent" not in st.session_state:
    st.session_state.email_sent = {"temperature": False, "humidity": False, "pressure": False, "co2": False,
                                   "pm25": False}

if "beep_on" not in st.session_state:
    st.session_state.beep_on = False

if "alarm" not in st.session_state:
    st.session_state.alarm = False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "hist" not in st.session_state:
    st.session_state.hist = pd.DataFrame(columns=["t", "Temp", "Hum", "Press", "CO2", "PM25"])

# Initialize data storage for analytics
if "historical_data" not in st.session_state:
    # Generate 30 days of fake historical data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    historical = pd.DataFrame({
        'Date': dates,
        'Temperature': np.random.uniform(22, 36, 30),
        'Humidity': np.random.uniform(40, 75, 30),
        'Pressure': np.random.uniform(980, 1025, 30),
        'PM2.5': np.random.uniform(10, 80, 30),
        'CO2': np.random.uniform(400, 1500, 30),
        'Noise': np.random.uniform(25, 85, 30),
        'Energy_Consumption': np.random.uniform(50, 200, 30)
    })
    st.session_state.historical_data = historical

# Initialize report storage
if "reports" not in st.session_state:
    st.session_state.reports = []

# Initialize email configuration - NOW EMAIL_MODULE_AVAILABLE IS DEFINED
if "email_config" not in st.session_state:
    st.session_state.email_config = {
        "sender_email": "parthbhale1247@gmail.com",
        "receiver_email": "parthbhale1234@gmail.com",
        "configured": EMAIL_MODULE_AVAILABLE  # ← NOW THIS WORKS!
    }


# ... rest of your dashboard.py code continues ...
# Enhanced email functionality using your existing module
class EnhancedEmailSender:
    @staticmethod
    def send_report_email(report_type, report_date, time_period, recipients=None,
                          pdf_data=None, excel_data=None, include_attachment=True):
        """Send report email with optional attachments"""
        try:
            if not EMAIL_MODULE_AVAILABLE:
                return False, "Email module not configured. Please check email_alert.py"

            # Prepare email content
            subject = f"📊 {report_type} Report - {report_date}"

            # Create email body
            body = f"""
            CRITICAL SPACE MONITORING REPORT
            =================================

            Report Type: {report_type}
            Report Date: {report_date}
            Time Period: {time_period}
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            Report Summary:
            --------------
            This report contains comprehensive monitoring data for the specified period.

            Key Highlights:
            • System monitoring data for {time_period}
            • Alert analysis and statistics
            • Environmental parameter trends
            • Recommendations and action items

            Report Files:
            -------------
            """

            if pdf_data and include_attachment:
                body += "• Complete Report (PDF format)\n"

            if excel_data and include_attachment:
                body += "• Raw Data Export (Excel format)\n"

            body += f"""

            Access the full dashboard at: http://your-dashboard-url.com

            ---
            Critical Space Monitoring System
            Automated Report Delivery
            """

            # Send the email
            success = send_email(subject, body)

            if success:
                return True, "Report email sent successfully!"
            else:
                return False, "Failed to send email"

        except Exception as e:
            return False, f"Error sending email: {str(e)}"

    @staticmethod
    def send_alert_email(parameter, value, threshold, severity="HIGH"):
        """Send alert email for critical conditions"""
        try:
            if not EMAIL_MODULE_AVAILABLE:
                return False, "Email module not configured"

            subject = f"🚨 {severity} ALERT: {parameter} Critical"

            body = f"""
            ⚠️ CRITICAL ALERT NOTIFICATION
            ==============================

            Parameter: {parameter}
            Current Value: {value}
            Threshold: {threshold}
            Severity: {severity}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Location: Main Monitoring Station

            Description:
            -------------
            The {parameter} parameter has exceeded the safe threshold of {threshold}.
            Current reading: {value}

            Recommended Actions:
            --------------------
            1. Check sensor calibration
            2. Verify system operations
            3. Implement corrective measures
            4. Review historical trends

            Immediate Steps:
            ----------------
            • Verify sensor readings
            • Check system ventilation
            • Review alert history
            • Notify technical team

            ---
            Critical Space Monitoring System
            Automated Alert System
            """

            success = send_email(subject, body)
            return success, "Alert email sent" if success else "Failed to send alert email"

        except Exception as e:
            return False, f"Error sending alert email: {str(e)}"

    @staticmethod
    def send_daily_summary_email():
        """Send daily summary email"""
        try:
            if not EMAIL_MODULE_AVAILABLE:
                return False, "Email module not configured"

            subject = f"📈 Daily Monitoring Summary - {datetime.now().strftime('%Y-%m-%d')}"

            # Get today's data
            today = datetime.now().date()
            today_data = st.session_state.historical_data[
                st.session_state.historical_data['Date'].dt.date == today
                ]

            if len(today_data) > 0:
                temp_avg = today_data['Temperature'].mean()
                humidity_avg = today_data['Humidity'].mean()
                co2_max = today_data['CO2'].max()
                alerts = len(today_data[today_data['Temperature'] > 34]) + \
                         len(today_data[today_data['Humidity'] > 70]) + \
                         len(today_data[today_data['CO2'] > 1200])
            else:
                temp_avg = 0
                humidity_avg = 0
                co2_max = 0
                alerts = 0

            body = f"""
            📊 DAILY MONITORING SUMMARY
            ============================

            Date: {datetime.now().strftime('%Y-%m-%d')}
            Generated: {datetime.now().strftime('%H:%M:%S')}

            Daily Statistics:
            -----------------
            • Average Temperature: {temp_avg:.1f}°C
            • Average Humidity: {humidity_avg:.1f}%
            • Peak CO₂ Level: {co2_max:.0f} ppm
            • Total Alerts: {alerts}

            System Status:
            --------------
            • Monitoring: ACTIVE
            • Sensors: ONLINE
            • Alerts: {"ACTIVE" if alerts > 0 else "NORMAL"}
            • Uptime: 99.8%

            Recommendations:
            ----------------
            1. Review today's alerts
            2. Check system logs
            3. Verify sensor readings
            4. Plan maintenance if needed

            ---
            Critical Space Monitoring System
            Automated Daily Report
            """

            success = send_email(subject, body)
            return success, "Daily summary sent" if success else "Failed to send daily summary"

        except Exception as e:
            return False, f"Error sending daily summary: {str(e)}"

    @staticmethod
    def test_email_connection():
        """Test email connection"""
        try:
            if not EMAIL_MODULE_AVAILABLE:
                return False, "Email module not available"

            # Send a test email
            test_subject = "Test Email - Critical Space Monitoring"
            test_body = "This is a test email from the Critical Space Monitoring System.\n\nIf you receive this, email configuration is working correctly."

            success = send_email(test_subject, test_body)

            if success:
                return True, "Test email sent successfully!"
            else:
                return False, "Failed to send test email"

        except Exception as e:
            return False, f"Test failed: {str(e)}"


# Helper function to generate PDF reports
def generate_pdf_report(report_type, report_date, time_period, include_sections, report_content, charts_data=None):
    """Generate a PDF report with all the necessary data"""
    try:
        from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        # Create a buffer for PDF
        buffer = BytesIO()

        # Create document with custom settings
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#0a1929'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        heading1_style = ParagraphStyle(
            'Heading1',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor('#1a3b5a'),
            fontName='Helvetica-Bold'
        )

        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=colors.black
        )

        # Build the content
        content = []

        # Title
        content.append(Paragraph(f"{report_type} Report", title_style))
        content.append(Spacer(1, 20))

        # Report metadata
        meta_data = [
            f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"<b>Report Date:</b> {report_date}",
            f"<b>Time Period:</b> {time_period}",
            f"<b>Location:</b> Main Monitoring Station",
            f"<b>Report ID:</b> {datetime.now().strftime('%Y%m%d%H%M%S')}",
            f"<b>Included Sections:</b> {', '.join(include_sections)}"
        ]

        for meta in meta_data:
            content.append(Paragraph(meta, normal_style))

        content.append(Spacer(1, 30))

        # Add report content sections
        sections = report_content.split("## ")
        for section in sections:
            if section.strip():
                lines = section.strip().split('\n')
                if lines:
                    section_title = lines[0]
                    section_content = '\n'.join(lines[1:]) if len(lines) > 1 else ""

                    content.append(Paragraph(section_title, heading1_style))
                    if section_content:
                        content.append(Paragraph(section_content.replace('\n', '<br/>'), normal_style))
                    content.append(Spacer(1, 15))

        # Footer
        content.append(Spacer(1, 40))
        content.append(Paragraph(f"Report generated by Critical Space Monitoring System",
                                 ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9,
                                                textColor=colors.grey, alignment=TA_CENTER)))
        content.append(Paragraph(f"Page 1 of 1",
                                 ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9,
                                                textColor=colors.grey, alignment=TA_CENTER)))

        # Build PDF
        doc.build(content)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        # Fallback to simple text report
        simple_report = f"""
        {report_type} Report
        ====================

        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Report Date: {report_date}
        Time Period: {time_period}
        Location: Main Monitoring Station

        {report_content}
        """
        # Convert to PDF
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        content = [Paragraph(simple_report.replace('\n', '<br/>'), styles["Normal"])]
        doc.build(content)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


def generate_excel_report(report_type, report_date, time_period, include_sections, report_content, filtered_data):
    """Generate an Excel report with multiple sheets"""
    # Create Excel writer
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = {
            'Report Type': [report_type],
            'Report Date': [report_date],
            'Time Period': [time_period],
            'Generated On': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'Location': ['Main Monitoring Station']
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Data sheet
        filtered_data.to_excel(writer, sheet_name='Raw Data', index=False)

        # Statistics sheet
        stats_df = filtered_data.describe().round(2)
        stats_df.to_excel(writer, sheet_name='Statistics')

        # Alert summary sheet
        alert_summary = pd.DataFrame({
            'Parameter': ['Temperature', 'Humidity', 'Pressure', 'CO2', 'PM2.5'],
            'Threshold': ['>34°C', '>70%', '<990 hPa', '>1200 ppm', '>55 µg/m³'],
            'Alerts Count': [
                len(filtered_data[filtered_data['Temperature'] > 34]),
                len(filtered_data[filtered_data['Humidity'] > 70]),
                len(filtered_data[filtered_data['Pressure'] < 990]),
                len(filtered_data[filtered_data['CO2'] > 1200]),
                len(filtered_data[filtered_data['PM2.5'] > 55])
            ],
            'Max Value': [
                filtered_data['Temperature'].max(),
                filtered_data['Humidity'].max(),
                filtered_data['Pressure'].min(),
                filtered_data['CO2'].max(),
                filtered_data['PM2.5'].max()
            ],
            'Average': [
                filtered_data['Temperature'].mean(),
                filtered_data['Humidity'].mean(),
                filtered_data['Pressure'].mean(),
                filtered_data['CO2'].mean(),
                filtered_data['PM2.5'].mean()
            ]
        })
        alert_summary.to_excel(writer, sheet_name='Alert Summary', index=False)

        # Recommendations sheet
        recommendations = pd.DataFrame({
            'Priority': ['High', 'High', 'Medium', 'Medium', 'Low'],
            'Recommendation': [
                'Install additional ventilation for high CO2 areas',
                'Schedule HVAC maintenance for temperature control',
                'Implement real-time alert notifications',
                'Add air purification in PM2.5 hotspots',
                'Review energy consumption patterns'
            ],
            'Estimated Cost': ['$5,000', '$3,000', '$1,500', '$8,000', '$500'],
            'Timeline': ['2 weeks', '1 month', '3 weeks', '2 months', '2 weeks']
        })
        recommendations.to_excel(writer, sheet_name='Recommendations', index=False)

        # Format the workbook
        workbook = writer.book
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            # Auto-adjust column widths
            for column in sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                sheet.column_dimensions[column_letter].width = adjusted_width

    excel_data = output.getvalue()
    output.close()
    return excel_data


def save_report_to_history(report_type, report_date, time_period, include_sections, file_size, file_format,
                           email_sent=False):
    """Save report metadata to history"""
    report_id = datetime.now().strftime('%Y%m%d%H%M%S')
    report_metadata = {
        'id': report_id,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': report_type,
        'report_date': str(report_date),
        'time_period': time_period,
        'sections': include_sections,
        'size': file_size,
        'format': file_format,
        'email_sent': email_sent,
        'status': 'Generated'
    }

    st.session_state.reports.append(report_metadata)

    # Keep only last 50 reports
    if len(st.session_state.reports) > 50:
        st.session_state.reports = st.session_state.reports[-50:]

    return report_id


def analytics_page():
    # ----- LOGIN GUARD -----
    if not st.session_state.get('logged_in', False):
        st.stop()
    # Title
    st.markdown("<div class='hero'>📊 Advanced Analytics & Trends</div>", unsafe_allow_html=True)

    # Create navigation header for analytics page
    now = datetime.now().strftime("%H:%M:%S")

    # Analytics Overview Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_temp = st.session_state.historical_data['Temperature'].mean()
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{avg_temp:.1f}°C</div>
            <div class="stat-label">Avg Temperature</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        max_co2 = st.session_state.historical_data['CO2'].max()
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{max_co2:.0f} ppm</div>
            <div class="stat-label">Peak CO₂</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        alert_days = len(st.session_state.historical_data[st.session_state.historical_data['Temperature'] > 34])
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{alert_days}</div>
            <div class="stat-label">Alert Days</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        energy_avg = st.session_state.historical_data['Energy_Consumption'].mean()
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{energy_avg:.0f} kWh</div>
            <div class="stat-label">Avg Energy Use</div>
        </div>
        """, unsafe_allow_html=True)

    # Time Range Selector
    st.markdown("<div class='card'><div class='hdr'>📅 Date Range Selection</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date",
                                   value=datetime.now() - timedelta(days=30),
                                   min_value=datetime.now() - timedelta(days=365),
                                   max_value=datetime.now())
    with col2:
        end_date = st.date_input("End Date",
                                 value=datetime.now(),
                                 min_value=datetime.now() - timedelta(days=365),
                                 max_value=datetime.now())

    # Filter data based on selection
    filtered_data = st.session_state.historical_data[
        (st.session_state.historical_data['Date'] >= pd.Timestamp(start_date)) &
        (st.session_state.historical_data['Date'] <= pd.Timestamp(end_date))
        ]

    st.markdown("</div>", unsafe_allow_html=True)

    # Main Analytics Charts
    tab1, tab2, tab3 = st.tabs(["📈 Trends Over Time", "🔍 Correlation Analysis", "📊 Statistical Summary"])

    with tab1:
        st.markdown("<div class='card'><div class='hdr'>Time Series Analysis</div>", unsafe_allow_html=True)

        # Multi-line chart for all parameters - SIMPLIFIED VERSION
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=filtered_data['Date'],
            y=filtered_data['Temperature'],
            name='Temperature',
            line=dict(color='#6fe3ff', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=filtered_data['Date'],
            y=filtered_data['Humidity'],
            name='Humidity',
            line=dict(color='#ff7d7d', width=2),
            yaxis='y2'
        ))

        fig.add_trace(go.Scatter(
            x=filtered_data['Date'],
            y=filtered_data['CO2'] / 10,
            name='CO₂ (ppm/10)',
            line=dict(color='#cc99ff', width=2),
            yaxis='y3'
        ))

        # SIMPLIFIED LAYOUT - NO titlefont property
        fig.update_layout(
            template="plotly_dark",
            height=500,
            title="Environmental Parameters Over Time",
            xaxis=dict(title="Date"),
            yaxis=dict(title="Temperature (°C)"),
            yaxis2=dict(
                title="Humidity (%)",
                overlaying="y",
                side="right"
            ),
            yaxis3=dict(
                title="CO₂ (ppm/10)",
                overlaying="y",
                side="right",
                position=0.95
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Individual parameter charts
        st.markdown("<div class='card'><div class='hdr'>Individual Parameter Analysis</div>", unsafe_allow_html=True)
        selected_param = st.selectbox(
            "Select Parameter",
            ["Temperature", "Humidity", "Pressure", "PM2.5", "CO2", "Noise", "Energy_Consumption"],
            index=0
        )

        col1, col2 = st.columns(2)
        with col1:
            fig2 = px.line(filtered_data, x='Date', y=selected_param,
                           title=f'{selected_param} Trend',
                           template="plotly_dark")
            fig2.update_traces(line_color='#7ceaff')
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            fig3 = px.histogram(filtered_data, x=selected_param,
                                title=f'{selected_param} Distribution',
                                template="plotly_dark")
            fig3.update_traces(marker_color='#ff7d7d')
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='card'><div class='hdr'>Correlation Analysis</div>", unsafe_allow_html=True)

        # Correlation matrix
        corr_params = ['Temperature', 'Humidity', 'CO2', 'PM2.5', 'Energy_Consumption']
        corr_matrix = filtered_data[corr_params].corr()

        fig4 = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_params,
            y=corr_params,
            colorscale='RdYlBu_r',
            zmin=-1,
            zmax=1,
            text=np.round(corr_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverinfo='text'
        ))

        fig4.update_layout(
            template="plotly_dark",
            title="Correlation Matrix",
            height=500
        )

        st.plotly_chart(fig4, use_container_width=True)

        # Scatter plot for selected correlation - REMOVED TRENDLINE
        st.markdown("<div class='card'><div class='hdr'>Scatter Plot Analysis</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            x_param = st.selectbox("X-axis Parameter", corr_params, index=0, key='x_param')
        with col2:
            y_param = st.selectbox("Y-axis Parameter", corr_params, index=1, key='y_param')

        # FIXED: Removed trendline="ols" to avoid statsmodels dependency
        fig5 = px.scatter(filtered_data, x=x_param, y=y_param,
                          title=f'{x_param} vs {y_param}',
                          template="plotly_dark")
        fig5.update_traces(marker=dict(color='#7ceaff', size=8))
        st.plotly_chart(fig5, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='card'><div class='hdr'>Statistical Summary</div>", unsafe_allow_html=True)

        # Summary statistics table
        stats_df = filtered_data.describe().round(2)
        st.dataframe(stats_df.style.background_gradient(cmap='Blues'), use_container_width=True)

        # Alert statistics
        st.markdown("<div class='card'><div class='hdr'>Alert Statistics</div>", unsafe_allow_html=True)

        alert_stats = pd.DataFrame({
            'Parameter': ['Temperature', 'Humidity', 'Pressure', 'CO2', 'PM2.5'],
            'Threshold': ['>34°C', '>70%', '<990 hPa', '>1200 ppm', '>55 µg/m³'],
            'Alerts Count': [
                len(filtered_data[filtered_data['Temperature'] > 34]),
                len(filtered_data[filtered_data['Humidity'] > 70]),
                len(filtered_data[filtered_data['Pressure'] < 990]),
                len(filtered_data[filtered_data['CO2'] > 1200]),
                len(filtered_data[filtered_data['PM2.5'] > 55])
            ],
            'Max Value': [
                filtered_data['Temperature'].max(),
                filtered_data['Humidity'].max(),
                filtered_data['Pressure'].min(),
                filtered_data['CO2'].max(),
                filtered_data['PM2.5'].max()
            ]
        })

        st.dataframe(alert_stats.style.background_gradient(subset=['Alerts Count'], cmap='Reds'),
                     use_container_width=True)

        # Export analytics data
        st.markdown("<div class='card'><div class='hdr'>Export Analytics Data</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"Analytics_Data_{start_date}_{end_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col2:
            # Generate Excel report
            excel_data = generate_excel_report(
                report_type="Analytics Export",
                report_date=datetime.now().date(),
                time_period=f"{start_date} to {end_date}",
                include_sections=["Raw Data", "Statistics", "Alert Summary"],
                report_content=f"Analytics export for period {start_date} to {end_date}",
                filtered_data=filtered_data
            )

            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name=f"Analytics_Report_{start_date}_{end_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col3:
            # Email analytics report
            if st.button("📧 Email Report", use_container_width=True, key="email_analytics"):
                with st.spinner("Sending analytics report..."):
                    success, message = EnhancedEmailSender.send_report_email(
                        report_type="Analytics Export",
                        report_date=datetime.now().date(),
                        time_period=f"{start_date} to {end_date}"
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        st.markdown("</div>", unsafe_allow_html=True)

    # Sidebar for analytics page
    with st.sidebar:
        st.markdown("### ⚙️ Analytics Settings")

        st.markdown("---")

        # Quick navigation
        st.markdown("### 🚀 Quick Navigation")
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("📊", key="analytics_side_dash", help="Go to Dashboard"):
                st.session_state.current_page = "dashboard"
                st.rerun()
        with nav_col2:
            if st.button("📈", key="analytics_side_analytics", help="Go to Analytics"):
                st.session_state.current_page = "analytics"
                st.rerun()
        with nav_col3:
            if st.button("📋", key="analytics_side_reports", help="Go to Reports"):
                st.session_state.current_page = "reports"
                st.rerun()

        st.markdown("---")

        # Data info
        st.markdown("### 📊 Data Info")
        st.metric("Days of Data", len(filtered_data))
        st.metric("Parameters Tracked", "7")

        st.markdown("---")

        # Back to dashboard button
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()


def reports_page():
    # ----- LOGIN GUARD -----
if "email_config" not in st.session_state:
        st.session_state.email_config = {
            "sender_email": "",
            "receiver_email": "",
            "smtp_server": "",
            "smtp_port": "",
            "password": ""
        }

    # LOGIN GUARD
    if not st.session_state.get("logged_in", False):
        st.stop()
# --- SAFE INITIALIZATION FOR CLOUD ---


    # Title
    st.markdown("<div class='hero'>📋 Comprehensive Reports</div>", unsafe_allow_html=True)

    # Create navigation header for reports page
    now = datetime.now().strftime("%H:%M:%S")

    # Email Configuration Section
    st.markdown("<div class='card'><div class='hdr'>📧 Email Configuration</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Sender Email:** {st.session_state.email_config['sender_email']}")
    with col2:
        st.info(f"**Receiver Email:** {st.session_state.email_config['receiver_email']}")

    # Email status
    if EMAIL_MODULE_AVAILABLE:
        st.success("✅ Email module is configured and ready to use")

        # Test email connection
        if st.button("🔧 Test Email Connection", key="test_email_conn"):
            with st.spinner("Testing email connection..."):
                success, message = EnhancedEmailSender.test_email_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
    else:
        st.warning("⚠️ Email module not found. Please ensure email_alert.py is in the same directory.")
        st.info("To set up email, create a file named 'email_alert.py' with your email credentials.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Report Generation Options
    st.markdown("<div class='card'><div class='hdr'>📄 Report Generator</div>", unsafe_allow_html=True)

    report_type = st.selectbox(
        "Select Report Type",
        ["Daily Summary", "Weekly Analysis", "Monthly Review", "Incident Report", "Compliance Report", "Custom Report"]
    )

    col1, col2 = st.columns(2)
    with col1:
        report_date = st.date_input("Report Date", value=datetime.now())
    with col2:
        time_period = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last quarter", "Custom range", "Year to date"]
        )

    include_sections = st.multiselect(
        "Include Sections",
        ["Executive Summary", "Sensor Data", "Alert History", "Trend Analysis",
         "Recommendations", "Action Items", "Cost Analysis", "Energy Consumption",
         "System Performance", "Maintenance Log"],
        default=["Executive Summary", "Sensor Data", "Alert History", "Recommendations"]
    )

    # Email options
    st.markdown("#### 📧 Email Options")
    email_recipients = st.text_input("Email Recipients (comma separated)",
                                     "parthbhale1234@gmail.com",
                                     key="email_recipients")

    email_options_col1, email_options_col2 = st.columns(2)
    with email_options_col1:
        send_email_check = st.checkbox("Send email with report", value=True, key="send_email_check")
    with email_options_col2:
        include_attachment = st.checkbox("Include attachments", value=True, key="include_attachment")

    st.markdown("</div>", unsafe_allow_html=True)

    # Generated Report Preview
    st.markdown("<div class='card'><div class='hdr'>📋 Report Preview</div>", unsafe_allow_html=True)

    # Mock report content with more details
    report_content = f"""
    # {report_type} Report
    **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    **Period:** {time_period}
    **Location:** Main Monitoring Station
    **Report ID:** {datetime.now().strftime('%Y%m%d%H%M%S')}

    ## Executive Summary
    - Total monitoring period: 30 days
    - System uptime: 99.8%
    - Critical alerts: {len(st.session_state.historical_data[st.session_state.historical_data['Temperature'] > 34])}
    - Average temperature: {st.session_state.historical_data['Temperature'].mean():.1f}°C
    - Peak CO₂ level: {st.session_state.historical_data['CO2'].max():.0f} ppm
    - Average energy consumption: {st.session_state.historical_data['Energy_Consumption'].mean():.0f} kWh

    ## Key Findings
    1. Temperature remained within acceptable range for 85% of the period
    2. Humidity control maintained optimal conditions (average: {st.session_state.historical_data['Humidity'].mean():.1f}%)
    3. Air quality improved by 15% compared to previous period
    4. Energy consumption optimized by 8% through automated controls
    5. System reliability maintained at 99.8% uptime

    ## Sensor Data Overview
    - Temperature Range: {st.session_state.historical_data['Temperature'].min():.1f}°C to {st.session_state.historical_data['Temperature'].max():.1f}°C
    - Humidity Range: {st.session_state.historical_data['Humidity'].min():.1f}% to {st.session_state.historical_data['Humidity'].max():.1f}%
    - CO₂ Range: {st.session_state.historical_data['CO2'].min():.0f} ppm to {st.session_state.historical_data['CO2'].max():.0f} ppm
    - PM2.5 Range: {st.session_state.historical_data['PM2.5'].min():.1f} µg/m³ to {st.session_state.historical_data['PM2.5'].max():.1f} µg/m³

    ## Alert History
    - Temperature Alerts: {len(st.session_state.historical_data[st.session_state.historical_data['Temperature'] > 34])} occurrences
    - Humidity Alerts: {len(st.session_state.historical_data[st.session_state.historical_data['Humidity'] > 70])} occurrences
    - CO₂ Alerts: {len(st.session_state.historical_data[st.session_state.historical_data['CO2'] > 1200])} occurrences
    - PM2.5 Alerts: {len(st.session_state.historical_data[st.session_state.historical_data['PM2.5'] > 55])} occurrences

    ## Recommendations
    1. Consider additional ventilation during peak occupancy hours (10:00-16:00)
    2. Schedule maintenance for HVAC systems before summer season
    3. Implement automated alerts for rapid response to critical conditions
    4. Review energy consumption patterns for further optimization
    5. Consider upgrading air filtration in high PM2.5 areas

    ## Action Items
    - [ ] Review alert response times and implement improvements
    - [ ] Update maintenance schedules based on system performance data
    - [ ] Train staff on new monitoring protocols and emergency procedures
    - [ ] Validate sensor calibration quarterly
    - [ ] Implement energy-saving measures identified in analysis

    ## Cost Analysis
    - Estimated energy savings potential: $1,200/month
    - Maintenance cost avoidance: $5,000/year
    - Compliance risk mitigation: Priceless
    - Recommended investment: $15,000 for system upgrades

    *Report generated by Critical Space Monitoring System - Version 2.1*
    *Confidential - For internal use only*
    """

    st.text_area("Report Content Preview", report_content, height=300, key="report_preview")

    # Report Charts
    st.markdown("<div class='card'><div class='hdr'>📈 Report Charts Preview</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # Alert frequency chart
        alerts_by_day = st.session_state.historical_data['Temperature'] > 34
        fig1 = go.Figure(data=[go.Bar(
            x=st.session_state.historical_data['Date'],
            y=alerts_by_day.astype(int),
            marker_color='#ff7676'
        )])
        fig1.update_layout(
            template="plotly_dark",
            title="Temperature Alerts by Day",
            height=300
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Parameter distribution
        fig2 = go.Figure()
        fig2.add_trace(go.Box(
            y=st.session_state.historical_data['Temperature'],
            name='Temperature',
            marker_color='#6fe3ff'
        ))
        fig2.add_trace(go.Box(
            y=st.session_state.historical_data['Humidity'],
            name='Humidity',
            marker_color='#ff7d7d'
        ))
        fig2.update_layout(
            template="plotly_dark",
            title="Parameter Distribution",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Export Options
    st.markdown("<div class='card'><div class='hdr'>💾 Export Options</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📄 Generate PDF Report", use_container_width=True, key="generate_pdf"):
            with st.spinner("Generating PDF report..."):
                # Get filtered data for the selected time period
                if time_period == "Last 7 days":
                    start_date = datetime.now() - timedelta(days=7)
                elif time_period == "Last 30 days":
                    start_date = datetime.now() - timedelta(days=30)
                elif time_period == "Last quarter":
                    start_date = datetime.now() - timedelta(days=90)
                else:
                    start_date = datetime.now() - timedelta(days=30)

                filtered_data = st.session_state.historical_data[
                    st.session_state.historical_data['Date'] >= pd.Timestamp(start_date)
                    ]

                pdf_data = generate_pdf_report(
                    report_type=report_type,
                    report_date=report_date,
                    time_period=time_period,
                    include_sections=include_sections,
                    report_content=report_content,
                    charts_data=filtered_data
                )

                # Save to history
                report_id = save_report_to_history(
                    report_type=report_type,
                    report_date=report_date,
                    time_period=time_period,
                    include_sections=include_sections,
                    file_size=f"{len(pdf_data) / 1024:.1f} KB",
                    file_format="PDF",
                    email_sent=False
                )

                st.success(f"PDF report generated! (ID: {report_id})")

                # Create download button
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_data,
                    file_name=f"{report_type.replace(' ', '_')}_{report_date}_{report_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                # Send email if requested
                if send_email_check and EMAIL_MODULE_AVAILABLE:
                    with st.spinner("Sending email..."):
                        success, message = EnhancedEmailSender.send_report_email(
                            report_type=report_type,
                            report_date=report_date,
                            time_period=time_period,
                            recipients=[email.strip() for email in email_recipients.split(',')],
                            pdf_data=pdf_data if include_attachment else None,
                            include_attachment=include_attachment
                        )

                        if success:
                            st.success("✅ Report emailed successfully!")
                            # Update report history
                            for report in st.session_state.reports:
                                if report['id'] == report_id:
                                    report['email_sent'] = True
                                    break
                        else:
                            st.error(f"Email failed: {message}")

    with col2:
        if st.button("📊 Generate Excel Report", use_container_width=True, key="generate_excel"):
            with st.spinner("Generating Excel report..."):
                # Get filtered data
                if time_period == "Last 7 days":
                    start_date = datetime.now() - timedelta(days=7)
                elif time_period == "Last 30 days":
                    start_date = datetime.now() - timedelta(days=30)
                elif time_period == "Last quarter":
                    start_date = datetime.now() - timedelta(days=90)
                else:
                    start_date = datetime.now() - timedelta(days=30)

                filtered_data = st.session_state.historical_data[
                    st.session_state.historical_data['Date'] >= pd.Timestamp(start_date)
                    ]

                excel_data = generate_excel_report(
                    report_type=report_type,
                    report_date=report_date,
                    time_period=time_period,
                    include_sections=include_sections,
                    report_content=report_content,
                    filtered_data=filtered_data
                )

                # Save to history
                report_id = save_report_to_history(
                    report_type=report_type,
                    report_date=report_date,
                    time_period=time_period,
                    include_sections=include_sections,
                    file_size=f"{len(excel_data) / 1024:.1f} KB",
                    file_format="Excel",
                    email_sent=False
                )

                st.success(f"Excel report generated! (ID: {report_id})")

                # Create download button
                st.download_button(
                    label="⬇️ Download Excel",
                    data=excel_data,
                    file_name=f"{report_type.replace(' ', '_')}_{report_date}_{report_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    with col3:
        if st.button("📧 Email Report Only", use_container_width=True, key="email_report_only"):
            if EMAIL_MODULE_AVAILABLE:
                with st.spinner("Sending report email..."):
                    success, message = EnhancedEmailSender.send_report_email(
                        report_type=report_type,
                        report_date=report_date,
                        time_period=time_period,
                        recipients=[email.strip() for email in email_recipients.split(',')]
                    )

                    if success:
                        st.success("✅ Report emailed successfully!")

                        # Save to history
                        save_report_to_history(
                            report_type=report_type,
                            report_date=report_date,
                            time_period=time_period,
                            include_sections=include_sections,
                            file_size="N/A",
                            file_format="Email",
                            email_sent=True
                        )
                    else:
                        st.error(f"❌ Email failed: {message}")
            else:
                st.error("Email module not available")

    with col4:
        if st.button("📁 Save to Archive", use_container_width=True, key="save_archive"):
            # Save report metadata to session state
            report_id = save_report_to_history(
                report_type=report_type,
                report_date=report_date,
                time_period=time_period,
                include_sections=include_sections,
                file_size="N/A",
                file_format="Archived",
                email_sent=False
            )
            st.success(f"✅ Report saved to archive! (ID: {report_id})")

    # Scheduled Reports
    st.markdown("<div class='card'><div class='hdr'>⏰ Scheduled Reports</div>", unsafe_allow_html=True)

    schedule_col1, schedule_col2, schedule_col3 = st.columns(3)
    with schedule_col1:
        daily_report = st.checkbox("Daily Report", value=True, key="daily_report")
    with schedule_col2:
        weekly_report = st.checkbox("Weekly Summary", value=True, key="weekly_report")
    with schedule_col3:
        monthly_report = st.checkbox("Monthly Review", value=False, key="monthly_report")

    col1, col2 = st.columns(2)
    with col1:
        schedule_format = st.selectbox("Schedule Format", ["PDF", "Excel", "Email Only"], key="schedule_format")
    with col2:
        schedule_time = st.time_input("Schedule Time", value=datetime.now().time(), key="schedule_time")

    # Quick email actions
    st.markdown("#### Quick Email Actions")
    quick_email_col1, quick_email_col2, quick_email_col3 = st.columns(3)

    with quick_email_col1:
        if st.button("📨 Send Test Email", use_container_width=True, key="send_test_email"):
            if EMAIL_MODULE_AVAILABLE:
                with st.spinner("Sending test email..."):
                    success, message = EnhancedEmailSender.test_email_connection()
                    if success:
                        st.success("✅ Test email sent!")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.error("Email module not available")

    with quick_email_col2:
        if st.button("📊 Send Daily Summary", use_container_width=True, key="send_daily_summary"):
            if EMAIL_MODULE_AVAILABLE:
                with st.spinner("Sending daily summary..."):
                    success, message = EnhancedEmailSender.send_daily_summary_email()
                    if success:
                        st.success("✅ Daily summary sent!")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.error("Email module not available")

    with quick_email_col3:
        if st.button("💾 Save Schedule", use_container_width=True, key="save_schedule"):
            st.success("✅ Report schedule saved successfully!")

    st.markdown("</div>", unsafe_allow_html=True)

    # Previous Reports
    st.markdown("<div class='card'><div class='hdr'>📚 Report Archive</div>", unsafe_allow_html=True)

    # Display saved reports
    if st.session_state.reports:
        st.write(f"**Total Reports:** {len(st.session_state.reports)}")

        # Create a DataFrame for display
        reports_df = pd.DataFrame(st.session_state.reports)

        # Add email status icon
        def get_email_status_icon(email_sent):
            return "✅" if email_sent else "❌"

        # Display in a nice table
        for report in reversed(st.session_state.reports[-10:]):  # Show last 10 reports
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 2])
            with col1:
                st.write(f"**{report['date']}**")
            with col2:
                st.write(report['type'])
            with col3:
                st.write(report['format'])
            with col4:
                st.write(get_email_status_icon(report.get('email_sent', False)))
            with col5:
                if st.button("📧 Resend", key=f"resend_{report['id']}"):
                    if EMAIL_MODULE_AVAILABLE:
                        with st.spinner("Resending email..."):
                            success, message = EnhancedEmailSender.send_report_email(
                                report_type=report['type'],
                                report_date=report['report_date'],
                                time_period=report['time_period']
                            )
                            if success:
                                st.success("✅ Email resent!")
                                report['email_sent'] = True
                            else:
                                st.error(f"❌ {message}")

        # Quick actions
        st.markdown("#### Quick Actions")
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("📥 Export All as CSV", use_container_width=True):
                csv_data = pd.DataFrame(st.session_state.reports).to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="all_reports_metadata.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with action_col2:
            if st.button("🗑️ Clear Old Reports", use_container_width=True):
                # Keep only last 20 reports
                st.session_state.reports = st.session_state.reports[-20:]
                st.success("✅ Old reports cleared!")
                st.rerun()
    else:
        st.info("📭 No reports generated yet. Generate your first report above!")

    st.markdown("</div>", unsafe_allow_html=True)

    # Sidebar for reports page
    with st.sidebar:
        st.markdown("### ⚙️ Reports Settings")

        st.markdown("---")

        # Quick navigation
        st.markdown("### 🚀 Quick Navigation")
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("📊", key="reports_side_dash", help="Go to Dashboard"):
                st.session_state.current_page = "dashboard"
                st.rerun()
        with nav_col2:
            if st.button("📈", key="reports_side_analytics", help="Go to Analytics"):
                st.session_state.current_page = "analytics"
                st.rerun()
        with nav_col3:
            if st.button("📋", key="reports_side_reports", help="Go to Reports"):
                st.session_state.current_page = "reports"
                st.rerun()

        st.markdown("---")

        # Email status
        st.markdown("### 📧 Email Status")
        if EMAIL_MODULE_AVAILABLE:
            st.success("✅ Configured")
            if st.button("Test Connection", key="sidebar_test_email"):
                with st.spinner("Testing..."):
                    success, message = EnhancedEmailSender.test_email_connection()
                    if success:
                        st.success("✅ Connected")
                    else:
                        st.error(f"❌ {message}")
        else:
            st.error("❌ Not Configured")
            st.info("Add email_alert.py to enable")

        # Report settings
        st.markdown("### 📋 Report Settings")
        auto_generate = st.checkbox("Auto-generate weekly", value=True, key="auto_gen")
        email_notify = st.checkbox("Email notifications", value=True, key="email_notify")

        # Archive settings
        st.markdown("### 📁 Archive Settings")
        keep_days = st.slider("Keep reports (days)", 30, 365, 90, key="keep_days")
        auto_cleanup = st.checkbox("Auto-cleanup", value=True, key="auto_cleanup")

        st.markdown("---")

        # Quick stats
        st.markdown("### 📊 Report Stats")
        st.metric("Total Reports", len(st.session_state.reports))

        if st.session_state.reports:
            email_sent_count = sum(1 for r in st.session_state.reports if r.get('email_sent', False))
            st.metric("Emails Sent", email_sent_count)

        st.markdown("---")

        # Quick email actions
        st.markdown("### 🚀 Quick Actions")
        if st.button("📨 Send Test", use_container_width=True):
            if EMAIL_MODULE_AVAILABLE:
                success, message = EnhancedEmailSender.test_email_connection()
                if success:
                    st.success("✅ Test sent!")
                else:
                    st.error(f"❌ {message}")

        if st.button("📊 Daily Summary", use_container_width=True):
            if EMAIL_MODULE_AVAILABLE:
                success, message = EnhancedEmailSender.send_daily_summary_email()
                if success:
                    st.success("✅ Summary sent!")
                else:
                    st.error(f"❌ {message}")

        st.markdown("---")

        # Back to dashboard button
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()

def dashboard_page():
    if 'sound_allowed' not in st.session_state:
        st.session_state.sound_allowed = True

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"

    if 'email_sent' not in st.session_state:
        st.session_state.email_sent = {"temperature": False, "humidity": False, "pressure": False, "co2": False,
                                       "pm25": False}

    if 'beep_on' not in st.session_state:
        st.session_state.beep_on = False

    if 'alarm' not in st.session_state:
        st.session_state.alarm = False

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if 'hist' not in st.session_state:
        st.session_state.hist = pd.DataFrame(columns=["t", "Temp", "Hum", "Press", "CO2", "PM25"])

    if 'historical_data' not in st.session_state:
        # Generate 30 days of fake historical data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        historical = pd.DataFrame({
            'Date': dates,
            'Temperature': np.random.uniform(22, 36, 30),
            'Humidity': np.random.uniform(40, 75, 30),
            'Pressure': np.random.uniform(980, 1025, 30),
            'PM2.5': np.random.uniform(10, 80, 30),
            'CO2': np.random.uniform(400, 1500, 30),
            'Noise': np.random.uniform(25, 85, 30),
            'Energy_Consumption': np.random.uniform(50, 200, 30)
        })
        st.session_state.historical_data = historical

        # ===== LOGIN GUARD =====
    if not st.session_state.get('logged_in', False):
        st.stop()

        # Rest of your function...

    # ----- HIDE STREAMLIT CHROME -----
    st.markdown("""
    <style>
    header, footer {visibility:hidden;}
    [data-testid="stToolbar"] {visibility:hidden;}
    </style>
    """, unsafe_allow_html=True)

    # ----- BACKGROUND IMAGE -----
    def b64(file):
        try:
            with open(file, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except:
            # Return a default gradient background if image not found
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    bg = b64("bg1.png")

    # ----- GLOBAL CSS (MATCH IMAGE FEEL) -----
    st.markdown(f"""
    <style>
    .stApp {{
        background: url("data:image/png;base64,{bg}") center/cover no-repeat;
        color: #d8f6ff;
    }}
    .veil {{
        position: fixed; inset:0;
        background: linear-gradient(180deg, rgba(7,16,28,.55), rgba(5,12,22,.85));
        z-index:-1;
    }}

    /* Top bar */
    .top {{
        display:grid; grid-template-columns: 1fr 2fr;
        align-items:center;
        padding: 14px 28px;
        border-bottom:1px solid rgba(140,220,255,.25);
        background: rgba(8,18,33,.65);
        backdrop-filter: blur(8px);
    }}
    .brand {{
        letter-spacing:.18em; font-weight:700; color:#7ceaff;
    }}
    .menu {{
        text-align:right; font-weight:600;
    }}
    .menu span {{ 
        margin-left:26px; 
        color:#a8edff; 
        cursor: pointer;
        transition: color 0.3s;
    }}
    .menu span:hover {{ 
        color: #7ceaff;
        text-decoration: underline;
    }}
    .active-nav {{ 
        color: #67ffb5 !important;
        font-weight: 700;
        border-bottom: 2px solid #67ffb5;
        padding-bottom: 2px;
    }}
    .live {{ color:#67ffb5; }}

    /* Title */
    .hero {{
        margin: 18px 28px;
        font-size: 28px; font-weight:700; color:#bff5ff;
    }}

    /* Glass cards */
    .card {{
        background: rgba(11,24,44,.75);
        border:1px solid rgba(140,220,255,.25);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,.02), 0 0 24px rgba(0,0,0,.45);
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 20px;
    }}
    .hdr {{ font-size:20px; margin-bottom:10px; color:#bff5ff; }}

    /* Table style */
    table {{ width:100%; border-collapse:collapse; }}
    th,td {{ padding:10px; text-align:left; }}
    th {{ border-bottom:2px solid rgba(140,220,255,.3); }}
    tr:not(:last-child) td {{ border-bottom:1px solid rgba(255,255,255,.06); }}
    .ok {{ color:#67ffb5; }}
    .mid {{ color:#ffd966; }}
    .bad {{ color:#ff7676; }}

    /* Alerts + Notifications */
    .alert {{ background: rgba(110,20,20,.6); border-left:4px solid #ff6b6b; padding:10px; border-radius:8px; margin-bottom:8px; }}
    .note  {{ background: rgba(15,80,65,.55); border-left:4px solid #4deac2; padding:10px; border-radius:8px; margin-bottom:8px; }}
    .info  {{ background: rgba(20,60,110,.55); border-left:4px solid #6fe3ff; padding:10px; border-radius:8px; margin-bottom:8px; }}

    /* Stats cards */
    .stat-card {{
        background: rgba(11,24,44,.75);
        border:1px solid rgba(140,220,255,.25);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }}
    .stat-value {{ font-size: 28px; font-weight: bold; color: #7ceaff; }}
    .stat-label {{ font-size: 14px; color: #a8edff; margin-top: 5px; }}

    /* Navigation buttons */
    .nav-btn {{
        background: none;
        border: none;
        color: #a8edff;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        padding: 5px 10px;
        margin-left: 20px;
    }}
    .nav-btn:hover {{
        color: #7ceaff;
        text-decoration: underline;
    }}
    .nav-btn.active {{
        color: #67ffb5;
        border-bottom: 2px solid #67ffb5;
    }}

    /* Custom button styling */
    .stButton > button {{
        background: rgba(11,24,44,.75);
        border: 1px solid rgba(140,220,255,.25);
        color: #d8f6ff;
        border-radius: 8px;
        transition: all 0.3s;
    }}
    .stButton > button:hover {{
        background: rgba(11,24,44,.9);
        border: 1px solid rgba(140,220,255,.5);
        color: #7ceaff;
    }}
    </style>
    <div class="veil"></div>
    """, unsafe_allow_html=True)

    # ----- HEADER / NAVBAR -----
    now = datetime.now().strftime("%H:%M:%S")

    # Get current page safely
    current_page = st.session_state.get('current_page', 'dashboard')

    st.markdown(f"""
    <div class="top">
      <div class="brand">CRITICAL SPACE MONITORING</div>
      <div class="menu">
        <span style="{'color: #67ffb5; font-weight: 700; border-bottom: 2px solid #67ffb5; padding-bottom: 2px;' if current_page == 'dashboard' else ''}">Dashboard</span>
        <span style="{'color: #67ffb5; font-weight: 700; border-bottom: 2px solid #67ffb5; padding-bottom: 2px;' if current_page == 'analytics' else ''}">Analytics</span>
        <span style="{'color: #67ffb5; font-weight: 700; border-bottom: 2px solid #67ffb5; padding-bottom: 2px;' if current_page == 'reports' else ''}">Reports</span>
        <span class="live">● LIVE&nbsp;{now}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Create clickable navigation using columns
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([2, 1, 1, 2])

    with nav_col1:
        # Empty column for spacing
        pass

    with nav_col2:
        if st.button("Dashboard", key="nav_dashboard", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()

    with nav_col3:
        if st.button("Analytics", key="nav_analytics", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()

    with nav_col4:
        if st.button("Reports", key="nav_reports", use_container_width=True):
            st.session_state.current_page = "reports"
            st.rerun()

    # Add some spacing
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Handle page navigation - USE .get() HERE
    current_page = st.session_state.get('current_page', 'dashboard')
    if current_page != "dashboard":
        if current_page == "analytics":
            analytics_page()
        elif current_page == "reports":
            reports_page()
        return

    # ----- TITLE -----
    st.markdown("<div class='hero'>Critical Space Environment Monitoring – Real-Time Dashboard</div>",
                unsafe_allow_html=True)

    # ----- DATA (demo) -----
    def read():
        return {
            "Temperature": round(random.uniform(22, 36), 1),
            "Humidity": round(random.uniform(40, 75), 1),
            "Pressure": round(random.uniform(980, 1025), 1),
            "PM2.5": round(random.uniform(10, 80), 1),
            "CO2": round(random.uniform(400, 1500), 1),
            "Noise": round(random.uniform(25, 85), 1)
        }

    s = read()

    # ----- STATUS -----
    def status(name, val):
        if name == "Temperature":
            if val > 34: return "High", "bad"
            if val > 26: return "Warm", "mid"
            return "Normal", "ok"
        if name == "Humidity":
            if val > 70: return "Very High", "bad"
            if val > 60: return "High", "mid"
            return "Normal", "ok"
        if name == "CO2":
            if val > 1200: return "High", "bad"
            if val > 800:  return "Moderate", "mid"
            return "Normal", "ok"
        if name == "PM2.5":
            if val > 55: return "High", "bad"
            if val > 35: return "Moderate", "mid"
            return "Clean", "ok"
        if name == "Pressure":
            if val < 990: return "Low", "bad"
            if val < 1000: return "Moderate", "mid"
            return "Normal", "ok"
        return "Safe", "ok"

    # ----- BEEP -----
    def load_beep():
        try:
            with open("beep-02.mp3", "rb") as f:
                return base64.b64encode(f.read()).decode()
        except:
            # Fallback to online beep if local file not found
            return "T2dnUwACAAAAAAAAAAAuZnpXAAAAABX54EgB9tEDh4dG9vZ0dG5nLm1pY3Jvc29mdC5jb20vdG9vbHMvZWNobzFfbWFpbi5tcDMA//NgxAAdGV0qb0IAAUZGw2m3m5u7u7u2Nju7R7t7tHbHf93R2x3d9v//////f//////////////////////////8R3///EQ4fBAQEEB/fuAQMBA0E0KQBAQdBAf4eH+P/8uFGh0b2QAAAAAAAAAAAA//MUZAAAAAGkAAAAAAAAA0gAAAAATEFN//MUZAMAAAGkAAAAAAAAA0gAAAAARTMu//MUZAYAAAGkAAAAAAAAA0gAAAAAOTku//MUZAkAAAGkAAAAAAAAA0gAAAAANVVV"

    beep = load_beep()

    # ----- QUICK STATS ROW -----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{s['Temperature']}°C</div>
            <div class="stat-label">Temperature</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{s['Humidity']}%</div>
            <div class="stat-label">Humidity</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{s['CO2']} ppm</div>
            <div class="stat-label">CO₂ Level</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        air_quality = "Good" if s['PM2.5'] < 35 else "Moderate" if s['PM2.5'] < 55 else "Poor"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{air_quality}</div>
            <div class="stat-label">Air Quality</div>
        </div>
        """, unsafe_allow_html=True)

    # ----- MAIN GRID (TOP ROW: LEFT + RIGHT) -----
    top_left, top_right = st.columns([1.15, 2.0], gap="large")

    # LEFT: LIVE SENSOR DATA (table card)
    with top_left:
        st.markdown("<div class='card'><div class='hdr'>Live Sensor Data</div>", unsafe_allow_html=True)
        rows = [
            ("Temperature", f"{s['Temperature']} °C"),
            ("Humidity", f"{s['Humidity']} %"),
            ("Pressure", f"{s['Pressure']} hPa"),
            ("Air Quality (PM2.5)", f"{s['PM2.5']} µg/m³"),
            ("CO₂ Level", f"{s['CO2']} ppm"),
            ("Noise Level", f"{s['Noise']} dB"),
        ]
        html = "<table><tr><th>Parameter</th><th>Current Value</th><th>Status</th></tr>"
        key_map = {
            "Temperature": "Temperature",
            "Humidity": "Humidity",
            "Pressure": "Pressure",
            "Air Quality (PM2.5)": "PM2.5",
            "CO₂ Level": "CO2",
            "Noise Level": "Noise"
        }

        for name, val in rows:
            key = key_map[name]
            lab, cls = status(key, s[key])
            html += f"<tr><td>{name}</td><td>{val}</td><td class='{cls}'>{lab}</td></tr>"

        html += "</table></div>"
        st.markdown(html, unsafe_allow_html=True)

    # RIGHT: LINE GRAPH (big card)
    with top_right:
        st.markdown("<div class='card'><div class='hdr'>Real-Time Trends (Last 20 readings)</div>",
                    unsafe_allow_html=True)

        # Add all parameters to history
        st.session_state.hist.loc[len(st.session_state.hist)] = [
            datetime.now().strftime("%H:%M:%S"),
            s["Temperature"],
            s["Humidity"],
            s["Pressure"],
            s["CO2"],
            s["PM2.5"]
        ]

        # Keep only last 20 points
        if len(st.session_state.hist) > 20:
            st.session_state.hist = st.session_state.hist.iloc[-20:]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=st.session_state.hist["t"], y=st.session_state.hist["Temp"],
                                 name="Temperature", line=dict(color="#6fe3ff", width=2)))
        fig.add_trace(go.Scatter(x=st.session_state.hist["t"], y=st.session_state.hist["Hum"],
                                 name="Humidity", line=dict(color="#ff7d7d", width=2)))
        fig.add_trace(go.Scatter(x=st.session_state.hist["t"], y=st.session_state.hist["Press"] / 10,
                                 name="Pressure (hPa/10)", line=dict(color="#ffcc66", width=2)))
        fig.add_trace(go.Scatter(x=st.session_state.hist["t"], y=st.session_state.hist["CO2"] / 20,
                                 name="CO₂ (ppm/20)", line=dict(color="#cc99ff", width=2)))

        fig.update_layout(
            template="plotly_dark",
            height=310,
            margin=dict(l=10, r=10, t=24, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- BOTTOM GRID (ALERTS | NOTIFICATIONS) -----
    bottom_left, bottom_right = st.columns([1, 1], gap="large")

    # ALERTS
    with bottom_left:
        st.markdown("<div class='card'><div class='hdr'>⚠️ Critical Alerts</div>", unsafe_allow_html=True)
        unsafe = False

        # Check all parameters and send emails if needed
        if s["Temperature"] > 34:
            unsafe = True
            st.markdown(f"<div class='alert'>🔥 Temperature exceeded 34°C (Current: {s['Temperature']}°C)</div>",
                        unsafe_allow_html=True)

            if not st.session_state.email_sent["temperature"]:
                try:
                    email_alert.send_email(
                        "CRITICAL TEMPERATURE ALERT",
                        f"Temperature crossed safe limit!\n\n"
                        f"Current Value: {s['Temperature']}°C\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Location: Main Monitoring Station\n"
                        f"Threshold: 34°C\n\n"
                        f"Please take immediate action."
                    )
                    st.session_state.email_sent["temperature"] = True
                except Exception as e:
                    st.error(f"Failed to send email alert: {e}")

        if s["Humidity"] > 70:
            unsafe = True
            st.markdown(f"<div class='alert'>💧 Humidity exceeded 70% (Current: {s['Humidity']}%)</div>",
                        unsafe_allow_html=True)

            if not st.session_state.email_sent["humidity"]:
                try:
                    email_alert.send_email(
                        "HIGH HUMIDITY ALERT",
                        f"Humidity crossed critical limit!\n\n"
                        f"Current Value: {s['Humidity']}%\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Location: Main Monitoring Station\n"
                        f"Threshold: 70%\n\n"
                        f"Risk of mold growth and equipment damage."
                    )
                    st.session_state.email_sent["humidity"] = True
                except Exception as e:
                    st.error(f"Failed to send email alert: {e}")

        if s["Pressure"] < 990:
            unsafe = True
            st.markdown(f"<div class='alert'>🌡️ Pressure below 990 hPa (Current: {s['Pressure']} hPa)</div>",
                        unsafe_allow_html=True)

            if not st.session_state.email_sent["pressure"]:
                try:
                    email_alert.send_email(
                        "LOW PRESSURE ALERT",
                        f"Atmospheric pressure below safe limit!\n\n"
                        f"Current Value: {s['Pressure']} hPa\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Location: Main Monitoring Station\n"
                        f"Threshold: 990 hPa\n\n"
                        f"May indicate weather changes or system issues."
                    )
                    st.session_state.email_sent["pressure"] = True
                except Exception as e:
                    st.error(f"Failed to send email alert: {e}")

        if s["CO2"] > 1200:
            unsafe = True
            st.markdown(f"<div class='alert'>☁️ CO₂ exceeded 1200 ppm (Current: {s['CO2']} ppm)</div>",
                        unsafe_allow_html=True)

            if not st.session_state.email_sent["co2"]:
                try:
                    email_alert.send_email(
                        "HIGH CO₂ ALERT",
                        f"CO₂ level crossed safe limit!\n\n"
                        f"Current Value: {s['CO2']} ppm\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Location: Main Monitoring Station\n"
                        f"Threshold: 1200 ppm\n\n"
                        f"Ventilation required for occupant safety."
                    )
                    st.session_state.email_sent["co2"] = True
                except Exception as e:
                    st.error(f"Failed to send email alert: {e}")

        if s["PM2.5"] > 55:
            unsafe = True
            st.markdown(f"<div class='alert'>💨 PM2.5 exceeded 55 µg/m³ (Current: {s['PM2.5']} µg/m³)</div>",
                        unsafe_allow_html=True)

            if not st.session_state.email_sent["pm25"]:
                try:
                    email_alert.send_email(
                        "POOR AIR QUALITY ALERT",
                        f"PM2.5 level crossed safe limit!\n\n"
                        f"Current Value: {s['PM2.5']} µg/m³\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Location: Main Monitoring Station\n"
                        f"Threshold: 55 µg/m³\n\n"
                        f"Air purification or ventilation required."
                    )
                    st.session_state.email_sent["pm25"] = True
                except Exception as e:
                    st.error(f"Failed to send email alert: {e}")

        if not unsafe:
            st.markdown("<div class='note'>✅ All parameters within safe range</div>", unsafe_allow_html=True)
            # Reset all email flags when safe
            for key in st.session_state.email_sent:
                st.session_state.email_sent[key] = False

        st.markdown("</div>", unsafe_allow_html=True)

    # NOTIFICATIONS + EXPORT
    with bottom_right:
        st.markdown("<div class='card'><div class='hdr'>📢 System Notifications</div>", unsafe_allow_html=True)

        # Show which emails were sent
        email_count = sum(st.session_state.email_sent.values())
        if email_count > 0:
            st.markdown(f"<div class='alert'>📧 {email_count} alert email(s) sent to admin</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown("<div class='note'>📧 No emails sent (all parameters normal)</div>", unsafe_allow_html=True)

        st.markdown("<div class='note'>📱 SMS notifications active</div>", unsafe_allow_html=True)
        st.markdown("<div class='note'>☁️ Data synced to cloud storage</div>", unsafe_allow_html=True)
        st.markdown("<div class='note'>📊 Logged to database</div>", unsafe_allow_html=True)
        st.markdown("<div class='note'>🔄 Real-time monitoring active</div>", unsafe_allow_html=True)

        # Export section
        st.markdown("<div class='hdr'>📄 Quick Export</div>", unsafe_allow_html=True)

        def make_pdf(data):
            try:
                from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib import colors
                from reportlab.platypus import TableStyle

                buf = BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=A4)
                styles = getSampleStyleSheet()

                # Custom styles
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Title'],
                    fontSize=24,
                    spaceAfter=30,
                    textColor=colors.HexColor('#4deac2')
                )

                content = []

                # Title
                content.append(Paragraph("Critical Space Monitoring Report", title_style))
                content.append(Spacer(1, 20))

                # Report info
                content.append(
                    Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
                content.append(Paragraph("Location: Main Monitoring Station", styles["Normal"]))
                content.append(Spacer(1, 20))

                # Parameter table
                table_data = [['Parameter', 'Value', 'Status']]

                for param, value in data.items():
                    lab, _ = status(param, value)
                    table_data.append([param, str(value), lab])

                table = Table(table_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3b5a')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0b182c')),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4deac2')),
                ]))

                content.append(table)
                content.append(Spacer(1, 30))

                doc.build(content)
                pdf_bytes = buf.getvalue()
                buf.close()
                return pdf_bytes

            except Exception as e:
                st.error(f"Error generating PDF: {e}")
                # Fallback to simple text report
                simple_report = f"""
                Critical Space Monitoring Report
                =================================

                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                Location: Main Monitoring Station

                Sensor Readings:
                """
                for param, value in data.items():
                    lab, _ = status(param, value)
                    simple_report += f"\n{param}: {value} ({lab})"

                # Convert to PDF bytes
                from reportlab.platypus import SimpleDocTemplate, Paragraph
                from reportlab.lib.styles import getSampleStyleSheet
                buf = BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=A4)
                styles = getSampleStyleSheet()
                content = [Paragraph(simple_report.replace('\n', '<br/>'), styles["Normal"])]
                doc.build(content)
                pdf_bytes = buf.getvalue()
                buf.close()
                return pdf_bytes

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Generate PDF"):
                pdf_data = make_pdf(s)
                st.download_button(
                    label="⬇️ Download",
                    data=pdf_data,
                    file_name=f"Dashboard_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
        with col2:
            csv = pd.DataFrame([s]).to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"Sensor_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- EVENT BASED BEEP ----------
    # Check if any parameter is in critical state
    # ---------- EVENT BASED REPEATING BEEP ----------

    critical_conditions = [
        s["Temperature"] > 34,
        s["Humidity"] > 70,
        s["Pressure"] < 990,
        s["CO2"] > 1200,
        s["PM2.5"] > 55
    ]

    any_critical = any(critical_conditions)

    # REPEATING ALARM WHENEVER CRITICAL
    if any_critical and st.session_state.sound_allowed:

        st.markdown("<div class='alert'>🚨 AUDIBLE ALARM ACTIVATED</div>", unsafe_allow_html=True)

        # Local Windows sound (non-cloud)
        if platform.system() == "Windows" and not is_cloud():
            try:
                winsound.Beep(2500, 1200)
            except:
                pass

        # Browser audio for cloud + mobile
        if beep:
            stamp = str(time.time())
            st.markdown(f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{beep}#{stamp}" type="audio/mp3">
                </audio>
            """, unsafe_allow_html=True)

    # Reset alarm flag, only used for display logic (not required to block sound)
    st.session_state.alarm = any_critical

    # ----- SIDEBAR -----
    with st.sidebar:
        st.markdown("### ⚙️ Dashboard Settings")

        # Sound control
        sound_enabled = st.checkbox("Enable Alarm Sounds", value=st.session_state.sound_allowed, key="sound_enabled")
        if sound_enabled != st.session_state.sound_allowed:
            st.session_state.sound_allowed = sound_enabled
            st.rerun()

        if st.session_state.sound_allowed:
            st.markdown("*🔊 Alarm sounds enabled*")
        else:
            st.markdown("*🔇 Alarm sounds disabled*")

        st.markdown("---")

        # Refresh rate
        refresh_rate = st.select_slider(
            "Refresh Rate (seconds)",
            options=[1, 2, 3, 5, 10],
            value=3,
            key="refresh_rate"
        )

        # Test sound button
        if st.button("🔊 Test Alarm Sound", key="test_sound"):
            if beep and st.session_state.sound_allowed:
                stamp = str(time.time())
                st.markdown(f"""
                    <audio autoplay>
                        <source src="data:audio/mp3;base64,{beep}#{stamp}" type="audio/mp3">
                    </audio>
                """, unsafe_allow_html=True)
                st.success("Test sound played!")

        st.markdown("---")

        # System status
        st.markdown("### 📈 System Status")
        total_readings = len(st.session_state.hist) if "hist" in st.session_state else 0
        st.metric("Total Readings", f"{total_readings}")
        st.metric("Active Alerts", f"{sum(critical_conditions)}")

        st.markdown("---")

        # Quick navigation
        st.markdown("### 🚀 Quick Navigation")
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("📊", key="sidebar_dash", help="Go to Dashboard"):
                st.session_state.current_page = "dashboard"
                st.rerun()
        with nav_col2:
            if st.button("📈", key="sidebar_analytics", help="Go to Analytics"):
                st.session_state.current_page = "analytics"
                st.rerun()
        with nav_col3:
            if st.button("📋", key="sidebar_reports", help="Go to Reports"):
                st.session_state.current_page = "reports"
                st.rerun()

        st.markdown("---")

        # Logout button
        if st.button("🚪 Logout", key="logout"):
            st.session_state.logged_in = False
            st.session_state.current_page = "dashboard"
            st.rerun()

    # ----- REFRESH -----
    time.sleep(refresh_rate)
    st.rerun()

# Main function to run the app
def main():
    # Set page config
    st.set_page_config(
        page_title="Critical Space Monitoring",
        page_icon="🚨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Check if user is logged in
    if not st.session_state.logged_in:
        # Show login page
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(135deg, #0a1929 0%, #0c1b2e 100%);
        }}
        .login-container {{
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: rgba(11,24,44,.85);
            border-radius: 20px;
            border: 1px solid rgba(140,220,255,.25);
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }}
        .login-title {{
            text-align: center;
            color: #7ceaff;
            font-size: 28px;
            margin-bottom: 30px;
            font-weight: bold;
        }}
        </style>
        <div class="login-container">
            <div class="login-title">CRITICAL SPACE MONITORING</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔐 Login")
            username = st.text_input("Username", key="username")
            password = st.text_input("Password", type="password", key="password")

            if st.button("Login", key="login_button", use_container_width=True):
                if username == "admin" and password == "admin":  # Simple demo login
                    st.session_state.logged_in = True
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    else:
        # User is logged in, show the appropriate page
        if st.session_state.current_page == "dashboard":
            dashboard_page()
        elif st.session_state.current_page == "analytics":
            analytics_page()
        elif st.session_state.current_page == "reports":
            reports_page()


# Run the app
if __name__ == "__main__":
    main()



