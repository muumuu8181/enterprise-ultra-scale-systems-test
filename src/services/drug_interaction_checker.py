from typing import List

async def check_interactions(medication_ids: List[int]) -> List[str]:
    """
    薬物相互作用をチェックする (DrugBank API統合モック)

    Args:
        medication_ids (List[int]): チェック対象の薬剤IDリスト

    Returns:
        List[str]: 検出された相互作用のリスト
    """
    # モック実装: DrugBank APIへの問い合わせをシミュレート
    interactions = []

    # テスト用の簡易ロジック: ID 1と2が含まれている場合に相互作用を返す
    if 1 in medication_ids and 2 in medication_ids:
        interactions.append("重大な相互作用: 薬剤Aと薬剤Bの併用は避けてください (DrugBank ID: DB00123)")

    return interactions
