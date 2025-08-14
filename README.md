# 🎮 Bullet Dodger (총알피하기)
Streamlit 위에서 돌아가는 캔버스 기반 미니게임입니다. 키보드/모바일 조이스틱을 지원하고, 난이도는 사이드바에서 조절할 수 있습니다.

## 데모(배포)
- **Streamlit Cloud**에 이 저장소를 연결하면 자동으로 빌드되어 공개 URL이 생성됩니다.

## 로컬 실행
```bash
# 1) 클론
git clone https://github.com/<YOUR-ID>/bullet-dodger.git
cd bullet-dodger

# 2) 가상환경(선택)
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# 3) 의존성 설치
pip install -r requirements.txt

# 4) 실행
streamlit run app.py
