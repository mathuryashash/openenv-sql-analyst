import os
import uvicorn
from fastapi import FastAPI
from environment.env import SQLAnalystEnv
from environment.models import Action

# Initialize the API and our RL Environment
app = FastAPI(title="OpenEnv SQL Analyst")
env = SQLAnalystEnv()

@app.get("/")
def health_check():
    """Hackathon requirement: Ping must return 200 OK"""
    return {"status": "ok", "message": "OpenEnv SQL Analyst is live!"}

@app.post("/reset")
def reset():
    """Hackathon requirement: Must respond to reset()"""
    return env.reset()

@app.post("/step")
def step(action: Action):
    """Executes the agent's action and returns the new state"""
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info
    }

@app.get("/state")
def state():
    return env.state()

def main():
    print("🚀 Starting OpenEnv Production Server on port 7860...")
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()