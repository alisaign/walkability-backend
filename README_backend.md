# Walkability Index – Backend

## How to Run

1. **Go to backend folder**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # Activate:
   venv\Scripts\activate     # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start FastAPI server**
   ```bash
   uvicorn main:app --reload
   ```

5. **Open in browser**
   ```
   http://127.0.0.1:8000/docs
   ```

The API will now be running locally and ready to receive requests from the frontend.
