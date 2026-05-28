import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# --- 페이지 설정 ---
st.set_page_config(
    page_title="토스 스타일 주식 분석기",
    page_icon="📈",
    layout="wide"
)

st.title("📈 토스증권 스타일 주식 수익률 비교 분석기")
st.markdown("여러 종목의 **누적 수익률**과 **차트**를 한눈에 비교해 보세요.")

# --- 사이드바: 설정 영역 ---
st.sidebar.header("🔍 설정")

# 기간 선택
today = datetime.date.today()
start_date = st.sidebar.date_input("시작일", today - datetime.timedelta(days=365))
end_date = st.sidebar.date_input("종료일", today)

# 비교할 주식 리스트
ticker_dict = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "에코프로비엠": "247540.KQ",
    "네이버(NAVER)": "035420.KS",
    "카카오": "035720.KS",
    "Apple (AAPL)": "AAPL",
    "Tesla (TSLA)": "TSLA",
    "NVIDIA (NVDA)": "NVDA",
    "Microsoft (MSFT)": "MSFT"
}

# 사용자 종목 선택
selected_names = st.sidebar.multiselect(
    "비교할 종목을 선택하세요 (여러 개 가능)",
    options=list(ticker_dict.keys()),
    default=["삼성전자", "Apple (AAPL)", "NVIDIA (NVDA)"]
)

# 커스텀 티커 입력 기능
custom_ticker = st.sidebar.text_input("리스트에 없는 티커 직접 입력 (예: 000270.KS 또는 AMZN)")
if custom_ticker:
    ticker_dict[custom_ticker] = custom_ticker
    if custom_ticker not in selected_names:
        selected_names.append(custom_ticker)

# --- 데이터 로드 및 가공 ---
if selected_names:
    selected_tickers = [ticker_dict[name] for name in selected_names]
    
    @st.cache_data(ttl=3600)
    def load_data(tickers, start, end):
        # 1. 안전하게 'Close' 또는 'Adj Close'를 명시해서 다운로드하거나 전체를 받은 뒤 추출합니다.
        # yfinance 최신 구조 대응을 위해 group_by='ticker' 옵션을 사용하면 다루기 더 쉽습니다.
        raw_data = yf.download(tickers, start=start, end=end, group_by='ticker')
        
        df_close = pd.DataFrame()
        
        # 단일 종목일 때와 다중 종목일 때 데이터 구조 분기 처리
        if len(tickers) == 1:
            ticker = tickers[0]
            # 단일 종목은 상위 멀티인덱스가 없을 수 있으므로 체크 후 가져옴
            if 'Adj Close' in raw_data.columns:
                df_close[ticker] = raw_data['Adj Close']
            else:
                df_close[ticker] = raw_data['Close']
        else:
            # 다중 종목일 경우 각 티커별로 'Adj Close' 또는 'Close' 추출
            for ticker in tickers:
                if ticker in raw_data.columns.levels[0]:
                    if 'Adj Close' in raw_data[ticker].columns:
                        df_close[ticker] = raw_data[ticker]['Adj Close']
                    else:
                        df_close[ticker] = raw_data[ticker]['Close']
                        
        return df_close

    try:
        df_close = load_data(selected_tickers, start_date, end_date)
        
        if df_close.empty:
            st.error("선택한 기간에 데이터가 존재하지 않습니다. 날짜를 다시 조정해 주세요.")
        else:
            # 이름 변경 (티커 -> 한글/영문 이름)
            inv_ticker_dict = {v: k for k, v in ticker_dict.items()}
            df_close = df_close.rename(columns=inv_ticker_dict)

            # 결측치 처리 (주말/휴일 등으로 인한 빈칸 채우기)
            df_close = df_close.ffill().bfill()

            # 누적 수익률 계산 (첫날 종가 대비 % 변화율)
            df_return = (df_close / df_close.iloc[0] - 1) * 100

            # --- 메인 화면 레이아웃 ---
            
            # 1. 최신 수익률 요약 메트릭
            st.subheader("📊 종목별 누적 수익률 요약")
            cols = st.columns(len(selected_names))
            
            for i, name in enumerate(selected_names):
                if name in df_return.columns:
                    current_return = df_return[name].iloc[-1]
                    current_price = df_close[name].iloc[-1]
                    
                    color_arrow = "🔺" if current_return >= 0 else "🔻"
                    
                    cols[i].metric(
                        label=name,
                        value=f"{current_price:,.2f}" if current_price > 100 else f"${current_price:,.2f}",
                        delta=f"{color_arrow} {current_return:.2f}%"
                    )

            st.markdown("---")

            # 2. 누적 수익률 차트
            st.subheader("📈 기간 내 누적 수익률 추이 (%)")
            st.line_chart(df_return)

            # 3. 데이터 상세 보기
            st.markdown("---")
            with st.expander("📄 주가 데이터 원본 보기"):
                st.dataframe(df_close, use_container_width=True)

    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
else:
    st.info("왼쪽 사이드바에서 비교할 종목을 선택해 주세요!")
