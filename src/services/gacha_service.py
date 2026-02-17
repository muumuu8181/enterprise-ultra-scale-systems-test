import random
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.gacha import GachaRate, GachaBanner

class GachaService:
    BASE_RATE_5_STAR = 0.006  # 0.6%
    SOFT_PITY_START = 75
    HARD_PITY = 90

    # 4-star logic simplified for this task, focus on 5-star pity
    RATE_4_STAR = 0.051

    @classmethod
    def calculate_probability(cls, pity_count: int) -> float:
        if pity_count < cls.SOFT_PITY_START:
            return cls.BASE_RATE_5_STAR
        elif pity_count >= cls.HARD_PITY:
            return 1.0
        else:
            # Linear increase from 75 to 90
            # 75: 0.6%
            # ...
            # 89: high%
            # 90: 100%
            # Common formula: rate + (pity - 74) * ( (1 - rate) / (90 - 74) ) ?
            # Or simplified: increase by ~6% per pull
            extra_rate = (pity_count - cls.SOFT_PITY_START + 1) * 0.06
            return min(1.0, cls.BASE_RATE_5_STAR + extra_rate)

    @classmethod
    def select_item(cls, rates: List[GachaRate], target_rarity: int) -> GachaRate:
        candidates = [r for r in rates if r.rarity == target_rarity]
        if not candidates:
            raise ValueError(f"No items for rarity {target_rarity}")

        total_weight = sum(r.weight for r in candidates)
        pick = random.randint(1, total_weight)
        current = 0
        for r in candidates:
            current += r.weight
            if pick <= current:
                return r
        return candidates[-1]

    @classmethod
    def simulate_pulls(cls, rates: List[GachaRate], count: int, current_pity: int) -> Tuple[List[dict], int]:
        results = []
        pity = current_pity

        # Ensure we have rates
        rates_5 = [r for r in rates if r.rarity == 5]
        rates_4 = [r for r in rates if r.rarity == 4]
        rates_3 = [r for r in rates if r.rarity == 3]

        if not rates_5 or not rates_4 or not rates_3:
             # Fallback if rates are missing for simplicity in tests/mock
             # In real app, this should error out
             pass

        for _ in range(count):
            pity += 1
            prob_5 = cls.calculate_probability(pity)

            roll = random.random()

            if roll < prob_5:
                # 5 Star
                item = cls.select_item(rates, 5)
                results.append({"item_id": item.item_id, "rarity": 5, "is_pickup": item.is_pickup})
                pity = 0
            else:
                # Not 5 Star
                # Check 4 Star (simplified fixed rate for now, usually has pity too)
                if random.random() < cls.RATE_4_STAR:
                    item = cls.select_item(rates, 4)
                    results.append({"item_id": item.item_id, "rarity": 4, "is_pickup": item.is_pickup})
                else:
                    item = cls.select_item(rates, 3)
                    results.append({"item_id": item.item_id, "rarity": 3, "is_pickup": item.is_pickup})

        return results, pity
