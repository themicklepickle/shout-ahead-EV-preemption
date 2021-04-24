## 1. Create GCP Instance

- location: `us-west1`
- zone: `us-west1-b`
- machine type: `2 cores, 1 GB memory`
- boot disk: `Ubuntu 20.04 LTS`
- firewall: `Allow HTTP traffic, Allow HTTPS traffic`

## 2. Setup SSH from iTerm to GCP instance

### Create new SSH key

- `ssh-keygen -t rsa -f ~/.ssh/[INSTANCE NAME] -C michael`
- `chmod 400 ~/.ssh/[INSTANCE NAME]`

### Add SSH key to GCP instance

- open the public SSH key file located at `~/.ssh/[INSTANCE NAME].pub`
- copy its content
- navigate to the [GCP console](https://console.cloud.google.com/compute/instances?authuser=1&project=virtual-machine-301620&instancessize=50)
- click on the name of the instance
- click `EDIT`
- scroll down to `SSH Keys`
- paste the public SSH key content
- click `Save`
- copy the external IP of the instance (for the next step)

### Add iTerm profile

- duplicate existing VM profile
- change commmand to `ssh -i /Users/Michael/.ssh/[INSTANCE NAME] michael@[EXTERNAL IP]`
- set shortcut

## 3. Configure Instance

### Install Python3.8

- `sudo apt update`
- `sudo apt install software-properties-common`
- `sudo add-apt-repository ppa:deadsnakes/ppa`
- `sudo apt update`
- `sudo apt install python3.8`
- `sudo apt install python3-pip`
- or all together:
  ```
  sudo apt update &&
  sudo apt install software-properties-common &&
  sudo add-apt-repository ppa:deadsnakes/ppa &&
  sudo apt update &&
  sudo apt install python3.8 &&
  sudo apt install python3-pip
  ```

### Install SUMO

- `sudo add-apt-repository ppa:sumo/stable`
- `sudo apt-get update`
- `sudo apt-get install sumo sumo-tools sumo-doc`
- or all together:
  ```
  sudo add-apt-repository ppa:sumo/stable &&
  sudo apt-get update &&
  sudo apt-get install sumo sumo-tools sumo-doc
  ```

### Clone git repo

- `git clone https://github.com/themicklepickle/ASP.git ASP`
- `cd ASP`
- `git pull origin [BRANCH]`
- or all together:
  ```
  git clone https://github.com/themicklepickle/shout-ahead-EV-preemption.git ASP &&
  cd ASP &&
  git pull origin [BRANCH]
  ```

### Install Python modules

- `pip3 install -r requirements.txt`

### Load Environment Variables

- copy content of local `.env`
- `vim .env`
- paste copied content
- type `ESC`
- type `:wq`

## 4. Run Simulation

### Create new tmux session

- `tmux new -s l`

### Run simulation

- `python3 main.py`

## ALL THE SETUP

```
sudo apt update &&
sudo apt install software-properties-common &&
sudo add-apt-repository ppa:deadsnakes/ppa -y &&
sudo apt update &&
sudo apt install python3.8 -y &&
sudo apt install python3-pip -y &&
sudo add-apt-repository ppa:sumo/stable -y &&
sudo apt-get update &&
sudo apt-get install sumo sumo-tools sumo-doc -y &&
git clone https://github.com/themicklepickle/shout-ahead-EV-preemption.git ASP &&
cd ASP &&
pip3 install -r requirements.txt &&
tmux new -s l &&
vim credentials.json
```
