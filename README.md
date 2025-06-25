# Market Comparison Analysis System

This system performs comprehensive market comparison analysis using CrewAI agents and stores results in MongoDB with a clean, simple JSON structure.

## Features

- **Clean JSON Output**: Results are stored in a simple, readable JSON format
- **MongoDB Integration**: Automatic storage to MongoDB with proper ObjectId formatting
- **Multi-Agent Analysis**: Uses specialized agents for different aspects of market analysis
- **Error Handling**: Robust error handling and debugging output

## Data Structure

The system now stores data in this clean format:

```json
{
  "_id": {
    "$oid": "684f38658023945a42f08c85"
  },
  "swot_analysis": {
    "strengths": [
      "Strong brand reputation",
      "Diverse product range"
    ],
    "weaknesses": [
      "Weak online presence",
      "Dependence on third-party suppliers"
    ],
    "opportunities": [
      "Expansion into emerging markets",
      "Increasing demand for eco-friendly products"
    ],
    "threats": [
      "Intense competition",
      "Changing regulatory environment"
    ]
  },
  "pricing_comparison": {
    "competitor_pricing": [
      {
        "competitor": "Company A",
        "product_line": "Project Management Software",
        "price_range": "$200-$500"
      }
    ],
    "our_pricing": [
      {
        "product_line": "Project Management Software",
        "price_range": "$220-$480"
      }
    ]
  },
  "competitive_positioning": {
    "market_share": "12%",
    "key_differentiators": [
      "Innovative product features",
      "Excellent customer service"
    ],
    "customer_segments": [
      "Eco-conscious consumers",
      "Tech-savvy millennials"
    ]
  },
  "market_analysis": {
    "industry_trends": [
      "Rising interest in sustainable products",
      "Growth in smart home technology"
    ],
    "consumer_behaviors": [
      "Increased online shopping",
      "Preference for high-quality goods"
    ],
    "market_growth": "5% annual increase in demand for project management software"
  },
  "recommendations": {
    "strategic_moves": [
      "Increase digital marketing efforts",
      "Form strategic partnerships with eco-friendly brands"
    ],
    "product_development": [
      "Invest in smart technology",
      "Enhance eco-friendly product lines"
    ]
  },
  "createdAt": {
    "$date": "2025-06-15T21:17:25.778Z"
  }
}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your_openai_api_key"
export SERPER_API_KEY="your_serper_api_key"
```

3. Configure MongoDB connection in `src/marketcompare/main.py`

## Usage

### Run the full analysis:
```bash
python -m src.marketcompare.main
```

### Test crew compilation:
```bash
# Uncomment the test_crew_compilation() line in main.py
python -m src.marketcompare.main
```

### Test clean structure transformation:
```bash
# Uncomment the test_clean_structure() line in main.py
python -m src.marketcompare.main
```

## Troubleshooting

### Crew Compilation Issues
- Check that all environment variables are set
- Verify MongoDB connection string
- Ensure all required files are present in the company_docs directory

### Data Structure Issues
- The system automatically transforms complex crew output to clean JSON
- Check the console output for debugging information
- Use the test functions to verify the transformation works

### MongoDB Connection Issues
- Verify the connection string in `main.py`
- Check that the database and collections exist
- Ensure network connectivity to MongoDB

## File Structure

```
marketcompare/
├── src/marketcompare/
│   ├── main.py              # Main execution file
│   ├── crew.py              # CrewAI configuration
│   ├── enhanced_models.py   # Pydantic models
│   ├── config/
│   │   ├── agents.yaml      # Agent configurations
│   │   └── tasks.yaml       # Task configurations
│   └── company_docs/        # Company documents for analysis
├── README.md
└── requirements.txt
```

## Recent Changes

- **Simplified JSON Structure**: Removed complex nested objects and source attributions
- **Better Error Handling**: Added comprehensive debugging output
- **Task Dependencies**: Fixed task flow to include initialization step
- **MongoDB Integration**: Improved data transformation and storage
