import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from app.models.country import Country
from app.models.raw_event import RawEvent
from app.models.processed_event import ProcessedEvent

class AIAnalysisService:
    """AI-powered country risk analysis using OpenAI API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"  # Fast and cost-effective
        
    async def generate_country_analysis(
        self, 
        country: Country, 
        latest_score: Any, 
        recent_events: List[ProcessedEvent], 
        historical_scores: List[Any],
        economic_indicators: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered analysis for a country"""
        
        if not self.api_key:
            return self._fallback_analysis(country, latest_score, recent_events, historical_scores)
        
        # Prepare context data
        context = self._prepare_analysis_context(country, latest_score, recent_events, historical_scores, economic_indicators)
        
        # Generate AI content
        try:
            analysis_content = await self._generate_ai_content(context)
            return self._structure_analysis_response(analysis_content, latest_score, historical_scores)
        except Exception as e:
            print(f"AI analysis failed for {country.name}: {e}")
            return self._fallback_analysis(country, latest_score, recent_events, historical_scores)
    
    def _prepare_analysis_context(
        self, 
        country: Country, 
        latest_score: Any, 
        recent_events: List[ProcessedEvent], 
        historical_scores: List[Any],
        economic_indicators: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Prepare rich context for AI analysis with specific data driving risk scores"""
        
        # Extract current scores with confidence intervals if available
        if latest_score:
            if hasattr(latest_score, 'political_stability_score'):
                scores = {
                    "overall": float(latest_score.overall_score),
                    "political": float(latest_score.political_stability_score),
                    "economic": float(latest_score.economic_risk_score),
                    "security": float(latest_score.conflict_risk_score),
                    "social": float(latest_score.institutional_quality_score),
                    "confidence_lower": float(getattr(latest_score, 'confidence_lower', 0)),
                    "confidence_upper": float(getattr(latest_score, 'confidence_upper', 0)),
                    "score_date": getattr(latest_score, 'score_date', datetime.now()).strftime("%Y-%m-%d")
                }
            else:
                scores = {
                    "overall": float(latest_score.overall_score),
                    "political": float(latest_score.political_score),
                    "economic": float(latest_score.economic_score),
                    "security": float(latest_score.security_score),
                    "social": float(latest_score.social_score),
                    "confidence_level": float(getattr(latest_score, 'confidence_level', 80)),
                    "score_date": getattr(latest_score, 'timestamp', datetime.now()).strftime("%Y-%m-%d")
                }
        else:
            scores = {"overall": 50, "political": 50, "economic": 50, "security": 50, "social": 50, "score_date": datetime.now().strftime("%Y-%m-%d")}
        
        # Calculate detailed trends with component-level changes
        trend_data = self._calculate_detailed_trends(historical_scores)
        
        # Analyze recent events with specific details
        event_analysis = self._analyze_recent_events_detailed(recent_events)
        
        # Get economic and governance indicators
        economic_context = self._get_economic_context(country, economic_indicators)
        
        return {
            "country": {
                "name": country.name,
                "region": country.region,
                "population": country.population,
                "population_size": "large" if country.population > 100000000 else "medium" if country.population > 10000000 else "small"
            },
            "risk_scores": scores,
            "trends": trend_data,
            "recent_events": event_analysis,
            "economic_context": economic_context,
            "analysis_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def _calculate_detailed_trends(self, historical_scores: List[Any]) -> Dict[str, Any]:
        """Calculate detailed trends with component-level analysis"""
        if len(historical_scores) < 2:
            return {"summary": "Insufficient historical data for trend analysis", "component_changes": {}}
        
        oldest = historical_scores[0]
        newest = historical_scores[-1]
        
        # Calculate overall change
        overall_change = float(newest.overall_score) - float(oldest.overall_score)
        
        # Calculate component changes
        component_changes = {}
        if hasattr(newest, 'political_stability_score'):
            component_changes = {
                "political": float(newest.political_stability_score) - float(oldest.political_stability_score),
                "economic": float(newest.economic_risk_score) - float(oldest.economic_risk_score),
                "security": float(newest.conflict_risk_score) - float(oldest.conflict_risk_score),
                "social": float(newest.institutional_quality_score) - float(oldest.institutional_quality_score)
            }
        else:
            component_changes = {
                "political": float(newest.political_score) - float(oldest.political_score),
                "economic": float(newest.economic_score) - float(oldest.economic_score),
                "security": float(newest.security_score) - float(oldest.security_score),
                "social": float(newest.social_score) - float(oldest.social_score)
            }
        
        # Identify biggest drivers of change
        biggest_driver = max(component_changes.items(), key=lambda x: abs(x[1]))
        
        return {
            "overall_change": round(overall_change, 2),
            "direction": "improving" if overall_change < -2 else "deteriorating" if overall_change > 2 else "stable",
            "component_changes": {k: round(v, 2) for k, v in component_changes.items()},
            "biggest_driver": {"component": biggest_driver[0], "change": round(biggest_driver[1], 2)},
            "time_period": f"{len(historical_scores)} data points over 30 days"
        }
    
    def _analyze_recent_events_detailed(self, recent_events: List[ProcessedEvent]) -> Dict[str, Any]:
        """Analyze recent events with specific details and impact assessment"""
        if not recent_events:
            return {"summary": "No recent events data available", "specific_events": [], "impact_analysis": {}}
        
        # Categorize and analyze events
        categories = {}
        high_impact_events = []
        sentiment_scores = []
        severity_scores = []
        
        for event in recent_events:
            # Get event details
            category = getattr(event, 'risk_category', 'general')
            categories[category] = categories.get(category, 0) + 1
            
            # Collect quantitative scores
            if hasattr(event, 'sentiment_score') and event.sentiment_score is not None:
                sentiment_scores.append(float(event.sentiment_score))
            
            if hasattr(event, 'severity_score') and event.severity_score is not None:
                severity_scores.append(float(event.severity_score))
            
            # Get specific event details for high-impact events
            if hasattr(event, 'severity_score') and event.severity_score and float(event.severity_score) > 0.6:
                event_detail = {
                    "category": category,
                    "severity": round(float(event.severity_score), 2),
                    "sentiment": round(float(event.sentiment_score), 2) if hasattr(event, 'sentiment_score') and event.sentiment_score else 0,
                    "confidence": round(float(event.confidence), 2) if hasattr(event, 'confidence') and event.confidence else 0
                }
                
                # Add event title if available
                if hasattr(event, 'raw_event') and event.raw_event and hasattr(event.raw_event, 'title'):
                    event_detail["title"] = event.raw_event.title[:120]
                    event_detail["date"] = getattr(event.raw_event, 'event_date', datetime.now()).strftime("%Y-%m-%d")
                
                high_impact_events.append(event_detail)
        
        # Calculate impact metrics
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        avg_severity = sum(severity_scores) / len(severity_scores) if severity_scores else 0
        
        return {
            "summary": f"{len(recent_events)} events analyzed, {len(high_impact_events)} high-impact",
            "category_breakdown": categories,
            "specific_events": high_impact_events[:8],  # Top 8 high-impact events
            "impact_analysis": {
                "average_sentiment": round(avg_sentiment, 3),
                "average_severity": round(avg_severity, 3),
                "sentiment_trend": "negative" if avg_sentiment < -0.2 else "positive" if avg_sentiment > 0.2 else "neutral",
                "severity_level": "high" if avg_severity > 0.7 else "medium" if avg_severity > 0.4 else "low"
            }
        }
    
    def _get_economic_context(self, country: Country, economic_indicators: Optional[Dict] = None) -> Dict[str, Any]:
        """Get economic and governance context that drives risk scores"""
        # This would typically pull from World Bank API or economic indicators table
        # For now, provide framework for economic context
        
        context = {
            "population_context": self._get_population_context(country.population),
            "regional_context": self._get_regional_economic_context(country.region),
            "governance_indicators": economic_indicators or {}
        }
        
        return context
    
    def _get_population_context(self, population: int) -> Dict[str, Any]:
        """Analyze population-related risk factors"""
        if population > 300000000:
            return {"size": "very large", "economic_scale": "major global economy", "complexity": "high governance complexity"}
        elif population > 100000000:
            return {"size": "large", "economic_scale": "significant regional economy", "complexity": "substantial governance challenges"}
        elif population > 50000000:
            return {"size": "medium-large", "economic_scale": "medium regional influence", "complexity": "moderate governance complexity"}
        elif population > 10000000:
            return {"size": "medium", "economic_scale": "limited regional influence", "complexity": "manageable governance scale"}
        else:
            return {"size": "small", "economic_scale": "limited economic influence", "complexity": "simplified governance structure"}
    
    def _get_regional_economic_context(self, region: str) -> Dict[str, Any]:
        """Get region-specific economic and political context"""
        regional_contexts = {
            "North America": {
                "economic_integration": "high (NAFTA/USMCA)",
                "institutional_strength": "strong democratic institutions",
                "key_challenges": "political polarization, trade tensions"
            },
            "Europe": {
                "economic_integration": "very high (EU integration)",
                "institutional_strength": "strong multilateral institutions",
                "key_challenges": "energy security, demographic transition"
            },
            "Asia": {
                "economic_integration": "growing (ASEAN, RCEP)",
                "institutional_strength": "mixed governance models",
                "key_challenges": "territorial disputes, development gaps"
            },
            "Middle East": {
                "economic_integration": "limited",
                "institutional_strength": "varied, often weak",
                "key_challenges": "sectarian conflicts, resource dependence"
            },
            "Africa": {
                "economic_integration": "developing (AfCFTA)",
                "institutional_strength": "building capacity",
                "key_challenges": "infrastructure gaps, governance challenges"
            },
            "South America": {
                "economic_integration": "moderate (Mercosur)",
                "institutional_strength": "democratic but fragile",
                "key_challenges": "economic volatility, political instability"
            }
        }
        
        return regional_contexts.get(region, {
            "economic_integration": "limited data",
            "institutional_strength": "varied",
            "key_challenges": "region-specific factors"
        })

    def _analyze_recent_events(self, recent_events: List[ProcessedEvent]) -> Dict[str, Any]:
        """Analyze recent events for AI context"""
        if not recent_events:
            return {"summary": "Limited recent event data available", "categories": {}, "notable_events": []}
        
        categories = {}
        high_impact_events = []
        sentiment_scores = []
        
        for event in recent_events:
            # Categorize events
            category = getattr(event, 'risk_category', 'general')
            categories[category] = categories.get(category, 0) + 1
            
            # Collect sentiment data
            if hasattr(event, 'sentiment_score') and event.sentiment_score is not None:
                sentiment_scores.append(float(event.sentiment_score))
            
            # Identify high-impact events
            if hasattr(event, 'severity_score') and event.severity_score and float(event.severity_score) > 0.7:
                if hasattr(event, 'raw_event') and event.raw_event and hasattr(event.raw_event, 'title'):
                    high_impact_events.append(event.raw_event.title[:100])
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        return {
            "summary": f"{len(recent_events)} events analyzed over past 30 days",
            "categories": categories,
            "notable_events": high_impact_events[:5],  # Top 5 high-impact events
            "average_sentiment": round(avg_sentiment, 2),
            "sentiment_trend": "negative" if avg_sentiment < -0.2 else "positive" if avg_sentiment > 0.2 else "neutral"
        }
    
    async def _generate_ai_content(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI content using OpenAI API"""
        
        prompt = self._build_analysis_prompt(context)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a geopolitical risk analyst providing concise, factual analysis based on quantitative risk data. Focus on specific current conditions and avoid generic statements."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 800,
            "temperature": 0.3,  # Lower temperature for more factual output
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"OpenAI API error: {response.status}")
                
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)
    
    def _build_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build detailed prompt for AI analysis with specific data points"""
        
        country = context["country"]
        scores = context["risk_scores"]
        trends = context["trends"]
        events = context["recent_events"]
        economic = context["economic_context"]
        
        # Build detailed trend information
        trend_detail = ""
        if trends.get("component_changes"):
            component_changes = trends["component_changes"]
            biggest_driver = trends.get("biggest_driver", {})
            trend_detail = f"""
