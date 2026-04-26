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
                  user_key TEXT,
                  key_approved BOOLEAN DEFAULT 0,
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
    
    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  is_super_admin BOOLEAN DEFAULT 0)''')
    
    # Check if default admin exists
    c.execute("SELECT * FROM admin WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO admin (username, password, is_super_admin) VALUES (?, ?, ?)",
                  ('admin', 'admin123', 1))
    
    conn.commit()
    conn.close()

def create_user(username, password):
    """Create new user"""
    try:
        user_key = generate_user_key(username, password)
        conn = sqlite3.connect('e2e_automation.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, user_key, key_approved) VALUES (?, ?, ?, ?)", 
                  (username, password, user_key, 0))
        user_id = c.lastrowid
        
        # Create default config for user
        c.execute("INSERT INTO user_config (user_id, chat_id, name_prefix, delay, cookies, messages) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, "", "", 5, "", ""))
        conn.commit()
        conn.close()
        return True, "Account created successfully! Please wait for admin approval."
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def verify_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT id, user_key, key_approved FROM users WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    conn.close()
    return result if result else None

def verify_admin(username, password):
    """Verify admin credentials"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT id, username, is_super_admin FROM admin WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    conn.close()
    return result if result else None

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

def get_all_pending_users():
    """Get all users pending approval"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT id, username, user_key, created_at FROM users WHERE key_approved = 0 ORDER BY created_at DESC")
    result = c.fetchall()
    conn.close()
    return result

def get_all_approved_users():
    """Get all approved users"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT id, username, user_key, created_at FROM users WHERE key_approved = 1 ORDER BY created_at DESC")
    result = c.fetchall()
    conn.close()
    return result

def approve_user(user_id):
    """Approve a user"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("UPDATE users SET key_approved = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def reject_user(user_id):
    """Reject/Delete a user"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("DELETE FROM user_config WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def generate_user_key(username, password):
    combined = f"{username}:{password}"
    key_hash = hashlib.sha256(combined.encode()).hexdigest()[:8].upper()
    return f"KEY-{key_hash}"

# Initialize database
init_database()

# ============================================================
#            NORMAL THEME CSS
# ============================================================
normal_css = """
<style>
    /* Main container styling */
    .main .block-container {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin: 1rem auto;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
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
        background: linear-gradient(135deg, #667eea, #764ba2);
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
        background: #f8f9fa;
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
        background: #f0f2f6;
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
        background: #1e1e1e;
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
        background: #f8f9fa;
        border-top: 1px solid #dee2e6;
        color: #6c757d;
        text-align: center;
        padding: 1.5rem;
        margin-top: 2rem;
        border-radius: 12px 12px 0 0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-right: 1px solid #dee2e6;
    }
    
    [data-testid="stSidebar"] h3 {
        color: #333;
    }
    
    /* Success/Error/Warning messages */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Divider */
    hr {
        margin: 1rem 0;
        border-color: #dee2e6;
    }
    
    /* Card styling */
    .user-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
</style>
"""

st.markdown(normal_css, unsafe_allow_html=True)

# ============================================================
#            APP CONSTANTS & STATE
# ============================================================

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_key' not in st.session_state:
    st.session_state.user_key = None
if 'key_approved' not in st.session_state:
    st.session_state.key_approved = False
if 'automation_running' not in st.session_state:
    st.session_state.automation_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'message_count' not in st.session_state:
    st.session_state.message_count = 0

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
    while automation_state.running and msg_count < 100:
        for msg in messages_list:
            if not automation_state.running:
                break
            
            prefix = user_config.get('name_prefix', '')
            full_msg = f"{prefix} {msg}" if prefix else msg
            
            log_message(f"Sending: {full_msg[:50]}...", automation_state)
            time.sleep(2)
            
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
#            ADMIN PANEL
# ============================================================

def admin_panel():
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>ADMIN PANEL</h1>
        <p>User Management & Key Approval System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Admin info in sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="background: linear-gradient(135deg, #667eea15, #764ba215); border-radius: 12px; padding: 1rem;">
            <h3 style="color: #667eea; margin: 0;">👑 Admin</h3>
            <p style="color: #555; margin: 0.5rem 0; font-size: 0.9rem;">{st.session_state.username}</p>
            <p style="color: #28a745; margin-top: 0.5rem;">✅ Super Admin</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Admin Logout", use_container_width=True):
        for key in ['logged_in', 'is_admin', 'user_id', 'username', 'user_key', 'key_approved']:
            if key in st.session_state:
                st.session_state[key] = False if key != 'key_approved' else False
        st.rerun()
    
    # Get statistics
    pending_users = get_all_pending_users()
    approved_users = get_all_approved_users()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Total Users", len(approved_users) + len(pending_users))
    with col2:
        st.metric("⏳ Pending Approval", len(pending_users))
    with col3:
        st.metric("✅ Approved Users", len(approved_users))
    
    st.markdown("---")
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["⏳ Pending Approvals", "✅ Approved Users", "📊 Activity Log"])
    
    with tab1:
        if pending_users:
            st.markdown("### 📋 Users Waiting for Approval")
            for user in pending_users:
                user_id, username, user_key, created_at = user
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
                    with col1:
                        st.markdown(f"**👤 {username}**")
                    with col2:
                        st.code(user_key, language="text")
                    with col3:
                        st.caption(f"📅 {created_at[:10]}")
                    with col4:
                        approve_btn = st.button("✅ Approve", key=f"approve_{user_id}")
                        reject_btn = st.button("❌ Reject", key=f"reject_{user_id}")
                        
                        if approve_btn:
                            approve_user(user_id)
                            st.success(f"✅ Approved {username}!")
                            time.sleep(0.5)
                            st.rerun()
                        
                        if reject_btn:
                            reject_user(user_id)
                            st.warning(f"❌ Rejected {username}!")
                            time.sleep(0.5)
                            st.rerun()
                    st.divider()
        else:
            st.info("✨ No pending approvals! All users are approved.")
    
    with tab2:
        if approved_users:
            st.markdown("### ✅ Approved Users List")
            for user in approved_users:
                user_id, username, user_key, created_at = user
                with st.container():
                    col1, col2, col3 = st.columns([2, 3, 2])
                    with col1:
                        st.markdown(f"**👑 {username}**")
                    with col2:
                        st.code(user_key, language="text")
                    with col3:
                        st.caption(f"📅 {created_at[:10]}")
                    st.divider()
        else:
            st.info("📭 No approved users yet.")
    
    with tab3:
        st.markdown("### 📝 Admin Activity")
        st.info("Admin actions are logged here (coming soon)")

# ============================================================
#            USER PAGES
# ============================================================

def user_login_page():
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>SURAJ OBEROY E2E SERVER</h1>
        <p>"seven billion smiles in this world but yours is my favorite___✨"</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 User Login", "📝 User Sign Up"])
        
        with tab1:
            st.markdown("### Welcome Back!")
            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", key="login_password", type="password", placeholder="Enter your password")
            
            if st.button("Login", key="login_btn", use_container_width=True):
                if username and password:
                    result = verify_user(username, password)
                    if result:
                        user_id, user_key, key_approved = result
                        
                        st.session_state.logged_in = True
                        st.session_state.is_admin = False
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.user_key = user_key
                        st.session_state.key_approved = bool(key_approved)
                        
                        if key_approved:
                            st.success(f"✨ Welcome back, {username}!")
                        else:
                            st.warning("⏳ Your account is pending admin approval!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password!")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        with tab2:
            st.markdown("### Create New Account")
            st.info("📝 Sign up and wait for admin approval to get access")
            new_username = st.text_input("Choose Username", key="signup_username", placeholder="Choose a unique username")
            new_password = st.text_input("Choose Password", key="signup_password", type="password", placeholder="Create a strong password")
            confirm_password = st.text_input("Confirm Password", key="confirm_password", type="password", placeholder="Re-enter your password")
            
            if st.button("Create Account", key="signup_btn", use_container_width=True):
                if new_username and new_password and confirm_password:
                    if new_password == confirm_password:
                        success, message = create_user(new_username, new_password)
                        if success:
                            st.success(f"✅ {message}")
                            st.info("📱 Admin will be notified. Please wait for approval.")
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Passwords do not match!")
                else:
                    st.warning("⚠️ Please fill all fields")

def user_pending_page():
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>ACCOUNT PENDING APPROVAL</h1>
        <p>Your account is waiting for admin approval</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("⏳ **Your account is pending admin approval!**")
        st.info(f"""
        **Username:** {st.session_state.username}
        
        **Your Key:** `{st.session_state.user_key}`
        
        Please wait for the admin to approve your account. You will be notified once approved.
        """)
        
        if st.button("🔄 Check Approval Status", use_container_width=True):
            result = verify_user(st.session_state.username, st.session_state.password if 'password' in st.session_state else '')
            if result:
                user_id, user_key, key_approved = result
                if key_approved:
                    st.session_state.key_approved = True
                    st.success("✅ Your account has been approved! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("⏳ Still pending approval. Please wait.")
        
        if st.button("🚪 Logout", use_container_width=True):
            for key in ['logged_in', 'user_id', 'username', 'user_key', 'key_approved']:
                st.session_state[key] = False
            st.rerun()

def user_main_app():
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
        
        for key in ['logged_in', 'user_id', 'username', 'user_key', 'key_approved', 'automation_running']:
            if key in st.session_state:
                st.session_state[key] = False
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
#            SEPARATE ADMIN LOGIN PAGE
# ============================================================

def admin_login_page():
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>ADMIN LOGIN</h1>
        <p>Authorized Access Only</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Admin Authentication")
        admin_username = st.text_input("Admin Username", key="admin_username", placeholder="Enter admin username")
        admin_password = st.text_input("Admin Password", key="admin_password", type="password", placeholder="Enter admin password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔓 Login as Admin", use_container_width=True):
                if admin_username and admin_password:
                    result = verify_admin(admin_username, admin_password)
                    if result:
                        admin_id, admin_name, is_super = result
                        st.session_state.logged_in = True
                        st.session_state.is_admin = True
                        st.session_state.username = admin_name
                        st.session_state.user_id = admin_id
                        st.success(f"✨ Welcome Admin, {admin_name}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid admin credentials!")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        with col2:
            if st.button("◀️ Back to User Login", use_container_width=True):
                st.session_state.show_admin_login = False
                st.rerun()
        
        st.markdown("---")
        st.caption("Default Admin Credentials: admin / admin123")

# ============================================================
#            MAIN ROUTING
# ============================================================

# Show admin login toggle button on main login page
if not st.session_state.logged_in:
    # Check if we're showing admin login
    if 'show_admin_login' not in st.session_state:
        st.session_state.show_admin_login = False
    
    if st.session_state.show_admin_login:
        admin_login_page()
    else:
        # Show user login with admin button
        user_login_page()
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("👑 Admin Login", use_container_width=True):
                st.session_state.show_admin_login = True
                st.rerun()

elif st.session_state.is_admin:
    # Show admin panel
    admin_panel()
elif not st.session_state.key_approved:
    # Show pending approval page for users
    user_pending_page()
else:
    # Show main app for approved users
    user_main_app()

st.markdown("""
<div class="footer">
    Made with ❤️ by <span style="color: #667eea; font-weight: bold;">SURAJ OBEROY</span> | © 2026
</div>
""", unsafe_allow_html=True)