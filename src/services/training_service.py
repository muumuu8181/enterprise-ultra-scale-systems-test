import pandas as pd
from typing import List, Dict, Any, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.models.training_models import TrainingDataset

async def point_in_time_join(entities_df: pd.DataFrame, feature_views: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Performs a point-in-time correct join between an entities DataFrame and a list of feature views.

    Args:
        entities_df: DataFrame containing entity IDs and 'event_timestamp'.
        feature_views: List of dictionaries, each containing:
            - 'df': DataFrame with features
            - 'join_key': Column name to join on (entity ID)
            - 'timestamp_col': Column name for timestamp in feature DataFrame

    Returns:
        DataFrame with features joined to entities.
    """
    if "event_timestamp" not in entities_df.columns:
        raise ValueError("entities_df must have 'event_timestamp' column")

    # Sort for merge_asof
    result_df = entities_df.sort_values("event_timestamp")

    for fv in feature_views:
        fv_df = fv.get('df')
        join_key = fv.get('join_key')
        ts_col = fv.get('timestamp_col')

        if fv_df is None or join_key is None or ts_col is None:
            continue

        # Ensure feature dataframe is sorted by timestamp
        fv_df = fv_df.sort_values(ts_col)

        # Perform point-in-time join (asof join)
        result_df = pd.merge_asof(
            result_df,
            fv_df,
            left_on="event_timestamp",
            right_on=ts_col,
            by=join_key,
            direction="backward"
        )

    return result_df

async def create_training_dataset(
    db: Session,
    feature_view_id: str,
    label_query: str,
    start_date: datetime,
    end_date: datetime
) -> TrainingDataset:
    """
    Creates a training dataset by fetching labels and features, joining them,
    persisting the result, and creating a database record.
    """
    # Mock implementation of fetching data
    # In a real system, this would execute the label_query and fetch features

    # Placeholder for snapshot path
    snapshot_path = f"s3://featurestore/training_datasets/{feature_view_id}/{datetime.now(timezone.utc).timestamp()}.parquet"

    # Mock sizes
    train_size = 0.7
    val_size = 0.2
    test_size = 0.1

    # Create the record
    training_dataset = TrainingDataset(
        feature_view_id=feature_view_id,
        label_source=label_query,
        train_size=train_size,
        val_size=val_size,
        test_size=test_size,
        snapshot_path=snapshot_path,
        created_at=datetime.now(timezone.utc)
    )

    db.add(training_dataset)
    db.commit()
    db.refresh(training_dataset)

    return training_dataset