TREND ANALYSIS ({trends.get('time_period', '30 days')}):
- Overall risk {trends.get('direction', 'stable')}: {trends.get('overall_change', 0):+.1f} points
- Component changes: Political {component_changes.get('political', 0):+.1f}, Economic {component_changes.get('economic', 0):+.1f}, Security {component_changes.get('security', 0):+.1f}, Social {component_changes.get('social', 0):+.1f}
- Biggest driver of change: {biggest_driver.get('component', 'none')} sector ({biggest_driver.get('change', 0):+.1f} points)"""
        
        # Build specific events information
        events_detail = ""
        if events.get("specific_events"):
            events_detail = "\nSPECIFIC HIGH-IMPACT EVENTS:\n"
            for i, event in enumerate(events["specific_events"][:5], 1):
                events_detail += f"- Event {i}: {event.get('category', 'general')} (severity: {event.get('severity', 0):.2f}, sentiment: {event.get('sentiment', 0):+.2f})\n"
                if event.get("title"):
                    events_detail += f"  \"{event['title']}\" ({event.get('date', 'recent')})\n"
        
        # Build economic context
        pop_context = economic.get("population_context", {})
        regional_context = economic.get("regional_context", {})
        
        prompt = f"""Analyze the geopolitical risk profile for {country['name']} based on quantitative data and specific events:

CURRENT RISK SCORES (0-100 scale, higher = more risk):
- Overall Risk: {scores['overall']:.1f} (assessed {scores.get('score_date', 'recently')})
- Political Risk: {scores['political']:.1f}
- Economic Risk: {scores['economic']:.1f}
- Security Risk: {scores['security']:.1f}
- Social/Institutional Risk: {scores['social']:.1f}
{f"- Confidence Range: {scores.get('confidence_lower', 0):.1f} - {scores.get('confidence_upper', 0):.1f}" if scores.get('confidence_lower') else f"- Confidence Level: {scores.get('confidence_level', 80):.1f}%"}

{trend_detail if trend_detail else "TREND ANALYSIS: Limited historical data available"}

RECENT EVENTS DATA:
- {events.get('summary', 'No recent events data')}
- Event categories: {', '.join([f"{k}: {v}" for k, v in events.get('category_breakdown', {}).items()]) if events.get('category_breakdown') else "No events categorized"}
- Impact metrics: Avg sentiment {events.get('impact_analysis', {}).get('average_sentiment', 0):+.3f}, Avg severity {events.get('impact_analysis', {}).get('average_severity', 0):.3f}
- Overall impact level: {events.get('impact_analysis', {}).get('severity_level', 'low')}
{events_detail}

