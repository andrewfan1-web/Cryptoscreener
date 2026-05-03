Perfect. I have confirmed your local folder and the IP address. Let's do this step-by-step.

  Step 1: Clean the Server
  We will SSH into the server and delete the ~/app directory entirely to get rid of the accidental files.

  In your PowerShell:

   1 # Log in to the server
   2 ssh -i .\ssh-key-2026-05-02.key ubuntu@152.69.171.16

  Once you are logged into the server (Ubuntu prompt), type this:

   1 # Delete the messy directory
   2 rm -rf ~/app
   3
   4 # Create a clean one
   5 mkdir ~/app
   6
   7 # Exit the server
   8 exit

  ---

  Step 2: Upload Only the Bot Files
  Now that the server is clean, run this from your local PowerShell to upload just the code. I've specifically selected the folders and files needed.

  In your PowerShell:

   1 scp -i .\ssh-key-2026-05-02.key -r main.py, requirements.txt, Dockerfile, docker-compose.yml, .env, src, tests ubuntu@152.69.171.16:~/app

  ---

  Step 3: Server Re-Setup (The "Always Free" AMD Optimization)
  Log back in and run the setup script to prepare the environment.

  In your PowerShell:

   1 ssh -i .\ssh-key-2026-05-02.key ubuntu@152.69.171.16

  Once logged in, copy and paste this entire block:

    1 # 1. Add 2GB Swap (Essential for your 1GB RAM)
    2 sudo fallocate -l 2G /swapfile && \
    3 sudo chmod 600 /swapfile && \
    4 sudo mkswap /swapfile && \
    5 sudo swapon /swapfile && \
    6 echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    7
    8 # 2. Install Docker
    9 sudo apt update && \
   10 sudo apt install -y docker.io docker-compose && \
   11 sudo usermod -aG docker $USER
   12
   13 # 3. Apply group changes (so you can use docker)
   14 newgrp docker

  ---

  Step 4: Start the Engine
  Finally, start your bot.

  Once logged in, run:

   1 cd ~/app
   2
   3 # Build and start
   4 docker-compose up -d --build
   5
   6 # Check that it started correctly
   7 docker-compose logs -f app

  Tell me if you see any error messages in the logs!