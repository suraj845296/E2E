# ============================================================
# COOKIES UPLOAD SECTION - ADD THIS IN CONFIGURATION TAB
# ============================================================

st.markdown("---")
st.markdown("### 🍪 Cookies Upload")

# Show existing cookies status
existing_cookies = user_config.get('cookies', '')
if existing_cookies:
    # Try to show how many cookies are stored
    cookie_lines = existing_cookies.strip().split('\n')
    st.success(f"🍪 {len(cookie_lines)} cookies currently stored")
    
    with st.expander("📋 View Current Cookies", expanded=False):
        st.code(existing_cookies[:500] + ("..." if len(existing_cookies) > 500 else ""), language="text")

# Cookies upload methods
col1, col2 = st.columns(2)

with col1:
    # Option 1: Upload cookies file
    uploaded_file = st.file_uploader(
        "📁 Upload Cookies File",
        type=['txt', 'json', 'cookies'],
        help="Upload .txt, .json, or .cookies file",
        key="cookies_uploader"
    )
    
    if uploaded_file:
        try:
            # Try reading as text first
            cookies_content = uploaded_file.getvalue().decode('utf-8')
            
            # If it's JSON, try to parse and format
            try:
                import json
                cookies_json = json.loads(cookies_content)
                if isinstance(cookies_json, list):
                    # Format as Netscape cookie format or keep as JSON
                    # For facebook/instagram automation, convert to Netscape format
                    formatted = "# Netscape HTTP Cookie File\n"
                    for c in cookies_json:
                        domain = c.get('domain', '')
                        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                        path = c.get('path', '/')
                        secure = 'TRUE' if c.get('secure', False) else 'FALSE'
                        expiry = c.get('expiry', c.get('expirationDate', ''))
                        if not expiry:
                            expiry = '9999999999'
                        name = c.get('name', '')
                        value = c.get('value', '')
                        formatted += f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n"
                    cookies_content = formatted
            except:
                pass  # Keep as plain text
            
            # Preview first 500 chars
            preview = cookies_content[:500]
            st.info(f"📄 File loaded! Size: {len(cookies_content)} characters")
            with st.expander("👁️ Preview", expanded=False):
                st.code(preview + ("..." if len(cookies_content) > 500 else ""), language="text")
            
            # Save button for uploaded cookies
            if st.button("💾 Save Uploaded Cookies", key="save_uploaded_cookies"):
                user_config_current = get_user_config(st.session_state.user_id)
                if user_config_current:
                    success = update_user_config(
                        st.session_state.user_id,
                        user_config_current['chat_id'],
                        user_config_current['name_prefix'],
                        user_config_current['delay'],
                        cookies_content,
                        user_config_current['messages'],
                        user_config_current.get('auto_reply_enabled', False),
                        user_config_current.get('auto_reply_message', '')
                    )
                    if success:
                        st.success("✅ Cookies saved from file!")
                        log_activity(st.session_state.username, f"Uploaded cookies file: {uploaded_file.name}")
                        st.rerun()
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

with col2:
    # Option 2: Paste cookies manually
    st.markdown("**📝 OR Paste Cookies Manually**")
    
    cookies_text = st.text_area(
        "Paste Cookies Here",
        value=existing_cookies,
        placeholder="Paste cookies in Netscape format or JSON...\n\nFormat 1 (Netscape):\n.facebook.com\tTRUE\t/\tTRUE\t12345\tcookie_name\tcookie_value\n\nFormat 2 (JSON):\n[{\"domain\":\".facebook.com\",\"name\":\"c_user\",\"value\":\"123456\"}]",
        height=200,
        key="cookies_text_input"
    )
    
    if cookies_text != existing_cookies:
        if st.button("💾 Save Pasted Cookies", key="save_pasted_cookies"):
            user_config_current = get_user_config(st.session_state.user_id)
            if user_config_current:
                success = update_user_config(
                    st.session_state.user_id,
                    user_config_current['chat_id'],
                    user_config_current['name_prefix'],
                    user_config_current['delay'],
                    cookies_text,
                    user_config_current['messages'],
                    user_config_current.get('auto_reply_enabled', False),
                    user_config_current.get('auto_reply_message', '')
                )
                if success:
                    st.success("✅ Cookies saved successfully!")
                    log_activity(st.session_state.username, "Updated cookies via paste")
                    st.rerun()

# Clear cookies button
if existing_cookies:
    if st.button("🗑️ Clear Cookies", key="clear_cookies"):
        user_config_current = get_user_config(st.session_state.user_id)
        if user_config_current:
            success = update_user_config(
                st.session_state.user_id,
                user_config_current['chat_id'],
                user_config_current['name_prefix'],
                user_config_current['delay'],
                '',  # Empty cookies
                user_config_current['messages'],
                user_config_current.get('auto_reply_enabled', False),
                user_config_current.get('auto_reply_message', '')
            )
            if success:
                st.warning("🗑️ Cookies cleared!")
                log_activity(st.session_state.username, "Cleared cookies")
                st.rerun()

st.markdown("---")
