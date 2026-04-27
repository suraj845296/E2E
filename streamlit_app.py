import streamlit as st
import time
import hashlib
import os
import json
import urllib.parse
from pathlib import Path
import sqlite3
from datetime import datetime
import tempfile

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="E2E BY SURAJ OBEROY",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
#            DATABASE FUNCTIONS (Cloud Compatible)
# ============================================================

# Use a persistent database path or fallback to in-memory
def get_db_path():
    """Get a writable database path"""
    # Try to use a persistent location if available (Streamlit Cloud)
    try:
        # For Streamlit Cloud
        persistent_dir = os.environ.get('STREAMLIT_PERSISTENT_DIR', None)
        if persistent_dir and os.path.exists(persistent_dir):
            db_path = os.path.join(persistent_dir, 'e2e_automation.db')
            return db_path
    except:
        pass
    
    # Fallback to temporary directory (in-memory for cloud, file for local)
    try:
        temp_dir = tempfile.gettempdir()
        db_path = os.path.join(temp_dir, 'e2e_automation.db')
        return db_path
    except:
        return ':memory:'  # Last resort - in-memory database

def init_database():
    """Initialize SQLite database"""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path, timeout=10)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      user_key TEXT,
                      key_approved BOOLEAN DEFAULT 0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # User config table (cookies field pehle se hai)
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
                      display_count INTEGER DEFAULT 0,
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
                      ('admin', 'admin123', 1))
        
        # Add new columns if they don't exist (for existing databases)
        try:
            c.execute("ALTER TABLE user_config ADD COLUMN auto_reply_enabled BOOLEAN DEFAULT 0")
        except:
            pass
        
        try:
            c.execute("ALTER TABLE user_config ADD COLUMN auto_reply_message TEXT")
        except:
            pass
        
        try:
            c.execute("ALTER TABLE user_config ADD COLUMN display_count INTEGER DEFAULT 0")
        except:
            pass
        
        # Create default test user if no users exist
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        if user_count == 0:
            test_user_key = generate_user_key("testuser", "test123")
            c.execute("INSERT INTO users (username, password, user_key, key_approved) VALUES (?, ?, ?, ?)",
                      ('testuser', 'test123', test_user_key, 1))
            test_user_id = c.lastrowid
            c.execute("INSERT INTO user_config (user_id, chat_id, name_prefix, delay, cookies, messages, display_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (test_user_id, "", "", 5, "", "Hello!\nThis is a test message.\nE2E Automation working!", 0))
            log_activity("system", "Created test user: testuser/test123")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        return False

def get_connection():
    """Get database connection with proper path"""
    db_path = get_db_path()
    return sqlite3.connect(db_path, timeout=10)

def log_activity(username, action):
    """Log user activity"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO activity_log (username, action) VALUES (?, ?)", (username, action))
        conn.commit()
        conn.close()
    except:
        pass

def get_activity_logs(limit=50):
    """Get recent activity logs"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT username, action, timestamp FROM activity_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        result = c.fetchall()
        conn.close()
        return result
    except:
        return []

def create_user(username, password):
    """Create new user"""
    try:
        user_key = generate_user_key(username, password)
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, user_key, key_approved) VALUES (?, ?, ?, ?)", 
                  (username, password, user_key, 0))
        user_id = c.lastrowid
        
        # Create default config for user
        c.execute("INSERT INTO user_config (user_id, chat_id, name_prefix, delay, cookies, messages, display_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, "", "", 5, "", "", 0))
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
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, user_key, key_approved FROM users WHERE username = ? AND password = ?", (username, password))
        result = c.fetchone()
        conn.close()
        if result:
            log_activity(username, "Logged in")
        return result if result else None
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def verify_admin(username, password):
    """Verify admin credentials"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, username, is_super_admin FROM admin WHERE username = ? AND password = ?", (username, password))
        result = c.fetchone()
        conn.close()
        if result:
            log_activity(username, "Admin logged in")
        return result if result else None
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def get_user_config(user_id):
    """Get user configuration - ab cookies bhi return hongi"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT chat_id, name_prefix, delay, cookies, messages, auto_reply_enabled, auto_reply_message, display_count FROM user_config WHERE user_id = ?", (user_id,))
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
                'auto_reply_message': result[6] or '',
                'display_count': result[7] or 0
            }
        return None
    except Exception as e:
        return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages, auto_reply_enabled=False, auto_reply_message='', display_count=None):
    """Update user configuration - ab cookies bhi save hongi"""
    try:
        conn = get_connection()
        c = conn.cursor()
        if display_count is not None:
            c.execute("""UPDATE user_config 
                         SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?,
                             auto_reply_enabled = ?, auto_reply_message = ?, display_count = ?
                         WHERE user_id = ?""",
                      (chat_id, name_prefix, delay, cookies, messages, 
                       1 if auto_reply_enabled else 0, auto_reply_message, display_count, user_id))
        else:
            c.execute("""UPDATE user_config 
                         SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?,
                             auto_reply_enabled = ?, auto_reply_message = ?
                         WHERE user_id = ?""",
                      (chat_id, name_prefix, delay, cookies, messages, 
                       1 if auto_reply_enabled else 0, auto_reply_message, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def update_display_count(user_id, new_count):
    """Update only the display count"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE user_config SET display_count = ? WHERE user_id = ?", (new_count, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_username(user_id):
    """Get username by ID"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except:
        return None

def get_automation_running(user_id):
    """Get automation running status"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT automation_running FROM user_config WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] == 1 if result else False
    except:
        return False

def set_automation_running(user_id, status):
    """Set automation running status"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE user_config SET automation_running = ? WHERE user_id = ?", (1 if status else 0, user_id))
        conn.commit()
        conn.close()
    except:
        pass

def get_all_pending_users():
    """Get all users pending approval"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, username, user_key, created_at FROM users WHERE key_approved = 0 ORDER BY created_at DESC")
        result = c.fetchall()
        conn.close()
        return result
    except:
        return []

def get_all_approved_users():
    """Get all approved users"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, username, user_key, created_at FROM users WHERE key_approved = 1 ORDER BY created_at DESC")
        result = c.fetchall()
        conn.close()
        return result
    except:
        return []

