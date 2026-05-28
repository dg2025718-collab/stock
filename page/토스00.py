import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.graph_objects as go

# --- 페이지 설정 (기본 테마를 세련되게 제어) ---
st.set_page_config(
    page_title="Toss Style Stock Insights",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 커스텀 스타일링 (토스 특유의 폰트, 여백, 카드 디자인 반영) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    html, body, [data-testid="stMarkdownContainer"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #f9fafb;
        border-right: 1px solid #e5e8eb;
    }
    
    /* 토스 스타일 카드 */
    .toss-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid #f2f4f6;
        margin-bottom: 15px;
        transition: transform 0.2s ease;
    }
    .toss-card:hover {
        transform: translateY(-2px);
    }
    .toss-card-title {
        font-size: 14px;
        color: #4e5968;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .toss-card-price {
        font-size: 22px;
        font-weight: 700;
        color: #191f28;
    }
    .toss-card-delta {
        font-size: 14px;
        font-weight: 600;
        margin-top: 4px;
    }
    .delta-plus { color: #f04452; }
    .delta-minus { color: #3182f6; }
    </style>
""", unsafe_allow_html=True)

# --- 상단 타이틀 ---
st.markdown("<h1 style='color: #191f28; font-weight: 700; margin-bottom: 5px;'>📈 토스증권 스타일 투자 분석 가이드</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #4e5968; font-size: 16px; margin-bottom: 30px;'>선택한 종목들의 실시간 시세와 기간별 누적 수익률을 비교합니다.</p>", unsafe_allow_html=True)

# --- 사이드바: 설정 영역 ---
st.sidebar.markdown("<h2 style='color: #191f28; font-size: 20px; font-weight: 700; margin-bottom: 20px;'>🔍 조건 변경</h2>", unsafe_allow_html=True)

# 기간 선택
today = datetime.date.today()
start_date = st.sidebar.date_input("조회 시작일", today - datetime.timedelta(days=365))
end_date = st.sidebar.date_input("조회 종료일", today)

# 기본 제공 인기 종목 리스트
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

st.sidebar.markdown("<br>", unsafe_allow_html=True)
selected_names = st.sidebar.multiselect(
    "관심 종목 선택",
    options=list(ticker_dict.keys()),
    default=["삼성전자", "Apple (AAPL)", "NVIDIA (NVDA)"]
)

# 직접 입력 기능
custom_ticker = st.sidebar.text_input("종목 코드 직접 입력 (예: AMZN, 000270.KS)")
if custom_ticker:
    ticker_dict[custom_ticker] = custom_ticker
    if custom_ticker not in selected_names:
        selected_names.append(custom_ticker)

# --- 데이터 로드 함수 ---
if selected_names:
    selected_tickers = [ticker_dict[name] for name in selected_names]
    
    @st.cache_data(ttl=3600)
    def load_stock_data(tickers, start, end):
        raw_data = yf.download(tickers, start=start, end=end, group_by='ticker')
        df_close = pd.DataFrame()
        
        if len(tickers) == 1:
            ticker = tickers[0]
            df_close[ticker] = raw_data['Adj Close'] if 'Adj Close' in raw_data.columns else raw_data['Close']
        else:
            for ticker in tickers:
                if ticker in raw_data.columns.levels[0]:
                    df_close[ticker] = raw_data[ticker]['Adj Close'] if 'Adj Close' in raw_data[ticker].columns else raw_data[ticker]['Close']
        return df_close

    try:
        df_close = load_stock_data(selected_tickers, start_date, end_date)
        
        if df_close.empty:
            st.error("선택한 기간에 데이터가 없습니다. 날짜를 다시 확인해 주세요.")
        else:
            # 딕셔너리 역매핑 (티커 -> 한글이름)
            inv_ticker_dict = {v: k for k, v in ticker_dict.items()}
            df_close = df_close.rename(columns=inv_ticker_dict)
            df_close = df_close.ffill().bfill()

            # 누적 수익률 계산
            df_return = (df_close / df_close.iloc[0] - 1) * 100

            # --- 1. 멋진 토스 스타일 대시보드 카드 배치 ---
            st.markdown("<h3 style='color: #191f28; font-size: 18px; font-weight: 600; margin-bottom: 15px;'>내 관심 종목 현황</h3>", unsafe_allow_html=True)
            
            # 카드가 한 줄에 최대 4개씩 배열되도록 동적 생성
            card_cols = st.columns(4)
            for i, name in enumerate(selected_names):
                if name in df_return.columns:
                    col_idx = i % 4
                    current_price = df_close[name].iloc[-1]
                    current_return = df_return[name].iloc[-1]
                    
                    # 화살표 및 플러스/마이너스 클래스 구분
                    if current_return >= 0:
                        status_class = "delta-plus"
                        arrow = "▲"
                    else:
                        status_class = "delta-minus"
                        arrow = "▼"
                    
                    price_format = f"{current_price:,.0f}원" if "KS" in ticker_dict.get(name, "") or "KQ" in ticker_dict.get(name, "") else f"${current_price:,.2f}"
                    
                    # HTML 카드로 렌더링
                    card_cols[col_idx].markdown(f"""
                        <div class="toss-card">
                            <div class="toss-card-title">{name}</div>
                            <div class="toss-card-price">{price_format}</div>
                            <div class="toss-card-delta {status_class}">{arrow} {current_return:.2f}%</div>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- 2. Plotly를 이용한 프리미엄 인터랙티브 차트 ---
            st.markdown("<h3 style='color: #191f28; font-size: 18px; font-weight: 600; margin-bottom: 5px;'>수익률 비교 추이</h3>", unsafe_allow_html=True)
            
            fig = go.Figure()
            for name in selected_names:
                if name in df_return.columns:
                    fig.add_trace(go.Scatter(
                        x=df_return.index,
                        y=df_return[name],
                        mode='l',
                        name=name,
                        line=dict(width=2.5),
                        hovertemplate=f'<b>{name}</b><br>수익률: %{{y:.2f}}%<br>날짜: %{{x|%Y-%m-%d}}<extra></extra>'
                    ))
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=20, b=0),
                height=450,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(
                    showgrid=True, gridcolor='#f2f4f6',
                    linecolor='#e5e8eb'
                ),
                yaxis=dict(
                    title="누적 수익률 (%)",
                    showgrid=True, gridcolor='#f2f4f6',
                    linecolor='#e5e8eb',
                    ticksuffix="%"
                )
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- 3. 데이터 하단 서브 테이블 ---
            with st.expander("📊 상세 종가 데이터 테이블 확인하기"):
                st.dataframe(df_close.style.format(formatter="{:,.2f}"))

    except Exception as e:
        st.error(f"데이터 로드 및 시각화 중 문제가 발생했습니다: {e}")
else:
    st.info("왼쪽 사이드바에서 분석하고 싶은 주식 종목을 골라보세요!")
