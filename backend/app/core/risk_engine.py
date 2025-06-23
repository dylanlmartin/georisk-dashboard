import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

@dataclass
class RiskScores:
    political: float
    economic: float
    security: float
    social: float
    overall: float
    confidence: float

class RiskEngine:
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Risk calculation weights
        self.weights = {
            'political': 0.35,
            'economic': 0.25,
            'security': 0.25,
            'social': 0.15
        }
        
        # Keywords for categorizing news
        self.keywords = {
            'political': ['election', 'government', 'policy', 'political', 'parliament', 'minister', 'president'],
            'security': ['conflict', 'terrorism', 'war', 'military', 'insurgency', 'bombing', 'civil war', 'armed conflict'],
            'social': ['protest', 'unrest', 'strike', 'demonstration', 'riot', 'civil']
        }
        
        # High-impact security keywords (more serious threats)
        self.high_security_keywords = ['terrorism', 'war', 'bombing', 'insurgency', 'civil war', 'armed conflict']
        
        # Local crime keywords to filter out (not geopolitical risks)
        self.local_crime_keywords = ['crypto', 'wallet', 'robbery', 'theft', 'burglary', 'mugging', 'scam']
        
        # Known high-risk countries that should have elevated baseline scores
        self.high_risk_adjustments = {
            'IR': {'political': +35, 'security': +40, 'reason': 'Regional conflicts, sanctions, nuclear tensions'},
            'AF': {'political': +40, 'security': +45, 'reason': 'Political instability, Taliban control'},
            'SY': {'political': +40, 'security': +50, 'reason': 'Ongoing civil war'},
            'YE': {'political': +35, 'security': +45, 'reason': 'Civil war, humanitarian crisis'},
            'LY': {'political': +30, 'security': +35, 'reason': 'Political fragmentation'},
            'MM': {'political': +35, 'security': +30, 'reason': 'Military coup, civil unrest'},
            'KP': {'political': +25, 'security': +30, 'reason': 'Authoritarian regime, nuclear program'},
            'RU': {'political': +25, 'security': +35, 'reason': 'War in Ukraine, authoritarianism'},
            'IQ': {'political': +20, 'security': +30, 'reason': 'Political instability, sectarian tensions'},
            'PK': {'political': +15, 'security': +25, 'reason': 'Political instability, terrorism threats'},
        }
        
        # Countries that should have baseline caps (stable democracies/developed nations)
        self.low_risk_caps = {
            # Nordic countries
            'NO': {'max_overall': 40, 'reason': 'Stable democracy, strong institutions'},
            'DK': {'max_overall': 40, 'reason': 'Stable democracy, strong institutions'},
            'SE': {'max_overall': 40, 'reason': 'Stable democracy, strong institutions'},
            'FI': {'max_overall': 40, 'reason': 'Stable democracy, strong institutions'},
            'IS': {'max_overall': 35, 'reason': 'Stable democracy'},
            
            # Western Europe stable democracies
            'CH': {'max_overall': 35, 'reason': 'Neutral, stable democracy'},
            'LU': {'max_overall': 35, 'reason': 'Stable EU member'},
            'AT': {'max_overall': 40, 'reason': 'Stable EU member'},
            'NL': {'max_overall': 40, 'reason': 'Stable EU member'},
            'BE': {'max_overall': 42, 'reason': 'Stable EU member'},
            'IE': {'max_overall': 40, 'reason': 'Stable EU member'},
            
            # Other developed nations
            'AU': {'max_overall': 40, 'reason': 'Stable democracy'},
            'NZ': {'max_overall': 35, 'reason': 'Stable democracy'},
            'CA': {'max_overall': 42, 'reason': 'Stable democracy'},
            'JP': {'max_overall': 45, 'reason': 'Stable democracy'},
            'KR': {'max_overall': 48, 'reason': 'Developed democracy, regional tensions'},
            
            # EU candidates/NATO members
            'ME': {'max_overall': 50, 'reason': 'NATO member, EU candidate'},
            'MT': {'max_overall': 42, 'reason': 'Stable EU member'},
        }
    
    def calculate_political_risk(self, news_articles: List[Dict[str, Any]]) -> float:
        """Calculate political risk based on news sentiment"""
        if not news_articles:
            return 50.0  # neutral baseline
            
        political_articles = self._filter_articles_by_keywords(news_articles, 'political')
        if not political_articles:
            return 50.0
            
        sentiments = []
        for article in political_articles:
            sentiment = self.sentiment_analyzer.polarity_scores(article['headline'])
            sentiments.append(sentiment['compound'])
        
        avg_sentiment = np.mean(sentiments)
        # Convert sentiment (-1 to 1) to risk score (0-100)
        # Negative sentiment = higher risk
        political_score = 50 + (avg_sentiment * -25)
        return max(0, min(100, political_score))
    
    def calculate_economic_risk(self, economic_data: Dict[str, Any]) -> float:
        """Calculate economic risk based on economic indicators"""
        risk_scores = []
        
        # GDP Growth Risk
        gdp_growth = economic_data.get('gdp_growth')
        if gdp_growth is not None:
            if gdp_growth < -5:
                gdp_risk = 80
            elif gdp_growth < 0:
                gdp_risk = 60
            elif gdp_growth < 2:
                gdp_risk = 40
            else:
                gdp_risk = 25
            risk_scores.append(gdp_risk)
        
        # Inflation Risk
        inflation = economic_data.get('inflation')
        if inflation is not None:
            if inflation > 20:
                inflation_risk = 85
            elif inflation > 10:
                inflation_risk = 65
            elif inflation > 5:
                inflation_risk = 45
            else:
                inflation_risk = 25
            risk_scores.append(inflation_risk)
        
        # Debt-to-GDP Risk
        debt_ratio = economic_data.get('debt_to_gdp')
        if debt_ratio is not None:
            if debt_ratio > 100:
                debt_risk = 80
            elif debt_ratio > 80:
                debt_risk = 60
            elif debt_ratio > 60:
                debt_risk = 40
            else:
                debt_risk = 25
            risk_scores.append(debt_risk)
        
        # Currency Volatility Risk
        currency_volatility = economic_data.get('currency_volatility')
        if currency_volatility is not None:
            if currency_volatility > 0.2:
                currency_risk = 85
            elif currency_volatility > 0.1:
                currency_risk = 65
            elif currency_volatility > 0.05:
                currency_risk = 45
            else:
                currency_risk = 25
            risk_scores.append(currency_risk)
        
        # Return average of available indicators, or neutral score if none available
        return np.mean(risk_scores) if risk_scores else 50.0
    
    def calculate_security_risk(self, news_articles: List[Dict[str, Any]]) -> float:
        """Calculate security risk based on geopolitical security threats (not local crime)"""
        if not news_articles:
            return 25.0  # low baseline for security
            
        # Filter for genuine security threats, excluding local crime
        security_articles = []
        for article in news_articles:
            headline = article.get('headline', '').lower()
            
            # Skip if it's clearly local crime
            if any(crime_word in headline for crime_word in self.local_crime_keywords):
                continue
                
            # Include if it contains security keywords
            if any(security_word in headline for security_word in self.keywords['security']):
                security_articles.append(article)
        
        if not security_articles:
            return 25.0
        
        # Weight articles by severity
        risk_points = 0
        total_weight = 0
        
        for article in security_articles:
            headline = article.get('headline', '').lower()
            
            # High-impact security incidents get more weight
            if any(high_word in headline for high_word in self.high_security_keywords):
                weight = 3.0  # Terrorism, war, etc.
            else:
                weight = 1.0  # General security issues
            
            sentiment = self.sentiment_analyzer.polarity_scores(article['headline'])
            # Convert sentiment (-1 to 1) to risk contribution (0 to weight*20)
            risk_contribution = weight * (10 + (sentiment['compound'] * -10))
            
            risk_points += risk_contribution
            total_weight += weight
        
        if total_weight > 0:
            # Average risk per article, scaled to reasonable range
            avg_risk = risk_points / total_weight
            # Scale based on frequency but cap the impact
            frequency_multiplier = min(2.0, len(security_articles) / len(news_articles) * 3)
            final_risk = avg_risk * frequency_multiplier
            return max(25, min(85, final_risk))
        
        return 25.0
    
    def calculate_social_risk(self, news_articles: List[Dict[str, Any]]) -> float:
        """Calculate social risk based on protest/unrest indicators"""
        if not news_articles:
            return 25.0  # low baseline for social risk
            
        social_articles = self._filter_articles_by_keywords(news_articles, 'social')
        if not social_articles:
            return 25.0
        
        # Similar to security risk calculation
        social_frequency = len(social_articles) / len(news_articles)
        base_risk = min(70, social_frequency * 150)
        
        sentiments = []
        for article in social_articles:
            sentiment = self.sentiment_analyzer.polarity_scores(article['headline'])
            sentiments.append(sentiment['compound'])
        
        if sentiments:
            avg_sentiment = np.mean(sentiments)
            sentiment_adjustment = avg_sentiment * -10
            return max(25, min(100, base_risk + sentiment_adjustment))
        
        return base_risk
    
    def calculate_confidence_level(self, news_articles: List[Dict[str, Any]], 
                                 economic_data: Dict[str, Any]) -> float:
        """Calculate confidence level based on data quality and freshness"""
        confidence_factors = []
        
        # News data quality (0-40 points)
        if news_articles:
            news_sources = set(article.get('source', '') for article in news_articles)
            source_diversity = min(40, len(news_sources) * 8)  # Up to 5 sources = 40 points
            confidence_factors.append(source_diversity)
        else:
            confidence_factors.append(0)
        
        # Economic data completeness (0-30 points)
        economic_completeness = 0
        required_indicators = ['gdp_growth', 'inflation', 'debt_to_gdp', 'currency_volatility']
        for indicator in required_indicators:
            if indicator in economic_data and economic_data[indicator] is not None:
                economic_completeness += 7.5
        confidence_factors.append(economic_completeness)
        
        # Data freshness (0-30 points) - assume recent data for now
        freshness_score = 25  # Default assumption of reasonably fresh data
        confidence_factors.append(freshness_score)
        
        return min(100, sum(confidence_factors))
    
    def calculate_overall_risk(self, political: float, economic: float, 
                             security: float, social: float) -> float:
        """Calculate weighted overall risk score"""
        overall = (
            political * self.weights['political'] +
            economic * self.weights['economic'] +
            security * self.weights['security'] +
            social * self.weights['social']
        )
        return max(0, min(100, overall))
    
    def calculate_risk_scores(self, news_articles: List[Dict[str, Any]], 
                            economic_data: Dict[str, Any], country_code: str = None) -> RiskScores:
        """Main method to calculate all risk scores"""
        political = self.calculate_political_risk(news_articles)
        economic = self.calculate_economic_risk(economic_data)
        security = self.calculate_security_risk(news_articles)
        social = self.calculate_social_risk(news_articles)
        
        # Apply country-specific risk adjustments for known high-risk situations
        if country_code and country_code in self.high_risk_adjustments:
            adjustments = self.high_risk_adjustments[country_code]
            political = min(100, political + adjustments.get('political', 0))
            security = min(100, security + adjustments.get('security', 0))
            
        overall = self.calculate_overall_risk(political, economic, security, social)
        
        # Apply caps for stable democracies/developed nations
        if country_code and country_code in self.low_risk_caps:
            cap_info = self.low_risk_caps[country_code]
            overall = min(overall, cap_info['max_overall'])
        
        confidence = self.calculate_confidence_level(news_articles, economic_data)
        
        return RiskScores(
            political=political,
            economic=economic,
            security=security,
            social=social,
            overall=overall,
            confidence=confidence
        )
    
    def _filter_articles_by_keywords(self, articles: List[Dict[str, Any]], 
                                   category: str) -> List[Dict[str, Any]]:
        """Filter articles by category keywords"""
        if category not in self.keywords:
            return []
        
        filtered = []
        keywords = self.keywords[category]
        
        for article in articles:
            headline = article.get('headline', '').lower()
            if any(keyword in headline for keyword in keywords):
                filtered.append(article)
        
        return filtered