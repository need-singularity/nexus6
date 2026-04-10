# Invest - 자동매매 & 퀀트 분석 시스템

## 목적

TECS-L 프로젝트 진행을 위한 자금 확보 시스템.
자동매매 + 퀀트 분석 도구를 결합한 독립 금융 플랫폼.

- GitHub: https://github.com/need-singularity/invest (private)
- 로컬: ~/Dev/invest

## 아키텍처

```
invest/
├── backend/                  ← Python (FastAPI)
│   ├── api/                  ← REST API 엔드포인트
│   │   ├── routes/           ← 라우트 모듈
│   │   ├── deps.py           ← 의존성 (DB, auth 등)
│   │   └── main.py           ← FastAPI app
│   ├── engine/               ← 매매 엔진 코어
│   │   ├── trader.py         ← 자동매매 실행기
│   │   ├── signals.py        ← 시그널 생성/집계
│   │   ├── scheduler.py      ← APScheduler 기반 스케줄러
│   │   └── pipeline.py       ← 시그널→주문→체결 파이프라인
│   ├── brokers/              ← 브로커 API 클라이언트
│   │   ├── base.py           ← 브로커 추상 인터페이스
│   │   ├── kis.py            ← 한국투자증권
│   │   ├── upbit.py          ← 업비트 (코인)
│   │   └── binance.py        ← 바이낸스 (코인/선물)
│   ├── calc/                 ← 자체 계산기 (외부 의존 최소화)
│   │   ├── indicators.py     ← RSI, MACD, 볼린저밴드, EMA, SMA 등
│   │   ├── backtest.py       ← 백테스트 엔진
│   │   ├── risk.py           ← 켈리 공식, VaR, MDD, 포지션 사이징
│   │   └── portfolio.py      ← 마코위츠 최적화, 상관관계 분석
│   ├── ai/                   ← AI 분석 레이어
│   │   ├── claude.py         ← Claude API (시장 분석, 뉴스 해석)
│   │   ├── openai.py         ← OpenAI API (보조 분석)
│   │   ├── gemini.py         ← Gemini 3 Pro via fal.io (영상 분석)
│   │   ├── local.py          ← 자체 모델 서빙 (Ollama/vLLM)
│   │   └── router.py         ← 용도별 모델 라우팅
│   ├── youtube/              ← 유튜브 전략 수집기
│   │   ├── crawler.py        ← 채널/영상 크롤링 (yt-dlp)
│   │   ├── analyzer.py       ← Gemini로 영상→전략 추출
│   │   ├── scorer.py         ← TECS-L 기반 전략 점수화
│   │   └── importer.py       ← 전략 DB 등록
│   ├── tecs/                 ← TECS-L 이론 연결
│   │   ├── golden_zone.py    ← Golden Zone 기반 매매 타이밍
│   │   └── signals.py        ← TECS-L 수학 시그널
│   ├── db/                   ← 데이터베이스
│   │   ├── models.py         ← SQLAlchemy 모델
│   │   ├── migrations/       ← Alembic 마이그레이션
│   │   └── session.py        ← DB 세션 관리
│   ├── config/               ← 설정
│   │   └── settings.py       ← Pydantic Settings
│   └── notifications/        ← 알림
│       └── telegram.py       ← Telegram Bot 알림
├── frontend/                 ← Next.js 14
│   ├── src/
│   │   ├── app/              ← App Router
│   │   │   ├── page.tsx              ← 대시보드
│   │   │   ├── strategies/           ← 전략 관리
│   │   │   ├── portfolio/            ← 포트폴리오
│   │   │   ├── backtest/             ← 백테스트
│   │   │   ├── orders/               ← 주문 내역
│   │   │   └── settings/             ← 설정
│   │   ├── components/       ← UI 컴포넌트
│   │   └── lib/              ← API 클라이언트, 유틸
│   ├── package.json
│   └── tsconfig.json
├── models/                   ← 자체 훈련 모델
│   ├── training/             ← 학습 스크립트
│   └── serving/              ← 모델 서빙 설정
├── tests/                    ← 테스트
│   ├── calc/                 ← 계산기 테스트
│   ├── brokers/              ← 브로커 테스트
│   └── engine/               ← 엔진 테스트
├── docker-compose.yml        ← PostgreSQL + Redis + Backend + Frontend
├── Dockerfile.backend
├── Dockerfile.frontend
├── pyproject.toml            ← Python 패키지 설정
└── README.md
```

