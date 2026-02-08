import pandas as pd
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv

class TallyAnalyticsEngine:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=self.api_key,
            temperature=0
        )
        self.df = None
        self.agent = None

    def load_csv(self, file_path_or_buffer):
        """Load CSV data into a Pandas DataFrame"""
        try:
            self.df = pd.read_csv(file_path_or_buffer)
            # Basic cleaning: strip whitespace from column names
            self.df.columns = [c.strip() for c in self.df.columns]
            
            # Initialize agent
            self.agent = create_pandas_dataframe_agent(
                self.llm,
                self.df,
                verbose=True,
                allow_dangerous_code=True, # Required for pandas agent to run code
                handle_parsing_errors=True
            )
            return True, f"Loaded {len(self.df)} rows."
        except Exception as e:
            return False, f"Error loading CSV: {str(e)}"

    def ask(self, query):
        """Ask a data analysis question"""
        if self.agent is None:
            return "No data loaded! Please upload a CSV first."
        
        try:
            # Custom prompt prefix to guide the agent
            prefix = (
                "You are a Tally data analyst expert. The user is asking about financial data "
                "exported from Tally. Use the provided dataframe to answer accurately. "
                "Calculations should be precise. If a column looks like a date, treat it as such. "
                "If searching for specific names, be case-insensitive."
            )
            
            response = self.agent.invoke({"input": f"{prefix}\n\nQuestion: {query}"})
            return response["output"]
        except Exception as e:
            return f"Error analyzing data: {str(e)}"

    def get_summary(self):
        """Get basic summary of the loaded data"""
        if self.df is None:
            return None
        
        return {
            "columns": list(self.df.columns),
            "rows": len(self.df),
            "preview": self.df.head(5)
        }