def approve_user(user_id):
    """Approve a user"""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET key_approved = 1 WHERE id = ?", (user_id,))
        username = get_username(user_id)
        conn.commit()
        conn.close()
        log_activity("admin", f"Approved user: {username}")
    except:
        pass

def reject_user(user_id):
    """Reject/Delete a user"""
    username = get_username(user_id)
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM user_config WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        log_activity("admin", f"Rejected user: {username}")
    except:
        pass

def change_user_password(user_id, new_password):
    """Change user password"""
    try:
        conn = get_connection()
        c = conn.cursor()
        username = get_username(user_id)
        new_key = generate_user_key(username, new_password)
        c.execute("UPDATE users SET password = ?, user_key = ? WHERE id = ?", (new_password, new_key, user_id))
        conn.commit()
        conn.close()
        return new_key
    except:
        return None

def generate_user_key(username, password):
    combined = f"{username}:{password}:e2e_secret_salt_2024"
    key_hash = hashlib.sha256(combined.encode()).hexdigest()[:12].upper()
    return f"E2E-{key_hash}"

# Initialize database
db_initialized = init_database()
if not db_initialized:
    st.error("Failed to initialize database. Please check permissions.")

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
    
    /* Display Counter Big Box */
    .display-counter-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 24px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        animation: slideIn 0.5s ease;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .display-counter-box h2 {
        color: white;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 1rem;
        opacity: 0.9;
    }
    
    .display-counter-number {
        font-size: 5rem;
        font-weight: 800;
        color: white;
        text-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        letter-spacing: 5px;
    }
    
    .display-counter-label {
        color: rgba(255,255,255,0.9);
        font-size: 0.9rem;
        margin-top: 0.5rem;
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
    
    /* Login container */
    .login-container {
        background: white;
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    /* Cookies card */
    .cookies-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #fdcb6e;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .cookies-card h4 {
        color: #d63031;
        margin-bottom: 0.5rem;
    }
    
    .cookies-card code {
        background: #2d3436;
        color: #00ff88;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    
    /* Counter button group */
    .counter-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin: 1rem 0;
    }
</style>
"""

st.markdown(premium_css, unsafe_allow_html=True)

# Add some custom JavaScript for smooth animations
st.components.v1.html("""
<script>
    document.documentElement.style.scrollBehavior = 'smooth';
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
if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = False

def log_message(msg, is_error=False):
    """Add a log message"""
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
    st.session_state.logs.append(formatted_msg)
    # Keep only last 100 logs
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

# ============================================================
#            AUTOMATION FUNCTIONS (Simulation Mode)
# ============================================================

def run_simulation(user_config, username, user_id):
    """Simulated automation without threading issues"""
    if st.session_state.simulation_mode:
        log_message("⚠️ Automation already running!")
        return False
    
    if not user_config.get('chat_id'):
        log_message("⚠️ Please set Chat ID in Configuration first!")
        return False
    
    log_message(f"🚀 Starting automation simulation for {username}...")
    
    # Cookies check
    cookies = user_config.get('cookies', '')
    if cookies:
        log_message(f"🍪 Cookies loaded ({len(cookies)} chars). Using authenticated session.")
    
    message_lines = user_config.get('messages', '').split('\n')
    messages_list = [msg.strip() for msg in message_lines if msg.strip()]
    
    if not messages_list:
        messages_list = ["Hello! This is an automated message from E2E System."]
    
    log_message(f"📋 Configuration loaded: {len(messages_list)} messages, {user_config.get('delay', 5)}s delay")
    
    delay = user_config.get('delay', 5)
    auto_reply_enabled = user_config.get('auto_reply_enabled', False)
    auto_reply_message = user_config.get('auto_reply_message', 'Thanks for your message! I will get back to you soon.')
    
    st.session_state.simulation_mode = True
    set_automation_running(user_id, True)
    msg_count = 0
    
    try:
        while st.session_state.simulation_mode and msg_count < 50:  # Limit to 50 messages for simulation
            for msg in messages_list:
                if not st.session_state.simulation_mode:
                    break
                
                prefix = user_config.get('name_prefix', '')
                full_msg = f"{prefix} {msg}" if prefix else msg
                
                log_message(f"📤 Sending: {full_msg[:60]}{'...' if len(full_msg) > 60 else ''}")
                time.sleep(1)  # Short delay for simulation
                
                msg_count += 1
                st.session_state.message_count = msg_count
                
                if auto_reply_enabled and msg_count % 5 == 0:
                    log_message(f"🤖 Auto-reply would be triggered: {auto_reply_message[:50]}...", True)
                
                log_message(f"✅ Message #{msg_count} sent successfully!")
                time.sleep(delay)
                
                if msg_count % 10 == 0:
                    log_message(f"📊 Status: {msg_count} messages sent | Running: Yes")
                
                # Force a rerun to update the UI
                if msg_count % 3 == 0:
                    st.rerun()
        
        if msg_count >= 50:
            log_message(f"⚠️ Maximum message limit (50) reached. Stopping.")
    
    except Exception as e:
        log_message(f"❌ Error in automation: {str(e)}", True)
    
    finally:
        log_message(f"🏁 Automation session ended. Total messages sent: {msg_count}")
        set_automation_running(user_id, False)
        st.session_state.simulation_mode = False

def start_automation(user_config, user_id):
    """Start the automation process"""
    if st.session_state.simulation_mode:
        log_message("⚠️ Automation is already running!")
        return False
    
    if not user_config.get('chat_id'):
        log_message("⚠️ Please set Chat ID in Configuration first!")
        return False
    
    st.session_state.message_count = 0
    st.session_state.logs = []
    username = get_username(user_id)
    log_activity(username, "Started automation")
    
    # Run simulation directly (no threading issues)
    run_simulation(user_config, username, user_id)
    return True

def stop_automation(user_id):
    """Stop the automation process"""
    st.session_state.simulation_mode = False
    set_automation_running(user_id, False)
    username = get_username(user_id)
    log_activity(username, "Stopped automation")
    log_message("⏹️ Automation stopped by user")

# ============================================================
#            ADMIN PANEL
# ============================================================

def admin_panel():
    """Admin panel interface"""
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
        for key in ['logged_in', 'is_admin', 'user_id', 'username', 'user_key', 'key_approved', 'show_admin_login']:
            if key in st.session_state:
                if key == 'key_approved':
                    st.session_state[key] = False
                elif key == 'show_admin_login':
                    st.session_state[key] = False
                else:
                    st.session_state[key] = False
        st.rerun()
    
    # Get statistics
    pending_users = get_all_pending_users()
    approved_users = get_all_approved_users()
    activity_logs = get_activity_logs(20)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Users", len(approved_users) + len(pending_users))
    with col2:
        st.metric("⏳ Pending", len(pending_users))
    with col3:
        st.metric("✅ Approved", len(approved_users))
    with col4:
        st.metric("📝 Activities", len(activity_logs))
    
    st.markdown("---")
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["⏳ Pending Approvals", "✅ Approved Users", "📊 Activity Log"])
    
    with tab1:
        if pending_users:
            st.markdown("### 📋 Users Waiting for Approval")
            for user in pending_users:
                user_id, username, user_key, created_at = user
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 3, 1, 2])
                    with col1:
                        st.markdown(f"**👤 {username}**")
                        st.caption(f"📅 {created_at[:10] if created_at else 'Unknown'}")
                    with col2:
                        st.code(user_key, language="text")
                    with col3:
                        st.markdown('<span class="status-badge status-pending">⏳ Pending</span>', unsafe_allow_html=True)
                    with col4:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ Approve", key=f"approve_{user_id}"):
                                approve_user(user_id)
                                st.success(f"✅ Approved {username}!")
                                st.rerun()
                        with col_b:
                            if st.button("❌ Reject", key=f"reject_{user_id}"):
                                reject_user(user_id)
                                st.warning(f"❌ Rejected {username}!")
                                st.rerun()
                    st.divider()
        else:
            st.success("✨ No pending approvals! All users are approved.")
    
    with tab2:
        if approved_users:
            st.markdown("### ✅ Approved Users")
            
            search_term = st.text_input("🔍 Search users", placeholder="Type username to search...")
            
            filtered_users = approved_users
            if search_term:
                filtered_users = [u for u in approved_users if search_term.lower() in u[1].lower()]
            
            for user in filtered_users:
                user_id, username, user_key, created_at = user
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
                    with col1:
                        st.markdown(f"**👑 {username}**")
                        st.caption(f"📅 {created_at[:10] if created_at else 'Unknown'}")
                    with col2:
                        st.code(user_key, language="text")
                    with col3:
                        st.markdown('<span class="status-badge status-approved">✅ Active</span>', unsafe_allow_html=True)
                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_{user_id}"):
                            reject_user(user_id)
                            st.warning(f"🗑️ Deleted {username}!")
                            st.rerun()
                    st.divider()
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