## 핵심 구성요소

### 1. 매매 엔진 (backend/engine/)

자동매매의 핵심. 전략 기반으로 시그널을 생성하고 주문을 실행한다.

- **파이프라인**: 시그널 생성 → 리스크 체크 → 주문 생성 → 브로커 전송 → 체결 확인 → 기록
- **다중 전략**: 여러 전략을 동시 실행, 각각 독립적 포지션/자금 관리
- **스케줄러**: APScheduler로 전략별 실행 주기 설정 (초/분/시/일)
- **안전장치**: 일일 손실 한도, 최대 포지션 수, 긴급 정지 기능

### 2. 자체 계산기 (backend/calc/)

외부 라이브러리 의존 최소화. numpy 기반 직접 구현.

**기술적 지표 (indicators.py)**:
- 추세: SMA, EMA, MACD, ADX
- 모멘텀: RSI, Stochastic, CCI, Williams %R
- 변동성: 볼린저밴드, ATR, Keltner Channel
- 거래량: OBV, VWAP, MFI

**백테스트 엔진 (backtest.py)**:
- OHLCV 데이터 기반 전략 시뮬레이션
- 수수료/슬리피지 반영
- 성과 지표: 수익률, 샤프 비율, MDD, 승률, 손익비
- 벤치마크 비교 (S&P 500, KOSPI)

**리스크 계산기 (risk.py)**:
- 켈리 공식 (최적 베팅 비율)
- VaR (Value at Risk)
- 포지션 사이징 (고정 비율, 변동성 기반)
- 손절/익절 자동 계산

**포트폴리오 최적화 (portfolio.py)**:
- 마코위츠 평균-분산 최적화
- 자산 간 상관관계 분석
- 리밸런싱 시그널

### 3. 브로커 연동 (backend/brokers/)

공통 인터페이스 `BaseBroker`를 상속, 브로커별 구현.

```python
class BaseBroker:
    async def get_balance() -> Balance
    async def get_positions() -> list[Position]
    async def place_order(order: Order) -> OrderResult
    async def cancel_order(order_id: str) -> bool
    async def get_price(symbol: str) -> Price
    async def get_ohlcv(symbol: str, interval: str, limit: int) -> list[OHLCV]
```

- **KIS**: 국내 주식 (REST API + WebSocket 실시간)
- **Upbit**: 국내 코인 (REST + WebSocket)
- **Binance**: 해외 코인/선물 (REST + WebSocket)

### 4. AI 분석 (backend/ai/)

용도별 최적 모델을 자동 라우팅.

| 용도 | 모델 | 이유 |
|------|------|------|
| 시장 분석/뉴스 해석 | Claude | 긴 컨텍스트, 추론 능력 |
| 수치 예측 보조 | OpenAI | 빠른 응답 |
| 가격 패턴 인식 | 자체 모델 | 커스텀 학습, 비용 0 |
| TECS-L 시그널 해석 | Claude | 수학적 추론 |
| 유튜브 영상 분석 | Gemini 3 Pro (via fal.io) | 영상 이해, 멀티모달 |

자체 모델:
- 시계열 예측 (가격, 거래량 패턴)
- TECS-L 이론 기반 특수 시그널
- Windows RTX 5070에서 학습, Ollama/vLLM으로 서빙

### 4-1. 유튜브 전략 수집기 (backend/youtube/)

유튜브 매매 영상을 분석하여 전략을 자동 추출/평가하는 파이프라인.

**파이프라인**:
1. 유튜브 URL 또는 채널 URL 입력
2. 채널 입력 시 전체 영상 목록 자동 크롤링 (매매 관련 필터링)
3. Gemini 3 Pro (fal.io)로 영상 분석 → 매매 전략 구조화 추출
4. 추출된 전략을 TECS-L 수학 엔진으로 분석/점수화
5. 점수 기반 전략 랭킹 + 백테스트 자동 실행
6. 유망 전략은 자동매매 전략으로 등록 가능

