# Step 2: DB詳細設計・DDL一覧

本ドキュメントは、システムで使用する PostgreSQL 15 の全テーブル定義（DDL）を記載する。
共通仕様:
- 全テーブルの主キーは UUID (v4) を使用する。
- 日時は全て `TIMESTAMP WITH TIME ZONE` (UTC) で保存する。
- 拡張可能なデータは `JSONB` 型を使用する。

## 共通設定
```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 更新日時自動更新用関数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
```

## 1. プレイヤー管理 (Player Domain)

```sql
-- 1. プレイヤー基本
CREATE TABLE players (
    player_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active', -- active, banned, deleted
    vip_level INT DEFAULT 0,
    total_spent DECIMAL(15, 4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 認証情報
CREATE TABLE player_auth (
    auth_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL, -- apple, google, twitter, email
    provider_uid VARCHAR(255) NOT NULL,
    access_token_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_uid)
);

-- 3. プレイヤーステータス (頻繁更新)
CREATE TABLE player_stats (
    player_id UUID PRIMARY KEY REFERENCES players(player_id) ON DELETE CASCADE,
    level INT DEFAULT 1,
    exp BIGINT DEFAULT 0,
    max_exp BIGINT DEFAULT 100,
    stamina INT DEFAULT 100,
    max_stamina INT DEFAULT 100,
    gems INT DEFAULT 0, -- 無償石 + 有償石
    paid_gems INT DEFAULT 0, -- 有償石内訳
    coins BIGINT DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. プロフィール
CREATE TABLE player_profiles (
    player_id UUID PRIMARY KEY REFERENCES players(player_id) ON DELETE CASCADE,
    display_name VARCHAR(50),
    bio TEXT,
    avatar_id VARCHAR(50),
    title_id INT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. 端末情報
CREATE TABLE player_device_info (
    device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    os_type VARCHAR(20), -- ios, android
    os_version VARCHAR(20),
    device_model VARCHAR(100),
    app_version VARCHAR(20),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. ログイン履歴
CREATE TABLE player_login_history (
    login_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    ip_address INET,
    user_agent TEXT,
    login_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. BAN履歴
CREATE TABLE player_banned_history (
    ban_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id),
    reason TEXT,
    banned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    admin_id UUID
);
```

## 2. ガチャシステム (Gacha Domain)

```sql
-- 8. ガチャマスタ
CREATE TABLE gacha_masters (
    gacha_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    gacha_type VARCHAR(20) NOT NULL, -- normal, event, limited, step
    start_at TIMESTAMP WITH TIME ZONE,
    end_at TIMESTAMP WITH TIME ZONE,
    cost_type VARCHAR(20) DEFAULT 'gem', -- gem, ticket, coin
    cost_amount INT NOT NULL,
    guaranteed_ssr_count INT DEFAULT 100, -- 天井回数
    is_active BOOLEAN DEFAULT TRUE
);

-- 9. ガチャ排出プール
CREATE TABLE gacha_pool_items (
    pool_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gacha_id UUID REFERENCES gacha_masters(gacha_id) ON DELETE CASCADE,
    item_id UUID NOT NULL, -- itemsテーブルへの参照だが疎結合にする場合もあり
    rarity VARCHAR(10) NOT NULL, -- N, R, SR, SSR
    base_rate DECIMAL(10, 8) NOT NULL, -- 確率 (例: 0.01500000 = 1.5%)
    pickup_rate DECIMAL(10, 8) DEFAULT 0,
    is_pickup BOOLEAN DEFAULT FALSE,
    CONSTRAINT chk_rate CHECK (base_rate >= 0 AND pickup_rate >= 0)
);

-- 10. ガチャ履歴 (パーティショニング対象)
CREATE TABLE gacha_histories (
    history_id UUID NOT NULL DEFAULT gen_random_uuid(), -- PKの一部
    player_id UUID NOT NULL,
    gacha_id UUID NOT NULL,
    drawn_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    items_json JSONB NOT NULL, -- 排出結果リスト [{"item_id": "...", "rarity": "SSR"}]
    cost_paid INT NOT NULL,
    currency_type VARCHAR(20),
    pity_count_before INT,
    PRIMARY KEY (player_id, history_id) -- player_idでハッシュパーティショニング
) PARTITION BY HASH (player_id);

-- パーティション作成 (0-15)
CREATE TABLE gacha_histories_00 PARTITION OF gacha_histories FOR VALUES WITH (MODULUS 16, REMAINDER 0);
CREATE TABLE gacha_histories_01 PARTITION OF gacha_histories FOR VALUES WITH (MODULUS 16, REMAINDER 1);
-- ... (省略: 実際は15まで作成) ...

-- 11. 天井カウント
CREATE TABLE player_pity_counters (
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    gacha_id UUID REFERENCES gacha_masters(gacha_id) ON DELETE CASCADE,
    current_pity INT DEFAULT 0,
    guaranteed_triggered_count INT DEFAULT 0,
    last_pulled_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (player_id, gacha_id)
);

-- 12. ガチャ天井交換所
CREATE TABLE gacha_shop_exchange (
    exchange_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gacha_id UUID REFERENCES gacha_masters(gacha_id) ON DELETE CASCADE,
    item_id UUID NOT NULL,
    required_points INT NOT NULL
);
```

