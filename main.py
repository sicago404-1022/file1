import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime
import requests
from io import BytesIO

# --- 페이지 설정 ---
st.set_page_config(page_title="YouTube 비디오 분석기", layout="wide")
st.title("📊 YouTube 영상 정보 및 댓글 분석기")

# --- 사이드바: API 키 입력 ---
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("YouTube API Key를 입력하세요", type="password")
    video_url = st.text_input("유튜브 영상 URL을 입력하세요")

def get_video_id(url):
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "be/" in url:
        return url.split("be/")[1].split("?")[0]
    return None

if api_key and video_url:
    video_id = get_video_id(video_url)
    
    if video_id:
        youtube = build("youtube", "v3", developerKey=api_key)

        # 1. 영상 정보 가져오기
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()

        if response["items"]:
            video_data = response["items"][0]
            snippet = video_data["snippet"]
            stats = video_data["statistics"]

            # 기본 정보 추출
            title = snippet["title"]
            published_at = datetime.strptime(snippet["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
            view_count = int(stats.get("viewCount", 0))
            comment_count = int(stats.get("commentCount", 0))
            like_count = int(stats.get("likeCount", 0))
            thumbnail_url = snippet["thumbnails"]["high"]["url"]

            # --- 화면 구성 ---
            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(thumbnail_url, caption="영상 썸네일")
                # 썸네일 다운로드 버튼
                response_img = requests.get(thumbnail_url)
                st.download_button(
                    label="🖼️ 썸네일 다운로드",
                    data=BytesIO(response_img.content),
                    file_name=f"{video_id}_thumbnail.jpg",
                    mime="image/jpeg"
                )

            with col2:
                st.subheader(title)
                st.write(f"📅 **게시일:** {published_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 주요 지표 시각화
                m1, m2, m3 = st.columns(3)
                m1.metric("조회 수", f"{view_count:,}회")
                m2.metric("댓글 수", f"{comment_count:,}개")
                m3.metric("좋아요 수", f"{like_count:,}개")

            st.divider()

            # 데이터 요약 표
            st.markdown("### 📝 영상 요약 정보")
            summary_df = pd.DataFrame({
                "항목": ["영상 제목", "게시 날짜", "조회 수", "댓글 수", "좋아요 수"],
                "데이터": [title, published_at.date(), f"{view_count:,}", f"{comment_count:,}", f"{like_count:,}"]
            })
            st.table(summary_df)

        else:
            st.error("영상을 찾을 수 없습니다. URL을 확인해 주세요.")
    else:
        st.warning("올바른 유튜브 URL을 입력해 주세요.")
else:
    st.info("사이드바에 API 키와 영상 URL을 입력하면 분석이 시작됩니다.")