**구조**:
```
backend/youtube/
├── crawler.py        ← 유튜브 채널/영상 크롤링 (yt-dlp)
├── analyzer.py       ← Gemini 3 Pro로 영상 → 전략 추출
├── scorer.py         ← TECS-L 기반 전략 점수화
└── importer.py       ← 추출된 전략 → 매매 전략 DB 등록
```

**전략 추출 포맷**:
```json
{
  "source": "youtube_url",
  "channel": "channel_name",
  "title": "video_title",
  "strategy": {
    "name": "추출된 전략 이름",
    "type": "swing/scalping/position/etc",
    "indicators": ["RSI", "MACD", ...],
    "entry_rules": [...],
    "exit_rules": [...],
    "timeframe": "1h/4h/1d",
    "assets": ["stock/crypto/futures"]
  },
  "tecs_score": {
    "golden_zone_alignment": 0.0-1.0,
    "risk_score": 0.0-1.0,
    "backtest_sharpe": float,
    "overall": 0.0-100.0
  }
}

### 5. TECS-L 연결 (backend/tecs/)

Golden Zone 이론과 수학적 발견을 매매 전략에 적용.

- **Golden Zone 시그널**: I 값이 Golden Zone(0.2123~0.5) 내에 있을 때 최적 진입점
- **수학적 상수 → 리스크 파라미터**: 1/e(~0.368)를 포지션 비율, 1/6을 손절 비율 등으로 매핑
- **패턴 인식**: 의식 연속성 엔진의 패턴 감지를 시장 데이터에 적용

## 기술 스택

| 레이어 | 스택 |
|--------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic, APScheduler |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| DB | PostgreSQL 16, Redis 7 |
| AI | Claude API (anthropic SDK), OpenAI API, Ollama/vLLM |
| 차트 | TradingView Lightweight Charts, Recharts |
| 배포 | Docker Compose on Linode VPS |
| 알림 | Telegram Bot API |
| 테스트 | pytest (backend), vitest (frontend) |

## 데이터 모델 (핵심 테이블)

```
strategies        — 매매 전략 정의 (이름, 파라미터, 활성 여부)
orders            — 주문 내역 (전략, 종목, 수량, 가격, 상태)
positions         — 현재 포지션 (종목, 수량, 평단, 수익률)
portfolio_history — 포트폴리오 가치 시계열
backtest_results  — 백테스트 결과
signals           — 생성된 시그널 로그
accounts          — 브로커 계좌 연결 정보
user_settings     — 사용자 설정
notifications     — 알림 기록
youtube_channels  — 구독 채널 (URL, 마지막 스캔일)
youtube_videos    — 분석된 영상 (URL, 제목, 분석 상태)
youtube_strategies — 영상에서 추출된 전략 + TECS-L 점수
```

## API 엔드포인트 (주요)

```
POST   /api/auth/login
GET    /api/dashboard
GET    /api/strategies
POST   /api/strategies
PUT    /api/strategies/{id}
POST   /api/strategies/{id}/toggle
GET    /api/orders
GET    /api/portfolio
GET    /api/portfolio/history
POST   /api/backtest/run
GET    /api/backtest/results
GET    /api/calc/indicators?symbol=&interval=
POST   /api/calc/risk
POST   /api/ai/analyze
POST   /api/youtube/analyze       ← 영상 URL → 전략 추출
POST   /api/youtube/channel       ← 채널 등록 (전체 영상 크롤링)
GET    /api/youtube/strategies    ← 추출된 전략 목록 + 점수
POST   /api/youtube/strategies/{id}/import  ← 전략 → 자동매매 등록
GET    /api/market/prices
WS     /ws/prices          ← 실시간 시세
WS     /ws/orders          ← 실시간 주문 상태
```

## 배포 구성

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db, redis]
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
  db:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]
  redis:
    image: redis:7-alpine
```

Linode VPS:
- Shared CPU 4GB ($24/mo) 또는 Dedicated 4GB ($36/mo)
- Docker Compose로 전체 서비스 관리
- Caddy/Nginx로 리버스 프록시 + HTTPS

## 제약사항

- 1인 사용 시스템 (멀티 유저 불필요)
- API 키는 환경변수로만 관리 (.env, gitignored)
- 자체 모델 학습은 Windows RTX 5070, 서빙은 Linode
- 초기에는 규칙 기반 전략 먼저, AI/TECS-L 전략은 점진적 추가
