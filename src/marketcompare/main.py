import sys
import warnings
import os
from pathlib import Path
from datetime import datetime, UTC
import json

# from marketcom.crew import Marketcom
from .crew import Marketcompare
from .enhanced_models import FinalReportOutput
from .tools.pdf_report_tool import PDFReportTool
import matplotlib.pyplot as plt
import base64
import io

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from pymongo import MongoClient
from bson import ObjectId

def get_file_content_by_filename(uri, db_name, collection_name, filename):
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    # Fetch the most recent document with matching filename
    doc = collection.find_one(
        {"originalFileName": filename},
        sort=[("uploadedAt", -1)]  # Latest first
    )

    if not doc:
        raise ValueError(f"No document found with originalFileName = '{filename}'")
    if "content" not in doc:
        raise ValueError(f"Document with originalFileName = '{filename}' has no 'content' field")

    return doc["content"]

def save_output_to_mongodb(result_data, uri, db_name, collection_name):
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

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.

def run():
    """Run the crew with file contents fetched from MongoDB"""
    # MongoDB config
    uri = "mongodb+srv://Ali:suy4C1XDn5fHQOyd@nulibrarysystem.9c6hrww.mongodb.net/"
    db_name = "sample_db"
    input_collection = "Market_LLM_Input"
    output_collection = "Market_LLM_Output"

    # Mapping of input variables to their MongoDB document IDs
    file_names = {
        'user_preference': None,  # If needed, you can upload this too
        'annual_report_2024': "annual_report_2024.txt",
        'customer_feedback_summary_q1_2025': "customer_feedback_summary_q1_2025.txt",
        'balance_sheet_2024': "balance_sheet_2024.txt",
        'cash_flow_statement_2024': "cash_flow_statement_2024.txt",
        'income_statement_2024': "income_statement_2024.txt",
        'marketing_report_q1_2025': "marketing_report_q1_2025.txt",
        'operational_report_q1_2025': "operational_report_q1_2025.txt",
        'sales_report_q1_2025': "sales_report_q1_2025.txt",
        'internal_pricing_document': "internal_pricing_document.txt",
        'product_roadmap_h2_2025': "product_roadmap_h2_2025.txt",
    }

    # Build the input dictionary for the crew
    inputs = {
        'topic': 'Market Comparison Analysis',
        'current_year': str(datetime.now().year),
    }

    # Fetch each document's content from MongoDB
    for key, filename in file_names.items():
        if filename:
            try:
                inputs[key] = get_file_content_by_filename(uri, db_name, input_collection, filename)
            except Exception as e:
                print(f"⚠️ Failed to load {key} from MongoDB: {e}")
                inputs[key] = f"[Error loading {key}]"
        else:
            inputs[key] = ""

    # Run the crew
    try:
        result = Marketcompare().crew().kickoff(inputs=inputs)

        # result_file_path = Path(
        #     "/Users/abdelrahmanmagdi/Desktop/eyide/crewai_connecting_db/marketcompare/src/results/market_comparison_report.json")
        #
        # try:
        #     with open(result_file_path, 'r', encoding='utf-8') as f:
        #         result = json.load(f)
        #     print(f"✅ Loaded result from JSON file: {result_file_path}")
        # except Exception as e:
        #     raise Exception(f"❌ Failed to load result from file: {e}")
        # print("✅ Crew analysis completed")
        import json as _json
        import re

        # Try to extract the forecast JSON robustly
        raw_str = result['raw'] if isinstance(result, dict) and 'raw' in result else getattr(result, 'raw', None)
        if raw_str is not None:
            if not raw_str.strip():
                raise Exception("Crew output 'raw' field is empty. Full result: {}".format(result))
            # Remove all markdown code block markers (```json, ```)
            raw_str = re.sub(r"```[a-zA-Z]*", "", raw_str).strip()
            try:
                forecast_json = _json.loads(raw_str)
            except Exception as e:
                raise Exception(f"Failed to parse forecast JSON from raw value: {e}\nRaw value: {raw_str}")
        elif isinstance(result, FinalReportOutput):
            forecast_json = result.dict(by_alias=True)
        elif isinstance(result, dict):
            forecast_json = result
        else:
            raise Exception(f"Crew did not return a recognizable forecast output. Full result: {result}")

        # Remove _id if it's a dict with $oid, or let MongoDB generate it
        if isinstance(forecast_json.get("_id"), dict) and "$oid" in forecast_json["_id"]:
            oid_str = forecast_json["_id"]["$oid"]
            if isinstance(oid_str, str) and len(oid_str) == 24:
                forecast_json["_id"] = ObjectId(oid_str)
            else:
                forecast_json.pop("_id")
        elif "_id" in forecast_json:
            forecast_json.pop("_id")

        # Save the extracted JSON to MongoDB (not the original result object)
        inserted_id = save_output_to_mongodb(forecast_json, uri, db_name, output_collection)
        
        # Debug output to show what was stored
        print(f"✅ Successfully extracted and stored JSON data:")
        print(f"   - MongoDB ID: {inserted_id}")
        print(f"   - Data type: {type(forecast_json)}")
        print(f"   - Keys: {list(forecast_json.keys())}")
        
        # Show a sample of the stored data
        if 'swot_analysis' in forecast_json:
            print(f"   - SWOT Analysis keys: {list(forecast_json['swot_analysis'].keys())}")
        if 'pricing_comparison' in forecast_json:
            print(f"   - Pricing Comparison keys: {list(forecast_json['pricing_comparison'].keys())}")

        # --- PDF Report Generation ---
        try:
            # Create professional business report content
            report_title = "Market Comparison Analysis Report"
            company_name = "Innovatech Solutions Ltd."
            report_date = datetime.now().strftime("%B %d, %Y")
            
            # Extract key data for the report
            swot_data = forecast_json.get('swot_analysis', {})
            pricing_data = forecast_json.get('pricing_comparison', {})
            competitive_data = forecast_json.get('competitive_positioning', {})
            market_data = forecast_json.get('market_analysis', {})
            recommendations_data = forecast_json.get('recommendations', {})
            
            # Create dynamic analysis text using actual crew results
            analysis_text = f"""
EXECUTIVE SUMMARY
================
This comprehensive market comparison analysis provides strategic insights into {company_name}'s competitive position, market opportunities, and recommended actions for sustainable growth. The analysis reveals key findings and strategic recommendations based on comprehensive market research and competitive intelligence.

KEY FINDINGS
===========
"""
            
            # Add dynamic key findings from the analysis
            if 'key_findings' in forecast_json:
                for finding in forecast_json['key_findings']:
                    analysis_text += f"• {finding}\n"
            else:
                analysis_text += "• Analysis completed with comprehensive market insights\n"
                analysis_text += "• Strategic recommendations developed based on competitive analysis\n"
                analysis_text += "• Market positioning and opportunities identified\n"

            analysis_text += f"""
SWOT ANALYSIS
=============
STRENGTHS:
"""
            
            # Add dynamic strengths
            strengths = swot_data.get('strengths', [])
            if strengths:
                for strength in strengths:
                    analysis_text += f"• {strength}\n"
            else:
                analysis_text += "• Strong market position and competitive advantages\n"

            analysis_text += f"""
WEAKNESSES:
"""
            
            # Add dynamic weaknesses
            weaknesses = swot_data.get('weaknesses', [])
            if weaknesses:
                for weakness in weaknesses:
                    analysis_text += f"• {weakness}\n"
            else:
                analysis_text += "• Areas for improvement identified in analysis\n"

            analysis_text += f"""
OPPORTUNITIES:
"""
            
            # Add dynamic opportunities
            opportunities = swot_data.get('opportunities', [])
            if opportunities:
                for opportunity in opportunities:
                    analysis_text += f"• {opportunity}\n"
            else:
                analysis_text += "• Market expansion and growth opportunities available\n"

            analysis_text += f"""
THREATS:
"""
            
            # Add dynamic threats
            threats = swot_data.get('threats', [])
            if threats:
                for threat in threats:
                    analysis_text += f"• {threat}\n"
            else:
                analysis_text += "• Competitive and market risks identified\n"

            analysis_text += f"""
COMPETITIVE POSITIONING
======================
Market Share: {competitive_data.get('market_share', 'N/A')}
Key Differentiators:
"""
            
            # Add dynamic differentiators
            differentiators = competitive_data.get('key_differentiators', [])
            if differentiators:
                for diff in differentiators:
                    analysis_text += f"• {diff}\n"
            else:
                analysis_text += "• Competitive advantages identified in analysis\n"

            analysis_text += f"""
Target Customer Segments:
"""
            
            # Add dynamic customer segments
            segments = competitive_data.get('target_segments', [])
            if segments:
                for segment in segments:
                    analysis_text += f"• {segment}\n"
            else:
                analysis_text += "• Primary and secondary market segments identified\n"

            analysis_text += f"""
PRICING ANALYSIS
===============
Our Pricing Strategy:
"""
            
            # Add dynamic pricing strategy
            our_pricing = pricing_data.get('our_pricing', [])
            if our_pricing:
                for pricing in our_pricing:
                    analysis_text += f"• {pricing.get('product_line', 'Product')}: {pricing.get('price_range', 'N/A')}\n"
            else:
                analysis_text += "• Competitive pricing strategy implemented\n"

            analysis_text += f"""
Competitive Landscape:
"""
            
            # Add dynamic competitor pricing
            competitor_pricing = pricing_data.get('competitor_pricing', [])
            if competitor_pricing:
                for comp in competitor_pricing:
                    analysis_text += f"• {comp.get('competitor', 'Competitor')}: {comp.get('price_range', 'N/A')}\n"
            else:
                analysis_text += "• Competitive pricing analysis completed\n"

            analysis_text += f"""
MARKET TRENDS
=============
Industry Trends:
"""
            
            # Add dynamic market trends
            trends = market_data.get('industry_trends', [])
            if trends:
                for trend in trends:
                    analysis_text += f"• {trend}\n"
            else:
                analysis_text += "• Key industry trends and market dynamics identified\n"

            analysis_text += f"""
Market Growth: {market_data.get('market_growth', 'N/A')}

STRATEGIC RECOMMENDATIONS
========================
Immediate Actions (Next 3-6 Months):
"""
            
            # Add dynamic immediate recommendations
            immediate_recs = recommendations_data.get('immediate_actions', [])
            if immediate_recs:
                for rec in immediate_recs:
                    analysis_text += f"• {rec}\n"
            else:
                analysis_text += "• Strategic initiatives for immediate implementation\n"

            analysis_text += f"""
Product Development Initiatives (6-12 Months):
"""
            
            # Add dynamic long-term recommendations
            long_term_recs = recommendations_data.get('long_term_initiatives', [])
            if long_term_recs:
                for rec in long_term_recs:
                    analysis_text += f"• {rec}\n"
            else:
                analysis_text += "• Long-term strategic development priorities\n"

            analysis_text += f"""
CONCLUSION
==========
{company_name} demonstrates strong market positioning with significant opportunities for growth and expansion. The comprehensive analysis provides a roadmap for strategic decision-making and competitive advantage.

Key insights from this analysis include:
• Strategic positioning in target markets
• Competitive advantages and differentiation opportunities  
• Market expansion and growth potential
• Risk mitigation and threat management strategies

With proper execution of the recommended initiatives, {company_name} is positioned for sustained growth and market leadership.

Report Generated: {report_date}
Analysis Period: Current Market Conditions
Prepared by: AI Market Analysis Team
"""
            
            # Create dynamic graphs based on actual data
            graph_images = []
            
            # Graph 1: SWOT Analysis Summary (this one was already dynamic)
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            categories = ['Strengths', 'Weaknesses', 'Opportunities', 'Threats']
            counts = [
                len(swot_data.get('strengths', [])),
                len(swot_data.get('weaknesses', [])),
                len(swot_data.get('opportunities', [])),
                len(swot_data.get('threats', []))
            ]
            colors = ['#28a745', '#dc3545', '#ffc107', '#6c757d']
            bars = ax1.bar(categories, counts, color=colors)
            ax1.set_title('SWOT Analysis Summary', fontsize=16, fontweight='bold')
            ax1.set_ylabel('Number of Items', fontsize=12)
            for bar, count in zip(bars, counts):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                        str(count), ha='center', va='bottom', fontweight='bold')
            ax1.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            graph_images.append(fig_to_base64(fig1))
            plt.close(fig1)
            
            # Graph 2: Pricing Comparison (dynamic based on actual pricing data)
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            if our_pricing and competitor_pricing:
                # Extract product names and create comparison
                products = [p.get('product_line', f'Product {i}') for i, p in enumerate(our_pricing)]
                our_prices = [p.get('price_range', '0') for p in our_pricing]
                comp_prices = [p.get('price_range', '0') for p in competitor_pricing[:len(our_pricing)]]
                
                x = range(len(products))
                width = 0.35
                
                ax2.bar([i - width/2 for i in x], our_prices, width, label='Our Pricing', color='#A23B72')
                ax2.bar([i + width/2 for i in x], comp_prices, width, label='Competitor Pricing', color='#2E86AB')
                
                ax2.set_title('Pricing Comparison', fontsize=16, fontweight='bold')
                ax2.set_ylabel('Price Range', fontsize=12)
                ax2.set_xlabel('Products', fontsize=12)
                ax2.set_xticks(x)
                ax2.set_xticklabels(products, rotation=45)
                ax2.legend()
                ax2.grid(axis='y', alpha=0.3)
            else:
                # Fallback if no pricing data
                ax2.text(0.5, 0.5, 'Pricing data not available', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Pricing Comparison', fontsize=16, fontweight='bold')
            plt.tight_layout()
            graph_images.append(fig_to_base64(fig2))
            plt.close(fig2)
            
            # Graph 3: Recommendations Distribution (dynamic based on actual recommendations)
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            if immediate_recs and long_term_recs:
                categories = ['Immediate Actions', 'Long-term Initiatives']
                counts = [len(immediate_recs), len(long_term_recs)]
                colors = ['#28a745', '#17a2b8']
                bars = ax3.bar(categories, counts, color=colors)
                ax3.set_title('Strategic Recommendations Distribution', fontsize=16, fontweight='bold')
                ax3.set_ylabel('Number of Recommendations', fontsize=12)
                for bar, count in zip(bars, counts):
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            str(count), ha='center', va='bottom', fontweight='bold')
                ax3.grid(axis='y', alpha=0.3)
            else:
                # Fallback if no recommendations data
                ax3.text(0.5, 0.5, 'Recommendations data not available', ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title('Strategic Recommendations', fontsize=16, fontweight='bold')
            plt.tight_layout()
            graph_images.append(fig_to_base64(fig3))
            plt.close(fig3)

            pdf_tool = PDFReportTool()
            
            # Debug: Check the type and content of analysis_text
            print(f"🔍 Debug: analysis_text type: {type(analysis_text)}")
            print(f"🔍 Debug: analysis_text length: {len(analysis_text) if isinstance(analysis_text, str) else 'N/A'}")
            print(f"🔍 Debug: analysis_text preview: {analysis_text[:200] if isinstance(analysis_text, str) else str(analysis_text)[:200]}")
            
            # Ensure analysis_text is a string
            if not isinstance(analysis_text, str):
                analysis_text = str(analysis_text)
            
            pdf_result = pdf_tool._run(
                analysis_text=analysis_text,
                graph_images=graph_images,
                pdf_filename="market_comparison_report.pdf",
                store_in_mongo=True,
                mongo_collection="Market_Report"
            )
            print(pdf_result)
        except Exception as e:
            print(f"❌ Error generating PDF report: {e}")

    except Exception as e:
        raise Exception(f"❌ An error occurred while running the crew: {e}")

def train():
    """
    Train the crew for a given number of iterations.
    """
    # Set up paths for training
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Function to safely read file content
    def read_file_content(file_path):
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
                return f"Error reading file: {file_path}"
        else:
            print(f"Warning: File not found: {file_path}")
            return f"File not found: {file_path}"

    # Read essential files for training
    preferences_file = script_dir / 'knowledge' / 'user_preference.txt'
    user_preference_content = read_file_content(preferences_file)

    company_docs_dir = script_dir / 'company_docs'
    annual_report_path = company_docs_dir / 'annual_reports' / 'annual_report_2024.txt'
    annual_report_content = read_file_content(annual_report_path)

    inputs = {
        "topic": "Market Comparison Analysis",
        'current_year': str(datetime.now().year),
        'user_preference': user_preference_content,
        'annual_report_2024': annual_report_content,
        # Add other file contents as needed for training
    }

    try:
        Marketcompare().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Marketcompare().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    # Set up paths for testing
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Function to safely read file content
    def read_file_content(file_path):
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
                return f"Error reading file: {file_path}"
        else:
            print(f"Warning: File not found: {file_path}")
            return f"File not found: {file_path}"

    # Read essential files for testing
    preferences_file = script_dir / 'knowledge' / 'user_preference.txt'
    user_preference_content = read_file_content(preferences_file)

    company_docs_dir = script_dir / 'company_docs'
    annual_report_path = company_docs_dir / 'annual_reports' / 'annual_report_2024.txt'
    annual_report_content = read_file_content(annual_report_path)

    inputs = {
        "topic": "Market Comparison Analysis",
        "current_year": str(datetime.now().year),
        'user_preference': user_preference_content,
        'annual_report_2024': annual_report_content,
        # Add other file contents as needed for testing
    }

    try:
        Marketcompare().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def test_json_extraction():
    """Test the JSON extraction logic with simulated crew output"""
    print("🧪 Testing JSON extraction logic...")
    
    # Simulate the crew output structure
    simulated_result = {
        "raw": '''{
            "_id": {"$oid": "5f3a8e046b912c7e8a5d3b24"},
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
                    },
                    {
                        "competitor": "Company B",
                        "product_line": "Project Management Software",
                        "price_range": "$180-$450"
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
            }
        }'''
    }
    
    # Test the extraction logic
    import json as _json
    import re
    
    raw_str = simulated_result['raw']
    raw_str = re.sub(r"```[a-zA-Z]*", "", raw_str).strip()
    
    try:
        forecast_json = _json.loads(raw_str)
        print("✅ JSON extraction successful!")
        print(f"   - Extracted keys: {list(forecast_json.keys())}")
        print(f"   - SWOT Analysis keys: {list(forecast_json['swot_analysis'].keys())}")
        print(f"   - Pricing Comparison keys: {list(forecast_json['pricing_comparison'].keys())}")
        
        # Test MongoDB storage
        uri = "mongodb+srv://Ali:suy4C1XDn5fHQOyd@nulibrarysystem.9c6hrww.mongodb.net/"
        db_name = "sample_db"
        collection_name = "Market_LLM_Output"
        
        # Remove _id to let MongoDB generate it
        if "_id" in forecast_json:
            forecast_json.pop("_id")
        
        inserted_id = save_output_to_mongodb(forecast_json, uri, db_name, collection_name)
        print(f"✅ Test data saved to MongoDB with ID: {inserted_id}")
        
    except Exception as e:
        print(f"❌ JSON extraction failed: {e}")
        raise

def test_clean_structure():
    """Test the clean structure transformation"""
    from bson import ObjectId
    from datetime import datetime
    
    # Simulate the complex crew output
    complex_output = {
        "_output": [
            {
                "name": "final_report_task",
                "raw": {
                    "_id": {"$oid": str(ObjectId())},
                    "swot_analysis": {
                        "strengths": ["Strong brand reputation", "Diverse product range"],
                        "weaknesses": ["Weak online presence", "Dependence on third-party suppliers"],
                        "opportunities": ["Expansion into emerging markets", "Increasing demand for eco-friendly products"],
                        "threats": ["Intense competition", "Changing regulatory environment"]
                    },
                    "pricing_comparison": {
                        "competitors": {
                            "TaskMaster Pro": "$19 per user per month",
                            "CollabSuite": "$29 per user per month"
                        }
                    },
                    "recommendations": {
                        "strategic_initiatives": ["Increase digital marketing efforts", "Form strategic partnerships"],
                        "immediate_actions": ["Invest in smart technology", "Enhance eco-friendly product lines"]
                    },
                    "market_analysis": {
                        "trends": [
                            {"name": "Rising interest in sustainable products"},
                            {"name": "Growth in smart home technology"}
                        ]
                    }
                }
            }
        ]
    }
    
    # Test the transformation
    uri = "mongodb+srv://Ali:suy4C1XDn5fHQOyd@nulibrarysystem.9c6hrww.mongodb.net/"
    db_name = "sample_db"
    collection_name = "Market_LLM_Output"
    
    print("🧪 Testing clean structure transformation...")
    save_output_to_mongodb(complex_output, uri, db_name, collection_name)
    print("✅ Test completed!")

def test_crew_compilation():
    """Test if the crew compiles and runs with minimal data"""
    print("🧪 Testing crew compilation...")
    
    # Minimal test inputs
    test_inputs = {
        'topic': 'Market Comparison Analysis',
        'current_year': str(datetime.now().year),
        'user_preference': 'Test user preference',
        'annual_report_2024': 'Test annual report content',
    }
    
    try:
        # Create crew instance
        crew_instance = Marketcompare().crew()
        print("✅ Crew instance created successfully")
        
        # Try to run with minimal data
        result = crew_instance.kickoff(inputs=test_inputs)
        print("✅ Crew execution completed")
        print(f"📊 Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"📋 Result keys: {list(result.keys())}")
            if '_output' in result:
                print(f"📝 Number of task outputs: {len(result['_output'])}")
                for i, output in enumerate(result['_output']):
                    print(f"  Task {i+1}: {output.get('name', 'Unknown')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Crew compilation/execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_b64

if __name__ == "__main__":
    # Uncomment to test crew compilation
    # test_crew_compilation()
    
    # Uncomment to test the clean structure
    # test_clean_structure()
    
    # Uncomment to test JSON extraction logic
    # test_json_extraction()
    
    run()
