import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Dispatch System - Live Dashboard", page_icon="🚛", layout="wide")

# Google Sheet की बेस लिंक
SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/1Rajn2oci_FNlzKXlnf7qo5JKH-JCznwzXUf7WlwQXl0/export?format=csv"

def get_shift_date():
    now = datetime.now()
    if now.hour < 6:
        return (now - timedelta(days=1)).strftime("%d.%m.%Y")
    return now.strftime("%d.%m.%Y")

# आज की तारीख का टैब आटोमैटिक फेच करने का तरीका
sheet_to_use = get_shift_date()

@st.cache_data(ttl=10) # इससे डेटा हर 10 सेकंड में ऑटोमैटिक रिफ्रेश होता रहेगा
def load_data(sheet_name):
    # सीधे आज की तारीख वाले टैब का नाम URL में जोड़ा गया है
    url = f"{SHEET_BASE_URL}&sheet={sheet_name}"
    try:
        df = pd.read_csv(url, header=2)
        if df.empty or len(df.columns) < 3:
            # अगर उस तारीख का टैब न मिले तो मास्टर या पहली शीट ले लेगा
            df = pd.read_csv(SHEET_BASE_URL, header=2)
    except:
        df = pd.read_csv(SHEET_BASE_URL, header=2)
    return df

df = load_data(sheet_to_use)

NOTICE_TXT_FILE = r"C:\Dispatch_System\notice.txt"

