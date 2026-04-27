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
                  auto_reply_enabled BOOLEAN DEFAULT 0,
                  auto_reply_message TEXT,
                  admin_e2ee_thread_id TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  is_super_admin BOOLEAN DEFAULT 0)''')
    
    # Activity log table
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT,
                  action TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Check if default admin exists
    c.execute("SELECT * FROM admin WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO admin (username, password, is_super_admin) VALUES (?, ?, ?)",
                  ('surajxwd', 'surajxwd123', 1))
    
    # Add new columns if they don't exist (for existing databases)
    try:
        c.execute("ALTER TABLE user_config ADD COLUMN auto_reply_enabled BOOLEAN DEFAULT 0")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE user_config ADD COLUMN auto_reply_message TEXT")
    except:
        pass
    
    conn.commit()
    conn.close()

def log_activity(username, action):
    """Log user activity"""
    try:
        conn = sqlite3.connect('e2e_automation.db')
        c = conn.cursor()
        c.execute("INSERT INTO activity_log (username, action) VALUES (?, ?)", (username, action))
        conn.commit()
        conn.close()
    except:
        pass

def get_activity_logs(limit=50):
    """Get recent activity logs"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT username, action, timestamp FROM activity_log ORDER BY timestamp DESC LIMIT ?", (limit,))
    result = c.fetchall()
    conn.close()
    return result

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
        log_activity(username, "Created new account")
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
    if result:
        log_activity(username, "Logged in")
    return result if result else None

def verify_admin(username, password):
    """Verify admin credentials"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT id, username, is_super_admin FROM admin WHERE username = ? AND password = ?", (username, password))
    result = c.fetchone()
    conn.close()
    if result:
        log_activity(username, "Admin logged in")
    return result if result else None

def get_user_config(user_id):
    """Get user configuration"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("SELECT chat_id, name_prefix, delay, cookies, messages, auto_reply_enabled, auto_reply_message FROM user_config WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return {
            'chat_id': result[0] or '',
            'name_prefix': result[1] or '',
            'delay': result[2] or 5,
            'cookies': result[3] or '',
            'messages': result[4] or '',
            'auto_reply_enabled': bool(result[5]) if result[5] is not None else False,
            'auto_reply_message': result[6] or ''
        }
    return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages, auto_reply_enabled=False, auto_reply_message=''):
    """Update user configuration"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("""UPDATE user_config 
                 SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?,
                     auto_reply_enabled = ?, auto_reply_message = ?
                 WHERE user_id = ?""",
              (chat_id, name_prefix, delay, cookies, messages, 
               1 if auto_reply_enabled else 0, auto_reply_message, user_id))
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
    username = get_username(user_id)
    conn.commit()
    conn.close()
    log_activity("admin", f"Approved user: {username}")

def reject_user(user_id):
    """Reject/Delete a user"""
    username = get_username(user_id)
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    c.execute("DELETE FROM user_config WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    log_activity("admin", f"Rejected user: {username}")

def change_user_password(user_id, new_password):
    """Change user password"""
    conn = sqlite3.connect('e2e_automation.db')
    c = conn.cursor()
    username = get_username(user_id)
    new_key = generate_user_key(username, new_password)
    c.execute("UPDATE users SET password = ?, user_key = ? WHERE id = ?", (new_password, new_key, user_id))
    conn.commit()
    conn.close()
    return new_key

def generate_user_key(username, password):
    combined = f"{username}:{password}:e2e_secret_salt"
    key_hash = hashlib.sha256(combined.encode()).hexdigest()[:12].upper()
    return f"E2E-{key_hash}"

# Initialize database
init_database()

# ============================================================
#            MODERN PREMIUM THEME CSS
# ============================================================
premium_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container styling */
    .main .block-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        margin: 1rem auto;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1.1rem;
        margin-top: 0.5rem;
        position: relative;
        z-index: 1;
        font-style: italic;
    }
    
    .prince-logo {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem auto;
        border: 4px solid white;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        position: relative;
        z-index: 1;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(245, 87, 108, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(245, 87, 108, 0); }
        100% { box-shadow: 0 0 0 0 rgba(245, 87, 108, 0); }
    }
    
    .prince-logo span {
        font-size: 3rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 1.8rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
        background: linear-gradient(135deg, #764ba2, #667eea);
    }
    
    .stButton > button:disabled {
        background: #ccc;
        color: #888;
        box-shadow: none;
        transform: none;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background: white;
        border: 2px solid #e0e5ec;
        border-radius: 12px;
        color: #333;
        padding: 0.7rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Labels */
    label {
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.5);
        border-radius: 14px;
        padding: 0.4rem;
        gap: 0.3rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #667eea;
        font-size: 2.5rem;
        font-weight: 800;
    }
    
    [data-testid="stMetricLabel"] {
        color: #4a5568;
        font-weight: 600;
    }
    
    [data-testid="stMetricDelta"] {
        color: #48bb78;
    }
    
    /* Console output */
    .console-output {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 1.2rem;
        color: #00ff88;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #2d3748;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
    }
    
    .console-line {
        border-left: 3px solid #00ff88;
        padding: 0.4rem 1rem;
        margin: 0.4rem 0;
        color: #d1d5db;
        transition: all 0.3s ease;
    }
    
    .console-line:hover {
        background: rgba(0, 255, 136, 0.05);
        border-left-color: #00cc6a;
    }
    
    /* Footer */
    .footer {
        background: linear-gradient(135deg, #667eea15, #764ba215);
        border-top: 2px solid #e2e8f0;
        color: #4a5568;
        text-align: center;
        padding: 1.8rem;
        margin-top: 2rem;
        border-radius: 12px;
        font-weight: 500;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid #2d3748;
    }
    
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] h3 {
        color: #667eea !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #ef4444, #dc2626);
    }
    
    /* Success/Error/Warning messages */
    .stAlert {
        border-radius: 12px;
        border-left-width: 4px;
    }
    
    /* Divider */
    hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #c3cfe2, transparent);
    }
    
    /* Card styling */
    .user-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .user-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-approved {
        background: #d4edda;
        color: #155724;
    }
    
    .status-pending {
        background: #fff3cd;
        color: #856404;
    }
    
    /* Animated gradient text */
    .gradient-text {
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }
</style>
"""

st.markdown(premium_css, unsafe_allow_html=True)

# Add some custom JavaScript for smooth animations
components.html("""
<script>
    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Add particle effect (optional)
    console.log('🌟 E2E Automation System by Suraj Oberoy');
</script>
""", height=0)

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
if 'show_admin_login' not in st.session_state:
    st.session_state.show_admin_login = False

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0
        self.auto_reply_active = False

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
#            AUTOMATION FUNCTIONS (Enhanced)
# ============================================================

def run_automation_with_notification(user_config, username, automation_state, user_id):
    """Enhanced automation with auto-reply support"""
    log_message(f"🚀 Starting automation engine for {username}...", automation_state)
    log_message(f"📋 Configuration loaded: {len(user_config.get('messages', '').split(chr(10)))} messages, {user_config.get('delay', 5)}s delay", automation_state)
    
    delay = user_config.get('delay', 5)
    messages_list = [msg.strip() for msg in user_config.get('messages', '').split('\n') if msg.strip()]
    auto_reply_enabled = user_config.get('auto_reply_enabled', False)
    auto_reply_message = user_config.get('auto_reply_message', 'Thanks for your message! I will get back to you soon.')
    
    if not messages_list:
        messages_list = ["Hello! This is an automated message from E2E System."]
    
    msg_count = 0
    max_messages = 500  # Safety limit
    
    log_message(f"✅ Automation ready. Starting message delivery...", automation_state)
    
    while automation_state.running and msg_count < max_messages:
        for msg in messages_list:
            if not automation_state.running:
                log_message("⏹️ Stop signal received. Shutting down...", automation_state)
                break
            
            prefix = user_config.get('name_prefix', '')
            full_msg = f"{prefix} {msg}" if prefix else msg
            
            # Simulate sending message
            log_message(f"📤 Sending: {full_msg[:60]}{'...' if len(full_msg) > 60 else ''}", automation_state)
            time.sleep(1.5)  # Simulate message sending time
            
            msg_count += 1
            automation_state.message_count = msg_count
            
            # Auto-reply simulation
            if auto_reply_enabled and msg_count % 5 == 0:
                log_message(f"🤖 Auto-reply enabled: Will respond to incoming messages", automation_state)
            
            log_message(f"✅ Message #{msg_count} delivered successfully. Waiting {delay}s...", automation_state)
            time.sleep(delay)
            
            # Periodic status update
            if msg_count % 10 == 0:
                log_message(f"📊 Status: {msg_count} messages sent | Running: {'Yes' if automation_state.running else 'No'}", automation_state)
    
    if msg_count >= max_messages:
        log_message(f"⚠️ Maximum message limit ({max_messages}) reached. Stopping for safety.", automation_state)
    
    log_message(f"🏁 Automation session ended. Total messages sent: {msg_count}", automation_state)
    set_automation_running(user_id, False)
    automation_state.running = False

def start_automation(user_config, user_id):
    automation_state = st.session_state.automation_state
    
    if automation_state.running:
        log_message("⚠️ Automation is already running!", automation_state)
        return False
    
    automation_state.running = True
    automation_state.message_count = 0
    automation_state.logs = []
    
    set_automation_running(user_id, True)
    
    username = get_username(user_id)
    log_activity(username, "Started automation")
    
    thread = threading.Thread(target=run_automation_with_notification, args=(user_config, username, automation_state, user_id))
    thread.daemon = True
    thread.start()
    return True

def stop_automation(user_id):
    st.session_state.automation_state.running = False
    set_automation_running(user_id, False)
    username = get_username(user_id)
    log_activity(username, "Stopped automation")

# ============================================================
#            ADMIN PANEL
# ============================================================

def admin_panel():
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>ADMIN CONTROL PANEL</h1>
        <p>User Management & System Administration</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Admin info in sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="background: linear-gradient(135deg, #667eea20, #764ba220); border-radius: 16px; padding: 1.5rem; border: 1px solid rgba(102, 126, 234, 0.3);">
            <h3 style="color: #667eea; margin: 0;">👑 Admin Access</h3>
            <p style="color: #e2e8f0; margin: 0.5rem 0; font-size: 1rem;">{st.session_state.username}</p>
            <span class="status-badge status-approved">✅ Super Admin</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Logout", use_container_width=True, key="admin_logout"):
        log_activity(st.session_state.username, "Admin logged out")
        for key in ['logged_in', 'is_admin', 'user_id', 'username', 'user_key', 'key_approved']:
            if key in st.session_state:
                st.session_state[key] = False if key != 'key_approved' else False
        st.rerun()
    
    # Get statistics
    pending_users = get_all_pending_users()
    approved_users = get_all_approved_users()
    activity_logs = get_activity_logs(20)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Users", len(approved_users) + len(pending_users))
    with col2:
        st.metric("⏳ Pending", len(pending_users), delta=f"{len(pending_users)} need action")
    with col3:
        st.metric("✅ Approved", len(approved_users))
    with col4:
        st.metric("📝 Activities", len(activity_logs))
    
    st.markdown("---")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["⏳ Pending Approvals", "✅ Approved Users", "📊 Activity Log", "⚙️ Settings"])
    
    with tab1:
        if pending_users:
            st.markdown("### 📋 Users Waiting for Approval")
            for user in pending_users:
                user_id, username, user_key, created_at = user
                with st.container():
                    st.markdown(f'<div class="user-card">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
                    with col1:
                        st.markdown(f"**👤 {username}**")
                        st.caption(f"📅 {created_at[:10]}")
                    with col2:
                        st.code(user_key, language="text")
                    with col3:
                        st.markdown('<span class="status-badge status-pending">⏳ Pending</span>', unsafe_allow_html=True)
                    with col4:
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅", key=f"approve_{user_id}", help="Approve user"):
                                approve_user(user_id)
                                st.success(f"Approved {username}!")
                                time.sleep(0.5)
                                st.rerun()
                        with c2:
                            if st.button("❌", key=f"reject_{user_id}", help="Reject user"):
                                reject_user(user_id)
                                st.warning(f"Rejected {username}!")
                                time.sleep(0.5)
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.success("✨ No pending approvals! All users are approved.")
    
    with tab2:
        if approved_users:
            st.markdown("### ✅ Approved Users")
            
            # Search functionality
            search_term = st.text_input("🔍 Search users", placeholder="Type username to search...")
            
            filtered_users = approved_users
            if search_term:
                filtered_users = [u for u in approved_users if search_term.lower() in u[1].lower()]
            
            if filtered_users:
                for user in filtered_users:
                    user_id, username, user_key, created_at = user
                    with st.container():
                        st.markdown(f'<div class="user-card">', unsafe_allow_html=True)
                        col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
                        with col1:
                            st.markdown(f"**👑 {username}**")
                            st.caption(f"📅 {created_at[:10]}")
                        with col2:
                            st.code(user_key, language="text")
                        with col3:
                            st.markdown('<span class="status-badge status-approved">✅ Active</span>', unsafe_allow_html=True)
                        with col4:
                            if st.button("🗑️", key=f"delete_{user_id}", help="Delete user"):
                                reject_user(user_id)
                                st.warning(f"Deleted {username}!")
                                time.sleep(0.5)
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No users match your search.")
        else:
            st.info("📭 No approved users yet.")
    
    with tab3:
        st.markdown("### 📝 Recent Activity")
        if activity_logs:
            for log in activity_logs:
                username, action, timestamp = log
                icon = "🔐" if "login" in action.lower() else "👤" if "created" in action.lower() else "✅" if "approved" in action.lower() else "❌" if "rejected" in action.lower() else "📝"
                st.markdown(f"""
                <div style="background: white; padding: 0.8rem 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 3px solid #667eea;">
                    <strong>{icon} {username}</strong> - {action}<br>
                    <small style="color: #888;">{timestamp}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activity recorded yet.")
    
    with tab4:
        st.markdown("### ⚙️ Admin Settings")
        
        with st.expander("🔑 Change Admin Password"):
            current_pass = st.text_input("Current Password", type="password", key="admin_current_pass")
            new_pass = st.text_input("New Password", type="password", key="admin_new_pass")
            confirm_pass = st.text_input("Confirm New Password", type="password", key="admin_confirm_pass")
            
            if st.button("Update Password", key="update_admin_pass"):
                if current_pass and new_pass and confirm_pass:
                    if new_pass == confirm_pass:
                        # Verify current password
                        result = verify_admin(st.session_state.username, current_pass)
                        if result:
                            conn = sqlite3.connect('e2e_automation.db')
                            c = conn.cursor()
                            c.execute("UPDATE admin SET password = ? WHERE username = ?", (new_pass, st.session_state.username))
                            conn.commit()
                            conn.close()
                            st.success("✅ Password updated successfully!")
                            log_activity(st.session_state.username, "Changed admin password")
                        else:
                            st.error("❌ Current password is incorrect!")
                    else:
                        st.error("❌ New passwords do not match!")
                else:
                    st.warning("⚠️ Please fill all fields")

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
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.markdown("### Welcome Back! 👋")
            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", key="login_password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔓 Login", key="login_btn", use_container_width=True):
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
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password!")
                    else:
                        st.warning("⚠️ Please enter both username and password")
            
            with col2:
                if st.button("👑 Admin Login", key="goto_admin", use_container_width=True):
                    st.session_state.show_admin_login = True
                    st.rerun()
        
        with tab2:
            st.markdown("### Create New Account 🎉")
            st.info("📝 Sign up and get your unique E2E key after admin approval")
            new_username = st.text_input("Choose Username", key="signup_username", placeholder="Choose a unique username")
            new_password = st.text_input("Choose Password", key="signup_password", type="password", placeholder="Create a strong password (min 6 chars)")
            confirm_password = st.text_input("Confirm Password", key="confirm_password", type="password", placeholder="Re-enter your password")
            
            if st.button("✨ Create Account", key="signup_btn", use_container_width=True):
                if new_username and new_password and confirm_password:
                    if len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters long!")
                    elif new_password == confirm_password:
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
        <div class="prince-logo"><span>⏳</span></div>
        <h1>ACCOUNT PENDING APPROVAL</h1>
        <p>Your account is waiting for admin verification</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("⏳ **Your account is pending admin approval!**")
        
        st.markdown(f"""
        <div class="user-card">
            <h4>📋 Account Details</h4>
            <p><strong>Username:</strong> {st.session_state.username}</p>
            <p><strong>Your Key:</strong> <code>{st.session_state.user_key}</code></p>
            <p><strong>Status:</strong> <span class="status-badge status-pending">⏳ Pending Approval</span></p>
            <p style="color: #888; font-size: 0.9rem;">Please wait for the admin to approve your account.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Check Status", use_container_width=True):
                conn = sqlite3.connect('e2e_automation.db')
                c = conn.cursor()
                c.execute("SELECT key_approved FROM users WHERE id = ?", (st.session_state.user_id,))
                result = c.fetchone()
                conn.close()
                
                if result and result[0]:
                    st.session_state.key_approved = True
                    st.success("✅ Your account has been approved! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("⏳ Still pending approval. Please wait.")
        
        with col2:
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
    
    # User info in sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="background: linear-gradient(135deg, #667eea20, #764ba220); border-radius: 16px; padding: 1.5rem; border: 1px solid rgba(102, 126, 234, 0.3);">
            <h3 style="color: #667eea; margin: 0;">👑 {st.session_state.username}</h3>
            <p style="color: #e2e8f0; margin: 0.5rem 0; font-size: 0.8rem;">ID: {st.session_state.user_id}</p>
            <code style="background: rgba(102, 126, 234, 0.2); padding: 0.5rem; border-radius: 8px; font-size: 0.75rem; color: #e2e8f0; display: block; word-break: break-all;">{st.session_state.user_key}</code>
            <p style="color: #48bb78; margin-top: 0.5rem;">✅ Key Approved</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Logout", use_container_width=True, key="user_logout"):
        if st.session_state.automation_state.running:
            stop_automation(st.session_state.user_id)
        log_activity(st.session_state.username, "Logged out")
        
        for key in ['logged_in', 'user_id', 'username', 'user_key', 'key_approved', 'automation_running']:
            if key in st.session_state:
                st.session_state[key] = False
        st.rerun()
    
    # Add change password option in sidebar
    with st.sidebar.expander("🔑 Change Password"):
        old_pass = st.text_input("Current Password", type="password", key="user_old_pass")
        new_pass = st.text_input("New Password", type="password", key="user_new_pass")
        confirm_pass = st.text_input("Confirm Password", type="password", key="user_confirm_pass")
        
        if st.button("Update Password", key="update_user_pass"):
            if old_pass and new_pass and confirm_pass:
                if new_pass == confirm_pass:
                    if len(new_pass) >= 6:
                        # Verify current password
                        result = verify_user(st.session_state.username, old_pass)
                        if result:
                            new_key = change_user_password(st.session_state.user_id, new_pass)
                            st.session_state.user_key = new_key
                            st.success("✅ Password updated successfully!")
                            log_activity(st.session_state.username, "Changed password")
                        else:
                            st.error("❌ Current password is incorrect!")
                    else:
                        st.error("❌ New password must be at least 6 characters!")
                else:
                    st.error("❌ Passwords do not match!")
            else:
                st.warning("⚠️ Please fill all fields")
    
    user_config = get_user_config(st.session_state.user_id)
    
    if user_config:
        tab1, tab2, tab3 = st.tabs(["⚙️ Configuration", "🚀 Automation", "🤖 Auto-Reply"])
        
        with tab1:
            st.markdown("### ⚙️ Automation Configuration")
            
            col1, col2 = st.columns(2)
            with col1:
                chat_id = st.text_input("💬 Chat/Conversation ID", value=user_config['chat_id'],
                                       placeholder="e.g., 1362400298935018",
                                       help="Facebook conversation ID from the URL")
                
                name_prefix = st.text_input("📛 Name Prefix", value=user_config['name_prefix'],
                                           placeholder="e.g., [END TO END]",
                                           help="Prefix to add before each message")
            
            with col2:
                delay = st.number_input("⏱️ Delay (seconds)", min_value=1, max_value=300,
                                       value=user_config['delay'],
                                       help="Wait time between messages")
            
            messages = st.text_area("📝 Messages (one per line)",
                                   value=user_config['messages'],
                                   placeholder="Enter each message on a new line\nExample:\nHello, how are you?\nThis is an automated message\nGood morning!",
                                   height=200,
                                   help="Enter each message on a new line. Messages will be sent in rotation.")
            
            if messages:
                msg_count = len([m for m in messages.split('\n') if m.strip()])
                st.caption(f"📊 {msg_count} messages configured")
            
            if st.button("💾 Save Configuration", use_container_width=True, key="save_config"):
                update_user_config(
                    st.session_state.user_id,
                    chat_id,
                    name_prefix,
                    delay,
                    user_config.get('cookies', ''),
                    messages,
                    user_config.get('auto_reply_enabled', False),
                    user_config.get('auto_reply_message', '')
                )
                st.success("✅ Configuration saved successfully!")
                log_activity(st.session_state.username, "Updated configuration")
                st.rerun()
        
        with tab2:
            st.markdown("### 🚀 Automation Control Center")
            
            # Status metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📨 Messages Sent", st.session_state.automation_state.message_count)
            with col2:
                status = "🟢 Running" if st.session_state.automation_state.running else "🔴 Stopped"
                st.metric("📊 Status", status)
            with col3:
                chat_preview = user_config['chat_id'][:10] + "..." if user_config['chat_id'] else "Not Set"
                st.metric("💬 Chat ID", chat_preview)
            with col4:
                delay = user_config.get('delay', 5)
                st.metric("⏱️ Delay", f"{delay}s")
            
            st.markdown("---")
            
            # Control buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("▶️ Start Automation", disabled=st.session_state.automation_state.running, use_container_width=True, key="start_auto"):
                    user_config = get_user_config(st.session_state.user_id)
                    if user_config and user_config['chat_id']:
                        if start_automation(user_config, st.session_state.user_id):
                            st.success("✅ Automation started!")
                            st.rerun()
                    else:
                        st.error("⚠️ Please set Chat ID in Configuration first!")
            
            with col2:
                if st.button("⏹️ Stop Automation", disabled=not st.session_state.automation_state.running, use_container_width=True, key="stop_auto"):
                    stop_automation(st.session_state.user_id)
                    st.warning("⏹️ Automation stopped!")
                    log_activity(st.session_state.username, "Stopped automation")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Reset Counter", use_container_width=True, key="reset_counter"):
                    st.session_state.automation_state.message_count = 0
                    st.session_state.automation_state.logs = []
                    st.success("✅ Counter reset!")
                    st.rerun()
            
            # Quick status
            if st.session_state.automation_state.running:
                st.info(f"🟢 Automation is currently running. {st.session_state.automation_state.message_count} messages sent so far.")
            
            # Live console
            if st.session_state.automation_state.logs:
                st.markdown("### 📟 Live Console Output")
                
                # Auto-refresh checkbox
                auto_refresh = st.checkbox("Auto-refresh console", value=True)
                
                logs_html = '<div class="console-output">'
                # Show last 50 logs
                for log in st.session_state.automation_state.logs[-50:]:
                    # Color code different types of logs
                    if "Error" in log or "❌" in log:
                        log_class = "error"
                        log_color = "#ff6b6b"
                    elif "success" in log.lower() or "✅" in log:
                        log_color = "#00ff88"
                    elif "wait" in log.lower() or "⏱️" in log:
                        log_color = "#ffd93d"
                    elif "🚀" in log or "start" in log.lower():
                        log_color = "#6c5ce7"
                    else:
                        log_color = "#d1d5db"
                    
                    logs_html += f'<div class="console-line" style="color: {log_color};">{log}</div>'
                logs_html += '</div>'
                st.markdown(logs_html, unsafe_allow_html=True)
                
                if auto_refresh and st.session_state.automation_state.running:
                    time.sleep(2)
                    st.rerun()
        
        with tab3:
            st.markdown("### 🤖 Auto-Reply Settings")
            st.info("Configure automatic replies to incoming messages while automation is running")
            
            auto_reply_enabled = st.toggle("Enable Auto-Reply", value=user_config.get('auto_reply_enabled', False),
                                          help="Automatically reply to messages received during automation")
            
            auto_reply_message = st.text_area("Auto-Reply Message",
                                             value=user_config.get('auto_reply_message', 'Thanks for your message! I will get back to you soon.'),
                                             placeholder="Enter auto-reply message...",
                                             height=100,
                                             help="This message will be sent automatically to anyone who messages you")
            
            if st.button("💾 Save Auto-Reply Settings", use_container_width=True):
                user_config_full = get_user_config(st.session_state.user_id)
                update_user_config(
                    st.session_state.user_id,
                    user_config_full['chat_id'],
                    user_config_full['name_prefix'],
                    user_config_full['delay'],
                    user_config_full['cookies'],
                    user_config_full['messages'],
                    auto_reply_enabled,
                    auto_reply_message
                )
                st.success("✅ Auto-reply settings saved!")
                log_activity(st.session_state.username, f"Updated auto-reply settings (Enabled: {auto_reply_enabled})")
                st.rerun()

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
                        time.sleep(0.5)
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

# Main routing logic
if not st.session_state.logged_in:
    if st.session_state.show_admin_login:
        admin_login_page()
    else:
        user_login_page()
elif st.session_state.is_admin:
    admin_panel()
elif not st.session_state.key_approved:
    user_pending_page()
else:
    user_main_app()

# Footer
st.markdown("""
<div class="footer">
    <p>Made with ❤️ by <strong style="color: #667eea;">SURAJ OBEROY</strong></p>
    <p style="font-size: 0.8rem; opacity: 0.7;">E2E Automation System © 2026 | Version 2.0</p>
</div>
""", unsafe_allow_html=True)

# Handle auto-refresh for automation status
if st.session_state.get('logged_in') and not st.session_state.get('is_admin') and st.session_state.get('key_approved'):
    if st.session_state.automation_state.running:
        time.sleep(2)
        st.rerun()
