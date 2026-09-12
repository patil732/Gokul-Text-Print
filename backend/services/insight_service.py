class InsightService:
    @staticmethod
    def generate_insights(data, decision, alerts):
        """
        Generates rule-based business insights from model decisions and alerts.
        """
        sales = data.get('sales', 0)
        growth = data.get('growth_rate', 0)
        trend = data.get('trend', 0)

        # 1. Summary Logic
        if growth > 0.1:
            summary = "Business is expanding rapidly with high demand growth."
        elif trend == -1:
            summary = "Business is facing a downward trend in recent cycles."
        else:
            summary = "Market performance remains steady with moderate fluctuations."

        # 2. Risk Level Logic
        if trend == -1 and sales < 5000:
            risk_level = "High"
        elif trend == -1 or sales < 5000:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # 3. Recommendation Logic
        if decision == "Increase Production":
            recommendation = "Scale up operations and optimize inventory for upcoming demand."
        else:
            recommendation = "Optimize current stock levels and focus on high-margin products to mitigate risk."

        return {
            "summary": summary,
            "risk_level": risk_level,
            "recommendation": recommendation
        }