# --- OneSignal Auto-Notification Function ---
def send_push_notification(vehicle_number, destination, program_no="", loading_plan="", actual_ton="", action_type="New"):
    url = "https://onesignal.com/api/v1/notifications"
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Key os_v2_app_7vcfabewjrhabjuy4ohuncrfjgc2cgkoxaijoqmurxdsczkgqr2g7a2lvzderg2fkwujnlafpmqsdofc532qjtdv"
    }
    
    if action_type == "Final":
        status_text = "✅ गाड़ी फाइनल हो गई (Final)"
        details_text = f"Actual Tons:- {actual_ton} MT"
    elif action_type == "Updated":
        status_text = "✏️ रिकॉर्ड अपडेट हुआ (Updated)"
        details_text = f"Plan:- {loading_plan} | Actual:- {actual_ton} MT"
    else:
        status_text = "🆕 नई एंट्री (New Entry)"
        details_text = f"लोडिंग प्लान:- {loading_plan} MT"
        
    message_text = f"{status_text}\nगाड़ी न०:- {vehicle_number} | Desti.:- {destination}\n{details_text} | प्रोग्राम न०:- {program_no}"
    
    payload = {
        "app_id": "fd445004-964c-4e00-a698-e38f468a2549",
        "included_segments": ["All"],
        "headings": {"en": "🚨 Dispatch Alert"},
        "contents": {"en": message_text},
        "sound": "default",
        "android_sound": "default",
        "priority": 10
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print("OneSignal Response:", response.status_code, response.text)
    except Exception as e:
        print("Notification Error:", e)

def get_notice_from_txt():
    if os.path.exists(NOTICE_TXT_FILE):
        try:
            with open(NOTICE_TXT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return content
        except: pass
    return "😊 राधे - राधे 🚨 आवश्यक सूचना:- कृपया सभी गाड़ियों की लोडिंग समय पर पूरी करें!"

# --- Helper Function for Cleaning Program Number ---
def clean_prog_val(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']:
        return ''
    try:
        val_int = int(float(val))
        return str(val_int) if val_int != 0 else ''
    except:
        return str(val) if str(val).lower() != 'nan' else ''

# --- Helper Function for Cleaning Adv and Text Values ---
def clean_text_val(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']:
        return ''
    return str(val).strip()

# --- Session State Initialization ---
if "show_notif_list" not in st.session_state:
    st.session_state["show_notif_list"] = False

if "notification_history" not in st.session_state:
    st.session_state["notification_history"] = []

if "is_cleared" not in st.session_state:
    st.session_state["is_cleared"] = False

if "trigger_popup" not in st.session_state:
    st.session_state["trigger_popup"] = True

if "last_total_signature" not in st.session_state:
    st.session_state["last_total_signature"] = ""

# --- CSS Styling ---
st.markdown("""
    <style>
    @keyframes dot-blink {
        0% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0px red; }
        50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 10px red; }
        100% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0px red; }
    }
    
    @keyframes border-blink {
        0% { border-color: #b5651d; }
        50% { border-color: #ff4500; }
        100% { border-color: #b5651d; }
    }
    
    @keyframes yellow-card-blink {
        0% { background-color: #ffc107; color: #000; }
        50% { background-color: #ffeb3b; color: #000; box-shadow: 0 0 12px #ff9800; }
        100% { background-color: #ffc107; color: #000; }
    }
    
    html, body, [class*="css"], .custom-table th, .custom-table td { 
        font-family: 'Cambria', Georgia, serif !important; 
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0.3rem !important; max-width: 100% !important; overflow-x: hidden !important; }
    
    .box-full { 
        background-color: transparent; 
        border: none; 
        padding: 2px 4px; 
        border-radius: 0px; 
        height: 42px; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
        margin-bottom: 2px;
    }

    .main-title { font-size: 13px; font-weight: 900; color: #1F4E78; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin: 0; }
    .sub-title { font-size: 9.5px; font-weight: 600; color: #495057; margin: 0; }

    div.stButton > button {
        background-color: #f8f9fa !important;
        border: 1px solid #ced4da !important;
        padding: 2px 4px !important;
        font-size: 10px !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        height: 34px !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        background-color: #e2e6ea !important;
        border-color: #adb5bd !important;
    }

    .card-cyan { background-color: #0dcaf0; color: #000; padding: 6px; border-radius: 8px; text-align: center; }
    .card-gray { background-color: #495057; color: white; padding: 6px; border-radius: 8px; text-align: center; }
    .card-orange-blink { 
        background-color: #ffc107; 
        color: #000; 
        padding: 6px; 
        border-radius: 8px; 
        text-align: center; 
        animation: yellow-card-blink 1.2s infinite ease-in-out;
    }
    .card-green { background-color: #198754; color: white; padding: 6px; border-radius: 8px; text-align: center; }
    
    .card-title { font-size: 8.5px; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 11px; font-weight: 900; margin-top: 2px; }

    .grid-table { width: 100%; border-collapse: separate; border-spacing: 4px; margin-bottom: 4px; table-layout: fixed; }

    .notice-box {
        background: #fff3cd; 
        color: #856404; 
        padding: 3px; 
        font-weight: bold; 
        font-size: 15px; 
        border: 1px solid #ffeeba; 
        border-radius: 8px; 
        font-family: 'Cambria', Georgia, serif;
        margin-bottom: 4px !important;
    }

    .title-box { 
        border: 2px solid #b5651d; 
        border-radius: 6px; 
        padding: 6px 8px; 
        background-color: #fff8f0; 
        margin-top: 2px !important;
        display: flex;
        align-items: center;
        gap: 6px;
        width: 100%;
        box-sizing: border-box;
        animation: border-blink 1.5s infinite ease-in-out;
    }

    .live-dot {
        height: 8px;
        width: 8px;
        background-color: #ff0000;
        border-radius: 50%;
        display: inline-block;
        animation: dot-blink 1s infinite ease-in-out;
        flex-shrink: 0;
    }

    .box-title { 
        color: #b5651d; 
        font-weight: 900; 
        font-size: 12px;
        margin: 0;
    }

    .table-scroll-container {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: auto !important;
        border-radius: 6px;
        border: 1px solid #ddd;
        background: white;
        margin-top: 4px;
        margin-bottom: 6px;
        box-sizing: border-box;
    }
    
    .custom-table { 
        width: 100% !important; 
        border-collapse: collapse; 
        font-size: 8.5px !important; 
        background-color: white; 
    }
    .custom-table th { 
        background-color: #1F4E78; 
        color: white; 
        padding: 4px 2px !important; 
        text-align: center; 
        border: 1px solid #ddd; 
    }
    .custom-table td { 
        padding: 4px 2px !important; 
        text-align: center; 
        border: 1px solid #ddd; 
        color: #000; 
    }
    
    .vehicle-bold {
        font-weight: 900 !important;
        font-size: 9.5px !important;
        color: #000 !important;
        white-space: nowrap !important;
    }

    .notif-card {
        background-color: #F3F0FA;
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        font-size: 12px;
        color: #000;
    }
    
    .popup-card {
        background-color: #F3F0FA;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 13px;
        color: #000;
        margin-bottom: 10px;
        line-height: 1.4;
    }

    div[data-testid="stDialog"] h3, div[data-testid="stDialog"] [data-testid="stMarkdownContainer"] h3 {
        font-size: 13px !important;
        font-weight: bold !important;
        color: #b5651d !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

try:
    if not df.empty:
        df.columns = df.columns.astype(str).str.strip()
        
        col_veh = next((c for c in df.columns if 'vehicle' in c.lower()), df.columns[4] if len(df.columns) > 4 else df.columns[0])
        col_plan = next((c for c in df.columns if 'plan' in c.lower()), None)
        col_actual = next((c for c in df.columns if 'actual' in c.lower()), None)
        col_time = next((c for c in df.columns if 'time' in c.lower()), None)
        col_trans = next((c for c in df.columns if 'transport' in c.lower()), None)
        col_dest = next((c for c in df.columns if 'destination' in c.lower() or 'destinations' in c.lower()), None)
        col_prog = next((c for c in df.columns if 'prog' in c.lower() or 'pro' in c.lower()), None)
        
        col_adv = next((c for c in df.columns if c.lower() == 'adv' or c.lower() == 'advance'), None)
        if col_adv:
            if df[col_adv].isna().all() or (df[col_adv].astype(str).str.lower().isin(['nan', 'none', '']).all()):
                col_adv = None
        
        col_status = None
        for col in df.columns:
            if 'current status' in col.lower() or col.lower() == 'status':
                col_status = col
                break
        if not col_status:
            col_status = df.columns[-1]
        
        if col_veh: df = df.dropna(subset=[col_veh])
        total_vehicles = len(df)
        total_plan_mt = float(pd.to_numeric(df[col_plan], errors='coerce').sum()) if col_plan and not df.empty else 0.0
        
        ul_df = df[~df[col_status].astype(str).str.lower().str.contains('final', na=False)].copy() if col_status else pd.DataFrame()
        final_df = df[df[col_status].astype(str).str.lower().str.contains('final', na=False)] if col_status else pd.DataFrame()
        
        ul_plan_sum = float(pd.to_numeric(ul_df[col_plan], errors='coerce').sum()) if col_plan and not ul_df.empty else 0.0
        final_act_sum = float(pd.to_numeric(final_df[col_actual], errors='coerce').sum()) if final_df is not None and not final_df.empty else 0.0

        if not df.empty and not st.session_state["is_cleared"]:
            all_notifications = []
            for index, row in df.iterrows():
                v_veh = str(row.get(col_veh, ''))
                raw_prog = row.get(col_prog, '')
                v_prog = clean_prog_val(raw_prog)
                v_dest = str(row.get(col_dest, '')) if col_dest else '-'
                v_time = str(row.get(col_time, '')) if col_time and col_time in df.columns else datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                
                v_mt = row.get(col_actual, '')
                if pd.isna(v_mt) or str(v_mt) == '' or str(v_mt) == 'nan':
                    v_mt = row.get(col_plan, '0')
                
                v_status = str(row.get(col_status, '')).strip()
                if not v_status or v_status.lower() == 'nan':
                    v_status = 'Under Loading'

                if v_veh and v_veh != 'nan':
                    notif_dict = {
                        "time": v_time,
                        "status": v_status,
                        "vehicle": v_veh,
                        "prog": v_prog,
                        "dest": v_dest,
                        "mt": v_mt
                    }
                    if notif_dict not in all_notifications:
                        all_notifications.append(notif_dict)
            
            st.session_state["notification_history"] = list(reversed(all_notifications))

            target_row = df.iloc[-1]
            l_veh = str(target_row.get(col_veh, ''))
            l_status = str(target_row.get(col_status, '')).strip()
            if not l_status or l_status.lower() == 'nan':
                l_status = 'Under Loading'

            l_dest = str(target_row.get(col_dest, '')) if col_dest else '-'
            l_prog = clean_prog_val(target_row.get(col_prog, ''))
            
            l_mt = target_row.get(col_actual, '')
            if pd.isna(l_mt) or str(l_mt) == '' or str(l_mt) == 'nan':
                l_mt = target_row.get(col_plan, '0')

            current_total_signature = f"{len(df)}_${l_veh}_${l_status}"
            
            if st.session_state["last_total_signature"] != current_total_signature:
                st.session_state["trigger_popup"] = True
                st.session_state["last_total_signature"] = current_total_signature
                
                is_fin_check = any(w in l_status.lower().strip() for w in ['final', 'complete', 'dispatched', 'done', 'closed', 'finish'])
                act_type = "Final" if is_fin_check else "New"
                send_push_notification(l_veh, l_dest, l_prog, l_mt, l_mt, act_type)

        # --- UI Layout ---
        st.markdown(f'''
            <div class="box-full">
                <div class="main-title">🚛 M/s Surya Roshni Limited - Hindupur</div>
                <div class="sub-title">Smart Dispatch Management System ({sheet_to_use})</div>
            </div>
        ''', unsafe_allow_html=True)

        if st.session_state.get("show_notif_list", False):
            @st.dialog("📭 Notifications List")
            def show_notifications_popup():
                if st.session_state["notification_history"]:
                    for item in st.session_state["notification_history"][:10]:
                        prog_text = f" | Prog: {item['prog']}" if item['prog'] else ""
                        st.markdown(f"""
                            <div class="notif-card">
                                <b>Message Sent Date :</b> {item['time']}<br>
                                <b>Action Note :</b> Status - <span style="font-weight:bold;">{item['status']}</span><br>
                                <b>Vehicle Number :</b> {item['vehicle']}<br>
                                <b>Dispatch Text Details :</b><br>
                                📍 डेस्टिनेशन: {item['dest']}{prog_text} | ⚖️ लोडिंग: {item['mt']} MT
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.write("कोई नया नोटिफिकेशन नहीं है।")
                
                col_close1, col_close2 = st.columns(2)
                with col_close1:
                    if st.button("🗑️ Clear List", key="clear_notif_popup"):
                        st.session_state["notification_history"] = []
                        st.session_state["is_cleared"] = True
                        st.rerun()
                with col_close2:
                    if st.button("❌ Close", key="close_notif_popup"):
                        st.session_state["show_notif_list"] = False
                        st.rerun()

            show_notifications_popup()

        elif st.session_state.get("trigger_popup", True) and not df.empty:
            is_final = any(w in l_status.lower().strip() for w in ['final', 'complete', 'dispatched', 'done', 'closed', 'finish'])
            popup_title = "✅ Final Dispatch Alert" if is_final else "🚨 Under Loading Alert"

            @st.dialog(popup_title)
            def show_popup():
                prog_text = f" | Prog: {l_prog}" if l_prog and l_prog != 'nan' else ""
                st.markdown(f"""
                    <div class="popup-card">
                        <b>Action Note :</b> Status - <span style="font-weight:bold;">{l_status}</span><br>
                        <b>Vehicle Number :</b> {l_veh}<br>
                        <b>Dispatch Text Details :</b><br>
                        📍 डेस्टिनेशन: {l_dest}{prog_text} | ⚖️ लोडिंग: {l_mt} MT
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("✅ ठीक है (Close)", key="dialog_close_btn", use_container_width=True):
                    st.session_state["trigger_popup"] = False
                    st.rerun()

            show_popup()
        
        st.markdown(f"""
            <table class="grid-table">
                <tr>
                    <td style="width: 50%;"><div class="card-cyan"><div class="card-title">TOTAL IN PLANT</div><div class="card-value">{total_plan_mt:.2f} MT</div></div></td>
                    <td style="width: 50%;"><div class="card-gray"><div class="card-title">TOTAL Vehicle</div><div class="card-value">{total_vehicles}</div></div></td>
                </tr>
                <tr>
                    <td style="width: 50%;"><div class="card-orange-blink"><div class="card-title">⏳ UNDER LOADING Vehicle</div><div class="card-value">{len(ul_df)} Veh ({ul_plan_sum:.2f} MT)</div></div></td>
                    <td style="width: 50%;"><div class="card-green"><div class="card-title">FINAL Vehicle</div><div class="card-value">{len(final_df)} ({final_act_sum:.2f} MT Actual)</div></div></td>
                </tr>
            </table>
        """, unsafe_allow_html=True)
        
        notice_msg = get_notice_from_txt()
        st.markdown(f'<marquee class="notice-box">{notice_msg}</marquee>', unsafe_allow_html=True)
        
        if not ul_df.empty:
            cols = [c for c in [col_veh, col_time, col_trans, col_dest, col_plan, col_adv, col_prog] if c]
            df_view = ul_df[cols].copy()
            
            if col_veh in df_view.columns:
                df_view[col_veh] = df_view[col_veh].apply(lambda x: f'<span class="vehicle-bold">{x}</span>')

            if col_prog and col_prog in df_view.columns:
                df_view[col_prog] = df_view[col_prog].apply(clean_prog_val)

            if col_adv and col_adv in df_view.columns:
                df_view[col_adv] = df_view[col_adv].apply(clean_text_val)

            df_view.insert(0, 'Sr. No.', range(1, len(df_view) + 1))
            
            rename_dict = {
                col_veh: 'Vehicle No.', 
                col_time: 'Time', 
                col_trans: 'Transport Name', 
                col_dest: 'Destinations', 
                col_plan: 'Plan', 
                col_prog: 'Pro No.'
            }
            if col_adv:
                rename_dict[col_adv] = 'Adv'

            df_view = df_view.rename(columns=rename_dict)
            table_html = df_view.to_html(classes="custom-table", index=False, escape=False)
            
            st.markdown(f"""
                <div class="title-box">
                    <span class="live-dot"></span>
                    <div class="box-title">Under Loading Vehicles (Only View)</div>
                </div>
                <div class="table-scroll-container">
                    {table_html}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="title-box">
                    <span class="live-dot"></span>
                    <div class="box-title">Under Loading Vehicles (Only View)</div>
                </div>
                <p style="text-align:center; font-size:11px; margin:5px 0;">फिलहाल कोई अंडर लोडिंग गाड़ी नहीं है।</p>
            """, unsafe_allow_html=True)

        st.write("")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔔 View Alerts List", use_container_width=True):
                st.session_state["show_notif_list"] = True
                st.rerun()
                
        with col_btn2:
            if st.button("🔄 Refresh Dashboard", use_container_width=True):
                st.cache_data.clear()
                st.session_state["show_notif_list"] = False
                st.session_state["is_cleared"] = False
                st.session_state["trigger_popup"] = True
                send_push_notification(l_veh, l_dest, l_prog, l_mt, l_mt, "Updated")
                st.toast("डैशबोर्ड अपडेट हो गया!", icon="🚀")
                st.rerun()
    else:
        st.warning("गूगल शीट में कोई डेटा उपलब्ध नहीं है।")
except Exception as e:
    st.error(f"डेटा लोड करने में त्रुटि: {e}")
