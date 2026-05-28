import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 페이지 기본 설정
st.set_page_config(
    page_title="한/미 주요 주식 수익률 비교 분석기",
    page_icon="📈",
    layout="wide"
)

st.title("📈 한/미 주요 주식 수익률 및 차트 비교")
st.markdown("한국(KRX)과 미국(US) 주요 주식의 수익률을 동일 선상에서 쉽게 비교해 보세요.")

# ------------------------------------
# 사이드바: 자산 선택 및 기간 설정
# ------------------------------------
st.sidebar.header("⚙️ 설정 및 자산 선택")

# 기본 제공 자산 리스트 (딕셔너리 형태)
asset_dict = {
    "미국 주식": {
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT",
        "NVIDIA (NVDA)": "NVDA",
        "Tesla (TSLA)": "TSLA",
        "S&P 500 ETF (SPY)": "SPY",
        "Nasdaq 100 ETF (QQQ)": "QQQ"
    },
    "한국 주식": {
        "삼성전자 (005930)": "005930.KS",
        "SK하이닉스 (000660)": "000660.KS",
        "현대차 (005380)": "005380.KS",
        "네이버 (035420)": "035420.KS",
        "KOSPI 200 ETF (069500)": "069500.KS",
        "KOSDAQ 150 ETF (233740)": "233740.KS"
    }
}

# 사용자 다중 선택
us_selected = st.sidebar.multiselect(
    "미국 자산 선택", 
    options=list(asset_dict["미국 주식"].keys()),
    default=["Apple (AAPL)", "S&P 500 ETF (SPY)"]
)

kr_selected = st.sidebar.multiselect(
    "한국 자산 선택", 
    options=list(asset_dict["한국 주식"].keys()),
    default=["삼성전자 (005930)", "KOSPI 200 ETF (069500)"]
)

# 커스텀 티커 입력 기능
st.sidebar.subheader("➕ 커스텀 티커 추가")
custom_ticker = st.sidebar.text_input("직접 입력 (예: TSMC는 TSM, 카카오는 035720.KS)").strip()

# 기간 설정
st.sidebar.subheader("📅 분석 기간 설정")
duration = st.sidebar.selectbox(
    "기간 선택",
    options=["1개월", "3개월", "6개월", "1년", "3년", "5년", "직접 지정"]
)

end_date = datetime.today()
if duration == "1개월":
    start_date = end_date - timedelta(days=30)
elif duration == "3개월":
    start_date = end_date - timedelta(days=90)
elif duration == "6개월":
    start_date = end_date - timedelta(days=180)
elif duration == "1년":
    start_date = end_date - timedelta(days=365)
elif duration == "3년":
    start_date = end_date - timedelta(days=365 * 3)
elif duration == "5년":
    start_date = end_date - timedelta(days=365 * 5)
else:
    start_date = st.sidebar.date_input("시작일", end_date - timedelta(days=365))
    end_date = st.sidebar.date_input("종료일", end_date)

# ------------------------------------
# 데이터 수집 및 가공
# ------------------------------------
# 선택된 티커 리스트 취합
selected_tickers = {}
for name in us_selected:
    selected_tickers[name] = asset_dict["미국 주식"][name]
for name in kr_selected:
    selected_tickers[name] = asset_dict["한국 주식"][name]

if custom_ticker:
    selected_tickers[f"커스텀 ({custom_ticker})"] = custom_ticker

if not selected_tickers:
    st.warning("⚠️ 분석할 주식을 최소 하나 이상 선택해 주세요.")
else:
    tickers_list = list(selected_tickers.values())
    
    with st.spinner("금융 데이터를 가져오는 중입니다..."):
        try:
            # yfinance 데이터 다운로드
            data = yf.download(tickers_list, start=start_date, end=end_date, progress=False)
            
            # 1단계 에러 방지: 데이터가 완전히 비어있는 경우 처리
            if data.empty or 'Close' not in data:
                st.error("⚠️ 선택한 기간 내에 가져온 주가 데이터가 없습니다. 분석 기간을 더 길게 설정하거나 다른 자산을 선택해 주세요.")
                st.stop()
                
            # 주가가 단일 티커일 때와 다중 티커일 때의 DataFrame 구조 대응
            if len(tickers_list) == 1:
                close_prices = pd.DataFrame(data['Close'])
                close_prices.columns = [list(selected_tickers.keys())[0]]
            else:
                close_prices = data['Close']
                # 컬럼명을 티커 기호 대신 가독성 좋은 이름으로 변경
                inv_map = {v: k for k, v in selected_tickers.items()}
                close_prices = close_prices.rename(columns=inv_map)
            
            # 2단계 에러 방지: 모든 행이 NaN인 경우 제거 및 데이터 유무 재체크
            close_prices = close_prices.dropna(how='all')
            
            if close_prices.empty:
                st.error("⚠️ 유효한 종가(Close) 데이터가 존재하지 않습니다. 기간을 조정해 보세요.")
                st.stop()
                
            # 3단계 에러 방지: 한/미 휴장일 차이 메우기 (순방향 후 역방향 결측치 채우기)
            close_prices = close_prices.ffill().bfill()

            # 누적 수익률 계산 (기준일 가격을 100으로 잡고 변화율 계산)
            normalized_return = (close_prices / close_prices.iloc[0] - 1) * 100

            # ------------------------------------
            # 대시보드 화면 구성
            # ------------------------------------
            # 주요 지표 (가장 최근 거래일 기준 수익률 카드)
            st.subheader("📊 최근 누적 수익률 현황")
            metrics_cols = st.columns(len(normalized_return.columns))
            
            for i, col_name in enumerate(normalized_return.columns):
                latest_return = normalized_return[col_name].iloc[-1]
                latest_price = close_prices[col_name].iloc[-1]
                
                with metrics_cols[i]:
                    st.metric(
                        label=col_name,
                        value=f"{latest_price:,.2f}",
                        delta=f"{latest_return:+.2f}% (누적)"
                    )
            
            st.markdown("---")

            # 대화형 라인 차트 그리기
            st.subheader("📈 누적 수익률 비교 차트 (%)")
            st.caption("시작일의 주가를 0%로 맞추어 통화와 관계없이 순수 수익률 추이를 비교합니다.")
            
            fig = px.line(
                normalized_return,
                x=normalized_return.index,
                y=normalized_return.columns,
                labels={"value": "누적 수익률 (%)", "Date": "날짜", "variable": "자산명"},
                template="plotly_dark"
            )
            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # 데이터 테이블 및 통계치 정보
            st.subheader("📋 상세 데이터 및 변동성")
            
            tab1, tab2 = st.tabs(["📊 기간 통계 정보", "📄 원본 종가 데이터"])
            
            with tab1:
                summary_df = pd.DataFrame({
                    "시작 가격": close_prices.iloc[0],
                    "최종 가격": close_prices.iloc[-1],
                    "기간 최고가": close_prices.max(),
                    "기간 최저가": close_prices.min(),
                    "최종 누적 수익률 (%)": normalized_return.iloc[-1]
                })
                st.dataframe(summary_df.style.format("{:,.2f}"), use_container_width=True)
                
            with tab2:
                st.dataframe(close_prices, use_container_width=True)
                
        except Exception as e:
            st.error(f"데이터를 처리하는 중 예기치 못한 오류가 발생했습니다: {e}")
            st.info("선택한 자산이나 기간 설정을 확인해 주세요.")
