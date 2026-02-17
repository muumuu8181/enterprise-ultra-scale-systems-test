from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.models.story_models import Chapter, Stage, UserStageProgress
from src.models.user import User

class StoryService:
    """
    ストーリーモードに関するビジネスロジックを提供するサービスクラス
    """

    @staticmethod
    async def unlock_chapter(user_id: int, chapter_id: int, db: AsyncSession) -> bool:
        """
        指定された章が解放可能かチェックする。
        ここでは「前の章の全ステージをクリアしていること」を条件とする。
        第1章は常に解放。
        """
        chapter = await db.get(Chapter, chapter_id)
        if not chapter:
            return False

        # 第1章は無条件解放
        if chapter.order == 1:
            return True

        # 前の章を取得
        stmt = select(Chapter).where(Chapter.order == chapter.order - 1)
        result = await db.execute(stmt)
        prev_chapter = result.scalars().first()

        if not prev_chapter:
            # 前の章が見つからない場合（データ不整合でなければ）解放とみなす
            return True

        # 前の章のステージ一覧を取得
        stmt_stages = select(Stage).where(Stage.chapter_id == prev_chapter.id)
        result_stages = await db.execute(stmt_stages)
        stages = result_stages.scalars().all()

        if not stages:
            return True # ステージがないならクリア扱い

        # ユーザーのクリア済みステージ数を取得
        stage_ids = [s.id for s in stages]
        # 空リストの場合はSQLエラー回避のため早期リターン
        if not stage_ids:
            return True

        stmt_progress = select(UserStageProgress).where(
            and_(
                UserStageProgress.user_id == user_id,
                UserStageProgress.stage_id.in_(stage_ids),
                UserStageProgress.cleared == True
            )
        )
        result_progress = await db.execute(stmt_progress)
        cleared_progress = result_progress.scalars().all()

        # 全ステージクリアしていれば解放可能
        return len(cleared_progress) == len(stages)

    @staticmethod
    def calculate_stars(stage: Stage, score: int, time_sec: int) -> int:
        """
        ステージクリア時の星の獲得数を計算する。
        基本1つ（クリア）、条件達成で最大3つまで。
        条件は JSON 形式で {"time_limit": int, "min_score": int} を想定。
        """
        stars = 1 # クリアで1つ

        if not stage.star_conditions:
            return 3 # 条件設定がなければ最大評価

        conditions = stage.star_conditions

        # 条件1: 時間制限 (秒以内)
        if "time_limit" in conditions:
            if time_sec <= conditions["time_limit"]:
                stars += 1

        # 条件2: スコア (以上)
        if "min_score" in conditions:
            if score >= conditions["min_score"]:
                stars += 1

        return min(stars, 3)

    @staticmethod
    async def complete_stage(user_id: int, stage_id: int, score: int, time_sec: int, db: AsyncSession) -> UserStageProgress:
        """
        ステージクリア処理を行う。進捗を更新し、獲得した星を保存する。
        """
        stage = await db.get(Stage, stage_id)
        if not stage:
            raise ValueError(f"Stage with id {stage_id} not found")

        # Cache chapter_id for later use (avoid lazy load after commit)
        chapter_id = stage.chapter_id

        # 星の計算
        stars = StoryService.calculate_stars(stage, score, time_sec)

        # 既存の進捗を取得
        stmt = select(UserStageProgress).where(
            and_(UserStageProgress.user_id == user_id, UserStageProgress.stage_id == stage_id)
        )
        result = await db.execute(stmt)
        progress = result.scalars().first()

        is_first_clear = False
        if progress:
            # 更新
            if not progress.cleared:
                is_first_clear = True
                progress.cleared = True
            progress.attempts += 1
            if score > progress.best_score:
                progress.best_score = score
            if stars > progress.stars:
                progress.stars = stars
        else:
            # 新規作成
            is_first_clear = True
            progress = UserStageProgress(
                user_id=user_id,
                stage_id=stage_id,
                cleared=True,
                stars=stars,
                best_score=score,
                attempts=1
            )
            db.add(progress)

        # 即時コミット
        await db.commit()
        await db.refresh(progress)

        # 初回クリア時のみ章クリア判定と報酬付与を行う
        if is_first_clear:
             # 同じ章の全ステージを取得
             stmt_all = select(Stage.id).where(Stage.chapter_id == chapter_id)
             result_all = await db.execute(stmt_all)
             all_stage_ids = result_all.scalars().all()

             # ユーザーのクリア済みステージ数を取得
             if all_stage_ids:
                 stmt_cleared = select(UserStageProgress).where(
                     and_(
                         UserStageProgress.user_id == user_id,
                         UserStageProgress.stage_id.in_(all_stage_ids),
                         UserStageProgress.cleared == True
                     )
                 )
                 result_cleared = await db.execute(stmt_cleared)
                 cleared_count = len(result_cleared.scalars().all())

                 if cleared_count == len(all_stage_ids):
                     await StoryService.grant_chapter_rewards(user_id, chapter_id, db)

        return progress

    @staticmethod
    async def grant_chapter_rewards(user_id: int, chapter_id: int, db: AsyncSession):
        """
        章クリア報酬を付与する（簡易実装）。
        """
        chapter = await db.get(Chapter, chapter_id)
        if not chapter or not chapter.rewards:
            return

        # 報酬付与ロジック（例：User.currencyを加算）
        rewards = chapter.rewards
        if "currency" in rewards:
            amount = rewards["currency"]
            user = await db.get(User, user_id)
            if user:
                user.currency += amount
                await db.commit()
