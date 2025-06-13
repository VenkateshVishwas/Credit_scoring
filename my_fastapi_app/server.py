import os
import pandas as pd
from datetime import datetime
import ollama
from typing import Dict, Any, Optional

# main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "docs")

from fastapi import FastAPI, Request
from pydantic import BaseModel
# from logic import process_query

app = FastAPI()

class QueryRequest(BaseModel):
    query: str


@app.on_event("startup")
async def startup_event():
    if test_system():
        print("\n" + "="*50)
        run_credit_agent()
    else:
        raise RuntimeError("System test failed. Please check your data files and Ollama installation.")
    
    
@app.post("/process")
async def process(request: QueryRequest):
    response = process_user_query(request.query)
    return {"result": response}


# ---------------------------
# 1️⃣ DATA PREPROCESSING
# ---------------------------

def parse_timestamp(df):
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['month'] = df['timestamp'].dt.to_period('M')
    return df

def agent_1_utilities_rent_telecom():
    try:
        users_df = pd.read_csv(os.path.join(DATA_DIR, "users.csv"))
        loc_df = pd.read_csv(os.path.join(DATA_DIR, "location_data.csv"))
        bill_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "bill_payments.csv")))
        rent_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "inferred_rent_payments.csv")))
        telecom_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "telecom_usage.csv")))

        utility_spend = bill_df.groupby(['user_id', 'month'])['amount'].sum().reset_index(name='monthly_utility_spend')
        rent_avg = rent_df.groupby('user_id')['amount'].mean().reset_index(name='avg_rent_payment')
        telecom_avg = telecom_df.groupby('user_id')[['monthly_data_usage_gb', 'monthly_recharge_amount']].mean().reset_index()

        agent1_df = users_df.merge(utility_spend, on='user_id', how='left') \
                           .merge(rent_avg, on='user_id', how='left') \
                           .merge(telecom_avg, on='user_id', how='left') \
                           .merge(loc_df, on='user_id', how='left')

        return agent1_df.fillna(0)
    except Exception as e:
        print(f"Error in agent_1_utilities_rent_telecom: {e}")
        return pd.DataFrame()

def agent_2_financials():
    try:
        users_df = pd.read_csv(os.path.join(DATA_DIR, "users.csv"))
        loc_df = pd.read_csv(os.path.join(DATA_DIR, "location_data.csv"))
        upi_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "upi_transactions.csv")))
        wallet_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "wallet_balances.csv")))
        fin_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "financial_transactions.csv")))
        gig_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "gig_income.csv")))
        salary_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "salary_income.csv")))
        loan_df = pd.read_csv(os.path.join(DATA_DIR, "loan_history.csv"))

        upi_total = upi_df.groupby('user_id')['amount'].sum().reset_index(name='upi_total_spent')
        wallet_bal = wallet_df.groupby(['user_id', 'wallet_type'])['balance_amount'].last().unstack().fillna(0).reset_index()
        fin_total = fin_df.groupby('user_id')['amount'].sum().reset_index(name='total_transactions')
        gig_income = gig_df.groupby('user_id')['amount'].sum().reset_index(name='gig_income_total')
        salary = salary_df.groupby('user_id')['amount'].mean().reset_index(name='avg_salary')

        agent2_df = users_df.merge(upi_total, on='user_id', how='left') \
                           .merge(wallet_bal, on='user_id', how='left') \
                           .merge(fin_total, on='user_id', how='left') \
                           .merge(gig_income, on='user_id', how='left') \
                           .merge(salary, on='user_id', how='left') \
                           .merge(loan_df, on='user_id', how='left') \
                           .merge(loc_df, on='user_id', how='left')

        return agent2_df.fillna(0)
    except Exception as e:
        print(f"Error in agent_2_financials: {e}")
        return pd.DataFrame()

def agent_3_ecommerce():
    try:
        users_df = pd.read_csv(os.path.join(DATA_DIR, "users.csv"))
        loc_df = pd.read_csv(os.path.join(DATA_DIR, "location_data.csv"))
        ecommerce_df = parse_timestamp(pd.read_csv(os.path.join(DATA_DIR, "ecommerce_activity.csv")))

        monthly_spend = ecommerce_df.groupby(['user_id', 'month'])['amount'].sum().reset_index(name='monthly_ecom_spend')
        return users_df.merge(monthly_spend, on='user_id', how='left') \
                       .merge(loc_df, on='user_id', how='left') \
                       .fillna(0)
    except Exception as e:
        print(f"Error in agent_3_ecommerce: {e}")
        return pd.DataFrame()

