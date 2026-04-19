import time
import logging
from flask import Blueprint, request, jsonify
from database import get_db
from bson.objectid import ObjectId
from utils.auth_middleware import login_required

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

vote_bp = Blueprint('vote', __name__)

def get_collections():
    db = get_db()
    if db is None:
        return None, None
    return db["candidates"], db["users"]

@vote_bp.route('/candidates', methods=['GET'])
@login_required
def get_candidates(current_user):
    candidates_coll, _ = get_collections()
    if candidates_coll is None:
        return jsonify({'message': 'Database connection error!'}), 503

    start_time = time.perf_counter()
    
    # Optimized: Field selection to minimize transfer
    candidates = list(candidates_coll.find({}, {'name': 1, 'party': 1}))
    for c in candidates:
        c['id'] = str(c['_id'])
        del c['_id']
    
    elapsed = (time.perf_counter() - start_time) * 1000
    logging.info(f"CANDIDATES_GET: {elapsed:.2f}ms")
    
    return jsonify(candidates), 200

from datetime import datetime

@vote_bp.route('/voting-status', methods=['GET'])
def get_voting_status():
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
    
    settings = db["settings"].find_one({})
    if not settings:
        return jsonify({'is_active': False, 'remaining_seconds': 0}), 200
        
    is_active = settings.get('voting_active', False)
    end_time_str = settings.get('end_time')
    remaining_seconds = 0

    if is_active and end_time_str:
        end_time = datetime.fromisoformat(end_time_str)
        now = datetime.utcnow()
        if now < end_time:
            remaining_seconds = int((end_time - now).total_seconds())
        else:
            is_active = False
            # Auto-update DB if expired but still marked active
            db["settings"].update_one({}, {'$set': {'voting_active': False, 'end_time': None}})
            
    return jsonify({
        'is_active': is_active,
        'remaining_seconds': remaining_seconds
    }), 200

@vote_bp.route('/cast-vote', methods=['POST'])
@login_required
def cast_vote(current_user):
    candidates_coll, users_coll = get_collections()
    db = get_db()
    if candidates_coll is None or users_coll is None or db is None:
        return jsonify({'message': 'Database connection error!'}), 503

    # Check voting window (Strict Validation)
    settings = db["settings"].find_one({})
    if not settings or not settings.get('voting_active'):
        return jsonify({'message': 'Voting is currently closed!'}), 403
    
    if settings.get('end_time'):
        end_time = datetime.fromisoformat(settings.get('end_time'))
        if datetime.utcnow() > end_time:
            db["settings"].update_one({}, {'$set': {'voting_active': False, 'end_time': None}})
            return jsonify({'message': 'Voting has ended!'}), 403

    start_total = time.perf_counter()
    data = request.json
    candidate_id = data.get('candidate_id')

    if not candidate_id:
        return jsonify({'message': 'Candidate ID is required!'}), 400

    # Optimized search with field selection
    start_db = time.perf_counter()
    user = users_coll.find_one({'_id': ObjectId(current_user['user_id'])}, {'has_voted': 1})
    if user.get('has_voted'):
        return jsonify({'message': 'You have already voted!'}), 403

    # Check if candidate exists (Fetch name and party for history record)
    candidate = candidates_coll.find_one({'_id': ObjectId(candidate_id)}, {'_id': 1, 'name': 1, 'party': 1})
    db_check_time = (time.perf_counter() - start_db) * 1000
    
    if not candidate:
        return jsonify({'message': 'Candidate not found!'}), 404

    # Atomic update and Recording History
    start_update = time.perf_counter()
    
    # 1. Increment candidate vote count
    candidates_coll.update_one(
        {'_id': ObjectId(candidate_id)},
        {'$inc': {'votes': 1}}
    )
    
    # 2. Mark user as voted
    users_coll.update_one(
        {'_id': ObjectId(current_user['user_id'])},
        {'$set': {'has_voted': True}}
    )

    # 3. Record specifically which candidate this user voted for in "votes" collection
    db["votes"].insert_one({
        'user_id': ObjectId(current_user['user_id']),
        'candidate_id': ObjectId(candidate_id),
        'candidate_name': candidate.get('name'),
        'candidate_party': candidate.get('party'),
        'timestamp': datetime.utcnow().isoformat()
    })
    
    update_time = (time.perf_counter() - start_update) * 1000

    total_time = (time.perf_counter() - start_total) * 1000
    logging.info(f"CAST_VOTE: Total={total_time:.2f}ms | DB_Check={db_check_time:.2f}ms | Update={update_time:.2f}ms")

    return jsonify({'message': 'Vote cast successfully!'}), 200

@vote_bp.route('/results', methods=['GET'])
@login_required
def get_results(current_user):
    candidates_coll, _ = get_collections()
    if candidates_coll is None:
        return jsonify({'message': 'Database connection error!'}), 503

    start_time = time.perf_counter()
    # Results with ID for management
    raw_results = list(candidates_coll.find({}, {'name': 1, 'votes': 1}))
    results = []
    for r in raw_results:
        results.append({
            'id': str(r['_id']),
            'name': r['name'],
            'votes': r['votes']
        })
    
    elapsed = (time.perf_counter() - start_time) * 1000
    logging.info(f"RESULTS_GET: {elapsed:.2f}ms")
    
    return jsonify(results), 200

@vote_bp.route('/my-vote', methods=['GET'])
@login_required
def get_my_vote(current_user):
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
    
    vote = db["votes"].find_one({'user_id': ObjectId(current_user['user_id'])})
    if not vote:
        return jsonify({'message': 'No vote recorded for this user.'}), 404
        
    return jsonify({
        'candidate_name': vote.get('candidate_name', 'Unknown'),
        'candidate_party': vote.get('candidate_party', 'Unknown'),
        'timestamp': vote.get('timestamp')
    }), 200

@vote_bp.route('/request_candidate', methods=['POST'])
@login_required
def request_candidate(current_user):
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
    
    data = request.json
    name = data.get('name')
    party = data.get('party')
    
    if not all([name, party]):
        return jsonify({'message': 'Name and party are required!'}), 400
        
    # Security: Prevent duplicates (Pending or Approved)
    existing = db["candidate_requests"].find_one({
        'user_id': ObjectId(current_user['user_id']),
        'status': {'$in': ['pending', 'approved']}
    })
    
    if existing:
        return jsonify({'message': 'A request is already pending or approved for this user!'}), 400

    db["candidate_requests"].insert_one({
        'user_id': ObjectId(current_user['user_id']),
        'name': name,
        'party': party,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    })
    
    return jsonify({'message': 'Request submitted successfully!'}), 201

@vote_bp.route('/my-candidate-request', methods=['GET'])
@login_required
def get_my_candidate_request(current_user):
    db = get_db()
    if db is None:
        return jsonify({'message': 'Database connection error!'}), 503
    
    request_doc = db["candidate_requests"].find_one(
        {'user_id': ObjectId(current_user['user_id'])},
        sort=[('created_at', -1)]
    )
    
    if not request_doc:
        return jsonify(None), 200
        
    return jsonify({
        'name': request_doc.get('name'),
        'party': request_doc.get('party'),
        'status': request_doc.get('status'),
        'timestamp': request_doc.get('created_at')
    }), 200
