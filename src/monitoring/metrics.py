from prometheus_client import Counter, Histogram, Gauge

# トランザクション総数 (ラベル: type, status)
TRANSACTION_TOTAL = Counter(
    'transaction_total',
    'Total number of transactions',
    ['type', 'status']
)

# トランザクション金額のヒストグラム (バケット: 1k, 10k, 100k, 1M)
TRANSACTION_AMOUNT_HISTOGRAM = Histogram(
    'transaction_amount_histogram',
    'Histogram of transaction amounts',
    buckets=[1000.0, 10000.0, 100000.0, 1000000.0]
)

# アクティブセッション数
ACTIVE_SESSIONS = Gauge(
    'active_sessions',
    'Number of active sessions'
)

# 不正検知アラート総数 (ラベル: severity)
FRAUD_ALERTS_TOTAL = Counter(
    'fraud_alerts_total',
    'Total number of fraud alerts',
    ['severity']
)

# APIリクエスト所要時間
API_REQUEST_DURATION_SECONDS = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds'
)
