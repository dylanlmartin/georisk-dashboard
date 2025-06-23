import numpy as np
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, func, and_
from sklearn.linear_model import LinearRegression

from ..models import (Country, RawEvent, ProcessedEvent, EconomicIndicator, 
                     FeatureVector, RiskScoreV2)
from ..core.logging import get_logger

logger = get_logger(__name__)

class FeatureEngineeringService:
    """
    Feature engineering service implementing time-series and economic features
    from technical specification for ML pipeline
    """
    
    def __init__(self):
        # Time periods for feature calculation
        self.time_periods = [7, 30, 90, 365]  # days
        
        # Economic indicators we track
        self.economic_indicators = {
            "PV.EST": "political_stability",
            "GE.EST": "government_effectiveness", 
            "RQ.EST": "regulatory_quality",
            "RL.EST": "rule_of_law",
            "CC.EST": "control_of_corruption",
            "NY.GDP.MKTP.KD.ZG": "gdp_growth",
            "FP.CPI.TOTL.ZG": "inflation",
            "GC.DOD.TOTL.GD.ZS": "debt_to_gdp",
            "NE.TRD.GNFS.ZS": "trade_gdp_ratio"
        }
    
    async def generate_features_for_country(
        self,
        session: AsyncSession,
        country_id: int,
        target_date: date
    ) -> Dict[str, Any]:
        """
        Generate all features for a country on a specific date
        
        Args:
            session: Database session
            country_id: Country ID
            target_date: Date to generate features for
            
        Returns:
            Dictionary of engineered features
        """
        features = {}
        
        try:
            # Time series features from events
            event_features = await self._generate_event_features(
                session, country_id, target_date
            )
            features.update(event_features)
            
            # Economic indicator features
            economic_features = await self._generate_economic_features(
                session, country_id, target_date
            )
            features.update(economic_features)
            
            # Network features (simplified for MVP)
            network_features = await self._generate_network_features(
                session, country_id, target_date
            )
            features.update(network_features)
            
            # Add metadata
            features["feature_date"] = target_date.isoformat()
            features["country_id"] = country_id
            features["generated_at"] = datetime.now().isoformat()
            
            logger.info(f"Generated {len(features)} features for country {country_id}")
            return features
            
        except Exception as e:
            logger.error(f"Error generating features for country {country_id}: {str(e)}")
            return {}
    
    async def _generate_event_features(
        self,
        session: AsyncSession,
        country_id: int,
        target_date: date
    ) -> Dict[str, Any]:
        """Generate time-series features from processed events"""
        features = {}
        
        for period in self.time_periods:
            try:
                start_date = target_date - timedelta(days=period)
                
                # Get processed events in period
                result = await session.execute(
                    select(ProcessedEvent, RawEvent)
                    .join(RawEvent)
                    .where(
                        and_(
                            RawEvent.country_id == country_id,
                            RawEvent.event_date >= start_date,
                            RawEvent.event_date <= target_date
                        )
                    )
                )
                
                events = result.fetchall()
                
                if not events:
                    # Set zero values for periods with no events
                    features.update({
                        f"conflict_events_{period}d": 0,
                        f"protest_events_{period}d": 0,
                        f"diplomatic_events_{period}d": 0,
                        f"economic_events_{period}d": 0,
                        f"avg_sentiment_{period}d": 0.0,
                        f"sentiment_volatility_{period}d": 0.0,
                        f"event_trend_{period}d": 0.0,
                        f"severity_max_{period}d": 0.0
                    })
                    continue
                
                # Count events by category
                category_counts = {"conflict": 0, "protest": 0, "diplomatic": 0, "economic": 0}
                sentiments = []
                severities = []
                daily_counts = {}
                
                for processed_event, raw_event in events:
                    category = processed_event.risk_category
                    if category in category_counts:
                        category_counts[category] += 1
                    
                    if processed_event.sentiment_score is not None:
                        sentiments.append(float(processed_event.sentiment_score))
                    
                    if processed_event.severity_score is not None:
                        severities.append(float(processed_event.severity_score))
                    
                    # Count events by day for trend calculation
                    event_date = raw_event.event_date
                    daily_counts[event_date] = daily_counts.get(event_date, 0) + 1
                
                # Calculate features
                features.update({
                    f"conflict_events_{period}d": category_counts["conflict"],
                    f"protest_events_{period}d": category_counts["protest"],
                    f"diplomatic_events_{period}d": category_counts["diplomatic"],
                    f"economic_events_{period}d": category_counts["economic"],
                    f"avg_sentiment_{period}d": np.mean(sentiments) if sentiments else 0.0,
                    f"sentiment_volatility_{period}d": np.std(sentiments) if len(sentiments) > 1 else 0.0,
                    f"event_trend_{period}d": self._calculate_trend(daily_counts, start_date, target_date),
                    f"severity_max_{period}d": max(severities) if severities else 0.0
                })
                
            except Exception as e:
                logger.warning(f"Error generating event features for {period}d period: {str(e)}")
                # Set default values on error
                features.update({
                    f"conflict_events_{period}d": 0,
                    f"protest_events_{period}d": 0,
                    f"diplomatic_events_{period}d": 0,
                    f"economic_events_{period}d": 0,
                    f"avg_sentiment_{period}d": 0.0,
                    f"sentiment_volatility_{period}d": 0.0,
                    f"event_trend_{period}d": 0.0,
                    f"severity_max_{period}d": 0.0
                })
        
        return features
    
    async def _generate_economic_features(
        self,
        session: AsyncSession,
        country_id: int,
        target_date: date
    ) -> Dict[str, Any]:
        """Generate features from economic indicators"""
        features = {}
        
        for indicator_code, feature_name in self.economic_indicators.items():
            try:
                # Get latest value
                latest_result = await session.execute(
                    select(EconomicIndicator.year, EconomicIndicator.value)
                    .where(
                        and_(
                            EconomicIndicator.country_id == country_id,
                            EconomicIndicator.indicator_code == indicator_code
                        )
                    )
                    .order_by(EconomicIndicator.year.desc())
                    .limit(1)
                )
                latest = latest_result.fetchone()
                
                if latest:
                    latest_value = float(latest.value)
                    features[f"{feature_name}_latest"] = latest_value
                    
                    # Get historical values for trend and volatility
                    historical_result = await session.execute(
                        select(EconomicIndicator.year, EconomicIndicator.value)
                        .where(
                            and_(
                                EconomicIndicator.country_id == country_id,
                                EconomicIndicator.indicator_code == indicator_code,
                                EconomicIndicator.year >= latest.year - 3  # Last 3 years
                            )
                        )
                        .order_by(EconomicIndicator.year)
                    )
                    historical = historical_result.fetchall()
                    
                    if len(historical) >= 2:
                        values = [float(row.value) for row in historical]
                        years = [row.year for row in historical]
                        
                        # Year-over-year change
                        if len(historical) >= 2:
                            yoy_change = ((values[-1] - values[-2]) / abs(values[-2])) * 100 if values[-2] != 0 else 0
                            features[f"{feature_name}_yoy_change"] = yoy_change
                        else:
                            features[f"{feature_name}_yoy_change"] = 0.0
                        
                        # Volatility (standard deviation)
                        features[f"{feature_name}_volatility"] = np.std(values) if len(values) > 1 else 0.0
                        
                        # Trend (linear regression slope)
                        if len(values) >= 3:
                            features[f"{feature_name}_trend"] = self._calculate_linear_trend(years, values)
                        else:
                            features[f"{feature_name}_trend"] = 0.0
                    else:
                        # Set defaults if insufficient historical data
                        features[f"{feature_name}_yoy_change"] = 0.0
                        features[f"{feature_name}_volatility"] = 0.0
                        features[f"{feature_name}_trend"] = 0.0
                else:
                    # Set defaults if no data available
                    features[f"{feature_name}_latest"] = 0.0
                    features[f"{feature_name}_yoy_change"] = 0.0
                    features[f"{feature_name}_volatility"] = 0.0
                    features[f"{feature_name}_trend"] = 0.0
                    
            except Exception as e:
                logger.warning(f"Error generating economic features for {indicator_code}: {str(e)}")
                # Set default values on error
                features[f"{feature_name}_latest"] = 0.0
                features[f"{feature_name}_yoy_change"] = 0.0
                features[f"{feature_name}_volatility"] = 0.0
                features[f"{feature_name}_trend"] = 0.0
        
        return features
    
    async def _generate_network_features(
        self,
        session: AsyncSession,
        country_id: int,
        target_date: date
    ) -> Dict[str, Any]:
        """Generate network-based features (simplified for MVP)"""
        features = {}
        
        try:
            # Placeholder values as specified in technical spec
            features["trade_dependence"] = 0.5
            features["alliance_strength"] = 0.5
            
            # Regional instability: average risk score of neighboring countries
            # For MVP, we'll use a simplified approach based on region
            result = await session.execute(
                select(Country.region).where(Country.id == country_id)
            )
            country_region = result.scalar()
            
            if country_region:
                # Get average latest risk scores for countries in same region
                regional_scores = await session.execute(
                    select(func.avg(RiskScoreV2.overall_score))
                    .join(Country)
                    .where(
                        and_(
                            Country.region == country_region,
                            Country.id != country_id,  # Exclude current country
                            RiskScoreV2.score_date >= target_date - timedelta(days=30)  # Recent scores
                        )
                    )
                )
                avg_regional_risk = regional_scores.scalar()
                features["regional_instability"] = float(avg_regional_risk) if avg_regional_risk else 50.0
            else:
                features["regional_instability"] = 50.0  # Default value
                
        except Exception as e:
            logger.warning(f"Error generating network features: {str(e)}")
            features["trade_dependence"] = 0.5
            features["alliance_strength"] = 0.5
            features["regional_instability"] = 50.0
        
        return features
    
    def _calculate_trend(self, daily_counts: Dict[date, int], start_date: date, end_date: date) -> float:
        """Calculate linear trend of daily event counts"""
        try:
            if not daily_counts:
                return 0.0
            
            # Create complete date range with zero counts for missing days
            current_date = start_date
            dates = []
            counts = []
            
            while current_date <= end_date:
                dates.append((current_date - start_date).days)  # Days since start
                counts.append(daily_counts.get(current_date, 0))
                current_date += timedelta(days=1)
            
            if len(dates) < 2:
                return 0.0
            
            return self._calculate_linear_trend(dates, counts)
            
        except Exception as e:
            logger.warning(f"Error calculating trend: {str(e)}")
            return 0.0
    
    def _calculate_linear_trend(self, x_values: List, y_values: List) -> float:
        """Calculate linear regression slope"""
        try:
            if len(x_values) < 2 or len(y_values) < 2:
                return 0.0
            
            x_array = np.array(x_values).reshape(-1, 1)
            y_array = np.array(y_values)
            
            model = LinearRegression()
            model.fit(x_array, y_array)
            
            return float(model.coef_[0])
            
        except Exception as e:
            logger.warning(f"Error calculating linear trend: {str(e)}")
            return 0.0
    
    async def store_features(
        self,
        session: AsyncSession,
        country_id: int,
        target_date: date,
        features: Dict[str, Any]
    ) -> bool:
        """Store generated features in database"""
        try:
            # Check if features already exist for this date
            existing = await session.execute(
                select(FeatureVector.id).where(
                    and_(
                        FeatureVector.country_id == country_id,
                        FeatureVector.feature_date == target_date
                    )
                )
            )
            
            if existing.fetchone():
                # Update existing features
                await session.execute(
                    FeatureVector.__table__.update()
                    .where(
                        and_(
                            FeatureVector.country_id == country_id,
                            FeatureVector.feature_date == target_date
                        )
                    )
                    .values(features=features)
                )
            else:
                # Insert new features
                await session.execute(
                    insert(FeatureVector).values(
                        country_id=country_id,
                        feature_date=target_date,
                        features=features
                    )
                )
            
            await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing features for country {country_id}: {str(e)}")
            await session.rollback()
            return False
    
    async def generate_and_store_features_for_all_countries(
        self,
        session: AsyncSession,
        target_date: Optional[date] = None
    ) -> int:
        """Generate and store features for all countries"""
        if target_date is None:
            target_date = datetime.now().date()
        
        # Get all countries
        result = await session.execute(select(Country.id, Country.name))
        countries = result.fetchall()
        
        success_count = 0
        
        for country_id, country_name in countries:
            try:
                logger.info(f"Generating features for {country_name}")
                
                features = await self.generate_features_for_country(
                    session, country_id, target_date
                )
                
                if features:
                    stored = await self.store_features(
                        session, country_id, target_date, features
                    )
                    if stored:
                        success_count += 1
                        
            except Exception as e:
                logger.error(f"Failed to generate features for {country_name}: {str(e)}")
                continue
        
        logger.info(f"Generated features for {success_count}/{len(countries)} countries")
        return success_count