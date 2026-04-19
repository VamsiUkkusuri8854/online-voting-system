# 🗳️ VoteSafe: Secure Online Voting System

A professional, high-fidelity digital voting platform built with security and user experience at its core. VoteSafe utilizes **JWT Authentication**, **MongoDB** for persistent record-keeping, and a modern **Glassmorphism UI** to provide an intuitive yet robust election management experience.

---

## 🌟 Key Features

### 🤵 For Users
- **Secure Authentication**: High-security login system using JWT (JSON Web Tokens) and Bcrypt password hashing.
- **Democratic Participation**: Browse registered candidates and cast your vote with a single click.
- **Candidacy Requests**: Aspiring leaders can request to join the election directly from their dashboard.
- **Real-time Status**: Live countdown timer for election duration and instant verification of your cast vote.

### 🛡️ For Administrators
- **Election Control**: Start and stop polls with custom durations.
- **Real-time Analytics**: High-level dashboard showing total votes, leading candidates, and participation metrics.
- **Candidate Management**: Full CRUD operations (Add, Edit, Delete) for candidates, including approval of user requests.
- **Audit Logs**: Securely monitor the election progress in real-time.

### 🍱 UI/UX
- **Dynamic Themes**: Seamless Dark and Light mode support with persistent state.
- **Immersive Design**: Professional voting-themed backgrounds with smooth glassmorphism effects.
- **Responsive Architecture**: Fully optimized for Desktop, Tablet, and Mobile devices.
- **Micro-interactions**: Entrance animations, pulse effects, and real-time notification toasts.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Database**: MongoDB (with connection pooling and indexing)
- **Security**: JWT (token-based sessions), Bcrypt (encryption)
- **Frontend**: Vanilla JavaScript (ES6+), CSS3 (Modern Glassmorphism), HTML5
- **Icons & Graphics**: FontAwesome 6, Chart.js, Custom SVG Illustrations

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MongoDB instance (Local or Atlas)
- Node.js (Optional, for any static asset tooling)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/votesafe.git
   cd votesafe
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/scripts/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   - Copy `.env.example` to `.env`.
   - Fill in your `MONGO_URI` and a secure `SECRET_KEY`.

5. **Initialize Database**:
   - The system automatically creates necessary indexes and settings on the first run.

6. **Create an Admin User**:
   ```bash
   python create_admin.py
   ```

7. **Run the Application**:
   ```bash
   python app.py
   ```
   *Access the app at `http://127.0.0.1:5000`*

---

## 📂 Project Structure

```text
├── app.py              # Application entry point & Routing
├── database.py         # MongoDB connection & indexing logic
├── routes/             # Blueprint-based API endpoints
│   ├── auth.py         # Authentication & Registration
│   ├── admin.py        # Management & Analytics
│   └── vote.py         # Voting & Results
├── static/             # Assets
│   ├── css/            # Modern Glassmorphic styling
│   ├── js/             # Frontend logic & API handlers
│   └── images/         # Thematic backgrounds
├── templates/          # HTML5 Semantic Pages
├── utils/              # Wrappers & Middlewares
└── .env                # Environment secrets (Ignore in git)
```

---

## 🔒 Security Measures
- **Stateful JWT**: Tokens are stored in secure cookies for route protection and LocalStorage for API headers.
- **Database Indexing**: Unique indexes on emails prevent duplicate registrations.
- **Atomic Operations**: MongoDB `$inc` and `$set` ensure vote counts remain accurate under concurrency.
- **Route Guards**: Frontend and Backend decorators prevent non-admin access to sensitive tools.

---

## 📜 License
Built with ❤️ by **Vamsi** for the Online Voting System Project 2026.
Powered by JWT & MongoDB.
