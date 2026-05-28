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

# 비교할 주식 리스트 (토스증권 인기 종목 기준 예시)
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

# 사용자 종목 선택 (다중 선택 가능)
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
    
    @st.cache_data(ttl=3600)  # 1시간 동안 데이터 캐싱하여 속도 향상
    def load_data(tickers, start, end):
        data = yf.download(tickers, start=start, end=end)['Adj Close']
        # 단일 종목 선택 시 Series가 반환되므로 DataFrame으로 변환
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])
        return data

    try:
        df_close = load_data(selected_tickers, start_date, end_date)
        
        # 이름 변경 (티커 -> 한글/영문 이름)
        inv_ticker_dict = {v: k for k, v in ticker_dict.items()}
        df_close = df_close.rename(columns=inv_ticker_dict)

        # 결측치 처리
        df_close = df_close.ffill().bfill()

        # 누적 수익률 계산 (시작 시점 대비 변화율)
        df_return = (df_close / df_close.iloc[0] - 1) * 100

        # --- 메인 화면 레이아웃 ---
        
        # 1. 최신 수익률 요약 메트릭
        st.subheader("📊 종목별 누적 수익률 요약")
        cols = st.columns(len(selected_names))
        
        for i, name in enumerate(selected_names):
            if name in df_return.columns:
                current_return = df_return[name].iloc[-1]
                current_price = df_close[name].iloc[-1]
                
                # 토스 감성의 컬러 적용 (+는 빨강/주황, -는 파랑)
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
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.info("티커 심볼이 올바른지, 혹은 선택한 기간에 데이터가 존재하는지 확인해 주세요.")
else:
    st.info("왼쪽 사이드바에서 비교할 종목을 선택해 주세요!")
