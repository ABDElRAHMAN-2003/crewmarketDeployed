from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import json
from datetime import datetime
import uuid


class SourcedItem(BaseModel):
    """Base model for items with source attribution."""
    content: str = Field(..., description="The actual content or data point")
    source: str = Field(...,
                        description="Source attribution in the format 'Source Name - Excerpt' or 'Information not available'")


class InitTaskOutput(BaseModel):
    """Output model for the initialization task."""
    target_company: str = Field(..., description="The target company to analyze")
    competitors: List[str] = Field(..., description="List of specific competitors to focus on")
    regions: List[str] = Field(..., description="Regions of interest for the analysis")
    key_metrics: List[str] = Field(..., description="Key metrics for competitive positioning")
    priorities: List[str] = Field(default_factory=list, description="User priorities or preferences")
    task_assignments: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Specific research tasks assigned to each specialized agent"
    )

    def json_str(self, **kwargs):
        """Return a formatted JSON string representation of the model."""
        return json.dumps(self.dict(), indent=2, **kwargs)


class InternalDataOutput(BaseModel):
    """Output model for the internal data analysis task."""
    company_strengths: List[SourcedItem] = Field(..., description="Company strengths with source attribution")
    company_weaknesses: List[SourcedItem] = Field(..., description="Company weaknesses with source attribution")
    product_details: List[SourcedItem] = Field(...,
                                               description="Current product/service details with source attribution")
    pricing_information: List[SourcedItem] = Field(..., description="Pricing information with source attribution")
    internal_strategies: List[SourcedItem] = Field(...,
                                                   description="Internal strategies and initiatives with source attribution")
    additional_information: Optional[List[SourcedItem]] = Field(default_factory=list,
                                                                description="Any other relevant internal information")

    def json_str(self, **kwargs):
        """Return a formatted JSON string representation of the model."""
        return json.dumps(self.dict(), indent=2, **kwargs)


class MarketTrend(BaseModel):
    """Model for market trend information."""
    name: str = Field(..., description="The trend name/description")
    growth_rate: Optional[str] = Field(default=None, description="Growth rate if available")
    impact: str = Field(..., description="Potential impact (high, medium, low)")
    source: str = Field(..., description="Source URL and publication/section")

    @validator('impact')
    def validate_impact(cls, v):
        """Validate that impact is one of the allowed values."""
        allowed_values = ['high', 'medium', 'low']
        if v.lower() not in allowed_values:
            raise ValueError(f"Impact must be one of {allowed_values}")
        return v.lower()


class MarketResearchOutput(BaseModel):
    """Output model for the market research task."""
    market_trends: List[MarketTrend] = Field(..., description="Current market trends in the industry")
    market_growth: List[SourcedItem] = Field(..., description="Market growth rates and projections")
    opportunities: List[SourcedItem] = Field(..., description="Emerging opportunities in the market")
    threats: List[SourcedItem] = Field(..., description="Potential threats to the market")
    market_share_data: Dict[str, str] = Field(...,
                                              description="Market share data for companies with source attribution")

    def json_str(self, **kwargs):
        """Return a formatted JSON string representation of the model."""
        return json.dumps(self.dict(), indent=2, **kwargs)


class CompetitorDetail(BaseModel):
    """Model for detailed competitor information."""
    pricing: List[SourcedItem] = Field(..., description="Product/service pricing information")
    discount_strategies: List[SourcedItem] = Field(..., description="Discount strategies and promotional offers")
    product_features: List[SourcedItem] = Field(..., description="Product features and specifications")
    customer_satisfaction: List[SourcedItem] = Field(..., description="Customer satisfaction metrics")
    innovation_indicators: List[SourcedItem] = Field(..., description="Innovation indicators")
    additional_information: Optional[List[SourcedItem]] = Field(default_factory=list,
                                                                description="Any other relevant information")


class CompetitorAnalysisOutput(BaseModel):
    """Output model for the competitor analysis task."""
    competitors: Dict[str, CompetitorDetail] = Field(..., description="Detailed information about each competitor")

    def json_str(self, **kwargs):
        """Return a formatted JSON string representation of the model."""
        return json.dumps(self.dict(), indent=2, **kwargs)


class SWOTAnalysis(BaseModel):
    """Model for SWOT analysis section."""
    strengths: List[SourcedItem] = Field(..., description="Company strengths with source attribution")
    weaknesses: List[SourcedItem] = Field(..., description="Company weaknesses with source attribution")
    opportunities: List[SourcedItem] = Field(..., description="Market opportunities with source attribution")
    threats: List[SourcedItem] = Field(..., description="Market threats with source attribution")


