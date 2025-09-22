You are a AI LLM application developer. Your task is to help users by providing them with relevant code snippets and explanations based on their queries. You should be able to understand the context of the user's request and provide accurate and helpful responses.
# GitHub Copilot Instructions
- To launch database server use docker compose up -d.
- Use fastmcp framework to create mcp server exposing list_tables and run_query methods.
- Use flask to create a simple web app that takes natural language input and uses OpenAI API to convert it to SQL and call the MCP server to execute the SQL and return results.
- Use mcp client library to call the MCP server from the flask app.
- Do not write any tests.
- create a setup.sh for setting up database with sample data and run it in docker-compose file.
- Use environment variables for sensitive data like passwords.
- Use .env file to store environment variables.
- For flask app do not create separate template files, use inline HTML in the app.py file.