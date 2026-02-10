import os
import requests
import sys

# --- CONFIGURATION FROM ENVIRONMENT VARIABLES ---
# These are set in GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
THRESHOLD_PCR = 1.2  # Change this to your preferred alert level

def send_telegram(message):
    """Sends a notification to your Telegram Bot."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Error: Telegram credentials missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Telegram notification sent.")
    except Exception as e:
        print(f"❌ Failed to send Telegram: {e}")

def fetch_sensibull_pcr():
    """Fetches the latest PCR value from Sensibull."""
    url = "https://oxide.sensibull.com/v1/compute/compute_intraday"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://web.sensibull.com/",
        "Content-Type": "application/json"
    }
    payload_body = {
        "underlying": "NIFTY",
        "interval": "5M",
        "chart_keys": ["pcr"],
        "update_atm": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload_body, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Data path: payload -> chart_data -> {timestamp} -> pcr_data -> pcr
        chart_data = data.get('payload', {}).get('chart_data', {})
        if chart_data:
            # Get the most recent timestamp (last key in the dictionary)
            latest_ts = sorted(chart_data.keys())[-1]
            pcr = chart_data[latest_ts].get('pcr_data', {}).get('pcr')
            return pcr, latest_ts
    except Exception as e:
        print(f"❌ Data Fetch Error: {e}")
    return None, None

def main():
    print("--- PCR Monitor Execution Start ---")
    pcr_value, timestamp = fetch_sensibull_pcr()
    
    if pcr_value is not None:
        print(f"Latest PCR: {pcr_value} at {timestamp}")
        
        if pcr_value >= THRESHOLD_PCR:
            alert_msg = (
                f"🚨 *PCR ALERT: {pcr_value}*\n"
                f"🕒 Time: {timestamp}\n"
                f"📈 Status: Threshold ({THRESHOLD_PCR}) reached."
            )
            send_telegram(alert_msg)
        else:
            print(f"PCR is {pcr_value}, which is below threshold {THRESHOLD_PCR}. No alert sent.")
    else:
        print("Could not retrieve PCR data. API might be down or structure changed.")
    
    print("--- Execution Finished ---")

if __name__ == "__main__":
    main()
