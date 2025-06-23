import aiohttp
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    headline: str
    source: str
    published_at: datetime
    url: str
    content: Optional[str] = None

@dataclass
class EconomicData:
    country_code: str
    gdp_growth: Optional[float] = None
    inflation: Optional[float] = None
    unemployment: Optional[float] = None
    debt_to_gdp: Optional[float] = None
    currency_volatility: Optional[float] = None

class DataCollector:
    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY")
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API endpoints
        self.news_api_url = "https://newsapi.org/v2/everything"
        self.world_bank_url = "https://api.worldbank.org/v2/country"
        self.alpha_vantage_url = "https://www.alphavantage.co/query"
        
        # Rate limiting
        self.news_api_calls = 0
        self.alpha_vantage_calls = 0
        self.last_reset = datetime.now()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def collect_news_data(self, country_name: str, 
                              country_code: str) -> List[NewsArticle]:
        """Collect news articles for a specific country"""
        if not self.news_api_key:
            logger.warning("NewsAPI key not configured")
            return []
        
        if not await self._check_news_api_rate_limit():
            logger.warning("NewsAPI rate limit exceeded")
            return []
        
        try:
            # Search for news mentioning the country (avoid short country codes that might match common words)
            if len(country_code) <= 2:
                # For short codes like "FR", only search by country name to avoid false matches
                search_query = f'"{country_name}"'
                
                # Add alternative names for countries that might be referenced differently
                if country_name.lower() == "iran":
                    search_query = f'"{country_name}" OR "Iranian" OR "Tehran"'
                elif country_name.lower() == "russia":
                    search_query = f'"{country_name}" OR "Russian" OR "Moscow" OR "Kremlin"'
                elif country_name.lower() == "china":
                    search_query = f'"{country_name}" OR "Chinese" OR "Beijing"'
                elif country_name.lower() == "united states":
                    search_query = f'"United States" OR "America" OR "U.S." OR "USA"'
            else:
                # For longer codes, can include both
                search_query = f'"{country_name}" OR "{country_code}"'
            
            params = {
                'q': search_query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 20,
                'from': (datetime.now() - timedelta(days=7)).isoformat(),
                'apiKey': self.news_api_key
            }
            
            async with self.session.get(self.news_api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = []
                    
                    for article in data.get('articles', []):
                        if article.get('title') and article.get('publishedAt'):
                            # Filter out articles that don't seem relevant to the country
                            title = article['title'].lower()
                            description = article.get('description', '').lower()
                            full_text = title + ' ' + description
                            
                            # Skip if country name is not prominently mentioned
                            if country_name.lower() not in full_text:
                                continue
                                
                            # Skip obvious false positives
                            if any(skip_word in title for skip_word in ['astronomy', 'picture of the day', 'recipe', 'weather']):
                                continue
                            
                            published_at = datetime.fromisoformat(
                                article['publishedAt'].replace('Z', '+00:00')
                            )
                            
                            articles.append(NewsArticle(
                                headline=article['title'],
                                source=article.get('source', {}).get('name', 'Unknown'),
                                published_at=published_at,
                                url=article.get('url', ''),
                                content=article.get('description', '')
                            ))
                    
                    self.news_api_calls += 1
                    logger.info(f"Collected {len(articles)} news articles for {country_name}")
                    return articles
                else:
                    logger.error(f"NewsAPI error: {response.status} - {await response.text()}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error collecting news data for {country_name}: {e}")
            return []
    
    async def collect_economic_data(self, country_code: str) -> EconomicData:
        """Collect economic indicators from World Bank API"""
        economic_data = EconomicData(country_code=country_code)
        
        try:
            # World Bank indicators mapping
            indicators = {
                'gdp_growth': 'NY.GDP.MKTP.KD.ZG',  # GDP growth (annual %)
                'inflation': 'FP.CPI.TOTL.ZG',      # Inflation, consumer prices (annual %)
                'unemployment': 'SL.UEM.TOTL.ZS',   # Unemployment, total (% of total labor force)
                'debt_to_gdp': 'GC.DOD.TOTL.GD.ZS'  # Central government debt, total (% of GDP)
            }
            
            for indicator_name, indicator_code in indicators.items():
                url = f"{self.world_bank_url}/{country_code}/indicator/{indicator_code}"
                params = {
                    'format': 'json',
                    'date': f"{datetime.now().year-2}:{datetime.now().year}",  # Last 3 years
                    'per_page': 3
                }
                
                try:
                    async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if len(data) > 1 and data[1]:  # World Bank returns metadata in first element
                                # Get the most recent non-null value
                                for entry in data[1]:
                                    if entry.get('value') is not None:
                                        setattr(economic_data, indicator_name, float(entry['value']))
                                        break
                        
                        # Small delay to be respectful to the API
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    logger.error(f"Error fetching {indicator_name} for {country_code}: {e}")
                    continue
            
            # Get currency volatility from Alpha Vantage (if available)
            if self.alpha_vantage_key and await self._check_alpha_vantage_rate_limit():
                currency_volatility = await self._get_currency_volatility(country_code)
                if currency_volatility is not None:
                    economic_data.currency_volatility = currency_volatility
            
            logger.info(f"Collected economic data for {country_code}")
            return economic_data
            
        except Exception as e:
            logger.error(f"Error collecting economic data for {country_code}: {e}")
            return economic_data
    
    async def _get_currency_volatility(self, country_code: str) -> Optional[float]:
        """Calculate currency volatility using Alpha Vantage API"""
        try:
            # Map country codes to currency pairs (simplified)
            currency_map = {
                'US': 'USD',
                'GB': 'GBP',
                'EU': 'EUR',
                'JP': 'JPY',
                'CA': 'CAD',
                'AU': 'AUD',
                'CH': 'CHF',
                'SE': 'SEK',
                'NO': 'NOK',
                'DK': 'DKK'
            }
            
            currency = currency_map.get(country_code)
            if not currency or currency == 'USD':
                return None  # Skip if no mapping or USD (base currency)
            
            params = {
                'function': 'FX_DAILY',
                'from_symbol': currency,
                'to_symbol': 'USD',
                'apikey': self.alpha_vantage_key,
                'outputsize': 'compact'  # Last 100 days
            }
            
            async with self.session.get(self.alpha_vantage_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    time_series = data.get('Time Series (FX Daily)', {})
                    
                    if time_series:
                        # Calculate volatility from daily closes
                        closes = []
                        for date_str in sorted(time_series.keys(), reverse=True)[:30]:  # Last 30 days
                            close_price = float(time_series[date_str]['4. close'])
                            closes.append(close_price)
                        
                        if len(closes) > 1:
                            # Calculate daily returns
                            returns = []
                            for i in range(1, len(closes)):
                                daily_return = (closes[i] - closes[i-1]) / closes[i-1]
                                returns.append(daily_return)
                            
                            # Standard deviation of returns as volatility measure
                            import numpy as np
                            volatility = np.std(returns) if returns else 0.0
                            self.alpha_vantage_calls += 1
                            return volatility
                        
        except Exception as e:
            logger.error(f"Error calculating currency volatility for {country_code}: {e}")
        
        return None
    
    async def _check_news_api_rate_limit(self) -> bool:
        """Check if we can make NewsAPI calls (1000/day limit)"""
        self._reset_daily_counters()
        return self.news_api_calls < 950  # Leave some buffer
    
    async def _check_alpha_vantage_rate_limit(self) -> bool:
        """Check if we can make Alpha Vantage calls (25/day limit)"""
        self._reset_daily_counters()
        return self.alpha_vantage_calls < 20  # Leave some buffer
    
    def _reset_daily_counters(self):
        """Reset API call counters if it's a new day"""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.news_api_calls = 0
            self.alpha_vantage_calls = 0
            self.last_reset = now
    
    async def collect_country_data(self, country_name: str, 
                                 country_code: str) -> Dict[str, Any]:
        """Collect all data for a country (news + economic)"""
        async with self:
            news_articles = await self.collect_news_data(country_name, country_code)
            economic_data = await self.collect_economic_data(country_code)
            
            # Convert to format expected by risk engine
            news_data = [
                {
                    'headline': article.headline,
                    'source': article.source,
                    'published_at': article.published_at,
                    'url': article.url
                }
                for article in news_articles
            ]
            
            economic_dict = {
                'gdp_growth': economic_data.gdp_growth,
                'inflation': economic_data.inflation,
                'unemployment': economic_data.unemployment,
                'debt_to_gdp': economic_data.debt_to_gdp,
                'currency_volatility': economic_data.currency_volatility
            }
            
            return {
                'news_articles': news_data,
                'economic_data': economic_dict
            }