## 3. インベントリ・アイテム (Inventory Domain)

```sql
-- 13. アイテムマスタ
CREATE TABLE items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    item_type VARCHAR(20) NOT NULL, -- character, weapon, material
    rarity VARCHAR(10),
    description TEXT,
    max_stack INT DEFAULT 999,
    base_stats JSONB -- { "attack": 100, "hp": 500 }
);

-- 14. アイテムカテゴリ
CREATE TABLE item_categories (
    category_id INT PRIMARY KEY,
    name VARCHAR(50)
);

-- 15. プレイヤー所持アイテム
CREATE TABLE player_inventory (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(item_id),
    quantity INT DEFAULT 0,
    obtained_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_locked BOOLEAN DEFAULT FALSE,
    enhancement_level INT DEFAULT 0,
    exp BIGINT DEFAULT 0,
    extra_stats JSONB,
    UNIQUE(player_id, item_id, enhancement_level, extra_stats) -- スタック可能なアイテムの場合
);

-- 16. アイテム強化履歴
CREATE TABLE item_enhancements (
    enhancement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    target_inventory_id UUID REFERENCES player_inventory(inventory_id),
    material_item_ids JSONB, -- 消費素材リスト
    before_level INT,
    after_level INT,
    cost_coins BIGINT,
    enhanced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 17. 合成レシピ
CREATE TABLE item_recipes (
    recipe_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_item_id UUID REFERENCES items(item_id),
    required_materials JSONB, -- [{"item_id": "...", "count": 5}]
    cost_coins INT
);
```

## 4. イベント・クエスト (Event & Quest Domain)

```sql
-- 18. イベントマスタ
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    event_type VARCHAR(20), -- story, ranking, raid
    start_at TIMESTAMP WITH TIME ZONE,
    end_at TIMESTAMP WITH TIME ZONE,
    reward_json JSONB
);

-- 19. イベントステージ
CREATE TABLE event_stages (
    stage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(event_id) ON DELETE CASCADE,
    stage_order INT,
    stamina_cost INT,
    enemy_data JSONB
);

-- 20. イベント参加状況
CREATE TABLE event_participations (
    participation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    event_id UUID REFERENCES events(event_id) ON DELETE CASCADE,
    score BIGINT DEFAULT 0,
    current_rank INT,
    cleared_stages JSONB, -- [stage_id, stage_id...]
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, event_id)
);

-- 21. イベントランキングスナップショット
CREATE TABLE event_rankings (
    ranking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(event_id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    score BIGINT NOT NULL,
    rank INT NOT NULL,
    snapshot_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 22. イベント報酬
CREATE TABLE event_rewards (
    reward_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(event_id) ON DELETE CASCADE,
    condition_type VARCHAR(20), -- rank, point
    condition_value INT,
    reward_item_json JSONB
);

-- 23. クエストマスタ
CREATE TABLE quests (
    quest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    quest_type VARCHAR(20), -- main, daily, weekly
    stamina_cost INT,
    drop_table_json JSONB
);

-- 24. クエストログ
CREATE TABLE quest_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    quest_id UUID REFERENCES quests(quest_id),
    result VARCHAR(10), -- clear, fail
    drops_json JSONB,
    cleared_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 25. クエスト実績
CREATE TABLE quest_achievements (
    achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    achievement_key VARCHAR(50),
    progress INT DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 26. デイリー進捗
CREATE TABLE quest_daily_progress (
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    points INT DEFAULT 0,
    rewards_claimed JSONB,
    PRIMARY KEY (player_id, date)
);
```

## 5. ギルド・ソーシャル (Guild & Social Domain)

