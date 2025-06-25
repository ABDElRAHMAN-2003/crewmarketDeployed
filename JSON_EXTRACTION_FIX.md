# JSON Extraction and MongoDB Storage Fix

## Problem Description

The CrewAI system was outputting Pydantic objects, but the requirement was to store raw JSON directly in MongoDB. The issue was in the data processing pipeline where:

1. CrewAI was returning a Pydantic object with a `raw` field containing JSON string
2. The code was extracting the JSON correctly but then storing the original Pydantic object instead of the extracted JSON
3. This resulted in MongoDB storing the Pydantic object structure instead of the clean JSON data

## Solution Implemented

### 1. Fixed JSON Extraction Logic

**File: `src/marketcompare/main.py`**

The main logic in the `run()` function was updated to:

```python
# Extract JSON from the raw field
raw_str = result['raw'] if isinstance(result, dict) and 'raw' in result else getattr(result, 'raw', None)
if raw_str is not None:
    # Clean the raw string and parse as JSON
    raw_str = re.sub(r"```[a-zA-Z]*", "", raw_str).strip()
    forecast_json = _json.loads(raw_str)
elif isinstance(result, FinalReportOutput):
    forecast_json = result.dict(by_alias=True)
elif isinstance(result, dict):
    forecast_json = result
else:
    raise Exception(f"Crew did not return a recognizable forecast output. Full result: {result}")

# Store the extracted JSON (not the original result object)
save_output_to_mongodb(forecast_json, uri, db_name, output_collection)
```

### 2. Enhanced MongoDB Storage Function

**File: `src/marketcompare/main.py`**

Updated `save_output_to_mongodb()` function to:

```python
def save_output_to_mongodb(result_data, uri, db_name, collection_name):
    from datetime import datetime, UTC
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    # If it's a Pydantic object, convert to dict
    if hasattr(result_data, "dict"):
        result_data = result_data.dict()
    # If it's already a dict, use it as is
    elif not isinstance(result_data, dict):
        raise ValueError(f"Expected dict or Pydantic object, got {type(result_data)}")

    # Add timestamp
    result_data["createdAt"] = datetime.now(UTC)
    
    # Insert into MongoDB
    inserted = collection.insert_one(result_data)
    print(f"✅ Report saved to MongoDB with _id: {inserted.inserted_id}")
    return inserted.inserted_id
```

### 3. Added Debugging and Testing

**File: `src/marketcompare/main.py`**

Added comprehensive debugging output and a test function:

```python
def test_json_extraction():
    """Test the JSON extraction logic with simulated crew output"""
    # Simulates the crew output structure and tests the extraction logic
    # Verifies that JSON is properly extracted and stored in MongoDB
```

## Expected Data Structure in MongoDB

After the fix, MongoDB will store clean JSON data in this format:

```json
{
  "_id": {
    "$oid": "68581b8fb8524a0f42123c75"
  },
  "swot_analysis": {
    "strengths": ["Strong brand reputation", "Diverse product range"],
    "weaknesses": ["Weak online presence", "Dependence on third-party suppliers"],
    "opportunities": ["Expansion into emerging markets", "Increasing demand for eco-friendly products"],
    "threats": ["Intense competition", "Changing regulatory environment"]
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
    "key_differentiators": ["Innovative product features", "Excellent customer service"],
    "customer_segments": ["Eco-conscious consumers", "Tech-savvy millennials"]
  },
  "market_analysis": {
    "industry_trends": ["Rising interest in sustainable products", "Growth in smart home technology"],
    "consumer_behaviors": ["Increased online shopping", "Preference for high-quality goods"],
    "market_growth": "5% annual increase in demand for project management software"
  },
  "recommendations": {
    "strategic_moves": ["Increase digital marketing efforts", "Form strategic partnerships with eco-friendly brands"],
    "product_development": ["Invest in smart technology", "Enhance eco-friendly product lines"]
  },
  "createdAt": {
    "$date": "2025-01-15T21:17:25.778Z"
  }
}
```

## Testing

To test the JSON extraction logic:

```bash
cd src
python -c "from marketcompare.main import test_json_extraction; test_json_extraction()"
```

This will:
1. Simulate the crew output structure
2. Extract the JSON from the `raw` field
3. Store it in MongoDB
4. Verify the data structure

## Benefits

1. **Clean JSON Storage**: MongoDB now stores the actual JSON data instead of Pydantic object structures
2. **Better Queryability**: The JSON structure is easier to query and analyze
3. **Consistent Data Format**: All data follows the expected JSON schema
4. **Improved Debugging**: Added comprehensive logging to track the extraction process
5. **Future-Proof**: Fixed deprecation warnings and improved error handling

## Files Modified

- `src/marketcompare/main.py`: Main logic for JSON extraction and MongoDB storage 