def master_agent(user_query="Generate score"):
    try:
        df1 = agent_1_utilities_rent_telecom()
        df2 = agent_2_financials()
        df3 = agent_3_ecommerce()

        if df1.empty or df2.empty or df3.empty:
            print("Warning: Some agent data is missing")
            return pd.DataFrame()

        string_columns = ['user_id', 'name']
        context_df = df1[string_columns].drop_duplicates()

        df1_num = df1.groupby('user_id').mean(numeric_only=True).reset_index()
        df2_num = df2.groupby('user_id').mean(numeric_only=True).reset_index()
        df3_num = df3.groupby('user_id').mean(numeric_only=True).reset_index()

        final_numeric = df1_num.merge(df2_num, on='user_id', how='outer') \
                             .merge(df3_num, on='user_id', how='outer')

        final = final_numeric.merge(context_df.drop_duplicates('user_id'), on='user_id', how='left') \
                           .merge(pd.read_csv(os.path.join(DATA_DIR, "location_data.csv")).drop_duplicates('user_id'), on='user_id', how='left')

        return final
    except Exception as e:
        print(f"Error in master_agent: {e}")
        return pd.DataFrame()


# ---------------------------
# 2️⃣ LLM CREDIT SCORING FUNCTIONS
# ---------------------------

def check_ollama_connection(model='gemma3:4b') -> bool:
    """Check if Ollama is running and model is available"""
    try:
        response = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': 'Hello'}]
        )
        return True
    except Exception as e:
        print(f"Ollama connection failed: {e}")
        return False

def get_credit_score_from_llm(user_data: dict, model='gemma3:4b') -> str:
    """Get credit score using LLM with fallback to rule-based scoring"""
    
    # Try LLM first
    if check_ollama_connection(model):
        try:
            summary = "\n".join([f"{k}: {v}" for k, v in user_data.items() if isinstance(v, (int, float, str))])
            
            prompt = f"""
You are an AI financial analyst specializing in alternative credit scoring for underserved communities.
Assess creditworthiness based on the following user data and provide:
1. A credit score out of 100
2. Key factors that influenced the score
3. Brief reasoning

User data:
{summary}
"""
            response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': 'You assess credit risk based on alternative data such as utility bills, telecom usage, digital transactions, and location stability.'},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f"LLM scoring failed, using rule-based fallback: {e}")
    
    # Fallback to rule-based scoring
    return get_rule_based_credit_score(user_data)

def get_rule_based_credit_score(user_data: dict) -> str:
    """Rule-based credit scoring as fallback when LLM is unavailable"""
    score = 50  # Base score
    factors = []
    
    # Income factors
    avg_salary = user_data.get('avg_salary', 0)
    gig_income = user_data.get('gig_income_total', 0)
    
    if avg_salary > 20000:
        score += 15
        factors.append("High salary income (+15)")
    elif avg_salary > 10000:
        score += 8
        factors.append("Moderate salary income (+8)")
    
    if gig_income > 5000:
        score += 10
        factors.append("Additional gig income (+10)")
    
    # Payment behavior
    utility_spend = user_data.get('monthly_utility_spend', 0)
    if 0 < utility_spend < 2000:
        score += 12
        factors.append("Regular utility payments (+12)")
    elif utility_spend > 3000:
        score -= 8
        factors.append("High utility expenses (-8)")
    
    # Digital activity
    upi_total = user_data.get('upi_total_spent', 0)
    if upi_total > 5000:
        score += 8
        factors.append("Active digital transactions (+8)")
    
    # Location stability
    location_stability = user_data.get('location_stability', '')
    if location_stability == 'high':
        score += 10
        factors.append("High location stability (+10)")
    elif location_stability == 'medium':
        score += 5
        factors.append("Medium location stability (+5)")
    
    # Loan history
    outstanding_amount = user_data.get('outstanding_amount', 0)
    on_time_repayments = user_data.get('on_time_repayments', 0)
    
    if outstanding_amount > 30000:
        score -= 15
        factors.append("High outstanding debt (-15)")
    elif outstanding_amount > 10000:
        score -= 8
        factors.append("Moderate outstanding debt (-8)")
    
    if on_time_repayments > 0.8:
        score += 12
        factors.append("Good repayment history (+12)")
    elif on_time_repayments > 0.5:
        score += 6
        factors.append("Fair repayment history (+6)")
    
    # Cap the score between 0 and 100
    score = max(0, min(100, score))
    
    assessment = f"""
**RULE-BASED CREDIT ASSESSMENT**
Credit Score: {score}/100

Key Factors:
{chr(10).join([f'• {factor}' for factor in factors])}

Risk Level: {'Low' if score >= 70 else 'Medium' if score >= 50 else 'High'}

Note: This assessment is based on alternative data sources including utility payments, 
digital transaction patterns, income sources, and location stability.
"""
    
    return assessment


# ---------------------------
# 3️⃣ SIMPLIFIED QUERY PROCESSOR
# ---------------------------

