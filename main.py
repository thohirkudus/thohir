from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import pandas as pd
import time

app = FastAPI(title="IDX Pro Terminal - God Tier", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ONLINE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRjsZ629EKwHrlOq-YRzofvZAZYrjlRrFzwGvqdYqu2F5MZt1oP9L3Fqe-flTl1HDH72ziVeHZkvPmR/pub?gid=573611628&single=true&output=csv"

# ==========================================
# FUNGSI PEMBERSIH ANGKA (ANTI-ERROR KOMA)
# ==========================================
def safe_float(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip()
    if not val_str or val_str.upper() == 'NAN' or val_str == '-':
        return 0.0
    
    # Hapus simbol yang tidak perlu
    val_str = val_str.replace('Rp', '').replace('$', '').replace('%', '').strip()
    
    # Logika Cerdas Pemisah Ribuan/Desimal
    if '.' in val_str and ',' in val_str:
        if val_str.rfind(',') > val_str.rfind('.'):
            # Format Indo: 1.234,56 -> 1234.56
            val_str = val_str.replace('.', '').replace(',', '.')
        else:
            # Format US: 1,234.56 -> 1234.56
            val_str = val_str.replace(',', '')
    elif ',' in val_str:
        # Hanya koma, asumsikan desimal Indo
        val_str = val_str.replace(',', '.')
        
    try:
        return float(val_str)
    except ValueError:
        return 0.0

# ==========================================
# FRONTEND / HTML TERMINAL DEWA
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return """
    <!DOCTYPE html>
    <html lang="id" class="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IDX QUANT ⚡ GOD TIER TERMINAL</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {
                darkMode: 'class',
                theme: {
                    extend: {
                        fontFamily: { sans: ['Inter', 'sans-serif'], mono: ['Fira Code', 'monospace'] },
                        colors: {
                            base: '#050505', surface: '#0a0a0a', panel: '#121212',
                            border: '#262626', neon: '#00ff88', danger: '#ff3366',
                            whale: '#00e5ff', alpha: '#b300ff', warning: '#f59e0b'
                        }
                    }
                }
            }
        </script>
        <style>
            body { background-color: #050505; color: #e5e5e5; }
            .glass-panel { background: rgba(18, 18, 18, 0.7); backdrop-filter: blur(12px); border: 1px solid #262626; }
            .text-glow-neon { text-shadow: 0 0 10px rgba(0, 255, 136, 0.4); }
            .text-glow-danger { text-shadow: 0 0 10px rgba(255, 51, 102, 0.4); }
            ::-webkit-scrollbar { width: 4px; height: 4px; }
            ::-webkit-scrollbar-track { background: #050505; }
            ::-webkit-scrollbar-thumb { background: #262626; border-radius: 2px; }
            ::-webkit-scrollbar-thumb:hover { background: #404040; }
            table { border-spacing: 0; }
            tr:hover td { background-color: rgba(255, 255, 255, 0.03); }
        </style>
    </head>
    <body class="min-h-screen flex flex-col font-sans antialiased selection:bg-neon selection:text-black text-sm">

        <!-- NAVBAR -->
        <header class="glass-panel sticky top-0 z-50 px-4 py-3 flex justify-between items-center">
            <div class="flex items-center gap-4">
                <div class="w-8 h-8 rounded bg-gradient-to-br from-neon to-blue-600 flex items-center justify-center shadow-[0_0_15px_rgba(0,255,136,0.3)]">
                    <i class="fa-solid fa-bolt text-black text-lg"></i>
                </div>
                <div>
                    <h1 class="font-bold text-lg tracking-widest text-white leading-tight">IDX<span class="text-neon">QUANT</span></h1>
                    <div class="flex items-center gap-2 text-[10px] font-mono text-gray-500 uppercase tracking-wider">
                        <span class="relative flex h-2 w-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon opacity-75"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-neon"></span></span>
                        Real-Time Institutional Engine
                    </div>
                </div>
            </div>
            
            <div class="flex gap-4">
                <div class="glass-panel px-4 py-1.5 rounded flex flex-col items-end">
                    <span class="text-[9px] text-gray-500 font-mono">IHSG COMPOSITE</span>
                    <div class="flex items-baseline gap-2">
                        <span id="ihsgPrice" class="font-mono font-bold text-white text-base">---</span>
                        <span id="ihsgChange" class="font-mono font-bold text-neon text-xs">---</span>
                    </div>
                </div>
            </div>
        </header>

        <!-- MAIN TERMINAL -->
        <main class="flex-1 w-full p-4 flex flex-col gap-4">
            
            <!-- TOP METRICS ROW -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="glass-panel p-4 rounded flex justify-between items-center border-l-2 border-l-whale">
                    <div>
                        <div class="text-[10px] text-gray-400 font-mono mb-1">SMART MONEY FLOW</div>
                        <div class="font-mono text-xl font-bold text-white" id="whaleCount">0 <span class="text-sm text-whale">AKUMULASI</span></div>
                    </div>
                    <i class="fa-solid fa-water text-2xl text-gray-700"></i>
                </div>
                <div class="glass-panel p-4 rounded flex justify-between items-center border-l-2 border-l-alpha">
                    <div>
                        <div class="text-[10px] text-gray-400 font-mono mb-1">AVG MARKET ALPHA</div>
                        <div class="font-mono text-xl font-bold text-white" id="avgAlpha">0.00%</div>
                    </div>
                    <i class="fa-solid fa-rocket text-2xl text-gray-700"></i>
                </div>
                <div class="glass-panel p-4 rounded flex justify-between items-center border-l-2 border-l-neon">
                    <div>
                        <div class="text-[10px] text-gray-400 font-mono mb-1">INSTITUTIONAL BUYS</div>
                        <div class="font-mono text-xl font-bold text-white" id="buyCount">0 <span class="text-sm text-neon">SIGNALS</span></div>
                    </div>
                    <i class="fa-solid fa-arrow-up-right-dots text-2xl text-gray-700"></i>
                </div>
                <div class="glass-panel p-4 rounded flex justify-between items-center border-l-2 border-l-warning">
                    <div>
                        <div class="text-[10px] text-gray-400 font-mono mb-1">VWAP BREAKOUT</div>
                        <div class="font-mono text-xl font-bold text-white" id="vwapCount">0 <span class="text-sm text-warning">EMITEN</span></div>
                    </div>
                    <i class="fa-solid fa-crosshairs text-2xl text-gray-700"></i>
                </div>
            </div>

            <!-- CONTROLS -->
            <div class="glass-panel p-2 rounded flex justify-between items-center gap-4">
                <div class="relative w-full max-w-md">
                    <i class="fa-solid fa-terminal absolute left-3 top-2.5 text-gray-600 text-xs"></i>
                    <input type="text" id="searchInput" placeholder="> grep emiten..." 
                        class="w-full bg-base border border-border rounded pl-8 pr-3 py-1.5 text-xs text-neon focus:outline-none focus:border-neon font-mono placeholder-gray-700 transition">
                </div>
                <button onclick="fetchMarketData()" class="bg-border hover:bg-gray-800 text-white font-mono px-4 py-1.5 rounded text-xs transition flex items-center gap-2 border border-gray-700">
                    <i class="fa-solid fa-rotate-right"></i> EXECUTE REFRESH
                </button>
            </div>

            <!-- QUANT DATA GRID -->
            <div class="glass-panel rounded flex-1 overflow-hidden flex flex-col">
                <div class="overflow-x-auto">
                    <table class="w-full text-left whitespace-nowrap">
                        <thead class="bg-surface border-b border-border text-[10px] text-gray-400 font-mono uppercase">
                            <tr>
                                <th class="px-4 py-3 font-semibold">Kode Saham</th>
                                <th class="px-4 py-3 font-semibold text-right">Close</th>
                                <th class="px-4 py-3 font-semibold text-right">Chg%</th>
                                <th class="px-4 py-3 font-semibold text-center">Vol Institusi</th>
                                <th class="px-4 py-3 font-semibold text-center">Posisi VWAP</th>
                                <th class="px-4 py-3 font-semibold text-center">Alpha</th>
                                <th class="px-4 py-3 font-semibold text-center">Risk / Reward (TP & SL)</th>
                                <th class="px-4 py-3 font-semibold text-center">Rekomendasi Final</th>
                            </tr>
                        </thead>
                        <tbody id="stockTableBody" class="font-mono text-[11px] divide-y divide-border">
                            <tr><td colspan="8" class="p-8 text-center text-gray-600">Syncing with Google Sheets Data...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>

        <script>
            let allStocks = [];

            async function fetchMarketData() {
                try {
                    const response = await fetch('/api/market-data');
                    const data = await response.json();
                    
                    document.getElementById('ihsgPrice').textContent = data.ihsg.price.toLocaleString('id-ID', {minimumFractionDigits: 2});
                    const changeElem = document.getElementById('ihsgChange');
                    changeElem.textContent = (data.ihsg.change >= 0 ? '+' : '') + data.ihsg.change.toFixed(2) + '%';
                    changeElem.className = data.ihsg.change >= 0 ? 'font-mono font-bold text-neon text-xs text-glow-neon' : 'font-mono font-bold text-danger text-xs text-glow-danger';

                    allStocks = data.stocks;
                    
                    const accum = allStocks.filter(s => (s.vol_status || '').toUpperCase().includes('AKUM') || (s.vol_status || '').toUpperCase().includes('PAUS')).length;
                    document.getElementById('whaleCount').innerHTML = `${accum} <span class="text-sm text-whale">AKUMULASI</span>`;
                    
                    const avgAlpha = allStocks.reduce((sum, s) => sum + s.alpha, 0) / (allStocks.length || 1);
                    document.getElementById('avgAlpha').textContent = (avgAlpha >= 0 ? '+' : '') + avgAlpha.toFixed(2) + '%';
                    
                    const buys = allStocks.filter(s => (s.rekomendasi || '').toUpperCase().includes('BUY') || (s.rekomendasi || '').toUpperCase().includes('BELI')).length;
                    document.getElementById('buyCount').innerHTML = `${buys} <span class="text-sm text-neon">SIGNALS</span>`;
                    
                    const vwapBreak = allStocks.filter(s => (s.vwap || '').toUpperCase().includes('ATAS') || (s.vwap || '').toUpperCase().includes('BREAK')).length;
                    document.getElementById('vwapCount').innerHTML = `${vwapBreak} <span class="text-sm text-warning">BREAKOUT</span>`;

                    renderTable(allStocks);
                } catch (error) {
                    console.error("Fetch error:", error);
                }
            }

            function renderTable(stocks) {
                const tbody = document.getElementById('stockTableBody');
                tbody.innerHTML = '';

                if (stocks.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-gray-600">No data available.</td></tr>`;
                    return;
                }

                stocks.forEach(stock => {
                    const isPos = stock.change >= 0;
                    const alphaPos = stock.alpha > 0;
                    
                    let volBadge = `<span class="bg-gray-800 text-gray-300 px-2 py-0.5 rounded border border-gray-600">${stock.vol_status}</span>`;
                    if (stock.vol_status.toUpperCase().includes('AKUMULASI') || stock.vol_status.toUpperCase().includes('PAUS')) {
                        volBadge = `<span class="bg-blue-900/40 text-whale px-2 py-0.5 rounded border border-whale/50 font-bold shadow-[0_0_8px_rgba(0,229,255,0.3)]">${stock.vol_status}</span>`;
                    }

                    let vwapBadge = `<span class="text-gray-400">${stock.vwap}</span>`;
                    if (stock.vwap.toUpperCase().includes('ATAS') || stock.vwap.toUpperCase().includes('ALIGNED')) {
                        vwapBadge = `<span class="text-warning font-bold"><i class="fa-solid fa-crosshairs mr-1"></i>${stock.vwap}</span>`;
                    } else if (stock.vwap.toUpperCase().includes('BAWAH')) {
                        vwapBadge = `<span class="text-danger"><i class="fa-solid fa-arrow-down mr-1"></i>${stock.vwap}</span>`;
                    }

                    const tpText = stock.tp > 0 ? stock.tp.toLocaleString('id-ID') : '-';
                    const slText = stock.sl > 0 ? stock.sl.toLocaleString('id-ID') : '-';
                    let riskRewardBadge = `<div class="flex items-center justify-center gap-2">
                        <span class="text-neon border border-neon/30 bg-neon/10 px-1.5 py-0.5 rounded">TP: ${tpText}</span>
                        <span class="text-danger border border-danger/30 bg-danger/10 px-1.5 py-0.5 rounded">SL: ${slText}</span>
                    </div>`;

                    let recBadge = `<span class="text-gray-400">${stock.rekomendasi}</span>`;
                    if (stock.rekomendasi.toUpperCase().includes('BUY') || stock.rekomendasi.toUpperCase().includes('BELI')) {
                        recBadge = `<span class="bg-emerald-900/40 text-neon px-2 py-1 rounded border border-neon/50 font-bold">${stock.rekomendasi}</span>`;
                    } else if (stock.rekomendasi.toUpperCase().includes('SELL') || stock.rekomendasi.toUpperCase().includes('JUAL')) {
                        recBadge = `<span class="bg-rose-900/40 text-danger px-2 py-1 rounded border border-danger/50 font-bold">${stock.rekomendasi}</span>`;
                    }

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="px-4 py-2.5">
                            <div class="font-bold text-white tracking-widest text-xs flex items-center gap-2">
                                ${stock.ticker} 
                                <span class="text-[9px] bg-gray-800 text-gray-400 px-1 rounded">${stock.sector}</span>
                            </div>
                            <div class="text-[9px] text-gray-400 mt-1">${stock.candle}</div>
                        </td>
                        <td class="px-4 py-2.5 text-right font-bold text-white text-xs">${stock.price.toLocaleString('id-ID')}</td>
                        <td class="px-4 py-2.5 text-right font-bold ${isPos ? 'text-neon text-glow-neon' : 'text-danger text-glow-danger'}">${isPos ? '+' : ''}${stock.change.toFixed(2)}%</td>
                        <td class="px-4 py-2.5 text-center">${volBadge}</td>
                        <td class="px-4 py-2.5 text-center">${vwapBadge}</td>
                        <td class="px-4 py-2.5 text-center font-bold ${alphaPos ? 'text-alpha' : 'text-gray-500'}">${alphaPos ? '+' : ''}${stock.alpha.toFixed(2)}%</td>
                        <td class="px-4 py-2.5 text-center">${riskRewardBadge}</td>
                        <td class="px-4 py-2.5 text-center">${recBadge}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            document.getElementById('searchInput').addEventListener('input', (e) => {
                const keyword = e.target.value.toLowerCase();
                const filtered = allStocks.filter(s => s.ticker.toLowerCase().includes(keyword) || s.sector.toLowerCase().includes(keyword));
                renderTable(filtered);
            });

            fetchMarketData();
            setInterval(fetchMarketData, 10000);
        </script>
    </body>
    </html>
    """

# ==========================================
# BACKEND / API DATA PARSER
# ==========================================
@app.get("/api/market-data")
async def get_market_data():
    data_list = []
    index_price, index_change = 0.0, 0.0
    
    try:
        forced_url = f"{ONLINE_CSV_URL}&_t={int(time.time())}"
        df = pd.read_csv(forced_url)
        df.columns = df.columns.str.strip()

        for _, row in df.iterrows():
            ticker = str(row.get('KODE SAHAM', '')).replace(' ', '').strip().upper()
            if not ticker or ticker == 'NAN' or ticker == 'KODESAHAM': 
                continue
            
            # Parsing Harga menggunakan fungsi pembersih koma/titik
            close_price = safe_float(row.get('Close', 0))
            open_price = safe_float(row.get('Open', 0))
            
            # Kalkulasi manual persentase perubahan (Change)
            if open_price > 0:
                change = ((close_price - open_price) / open_price) * 100
            else:
                change = 0.0

            # Deteksi Baris IHSG / COMPOSITE Super Agresif
            if ticker in ["COMPOSITE", "IHSG", "INDEX:JKSE", "JKSE", "^JKSE", "IDX:COMPOSITE"]:
                index_price = close_price
                index_change = change
                continue # Agar IHSG tidak ter-render sebagai emiten biasa di tabel

            # Parsing sisa data
            sector = str(row.get('SEKTOR', 'N/A')).strip()
            vol_status = str(row.get('Status Volume Institusi', 'N/A')).strip()
            vwap_status = str(row.get('Posisi vs VWAP', 'N/A')).strip()
            
            alpha_val = safe_float(row.get('Alpha (Excess Return)', 0))
            macd_hist = safe_float(row.get('MACD Histogram', 0))
            
            rekomendasi = str(row.get('REKOMENDASI INSTITUSI FINAL', 'N/A')).strip()
            candle = str(row.get('POLA CANDLE', '')).strip()
            
            tp_val = safe_float(row.get('Target Take Profit (+3x ATR)', 0))
            sl_val = safe_float(row.get('Batas Stop Loss (-2x ATR)', 0))

            data_list.append({
                "ticker": ticker,
                "sector": sector,
                "price": close_price,
                "change": change,
                "vol_status": vol_status,
                "vwap": vwap_status,
                "alpha": alpha_val,
                "macd_hist": macd_hist,
                "tp": tp_val,
                "sl": sl_val,
                "rekomendasi": rekomendasi,
                "candle": candle
            })
            
    except Exception as e:
        print(f"⚠️ Kesalahan Parsing Data Asli: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "ihsg": {
            "price": index_price if index_price > 0 else 7724.80, # Angka aman jika masih terputus
            "change": index_change
        },
        "stocks": data_list
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
