# 🛍️ AI E-Commerce Customer Support Agent

Welcome to your first coding project! This application is an intelligent customer support chatbot designed to help shoppers with order tracking, product recommendations, and FAQs.

---

## 📁 Project Structure

```text
AI CUSTOMER SUPPORT/
├── app.py             # The web chat screen built with Streamlit
├── agent.py           # The AI logic connecting to the OpenAI API
├── database.py        # The SQLite database handling orders & store data
├── requirements.txt   # List of external Python packages required
├── .env.example       # Example file showing where your API key goes
├── .gitignore         # Tells Git which sensitive or auto-generated files to ignore
└── README.md          # Guide and setup instructions (this file)
```

---

## 🪟 Windows Setup Instructions (Step-by-Step)

Follow these simple steps in your terminal (PowerShell or Command Prompt) inside this project folder:

### Step 1: Make sure Python is installed
Open your terminal and type:
```powershell
python --version
```
*(If you see `Python 3.x.x`, you are ready!)*

---

### Step 2: Create an isolated environment ("Virtual Environment")
A virtual environment is like a clean, separate sandbox for this project so its tools don't interfere with other programs on your computer.

```powershell
python -m venv venv
```
*(This will create a new folder named `venv` in your project.)*

---

### Step 3: Activate your virtual environment
Whenever you work on this project, turn on the sandbox:

```powershell
venv\Scripts\activate
```
*(You will see `(venv)` appear at the beginning of your terminal prompt line.)*

---

### Step 4: Install the project tools
Install all required libraries with one command:

```powershell
pip install -r requirements.txt
```

---

### Step 5: Set up your OpenAI API Key
1. Make a copy of `.env.example` and name the new file `.env`.
2. Open `.env` and replace `your_openai_api_key_here` with your real OpenAI API key.

---

### Step 6: Run the web application
When we finish writing the code in the upcoming steps, you will launch the app with:

```powershell
streamlit run app.py
```
This will open your browser automatically to show your chatbot!
