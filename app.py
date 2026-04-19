import os
import jwt
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Initialize Database Indexes
    from database import init_db
    with app.app_context():
        init_db()

    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.vote import vote_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(vote_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')

    # Multi-page Routing
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/candidates')
    def candidates():
        return render_template('candidates.html')

    @app.route('/admin')
    def admin():
        token = request.cookies.get('vote_safe_token')
        if not token:
            return "403 Unauthorized: Admin access required", 403
            
        try:
            decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if not decoded.get('is_admin'):
                return "403 Unauthorized: Admin access required", 403
        except Exception:
            return "403 Unauthorized: Admin access required", 403
            
        return render_template('admin.html')

    @app.route('/results')
    def results():
        return render_template('results.html')

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'message': 'Resource not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'message': 'Internal server error'}), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