```sql
-- 27. ギルド
CREATE TABLE guilds (
    guild_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    level INT DEFAULT 1,
    exp BIGINT DEFAULT 0,
    member_count INT DEFAULT 1,
    max_members INT DEFAULT 20,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 28. ギルドメンバー
CREATE TABLE guild_members (
    member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id UUID REFERENCES guilds(guild_id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- leader, sub_leader, member
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id) -- 1プレイヤー1ギルド
);

-- 29. ギルド加入申請
CREATE TABLE guild_join_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id UUID REFERENCES guilds(guild_id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, player_id)
);

-- 30. GvG履歴
CREATE TABLE guild_battles (
    battle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_a_id UUID REFERENCES guilds(guild_id),
    guild_b_id UUID REFERENCES guilds(guild_id),
    winner_guild_id UUID,
    battle_date TIMESTAMP WITH TIME ZONE
);

-- 31. ギルドチャット
CREATE TABLE guild_chat_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id UUID REFERENCES guilds(guild_id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(player_id),
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 32. フレンド関係
CREATE TABLE friend_relations (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id_1 UUID REFERENCES players(player_id) ON DELETE CASCADE,
    player_id_2 UUID REFERENCES players(player_id) ON DELETE CASCADE,
    status VARCHAR(20), -- friend, block
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id_1, player_id_2)
);

-- 33. フレンド申請
CREATE TABLE friend_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sender_id, receiver_id)
);

-- 34. ブロックリスト
CREATE TABLE blocked_users (
    block_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    blocked_player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 35. 一般チャット
CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_type VARCHAR(20), -- world, room, whisper
    channel_id VARCHAR(50),
    sender_id UUID REFERENCES players(player_id),
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 6. PvP・ランキング (PvP Domain)

```sql
-- 36. PvP対戦
CREATE TABLE pvp_matches (
    match_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id_1 UUID REFERENCES players(player_id),
    player_id_2 UUID REFERENCES players(player_id),
    result VARCHAR(20), -- p1_win, p2_win, draw
    played_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 37. PvPレート
CREATE TABLE pvp_ratings (
    player_id UUID PRIMARY KEY REFERENCES players(player_id) ON DELETE CASCADE,
    rating INT DEFAULT 1500,
    tier VARCHAR(20) DEFAULT 'bronze',
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 38. シーズン
CREATE TABLE seasons (
    season_id INT PRIMARY KEY,
    name VARCHAR(50),
    start_at TIMESTAMP WITH TIME ZONE,
    end_at TIMESTAMP WITH TIME ZONE
);

-- 39. PvPシーズン履歴
CREATE TABLE pvp_season_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id INT REFERENCES seasons(season_id),
    player_id UUID REFERENCES players(player_id),
    final_rating INT,
    final_rank INT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 40. ランキングボードキャッシュ
CREATE TABLE leaderboards (
    board_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_type VARCHAR(50), -- pvp_weekly, event_xyz
    top_data_json JSONB, -- 上位100位のスナップショット
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 7. 課金・ショップ (Billing Domain)

```sql
-- 41. 商品マスタ
CREATE TABLE billing_products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_product_id VARCHAR(100) NOT NULL, -- apple/google ID
    platform VARCHAR(20), -- ios, android
    name VARCHAR(100),
    price DECIMAL(10, 2),
    gems_granted INT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 42. 購入履歴 (重要)
CREATE TABLE purchases (
    purchase_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id),
    product_id UUID REFERENCES billing_products(product_id),
    transaction_id VARCHAR(255) UNIQUE, -- ストア側のトランザクションID
    status VARCHAR(20), -- pending, verified, completed, failed
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP WITH TIME ZONE
);

-- 43. レシート検証ログ
CREATE TABLE purchase_receipts (
    receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_id UUID REFERENCES purchases(purchase_id),
    raw_receipt TEXT,
    verification_response JSONB,
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 44. 返金履歴
CREATE TABLE billing_refunds (
    refund_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_id UUID REFERENCES purchases(purchase_id),
    reason TEXT,
    refunded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 45. サブスクリプション
CREATE TABLE billing_subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id),
    product_id UUID REFERENCES billing_products(product_id),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_auto_renew BOOLEAN DEFAULT TRUE
);
```

## 8. システム・運用 (System & Ops Domain)

```sql
-- 46. お知らせ
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(100),
    body TEXT,
    target_type VARCHAR(20), -- all, individual
    target_id UUID, -- player_id if individual
    scheduled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 47. プレイヤーメール (受信箱)
CREATE TABLE player_mails (
    mail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    subject VARCHAR(100),
    body TEXT,
    attachments_json JSONB, -- [{"item_id": "...", "count": 1}]
    is_read BOOLEAN DEFAULT FALSE,
    is_claimed BOOLEAN DEFAULT FALSE,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 48. メンテナンスログ
CREATE TABLE maintenance_logs (
    maintenance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_at TIMESTAMP WITH TIME ZONE,
    end_at TIMESTAMP WITH TIME ZONE,
    message TEXT,
    affected_features JSONB
);

-- 49. 管理操作ログ
CREATE TABLE admin_operations (
    op_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID, -- 管理者ID
    target_player_id UUID,
    operation_type VARCHAR(50),
    details_json JSONB,
    operated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 50. アプリバージョン管理
CREATE TABLE client_versions (
    version_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    platform VARCHAR(20),
    version_string VARCHAR(20),
    is_force_update BOOLEAN DEFAULT FALSE,
    released_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 51. ログインボーナス
CREATE TABLE player_login_bonuses (
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    bonus_master_id INT,
    consecutive_days INT DEFAULT 0,
    last_claimed_date DATE,
    PRIMARY KEY (player_id, bonus_master_id)
);

-- 52. ミッション
CREATE TABLE missions (
    mission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(100),
    condition_type VARCHAR(50),
    condition_value INT,
    rewards_json JSONB
);

-- 53. ミッション進捗
CREATE TABLE player_missions (
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    mission_id UUID REFERENCES missions(mission_id),
    progress INT DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    is_claimed BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (player_id, mission_id)
);

-- 54. 称号
CREATE TABLE player_titles (
    player_id UUID REFERENCES players(player_id) ON DELETE CASCADE,
    title_id INT,
    obtained_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, title_id)
);
```
