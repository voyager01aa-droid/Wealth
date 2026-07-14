import yfinance as yf
import pandas as pd
import requests
import io
from datetime import datetime

def get_nifty500_tickers():
    try:
        # NSE ki official website se Nifty 500 ki list fetch karna
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers)
        df = pd.read_csv(io.StringIO(res.text))
        
        # Yahoo Finance ke liye ticker ke aage '.NS' jodna zaroori hai
        tickers = [str(sym).strip() + ".NS" for sym in df['Symbol']]
        return tickers
    except Exception as e:
        print(f"Error fetching Nifty 500 list from NSE: {e}")
        # Fallback list agar NSE ka server down ho
        return ["RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "SBIN.NS", "INFY.NS"]

def analyze_stocks():
    tickers = get_nifty500_tickers()
    print(f"🔥 Total Tickers Loaded: {len(tickers)}. Starting Bulk Scan...")
    
    # TIGDAM: Ek hi baar mein saare 500 stocks ka 1 mahine ka data download karna (Super Fast)
    data = yf.download(tickers, period="1mo", group_by='ticker', progress=False)
    
    bullish_stocks = []
    
    for ticker in tickers:
        try:
            # Check agar bulk data mein ye stock available hai
            if ticker not in data.columns.levels[0]:
                continue
                
            hist = data[ticker].dropna()
            if len(hist) < 20:
                continue
                
            # Technical Calculations
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            last_close = hist['Close'].iloc[-1]
            sma_20 = hist['SMA_20'].iloc[-1]
            vol_today = hist['Volume'].iloc[-1]
            vol_avg = hist['Volume'].rolling(window=5).mean().iloc[-1]
            
            # STRICT INTRADAY BULLISH FILTER
            # 1. Price 20 SMA ke upar ho (Up-trend)
            # 2. Aaj ka volume pichle 5 din ke average volume se kam se kam 2 guna (2x) zyada ho
            if last_close > sma_20 and vol_today > (vol_avg * 2.0):
                
                entry = round(last_close, 2)
                # Midcap/Smallcap (Nifty 500) ke liye 2% Target aur 1% Stop Loss best hota hai
                target = round(entry + (entry * 0.02), 2) 
                stop_loss = round(entry - (entry * 0.01), 2)
                vol_multiplier = round(vol_today / vol_avg, 1)
                
                bullish_stocks.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry": entry,
                    "Target": target,
                    "Stop Loss": stop_loss,
                    "Volume_Surg": vol_multiplier,
                    "Reason": f"🔥 Volume Breakout ({vol_multiplier}x) + Bullish Momentum"
                })
        except Exception as e:
            continue
            
    # Saare filtered stocks mein se top 10 wahi chunenge jisme sabse bhayanak Volume Surge hua ho
    bullish_stocks.sort(key=lambda x: x['Volume_Surg'], reverse=True)
    return bullish_stocks[:10]

def generate_html(stocks):
    html_content = """
    <html>
    <head>
        <title>Nifty 500 Pre-Market Alpha Screener</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; padding: 30px; }
            h1 { color: #38bdf8; text-align: center; font-size: 28px; margin-bottom: 5px; }
            .subtitle { text-align: center; color: #94a3b8; margin-bottom: 30px; }
            table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            th, td { padding: 15px; text-align: center; border-bottom: 1px solid #334155; }
            th { background-color: #0284c7; color: white; font-weight: 600; text-transform: uppercase; font-size: 13px; }
            tr:hover { background-color: #334155; }
            .target-txt { color: #4ade80; font-weight: bold; }
            .sl-txt { color: #f87171; font-weight: bold; }
            .badge { background: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>🚀 Nifty 500 Top 10 Bullish Stocks</h1>
        <div class="subtitle">Updated Auto-Pilot: """ + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + """ IST</div>
        <table>
            <tr>
                <th>Stock Name</th>
                <th>Entry Trigger (₹)</th>
                <th>Target (2%) (₹)</th>
                <th>Stop Loss (1%) (₹)</th>
                <th>AI Analysis / Reason</th>
            </tr>
    """
    
    if not stocks:
        html_content += "<tr><td colspan='5' style='padding:30px; color:#94a3b8;'>No high-probability setups found today. Keep your capital safe!</td></tr>"
    else:
        for s in stocks:
            html_content += f"""
            <tr>
                <td><span class="badge">{s['Stock']}</span></td>
                <td><strong>{s['Entry']}</strong></td>
                <td class="target-txt">{s['Target']}</td>
                <td class="sl-txt">{s['Stop Loss']}</td>
                <td style="text-align:left; padding-left:20px;">{s['Reason']}</td>
            </tr>
            """
            
    html_content += """
        </table>
        <p style="text-align:center; font-size:12px; color:#64748b; margin-top:30px;">
            Disclaimer: Educational tracking tool. Intraday trading involves high leverage risk. Maintain strict 1:2 Risk-Reward.
        </p>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("🚀 Nifty 500 Dashboard Generated Successfully!")

if __name__ == "__main__":
    top_stocks = analyze_stocks()
    generate_html(top_stocks)