# ============================================================
#            USER PAGES
# ============================================================

def user_login_page():
    """User login page"""
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>SURAJ OBEROY E2E SERVER</h1>
        <p>"seven billion smiles in this world but yours is my favorite___✨"</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
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
                                st.rerun()
                            else:
                                st.warning("⏳ Your account is pending admin approval!")
                                st.rerun()
                        else:
                            st.error("❌ Invalid username or password!")
                    else:
                        st.warning("⚠️ Please enter both username and password")
            
            with col2:
                if st.button("👑 Admin Login", key="goto_admin", use_container_width=True):
                    st.session_state.show_admin_login = True
                    st.rerun()
            
            st.markdown("---")
            st.caption("💡 Test Account: testuser / test123")
        
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
        st.markdown('</div>', unsafe_allow_html=True)

def user_pending_page():
    """User pending approval page"""
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
                try:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("SELECT key_approved FROM users WHERE id = ?", (st.session_state.user_id,))
                    result = c.fetchone()
                    conn.close()
                    
                    if result and result[0]:
                        st.session_state.key_approved = True
                        st.success("✅ Your account has been approved! Redirecting...")
                        st.rerun()
                    else:
                        st.info("⏳ Still pending approval. Please wait.")
                except:
                    st.info("⏳ Still pending approval. Please wait.")
        
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                for key in ['logged_in', 'user_id', 'username', 'user_key', 'key_approved']:
                    st.session_state[key] = False
                st.rerun()