COUNTRY STRUCTURAL FACTORS:
- Population: {country['population']:,} ({pop_context.get('size', 'medium')} country)
- Economic scale: {pop_context.get('economic_scale', 'regional economy')}
- Governance complexity: {pop_context.get('complexity', 'moderate')}
- Regional integration: {regional_context.get('economic_integration', 'moderate')}
- Institutional strength: {regional_context.get('institutional_strength', 'mixed')}
- Key regional challenges: {regional_context.get('key_challenges', 'various factors')}

Provide a JSON response with exactly these fields:
{{
  "summary": "2-3 sentences referencing specific risk scores, trends, and quantitative data points",
  "key_drivers": ["3-4 factors citing specific scores, events, or data that drive current risk levels"],
  "risk_factors": ["3-4 specific risks mentioning actual data points, events, or quantitative indicators"],
  "stability_factors": ["3-4 strengths citing specific low scores, positive trends, or structural advantages"],
  "outlook": "1-2 sentences based on trend direction, event patterns, and quantitative indicators"
}}

CRITICAL: Reference specific numbers, scores, trends, and events from the data provided. Mention actual risk score values, trend magnitudes, event categories, and quantitative metrics. Avoid generic statements."""
        
        return prompt
    
    def _structure_analysis_response(
        self, 
        ai_content: Dict[str, str], 
        latest_score: Any, 
        historical_scores: List[Any]
    ) -> Dict[str, Any]:
        """Structure the AI response with metadata"""
        
        # Calculate trend metadata
        trend_direction = "stable"
        trend_magnitude = 0
        if len(historical_scores) >= 2:
            oldest_score = float(historical_scores[0].overall_score)
            newest_score = float(historical_scores[-1].overall_score)
            trend_magnitude = newest_score - oldest_score
            if trend_magnitude > 3:
                trend_direction = "increasing"
            elif trend_magnitude < -3:
                trend_direction = "decreasing"
        
        # Determine risk level
        overall_score = float(latest_score.overall_score) if latest_score else 50.0
        risk_level = (
            "very high" if overall_score >= 80 else 
            "high" if overall_score >= 65 else 
            "medium-high" if overall_score >= 50 else 
            "medium" if overall_score >= 35 else 
            "low-medium" if overall_score >= 20 else "low"
        )
        
        return {
            "summary": ai_content.get("summary", "Analysis unavailable"),
            "key_drivers": ai_content.get("key_drivers", ["Data analysis in progress"]),
            "risk_factors": ai_content.get("risk_factors", ["Assessment pending"]),
            "stability_factors": ai_content.get("stability_factors", ["Evaluation ongoing"]),
            "outlook": ai_content.get("outlook", "Continued monitoring required"),
            "risk_level": risk_level,
            "trend_direction": trend_direction,
            "trend_magnitude": round(trend_magnitude, 1),
            "ai_generated": True,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _fallback_analysis(
        self, 
        country: Country, 
        latest_score: Any, 
        recent_events: List[ProcessedEvent], 
        historical_scores: List[Any]
    ) -> Dict[str, Any]:
        """Enhanced fallback analysis with specific data when AI is unavailable"""
        
        # Extract scores
        if latest_score:
            if hasattr(latest_score, 'political_stability_score'):
                scores = {
                    "overall": float(latest_score.overall_score),
                    "political": float(latest_score.political_stability_score),
                    "economic": float(latest_score.economic_risk_score),
                    "security": float(latest_score.conflict_risk_score),
                    "social": float(latest_score.institutional_quality_score)
                }
            else:
                scores = {
                    "overall": float(latest_score.overall_score),
                    "political": float(latest_score.political_score),
                    "economic": float(latest_score.economic_score),
                    "security": float(latest_score.security_score),
                    "social": float(latest_score.social_score)
                }
        else:
            scores = {"overall": 50, "political": 50, "economic": 50, "security": 50, "social": 50}
        
        risk_level = (
            "very high" if scores["overall"] >= 80 else 
            "high" if scores["overall"] >= 65 else 
            "medium-high" if scores["overall"] >= 50 else 
            "medium" if scores["overall"] >= 35 else 
            "low-medium" if scores["overall"] >= 20 else "low"
        )
        
        # Calculate trends
        trend_data = self._calculate_detailed_trends(historical_scores)
        
        # Analyze events
        events_data = self._analyze_recent_events_detailed(recent_events)
        
        # Generate data-driven content
        highest_risk = max(scores.items(), key=lambda x: x[1] if x[0] != 'overall' else 0)
        lowest_risk = min(scores.items(), key=lambda x: x[1] if x[0] != 'overall' else 100)
        
        summary = (f"{country.name} presents {risk_level} risk levels with an overall score of {scores['overall']:.1f}. "
                  f"Highest risk area: {highest_risk[0]} ({highest_risk[1]:.1f}), "
                  f"strongest area: {lowest_risk[0]} ({lowest_risk[1]:.1f}). ")
        
        if trend_data.get("overall_change", 0) != 0:
            summary += f"Risk levels have {trend_data['direction']} by {abs(trend_data['overall_change']):.1f} points recently."
        
        # Generate specific factors based on actual data
        key_drivers = []
        if scores["political"] > 55:
            key_drivers.append(f"Political risk elevated at {scores['political']:.1f} points")
        if scores["economic"] > 55:
            key_drivers.append(f"Economic risk concerns at {scores['economic']:.1f} points")
        if scores["security"] > 55:
            key_drivers.append(f"Security challenges scoring {scores['security']:.1f} points")
        if scores["social"] > 55:
            key_drivers.append(f"Social/institutional risk at {scores['social']:.1f} points")
        
        if not key_drivers:
            key_drivers = [f"Risk levels moderate across all sectors (highest: {highest_risk[0]} at {highest_risk[1]:.1f})"]
        
        # Add trend driver if significant
        if trend_data.get("biggest_driver", {}).get("change", 0) != 0:
            driver = trend_data["biggest_driver"]
            key_drivers.append(f"{driver['component'].title()} sector trending {'+' if driver['change'] > 0 else ''}{driver['change']:.1f} points")
        
        risk_factors = []
        high_risk_areas = [k for k, v in scores.items() if k != 'overall' and v > 50]
        for area in high_risk_areas:
            risk_factors.append(f"{area.title()} sector vulnerabilities (score: {scores[area]:.1f})")
        
        if events_data.get("impact_analysis", {}).get("severity_level") == "high":
            risk_factors.append(f"Recent high-impact events detected (avg severity: {events_data['impact_analysis']['average_severity']:.2f})")
        
        if not risk_factors:
            risk_factors = ["Risk levels within manageable ranges across key sectors"]
        
        stability_factors = []
        low_risk_areas = [k for k, v in scores.items() if k != 'overall' and v < 45]
        for area in low_risk_areas:
            stability_factors.append(f"Strong {area} indicators (score: {scores[area]:.1f})")
        
        # Add population/regional factors
        if country.population > 100000000:
            stability_factors.append(f"Large population base ({country.population:,}) providing economic scale")
        
        stability_factors.append(f"{country.region} regional institutional framework")
        
        outlook = f"Current {risk_level} risk environment suggests "
        if trend_data.get("direction") == "improving":
            outlook += f"positive trajectory with {abs(trend_data['overall_change']):.1f}-point improvement."
        elif trend_data.get("direction") == "deteriorating":
            outlook += f"increasing vigilance needed with {trend_data['overall_change']:.1f}-point rise."
        else:
            outlook += "stable conditions requiring continued monitoring."
        
        return {
            "summary": summary,
            "key_drivers": key_drivers[:4],
            "risk_factors": risk_factors[:4],
            "stability_factors": stability_factors[:4],
            "outlook": outlook,
            "risk_level": risk_level,
            "trend_direction": trend_data.get("direction", "stable"),
            "trend_magnitude": round(trend_data.get("overall_change", 0), 1),
            "ai_generated": False,
            "data_driven": True,
            "generated_at": datetime.utcnow().isoformat()
        }