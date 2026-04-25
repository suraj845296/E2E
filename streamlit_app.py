import streamlit as st
import streamlit.components.v1 as components
import time
import threading
import hashlib
import os
import json
import urllib.parse
from pathlib import Path
import sqlite3
from datetime import datetime

st.set_page_config(
    page_title="E2E BY SURAJ OBEROY",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
#            DATABASE FUNCTIONS (Built-in - No external file needed)
# ============================================================

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # User config table
    c.execute('''CREATE TABLE IF NOT EXISTS user_config
                 (user_id INTEGER PRIMARY KEY,
                  chat_id TEXT,
                  name_prefix TEXT,
                  delay INTEGER DEFAULT 5,
                  cookies TEXT,
                  messages TEXT,
                  automation_running BOOLEAN DEFAULT 0,
                  admin_e2ee_thread_id TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
    """Create new user"""
    try:
        conn = sqlite3.connect('e2e_automation.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        user_id = c.lastrowid
        
        # Create default config for user
        c.execute("INSERT INTO user_config (user_id, chat_id, name_prefix, delay, cookies, messages) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, "", "", 5, "", ""))
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def verify_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_config(user_id):
    """Get user configuration"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT chat_id, name_prefix, delay, cookies, messages FROM user_config WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            'chat_id': result[0] or '',
            'name_prefix': result[1] or '',
            'delay': result[2] or 5,
            'cookies': result[3] or '',
            'messages': result[4] or ''
        }
    return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    """Update user configuration"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("""UPDATE user_config 
                 SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?
                 WHERE user_id = ?""",
              (chat_id, name_prefix, delay, cookies, messages, user_id))
    conn.commit()
    conn.close()

def get_username(user_id):
    """Get username by ID"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_automation_running(user_id):
    """Get automation running status"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT automation_running FROM user_config WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] == 1 if result else False

def set_automation_running(user_id, status):
    """Set automation running status"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("UPDATE user_config SET automation_running = ? WHERE user_id = ?", (1 if status else 0, user_id))
    conn.commit()
    conn.close()

def get_admin_e2ee_thread_id(user_id):
    """Get admin thread ID"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT admin_e2ee_thread_id FROM user_config WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_admin_e2ee_thread_id(user_id, thread_id, cookies, chat_type):
    """Set admin thread ID"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("UPDATE user_config SET admin_e2ee_thread_id = ? WHERE user_id = ?", (thread_id, user_id))
    conn.commit()
    conn.close()

# Initialize database
init_database()

# ============================================================
#            THEME CSS WITH BACKGROUND IMAGE
# ============================================================
normal_css = """
<style>
    /* Global background image */
    .stApp {
        background-image: url('https://i.ibb.co/1Y4DTdw4/your-image.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    
    /* Main container styling with semi-transparent background */
    .main .block-container {
        background: rgba(255, 255, 255, 0.92);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin: 1rem auto;
        backdrop-filter: blur(2px);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
    }
    
    .main-header h1 {
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    .prince-logo {
        width: 70px;
        height: 70px;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.9), rgba(118, 75, 162, 0.9));
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem auto;
        border: 3px solid white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .prince-logo span {
        font-size: 2.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(248, 249, 250, 0.95);
        border: 1px solid #ddd;
        border-radius: 8px;
        color: #333;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Labels */
    label {
        color: #333 !important;
        font-weight: 600 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(240, 242, 246, 0.9);
        border-radius: 10px;
        padding: 0.3rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 8px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #667eea;
        font-size: 2rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #555;
    }
    
    /* Console output */
    .console-output {
        background: rgba(30, 30, 30, 0.95);
        border-radius: 12px;
        padding: 1rem;
        color: #d4d4d4;
        font-family: 'Consolas', monospace;
        font-size: 0.85rem;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #333;
    }
    
    .console-line {
        border-left: 3px solid #667eea;
        padding: 0.3rem 0.8rem;
        margin: 0.3rem 0;
        color: #e0e0e0;
    }
    
    /* Footer */
    .footer {
        background: rgba(248, 249, 250, 0.9);
        border-top: 1px solid #dee2e6;
        color: #6c757d;
        text-align: center;
        padding: 1.5rem;
        margin-top: 2rem;
        border-radius: 12px 12px 0 0;
    }
    
    /* Sidebar with semi-transparent background */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(248, 249, 250, 0.95) 0%, rgba(233, 236, 239, 0.95) 100%);
        border-right: 1px solid #dee2e6;
        backdrop-filter: blur(5px);
    }
    
    [data-testid="stSidebar"] h3 {
        color: #333;
    }
    
    /* Success/Error/Warning messages */
    .stAlert {
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.95);
    }
    
    /* Divider */
    hr {
        margin: 1rem 0;
        border-color: #dee2e6;
    }
    
    /* Card-like elements */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 10px;
    }
</style>
"""

st.markdown(normal_css, unsafe_allow_html=True)

# ============================================================
#            APP CONSTANTS & STATE
# ============================================================

ADMIN_PASSWORD = "SURAJOBEROY"
WHATSAPP_NUMBER = "8452969216"
APPROVAL_FILE = "approved_keys.json"
PENDING_FILE = "pending_approvals.json"

def generate_user_key(username, password):
    combined = f"{username}:{password}"
    key_hash = hashlib.sha256(combined.encode()).hexdigest()[:8].upper()
    return f"KEY-{key_hash}"

def load_approved_keys():
    if os.path.exists(APPROVAL_FILE):
        try:
            with open(APPROVAL_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_approved_keys(keys):
    with open(APPROVAL_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def load_pending_approvals():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pending_approvals(pending):
    with open(PENDING_FILE, 'w') as f:
        json.dump(pending, f, indent=2)

def send_whatsapp_message(user_name, approval_key):
    message = f"👑 HELLO Suraj sir 👑\nMy name is {user_name}\nPlease approve my key:\n🔑 {approval_key}"
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMBER}&text={encoded_message}"
    return whatsapp_url

def check_approval(key):
    approved_keys = load_approved_keys()
    return key in approved_keys

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_key' not in st.session_state:
    st.session_state.user_key = None
if 'key_approved' not in st.session_state:
    st.session_state.key_approved = False
if 'approval_status' not in st.session_state:
    st.session_state.approval_status = 'not_requested'
if 'automation_running' not in st.session_state:
    st.session_state.automation_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'message_count' not in st.session_state:
    st.session_state.message_count = 0
if 'whatsapp_opened' not in st.session_state:
    st.session_state.whatsapp_opened = False
if 'auto_start_checked' not in st.session_state:
    st.session_state.auto_start_checked = False

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

if 'automation_state' not in st.session_state:
    st.session_state.automation_state = AutomationState()

def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    if automation_state:
        automation_state.logs.append(formatted_msg)
    else:
        st.session_state.logs.append(formatted_msg)

# ============================================================
#            AUTOMATION FUNCTIONS (Simplified for demo)
# ============================================================

def run_automation_with_notification(user_config, username, automation_state, user_id):
    """Simulated automation - In production, add your Selenium code here"""
    log_message(f"Starting automation for {username}...", automation_state)
    
    delay = user_config.get('delay', 5)
    messages_list = [msg.strip() for msg in user_config.get('messages', '').split('\n') if msg.strip()]
    
    if not messages_list:
        messages_list = ["Hello! This is an automated message."]
    
    msg_count = 0
    while automation_state.running and msg_count < 100:  # Limit for safety
        for msg in messages_list:
            if not automation_state.running:
                break
            
            prefix = user_config.get('name_prefix', '')
            full_msg = f"{prefix} {msg}" if prefix else msg
            
            log_message(f"Sending: {full_msg[:50]}...", automation_state)
            time.sleep(2)  # Simulate sending
            
            msg_count += 1
            automation_state.message_count = msg_count
            log_message(f"Message #{msg_count} sent. Waiting {delay}s...", automation_state)
            time.sleep(delay)
    
    log_message(f"Automation stopped. Total messages: {msg_count}", automation_state)

def start_automation(user_config, user_id):
    automation_state = st.session_state.automation_state
    
    if automation_state.running:
        return
    
    automation_state.running = True
    automation_state.message_count = 0
    automation_state.logs = []
    
    set_automation_running(user_id, True)
    
    username = get_username(user_id)
    thread = threading.Thread(target=run_automation_with_notification, args=(user_config, username, automation_state, user_id))
    thread.daemon = True
    thread.start()

def stop_automation(user_id):
    st.session_state.automation_state.running = False
    set_automation_running(user_id, False)

# ============================================================
#            UI PAGES
# ============================================================

def admin_panel():
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>ADMIN PANEL</h1>
        <p>KEY APPROVAL MANAGEMENT</p>
    </div>
    """, unsafe_allow_html=True)
    
    pending = load_pending_approvals()
    approved_keys = load_approved_keys()
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"**Total Approved Keys:** `{len(approved_keys)}`")
    with col2:
        st.warning(f"**Pending Approvals:** `{len(pending)}`")
    
    st.markdown("---")
    
    if pending:
        st.markdown("#### ⏳ Pending Approval Requests")
        for key, info in pending.items():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**👤 {info['name']}**")
            with col2:
                st.code(key)
            with col3:
                if st.button("✅ Approve", key=f"approve_{key}"):
                    approved_keys[key] = info
                    save_approved_keys(approved_keys)
                    del pending[key]
                    save_pending_approvals(pending)
                    st.success(f"✅ Approved {info['name']}!")
                    st.rerun()
            st.divider()
    else:
        st.info("✨ No pending approvals")
    
    if approved_keys:
        st.markdown("#### ✅ Approved Keys")
        for key, info in list(approved_keys.items())[:10]:
            st.markdown(f"**👑 {info['name']}**  \n`{key}`")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.approval_status = 'login'
        st.rerun()

def approval_request_page(user_key, username):
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>PREMIUM KEY APPROVAL REQUIRED</h1>
        <p>ONE MONTH 0 RS PAID</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.approval_status == 'not_requested':
        st.markdown("### 🔑 Request Access")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Your Unique Key:**  \n`{user_key}`")
        with col2:
            st.info(f"**Username:**  \n`{username}`")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📢 Request Approval", use_container_width=True):
                pending = load_pending_approvals()
                pending[user_key] = {
                    "name": username,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                save_pending_approvals(pending)
                st.session_state.approval_status = 'pending'
                st.session_state.whatsapp_opened = False
                st.rerun()
        with col2:
            if st.button("👑 Admin Panel", use_container_width=True):
                st.session_state.approval_status = 'admin_login'
                st.rerun()
    
    elif st.session_state.approval_status == 'pending':
        st.warning("⏳ Approval Pending...")
        st.info(f"**Your Key:** `{user_key}`")
        
        whatsapp_url = send_whatsapp_message(username, user_key)
        
        if not st.session_state.whatsapp_opened:
            whatsapp_js = f"""
            <script>
                setTimeout(function() {{
                    window.open('{whatsapp_url}', '_blank');
                }}, 500);
            </script>
            """
            components.html(whatsapp_js, height=0)
            st.session_state.whatsapp_opened = True
        
        st.success(f"📱 WhatsApp opening automatically for: **{username}**")
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <a href="{whatsapp_url}" target="_blank" style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                📱 Click Here to Open WhatsApp
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Check Approval Status", use_container_width=True):
                if check_approval(user_key):
                    st.session_state.key_approved = True
                    st.session_state.approval_status = 'approved'
                    st.success("✅ Approved! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⏳ Not approved yet. Please wait!")
        with col2:
            if st.button("◀️ Back", use_container_width=True):
                st.session_state.approval_status = 'not_requested'
                st.session_state.whatsapp_opened = False
                st.rerun()
    
    elif st.session_state.approval_status == 'admin_login':
        st.markdown("### 👑 Admin Login")
        admin_password = st.text_input("Enter Admin Password:", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔓 Login", use_container_width=True):
                if admin_password == ADMIN_PASSWORD:
                    st.session_state.approval_status = 'admin_panel'
                    st.rerun()
                else:
                    st.error("❌ Invalid password!")
        with col2:
            if st.button("◀️ Back", use_container_width=True):
                st.session_state.approval_status = 'not_requested'
                st.rerun()
    
    elif st.session_state.approval_status == 'admin_panel':
        admin_panel()

def login_page():
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>SURAJ OBEROY E2E SERVER</h1>
        <p>"seven billion smiles in this world but yours is my favorite___✨"</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.markdown("### Welcome Back!")
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", key="login_password", type="password", placeholder="Enter your password")
        
        if st.button("Login", key="login_btn", use_container_width=True):
            if username and password:
                user_id = verify_user(username, password)
                if user_id:
                    user_key = generate_user_key(username, password)
                    
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.session_state.user_key = user_key
                    
                    if check_approval(user_key):
                        st.session_state.key_approved = True
                        st.session_state.approval_status = 'approved'
                    else:
                        st.session_state.key_approved = False
                        st.session_state.approval_status = 'not_requested'
                    
                    st.success(f"✨ Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password!")
            else:
                st.warning("⚠️ Please enter both username and password")
    
    with tab2:
        st.markdown("### Create New Account")
        new_username = st.text_input("Choose Username", key="signup_username", placeholder="Choose a unique username")
        new_password = st.text_input("Choose Password", key="signup_password", type="password", placeholder="Create a strong password")
        confirm_password = st.text_input("Confirm Password", key="confirm_password", type="password", placeholder="Re-enter your password")
        
        if st.button("Create Account", key="signup_btn", use_container_width=True):
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    success, message = create_user(new_username, new_password)
                    if success:
                        st.success(f"✅ {message} Please login now!")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Passwords do not match!")
            else:
                st.warning("⚠️ Please fill all fields")

def main_app():
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>SURAJ OBEROY E2E OFFLINE</h1>
        <p>"seven billion smiles in this world but yours is my favorite___✨"</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="background: linear-gradient(135deg, #667eea15, #764ba215); border-radius: 12px; padding: 1rem;">
            <h3 style="color: #667eea; margin: 0;">👑 {st.session_state.username}</h3>
            <p style="color: #555; margin: 0.5rem 0; font-size: 0.8rem;">ID: {st.session_state.user_id}</p>
            <code style="background: #e9ecef; padding: 0.3rem; border-radius: 6px; font-size: 0.7rem; color: #333;">{st.session_state.user_key}</code>
            <p style="color: #28a745; margin-top: 0.5rem;">✅ Key Approved</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        if st.session_state.automation_state.running:
            stop_automation(st.session_state.user_id)
        
        for key in ['logged_in', 'user_id', 'username', 'user_key', 'key_approved', 
                    'automation_running', 'auto_start_checked', 'approval_status']:
            if key in st.session_state:
                if key == 'approval_status':
                    st.session_state[key] = 'not_requested'
                else:
                    st.session_state[key] = False if 'logged_in' not in key else False
        
        st.rerun()
    
    user_config = get_user_config(st.session_state.user_id)
    
    if user_config:
        tab1, tab2 = st.tabs(["⚙️ Configuration", "🚀 Automation"])
        
        with tab1:
            st.markdown("### Your Configuration")
            
            chat_id = st.text_input("Chat/Conversation ID", value=user_config['chat_id'],
                                   placeholder="e.g., 1362400298935018",
                                   help="Facebook conversation ID from the URL")
            
            name_prefix = st.text_input("Name Prefix", value=user_config['name_prefix'],
                                       placeholder="e.g., [END TO END]",
                                       help="Prefix to add before each message")
            
            delay = st.number_input("Delay (seconds)", min_value=1, max_value=300,
                                   value=user_config['delay'],
                                   help="Wait time between messages")
            
            messages = st.text_area("Messages (one per line)",
                                   value=user_config['messages'],
                                   placeholder="Enter each message on a new line",
                                   height=150,
                                   help="Enter each message on a new line")
            
            if st.button("💾 Save Configuration", use_container_width=True):
                update_user_config(
                    st.session_state.user_id,
                    chat_id,
                    name_prefix,
                    delay,
                    "",
                    messages
                )
                st.success("✅ Configuration saved successfully!")
                st.rerun()
        
        with tab2:
            st.markdown("### Automation Control")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📨 Messages Sent", st.session_state.automation_state.message_count)
            with col2:
                status = "🟢 Running" if st.session_state.automation_state.running else "🔴 Stopped"
                st.metric("📊 Status", status)
            with col3:
                user_config = get_user_config(st.session_state.user_id)
                chat_preview = user_config['chat_id'][:10] + "..." if user_config['chat_id'] else "Not Set"
                st.metric("💬 Chat ID", chat_preview)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("▶️ Start Automation", disabled=st.session_state.automation_state.running, use_container_width=True):
                    user_config = get_user_config(st.session_state.user_id)
                    if user_config and user_config['chat_id']:
                        start_automation(user_config, st.session_state.user_id)
                        st.success("✅ Automation started!")
                        st.rerun()
                    else:
                        st.error("⚠️ Please set Chat ID in Configuration first!")
            
            with col2:
                if st.button("⏹️ Stop Automation", disabled=not st.session_state.automation_state.running, use_container_width=True):
                    stop_automation(st.session_state.user_id)
                    st.warning("⏹️ Automation stopped!")
                    st.rerun()
            
            if st.session_state.automation_state.logs:
                st.markdown("### 📟 Live Console Output")
                logs_html = '<div class="console-output">'
                for log in st.session_state.automation_state.logs[-30:]:
                    logs_html += f'<div class="console-line">{log}</div>'
                logs_html += '</div>'
                st.markdown(logs_html, unsafe_allow_html=True)

# ============================================================
#            MAIN ROUTING
# ============================================================

if not st.session_state.logged_in:
    login_page()
elif not st.session_state.key_approved:
    approval_request_page(st.session_state.user_key, st.session_state.username)
else:
    main_app()

st.markdown("""
<div class="footer">
    Made with ❤️ by <span style="color: #667eea; font-weight: bold;">SURAJ OBEROY</span> | © 2026
</div>
""", unsafe_allow_html=True)
