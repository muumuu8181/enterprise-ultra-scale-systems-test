from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.tournament_models import Tournament, TournamentParticipant, TournamentMatch
from fastapi import HTTPException
import random
import math
from datetime import datetime, timezone
from typing import List, Optional

class TournamentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tournament(self, name: str, format: str, max_participants: int, prize_pool: dict = None) -> Tournament:
        """
        トーナメントを作成する
        Create a tournament
        """
        tournament = Tournament(
            name=name,
            format=format,
            max_participants=max_participants,
            prize_pool=prize_pool,
            status="scheduled"
        )
        self.db.add(tournament)
        await self.db.commit()
        await self.db.refresh(tournament)
        return tournament

    async def register_participant(self, tournament_id: int, user_id: int) -> TournamentParticipant:
        """
        ユーザーをトーナメントに登録する
        Register a user to the tournament
        """
        result = await self.db.execute(select(Tournament).where(Tournament.id == tournament_id))
        tournament = result.scalar_one_or_none()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        # Check existing registration
        result = await self.db.execute(select(TournamentParticipant).where(
            TournamentParticipant.tournament_id == tournament_id,
            TournamentParticipant.user_id == user_id
        ))
        if result.scalar_one_or_none():
             raise HTTPException(status_code=400, detail="User already registered")

        # Check capacity
        count_result = await self.db.execute(select(func.count(TournamentParticipant.id)).where(TournamentParticipant.tournament_id == tournament_id))
        count = count_result.scalar()
        if count >= tournament.max_participants:
             raise HTTPException(status_code=400, detail="Tournament is full")

        participant = TournamentParticipant(tournament_id=tournament_id, user_id=user_id)
        self.db.add(participant)
        await self.db.commit()
        await self.db.refresh(participant)
        return participant

    async def generate_bracket(self, tournament_id: int):
        """
        トーナメント表を生成する (シングルエリミネーション)
        Generate tournament bracket (Single Elimination)
        """
        result = await self.db.execute(select(Tournament).where(Tournament.id == tournament_id))
        tournament = result.scalar_one_or_none()
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")

        if tournament.status != "scheduled":
             raise HTTPException(status_code=400, detail="Tournament already started or completed")

        if tournament.format != "single_elimination":
             # ダブルエリミネーションなどは未実装
             # Double elimination and other formats are not implemented
             raise HTTPException(status_code=501, detail="Format not implemented")

        # Fetch participants
        result = await self.db.execute(select(TournamentParticipant).where(TournamentParticipant.tournament_id == tournament_id))
        participants = result.scalars().all()

        if len(participants) < 2:
            raise HTTPException(status_code=400, detail="Not enough participants")

        # Shuffle participants for random seeding
        participant_ids = [p.user_id for p in participants]
        random.shuffle(participant_ids)

        # Calculate number of rounds
        num_participants = len(participant_ids)
        # Find next power of 2
        next_power_of_2 = 2**math.ceil(math.log2(num_participants))

        # Pad with None to reach power of 2
        padded_participants = participant_ids + [None] * (next_power_of_2 - num_participants)

        # Round 1
        round_1_matches = []
        num_matches_r1 = next_power_of_2 // 2

        for i in range(num_matches_r1):
            p1 = padded_participants[i * 2]
            p2 = padded_participants[i * 2 + 1]

            match = TournamentMatch(
                tournament_id=tournament_id,
                round=1,
                match_number=i + 1,
                player1_id=p1,
                player2_id=p2
            )

            # Auto-win for bye
            if p2 is None and p1 is not None:
                match.winner_id = p1
            elif p1 is None and p2 is not None:
                match.winner_id = p2

            self.db.add(match)
            round_1_matches.append(match)

        await self.db.flush()

        # Create subsequent rounds (placeholders)
        current_round_matches = round_1_matches
        round_num = 1

        while len(current_round_matches) > 1:
            round_num += 1
            next_round_matches = []
            num_matches_next = len(current_round_matches) // 2

            for i in range(num_matches_next):
                match = TournamentMatch(
                    tournament_id=tournament_id,
                    round=round_num,
                    match_number=i + 1,
                    player1_id=None,
                    player2_id=None
                )
                self.db.add(match)
                next_round_matches.append(match)

            current_round_matches = next_round_matches
            await self.db.flush()

        tournament.status = "ongoing"
        tournament.starts_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Advance byes
        # We need to process matches that already have a winner (from Round 1 byes)
        result = await self.db.execute(select(TournamentMatch).where(
            TournamentMatch.tournament_id == tournament_id,
            TournamentMatch.winner_id.isnot(None),
            TournamentMatch.round == 1
        ))
        completed_r1_matches = result.scalars().all()

        for match in completed_r1_matches:
            await self.advance_winner(match)

    async def report_match_result(self, tournament_id: int, match_id: int, winner_id: int, score_a: int, score_b: int) -> TournamentMatch:
        """
        試合結果を報告する
        Report match result
        """
        result = await self.db.execute(select(TournamentMatch).where(
            TournamentMatch.id == match_id,
            TournamentMatch.tournament_id == tournament_id
        ))
        match = result.scalar_one_or_none()

        if not match:
             raise HTTPException(status_code=404, detail="Match not found")

        if match.winner_id is not None:
             raise HTTPException(status_code=400, detail="Match already finished")

        if match.player1_id is None or match.player2_id is None:
             raise HTTPException(status_code=400, detail="Match is not ready (opponent missing)")

        if winner_id not in (match.player1_id, match.player2_id):
             raise HTTPException(status_code=400, detail="Invalid winner")

        match.winner_id = winner_id
        match.score_a = score_a
        match.score_b = score_b

        await self.db.commit()
        await self.db.refresh(match)

        await self.advance_winner(match)
        # Refresh match again because advance_winner might have committed the session, expiring objects
        await self.db.refresh(match)
        return match

    async def advance_winner(self, match: TournamentMatch):
        """
        勝者を次のラウンドに進める
        Advance winner to the next round
        """
        next_round = match.round + 1
        next_match_number = (match.match_number + 1) // 2

        result = await self.db.execute(select(TournamentMatch).where(
            TournamentMatch.tournament_id == match.tournament_id,
            TournamentMatch.round == next_round,
            TournamentMatch.match_number == next_match_number
        ))
        next_match = result.scalar_one_or_none()

        if next_match:
            if match.match_number % 2 == 1:
                next_match.player1_id = match.winner_id
            else:
                next_match.player2_id = match.winner_id

            await self.db.commit()
        else:
            # Check if this was the final match
            # If so, complete the tournament
            result = await self.db.execute(select(func.max(TournamentMatch.round)).where(TournamentMatch.tournament_id == match.tournament_id))
            max_round = result.scalar()

            if match.round == max_round:
                result = await self.db.execute(select(Tournament).where(Tournament.id == match.tournament_id))
                tournament = result.scalar_one_or_none()
                if tournament:
                    tournament.status = "completed"
                    await self.db.commit()

    async def calculate_standings(self, tournament_id: int) -> List[dict]:
        """
        順位を計算する
        Calculate standings
        """
        result = await self.db.execute(select(TournamentMatch).where(
            TournamentMatch.tournament_id == tournament_id,
            TournamentMatch.winner_id.isnot(None)
        ).order_by(TournamentMatch.round.desc()))

        completed_matches = result.scalars().all()

        if not completed_matches:
            return []

        max_round = max(m.round for m in completed_matches)
        standings = []
        processed_users = set()

        # Winner
        final_match = next((m for m in completed_matches if m.round == max_round), None)
        if final_match and final_match.winner_id:
            standings.append({"user_id": final_match.winner_id, "rank": 1})
            processed_users.add(final_match.winner_id)

            loser = final_match.player1_id if final_match.winner_id == final_match.player2_id else final_match.player2_id
            if loser:
                standings.append({"user_id": loser, "rank": 2})
                processed_users.add(loser)

        # Losers of previous rounds
        for r in range(max_round - 1, 0, -1):
            matches_in_round = [m for m in completed_matches if m.round == r]
            rank = pow(2, max_round - r) + 1
            for m in matches_in_round:
                loser = m.player1_id if m.winner_id == m.player2_id else m.player2_id
                if loser and loser not in processed_users:
                    standings.append({"user_id": loser, "rank": rank})
                    processed_users.add(loser)

        return standings

    async def get_bracket(self, tournament_id: int) -> List[TournamentMatch]:
        result = await self.db.execute(select(TournamentMatch).where(TournamentMatch.tournament_id == tournament_id).order_by(TournamentMatch.round, TournamentMatch.match_number))
        return result.scalars().all()
