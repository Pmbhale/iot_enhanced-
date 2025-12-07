# login.py
# Face-login version (single admin user)
# Put your registered face image in the same folder with filename: admin_face.jpg
# Uses OpenCV (cv2) + numpy + PIL. If cv2 is missing: `pip install opencv-python`
# Keeps original UI styling intact; removes fingerprint flow.

import streamlit as st
from datetime import datetime
import base64
import time
from streamlit.components.v1 import html
from PIL import Image
import numpy as np

# Try to import cv2 and give a helpful message if missing
try:
    import cv2
except Exception as e:
    st.error("OpenCV (cv2) is required for face comparison. Install with `pip install opencv-python` and restart.")
    raise

# ---------------------------
# Utility: sound player
# ---------------------------
def play_sound(file):
    try:
        with open(file, "rb") as f:
            sound = base64.b64encode(f.read()).decode()
        html(f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{sound}" type="audio/mp3">
        </audio>
        """, height=0)
    except Exception:
        # fallback beep
        html("""
        <script>
        function playBeep() {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        }
        playBeep();
        </script>
        """, height=0)

# ---------------------------
# Image comparison helpers
# ---------------------------
def pil_to_cv2(img_pil):
    """Convert PIL image to OpenCV BGR"""
    img = np.array(img_pil.convert("RGB"))
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

def resize_for_compare(img_cv, size=(400,400)):
    return cv2.resize(img_cv, size, interpolation=cv2.INTER_AREA)

def hist_score(img1, img2):
    """Compare HSV histograms; return normalized score in [0,1] (1 = perfect)"""
    img1 = resize_for_compare(img1)
    img2 = resize_for_compare(img2)
    hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
    # use H and S channels
    hist1 = cv2.calcHist([hsv1], [0,1], None, [50,60], [0,180,0,256])
    hist2 = cv2.calcHist([hsv2], [0,1], None, [50,60], [0,180,0,256])
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)
    # compare correlation [-1,1] -> convert to [0,1]
    corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    # clamp and normalize
    score = (corr + 1.0) / 2.0
    return float(np.clip(score, 0.0, 1.0))

def orb_match_score(img1, img2):
    """Compute ORB keypoint matches ratio -> returns value in [0,1]"""
    img1_gray = cv2.cvtColor(resize_for_compare(img1), cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(resize_for_compare(img2), cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(nfeatures=1000)
    kp1, des1 = orb.detectAndCompute(img1_gray, None)
    kp2, des2 = orb.detectAndCompute(img2_gray, None)
    if des1 is None or des2 is None or len(kp1) < 5 or len(kp2) < 5:
        return 0.0
    # BFMatcher with Hamming
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    if not matches:
        return 0.0
    matches = sorted(matches, key=lambda x: x.distance)
    # good matches threshold: distance < 70
    good = [m for m in matches if m.distance < 70]
    # ratio relative to min keypoints count
    denom = min(len(kp1), len(kp2))
    if denom == 0:
        return 0.0
    ratio = len(good) / denom
    return float(np.clip(ratio, 0.0, 1.0))

def combined_similarity(img_cv, admin_cv):
    """Weighted combination of histogram correlation and ORB match ratio"""
    h = hist_score(img_cv, admin_cv)
    o = orb_match_score(img_cv, admin_cv)
    # weights tuned for single-user reliability
    return 0.6 * h + 0.4 * o, h, o

# ---------------------------
# Main login page
# ---------------------------
def login_page():
    st.markdown("""
    <style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, 
            #0a0e17 0%, 
            #121828 25%, 
            #0f172a 50%, 
            #0a0e17 100%);
        min-height: 100vh;
    }

    /* Center everything */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Futuristic scan lines overlay */
    .scanlines {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            transparent 50%,
            rgba(0, 150, 255, 0.03) 50%
        );
        background-size: 100% 4px;
        pointer-events: none;
        z-index: 1;
        opacity: 0.4;
    }

    /* Main login container */
    .login-container {
        position: relative;
        background: rgba(10, 14, 23, 0.85);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 150, 255, 0.2);
        border-radius: 16px;
        padding: 40px;
        width: 420px;
        margin: 0 auto;
        box-shadow: 
            0 0 60px rgba(0, 100, 255, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        z-index: 2;
        margin-bottom: 30px;
    }

    /* Glowing border effect */
    .login-container::before {
        content: '';
        position: absolute;
        top: -1px;
        left: -1px;
        right: -1px;
        bottom: -1px;
        background: linear-gradient(45deg, 
            #0066ff, 
            #00ccff, 
            #0066ff);
        border-radius: 17px;
        z-index: -1;
        opacity: 0.3;
        filter: blur(8px);
    }

    /* Header styles */
    .system-header {
        text-align: center;
        margin-bottom: 30px;
        position: relative;
    }

    .system-title {
        background: linear-gradient(90deg, 
            #00ccff 0%, 
            #0066ff 50%, 
            #00ccff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 8px;
        font-family: 'Arial', sans-serif;
    }

    .system-subtitle {
        color: #8892b0;
        font-size: 12px;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    /* Logo container */
    .logo-container {
        width: 80px;
        height: 80px;
        margin: 0 auto 20px;
        background: linear-gradient(135deg, 
            rgba(0, 102, 255, 0.1) 0%, 
            rgba(0, 204, 255, 0.1) 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(0, 150, 255, 0.3);
        box-shadow: 0 0 30px rgba(0, 150, 255, 0.2);
    }

    .logo-container img {
        width: 50px;
        height: 50px;
        filter: drop-shadow(0 0 10px rgba(0, 150, 255, 0.5));
    }

    /* Status indicator */
    .status-indicator {
        position: relative;
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #00ff88;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 10px #00ff88;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 255, 136, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
    }

    /* Input fields */
    .stTextInput > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(0, 150, 255, 0.3) !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput > div > div:hover {
        border-color: rgba(0, 200, 255, 0.5) !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }

    .stTextInput > div > div:focus-within {
        border-color: #00ccff !important;
        box-shadow: 0 0 15px rgba(0, 200, 255, 0.3) !important;
        background: rgba(255, 255, 255, 0.1) !important;
    }

    .stTextInput input {
        color: #ffffff !important;
        font-size: 14px !important;
        padding: 14px !important;
        background: transparent !important;
    }

    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.5) !important;
    }

    /* Labels */
    .input-label {
        color: #8892b0;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        display: block;
    }

    /* Button styling */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(90deg, 
            #0066ff 0%, 
            #00ccff 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 16px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        margin-top: 10px !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(0, 150, 255, 0.4) !important;
    }

    /* Time display */
    .time-display {
        background: rgba(0, 102, 255, 0.1);
        border: 1px solid rgba(0, 150, 255, 0.2);
        border-radius: 6px;
        padding: 10px 15px;
        margin: 20px 0;
        text-align: center;
    }

    .time-text {
        color: #00ccff;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        letter-spacing: 1px;
    }

    /* Footer */
    .footer {
        text-align: center;
        margin-top: 0px !important;
        padding-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        color: #8892b0;
        font-size: 11px;
        letter-spacing: 1px;
    }

    /* Fingerprint removed - replaced by camera capture button/controls */

    </style>

    <!-- Scanlines overlay -->
    <div class="scanlines"></div>
    """, unsafe_allow_html=True)

    # layout columns to center the UI
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # load logo (same as before)
        logo_html = ""
        logo_paths = ["logo.png", "Logo.png", "LOGO.png", "./logo.png"]
        for path in logo_paths:
            try:
                with open(path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                logo_html = f'<img src="data:image/png;base64,{logo_data}" alt="CSMS Logo">'
                break
            except Exception:
                continue
        if not logo_html:
            logo_html = '<div style="color: #00ccff; font-size: 32px;">🚀</div>'

        # main card (logo + title + time) - kept inside the same login-container
        st.markdown(f"""
        <div class="login-container">
          <div class="system-header">
            <div class="logo-container">
              {logo_html}
            </div>
            <div class="system-title">CRITICAL SPACE MONITORING SYSTEM</div>
            <div class="system-subtitle">CSMS v2.1.7 | Face Login Enabled</div>
          </div>

          <div class="time-display">
            <div class="time-text">🕒 {datetime.utcnow().strftime("%Y-%m-%d | %H:%M:%S")} UTC</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ---- form: username/password
        USER = "admin"
        PASS = "CSMS@2024"

        with st.form("login_form", clear_on_submit=False):
            form_container = st.container()
            with form_container:
                st.markdown('<div class="input-label">USER IDENTIFICATION</div>', unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="ENTER USERNAME", label_visibility="collapsed", key="username_input")
                st.markdown('<div class="input-label">SECURITY PASSPHRASE</div>', unsafe_allow_html=True)
                password = st.text_input("Password", type="password", placeholder="ENTER ENCRYPTED KEY", label_visibility="collapsed", key="password_input")
                submitted = st.form_submit_button("⚡ INITIATE SYSTEM ACCESS", use_container_width=True)

        # ---- camera capture for face login
        # ---------- FACE LOGIN SECTION (FULL BLOCK, NO CHANGES REMOVED) ----------

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("Or authenticate using your face (admin only). Click Capture and allow camera access.")

        # Initialize camera toggle
        if "show_camera" not in st.session_state:
            st.session_state.show_camera = False

        # Show camera only after button click
        if not st.session_state.show_camera:
            if st.button("📸 Capture Face to Login", use_container_width=True):
                st.session_state.show_camera = True
                st.rerun()
        else:
            # CAMERA OPENS ONLY NOW
            captured_file = st.camera_input("Capture your face to login", key="camera_capture")

            # Load admin face template
            admin_face_loaded = False
            admin_face_cv = None
            try:
                admin_pil = Image.open("admin_face.jpeg")
                admin_face_cv = pil_to_cv2(admin_pil)  # BGR OpenCV
                admin_face_loaded = True
            except FileNotFoundError:
                st.warning(
                    "Registered face image `admin_face.jpg` not found. Place your admin face image in the app folder with the name `admin_face.jpg` to enable face login.")
            except Exception as e:
                st.error(f"Error loading admin_face.jpg: {e}")

            # If camera capture provided, compare
            if captured_file is not None and admin_face_loaded:
                try:
                    user_pil = Image.open(captured_file)
                    user_cv = pil_to_cv2(user_pil)

                    sim, hscore, oratio = combined_similarity(user_cv, admin_face_cv)

                    MATCH_THRESHOLD = 0.55  # combined
                    HIST_THRESHOLD = 0.50  # fallback

                    st.write(f"Similarity: **{sim:.2f}**  — (hist {hscore:.2f}, orb {oratio:.2f})")

                    # ---- STRONG SECURITY THRESHOLDS ----
                    # ---- FINAL WORKING SECURITY THRESHOLDS ----
                    # ---------------- STRICTEST SAFE LOGIN CHECK ----------------

                    COMBINED_MIN = 0.50
                    HIST_MIN = 0.45
                    ORB_MIN = 0.39

                    # Login allowed ONLY if ALL three checks pass
                    if sim >= COMBINED_MIN and hscore >= HIST_MIN and oratio >= ORB_MIN:

                        play_sound("success.mp3")

                        with st.spinner("🔐 Face verified..."):
                            time.sleep(1)

                        st.success("✅ Face recognized. Access granted.")

                        st.session_state.logged_in = True
                        st.session_state.username = USER

                        time.sleep(1.2)
                        st.rerun()

                    else:
                        st.error(
                            "❌ Face not recognized. This system can only be unlocked by the registered admin face.")


                except Exception as e:
                    st.error(f"Face comparison error: {e}")

        # ---- handle password login
        if submitted:
            if username == USER and password == PASS:
                play_sound("success.mp3")
                with st.spinner("🔐 Authenticating..."):
                    time.sleep(1)
                st.markdown(f"""
                <div style="margin-top:10px;" class="success">
                    <div style="color:#00ff88; font-weight:700;">✓ ACCESS GRANTED • WELCOME, {username.upper()}</div>
                </div>
                """, unsafe_allow_html=True)
                st.session_state.logged_in = True
                st.session_state.username = username
                time.sleep(1.2)
                st.rerun()

            else:
                st.markdown(f"""
                <div class="warning" style="margin-top:10px;">
                    <div class="warning-text">⚠️ ACCESS DENIED • INVALID CREDENTIALS</div>
                </div>
                """, unsafe_allow_html=True)

        # footer (kept same)
        st.markdown("""
        <div class="footer">
            <div>
                <span class="status-indicator"></span> SYSTEM STATUS: <span style="color: #00ff88;">ACTIVE & SECURE</span>
            </div>
            <br>
            <div>
                © 2024 CSMS • ALL ACTIVITIES ARE MONITORED AND LOGGED
            </div>
            <div>
                ⚠️ UNAUTHORIZED ACCESS ATTEMPTS WILL BE REPORTED
            </div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------
# Dashboard (unchanged)
# ---------------------------
def dashboard_page():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0a0e17 0%, #121828 100%);
    }

    .dashboard-header {
        background: linear-gradient(90deg, #00ccff, #0066ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 20px 0;
        border-bottom: 1px solid rgba(0, 150, 255, 0.2);
        margin-bottom: 30px;
    }

    .metric-card {
        background: rgba(10, 14, 23, 0.8);
        border: 1px solid rgba(0, 150, 255, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }

    .logout-btn {
        background: linear-gradient(90deg, #ff6b6b, #ff8e53) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        color: white !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # header with logout
    col1, col2, col3 = st.columns([3,1,1])
    with col1:
        st.markdown(f'<h1 class="dashboard-header">🚀 Welcome to CSMS, {st.session_state.username}!</h1>', unsafe_allow_html=True)
    with col3:
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.success("✅ You have successfully logged into the Critical Space Monitoring System.")

    st.markdown("### 📊 System Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color:#00ccff; margin:0;">System Status</h3>
            <h1 style="color:#00ff88; margin:10px 0;">🟢 ACTIVE</h1>
            <p style="color:#8892b0; margin:0; font-size:12px;">All systems operational</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color:#00ccff; margin:0;">Security Level</h3>
            <h1 style="color:#00ff88; margin:10px 0;">MAXIMUM</h1>
            <p style="color:#8892b0; margin:0; font-size:12px;">Biometric verified</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color:#00ccff; margin:0;">CPU Usage</h3>
            <h1 style="color:#00ccff; margin:10px 0;">42%</h1>
            <p style="color:#8892b0; margin:0; font-size:12px;">Normal operation</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color:#00ccff; margin:0;">Memory</h3>
            <h1 style="color:#00ccff; margin:10px 0;">78%</h1>
            <p style="color:#8892b0; margin:0; font-size:12px;">Optimal</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 View Detailed Metrics", use_container_width=True):
            st.info("Detailed system metrics would appear here")
    with col2:
        if st.button("🔒 Security Dashboard", use_container_width=True):
            st.info("Security dashboard would appear here")
    with col3:
        if st.button("📋 Generate Report", use_container_width=True):
            st.info("Report generation would start here")

    st.markdown("---")
    st.markdown("### 📈 Recent Activity")
    activity_data = [
        {"time": "10:30 AM", "event": "Biometric Login", "user": "admin", "status": "✅ Success"},
        {"time": "10:25 AM", "event": "System Check", "user": "system", "status": "✅ Completed"},
        {"time": "10:15 AM", "event": "Database Backup", "user": "system", "status": "✅ Completed"},
        {"time": "09:45 AM", "event": "Network Scan", "user": "security", "status": "✅ No threats"},
    ]
    for activity in activity_data:
        col1, col2, col3, col4 = st.columns([2,3,2,2])
        with col1:
            st.write(f"🕒 {activity['time']}")
        with col2:
            st.write(f"**{activity['event']}**")
        with col3:
            st.write(activity['user'])
        with col4:
            st.write(f"{activity['status']}")

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if not st.session_state.logged_in:
        login_page()
    else:
        dashboard_page()
