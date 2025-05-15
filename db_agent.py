import psycopg2
from openai import OpenAI
from config import OPENAI_API_KEY, DB_CONFIG
import json
from typing import List, Dict
from datetime import datetime, date, time
from decimal import Decimal

class DatabaseAgent:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.db_connection = None
        self.connect_to_db()
        self.conversation_history: List[Dict] = [
            {"role": "system", "content": "You are a helpful database assistant. You can execute SQL queries to explore and analyze the database. Remember previous interactions and use that context to provide more relevant responses."}
        ]
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_query",
                    "description": "Execute a SQL query on the PostgreSQL database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query to execute."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def connect_to_db(self):
        """Establish connection to the PostgreSQL database"""
        try:
            self.db_connection = psycopg2.connect(**DB_CONFIG)
            print("Successfully connected to the database")
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            raise

    def serialize_value(self, value):
        """Serialize different types of values to JSON-compatible format"""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, time):
            return value.strftime('%H:%M:%S')
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (list, tuple)):
            return [self.serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}
        return value

    def execute_query(self, query):
        """Execute a SQL query and return the results"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            if cursor.description:  # If the query returns data
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                # Serialize each row of results
                serialized_results = [
                    [self.serialize_value(value) for value in row]
                    for row in results
                ]
                cursor.close()
                return json.dumps({
                    "columns": columns,
                    "results": serialized_results
                })
            else:  # If the query doesn't return data (e.g., INSERT, UPDATE)
                self.db_connection.commit()
                cursor.close()
                return json.dumps({"message": "Query executed successfully"})
        except Exception as e:
            print(f"Error executing query: {e}")
            self.db_connection.rollback()
            return json.dumps({"error": str(e)})

    def get_ai_response(self, prompt):
        """Get a response from OpenAI's API with tool calls"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.conversation_history,
                tools=self.tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Add assistant's message to conversation history
            self.conversation_history.append(message)
            
            # Handle tool calls if present
            if message.tool_calls:
                tool_calls = message.tool_calls
                tool_responses = []
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "execute_query":
                        result = self.execute_query(function_args["query"])
                    else:
                        result = json.dumps({"error": f"Unknown function: {function_name}"})
                    
                    tool_responses.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": result
                    })
                
                # Add tool responses to conversation history
                for tr in tool_responses:
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tr["tool_call_id"],
                        "name": tr["name"],
                        "content": tr["content"]
                    })
                
                # Get final response with tool results
                final_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self.conversation_history
                )
                
                # Add final response to conversation history
                final_message = final_response.choices[0].message
                self.conversation_history.append(final_message)
                
                return final_message.content
            
            return message.content
            
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return None

    def clear_memory(self):
        """Clear the conversation history"""
        self.conversation_history = [
            {"role": "system", "content": "You are a helpful database assistant. You can execute SQL queries to explore and analyze the database. Remember previous interactions and use that context to provide more relevant responses."}
        ]

    def close(self):
        """Close the database connection"""
        if self.db_connection:
            self.db_connection.close()
            print("Database connection closed")

def main():
    print("Welcome to the Database AI Agent!")
    print("You can ask questions about your database or request operations.")
    print("Type 'exit' or 'quit' to end the session.")
    print("Type 'clear' to clear the conversation history.")
    print("-" * 50)
    
    agent = DatabaseAgent()
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                # Check for exit command
                if user_input.lower() in ['exit', 'quit']:
                    print("\nGoodbye!")
                    break
                
                # Check for clear memory command
                if user_input.lower() == 'clear':
                    agent.clear_memory()
                    print("\nConversation history cleared.")
                    continue
                
                # Skip empty inputs
                if not user_input:
                    continue
                
                # Get AI response
                print("\nAgent: ", end="")
                response = agent.get_ai_response(user_input)
                if response:
                    print(response)
                else:
                    print("I apologize, but I encountered an error processing your request.")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")
                print("Please try again or type 'exit' to quit.")
    
    finally:
        agent.close()

if __name__ == "__main__":
    main() 