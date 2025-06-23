import numpy as np
import pandas as pd
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, and_
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
import pickle
import json

from ..models import Country, FeatureVector, RiskScoreV2
from ..core.logging import get_logger

logger = get_logger(__name__)

class MLRiskScoringService:
    """
    ML-based risk scoring service implementing Random Forest + XGBoost ensemble
    from technical specification with confidence intervals
    """
    
    def __init__(self):
        self.model_version = "1.0"
        
        # Model configurations from technical spec
        self.rf_config = {
            "n_estimators": 100,
            "max_depth": 10,
            "min_samples_split": 5,
            "random_state": 42
        }
        
        self.xgb_config = {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 6,
            "random_state": 42
        }
        
        # Component weights from technical spec
        self.component_weights = {
            "political_stability": 0.25,
            "conflict_risk": 0.30,
            "economic_risk": 0.25,
            "institutional_quality": 0.20
        }
        
        # Models for each component
        self.models = {
            "political_stability": {"rf": None, "xgb": None},
            "conflict_risk": {"rf": None, "xgb": None},
            "economic_risk": {"rf": None, "xgb": None},
            "institutional_quality": {"rf": None, "xgb": None}
        }
        
        # Feature categories for each component
        self.feature_mappings = {
            "political_stability": [
                "political_stability_latest", "government_effectiveness_latest",
                "protest_events_7d", "protest_events_30d", "protest_events_90d",
                "avg_sentiment_7d", "avg_sentiment_30d", "sentiment_volatility_7d"
            ],
            "conflict_risk": [
                "conflict_events_7d", "conflict_events_30d", "conflict_events_90d",
                "severity_max_7d", "severity_max_30d", "regional_instability",
                "event_trend_7d", "event_trend_30d"
            ],
            "economic_risk": [
                "gdp_growth_latest", "inflation_latest", "debt_to_gdp_latest",
                "trade_gdp_ratio_latest", "gdp_growth_yoy_change", "inflation_yoy_change",
                "gdp_growth_volatility", "inflation_volatility", "economic_events_30d"
            ],
            "institutional_quality": [
                "regulatory_quality_latest", "rule_of_law_latest", "control_of_corruption_latest",
                "government_effectiveness_latest", "political_stability_latest",
                "diplomatic_events_30d", "diplomatic_events_90d"
            ]
        }
    
    async def train_models(
        self,
        session: AsyncSession,
        min_training_samples: int = 200
    ) -> Dict[str, Any]:
        """
        Train ML models for risk scoring components
        
        Returns:
            Training results and performance metrics
        """
        training_results = {}
        
        try:
            # Get training data
            features_df, targets_df = await self._prepare_training_data(session)
            
            if len(features_df) < min_training_samples:
                logger.warning(f"Insufficient training data: {len(features_df)} < {min_training_samples}")
                return {"error": "Insufficient training data"}
            
            logger.info(f"Training models with {len(features_df)} samples")
            
            # Train models for each component
            for component in self.component_weights.keys():
                logger.info(f"Training models for {component}")
                
                component_results = await self._train_component_models(
                    features_df, targets_df, component
                )
                training_results[component] = component_results
            
            # Save models
            await self._save_models()
            
            return {
                "status": "success",
                "model_version": self.model_version,
                "training_samples": len(features_df),
                "components": training_results,
                "trained_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error training models: {str(e)}")
            return {"error": str(e)}
    
    async def _prepare_training_data(
        self,
        session: AsyncSession
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepare training data from feature vectors and risk scores"""
        
        # Get feature vectors with corresponding risk scores
        result = await session.execute(
            select(FeatureVector, RiskScoreV2, Country.name)
            .join(RiskScoreV2, and_(
                FeatureVector.country_id == RiskScoreV2.country_id,
                FeatureVector.feature_date == RiskScoreV2.score_date
            ))
            .join(Country)
            .order_by(FeatureVector.feature_date)
        )
        
        training_data = result.fetchall()
        
        if not training_data:
            logger.warning("No training data found")
            return pd.DataFrame(), pd.DataFrame()
        
        # Convert to DataFrames
        features_list = []
        targets_list = []
        
        for feature_vector, risk_score, country_name in training_data:
            # Extract features
            features = feature_vector.features.copy()
            features["country_id"] = feature_vector.country_id
            features["feature_date"] = feature_vector.feature_date.isoformat()
            
            # Extract targets
            targets = {
                "country_id": risk_score.country_id,
                "score_date": risk_score.score_date.isoformat(),
                "political_stability": float(risk_score.political_stability_score or 50.0),
                "conflict_risk": float(risk_score.conflict_risk_score or 50.0),
                "economic_risk": float(risk_score.economic_risk_score or 50.0),
                "institutional_quality": float(risk_score.institutional_quality_score or 50.0),
                "overall_score": float(risk_score.overall_score or 50.0)
            }
            
            features_list.append(features)
            targets_list.append(targets)
        
        features_df = pd.DataFrame(features_list)
        targets_df = pd.DataFrame(targets_list)
        
        # Fill missing values with appropriate defaults
        features_df = features_df.fillna(0.0)
        
        logger.info(f"Prepared training data: {len(features_df)} samples, {len(features_df.columns)} features")
        return features_df, targets_df
    
    async def _train_component_models(
        self,
        features_df: pd.DataFrame,
        targets_df: pd.DataFrame,
        component: str
    ) -> Dict[str, Any]:
        """Train Random Forest and XGBoost models for a specific component"""
        
        try:
            # Get relevant features for this component
            relevant_features = self.feature_mappings[component]
            available_features = [f for f in relevant_features if f in features_df.columns]
            
            if not available_features:
                logger.warning(f"No relevant features found for {component}")
                return {"error": "No relevant features"}
            
            X = features_df[available_features].values
            y = targets_df[component].values
            
            # Time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            
            # Train Random Forest
            rf_scores = []
            xgb_scores = []
            
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                # Random Forest
                rf = RandomForestRegressor(**self.rf_config)
                rf.fit(X_train, y_train)
                rf_pred = rf.predict(X_val)
                rf_scores.append(mean_absolute_error(y_val, rf_pred))
                
                # XGBoost
                xgb_model = xgb.XGBRegressor(**self.xgb_config)
                xgb_model.fit(X_train, y_train)
                xgb_pred = xgb_model.predict(X_val)
                xgb_scores.append(mean_absolute_error(y_val, xgb_pred))
            
            # Train final models on full dataset
            self.models[component]["rf"] = RandomForestRegressor(**self.rf_config)
            self.models[component]["rf"].fit(X, y)
            
            self.models[component]["xgb"] = xgb.XGBRegressor(**self.xgb_config)
            self.models[component]["xgb"].fit(X, y)
            
            return {
                "rf_cv_mae": np.mean(rf_scores),
                "xgb_cv_mae": np.mean(xgb_scores),
                "features_used": available_features,
                "training_samples": len(X)
            }
            
        except Exception as e:
            logger.error(f"Error training {component} models: {str(e)}")
            return {"error": str(e)}
    
    async def predict_risk_scores(
        self,
        session: AsyncSession,
        country_id: int,
        target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Predict risk scores for a country using trained models
        
        Returns:
            Dictionary with predicted scores and confidence intervals
        """
        try:
            # Get feature vector for the target date
            result = await session.execute(
                select(FeatureVector).where(
                    and_(
                        FeatureVector.country_id == country_id,
                        FeatureVector.feature_date == target_date
                    )
                )
            )
            feature_vector = result.scalar_one_or_none()
            
            if not feature_vector:
                logger.warning(f"No features found for country {country_id} on {target_date}")
                return None
            
            features = feature_vector.features
            predictions = {}
            confidence_intervals = {}
            
            # Predict each component
            for component in self.component_weights.keys():
                try:
                    component_pred, component_ci = await self._predict_component(
                        features, component
                    )
                    predictions[component] = component_pred
                    confidence_intervals[component] = component_ci
                    
                except Exception as e:
                    logger.warning(f"Error predicting {component}: {str(e)}")
                    predictions[component] = 50.0  # Default value
                    confidence_intervals[component] = {"lower": 40.0, "upper": 60.0}
            
            # Calculate overall score using component weights
            overall_score = sum(
                predictions[component] * weight
                for component, weight in self.component_weights.items()
            )
            
            # Calculate overall confidence interval
            overall_lower = sum(
                confidence_intervals[component]["lower"] * weight
                for component, weight in self.component_weights.items()
            )
            overall_upper = sum(
                confidence_intervals[component]["upper"] * weight
                for component, weight in self.component_weights.items()
            )
            
            return {
                "country_id": country_id,
                "score_date": target_date,
                "overall_score": round(overall_score, 2),
                "component_scores": {
                    "political_stability": round(predictions["political_stability"], 2),
                    "conflict_risk": round(predictions["conflict_risk"], 2),
                    "economic_risk": round(predictions["economic_risk"], 2),
                    "institutional_quality": round(predictions["institutional_quality"], 2)
                },
                "confidence_intervals": {
                    "overall": {
                        "lower": round(overall_lower, 2),
                        "upper": round(overall_upper, 2)
                    },
                    "components": confidence_intervals
                },
                "model_version": self.model_version
            }
            
        except Exception as e:
            logger.error(f"Error predicting risk scores for country {country_id}: {str(e)}")
            return None
    
    async def _predict_component(
        self,
        features: Dict[str, Any],
        component: str
    ) -> Tuple[float, Dict[str, float]]:
        """Predict a single component score with confidence interval"""
        
        # Get relevant features
        relevant_features = self.feature_mappings[component]
        feature_values = []
        
        for feature_name in relevant_features:
            value = features.get(feature_name, 0.0)
            feature_values.append(float(value) if value is not None else 0.0)
        
        X = np.array(feature_values).reshape(1, -1)
        
        # Get predictions from both models
        rf_pred = self.models[component]["rf"].predict(X)[0]
        xgb_pred = self.models[component]["xgb"].predict(X)[0]
        
        # Ensemble prediction (average)
        ensemble_pred = (rf_pred + xgb_pred) / 2.0
        
        # Calculate confidence interval using Random Forest individual predictions
        rf_individual_preds = []
        for estimator in self.models[component]["rf"].estimators_:
            pred = estimator.predict(X)[0]
            rf_individual_preds.append(pred)
        
        # 95% confidence interval
        std_dev = np.std(rf_individual_preds)
        confidence_interval = {
            "lower": max(0.0, ensemble_pred - 1.96 * std_dev),
            "upper": min(100.0, ensemble_pred + 1.96 * std_dev)
        }
        
        # Clamp prediction to valid range
        ensemble_pred = max(0.0, min(100.0, ensemble_pred))
        
        return ensemble_pred, confidence_interval
    
    async def store_predictions(
        self,
        session: AsyncSession,
        predictions: Dict[str, Any]
    ) -> bool:
        """Store ML predictions in database"""
        try:
            country_id = predictions["country_id"]
            score_date = predictions["score_date"]
            
            # Check if score already exists
            existing = await session.execute(
                select(RiskScoreV2.id).where(
                    and_(
                        RiskScoreV2.country_id == country_id,
                        RiskScoreV2.score_date == score_date
                    )
                )
            )
            
            score_data = {
                "overall_score": predictions["overall_score"],
                "political_stability_score": predictions["component_scores"]["political_stability"],
                "conflict_risk_score": predictions["component_scores"]["conflict_risk"],
                "economic_risk_score": predictions["component_scores"]["economic_risk"],
                "institutional_quality_score": predictions["component_scores"]["institutional_quality"],
                "spillover_risk_score": 50.0,  # Placeholder for MVP
                "confidence_lower": predictions["confidence_intervals"]["overall"]["lower"],
                "confidence_upper": predictions["confidence_intervals"]["overall"]["upper"],
                "model_version": predictions["model_version"]
            }
            
            if existing.fetchone():
                # Update existing score
                await session.execute(
                    RiskScoreV2.__table__.update()
                    .where(
                        and_(
                            RiskScoreV2.country_id == country_id,
                            RiskScoreV2.score_date == score_date
                        )
                    )
                    .values(**score_data)
                )
            else:
                # Insert new score
                await session.execute(
                    insert(RiskScoreV2).values(
                        country_id=country_id,
                        score_date=score_date,
                        **score_data
                    )
                )
            
            await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing predictions: {str(e)}")
            await session.rollback()
            return False
    
    async def _save_models(self) -> None:
        """Save trained models to disk"""
        try:
            models_data = {
                "version": self.model_version,
                "models": {},
                "feature_mappings": self.feature_mappings,
                "component_weights": self.component_weights
            }
            
            for component in self.models:
                models_data["models"][component] = {
                    "rf": pickle.dumps(self.models[component]["rf"]),
                    "xgb": pickle.dumps(self.models[component]["xgb"])
                }
            
            # Save to file (in production, would use proper model storage)
            with open(f"/tmp/risk_models_{self.model_version}.pkl", "wb") as f:
                pickle.dump(models_data, f)
                
            logger.info(f"Saved models version {self.model_version}")
            
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
    
    async def load_models(self, model_version: str = None) -> bool:
        """Load trained models from disk"""
        try:
            if model_version is None:
                model_version = self.model_version
            
            with open(f"/tmp/risk_models_{model_version}.pkl", "rb") as f:
                models_data = pickle.load(f)
            
            self.model_version = models_data["version"]
            self.feature_mappings = models_data["feature_mappings"]
            self.component_weights = models_data["component_weights"]
            
            for component in models_data["models"]:
                self.models[component] = {
                    "rf": pickle.loads(models_data["models"][component]["rf"]),
                    "xgb": pickle.loads(models_data["models"][component]["xgb"])
                }
            
            logger.info(f"Loaded models version {self.model_version}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False
    
    def models_trained(self) -> bool:
        """Check if models are trained and ready"""
        for component in self.models:
            if (self.models[component]["rf"] is None or 
                self.models[component]["xgb"] is None):
                return False
        return True