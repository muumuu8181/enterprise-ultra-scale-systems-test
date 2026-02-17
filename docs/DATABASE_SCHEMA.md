```sql
-- ユーザーマスタ
CREATE TABLE users (
  user_id BIGSERIAL PRIMARY KEY,
  external_id VARCHAR(128) UNIQUE NOT NULL,  -- SNS/Platform ID
  username VARCHAR(50) NOT NULL,
  email VARCHAR(255) UNIQUE,
  platform VARCHAR(20) NOT NULL CHECK (platform IN ('ios','android','steam','web')),
  level INT NOT NULL DEFAULT 1,
  exp BIGINT NOT NULL DEFAULT 0,
  premium_currency INT NOT NULL DEFAULT 0,  -- 有償石
  free_currency INT NOT NULL DEFAULT 0,     -- 無償石
  stamina INT NOT NULL DEFAULT 100,
  max_stamina INT NOT NULL DEFAULT 100,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_banned BOOLEAN NOT NULL DEFAULT FALSE,
  ban_reason TEXT,
  country_code CHAR(2),
  language_code VARCHAR(10) DEFAULT 'ja'
);
CREATE INDEX idx_users_external ON users(external_id);
CREATE INDEX idx_users_platform ON users(platform, created_at DESC);

-- ガチャバナー
CREATE TABLE gacha_banners (
  banner_id BIGSERIAL PRIMARY KEY,
  banner_name VARCHAR(200) NOT NULL,
  banner_type VARCHAR(30) NOT NULL CHECK (banner_type IN ('normal','pickup','limited','step_up','guaranteed','fes')),
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  cost_type VARCHAR(20) NOT NULL CHECK (cost_type IN ('premium','free','ticket')),
  single_cost INT NOT NULL DEFAULT 300,
  multi_cost INT NOT NULL DEFAULT 3000,  -- 通常10連分
  multi_count INT NOT NULL DEFAULT 10,
  pity_count INT NOT NULL DEFAULT 100,   -- 天井
  soft_pity_start INT NOT NULL DEFAULT 75,  -- ソフト天井開始
  guaranteed_rarity VARCHAR(10) DEFAULT 'SSR',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  banner_config JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_banners_active ON gacha_banners(is_active, start_at, end_at);

-- ガチャ排出設定
CREATE TABLE gacha_rates (
  rate_id BIGSERIAL PRIMARY KEY,
  banner_id BIGINT NOT NULL REFERENCES gacha_banners(banner_id),
  item_id BIGINT NOT NULL,
  item_type VARCHAR(20) NOT NULL,
  rarity VARCHAR(10) NOT NULL CHECK (rarity IN ('N','R','SR','SSR','UR')),
  base_rate NUMERIC(8,6) NOT NULL,   -- 基本排出率 (0.000001〜1.0)
  is_pickup BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE (banner_id, item_id)
);

-- ガチャ実行ログ
CREATE TABLE gacha_logs (
  log_id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id),
  banner_id BIGINT NOT NULL REFERENCES gacha_banners(banner_id),
  pulled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  item_id BIGINT NOT NULL,
  rarity VARCHAR(10) NOT NULL,
  is_pickup BOOLEAN NOT NULL DEFAULT FALSE,
  is_pity BOOLEAN NOT NULL DEFAULT FALSE,
  cost_type VARCHAR(20) NOT NULL,
  cost_amount INT NOT NULL,
  pity_count_at_pull INT NOT NULL DEFAULT 0,
  session_id UUID
) PARTITION BY RANGE (pulled_at);
CREATE TABLE gacha_logs_2026_q1 PARTITION OF gacha_logs FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE gacha_logs_2026_q2 PARTITION OF gacha_logs FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE INDEX idx_gacha_logs_user ON gacha_logs(user_id, pulled_at DESC);
CREATE INDEX idx_gacha_logs_banner ON gacha_logs(banner_id, pulled_at DESC);

-- ユーザー天井カウント
CREATE TABLE user_pity_counters (
  user_id BIGINT NOT NULL REFERENCES users(user_id),
  banner_id BIGINT NOT NULL REFERENCES gacha_banners(banner_id),
  current_pity INT NOT NULL DEFAULT 0,
  total_pulls INT NOT NULL DEFAULT 0,
  last_ssr_at INT,  -- SSR引いた時のカウント
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, banner_id)
);

-- ライブイベント
CREATE TABLE live_events (
  event_id BIGSERIAL PRIMARY KEY,
  event_name VARCHAR(200) NOT NULL,
  event_type VARCHAR(30) NOT NULL CHECK (event_type IN ('tower','raid','ranking','collection','story','collaboration')),
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  exchange_end_at TIMESTAMPTZ,  -- 交換期限
  status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','active','ended','maintenance')),
  event_config JSONB NOT NULL DEFAULT '{}',
  reward_table JSONB NOT NULL DEFAULT '[]'
);
CREATE INDEX idx_events_active ON live_events(status, start_at, end_at);

-- イベントポイント
CREATE TABLE event_points (
  user_id BIGINT NOT NULL REFERENCES users(user_id),
  event_id BIGINT NOT NULL REFERENCES live_events(event_id),
  points BIGINT NOT NULL DEFAULT 0,
  rank INT,
  rank_updated_at TIMESTAMPTZ,
  PRIMARY KEY (user_id, event_id)
);
CREATE INDEX idx_event_points_ranking ON event_points(event_id, points DESC);

-- 購入レコード
CREATE TABLE purchases (
  purchase_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL REFERENCES users(user_id),
  store_transaction_id VARCHAR(255) UNIQUE NOT NULL,
  platform VARCHAR(20) NOT NULL,
  product_id VARCHAR(100) NOT NULL,
  premium_currency_granted INT NOT NULL DEFAULT 0,
  bonus_currency_granted INT NOT NULL DEFAULT 0,
  amount_jpy NUMERIC(10,2) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','completed','refunded','disputed')),
  receipt_data TEXT,
  verified_at TIMESTAMPTZ,
  purchased_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_purchases_user ON purchases(user_id, purchased_at DESC);
CREATE INDEX idx_purchases_transaction ON purchases(store_transaction_id);
```
