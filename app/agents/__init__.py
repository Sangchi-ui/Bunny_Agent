from app.agents.cli_agent import CLIAgent

AGENTS = {
    "cli_agent": CLIAgent()
}

def get_agent(name: str):
    return AGENTS.get(name)
