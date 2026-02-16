from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import timedelta

app = FastAPI(title="Demand Forecasting Service")

class HistoricalData(BaseModel):
    date: str
    value: float

class PredictionRequest(BaseModel):
    history: List[HistoricalData]
    days_to_predict: int

class PredictionResult(BaseModel):
    date: str
    predicted_value: float

@app.post("/predict", response_model=List[PredictionResult])
def predict_demand(request: PredictionRequest):
    if len(request.history) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 data points for prediction")

    try:
        # Convert input to DataFrame
        # Pydantic v2 uses model_dump(), v1 used dict()
        try:
            data = [h.model_dump() for h in request.history]
        except AttributeError:
            data = [h.dict() for h in request.history]

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        start_date = df['date'].min()
        df['day_index'] = (df['date'] - start_date).dt.days

        # Train simple model (Linear Regression as a placeholder for Prophet/LSTM)
        X = df[['day_index']]
        y = df['value']
        model = LinearRegression()
        model.fit(X, y)

        # Predict future
        last_day = df['day_index'].max()
        future_indices = np.array([[last_day + i] for i in range(1, request.days_to_predict + 1)])
        predictions = model.predict(future_indices)

        results = []
        for i, pred in enumerate(predictions):
            future_date = start_date + timedelta(days=int(future_indices[i][0]))
            results.append(PredictionResult(date=future_date.strftime('%Y-%m-%d'), predicted_value=pred))

        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Demand Forecasting Service is running"}
