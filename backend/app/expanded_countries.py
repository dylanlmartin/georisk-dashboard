"""
Expanded country list for global geopolitical risk assessment.
This includes all countries with available data from World Bank API, 
filtered to exclude regional aggregates and focus on actual nations.
"""

# Comprehensive list of countries with ISO codes, regions, and population data
EXPANDED_COUNTRIES = [
    # North America
    {"code": "US", "name": "United States", "region": "North America", "population": 331900000},
    {"code": "CA", "name": "Canada", "region": "North America", "population": 38000000},
    {"code": "MX", "name": "Mexico", "region": "North America", "population": 128900000},
    
    # Europe
    {"code": "GB", "name": "United Kingdom", "region": "Europe", "population": 67800000},
    {"code": "DE", "name": "Germany", "region": "Europe", "population": 83200000},
    {"code": "FR", "name": "France", "region": "Europe", "population": 65300000},
    {"code": "IT", "name": "Italy", "region": "Europe", "population": 60400000},
    {"code": "ES", "name": "Spain", "region": "Europe", "population": 46800000},
    {"code": "PL", "name": "Poland", "region": "Europe", "population": 38000000},
    {"code": "RO", "name": "Romania", "region": "Europe", "population": 19300000},
    {"code": "NL", "name": "Netherlands", "region": "Europe", "population": 17400000},
    {"code": "BE", "name": "Belgium", "region": "Europe", "population": 11500000},
    {"code": "CZ", "name": "Czech Republic", "region": "Europe", "population": 10700000},
    {"code": "PT", "name": "Portugal", "region": "Europe", "population": 10300000},
    {"code": "GR", "name": "Greece", "region": "Europe", "population": 10700000},
    {"code": "HU", "name": "Hungary", "region": "Europe", "population": 9700000},
    {"code": "SE", "name": "Sweden", "region": "Europe", "population": 10400000},
    {"code": "AT", "name": "Austria", "region": "Europe", "population": 9000000},
    {"code": "CH", "name": "Switzerland", "region": "Europe", "population": 8700000},
    {"code": "BG", "name": "Bulgaria", "region": "Europe", "population": 6900000},
    {"code": "RS", "name": "Serbia", "region": "Europe", "population": 8700000},
    {"code": "DK", "name": "Denmark", "region": "Europe", "population": 5800000},
    {"code": "FI", "name": "Finland", "region": "Europe", "population": 5500000},
    {"code": "SK", "name": "Slovakia", "region": "Europe", "population": 5500000},
    {"code": "NO", "name": "Norway", "region": "Europe", "population": 5400000},
    {"code": "IE", "name": "Ireland", "region": "Europe", "population": 5000000},
    {"code": "HR", "name": "Croatia", "region": "Europe", "population": 3900000},
    {"code": "BA", "name": "Bosnia and Herzegovina", "region": "Europe", "population": 3300000},
    {"code": "AL", "name": "Albania", "region": "Europe", "population": 2800000},
    {"code": "SI", "name": "Slovenia", "region": "Europe", "population": 2100000},
    {"code": "LV", "name": "Latvia", "region": "Europe", "population": 1900000},
    {"code": "EE", "name": "Estonia", "region": "Europe", "population": 1300000},
    {"code": "ME", "name": "Montenegro", "region": "Europe", "population": 600000},
    {"code": "LU", "name": "Luxembourg", "region": "Europe", "population": 600000},
    {"code": "MT", "name": "Malta", "region": "Europe", "population": 500000},
    {"code": "IS", "name": "Iceland", "region": "Europe", "population": 400000},
    
    # Eastern Europe & Former Soviet
    {"code": "RU", "name": "Russia", "region": "Europe", "population": 145900000},
    {"code": "UA", "name": "Ukraine", "region": "Europe", "population": 44100000},
    {"code": "UZ", "name": "Uzbekistan", "region": "Central Asia", "population": 34200000},
    {"code": "KZ", "name": "Kazakhstan", "region": "Central Asia", "population": 19400000},
    {"code": "BY", "name": "Belarus", "region": "Europe", "population": 9500000},
    {"code": "AZ", "name": "Azerbaijan", "region": "Europe", "population": 10100000},
    {"code": "GE", "name": "Georgia", "region": "Europe", "population": 3700000},
    {"code": "AM", "name": "Armenia", "region": "Europe", "population": 3000000},
    {"code": "MD", "name": "Moldova", "region": "Europe", "population": 4000000},
    {"code": "KG", "name": "Kyrgyzstan", "region": "Central Asia", "population": 6600000},
    {"code": "TJ", "name": "Tajikistan", "region": "Central Asia", "population": 9500000},
    {"code": "TM", "name": "Turkmenistan", "region": "Central Asia", "population": 6000000},
    
    # Asia-Pacific
    {"code": "CN", "name": "China", "region": "Asia", "population": 1439000000},
    {"code": "IN", "name": "India", "region": "Asia", "population": 1380000000},
    {"code": "ID", "name": "Indonesia", "region": "Asia", "population": 273500000},
    {"code": "PK", "name": "Pakistan", "region": "Asia", "population": 225200000},
    {"code": "BD", "name": "Bangladesh", "region": "Asia", "population": 165000000},
    {"code": "JP", "name": "Japan", "region": "Asia", "population": 125800000},
    {"code": "PH", "name": "Philippines", "region": "Asia", "population": 109600000},
    {"code": "VN", "name": "Vietnam", "region": "Asia", "population": 97300000},
    {"code": "TR", "name": "Turkey", "region": "Europe", "population": 84300000},
    {"code": "IR", "name": "Iran", "region": "Middle East", "population": 84000000},
    {"code": "TH", "name": "Thailand", "region": "Asia", "population": 69800000},
    {"code": "MM", "name": "Myanmar", "region": "Asia", "population": 54400000},
    {"code": "KR", "name": "South Korea", "region": "Asia", "population": 51800000},
    {"code": "AF", "name": "Afghanistan", "region": "Asia", "population": 39000000},
    {"code": "MY", "name": "Malaysia", "region": "Asia", "population": 32400000},
    {"code": "NP", "name": "Nepal", "region": "Asia", "population": 29100000},
    {"code": "LK", "name": "Sri Lanka", "region": "Asia", "population": 21900000},
    {"code": "KH", "name": "Cambodia", "region": "Asia", "population": 16700000},
    {"code": "JO", "name": "Jordan", "region": "Middle East", "population": 10200000},
    {"code": "AE", "name": "United Arab Emirates", "region": "Middle East", "population": 9900000},
    {"code": "LA", "name": "Laos", "region": "Asia", "population": 7300000},
    {"code": "SG", "name": "Singapore", "region": "Asia", "population": 5900000},
    {"code": "OM", "name": "Oman", "region": "Middle East", "population": 5100000},
    {"code": "KW", "name": "Kuwait", "region": "Middle East", "population": 4300000},
    {"code": "MN", "name": "Mongolia", "region": "Asia", "population": 3300000},
    {"code": "BH", "name": "Bahrain", "region": "Middle East", "population": 1700000},
    {"code": "BT", "name": "Bhutan", "region": "Asia", "population": 800000},
    {"code": "MV", "name": "Maldives", "region": "Asia", "population": 500000},
    {"code": "BN", "name": "Brunei", "region": "Asia", "population": 400000},
    
    # Oceania
    {"code": "AU", "name": "Australia", "region": "Oceania", "population": 25500000},
    {"code": "PG", "name": "Papua New Guinea", "region": "Oceania", "population": 9000000},
    {"code": "NZ", "name": "New Zealand", "region": "Oceania", "population": 5100000},
    {"code": "FJ", "name": "Fiji", "region": "Oceania", "population": 900000},
    {"code": "SB", "name": "Solomon Islands", "region": "Oceania", "population": 700000},
    {"code": "VU", "name": "Vanuatu", "region": "Oceania", "population": 300000},
    {"code": "WS", "name": "Samoa", "region": "Oceania", "population": 200000},
    {"code": "TO", "name": "Tonga", "region": "Oceania", "population": 100000},
    
    # Middle East & North Africa
    {"code": "SA", "name": "Saudi Arabia", "region": "Middle East", "population": 34800000},
    {"code": "IQ", "name": "Iraq", "region": "Middle East", "population": 40200000},
    {"code": "DZ", "name": "Algeria", "region": "North Africa", "population": 44600000},
    {"code": "SD", "name": "Sudan", "region": "North Africa", "population": 44900000},
    {"code": "MA", "name": "Morocco", "region": "North Africa", "population": 37000000},
    {"code": "EG", "name": "Egypt", "region": "North Africa", "population": 102300000},
    {"code": "TN", "name": "Tunisia", "region": "North Africa", "population": 11800000},
    {"code": "LY", "name": "Libya", "region": "North Africa", "population": 6900000},
    {"code": "LB", "name": "Lebanon", "region": "Middle East", "population": 6800000},
    {"code": "IL", "name": "Israel", "region": "Middle East", "population": 9400000},
    {"code": "PS", "name": "Palestine", "region": "Middle East", "population": 5100000},
    {"code": "YE", "name": "Yemen", "region": "Middle East", "population": 30000000},
    {"code": "SY", "name": "Syria", "region": "Middle East", "population": 17500000},
    {"code": "QA", "name": "Qatar", "region": "Middle East", "population": 2900000},
    
    # Sub-Saharan Africa
    {"code": "NG", "name": "Nigeria", "region": "Africa", "population": 206100000},
    {"code": "ET", "name": "Ethiopia", "region": "Africa", "population": 115000000},
    {"code": "CD", "name": "Democratic Republic of Congo", "region": "Africa", "population": 90000000},
    {"code": "TZ", "name": "Tanzania", "region": "Africa", "population": 59700000},
    {"code": "ZA", "name": "South Africa", "region": "Africa", "population": 59300000},
    {"code": "KE", "name": "Kenya", "region": "Africa", "population": 53800000},
    {"code": "UG", "name": "Uganda", "region": "Africa", "population": 45700000},
    {"code": "GH", "name": "Ghana", "region": "Africa", "population": 31100000},
    {"code": "MZ", "name": "Mozambique", "region": "Africa", "population": 31300000},
    {"code": "MG", "name": "Madagascar", "region": "Africa", "population": 27700000},
    {"code": "CM", "name": "Cameroon", "region": "Africa", "population": 26500000},
    {"code": "CI", "name": "Ivory Coast", "region": "Africa", "population": 26400000},
    {"code": "NE", "name": "Niger", "region": "Africa", "population": 24200000},
    {"code": "BF", "name": "Burkina Faso", "region": "Africa", "population": 21000000},
    {"code": "MW", "name": "Malawi", "region": "Africa", "population": 19100000},
    {"code": "ML", "name": "Mali", "region": "Africa", "population": 20200000},
    {"code": "ZM", "name": "Zambia", "region": "Africa", "population": 18400000},
    {"code": "SN", "name": "Senegal", "region": "Africa", "population": 16700000},
    {"code": "SO", "name": "Somalia", "region": "Africa", "population": 15900000},
    {"code": "TD", "name": "Chad", "region": "Africa", "population": 16400000},
    {"code": "ZW", "name": "Zimbabwe", "region": "Africa", "population": 14900000},
    {"code": "GN", "name": "Guinea", "region": "Africa", "population": 13100000},
    {"code": "RW", "name": "Rwanda", "region": "Africa", "population": 12900000},
    {"code": "BJ", "name": "Benin", "region": "Africa", "population": 12100000},
    {"code": "BI", "name": "Burundi", "region": "Africa", "population": 11900000},
    {"code": "SS", "name": "South Sudan", "region": "Africa", "population": 11200000},
    {"code": "TG", "name": "Togo", "region": "Africa", "population": 8300000},
    {"code": "SL", "name": "Sierra Leone", "region": "Africa", "population": 8000000},
    {"code": "LR", "name": "Liberia", "region": "Africa", "population": 5100000},
    {"code": "CF", "name": "Central African Republic", "region": "Africa", "population": 4800000},
    {"code": "MR", "name": "Mauritania", "region": "Africa", "population": 4600000},
    {"code": "ER", "name": "Eritrea", "region": "Africa", "population": 3500000},
    {"code": "GM", "name": "Gambia", "region": "Africa", "population": 2400000},
    {"code": "BW", "name": "Botswana", "region": "Africa", "population": 2400000},
    {"code": "LS", "name": "Lesotho", "region": "Africa", "population": 2100000},
    {"code": "NA", "name": "Namibia", "region": "Africa", "population": 2500000},
    {"code": "GW", "name": "Guinea-Bissau", "region": "Africa", "population": 2000000},
    {"code": "GQ", "name": "Equatorial Guinea", "region": "Africa", "population": 1400000},
    {"code": "MU", "name": "Mauritius", "region": "Africa", "population": 1300000},
    {"code": "SZ", "name": "Eswatini", "region": "Africa", "population": 1200000},
    {"code": "DJ", "name": "Djibouti", "region": "Africa", "population": 1000000},
    {"code": "CG", "name": "Republic of Congo", "region": "Africa", "population": 5500000},
    {"code": "KM", "name": "Comoros", "region": "Africa", "population": 900000},
    {"code": "CV", "name": "Cape Verde", "region": "Africa", "population": 600000},
    {"code": "ST", "name": "Sao Tome and Principe", "region": "Africa", "population": 200000},
    {"code": "SC", "name": "Seychelles", "region": "Africa", "population": 100000},
    
    # Latin America & Caribbean
    {"code": "BR", "name": "Brazil", "region": "South America", "population": 215300000},
    {"code": "CO", "name": "Colombia", "region": "South America", "population": 50900000},
    {"code": "AR", "name": "Argentina", "region": "South America", "population": 45400000},
    {"code": "PE", "name": "Peru", "region": "South America", "population": 33000000},
    {"code": "VE", "name": "Venezuela", "region": "South America", "population": 28400000},
    {"code": "CL", "name": "Chile", "region": "South America", "population": 19100000},
    {"code": "GT", "name": "Guatemala", "region": "Central America", "population": 17900000},
    {"code": "EC", "name": "Ecuador", "region": "South America", "population": 17600000},
    {"code": "BO", "name": "Bolivia", "region": "South America", "population": 11700000},
    {"code": "CU", "name": "Cuba", "region": "Caribbean", "population": 11300000},
    {"code": "DO", "name": "Dominican Republic", "region": "Caribbean", "population": 10800000},
    {"code": "HT", "name": "Haiti", "region": "Caribbean", "population": 11400000},
    {"code": "HN", "name": "Honduras", "region": "Central America", "population": 10000000},
    {"code": "NI", "name": "Nicaragua", "region": "Central America", "population": 6600000},
    {"code": "CR", "name": "Costa Rica", "region": "Central America", "population": 5100000},
    {"code": "PA", "name": "Panama", "region": "Central America", "population": 4300000},
    {"code": "UY", "name": "Uruguay", "region": "South America", "population": 3500000},
    {"code": "JM", "name": "Jamaica", "region": "Caribbean", "population": 3000000},
    {"code": "TT", "name": "Trinidad and Tobago", "region": "Caribbean", "population": 1400000},
    {"code": "GY", "name": "Guyana", "region": "South America", "population": 800000},
    {"code": "SR", "name": "Suriname", "region": "South America", "population": 600000},
    {"code": "BZ", "name": "Belize", "region": "Central America", "population": 400000},
    {"code": "BB", "name": "Barbados", "region": "Caribbean", "population": 300000},
    {"code": "SV", "name": "El Salvador", "region": "Central America", "population": 6500000},
    {"code": "PY", "name": "Paraguay", "region": "South America", "population": 7100000},
]

def get_all_country_codes():
    """Get list of all country codes for data collection"""
    return [country["code"] for country in EXPANDED_COUNTRIES]

def get_countries_by_region(region_name):
    """Get countries filtered by region"""
    return [country for country in EXPANDED_COUNTRIES if country["region"] == region_name]

def get_country_info(country_code):
    """Get country information by ISO code"""
    for country in EXPANDED_COUNTRIES:
        if country["code"] == country_code:
            return country
    return None

# Priority groups for staged data collection
HIGH_PRIORITY_COUNTRIES = ["US", "CN", "RU", "GB", "DE", "FR", "JP", "IN", "BR", "TR"]
MEDIUM_PRIORITY_COUNTRIES = ["IT", "ES", "CA", "AU", "KR", "MX", "SA", "EG", "NG", "ZA", "AR", "ID", "PK", "BD", "VN", "TH", "MY", "PH", "IL", "IR", "IQ"]