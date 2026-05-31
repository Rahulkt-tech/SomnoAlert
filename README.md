# SomnoAlert Sleep Detector

This project uses Flask to serve a web user interface for the sleep detection app.

## How to run

1. Install dependencies:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Start the Flask backend:
   ```powershell
   .\.venv\Scripts\python.exe sleep_detector.py
   ```

3. Open the front-end in Live Server:
   - Serve `index.html` from the project root.
   - Open the Live Server page, for example `http://127.0.0.1:5500/index.html`.

4. Press `Start Detection` in the browser. The browser will ask for camera permission.

> The backend must be running on `http://127.0.0.1:5000` before the Live Server UI can talk to it.

## Notes

- The Flask app serves `templates/index.html` and `static/style.css`.
- Use the `Start Detection` button in the web UI to begin camera monitoring.
- The app also opens the browser automatically when it starts.
