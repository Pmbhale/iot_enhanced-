import streamlit as st
from datetime import datetime
import base64
import time
from streamlit.components.v1 import html

# --- SOUND PLAYER ---
def play_sound(file):
    with open(file, "rb") as f:
        sound = base64.b64encode(f.read()).decode()

    html(f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{sound}" type="audio/mp3">
    </audio>
    """, height=0)


# -----------------------------
# CLEAN UI FIX (NO EXTRA GAPS)
# -----------------------------
st.markdown("""
<style>
/* Remove global padding/gaps */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 0rem !important;
}

section.main > div {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
}

/* Remove vertical whitespace between components */
div[data-testid="stVerticalBlock"] {
    gap: 0rem !important;
}

/* Center everything */
body {
    margin: 0;
}

/* Title spacing fix */
h1 {
    margin-bottom: 0.3rem !important;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# LOGIN PAGE
# -----------------------------
def login_page():

    params = st.query_params or {}

    # After Register Success
    if "register_success" in params:
        st.query_params.clear()
        play_sound("success.mp3")
        st.success("✅ Passkey Registered Successfully!")
        st.session_state.logged_in = True
        st.session_state.username = "Admin"
        time.sleep(1)
        st.rerun()

    # After Biometric Success
    if "bio_success" in params:
        st.query_params.clear()
        play_sound("success.mp3")
        st.success("✅ Biometric Authentication Successful!")
        st.session_state.logged_in = True
        st.session_state.username = "Admin"
        time.sleep(1)
        st.rerun()

    # -----------------------------
    # UI TITLE
    # -----------------------------
    st.markdown("<h1>🔐 Login Using Biometrics</h1>", unsafe_allow_html=True)

    # -----------------------------
    # REGISTER BUTTON (FIRST TIME)
    # -----------------------------
    html("""
        <div style='text-align:center; margin-top:5px;'>
          <button 
            id="registerBtn"
            style="
              background:#222;
              border:none;
              border-radius:8px;
              padding:12px 20px;
              color:white;
              font-size:14px;
              cursor:pointer;
              width:60%;
            ">
            🔐 Register Passkey (First Time)
          </button>
        </div>

        <script>
        document.addEventListener("DOMContentLoaded", () => {

            let btn = document.getElementById("registerBtn");
            if (!btn) return;

            btn.onclick = async () => {

                if (!window.PublicKeyCredential) {
                    alert("Your device does not support Biometrics.");
                    return;
                }

                try {
                    const pub = {
                        challenge: new Uint8Array(32),
                        rp: { name: "Secure Login" },
                        user: {
                            id: new Uint8Array(16),
                            name: "admin",
                            displayName: "Admin User"
                        },
                        pubKeyCredParams: [{ type: "public-key", alg: -7 }],
                        authenticatorSelection: { userVerification: "required" }
                    };

                    await navigator.credentials.create({ publicKey: pub });

                    window.location.href = "?register_success=1";

                } catch (err) {
                    alert("Registration Error: " + err);
                }
            };
        });
        </script>
    """, height=0)


    # -----------------------------
    # BIOMETRIC LOGIN BUTTON
    # -----------------------------
    html("""
        <div style='text-align:center; margin-top:15px;'>
          <button 
            id="bioLoginBtn"
            style="
              background: linear-gradient(90deg,#00ccff,#0066ff);
              border:none;
              border-radius:8px;
              padding:14px 20px;
              color:white;
              font-size:15px;
              cursor:pointer;
              width:60%;
            ">
            🆔 Login with Face ID / Fingerprint
          </button>
        </div>

        <script>
        document.addEventListener("DOMContentLoaded", () => {

            let btn = document.getElementById("bioLoginBtn");
            if (!btn) return;

            btn.onclick = async () => {

                if (!window.PublicKeyCredential) {
                    alert("Biometric Login Not Supported!");
                    return;
                }

                try {
                    await navigator.credentials.get({
                        publicKey: {
                            challenge: new Uint8Array(32),
                            userVerification: "required"
                        }
                    });

                    window.location.href = "?bio_success=1";

                } catch (err) {
                    alert("Authentication Error: " + err);
                }
            };
        });
        </script>
    """, height=0)


# -----------------------------
# MAIN FLOW
# -----------------------------
if __name__ == "__main__":

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()

    else:
        st.title(f"🚀 Welcome, {st.session_state.username}")
        st.success("You are logged in using biometrics!")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
