#!/bin/bash

# RikSahyak Auto-Updater (Git Poller)
# This script runs in the background and checks GitHub every 60 seconds.
# If a new commit is detected on the 'main' branch, it pulls the changes
# and restarts the FastAPI server automatically.

cd ~/RikSahyak || exit

echo "Starting RikSahyak Auto-Updater..."

while true; do
    # Fetch the latest remote info without merging
    git fetch origin main >/dev/null 2>&1
    
    # Compare local HEAD with remote main branch
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "[$(date)] Update detected! Local: $LOCAL | Remote: $REMOTE"
        echo "Pulling latest code from GitHub..."
        
        # Pull the new code
        git pull origin main
        
        # Optional: if requirements.txt changed, we could run pip install here
        # ./backend/venv/bin/pip install -r backend/requirements.txt
        
        echo "Restarting the RikSahyak API server..."
        cd backend || exit
        pm2 restart riksahyak-api
        
        echo "[$(date)] Update applied and server restarted successfully!"
        cd ~/RikSahyak || exit
    fi
    
    # Wait for 60 seconds before checking again
    sleep 60
done
