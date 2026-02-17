# データベース設計書 (概要)

本システムは PostgreSQL 15 をメインDBとして使用し、50以上のテーブルで構成される。
大規模データへの対応として、履歴テーブルにはパーティショニングを適用し、頻繁なアクセスにはインデックス最適化を行う。

## 1. プレイヤー管理 (Player Domain)
| テーブル名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `players` | プレイヤー基本情報 (ID, 作成日, ステータス) | UUID PK |
| `player_auth` | 認証情報 (OAuthプロバイダ, Token) | Apple/Google/Twitter |
| `player_stats` | レベル, 経験値, スタミナ, 通貨保有量 | 頻繁に更新 |
| `player_profiles` | プロフィール詳細 (自己紹介, アバター設定) | |
| `player_device_info` | 端末情報 (OS, 機種, デバイスID) | 分析・サポート用 |
| `player_login_history` | ログイン履歴 (IP, 日時) | セキュリティ監査 |
| `player_banned_history` | アカウント停止履歴 | 不正対策 |

## 2. ガチャシステム (Gacha Domain)
| テーブル名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `gacha_masters` | ガチャ筐体定義 (期間, コスト, タイプ) | |
| `gacha_pool_items` | ガチャ排出アイテム一覧と確率定義 | |
| `gacha_histories` | ガチャ実行履歴 (結果, コスト) | **パーティショニング必須** |
| `player_pity_counters` | プレイヤー別天井カウント情報 | |
| `gacha_shop_exchange` | ガチャおまけポイント(天井)交換所定義 | |

## 3. インベントリ・アイテム (Inventory Domain)
| テーブル名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `items` | アイテムマスタ (名称, 種類, レアリティ) | |
| `item_categories` | アイテムカテゴリ定義 | |
| `player_inventory` | プレイヤー所持アイテム情報 | 数量, ロック状態 |
| `item_enhancements` | アイテム強化・合成履歴 | |
| `item_recipes` | 合成・進化レシピ定義 | |

## 4. イベント・クエスト (Event & Quest Domain)
| テーブル名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `events` | イベント定義 (期間, 形式) | |
| `event_stages` | イベント内ステージ構成 | |
| `event_participations` | イベント参加状況, 現在スコア | |
| `event_rankings` | イベントランキングスナップショット | |
| `event_rewards` | イベント報酬定義 | |
| `quests` | クエストマスタ (消費スタミナ, 報酬) | |
| `quest_logs` | クエスト実行ログ (勝敗, ドロップ) | |
| `quest_achievements` | 実績・称号獲得条件 | |
| `quest_daily_progress` | デイリークエスト進捗管理 | |

## 5. ギルド・ソーシャル (Guild & Social Domain)
| テーブル名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `guilds` | ギルド基本情報 (レベル, 経験値) | |
| `guild_members` | ギルドメンバー・役職管理 | |
| `guild_join_requests` | ギルド加入申請 | |
| `guild_battles` | GvG対戦履歴 | |
| `guild_chat_logs` | ギルドチャットログ | |
| `friend_relations` | フレンド関係 (申請中, 承認, ブロック) | |
| `friend_requests` | フレンド申請詳細 | |
| `blocked_users` | ブロックリスト | |
| `chat_messages` | 全体/個別チャットメッセージ | |

## 6. PvP・ランキング (PvP Domain)
| テーブル名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `pvp_matches` | PvP対戦履歴 | |
| `pvp_ratings` | プレイヤーレーティング (Elo/Rate) | |
| `pvp_seasons` | PvPシーズン定義 | |
| `pvp_ranking_rewards` | ランキング報酬定義 | |
| `leaderboards` | ランキング集計結果キャッシュ | |

## 7. 課金・ショップ (Billing Domain)
| テーブル名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `billing_products` | 商品マスタ (各ストアID, 価格) | |
| `purchases` | 購入トランザクション管理 | 冪等性担保 |
| `purchase_receipts` | レシート検証結果ログ | |
| `billing_refunds` | 返金処理履歴 | |
| `billing_subscriptions` | サブスクリプション状態管理 | |

## 8. システム・運用 (System & Ops Domain)
| テーブル名 | 説明 | 備考 |
| :--- | :--- | :--- |
| `notifications` | お知らせ・プッシュ通知履歴 | |
| `player_mails` | プレイヤー受信メール (プレゼント等) | |
| `mail_templates` | メールテンプレート | |
| `maintenance_logs` | メンテナンス実施履歴 | |
| `admin_operations` | 管理画面操作ログ | 監査用 |
| `system_config` | 動的システム設定 (Feature Flag等) | |
| `client_versions` | アプリバージョン管理 (強制アップデート) | |
| `asset_bundles` | アセットバンドル管理 (DLC) | |
| `player_login_bonuses` | ログインボーナス定義・履歴 | |
| `missions` | ミッションマスタ | |
| `player_missions` | ミッション達成状況 | |
| `player_titles` | 獲得称号一覧 | |
| `stamina_recoveries` | スタミナ回復履歴 | |
| `seasons` | ゲーム内シーズン全般管理 | |
