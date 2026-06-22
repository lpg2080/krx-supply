from pykrx import stock
from datetime import datetime, timedelta
import csv, time, re, io, urllib.request   # 기존 import 옆에 추가

WATCHLIST_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTYxJDl6v2PmzXOunftlSbhTnBngo2U3U1Id-obaTQDa85uhmdKAj1a5myqaJCVYKVBX9bMImdqwu8j/pub?gid=1188527226&single=true&output=csv"
FALLBACK = [
    "005930", "352820", "178920", "036570", "108320", "064260", "485540",
    "411060", "376300", "361610", "462870", "002310", "336260", "138930",
    "000660", "421320", "469070", "396500", "487240", "487230", "189300",
    "0025N0", "0167A0", "138540", "469150", "000250", "0173Y0", "462010",
    "0190C0", "009150", "011070", "001820", "222800", "195870", "353200",
    "007660", "007810", "000150", "042700", "067310", "033640", "036540",
    "089030", "131970", "005290", "101490", "357780", "036930", "240810",
    "084370", "265520", "403870", "000990", "440110", "298040", "267260",
    "034020", "322000", "010120", "062040", "099320", "012450", "047810",
    "211270", "462350", "001430", "347700", "005380", "012330", "086280",
    "011210", "064350", "307950", "204320", "018880", "005850", "010690",
    "003690", "402340", "017670", "005490", "006400", "086520", "247540",
    "066970", "277810", "454910", "108490", "090360", "058610", "035420",
    "035720", "373220", "267250", "278470", "003230", "004370", "003490",
    "079550",
]   # 원하면 기존 종목 리스트를 백업으로 넣어두면, 시트 접속 실패 시에도 돌아감

def load_tickers():
    try:
        raw = urllib.request.urlopen(WATCHLIST_CSV).read().decode("utf-8")
    except Exception as e:
        print("워치리스트 로드 실패, 폴백 사용:", e)
        return FALLBACK
    rows = list(csv.reader(io.StringIO(raw)))
    col = 0
    if rows and "종목코드" in [c.strip() for c in rows[0]]:
        col = [c.strip() for c in rows[0]].index("종목코드")
        rows = rows[1:]                      # 헤더 한 줄 건너뜀
    out, seen = [], set()
    for row in rows:
        if col >= len(row):
            continue
        t = row[col].strip().upper()
        if t.isdigit():
            t = t.zfill(6)                   # 5930 → 005930 (0 복원)
        if re.fullmatch(r"[0-9A-Z]{6}", t) and any(ch.isdigit() for ch in t):
            if t not in seen:                # 중복 제거
                seen.add(t); out.append(t)
    return out

tickers = load_tickers()
print("불러온 종목 수:", len(tickers))

todate   = datetime.today().strftime("%Y%m%d")
fromdate = (datetime.today() - timedelta(days=40)).strftime("%Y%m%d")   # ← 14→40 (20거래일 확보)
rows = []
for t in tickers:
    try:
        flow = stock.get_market_trading_value_by_date(fromdate, todate, t)   # ← .tail(5) 제거
        d1, d5, d20 = flow.tail(1), flow.tail(5), flow.tail(20)
        f_  = int(d5["외국인합계"].sum() / 1e8)          # 5일 (엔진)
        i_  = int(d5["기관합계"].sum() / 1e8)
        f1  = round(d1["외국인합계"].sum() / 1e8, 1)      # 당일 (관찰)
        i1  = round(d1["기관합계"].sum() / 1e8, 1)
        f20 = round(d20["외국인합계"].sum() / 1e8, 1)     # 20일 (관찰)
        i20 = round(d20["기관합계"].sum() / 1e8, 1)
        rows.append([t, f_, i_, f1, i1, f20, i20])
    except Exception as e:
        print(f"[{t}] 오류: {e}")
        rows.append([t, "", "", "", "", "", ""])
    time.sleep(0.3)
with open("supply.csv", "w", newline="", encoding="utf-8") as fp:
    w = csv.writer(fp)
    w.writerow(["종목코드", "외국인순매수", "기관순매수", "외인당일", "기관당일", "외인20일", "기관20일"])
    w.writerows(rows)
print("done")
