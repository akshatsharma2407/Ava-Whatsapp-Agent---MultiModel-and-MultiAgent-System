from langchain_tavily import TavilySearch
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain.tools import tool
from email.message import EmailMessage
import smtplib
from langchain.messages import HumanMessage
from ai_companion.settings import settings
# delay importing graph to avoid circular import with nodes/chains
# create_subgraph is only needed when the tool is executed, so import inside the function
from ai_companion.graph.utils.helpers import get_db


search_tool = TavilySearch(max_results=2)

@tool
def send_sales_email(recipient_email: str, subject: str, body: str):
    """
    Sends a professional sales email to a specific recipient.
    Use this only after the SQL query results are processed into a pitch.
    """
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['To'] = recipient_email
    msg['From'] = "akshatsharma5877@gmail.com"

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("akshatsharma5877@gmail.com", settings.gmail_password)
            smtp.send_message(msg)
        return "Email sent successfully!"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

@tool
def run_query(query):
    """This function takes the query as input and execute the command and return results from DB"""
    print(f"Query being run: {query}\n")
    return get_db().run(query)

@tool
def ava_sql_data_assistant(user_query: str) -> str:
    """
    Pass the user's ORIGINAL NATURAL LANGUAGE request to the internal Data Team.
    
    CRITICAL: 
    1. Do NOT write SQL code. 
    2. Do NOT attempt to format the request as a database query. 
    3. Simply pass the user's raw intent (e.g., 'Who are the top 5 artists?').
    4. The internal team handles all SQL generation and execution.
    """
    
    initial_state = {"messages": [HumanMessage(content=user_query)]}
    
    try:
        # import here to avoid circular imports when module is first loaded
        from ai_companion.graph.graph import create_subgraph
        final_state = create_subgraph().compile().invoke(initial_state)
            
    except Exception as e:
        return f"The database tool encountered an error: {str(e)}"
    else:
        return final_state

tools = [search_tool, ava_sql_data_assistant]
tool_node = ToolNode(tools)