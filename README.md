
# 🛠 Oracle_Cloud_Out_Of_Capacity_Script

A complete guide to deploy a Python bot that helps monitor and respond to Oracle Cloud "Out of Capacity" errors. This guide covers everything from bot setup to script execution across Windows and Linux.

---

## 🌐 Creating VCN and Subnet (Optional)

- **Destination CIDR Block**: `0.0.0.0/0`

---

## 🤖 Bot Configuration

- Use [**@BotFather**](https://t.me/BotFather) to create your Telegram bot and get the API token.
- Use [**@MissRose_bot**](https://t.me/MissRose_bot) if needed for group management or automation tasks.

Edit your `bot.py` file with the appropriate credentials and logic.

---

## 📁 Creating a GitHub Account & Repository

- **Sign up for GitHub**: [https://github.com/signup](https://github.com/signup)

You can clone this repository and modify it as needed.

---

## 💻 Running the Script

### 🪟 Windows Setup

1. **Download Python**: [https://www.python.org/](https://www.python.org/)
2. **Login to GitHub**: [https://github.com/login](https://github.com/login)
3. **Open Command Prompt**: `cmd`
4. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the Script**:
   ```bash
   python bot.py
   ```

---

### 🐧 Linux Setup

1. **Switch to Root**:
   ```bash
   sudo -i
   ```

2. **Update Packages**:
   ```bash
   apt-get update -y && apt-get upgrade -y
   ```

3. **Install Python3, pip, screen, and git**:
   ```bash
   apt-get install python3 python3-pip screen git -y
   ```

4. **Clone Repository**:
   ```bash
   git clone https://github.com/your-username/Oracle_Cloud_Out_Of_Capacity_Script.git
   ```

5. **Navigate to the Folder**:
   ```bash
   cd Oracle_Cloud_Out_Of_Capacity_Script
   ```

6. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

---

### ⚙️ Fix Common Errors

**Fix pip issues**:
```bash
apt-get remove python3-pip -y
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
sudo reboot
```

**Fix pyOpenSSL upgrade**:
```bash
pip install pyopenssl --upgrade
```

---

### 🧪 Run & Monitor Script

1. **Test Script**:
   ```bash
   python3 bot.py
   ```

2. **Run in Background with Screen**:
   ```bash
   screen
   python3 bot.py
   ```

3. **Reattach to Screen Session**:
   ```bash
   screen -r
   ```

---

> ✨ Make sure to update `bot.py` with your Bot API key and logic before running the script.