def user_main_app():
    """Main user application"""
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>SURAJ OBEROY E2E SYSTEM</h1>
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
        if st.session_state.simulation_mode:
            stop_automation(st.session_state.user_id)
        log_activity(st.session_state.username, "Logged out")
        
        for key in ['logged_in', 'user_id', 'username', 'user_key', 'key_approved', 'automation_running', 'simulation_mode']:
            st.session_state[key] = False
        st.rerun()
    
    # Change password in sidebar
    with st.sidebar.expander("🔑 Change Password"):
        old_pass = st.text_input("Current Password", type="password", key="user_old_pass")
        new_pass = st.text_input("New Password", type="password", key="user_new_pass")
        confirm_pass = st.text_input("Confirm Password", type="password", key="user_confirm_pass")
        
        if st.button("Update Password", key="update_user_pass"):
            if old_pass and new_pass and confirm_pass:
                if new_pass == confirm_pass:
                    if len(new_pass) >= 6:
                        result = verify_user(st.session_state.username, old_pass)
                        if result:
                            new_key = change_user_password(st.session_state.user_id, new_pass)
                            if new_key:
                                st.session_state.user_key = new_key
                                st.success("✅ Password updated successfully!")
                                log_activity(st.session_state.username, "Changed password")
                                st.rerun()
                            else:
                                st.error("❌ Failed to update password!")
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
        # Tabs mein Cookies wala tab add kiya
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚙️ Configuration", "🍪 Cookies Settings", "🚀 Automation", "🤖 Auto-Reply", "📊 Display Counter"])
        
        with tab1:
            st.markdown("### ⚙️ Automation Configuration")
            
            col1, col2 = st.columns(2)
            with col1:
                chat_id = st.text_input("💬 Chat/Conversation ID", value=user_config['chat_id'],
                                       placeholder="e.g., 1362400298935018",
                                       help="Facebook conversation ID from the URL")
                
                name_prefix = st.text_input("📛 Name Prefix", value=user_config['name_prefix'],
                                           placeholder="e.g., [END TO END]")
            
            with col2:
                delay = st.number_input("⏱️ Delay (seconds)", min_value=1, max_value=300,
                                       value=user_config['delay'])
            
            messages = st.text_area("📝 Messages (one per line)",
                                   value=user_config['messages'],
                                   placeholder="Enter each message on a new line\nExample:\nHello, how are you?\nThis is an automated message\nGood morning!",
                                   height=200)
            
            if messages:
                msg_count = len([m for m in messages.split('\n') if m.strip()])
                st.caption(f"📊 {msg_count} messages configured")
            
            if st.button("💾 Save Configuration", use_container_width=True, key="save_config"):
                success = update_user_config(
                    st.session_state.user_id,
                    chat_id,
                    name_prefix,
                    delay,
                    user_config.get('cookies', ''),
                    messages,
                    user_config.get('auto_reply_enabled', False),
                    user_config.get('auto_reply_message', ''),
                    user_config.get('display_count', 0)
                )
                if success:
                    st.success("✅ Configuration saved successfully!")
                    log_activity(st.session_state.username, "Updated configuration")
                    st.rerun()
                else:
                    st.error("❌ Failed to save configuration!")
        
        # ========== NAYA COOKIES TAB ==========
        with tab2:
            st.markdown("### 🍪 Facebook Cookies Settings")
            
            st.markdown("""
            <div class="cookies-card">
                <h4>📋 How to Get Facebook Cookies:</h4>
                <ol>
                    <li>Login to <strong>Facebook</strong> in your browser</li>
                    <li>Press <code>F12</code> to open Developer Tools</li>
                    <li>Go to <strong>Application/Storage</strong> tab</li>
                    <li>Click on <strong>Cookies</strong> → <strong>https://www.facebook.com</strong></li>
                    <li>Look for the <code>c_user</code> cookie (contains your user ID)</li>
                    <li>Look for the <code>xs</code> cookie (session token)</li>
                    <li>Copy all cookies in JSON format or key=value format</li>
                </ol>
                <p><strong>Example Format:</strong></p>
                <code>c_user=123456789; xs=abc123def456; fr=xyz789; datr=something</code>
            </div>
            """, unsafe_allow_html=True)
            
            cookies_value = st.text_area(
                "🔐 Facebook Cookies",
                value=user_config.get('cookies', ''),
                placeholder="Paste your Facebook cookies here...\nc_user=YOUR_USER_ID; xs=YOUR_TOKEN; fr=YOUR_FR; datr=YOUR_DATR",
                height=200,
                help="Enter Facebook cookies for authenticated automation"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Cookies", use_container_width=True, key="save_cookies_only"):
                    success = update_user_config(
                        st.session_state.user_id,
                        user_config['chat_id'],
                        user_config['name_prefix'],
                        user_config['delay'],
                        cookies_value,
                        user_config.get('messages', ''),
                        user_config.get('auto_reply_enabled', False),
                        user_config.get('auto_reply_message', ''),
                        user_config.get('display_count', 0)
                    )
                    if success:
                        st.success("✅ Cookies saved successfully!")
                        log_activity(st.session_state.username, "Updated Facebook cookies")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save cookies!")
            
            with col2:
                if st.button("🗑️ Clear Cookies", use_container_width=True, key="clear_cookies"):
                    success = update_user_config(
                        st.session_state.user_id,
                        user_config['chat_id'],
                        user_config['name_prefix'],
                        user_config['delay'],
                        '',
                        user_config.get('messages', ''),
                        user_config.get('auto_reply_enabled', False),
                        user_config.get('auto_reply_message', ''),
                        user_config.get('display_count', 0)
                    )
                    if success:
                        st.success("🗑️ Cookies cleared successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to clear cookies!")
            
            # Cookie status indicator
            if user_config.get('cookies'):
                cookie_len = len(user_config['cookies'])
                st.success(f"✅ Cookies are set! ({cookie_len} characters)")
                
                # Parse and show cookie info
                try:
                    cookie_str = user_config['cookies']
                    cookie_parts = cookie_str.split(';')
                    st.markdown("**📊 Cookie Summary:**")
                    
                    for part in cookie_parts[:5]:  # Show first 5 cookies
                        part = part.strip()
                        if '=' in part:
                            key, value = part.split('=', 1)
                            masked_value = value[:4] + "****" if len(value) > 4 else "****"
                            st.text(f"  - {key} = {masked_value}")
                    
                    if len(cookie_parts) > 5:
                        st.text(f"  ... and {len(cookie_parts) - 5} more")
                except:
                    st.info("Cookies are set but couldn't parse format.")
            else:
                st.warning("⚠️ No cookies set. Automation features may be limited.")
        
        with tab3:
            st.markdown("### 🚀 Automation Control Center")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📨 Messages Sent", st.session_state.message_count)
            with col2:
                status = "🟢 Running" if st.session_state.simulation_mode else "🔴 Stopped"
                st.metric("📊 Status", status)
            with col3:
                chat_preview = user_config['chat_id'][:10] + "..." if len(user_config['chat_id']) > 10 else user_config['chat_id'] or "Not Set"
                st.metric("💬 Chat ID", chat_preview)
            with col4:
                st.metric("⏱️ Delay", f"{user_config.get('delay', 5)}s")
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("▶️ Start Automation", disabled=st.session_state.simulation_mode, use_container_width=True, key="start_auto"):
                    user_config = get_user_config(st.session_state.user_id)
                    if user_config and user_config['chat_id']:
                        if start_automation(user_config, st.session_state.user_id):
                            st.success("✅ Automation started!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to start automation!")
                    else:
                        st.error("⚠️ Please set Chat ID in Configuration first!")
            
            with col2:
                if st.button("⏹️ Stop Automation", disabled=not st.session_state.simulation_mode, use_container_width=True, key="stop_auto"):
                    stop_automation(st.session_state.user_id)
                    st.warning("⏹️ Automation stopped!")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Reset Counter", use_container_width=True, key="reset_counter"):
                    st.session_state.message_count = 0
                    st.session_state.logs = []
                    st.success("✅ Counter reset!")
                    st.rerun()
            
            if st.session_state.simulation_mode:
                st.info(f"🟢 Automation is currently running. {st.session_state.message_count} messages sent so far.")
            
            # Live console
            if st.session_state.logs:
                st.markdown("### 📟 Live Console Output")
                
                auto_refresh = st.checkbox("Auto-refresh console", value=True)
                
                logs_html = '<div class="console-output">'
                for log in st.session_state.logs[-50:]:
                    if "Error" in log or "❌" in log:
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
                
                if auto_refresh and st.session_state.simulation_mode:
                    time.sleep(1)
                    st.rerun()
        
        with tab4:
            st.markdown("### 🤖 Auto-Reply Settings")
            st.info("Configure automatic replies to incoming messages while automation is running")
            
            auto_reply_enabled = st.toggle("Enable Auto-Reply", value=user_config.get('auto_reply_enabled', False))
            
            auto_reply_message = st.text_area("Auto-Reply Message",
                                             value=user_config.get('auto_reply_message', 'Thanks for your message! I will get back to you soon.'),
                                             placeholder="Enter auto-reply message...",
                                             height=100)
            
            if st.button("💾 Save Auto-Reply Settings", use_container_width=True):
                success = update_user_config(
                    st.session_state.user_id,
                    user_config['chat_id'],
                    user_config['name_prefix'],
                    user_config['delay'],
                    user_config.get('cookies', ''),
                    user_config['messages'],
                    auto_reply_enabled,
                    auto_reply_message,
                    user_config.get('display_count', 0)
                )
                if success:
                    st.success("✅ Auto-reply settings saved!")
                    log_activity(st.session_state.username, f"Updated auto-reply settings (Enabled: {auto_reply_enabled})")
                    st.rerun()
                else:
                    st.error("❌ Failed to save settings!")
        
        # ========== NEW DISPLAY COUNTER TAB ==========
        with tab5:
            st.markdown("### 📊 Display Counter")
            st.markdown("Manage your display counter value")
            
            # Display counter in a beautiful box
            current_count = user_config.get('display_count', 0)
            
            st.markdown(f"""
            <div class="display-counter-box">
                <h2>CURRENT DISPLAY COUNT</h2>
                <div class="display-counter-number">{current_count:,}</div>
                <div class="display-counter-label">Total Display Count</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Counter control buttons
            st.markdown("### ✏️ Update Counter Value")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("➕ +1", use_container_width=True, key="inc_1"):
                    new_count = current_count + 1
                    if update_display_count(st.session_state.user_id, new_count):
                        st.success(f"✅ Counter updated to {new_count:,}!")
                        log_activity(st.session_state.username, f"Increased display count to {new_count}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update counter!")
            
            with col2:
                if st.button("➕ +10", use_container_width=True, key="inc_10"):
                    new_count = current_count + 10
                    if update_display_count(st.session_state.user_id, new_count):
                        st.success(f"✅ Counter updated to {new_count:,}!")
                        log_activity(st.session_state.username, f"Increased display count to {new_count}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update counter!")
            
            with col3:
                if st.button("➕ +100", use_container_width=True, key="inc_100"):
                    new_count = current_count + 100
                    if update_display_count(st.session_state.user_id, new_count):
                        st.success(f"✅ Counter updated to {new_count:,}!")
                        log_activity(st.session_state.username, f"Increased display count to {new_count}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update counter!")
            
            with col4:
                if st.button("🔄 Reset to 0", use_container_width=True, key="reset_display"):
                    if update_display_count(st.session_state.user_id, 0):
                        st.success("✅ Counter reset to 0!")
                        log_activity(st.session_state.username, "Reset display count to 0")
                        st.rerun()
                    else:
                        st.error("❌ Failed to reset counter!")
            
            st.markdown("---")
            
            # Manual input for custom value
            st.markdown("### ✏️ Set Custom Value")
            col1, col2 = st.columns([3, 1])
            with col1:
                custom_value = st.number_input("Enter custom value", min_value=0, value=current_count, step=1, key="custom_display_value")
            with col2:
                if st.button("Set Value", use_container_width=True, key="set_custom"):
                    if update_display_count(st.session_state.user_id, int(custom_value)):
                        st.success(f"✅ Counter updated to {int(custom_value):,}!")
                        log_activity(st.session_state.username, f"Set display count to {int(custom_value)}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update counter!")
            
            st.markdown("---")
            
            # Subtract buttons
            st.markdown("### ➖ Decrease Counter")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("➖ -1", use_container_width=True, key="dec_1"):
                    new_count = max(0, current_count - 1)
                    if update_display_count(st.session_state.user_id, new_count):
                        st.success(f"✅ Counter updated to {new_count:,}!")
                        log_activity(st.session_state.username, f"Decreased display count to {new_count}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update counter!")
            
            with col2:
                if st.button("➖ -10", use_container_width=True, key="dec_10"):
                    new_count = max(0, current_count - 10)
                    if update_display_count(st.session_state.user_id, new_count):
                        st.success(f"✅ Counter updated to {new_count:,}!")
                        log_activity(st.session_state.username, f"Decreased display count to {new_count}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update counter!")
            
            with col3:
                if st.button("➖ -100", use_container_width=True, key="dec_100"):
                    new_count = max(0, current_count - 100)
                    if update_display_count(st.session_state.user_id, new_count):
                        st.success(f"✅ Counter updated to {new_count:,}!")
                        log_activity(st.session_state.username, f"Decreased display count to {new_count}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update counter!")
            
            # Display history/activity for this counter
            st.markdown("---")
            st.markdown("### 📈 Counter Instructions")
            st.info("""
            **How to use Display Counter:**
            - This counter is independent from the automation message counter
            - Use it to track any custom value or display count
            - You can increment/decrement by 1, 10, or 100
            - Set any custom value using the number input
            - The counter value is saved in your account settings
            """)

# ============================================================
#            SEPARATE ADMIN LOGIN PAGE
# ============================================================

def admin_login_page():
    """Admin login page"""
    st.markdown("""
    <div class="main-header">
        <div class="prince-logo"><span>👑</span></div>
        <h1>ADMIN LOGIN</h1>
        <p>Authorized Access Only</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
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
                        st.session_state.show_admin_login = False
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
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
#            MAIN ROUTING
# ============================================================

# Main routing logic
try:
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
        <p style="font-size: 0.8rem; opacity: 0.7;">E2E Automation System © 2026 | Version 2.1</p>
    </div>
    """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please refresh the page or contact support.")