class PricingComparison(BaseModel):
    """Model for pricing comparison section."""
    competitors: Dict[str, str] = Field(..., description="Competitor pricing with source attribution")
    discount_strategies: List[SourcedItem] = Field(..., description="Common discount strategies in the market")


class CompetitivePositioning(BaseModel):
    """Model for competitive positioning section."""
    metrics: List[str] = Field(..., description="Metrics used for competitive positioning")
    scores: Dict[str, List[str]] = Field(..., description="Scores for each competitor based on metrics")
    visualization_note: str = Field(..., description="Visualization recommendation")


class MarketAnalysis(BaseModel):
    """Model for market analysis section."""
    trends: List[Dict[str, str]] = Field(..., description="Market trends with growth rates and impact assessments")
    market_share: Dict[str, str] = Field(..., description="Market share data with source attribution")


class DataSynthesisOutput(BaseModel):
    """Output model for the data synthesis task."""
    swot_analysis: SWOTAnalysis = Field(..., description="SWOT analysis section")
    pricing_comparison: PricingComparison = Field(..., description="Pricing comparison section")
    competitive_positioning: CompetitivePositioning = Field(..., description="Competitive positioning section")
    market_analysis: MarketAnalysis = Field(..., description="Market analysis section")

    def json_str(self, **kwargs):
        """Return a formatted JSON string representation of the model."""
        return json.dumps(self.dict(), indent=2, **kwargs)


class RecommendationOutput(BaseModel):
    """Output model for the recommendation task."""
    immediate_actions: List[SourcedItem] = Field(..., description="Short-term, tactical moves the company should make")
    strategic_initiatives: List[SourcedItem] = Field(...,
                                                     description="Longer-term, strategic moves for sustainable advantage")
    urgent_alerts: List[SourcedItem] = Field(..., description="Critical issues requiring immediate attention")

    def json_str(self, **kwargs):
        """Return a formatted JSON string representation of the model."""
        return json.dumps(self.dict(), indent=2, **kwargs)


class MongoId(BaseModel):
    """Model for MongoDB ObjectId structure."""
    oid: str = Field(default_factory=lambda: str(uuid.uuid4().hex[:24]), alias="$oid")

    class Config:
        populate_by_name = True  # Updated from allow_population_by_field_name


class FinalReportOutput(BaseModel):
    """Output model for the final report task matching the simple required structure."""
    ID: MongoId = Field(default_factory=MongoId, description="MongoDB-style ID")
    swot_analysis: Dict[str, List[str]] = Field(..., description="SWOT analysis with simple lists")
    pricing_comparison: Dict[str, List[Dict[str, str]]] = Field(..., description="Pricing comparison with competitor and our pricing")
    competitive_positioning: Dict[str, Any] = Field(..., description="Competitive positioning with market share and differentiators")
    market_analysis: Dict[str, Any] = Field(..., description="Market analysis with trends and behaviors")
    recommendations: Dict[str, List[str]] = Field(..., description="Recommendations with strategic moves and product development")

    def json_str(self, **kwargs):
        """Return a formatted JSON string representation of the model."""
        return json.dumps(self.dict(by_alias=True), indent=2, **kwargs)

    @classmethod
    def parse_json(cls, json_str):
        """Parse a JSON string into a FinalReportOutput instance."""
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def validate_json(cls, json_str):
        """Validate that a JSON string conforms to the FinalReportOutput schema."""
        try:
            data = json.loads(json_str)
            cls(**data)
            return True
        except Exception as e:
            return False, str(e)


class MarkdownReportOutput(BaseModel):
    """Output model for the PDF-ready HTML report task."""
    executive_summary: str = Field(..., description="Brief overview of key findings and recommendations")
    market_analysis: str = Field(..., description="Analysis of market trends, share data, and context")
    competitive_landscape: str = Field(..., description="Comparison of the target company against competitors")
    swot_analysis: str = Field(..., description="Strengths, weaknesses, opportunities, and threats")
    strategic_recommendations: str = Field(..., description="Actionable recommendations with rationale")
    appendix: str = Field(..., description="Additional data tables and references")
    full_report: str = Field(..., description="The complete HTML report content ready for PDF conversion")
    report_metadata: Dict[str, str] = Field(..., description="Report metadata including title, date, company")

    def save_to_file(self, file_path):
        """Save the full HTML report to a file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.full_report)
        return file_path