def process_user_query(query: str, model='gemma3:4b') -> str:
    """
    Process user query and return appropriate response
    """
    query_lower = query.lower()
    
    try:
        # Handle different types of queries
        if 'list' in query_lower and 'user' in query_lower:
            return list_available_users()
        
        elif 'credit score' in query_lower or 'assess' in query_lower or 'creditworthiness' in query_lower:
            # Try to extract user name from query
            master_data = master_agent()
            if master_data.empty:
                return "Error: Unable to load user data. Please check if CSV files are available."
            
            # Look for user names in the query
            user_found = None
            for _, row in master_data.iterrows():
                if pd.notna(row['name']) and row['name'].lower() in query_lower:
                    user_found = row['name']
                    break
            
            if user_found:
                return get_user_credit_assessment(user_found)
            else:
                return f"Please specify a user name. Available users: {list_available_users()}"
        
        elif 'help' in query_lower:
            return get_help_message()
        
        else:
            # General query - try to use LLM if available
            if check_ollama_connection(model):
                try:
                    master_data = master_agent()
                    data_summary = f"System has {len(master_data)} users with financial and alternative credit data."
                    
                    prompt = f"""
You are a credit scoring assistant. The user asked: {query}

Available data: {data_summary}

Please provide a helpful response about credit scoring, user assessment, or system capabilities.
"""
                    response = ollama.chat(
                        model=model,
                        messages=[
                            {'role': 'system', 'content': 'You are an expert in alternative credit scoring for underserved populations.'},
                            {'role': 'user', 'content': prompt}
                        ]
                    )
                    return response['message']['content']
                except Exception as e:
                    return f"Error processing query with LLM: {e}"
            else:
                return "I can help you with credit scoring queries. Try asking about specific users or type 'help' for available commands."
    
    except Exception as e:
        return f"Error processing query: {e}"

def get_user_credit_assessment(name: str) -> str:
    """Get credit assessment for a specific user"""
    try:
        result_df = master_agent()
        if result_df.empty:
            return "Error: Unable to load user data."
        
        user_data = result_df[result_df['name'].str.contains(name, case=False, na=False)]
        
        if user_data.empty:
            available_users = result_df['name'].dropna().tolist()[:10]
            return f"No user found matching '{name}'. Available users: {', '.join(available_users)}"
        
        user_row = user_data.iloc[0].to_dict()
        llm_result = get_credit_score_from_llm(user_row)
        
        return f"""
Credit Assessment for: {user_row['name']}
{'='*50}
{llm_result}
"""
    except Exception as e:
        return f"Error generating assessment for {name}: {str(e)}"

def list_available_users() -> str:
    """List all available users"""
    try:
        users_df = pd.read_csv(os.path.join(DATA_DIR, "users.csv"))
        users = users_df['name'].dropna().tolist()
        return f"Available users ({len(users)}): {', '.join(users[:20])}" + \
               (f" ... and {len(users)-20} more" if len(users) > 20 else "")
    except Exception as e:
        return f"Error listing users: {str(e)}"

def get_help_message() -> str:
    """Return help message with available commands"""
    return """
Available Commands:
==================
• "assess [user name]" or "credit score for [user name]" - Get credit assessment
• "list users" - Show all available users
• "help" - Show this help message

Examples:
• "What is the credit score for John Doe?"
• "Assess creditworthiness of Jane Smith"
• "List all users"

Note: If Ollama is not running, the system will use rule-based scoring as fallback.
"""


# ---------------------------
# 4️⃣ MAIN INTERFACE
# ---------------------------

def run_credit_agent():
    """Main interface for the credit scoring agent"""
    print("=== Credit Scoring Agent ===")
    print("Type 'help' for available commands or 'exit' to quit")
    
    # Check system status
    ollama_status = "✓ Connected" if check_ollama_connection() else "✗ Not available (using rule-based fallback)"
    print(f"Ollama LLM Status: {ollama_status}")
    
    try:
        master_data = master_agent()
        print(f"Data Status: ✓ Loaded {len(master_data)} users")
    except Exception as e:
        print(f"Data Status: ✗ Error loading data: {e}")
        return
    
    print("-" * 50)
    
    # while True:
    #     try:
    #         question = input("\nEnter query: ").strip()
            
    #         if question.lower() == 'exit':
    #             print("Goodbye!")
    #             break
            
    #         if not question:
    #             print("Please enter a valid query.")
    #             continue
            
    #         print("\nProcessing...")
    #         response = process_user_query(question)
    #         print(f"\nResponse:\n{response}")
    #         print("-" * 50)
            
    #     except KeyboardInterrupt:
    #         print("\nGoodbye!")
    #         break
    #     except Exception as e:
    #         print(f"Error: {e}")


# ---------------------------
# 5️⃣ TESTING FUNCTIONS
# ---------------------------

def test_system():
    """Test the system functionality"""
    print("Testing Credit Scoring System...")
    
    # Test data loading
    try:
        master_data = master_agent()
        print(f"✓ Data loaded successfully: {len(master_data)} users")
    except Exception as e:
        print(f"✗ Data loading failed: {e}")
        return False
    
    # Test LLM connection
    if check_ollama_connection():
        print("✓ Ollama LLM connected")
    else:
        print("✗ Ollama LLM not available, will use rule-based fallback")
    
    # Test a sample assessment
    if not master_data.empty:
        sample_user = master_data.iloc[0]['name']
        print(f"\nTesting assessment for: {sample_user}")
        result = get_user_credit_assessment(sample_user)
        print("✓ Assessment completed")
        print(result[:200] + "..." if len(result) > 200 else result)
    
    return True


if __name__ == '__main__':
    # Run system test first
    if test_system():
        print("\n" + "="*50)
        run_credit_agent()
    else:
        print("System test failed. Please check your data files and Ollama installation.")